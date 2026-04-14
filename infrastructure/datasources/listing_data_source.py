from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Optional

from homeagent.config import DEMO_LISTINGS_PATH, PROCESSED_LISTINGS_PATH
from homeagent.domain.models import RentalListing, RoomType


class DemoDataSource:
    def __init__(self, data_path: Path | str = DEMO_LISTINGS_PATH) -> None:
        self.data_path = Path(data_path)
        self._listings = self._load_listings()
        self._cache = {item.listing_id: item for item in self._listings}

    def _load_listings(self) -> list[RentalListing]:
        with open(self.data_path, "r", encoding="utf-8") as file:
            raw = json.load(file)
        return [RentalListing.from_dict(item) for item in raw]

    def all_listings(self) -> list[RentalListing]:
        return [deepcopy(item) for item in self._listings]

    def search(self, params: dict) -> list[RentalListing]:
        scored_results: list[tuple[float, RentalListing]] = []

        districts = set(params.get("districts", []))
        room_types = {RoomType(value) for value in params.get("room_types", [])}
        locations = params.get("locations", [])
        price_min = params.get("price_min")
        price_max = params.get("price_max")
        area_min = params.get("area_min")
        area_max = params.get("area_max")
        max_distance = params.get("max_distance_to_metro")
        must_have_tags = set(params.get("must_have_tags", []))
        rent_type = params.get("rent_type")
        limit = int(params.get("limit", 20))

        for listing in self._listings:
            recall_score = 0.0

            if districts:
                recall_score += 40 if listing.district in districts else -22

            if room_types:
                recall_score += 35 if listing.room_type in room_types else -22

            if locations:
                if any(location in listing.location or location in listing.title for location in locations):
                    recall_score += 24
                else:
                    recall_score -= 8

            if price_min is not None or price_max is not None:
                if price_min is not None and listing.monthly_rent < price_min:
                    recall_score -= min(6, (price_min - listing.monthly_rent) / 400)
                if price_max is not None:
                    if listing.monthly_rent <= price_max:
                        recall_score += 18
                    else:
                        recall_score -= min(18, (listing.monthly_rent - price_max) / 250)

            if area_min is not None or area_max is not None:
                if area_min is not None and listing.area >= area_min:
                    recall_score += 8
                elif area_min is not None:
                    recall_score -= 5
                if area_max is not None and listing.area <= area_max:
                    recall_score += 6
                elif area_max is not None:
                    recall_score -= 4

            if max_distance is not None:
                distance = listing.transport.metro_distance
                if distance is None:
                    recall_score -= 10
                elif distance <= max_distance:
                    recall_score += 15
                else:
                    recall_score -= min(15, (distance - max_distance) / 180)

            if must_have_tags:
                matched_tags = must_have_tags & set(listing.tags)
                recall_score += len(matched_tags) * 8
                if not matched_tags:
                    recall_score -= 6

            if rent_type:
                recall_score += 12 if listing.rent_type == rent_type else -18

            recall_score += listing.transport.transport_score * 0.5
            recall_score += listing.facilities.facility_score * 0.3

            scored_results.append((recall_score, deepcopy(listing)))

        scored_results.sort(key=lambda item: item[0], reverse=True)
        return [listing for _, listing in scored_results[:limit]]

    def get_by_id(self, listing_id: str) -> Optional[RentalListing]:
        listing = self._cache.get(listing_id)
        return deepcopy(listing) if listing else None


def get_data_source() -> DemoDataSource:
    if Path(PROCESSED_LISTINGS_PATH).exists():
        return DemoDataSource(PROCESSED_LISTINGS_PATH)
    return DemoDataSource(DEMO_LISTINGS_PATH)
