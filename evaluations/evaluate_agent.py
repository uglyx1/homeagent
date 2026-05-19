from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class CaseResult:
    name: str
    query: str
    passed: bool
    score: float
    checks: list[str]


def load_cases(path: Path) -> list[dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def evaluate_case(case: dict[str, Any], user_id: str) -> CaseResult:
    import homeagent.app.agent as agent_module

    if os.environ.get("HOMEAGENT_LANGCHAIN_ENABLED", "").lower() == "false":
        agent_module.LANGCHAIN_WORKFLOW_ENABLED = False

    HouseRentingAgentV2 = agent_module.HouseRentingAgentV2

    agent = HouseRentingAgentV2(user_id=user_id)
    result = agent.search(case["query"], verbose=False)
    recommendations = result.recommendations

    checks: list[tuple[bool, str]] = []
    min_recommendations = int(case.get("min_recommendations", 1))
    checks.append(
        (
            len(recommendations) >= min_recommendations,
            f"推荐数量 {len(recommendations)} / 期望至少 {min_recommendations}",
        )
    )

    expected_districts = set(case.get("expected_districts", []))
    if expected_districts and recommendations:
        top_districts = {item.district for item in recommendations[:3]}
        checks.append(
            (
                bool(top_districts & expected_districts),
                f"Top3 区域 {sorted(top_districts)} / 期望 {sorted(expected_districts)}",
            )
        )

    expected_room_types = set(case.get("expected_room_types", []))
    if expected_room_types and recommendations:
        top_room_types = {item.room_type.value for item in recommendations[:3]}
        checks.append(
            (
                bool(top_room_types & expected_room_types),
                f"Top3 户型 {sorted(top_room_types)} / 期望 {sorted(expected_room_types)}",
            )
        )

    budget_max = case.get("budget_max")
    if budget_max is not None and recommendations:
        over_budget = [item.monthly_rent for item in recommendations[:3] if item.monthly_rent > int(budget_max)]
        checks.append(
            (
                not over_budget,
                f"Top3 租金均 <= {budget_max}" if not over_budget else f"Top3 超预算租金 {over_budget}",
            )
        )

    passed_count = sum(1 for ok, _ in checks if ok)
    score = round(passed_count / max(len(checks), 1), 2)
    return CaseResult(
        name=case["name"],
        query=case["query"],
        passed=all(ok for ok, _ in checks),
        score=score,
        checks=[f"{'PASS' if ok else 'FAIL'} - {message}" for ok, message in checks],
    )


def print_report(results: list[CaseResult]) -> None:
    passed = sum(1 for item in results if item.passed)
    score = round(sum(item.score for item in results) / max(len(results), 1), 2)
    print("=" * 72)
    print("HomeAgent 推荐评测")
    print("=" * 72)
    print(f"用例通过: {passed}/{len(results)}")
    print(f"平均得分: {score}")
    print()
    for item in results:
        status = "PASS" if item.passed else "FAIL"
        print(f"[{status}] {item.name} | score={item.score}")
        print(f"query: {item.query}")
        for check in item.checks:
            print(f"  - {check}")
        print()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run HomeAgent recommendation evaluation cases.")
    parser.add_argument(
        "--cases",
        type=Path,
        default=Path(__file__).with_name("cases.json"),
        help="Path to evaluation cases JSON.",
    )
    parser.add_argument("--user", default="eval_user", help="User id used for evaluation memory.")
    parser.add_argument("--llm", action="store_true", help="Allow LangGraph/LLM workflow during evaluation.")
    return parser


def run_evaluation(
    cases_path: Path | None = None,
    user_id: str = "eval_user",
    allow_llm: bool = False,
) -> list[CaseResult]:
    if not allow_llm:
        os.environ["HOMEAGENT_LANGCHAIN_ENABLED"] = "false"
        os.environ["HOMEAGENT_LANGGRAPH_ENABLED"] = "false"

    cases = load_cases(cases_path or Path(__file__).with_name("cases.json"))
    results = [evaluate_case(case, user_id=f"{user_id}_{index}") for index, case in enumerate(cases, start=1)]
    print_report(results)
    return results


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    results = run_evaluation(cases_path=args.cases, user_id=args.user, allow_llm=args.llm)
    if not all(item.passed for item in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
