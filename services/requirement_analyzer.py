from __future__ import annotations

import re

from homeagent.domain.models import RoomType, UserRequirements


DISTRICTS = [
    "朝阳区",
    "海淀区",
    "丰台区",
    "通州区",
    "昌平区",
    "大兴区",
    "西城区",
    "东城区",
    "石景山区",
    "北京经济技术开发区",
]

ROOM_TYPE_KEYWORDS = {
    RoomType.STUDIO: ["开间", "单间", "studio"],
    RoomType.ONE_BEDROOM: ["一室一厅", "一室", "一居", "1居"],
    RoomType.TWO_BEDROOM: ["两室一厅", "两室", "两居", "2居"],
    RoomType.THREE_BEDROOM: ["三室一厅", "三室", "三居", "3居"],
}

TAG_KEYWORDS = {
    "近地铁": ["近地铁", "地铁口", "靠近地铁", "地铁附近"],
    "电梯": ["电梯"],
    "阳台": ["阳台"],
    "独卫": ["独卫", "独立卫生间"],
    "可养宠物": ["养宠物", "宠物", "养猫", "养狗"],
    "可月付": ["月付", "押一付一"],
    "整租": ["整租"],
    "合租": ["合租"],
}

KNOWN_LOCATIONS = [
    "望京",
    "双井",
    "西二旗",
    "五道口",
    "中关村",
    "丽泽",
    "草桥",
    "回龙观",
    "旧宫",
    "金融街",
    "东直门",
    "国贸",
    "蒲黄榆",
    "四惠",
    "鲁谷",
    "五棵松",
    "亦庄河西区",
]


