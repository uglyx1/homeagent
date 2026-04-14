from __future__ import annotations

from copy import deepcopy

from homeagent.config import (
    DEFAULT_USER_ID,
    LANGCHAIN_WORKFLOW_ENABLED,
    LLM_MODEL,
    TOP_N_RECOMMENDATIONS,
)
from homeagent.app.tools import build_tool_registry
from homeagent.domain.models import RecommendationResult, RentalListing, UserRequirements
from homeagent.services.decision_engine import DecisionEngine
from homeagent.services.memory_manager import MemoryManager
from homeagent.services.recommender import Recommender
from homeagent.services.requirement_analyzer import RequirementAnalyzer
from homeagent.workflows.react_agent import ReActAgent
from homeagent.workflows import LangGraphRentalWorkflow, WorkflowExecution


class HouseRentingAgentV2:
    def __init__(self, user_id: str = DEFAULT_USER_ID) -> None:
        self.user_id = user_id
        self.memory = MemoryManager(user_id=user_id)
        self.analyzer = RequirementAnalyzer()
        self.tools = build_tool_registry(self.memory)
        self.decision_engine = DecisionEngine()
        self.recommender = Recommender()
        self.react_agent = ReActAgent(memory=self.memory, tools=self.tools)
        self.langgraph_workflow = LangGraphRentalWorkflow(
            memory=self.memory,
            tools=self.tools,
            analyzer=self.analyzer,
            model=LLM_MODEL,
        )

    def search(self, query: str, verbose: bool = False) -> RecommendationResult:
        workflow_result = self._run_workflow(query, verbose=verbose)
        requirements = workflow_result.parsed_requirements
        if requirements is None:
            raise RuntimeError("需求解析失败，无法继续推荐。")

        ranked_listings = self.decision_engine.evaluate(workflow_result.search_results, requirements)
        ranked_listings, relaxation_notes = self._maybe_relax_search(
            requirements=requirements,
            listings=ranked_listings,
            thoughts=workflow_result.thoughts,
        )
        recommendations = ranked_listings[:TOP_N_RECOMMENDATIONS]

        self.memory.update_from_requirements(requirements)
        self.memory.short_term.last_listing_ids = [item.listing_id for item in recommendations]

        summary = self._build_summary(len(ranked_listings), recommendations, relaxation_notes)
        next_steps = self._build_next_steps(recommendations, relaxation_notes)

        if self._llm_enabled():
            llm_summary, llm_steps = self.langgraph_workflow.summarize(
                query=query,
                requirements=requirements,
                recommendations=recommendations,
                knowledge_hits=workflow_result.knowledge_hits,
                relaxation_notes=relaxation_notes,
            )
            if llm_summary:
                summary = llm_summary
            if llm_steps:
                next_steps = llm_steps

        return RecommendationResult(
            query=query,
            parsed_requirements=requirements,
            total_found=len(ranked_listings),
            recommendations=recommendations,
            analysis_summary=summary,
            next_steps=next_steps,
            knowledge_hits=workflow_result.knowledge_hits,
            thoughts=workflow_result.thoughts,
            compare_rows=workflow_result.compare_rows,
            relaxation_notes=relaxation_notes,
        )

    def chat(self, query: str, verbose: bool = False) -> str:
        result = self.search(query, verbose=verbose)
        return self.recommender.format_recommendation_text(result)

    def get_memory_summary(self) -> str:
        return self.memory.get_profile_summary()

    def get_recent_conversations(self, limit: int = 8) -> list[dict[str, str]]:
        return self.memory.get_recent_conversations(limit=limit)

    def record_conversation(self, query: str, response: str) -> None:
        self.memory.record_conversation(query, response)

    def get_status_summary(self) -> str:
        listing_response = self.tools.execute("search_houses", {"params": {"limit": 1}})
        listing_text = "房源数据源可用。" if listing_response.get("success", False) else "房源数据源不可用。"
        knowledge_text = self.tools.execute("get_project_status", {}).get("result", "")
        if self._llm_enabled():
            llm_text = f"LangGraph 工作流已启用，当前模型：{LLM_MODEL}。"
        elif LANGCHAIN_WORKFLOW_ENABLED:
            llm_text = f"LangGraph 已配置但当前不可用，已回退到本地规则流；目标模型：{LLM_MODEL}。"
        else:
            llm_text = "LangGraph 工作流未启用，当前走本地规则工作流。"
        return f"{listing_text}\n{knowledge_text}\n{llm_text}".strip()

    def get_listing(self, listing_id: str) -> RentalListing | None:
        response = self.tools.execute("get_house_detail", {"listing_id": listing_id})
        if not response.get("success", False):
            return None
        return response.get("result")

    def get_listing_detail_text(self, listing_id: str) -> str:
        listing = self.get_listing(listing_id)
        if listing is None:
            return f"没有找到房源 {listing_id}"
        return self.recommender.format_listing_detail(listing)

    def get_compare_rows(self, listing_ids: list[str]) -> list[dict]:
        response = self.tools.execute("compare_houses", {"listing_ids": listing_ids})
        if not response.get("success", False):
            return []
        return response.get("result", [])

    def get_favorite_listing_ids(self) -> list[str]:
        profile = self.memory.long_term.get_profile(self.user_id)
        return profile.favorite_listing_ids.copy()

    def get_favorite_listings(self) -> list[RentalListing]:
        listings: list[RentalListing] = []
        for listing_id in self.get_favorite_listing_ids():
            listing = self.get_listing(listing_id)
            if listing is not None:
                listings.append(listing)
        return listings

    def record_feedback(self, listing_id: str) -> None:
        self.memory.record_feedback(listing_id)

    def _run_workflow(self, query: str, verbose: bool) -> WorkflowExecution:
        if self._llm_enabled():
            try:
                return self.langgraph_workflow.run(query, verbose=verbose)
            except Exception as exc:
                fallback = self.react_agent.run(query, verbose=verbose)
                fallback.thoughts.append(f"LangGraph 执行失败，已回退到本地规则流：{exc}")
                return WorkflowExecution(
                    parsed_requirements=fallback.parsed_requirements,
                    search_results=fallback.search_results,
                    knowledge_hits=fallback.knowledge_hits,
                    compare_rows=fallback.compare_rows,
                    thoughts=fallback.thoughts,
                )

        fallback = self.react_agent.run(query, verbose=verbose)
        return WorkflowExecution(
            parsed_requirements=fallback.parsed_requirements,
            search_results=fallback.search_results,
            knowledge_hits=fallback.knowledge_hits,
            compare_rows=fallback.compare_rows,
            thoughts=fallback.thoughts,
        )

    def _llm_enabled(self) -> bool:
        return LANGCHAIN_WORKFLOW_ENABLED and self.langgraph_workflow.available

    def _maybe_relax_search(
        self,
        requirements: UserRequirements,
        listings: list[RentalListing],
        thoughts: list[str],
    ) -> tuple[list[RentalListing], list[str]]:
        relaxation_notes: list[str] = []
        best_score = listings[0].match_score if listings else 0.0

        if len(listings) >= 3 and best_score >= 7.0:
            return listings, relaxation_notes

        base_params = self.analyzer.generate_search_params(requirements)
        candidates: list[tuple[list[RentalListing], str]] = []

        if requirements.max_distance_to_metro is not None:
            params = deepcopy(base_params)
            relaxed_requirements = deepcopy(requirements)
            relaxed_requirements.max_distance_to_metro = int(requirements.max_distance_to_metro * 1.5)
            params["max_distance_to_metro"] = relaxed_requirements.max_distance_to_metro
            candidates.append(
                (
                    self._execute_search(params, relaxed_requirements),
                    f"自动放宽地铁距离到 {params['max_distance_to_metro']} 米",
                )
            )

        if requirements.budget_max is not None:
            params = deepcopy(base_params)
            relaxed_requirements = deepcopy(requirements)
            relaxed_requirements.budget_max = int(requirements.budget_max * 1.15)
            params["price_max"] = relaxed_requirements.budget_max
            candidates.append(
                (
                    self._execute_search(params, relaxed_requirements),
                    f"自动把预算上浮到 {params['price_max']} 元",
                )
            )

        if requirements.preferred_districts:
            params = deepcopy(base_params)
            relaxed_requirements = deepcopy(requirements)
            relaxed_requirements.preferred_districts = self._expand_districts(requirements.preferred_districts)
            params["districts"] = relaxed_requirements.preferred_districts
            candidates.append(
                (
                    self._execute_search(params, relaxed_requirements),
                    "自动扩展到相邻区域做补充召回",
                )
            )

        best_list = listings
        best_note = ""
        for candidate_list, note in candidates:
            candidate_score = candidate_list[0].match_score if candidate_list else 0.0
            if len(candidate_list) > len(best_list) or candidate_score > best_score:
                best_list = candidate_list
                best_score = candidate_score
                best_note = note

        if not best_note and candidates and best_score < 6.5:
            fallback_list, fallback_note = max(
                candidates,
                key=lambda item: item[0][0].match_score if item[0] else -1,
            )
            best_list = fallback_list
            best_note = fallback_note

        if best_note:
            relaxation_notes.append(best_note)
            thoughts.append(f"候选结果偏少，已触发兜底策略：{best_note}。")

        return best_list, relaxation_notes

    def _execute_search(self, params: dict, requirements: UserRequirements) -> list[RentalListing]:
        response = self.tools.execute("search_houses", {"params": params})
        if not response.get("success", False):
            return []
        return self.decision_engine.evaluate(response["result"], requirements)

    @staticmethod
    def _expand_districts(districts: list[str]) -> list[str]:
        adjacency = {
            "朝阳区": ["东城区", "通州区", "海淀区"],
            "海淀区": ["昌平区", "西城区", "朝阳区"],
            "丰台区": ["大兴区", "西城区", "朝阳区"],
            "通州区": ["朝阳区", "大兴区"],
            "昌平区": ["海淀区"],
            "大兴区": ["丰台区", "通州区", "北京经济技术开发区"],
            "西城区": ["海淀区", "丰台区", "东城区"],
            "东城区": ["朝阳区", "西城区", "丰台区"],
            "石景山区": ["海淀区", "丰台区"],
            "北京经济技术开发区": ["大兴区", "通州区"],
        }
        expanded = list(districts)
        for district in districts:
            for neighbor in adjacency.get(district, []):
                if neighbor not in expanded:
                    expanded.append(neighbor)
        return expanded

    @staticmethod
    def _build_summary(
        total_found: int,
        recommendations: list[RentalListing],
        relaxation_notes: list[str],
    ) -> str:
        if not recommendations:
            return "当前没有找到合适房源，建议放宽预算或区域条件。"
        top = recommendations[0]
        summary = (
            f"共找到 {total_found} 套候选房源，当前最优推荐是 {top.title}，"
            f"租金 {top.monthly_rent} 元，匹配分 {top.match_score}。"
        )
        if relaxation_notes:
            summary += f" 系统还执行了兜底放宽策略：{'；'.join(relaxation_notes)}。"
        return summary

    @staticmethod
    def _build_next_steps(
        recommendations: list[RentalListing],
        relaxation_notes: list[str],
    ) -> list[str]:
        if not recommendations:
            return [
                "扩大区域范围，例如从单一区域扩展到相邻区。",
                "适当提高预算上限，或者降低地铁距离要求。",
            ]

        steps = [
            "先从前 2 到 3 套里挑出最感兴趣的继续对比。",
            "如果你有新的抓包 JSON，可以继续补充房源池。",
            "如果你后面给我 PDF，我可以把租房知识继续接入 Chroma 检索。",
        ]
        if relaxation_notes:
            steps.insert(1, f"本轮已经自动放宽过条件：{'；'.join(relaxation_notes)}。")
        return steps


def chat_houses_v2(query: str, user_id: str = DEFAULT_USER_ID, verbose: bool = False) -> str:
    agent = HouseRentingAgentV2(user_id=user_id)
    return agent.chat(query, verbose=verbose)
