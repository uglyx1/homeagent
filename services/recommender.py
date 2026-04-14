from __future__ import annotations

from homeagent.domain.models import ROOM_TYPE_DISPLAY, RecommendationResult, RentalListing


class Recommender:
    def format_recommendation_text(self, result: RecommendationResult) -> str:
        lines: list[str] = []
        lines.append("=" * 72)
        lines.append("巢选租房推荐报告")
        lines.append("=" * 72)
        lines.append("")
        lines.append("需求摘要")
        lines.append(f"- 原始问题: {result.query}")
        lines.append(f"- 分析总结: {result.analysis_summary}")
        lines.append(f"- 候选房源数: {result.total_found}")
        if result.parsed_requirements.applied_context:
            lines.append(f"- 自动补充偏好: {'；'.join(result.parsed_requirements.applied_context)}")
        lines.append(f"- 知识库命中: {len(result.knowledge_hits)} 条")
        if result.relaxation_notes:
            lines.append(f"- 已自动放宽条件: {'；'.join(result.relaxation_notes)}")

        lines.append("")
        lines.append(f"Top {len(result.recommendations)} 房源")
        for index, listing in enumerate(result.recommendations, start=1):
            lines.extend(self._format_listing(index, listing))

        if result.compare_rows:
            lines.append("")
            lines.append("房源对比结论")
            lines.extend(self._format_compare_rows(result.compare_rows))

        if result.knowledge_hits:
            lines.append("")
            lines.append("知识参考")
            for hit in result.knowledge_hits:
                lines.append(f"- {hit.title} | {hit.source}")
                lines.append(f"  {hit.snippet}")

        if result.next_steps:
            lines.append("")
            lines.append("下一步建议")
            for index, step in enumerate(result.next_steps, start=1):
                lines.append(f"{index}. {step}")

        if result.thoughts:
            lines.append("")
            lines.append("Agent 思考轨迹")
            for thought in result.thoughts:
                lines.append(f"- {thought}")

        return "\n".join(lines)

    @staticmethod
    def format_listing_detail(listing: RentalListing) -> str:
        lines = [
            "=" * 72,
            f"房源详情 [{listing.listing_id}]",
            "=" * 72,
            f"标题: {listing.title}",
            f"区域: {listing.district}{listing.location}",
            f"小区: {listing.community or '未标注'}",
            f"租赁方式: {listing.rent_type}",
            f"户型: {listing.layout or ROOM_TYPE_DISPLAY[listing.room_type]}",
            f"面积: {listing.area}㎡",
            f"租金: {listing.monthly_rent} 元/月",
            f"朝向: {listing.orientation or '未知'}",
            f"楼层: {listing.floor_level or '未标注'}",
            f"入住时间: {listing.available_from or '未标注'}",
            f"交通: {listing.transport.nearest_metro or '未标注地铁站'} / "
            f"{listing.transport.metro_distance or '未知'} 米",
            f"标签: {', '.join(listing.tags) if listing.tags else '无'}",
            f"亮点: {listing.highlight or '无'}",
            f"来源: {listing.source}",
            f"链接: {listing.source_url or '无'}",
        ]
        return "\n".join(lines)

    @staticmethod
    def _format_listing(index: int, listing: RentalListing) -> list[str]:
        return [
            "",
            f"{index}. [{listing.listing_id}] {listing.title}",
            f"   区域: {listing.district}{listing.location}",
            f"   小区: {listing.community or '未标注'}",
            f"   租金: {listing.monthly_rent} 元/月",
            f"   户型: {listing.layout or ROOM_TYPE_DISPLAY[listing.room_type]} | "
            f"{listing.area}㎡ | {listing.rent_type}",
            f"   朝向/楼层: {listing.orientation or '未知'} | {listing.floor_level or '未标注'}",
            f"   交通: {listing.transport.nearest_metro or '无'} | "
            f"距地铁 {listing.transport.metro_distance or '未知'} 米 | {listing.transport.commute_hint}",
            f"   标签: {', '.join(listing.tags) if listing.tags else '无'}",
            f"   匹配分: {listing.match_score}",
            f"   推荐理由: {listing.reason}",
            f"   亮点: {listing.highlight}",
            f"   链接: {listing.source_url or '无'}",
        ]

    @staticmethod
    def _format_compare_rows(compare_rows: list[dict]) -> list[str]:
        lines: list[str] = []
        if len(compare_rows) < 2:
            lines.append("- 当前可对比房源不足 2 套，建议先放宽条件获取更多候选。")
            return lines

        cheapest = min(compare_rows, key=lambda item: item["monthly_rent"])
        largest = max(compare_rows, key=lambda item: item["area"])
        closest = min(compare_rows, key=lambda item: item["metro_distance"] or 99999)

        lines.append(f"- 最便宜: {cheapest['title']}，{cheapest['monthly_rent']} 元/月")
        lines.append(f"- 面积最大: {largest['title']}，{largest['area']}㎡")
        if closest["metro_distance"] is None:
            lines.append("- 地铁距离: 当前对比房源里没有完整的地铁距离数据。")
        else:
            lines.append(f"- 离地铁最近: {closest['title']}，约 {closest['metro_distance']} 米")
        return lines