class RequirementAnalyzer:
    money_token_pattern = r"(\d+(?:\.\d+)?(?:k|K|w|W|千|万)?)"

    def analyze(
        self,
        user_query: str,
        previous: UserRequirements | None = None,
    ) -> UserRequirements:
        req = UserRequirements(raw_query=user_query.strip())

        self._parse_budget(user_query, req)
        self._parse_districts(user_query, req)
        self._parse_room_types(user_query, req)
        self._parse_area(user_query, req)
        self._parse_tags(user_query, req)
        self._parse_locations(user_query, req)
        self._inherit_previous(user_query, req, previous)

        return req

    def generate_search_params(self, requirements: UserRequirements) -> dict:
        params: dict = {
            "districts": requirements.preferred_districts,
            "locations": requirements.preferred_locations,
            "room_types": [item.value for item in requirements.preferred_room_types],
            "must_have_tags": requirements.must_have_tags,
        }

        if requirements.budget_min is not None:
            params["price_min"] = max(0, int(requirements.budget_min * 0.9))
        if requirements.budget_max is not None:
            params["price_max"] = int(requirements.budget_max * 1.05)
        if requirements.min_area is not None:
            params["area_min"] = requirements.min_area
        if requirements.max_area is not None:
            params["area_max"] = requirements.max_area
        if requirements.near_subway:
            params["max_distance_to_metro"] = requirements.max_distance_to_metro or 1000
        if "整租" in requirements.must_have_tags:
            params["rent_type"] = "整租"
        if "合租" in requirements.must_have_tags:
            params["rent_type"] = "合租"

        return params

    def _parse_budget(self, query: str, req: UserRequirements) -> None:
        range_match = re.search(
            rf"{self.money_token_pattern}\s*(?:-|到|至|~|～)\s*{self.money_token_pattern}",
            query,
        )
        if range_match:
            req.budget_min = self._money_to_int(range_match.group(1))
            req.budget_max = self._money_to_int(range_match.group(2))
            if req.budget_min > req.budget_max:
                req.budget_min, req.budget_max = req.budget_max, req.budget_min
            return

        upper_match = re.search(
            rf"(?:预算|租金)?\s*(?:不超过|最多|以内|以下)\s*{self.money_token_pattern}",
            query,
        )
        if upper_match:
            req.budget_max = self._money_to_int(upper_match.group(1))
            return

        around_match = re.search(
            rf"(?:预算|租金)?\s*{self.money_token_pattern}\s*(?:左右|上下|附近)",
            query,
        )
        if around_match:
            center = self._money_to_int(around_match.group(1))
            req.budget_min = max(0, center - 500)
            req.budget_max = center + 500
            return

        direct_match = re.search(rf"(?:预算|租金)\s*{self.money_token_pattern}", query)
        if direct_match:
            req.budget_max = self._money_to_int(direct_match.group(1))

    def _parse_districts(self, query: str, req: UserRequirements) -> None:
        aliases = {
            "亦庄": "北京经济技术开发区",
            "经开区": "北京经济技术开发区",
        }
        for district in DISTRICTS:
            if district in query and district not in req.preferred_districts:
                req.preferred_districts.append(district)
        for alias, district in aliases.items():
            if alias in query and district not in req.preferred_districts:
                req.preferred_districts.append(district)

    def _parse_room_types(self, query: str, req: UserRequirements) -> None:
        lower = query.lower()
        for room_type, keywords in ROOM_TYPE_KEYWORDS.items():
            if any(keyword.lower() in lower for keyword in keywords):
                req.preferred_room_types.append(room_type)

    def _parse_area(self, query: str, req: UserRequirements) -> None:
        range_match = re.search(r"(\d{2,3})\s*(?:-|到|至|~|～)\s*(\d{2,3})\s*(?:平|平米|㎡)", query)
        if range_match:
            req.min_area = int(range_match.group(1))
            req.max_area = int(range_match.group(2))
            return

        lower_match = re.search(r"(\d{2,3})\s*(?:平|平米|㎡)\s*(?:以上|起)", query)
        if lower_match:
            req.min_area = int(lower_match.group(1))
            return

        upper_match = re.search(r"(\d{2,3})\s*(?:平|平米|㎡)\s*(?:以下|以内)", query)
        if upper_match:
            req.max_area = int(upper_match.group(1))

    def _parse_tags(self, query: str, req: UserRequirements) -> None:
        for tag, keywords in TAG_KEYWORDS.items():
            if any(keyword in query for keyword in keywords) and tag not in req.must_have_tags:
                req.must_have_tags.append(tag)

        if "近地铁" in req.must_have_tags:
            req.near_subway = True
            req.max_distance_to_metro = 1000

        distance_match = re.search(r"(\d{2,4})\s*米.*地铁|地铁.*(\d{2,4})\s*米", query)
        if distance_match:
            value = next((group for group in distance_match.groups() if group), None)
            if value:
                req.near_subway = True
                req.max_distance_to_metro = int(value)

    def _parse_locations(self, query: str, req: UserRequirements) -> None:
        for item in KNOWN_LOCATIONS:
            if item in query and item not in req.preferred_locations:
                req.preferred_locations.append(item)

    def _inherit_previous(
        self,
        query: str,
        req: UserRequirements,
        previous: UserRequirements | None,
    ) -> None:
        if previous is None:
            return

        inherit_keywords = ["再推荐", "还有吗", "换几个", "继续", "同预算"]
        cheaper_keywords = ["便宜一点", "再便宜", "太贵了", "预算低一点"]

        if any(keyword in query for keyword in inherit_keywords):
            if not req.preferred_districts:
                req.preferred_districts = previous.preferred_districts.copy()
            if not req.preferred_room_types:
                req.preferred_room_types = previous.preferred_room_types.copy()
            if req.budget_min is None and req.budget_max is None:
                req.budget_min = previous.budget_min
                req.budget_max = previous.budget_max
            if not req.must_have_tags:
                req.must_have_tags = previous.must_have_tags.copy()
            if not req.preferred_locations:
                req.preferred_locations = previous.preferred_locations.copy()
            if not req.near_subway:
                req.near_subway = previous.near_subway
                req.max_distance_to_metro = previous.max_distance_to_metro

        if any(keyword in query for keyword in cheaper_keywords):
            if req.budget_max is None and previous.budget_max is not None:
                req.budget_max = max(1500, previous.budget_max - 1000)
            if req.budget_min is None and previous.budget_min is not None:
                req.budget_min = max(1000, previous.budget_min - 1000)
            if not req.preferred_districts:
                req.preferred_districts = previous.preferred_districts.copy()
            if not req.preferred_room_types:
                req.preferred_room_types = previous.preferred_room_types.copy()

    @staticmethod
    def _money_to_int(token: str) -> int:
        raw = token.strip()
        lower = raw.lower()
        if lower.endswith("k"):
            return int(float(lower[:-1]) * 1000)
        if lower.endswith("w"):
            return int(float(lower[:-1]) * 10000)
        if raw.endswith("千"):
            return int(float(raw[:-1]) * 1000)
        if raw.endswith("万"):
            return int(float(raw[:-1]) * 10000)
        return int(float(raw))
