from __future__ import annotations

from homeagent.domain.models import ROOM_TYPE_DISPLAY, RentalListing, UserRequirements


class DecisionEngine:
    def __init__(self) -> None:
        self.weights = {
            "budget": 0.35,
            "location": 0.2,
            "room_type": 0.2,
            "subway": 0.15,
            "tags": 0.1,
        }

    def evaluate(
        self,
        listings: list[RentalListing],
        requirements: UserRequirements,
    ) -> list[RentalListing]:
        ranked: list[RentalListing] = []
        for listing in listings:
            budget_score = self._score_budget(listing, requirements)
            location_score = self._score_location(listing, requirements)
            room_type_score = self._score_room_type(listing, requirements)
            subway_score = self._score_subway(listing, requirements)
            tags_score = self._score_tags(listing, requirements)

            total = (
                budget_score * self.weights["budget"]
                + location_score * self.weights["location"]
                + room_type_score * self.weights["room_type"]
                + subway_score * self.weights["subway"]
                + tags_score * self.weights["tags"]
            )
            listing.match_score = round(total, 2)
            listing.reason = self.generate_reason(listing, requirements)
            ranked.append(listing)

        ranked.sort(key=lambda item: item.match_score, reverse=True)
        return ranked

    def _score_budget(self, listing: RentalListing, requirements: UserRequirements) -> float:
        if requirements.budget_max is None:
            return 7.0
        if listing.monthly_rent <= requirements.budget_max:
            if requirements.budget_max == 0:
                return 10.0
            ratio = listing.monthly_rent / requirements.budget_max
            return max(6.5, 10 - ratio * 2)
        over_ratio = (listing.monthly_rent - requirements.budget_max) / requirements.budget_max
        return max(0.0, 6 - over_ratio * 10)

    def _score_location(self, listing: RentalListing, requirements: UserRequirements) -> float:
        score = 5.0
        if requirements.preferred_districts:
            if listing.district in requirements.preferred_districts:
                score += 3
            else:
                score -= 2
        if requirements.preferred_locations:
            if any(item in listing.location or item in listing.title for item in requirements.preferred_locations):
                score += 2
        return max(0.0, min(10.0, score))

    def _score_room_type(self, listing: RentalListing, requirements: UserRequirements) -> float:
        if not requirements.preferred_room_types:
            return 7.0
        return 10.0 if listing.room_type in requirements.preferred_room_types else 2.0

    def _score_subway(self, listing: RentalListing, requirements: UserRequirements) -> float:
        if not requirements.near_subway:
            return 7.0
        distance = listing.transport.metro_distance
        if distance is None:
            return 1.0
        max_distance = requirements.max_distance_to_metro or 1000
        if distance <= max_distance:
            return 10.0
        if distance <= max_distance * 1.5:
            return 6.5
        return 2.0

    def _score_tags(self, listing: RentalListing, requirements: UserRequirements) -> float:
        if not requirements.must_have_tags:
            return 7.0
        matched = len(set(requirements.must_have_tags) & set(listing.tags))
        return min(10.0, 4.0 + matched * 2.0)

    def generate_reason(self, listing: RentalListing, requirements: UserRequirements) -> str:
        reasons: list[str] = []

        if requirements.budget_max is not None and listing.monthly_rent <= requirements.budget_max:
            reasons.append(f"租金 {listing.monthly_rent} 元在预算内")
        if requirements.preferred_districts and listing.district in requirements.preferred_districts:
            reasons.append(f"位于目标区域 {listing.district}")
        if requirements.preferred_room_types and listing.room_type in requirements.preferred_room_types:
            reasons.append(f"户型符合 {ROOM_TYPE_DISPLAY[listing.room_type]}")
        if requirements.near_subway and listing.transport.metro_distance is not None:
            reasons.append(f"距地铁约 {listing.transport.metro_distance} 米")

        matched_tags = [tag for tag in requirements.must_have_tags if tag in listing.tags]
        if matched_tags:
            reasons.append(f"命中标签 {', '.join(matched_tags[:2])}")

        if not reasons:
            reasons.append("综合条件均衡，适合作为备选")

        return "；".join(reasons[:4])
