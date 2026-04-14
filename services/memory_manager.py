from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from homeagent.config import MEMORY_DIR
from homeagent.domain.models import RoomType, UserProfile, UserRequirements


class ShortTermMemory:
    def __init__(self) -> None:
        self.thought_history: list[dict[str, Any]] = []
        self.action_history: list[dict[str, Any]] = []
        self.observation_history: list[dict[str, Any]] = []
        self.last_requirements: UserRequirements | None = None
        self.last_listing_ids: list[str] = []

    def add_thought(self, step: int, thought: str) -> None:
        self.thought_history.append({"step": step, "thought": thought})

    def add_action(self, step: int, tool_name: str, params: dict[str, Any]) -> None:
        self.action_history.append({"step": step, "tool": tool_name, "params": params})

    def add_observation(self, step: int, observation: Any) -> None:
        self.observation_history.append({"step": step, "observation": observation})

    def clear(self) -> None:
        self.thought_history.clear()
        self.action_history.clear()
        self.observation_history.clear()


class LongTermMemory:
    def __init__(self, storage_dir: Path | str = MEMORY_DIR) -> None:
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._profiles: dict[str, UserProfile] = {}

    def _profile_path(self, user_id: str) -> Path:
        return self.storage_dir / f"{user_id}.json"

    def get_profile(self, user_id: str) -> UserProfile:
        if user_id not in self._profiles:
            path = self._profile_path(user_id)
            if path.exists():
                with open(path, "r", encoding="utf-8") as file:
                    data = json.load(file)
                self._profiles[user_id] = UserProfile(**data)
            else:
                self._profiles[user_id] = UserProfile(user_id=user_id)
        return self._profiles[user_id]

    def save_profile(self, user_id: str) -> None:
        profile = self.get_profile(user_id)
        with open(self._profile_path(user_id), "w", encoding="utf-8") as file:
            json.dump(asdict(profile), file, ensure_ascii=False, indent=2)

    def update_from_requirements(self, user_id: str, requirements: UserRequirements) -> None:
        profile = self.get_profile(user_id)

        if requirements.budget_min is not None or requirements.budget_max is not None:
            profile.budget_history.append(
                {"budget_min": requirements.budget_min, "budget_max": requirements.budget_max}
            )

        for district in requirements.preferred_districts:
            profile.district_frequency[district] = profile.district_frequency.get(district, 0) + 1
        profile.preferred_districts = sorted(
            profile.district_frequency,
            key=lambda key: profile.district_frequency[key],
            reverse=True,
        )[:5]

        for room_type in requirements.preferred_room_types:
            value = room_type.value
            profile.room_type_frequency[value] = profile.room_type_frequency.get(value, 0) + 1
        profile.preferred_room_types = sorted(
            profile.room_type_frequency,
            key=lambda key: profile.room_type_frequency[key],
            reverse=True,
        )[:3]

        for tag in requirements.must_have_tags:
            if tag not in profile.preferred_tags:
                profile.preferred_tags.append(tag)

        self.save_profile(user_id)

    def get_budget_preference(self, user_id: str) -> tuple[int | None, int | None]:
        profile = self.get_profile(user_id)
        mins = [item["budget_min"] for item in profile.budget_history if item.get("budget_min") is not None]
        maxs = [item["budget_max"] for item in profile.budget_history if item.get("budget_max") is not None]
        budget_min = round(sum(mins) / len(mins)) if mins else None
        budget_max = round(sum(maxs) / len(maxs)) if maxs else None
        return budget_min, budget_max

    def record_feedback(self, user_id: str, listing_id: str) -> None:
        profile = self.get_profile(user_id)
        if listing_id not in profile.favorite_listing_ids:
            profile.favorite_listing_ids.append(listing_id)
        self.save_profile(user_id)

    def record_conversation(self, user_id: str, query: str, response: str) -> None:
        profile = self.get_profile(user_id)
        profile.conversation_history.append({"query": query, "response": response})
        profile.conversation_history = profile.conversation_history[-12:]
        self.save_profile(user_id)

    def get_recent_conversations(self, user_id: str, limit: int = 8) -> list[dict[str, str]]:
        profile = self.get_profile(user_id)
        return profile.conversation_history[-limit:]

    def summary(self, user_id: str) -> str:
        profile = self.get_profile(user_id)
        lines = [f"用户画像：{user_id}"]
        budget_min, budget_max = self.get_budget_preference(user_id)
        if budget_min is not None or budget_max is not None:
            lines.append(f"- 常用预算：{budget_min or '不限'} - {budget_max or '不限'} 元")
        if profile.preferred_districts:
            lines.append(f"- 偏好区域：{', '.join(profile.preferred_districts[:3])}")
        if profile.preferred_room_types:
            lines.append(f"- 偏好户型：{', '.join(profile.preferred_room_types[:2])}")
        if profile.preferred_tags:
            lines.append(f"- 常见标签：{', '.join(profile.preferred_tags[:3])}")
        if profile.favorite_listing_ids:
            lines.append(f"- 收藏房源：{', '.join(profile.favorite_listing_ids[-3:])}")
        if profile.conversation_history:
            lines.append(f"- 最近对话：{len(profile.conversation_history)} 条")
        return "\n".join(lines)


class MemoryManager:
    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory()

    def update_from_requirements(self, requirements: UserRequirements) -> None:
        self.short_term.last_requirements = requirements
        self.long_term.update_from_requirements(self.user_id, requirements)

    def apply_profile_defaults(self, requirements: UserRequirements) -> UserRequirements:
        profile = self.long_term.get_profile(self.user_id)
        budget_min, budget_max = self.long_term.get_budget_preference(self.user_id)

        if not requirements.preferred_districts and profile.preferred_districts:
            requirements.preferred_districts = profile.preferred_districts[:2].copy()
            requirements.applied_context.append(
                f"自动补充历史偏好区域：{', '.join(requirements.preferred_districts)}"
            )

        if not requirements.preferred_room_types and profile.preferred_room_types:
            room_types: list[RoomType] = []
            for item in profile.preferred_room_types[:2]:
                try:
                    room_types.append(RoomType(item))
                except ValueError:
                    continue
            if room_types:
                requirements.preferred_room_types = room_types
                requirements.applied_context.append(
                    "自动补充历史偏好户型：" + ", ".join(item.value for item in room_types)
                )

        if (
            requirements.budget_min is None
            and requirements.budget_max is None
            and (budget_min is not None or budget_max is not None)
        ):
            requirements.budget_min = budget_min
            requirements.budget_max = budget_max
            requirements.applied_context.append(
                f"自动补充历史预算：{requirements.budget_min or '不限'} - "
                f"{requirements.budget_max or '不限'} 元"
            )

        return requirements

    def record_feedback(self, listing_id: str) -> None:
        self.long_term.record_feedback(self.user_id, listing_id)

    def record_conversation(self, query: str, response: str) -> None:
        self.long_term.record_conversation(self.user_id, query, response)

    def get_recent_conversations(self, limit: int = 8) -> list[dict[str, str]]:
        return self.long_term.get_recent_conversations(self.user_id, limit=limit)

    def get_profile_summary(self) -> str:
        return self.long_term.summary(self.user_id)
