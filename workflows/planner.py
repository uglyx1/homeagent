from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SubTask:
    task_id: str
    description: str
    tool_name: str | None = None
    status: TaskStatus = TaskStatus.PENDING
    result: object | None = None


@dataclass
class ExecutionPlan:
    query: str
    subtasks: list[SubTask] = field(default_factory=list)

    def get_next_pending(self) -> SubTask | None:
        for task in self.subtasks:
            if task.status == TaskStatus.PENDING:
                return task
        return None


class Planner:
    def decompose(self, query: str) -> ExecutionPlan:
        subtasks = [
            SubTask("t1", "解析用户需求", "parse_requirements"),
            SubTask("t2", "搜索候选房源", "search_houses"),
            SubTask("t3", "检索租房知识库", "retrieve_knowledge"),
        ]
        if any(keyword in query for keyword in ["对比", "比较"]):
            subtasks.append(SubTask("t4", "对比候选房源", "compare_houses"))
        return ExecutionPlan(query=query, subtasks=subtasks)
