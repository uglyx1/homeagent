from __future__ import annotations

from dataclasses import dataclass, field

from homeagent.app.tools import ToolRegistry
from homeagent.config import MAX_REACT_STEPS
from homeagent.services.memory_manager import MemoryManager
from homeagent.workflows.planner import ExecutionPlan, Planner, TaskStatus


@dataclass
class ReActResult:
    plan: ExecutionPlan
    thoughts: list[str] = field(default_factory=list)
    parsed_requirements: object | None = None
    search_results: list = field(default_factory=list)
    knowledge_hits: list = field(default_factory=list)
    compare_rows: list = field(default_factory=list)


class ReActAgent:
    def __init__(self, memory: MemoryManager, tools: ToolRegistry) -> None:
        self.memory = memory
        self.tools = tools
        self.planner = Planner()
        self.max_steps = MAX_REACT_STEPS

    def run(self, query: str, verbose: bool = False) -> ReActResult:
        self.memory.short_term.clear()
        plan = self.planner.decompose(query)
        result = ReActResult(plan=plan)

        step = 0
        while step < self.max_steps:
            task = plan.get_next_pending()
            if task is None:
                break

            thought = self._build_thought(task.description)
            result.thoughts.append(thought)
            self.memory.short_term.add_thought(step, thought)

            params = self._build_params(task.tool_name, query, result)
            self.memory.short_term.add_action(step, task.tool_name or "none", params)
            observation = self.tools.execute(task.tool_name, params)
            self.memory.short_term.add_observation(step, observation)

            if not observation.get("success", False):
                task.status = TaskStatus.FAILED
                break

            task.status = TaskStatus.COMPLETED
            task.result = observation["result"]

            if task.tool_name == "parse_requirements":
                result.parsed_requirements = observation["result"]
            elif task.tool_name == "search_houses":
                result.search_results = observation["result"]
            elif task.tool_name == "retrieve_knowledge":
                result.knowledge_hits = observation["result"]
            elif task.tool_name == "compare_houses":
                result.compare_rows = observation["result"]

            step += 1

        return result

    @staticmethod
    def _build_thought(description: str) -> str:
        return f"当前先执行“{description}”，把用户问题拆成可验证的中间结果。"

    @staticmethod
    def _build_params(tool_name: str | None, query: str, result: ReActResult) -> dict:
        if tool_name == "parse_requirements":
            return {"query": query}
        if tool_name == "search_houses":
            requirements = result.parsed_requirements
            if requirements is None:
                return {"params": {}}
            from homeagent.services.requirement_analyzer import RequirementAnalyzer

            analyzer = RequirementAnalyzer()
            return {"params": analyzer.generate_search_params(requirements)}
        if tool_name == "retrieve_knowledge":
            return {"query": query}
        if tool_name == "compare_houses":
            listing_ids = [item.listing_id for item in result.search_results[:3]]
            return {"listing_ids": listing_ids}
        return {}
