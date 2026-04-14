from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeagent.domain.models import KnowledgeHit, RentalListing, UserRequirements
from homeagent.infrastructure.datasources.listing_data_source import get_data_source
from homeagent.infrastructure.retrieval.knowledge_base import RentalKnowledgeBase
from homeagent.services.memory_manager import MemoryManager
from homeagent.services.requirement_analyzer import RequirementAnalyzer


@dataclass
class ToolDefinition:
    name: str
    description: str
    func: Callable[..., Any]


class ToolRegistry:
    def __init__(self) -> None:
        self.tools: dict[str, ToolDefinition] = {}

    def register(self, name: str, description: str, func: Callable[..., Any]) -> None:
        self.tools[name] = ToolDefinition(name=name, description=description, func=func)

    def execute(self, name: str, params: dict[str, Any]) -> dict[str, Any]:
        if name not in self.tools:
            return {"success": False, "error": f"未知工具: {name}"}
        try:
            result = self.tools[name].func(**params)
            return {"success": True, "tool": name, "result": result}
        except Exception as exc:
            return {"success": False, "tool": name, "error": str(exc)}

    def get_all_tools(self) -> list[dict[str, str]]:
        return [{"name": item.name, "description": item.description} for item in self.tools.values()]


class AgentTools:
    def __init__(self, memory: MemoryManager) -> None:
        self.memory = memory
        self.data_source = get_data_source()
        self.analyzer = RequirementAnalyzer()
        self.knowledge = RentalKnowledgeBase()

    def parse_requirements(self, query: str) -> UserRequirements:
        requirements = self.analyzer.analyze(query, previous=self.memory.short_term.last_requirements)
        return self.memory.apply_profile_defaults(requirements)

    def search_houses(self, params: dict[str, Any]) -> list[RentalListing]:
        return self.data_source.search(params)

    def get_house_detail(self, listing_id: str) -> RentalListing | None:
        return self.data_source.get_by_id(listing_id)

    def compare_houses(self, listing_ids: list[str]) -> list[dict[str, Any]]:
        rows = []
        for listing_id in listing_ids:
            listing = self.data_source.get_by_id(listing_id)
            if not listing:
                continue
            rows.append(
                {
                    "listing_id": listing.listing_id,
                    "title": listing.title,
                    "district": listing.district,
                    "location": listing.location,
                    "monthly_rent": listing.monthly_rent,
                    "area": listing.area,
                    "metro_distance": listing.transport.metro_distance,
                    "tags": listing.tags[:4],
                }
            )
        return rows

    def retrieve_knowledge(self, query: str) -> list[KnowledgeHit]:
        return self.knowledge.search(query)

    def get_user_profile(self) -> str:
        return self.memory.get_profile_summary()

    def get_project_status(self) -> str:
        return self.knowledge.status()


def build_tool_registry(memory: MemoryManager) -> ToolRegistry:
    tools = AgentTools(memory)
    registry = ToolRegistry()
    registry.register("parse_requirements", "解析用户租房需求", tools.parse_requirements)
    registry.register("search_houses", "根据条件搜索房源", tools.search_houses)
    registry.register("get_house_detail", "获取单套房源详情", tools.get_house_detail)
    registry.register("compare_houses", "对比多套房源", tools.compare_houses)
    registry.register("retrieve_knowledge", "检索租房知识库", tools.retrieve_knowledge)
    registry.register("get_user_profile", "读取用户画像摘要", tools.get_user_profile)
    registry.register("get_project_status", "查看项目数据和知识库状态", tools.get_project_status)
    return registry
