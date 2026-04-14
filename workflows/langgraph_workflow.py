from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, TypedDict

from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from homeagent.app.tools import ToolRegistry
from homeagent.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, LLM_TEMPERATURE
from homeagent.domain.models import KnowledgeHit, RentalListing, RoomType, UserRequirements
from homeagent.services.memory_manager import MemoryManager
from homeagent.services.requirement_analyzer import RequirementAnalyzer
from homeagent.utils.logger_handler import get_logger
from homeagent.utils.prompt_loader import load_prompt


logger = get_logger("homeagent.langgraph")


@dataclass
class WorkflowExecution:
    parsed_requirements: UserRequirements | None = None
    search_results: list[RentalListing] = field(default_factory=list)
    knowledge_hits: list[KnowledgeHit] = field(default_factory=list)
    compare_rows: list[dict[str, Any]] = field(default_factory=list)
    thoughts: list[str] = field(default_factory=list)
    summary_hint: str = ""
    next_steps_hint: list[str] = field(default_factory=list)


class WorkflowState(TypedDict, total=False):
    query: str
    verbose: bool
    thoughts: list[str]
    parsed_requirements: UserRequirements
    search_results: list[RentalListing]
    knowledge_hits: list[KnowledgeHit]
    compare_rows: list[dict[str, Any]]


