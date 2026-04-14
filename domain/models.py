from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class RoomType(str, Enum):
    STUDIO = "studio"
    ONE_BEDROOM = "1bedroom"
    TWO_BEDROOM = "2bedroom"
    THREE_BEDROOM = "3bedroom"


ROOM_TYPE_DISPLAY = {
    RoomType.STUDIO: "开间",
    RoomType.ONE_BEDROOM: "一室一厅",
    RoomType.TWO_BEDROOM: "两室一厅",
    RoomType.THREE_BEDROOM: "三室一厅",
}


@dataclass
class TransportInfo:
    nearest_metro: Optional[str] = None
    metro_distance: Optional[int] = None
    commute_hint: str = ""
    transport_score: float = 0.0


@dataclass
class FacilityInfo:
    nearby: list[str] = field(default_factory=list)
    facility_score: float = 0.0


@dataclass
class RentalListing:
    listing_id: str
    title: str
    district: str
    location: str
    community: str
    rent_type: str
    room_type: RoomType
    layout: str
    area: int
    monthly_rent: int
    available_from: str
    orientation: str = ""
    floor_level: str = ""
    image_url: str = ""
    tags: list[str] = field(default_factory=list)
    highlight: str = ""
    source: str = "demo_feed"
    source_url: str = ""
    transport: TransportInfo = field(default_factory=TransportInfo)
    facilities: FacilityInfo = field(default_factory=FacilityInfo)
    match_score: float = 0.0
    reason: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RentalListing":
        return cls(
            listing_id=str(data["listing_id"]),
            title=str(data["title"]),
            district=str(data["district"]),
            location=str(data["location"]),
            community=str(data.get("community", "")),
            rent_type=str(data["rent_type"]),
            room_type=RoomType(data["room_type"]),
            layout=str(data.get("layout", "")),
            area=int(data["area"]),
            monthly_rent=int(data["monthly_rent"]),
            available_from=str(data["available_from"]),
            orientation=str(data.get("orientation", "")),
            floor_level=str(data.get("floor_level", "")),
            image_url=str(data.get("image_url", "")),
            tags=list(data.get("tags", [])),
            highlight=str(data.get("highlight", "")),
            source=str(data.get("source", "demo_feed")),
            source_url=str(data.get("source_url", "")),
            transport=TransportInfo(**data.get("transport", {})),
            facilities=FacilityInfo(**data.get("facilities", {})),
        )


@dataclass
class UserRequirements:
    raw_query: str = ""
    city: str = "北京"
    budget_min: Optional[int] = None
    budget_max: Optional[int] = None
    preferred_districts: list[str] = field(default_factory=list)
    preferred_locations: list[str] = field(default_factory=list)
    preferred_room_types: list[RoomType] = field(default_factory=list)
    min_area: Optional[int] = None
    max_area: Optional[int] = None
    near_subway: bool = False
    max_distance_to_metro: Optional[int] = None
    must_have_tags: list[str] = field(default_factory=list)
    special_requirements: list[str] = field(default_factory=list)
    applied_context: list[str] = field(default_factory=list)


@dataclass
class KnowledgeHit:
    title: str
    snippet: str
    source: str


@dataclass
class RecommendationResult:
    query: str
    parsed_requirements: UserRequirements
    total_found: int
    recommendations: list[RentalListing]
    analysis_summary: str
    next_steps: list[str] = field(default_factory=list)
    knowledge_hits: list[KnowledgeHit] = field(default_factory=list)
    thoughts: list[str] = field(default_factory=list)
    compare_rows: list[dict[str, Any]] = field(default_factory=list)
    relaxation_notes: list[str] = field(default_factory=list)


@dataclass
class UserProfile:
    user_id: str
    budget_history: list[dict[str, Optional[int]]] = field(default_factory=list)
    preferred_districts: list[str] = field(default_factory=list)
    district_frequency: dict[str, int] = field(default_factory=dict)
    preferred_room_types: list[str] = field(default_factory=list)
    room_type_frequency: dict[str, int] = field(default_factory=dict)
    preferred_tags: list[str] = field(default_factory=list)
    favorite_listing_ids: list[str] = field(default_factory=list)
    conversation_history: list[dict[str, str]] = field(default_factory=list)
