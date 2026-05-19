from __future__ import annotations

from dataclasses import dataclass, field

from homeagent.domain.models import ROOM_TYPE_DISPLAY, RentalListing, RoomType, UserRequirements


@dataclass
class ListingDecisionReport:
    highlights: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    suitable_for: list[str] = field(default_factory=list)
    viewing_questions: list[str] = field(default_factory=list)


@dataclass
class CompareDecisionReport:
    verdict: str
    winners: list[str] = field(default_factory=list)
    tradeoffs: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)


class DecisionReportService:
    def build_listing_report(
        self,
        listing: RentalListing,
        requirements: UserRequirements | None = None,
    ) -> ListingDecisionReport:
        return ListingDecisionReport(
            highlights=self._listing_highlights(listing, requirements),
            risks=self._listing_risks(listing, requirements),
            suitable_for=self._suitable_for(listing),
            viewing_questions=self._viewing_questions(listing),
        )

    def build_compare_report(self, listings: list[RentalListing]) -> CompareDecisionReport:
        if len(listings) < 2:
            return CompareDecisionReport(
                verdict="至少加入 2 套房源后，巢选会自动给出横向对比结论。",
                next_steps=["先从推荐列表中把犹豫的房源加入对比。"],
            )

        cheapest = min(listings, key=lambda item: item.monthly_rent)
        largest = max(listings, key=lambda item: item.area)
        best_match = max(listings, key=lambda item: item.match_score)
        best_value = min(listings, key=lambda item: item.monthly_rent / max(item.area, 1))
        metro_listings = [item for item in listings if item.transport.metro_distance is not None]
        closest = min(metro_listings, key=lambda item: item.transport.metro_distance or 99999) if metro_listings else None

        verdict = (
            f"综合看，{best_match.title} 的匹配分最高；"
            f"{cheapest.title} 租金最低；"
            f"{best_value.title} 的单位面积成本更友好。"
        )
        if closest is not None:
            verdict += f" 如果最看重地铁距离，可以优先看 {closest.title}。"

        winners = [
            f"预算优先：{cheapest.title}，{cheapest.monthly_rent} 元/月。",
            f"空间优先：{largest.title}，{largest.area}㎡。",
            f"综合匹配：{best_match.title}，匹配分 {best_match.match_score:.1f}。",
            f"性价比：{best_value.title}，约 {best_value.monthly_rent / max(best_value.area, 1):.0f} 元/㎡。",
        ]
        if closest is not None:
            winners.append(f"通勤优先：{closest.title}，距地铁约 {closest.transport.metro_distance} 米。")

        tradeoffs = self._compare_tradeoffs(listings)
        next_steps = [
            "优先约看胜出维度最多的一套，再准备一套价格更低的备选。",
            "看房时重点确认采光、噪音、实际地铁步行时间和付款方式。",
            "如果仍然纠结，可以继续把预算、地铁距离或商圈权重说清楚，让系统重新排序。",
        ]
        return CompareDecisionReport(verdict=verdict, winners=winners, tradeoffs=tradeoffs, next_steps=next_steps)

    def _listing_highlights(
        self,
        listing: RentalListing,
        requirements: UserRequirements | None,
    ) -> list[str]:
        highlights: list[str] = []
        if requirements and requirements.budget_max and listing.monthly_rent <= requirements.budget_max:
            saved = requirements.budget_max - listing.monthly_rent
            highlights.append(f"租金在预算内，比预算上限低 {saved} 元。")
        elif listing.monthly_rent <= 6000:
            highlights.append("租金处在北京核心租房需求里相对克制的区间。")

        if listing.transport.metro_distance is not None:
            if listing.transport.metro_distance <= 500:
                highlights.append(f"距地铁约 {listing.transport.metro_distance} 米，步行友好。")
            elif listing.transport.metro_distance <= 1000:
                highlights.append(f"距地铁约 {listing.transport.metro_distance} 米，通勤可控。")

        if listing.area >= 90:
            highlights.append(f"{listing.area}㎡ 空间充足，适合多人合住或家庭。")
        elif listing.area >= 55 and listing.room_type in {RoomType.ONE_BEDROOM, RoomType.TWO_BEDROOM}:
            highlights.append("面积和户型比例较均衡，居住功能完整。")

        matched_tags = [tag for tag in ["精装", "集中供暖", "随时看房", "官方核验", "可月付"] if tag in listing.tags]
        if matched_tags:
            highlights.append(f"标签亮点：{'、'.join(matched_tags[:3])}。")
        if listing.highlight and listing.highlight not in "；".join(highlights):
            highlights.append(listing.highlight)
        return highlights[:5] or ["综合条件均衡，适合作为候选房源。"]

    @staticmethod
    def _listing_risks(
        listing: RentalListing,
        requirements: UserRequirements | None,
    ) -> list[str]:
        risks: list[str] = []
        if requirements and requirements.budget_max and listing.monthly_rent > requirements.budget_max:
            risks.append(f"租金超过预算 {listing.monthly_rent - requirements.budget_max} 元，需要确认是否能接受。")
        if listing.transport.metro_distance is None:
            risks.append("地铁距离未标注，建议实测步行时间。")
        elif listing.transport.metro_distance > 1000:
            risks.append(f"距地铁约 {listing.transport.metro_distance} 米，通勤步行成本偏高。")
        if not listing.orientation:
            risks.append("朝向信息缺失，看房时要重点确认采光。")
        if not listing.floor_level:
            risks.append("楼层信息缺失，需要确认电梯、噪音和采光情况。")
        if "官方核验" not in listing.tags:
            risks.append("未看到官方核验标签，建议核验房源真实性和出租资质。")
        return risks[:5] or ["暂无明显硬伤，建议看房时确认细节。"]

    @staticmethod
    def _suitable_for(listing: RentalListing) -> list[str]:
        room_label = listing.layout or ROOM_TYPE_DISPLAY[listing.room_type]
        suitable: list[str] = []
        if listing.room_type == RoomType.STUDIO:
            suitable.append("适合单人居住或通勤过渡。")
        elif listing.room_type == RoomType.ONE_BEDROOM:
            suitable.append("适合单人或情侣，隐私和功能区更完整。")
        elif listing.room_type == RoomType.TWO_BEDROOM:
            suitable.append("适合情侣、朋友合租或小家庭。")
        else:
            suitable.append("适合多人合租或家庭居住。")
        if "可月付" in listing.tags:
            suitable.append("适合现金流更看重灵活性的租客。")
        if "近地铁" in listing.tags:
            suitable.append("适合高频通勤、希望降低步行成本的人。")
        suitable.append(f"当前户型为 {room_label}，看房时可重点确认动线和储物空间。")
        return suitable[:4]

    @staticmethod
    def _viewing_questions(listing: RentalListing) -> list[str]:
        questions = [
            "押金、付款周期、中介费和服务费分别是多少？",
            "水电燃气、供暖、网络费用按民用还是商用标准收取？",
            "家具家电损坏责任如何约定，是否写进合同？",
            "房东是否允许转租、养宠、短租或提前退租？",
        ]
        if listing.transport.metro_distance is not None:
            questions.insert(0, f"从小区门口到 {listing.transport.nearest_metro or '地铁站'} 实际步行需要多久？")
        return questions[:5]

    @staticmethod
    def _compare_tradeoffs(listings: list[RentalListing]) -> list[str]:
        rents = [item.monthly_rent for item in listings]
        areas = [item.area for item in listings]
        tradeoffs: list[str] = []
        if max(rents) - min(rents) >= 1000:
            tradeoffs.append(f"租金差距达到 {max(rents) - min(rents)} 元/月，低价房源更值得先约看。")
        if max(areas) - min(areas) >= 20:
            tradeoffs.append(f"面积差距达到 {max(areas) - min(areas)}㎡，需要权衡空间和租金。")
        unknown_metro = [item.title for item in listings if item.transport.metro_distance is None]
        if unknown_metro:
            tradeoffs.append(f"{unknown_metro[0]} 缺少地铁距离，通勤判断不完整。")
        far_metro = [item for item in listings if (item.transport.metro_distance or 0) > 1000]
        if far_metro:
            tradeoffs.append(f"{far_metro[0].title} 距地铁较远，适合能接受骑行或公交接驳的人。")
        return tradeoffs[:4] or ["当前几套房源差异不大，建议用实际看房体验做最后判断。"]
