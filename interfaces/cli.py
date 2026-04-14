from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from homeagent.app.agent import HouseRentingAgentV2
    from homeagent.infrastructure.indexing.build_listing_index import main as rebuild_listing_index
    from homeagent.config import DEFAULT_USER_ID
except ModuleNotFoundError:
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from homeagent.app.agent import HouseRentingAgentV2
    from homeagent.infrastructure.indexing.build_listing_index import main as rebuild_listing_index
    from homeagent.config import DEFAULT_USER_ID


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="HomeAgent 租房 Agent Demo")
    parser.add_argument("query", nargs="*", help="租房需求，例如：朝阳区 两室一厅 预算6500 近地铁")
    parser.add_argument("--user", default=DEFAULT_USER_ID, help="用户 ID，用于保存简单画像")
    parser.add_argument("--profile", action="store_true", help="查看当前用户画像")
    parser.add_argument("--status", action="store_true", help="查看项目状态")
    parser.add_argument("--rebuild-index", action="store_true", help="根据 raw_data 重建房源索引")
    parser.add_argument("--show", metavar="LISTING_ID", help="查看指定房源详情")
    parser.add_argument("--verbose", action="store_true", help="输出更详细的思考轨迹")
    return parser


def interactive_loop(agent: HouseRentingAgentV2, verbose: bool = False) -> None:
    print("进入 HomeAgent 交互模式，输入 quit 退出，输入 profile 查看画像，输入 status 查看状态。")
    while True:
        query = input("\n请输入租房需求: ").strip()
        if not query:
            continue
        if query.lower() in {"quit", "exit"}:
            print("已退出。")
            break
        if query.lower() == "profile":
            print(agent.get_memory_summary())
            continue
        if query.lower() == "status":
            print(agent.get_status_summary())
            continue
        print()
        print(agent.chat(query, verbose=verbose))


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.rebuild_index:
        rebuild_listing_index()
        return

    agent = HouseRentingAgentV2(user_id=args.user)

    if args.status:
        print(agent.get_status_summary())
        return

    if args.profile:
        print(agent.get_memory_summary())
        return

    if args.show:
        print(agent.get_listing_detail_text(args.show))
        return

    if args.query:
        print(agent.chat(" ".join(args.query), verbose=args.verbose))
        return

    interactive_loop(agent, verbose=args.verbose)


if __name__ == "__main__":
    main()