class LangGraphRentalWorkflow:
    def __init__(
        self,
        memory: MemoryManager,
        tools: ToolRegistry,
        analyzer: RequirementAnalyzer,
        model: str = LLM_MODEL,
    ) -> None:
        self.memory = memory
        self.tools = tools
        self.analyzer = analyzer
        self.model = model
        self.llm = self._build_llm()

        self.requirement_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", load_prompt("requirement_parser_system.txt")),
                ("human", load_prompt("requirement_parser_human.txt")),
            ]
        )
        self.summary_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", load_prompt("summary_system.txt")),
                ("human", load_prompt("summary_human.txt")),
            ]
        )
        self.checkpointer = MemorySaver()
        self.graph = self._build_graph()

    @property
    def available(self) -> bool:
        return self.llm is not None

    def run(self, query: str, verbose: bool = False) -> WorkflowExecution:
        if not self.available:
            return WorkflowExecution()

        initial_state: WorkflowState = {
            "query": query,
            "verbose": verbose,
            "thoughts": [],
        }
        thread_id = f"{self.memory.user_id}:{abs(hash(query))}"
        final_state = self.graph.invoke(initial_state, config={"configurable": {"thread_id": thread_id}})
        return WorkflowExecution(
            parsed_requirements=final_state.get("parsed_requirements"),
            search_results=final_state.get("search_results", []),
            knowledge_hits=final_state.get("knowledge_hits", []),
            compare_rows=final_state.get("compare_rows", []),
            thoughts=final_state.get("thoughts", []),
        )

    def summarize(
        self,
        query: str,
        requirements: UserRequirements,
        recommendations: list[RentalListing],
        knowledge_hits: list[KnowledgeHit],
        relaxation_notes: list[str],
    ) -> tuple[str, list[str]]:
        if not self.available:
            return "", []

        prompt_value = self.summary_prompt.invoke(
            {
                "query": query,
                "requirements": json.dumps(
                    {
                        "budget_min": requirements.budget_min,
                        "budget_max": requirements.budget_max,
                        "districts": requirements.preferred_districts,
                        "locations": requirements.preferred_locations,
                        "room_types": [item.value for item in requirements.preferred_room_types],
                        "must_have_tags": requirements.must_have_tags,
                    },
                    ensure_ascii=False,
                ),
                "recommendations": json.dumps(
                    [self._serialize_listing(item) for item in recommendations[:5]],
                    ensure_ascii=False,
                ),
                "knowledge_hits": json.dumps(
                    [{"title": hit.title, "snippet": hit.snippet, "source": hit.source} for hit in knowledge_hits[:3]],
                    ensure_ascii=False,
                ),
                "relaxation_notes": json.dumps(relaxation_notes, ensure_ascii=False),
            }
        )
        payload = self._invoke_json(prompt_value)
        summary = str(payload.get("analysis_summary", "")).strip()
        steps = payload.get("next_steps", [])
        if not isinstance(steps, list):
            steps = []
        return summary, [str(item).strip() for item in steps if str(item).strip()]

    def _build_llm(self) -> ChatOpenAI | None:
        if not LLM_API_KEY:
            return None
        return ChatOpenAI(
            model=self.model,
            api_key=LLM_API_KEY,
            base_url=LLM_BASE_URL,
            temperature=LLM_TEMPERATURE,
        )

    def _build_graph(self):
        graph = StateGraph(WorkflowState)
        graph.add_node("parse_requirements", self._node_parse_requirements)
        graph.add_node("search_houses", self._node_search_houses)
        graph.add_node("retrieve_knowledge", self._node_retrieve_knowledge)
        graph.add_node("compare_houses", self._node_compare_houses)
        graph.add_edge(START, "parse_requirements")
        graph.add_edge("parse_requirements", "search_houses")
        graph.add_edge("search_houses", "retrieve_knowledge")
        graph.add_edge("retrieve_knowledge", "compare_houses")
        graph.add_edge("compare_houses", END)
        return graph.compile(checkpointer=self.checkpointer)

    def _node_parse_requirements(self, state: WorkflowState) -> WorkflowState:
        query = state["query"]
        requirements = self._parse_requirements_with_llm(query)
        requirements = self.memory.apply_profile_defaults(requirements)
        return {
            "parsed_requirements": requirements,
            "thoughts": state.get("thoughts", []) + ["LangGraph 已完成 LLM 需求解析。"],
        }

    def _node_search_houses(self, state: WorkflowState) -> WorkflowState:
        requirements = state.get("parsed_requirements")
        if requirements is None:
            return {"search_results": [], "thoughts": state.get("thoughts", [])}
        params = self.analyzer.generate_search_params(requirements)
        response = self.tools.execute("search_houses", {"params": params})
        results = response.get("result", []) if response.get("success", False) else []
        return {
            "search_results": results,
            "thoughts": state.get("thoughts", []) + ["LangGraph 已调用房源搜索工具。"],
        }

    def _node_retrieve_knowledge(self, state: WorkflowState) -> WorkflowState:
        response = self.tools.execute("retrieve_knowledge", {"query": state["query"]})
        hits = response.get("result", []) if response.get("success", False) else []
        return {
            "knowledge_hits": hits,
            "thoughts": state.get("thoughts", []) + ["LangGraph 已调用知识检索工具。"],
        }

    def _node_compare_houses(self, state: WorkflowState) -> WorkflowState:
        listing_ids = [item.listing_id for item in state.get("search_results", [])[:3]]
        if not listing_ids:
            return {
                "compare_rows": [],
                "thoughts": state.get("thoughts", []),
            }
        response = self.tools.execute("compare_houses", {"listing_ids": listing_ids})
        rows = response.get("result", []) if response.get("success", False) else []
        return {
            "compare_rows": rows,
            "thoughts": state.get("thoughts", []) + ["LangGraph 已整理候选房源对比结果。"],
        }

    def _parse_requirements_with_llm(self, query: str) -> UserRequirements:
        fallback = self.analyzer.analyze(query, previous=self.memory.short_term.last_requirements)
        if not self.available:
            return fallback

        prompt_value = self.requirement_prompt.invoke(
            {
                "query": query,
                "memory_summary": self.memory.get_profile_summary(),
                "recent_history": self._recent_history_text(),
            }
        )
        try:
            payload = self._invoke_json(prompt_value)
        except Exception as exc:
            logger.warning("LLM requirement parsing failed, fallback to rule analyzer: %s", exc)
            return fallback
        requirements = self._to_requirements(payload, fallback)
        requirements.raw_query = query
        return requirements

    def _recent_history_text(self) -> str:
        recent_history = self.memory.get_recent_conversations(limit=4)
        if not recent_history:
            return "无"
        return "\n".join(
            f"用户：{item['query']}\n助手：{item['response']}" for item in recent_history
        )

    def _invoke_json(self, prompt_value) -> dict[str, Any]:
        if self.llm is None:
            return {}
        message = self.llm.invoke(prompt_value.to_messages())
        content = message.content if isinstance(message, AIMessage) else str(message)
        return self._parse_json_content(content)

    @staticmethod
    def _parse_json_content(content: Any) -> dict[str, Any]:
        text = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
        text = text.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:].strip()
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            text = text[start : end + 1]
        return json.loads(text)

    def _to_requirements(self, payload: dict[str, Any], fallback: UserRequirements) -> UserRequirements:
        requirements = UserRequirements(raw_query=fallback.raw_query)
        requirements.budget_min = self._maybe_int(payload.get("budget_min"), fallback.budget_min)
        requirements.budget_max = self._maybe_int(payload.get("budget_max"), fallback.budget_max)
        requirements.preferred_districts = self._string_list(payload.get("districts")) or fallback.preferred_districts
        requirements.preferred_locations = self._string_list(payload.get("locations")) or fallback.preferred_locations
        requirements.preferred_room_types = self._parse_room_types(payload.get("room_types")) or fallback.preferred_room_types
        requirements.min_area = self._maybe_int(payload.get("min_area"), fallback.min_area)
        requirements.max_area = self._maybe_int(payload.get("max_area"), fallback.max_area)
        requirements.near_subway = bool(payload.get("near_subway", fallback.near_subway))
        requirements.max_distance_to_metro = self._maybe_int(
            payload.get("max_distance_to_metro"),
            fallback.max_distance_to_metro,
        )
        requirements.must_have_tags = self._string_list(payload.get("must_have_tags")) or fallback.must_have_tags
        requirements.special_requirements = (
            self._string_list(payload.get("special_requirements")) or fallback.special_requirements
        )
        return requirements

    @staticmethod
    def _serialize_listing(listing: RentalListing) -> dict[str, Any]:
        return {
            "listing_id": listing.listing_id,
            "title": listing.title,
            "district": listing.district,
            "location": listing.location,
            "layout": listing.layout,
            "monthly_rent": listing.monthly_rent,
            "area": listing.area,
            "tags": listing.tags,
            "match_score": listing.match_score,
            "reason": listing.reason,
        }

    @staticmethod
    def _string_list(value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if str(item).strip()]

    @staticmethod
    def _maybe_int(value: Any, fallback: int | None) -> int | None:
        if value in (None, ""):
            return fallback
        try:
            return int(value)
        except (TypeError, ValueError):
            return fallback

    @staticmethod
    def _parse_room_types(value: Any) -> list[RoomType]:
        if not isinstance(value, list):
            return []
        parsed: list[RoomType] = []
        for item in value:
            try:
                parsed.append(RoomType(str(item)))
            except ValueError:
                continue
        return parsed
