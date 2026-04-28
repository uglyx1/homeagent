from __future__ import annotations

import base64
import html

import streamlit as st

from homeagent.app.agent import HouseRentingAgentV2
from homeagent.domain.models import ROOM_TYPE_DISPLAY, RecommendationResult, RentalListing
from homeagent.interfaces.web.data import fetch_image_bytes
from homeagent.interfaces.web.insights import render_market_insights


def _safe(value: object) -> str:
    return html.escape(str(value)) if value is not None else ""


def _money(value: int | float | None) -> str:
    if value is None:
        return "未知"
    return f"{int(value)} 元/月"


def _image_mime(image_bytes: bytes) -> str:
    if image_bytes.startswith(b"\x89PNG"):
        return "image/png"
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


def _image_data_uri(url: str) -> str:
    image_bytes = fetch_image_bytes(url)
    if not image_bytes:
        return ""
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f"data:{_image_mime(image_bytes)};base64,{encoded}"


def toggle_compare(listing_id: str) -> None:
    compare_ids = st.session_state.compare_ids
    if listing_id in compare_ids:
        compare_ids.remove(listing_id)
    else:
        compare_ids.append(listing_id)


def render_requirements(result: RecommendationResult) -> None:
    requirements = result.parsed_requirements
    room_types = [ROOM_TYPE_DISPLAY[item] for item in requirements.preferred_room_types]
    st.markdown("#### 需求解析")
    st.json(
        {
            "预算上限": requirements.budget_max,
            "区域": requirements.preferred_districts,
            "商圈": requirements.preferred_locations,
            "户型": room_types,
            "面积下限": requirements.min_area,
            "面积上限": requirements.max_area,
            "近地铁": requirements.near_subway,
            "地铁距离上限": requirements.max_distance_to_metro,
            "标签": requirements.must_have_tags,
            "自动继承上下文": requirements.applied_context,
        }
    )


def render_listing_image(listing: RentalListing, height: int = 210) -> None:
    if listing.image_url:
        image_bytes = fetch_image_bytes(listing.image_url)
        if image_bytes:
            st.image(image_bytes, use_container_width=True)
            return
        st.markdown(f'<div class="empty-photo" style="height:{height}px;">图片加载失败</div>', unsafe_allow_html=True)
        return
    st.markdown(f'<div class="empty-photo" style="height:{height}px;">暂无房源图片</div>', unsafe_allow_html=True)


def render_summary_shell(result: RecommendationResult) -> None:
    top = result.recommendations[0] if result.recommendations else None
    top_title = top.title if top else "还没有找到合适房源"
    avg_rent = round(sum(item.monthly_rent for item in result.recommendations) / len(result.recommendations)) if result.recommendations else None
    best_score = max((item.match_score for item in result.recommendations), default=0)
    district_count = len({item.district for item in result.recommendations})
    st.markdown(
        f"""
        <div class="result-summary-grid">
            <div class="summary-card primary">
                <div class="result-summary-kicker">本轮结果</div>
                <div class="result-summary-title">{_safe(result.analysis_summary)}</div>
                <div class="result-summary-sub">当前最优推荐：{_safe(top_title)}</div>
                <div class="result-pill">{len(result.knowledge_hits)} 条知识参考 · {len(result.relaxation_notes)} 条自动放宽</div>
            </div>
            <div class="summary-card">
                <div class="summary-number">{len(result.recommendations)}</div>
                <div class="summary-label">推荐房源</div>
            </div>
            <div class="summary-card">
                <div class="summary-number">{_money(avg_rent).replace('/月', '')}</div>
                <div class="summary-label">平均预算位</div>
            </div>
            <div class="summary-card">
                <div class="summary-number">{best_score:.1f}</div>
                <div class="summary-label">最高匹配分 · 覆盖 {district_count} 区</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_listing_actions(agent: HouseRentingAgentV2, listing: RentalListing) -> None:
    is_compared = listing.listing_id in st.session_state.compare_ids
    favorite_ids = set(agent.get_favorite_listing_ids())
    is_favorited = listing.listing_id in favorite_ids

    action_cols = st.columns(4)
    with action_cols[0]:
        if st.button("详情", key=f"detail_{listing.listing_id}", use_container_width=True):
            st.session_state.selected_listing_id = listing.listing_id
    with action_cols[1]:
        if st.button("移出对比" if is_compared else "加入对比", key=f"compare_{listing.listing_id}", use_container_width=True):
            toggle_compare(listing.listing_id)
            st.rerun()
    with action_cols[2]:
        if st.button("已收藏" if is_favorited else "收藏", key=f"favorite_{listing.listing_id}", use_container_width=True):
            if not is_favorited:
                agent.record_feedback(listing.listing_id)
            st.rerun()
    with action_cols[3]:
        if listing.source_url:
            st.link_button("原链接", listing.source_url, use_container_width=True)


def render_listing_info(listing: RentalListing) -> None:
    tags = "".join(f'<span class="tag-pill">{tag}</span>' for tag in listing.tags[:6])
    layout = listing.layout or ROOM_TYPE_DISPLAY[listing.room_type]
    metro_name = listing.transport.nearest_metro or "未标注"
    metro_distance = f"{listing.transport.metro_distance} 米" if listing.transport.metro_distance else "未知"
    st.markdown(
        f"""
        <div class="listing-title">{listing.title}</div>
        <div class="listing-price-line">{listing.monthly_rent} 元/月</div>
        <div class="listing-meta">
            {layout} · {listing.area}㎡ · {listing.rent_type}<br/>
            {listing.district} · {listing.location} · {listing.community or '未标注小区'}<br/>
            朝向/楼层：{listing.orientation or '未知'} / {listing.floor_level or '未标注'}<br/>
            地铁：{metro_name} / {metro_distance}<br/>
            匹配分：{listing.match_score}<br/>
            推荐理由：{listing.reason}
        </div>
        <div class="tag-row">{tags}</div>
        """,
        unsafe_allow_html=True,
    )


def render_listing_card(agent: HouseRentingAgentV2, index: int, listing: RentalListing) -> None:
    image_uri = _image_data_uri(listing.image_url) if listing.image_url else ""
    if image_uri:
        image_html = f'<img src="{image_uri}" alt="{_safe(listing.title)}" />'
    else:
        image_html = '<div class="empty-photo">暂无房源图片</div>'

    layout = listing.layout or ROOM_TYPE_DISPLAY[listing.room_type]
    metro_name = listing.transport.nearest_metro or "未标注"
    metro_distance = f"{listing.transport.metro_distance} 米" if listing.transport.metro_distance else "未知"
    community = listing.community or "未标注小区"
    floor = listing.floor_level or "未标注"
    orientation = listing.orientation or "未知"
    tags = "".join(f'<span class="tag-pill">{_safe(tag)}</span>' for tag in listing.tags[:6])

    favorite_ids = set(agent.get_favorite_listing_ids())
    status_items = [f"匹配 {listing.match_score:.1f}"]
    if listing.listing_id in st.session_state.compare_ids:
        status_items.append("已入对比")
    if listing.listing_id in favorite_ids:
        status_items.append("已收藏")
    if listing.highlight:
        status_items.append(listing.highlight)
    statuses = "".join(f'<span class="listing-status">{_safe(item)}</span>' for item in status_items)

    st.markdown(
        f"""
        <div class="listing-card">
            <div class="listing-media">
                {image_html}
                <div class="listing-rank">推荐 {index}</div>
            </div>
            <div class="listing-body">
                <div>
                    <div class="listing-heading">
                        <div class="listing-title">{_safe(listing.title)}</div>
                        <div class="listing-price-line">{_money(listing.monthly_rent)}</div>
                    </div>
                    <div class="listing-status-row">{statuses}</div>
                </div>
                <div class="listing-meta-grid">
                    <div class="listing-meta-item">
                        <div class="listing-meta-label">户型面积</div>
                        <div class="listing-meta-value">{_safe(layout)} · {listing.area}㎡</div>
                    </div>
                    <div class="listing-meta-item">
                        <div class="listing-meta-label">小区商圈</div>
                        <div class="listing-meta-value">{_safe(community)} · {_safe(listing.location)}</div>
                    </div>
                    <div class="listing-meta-item">
                        <div class="listing-meta-label">地铁距离</div>
                        <div class="listing-meta-value">{_safe(metro_name)} · {_safe(metro_distance)}</div>
                    </div>
                    <div class="listing-meta-item">
                        <div class="listing-meta-label">楼层朝向</div>
                        <div class="listing-meta-value">{_safe(floor)} · {_safe(orientation)}</div>
                    </div>
                </div>
                <div class="listing-reason">{_safe(listing.reason)}</div>
                <div class="tag-row">{tags}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_listing_actions(agent, listing)


def render_selected_detail(agent: HouseRentingAgentV2) -> None:
    if not st.session_state.selected_listing_id:
        st.markdown('<div class="saved-note">先在推荐列表里点一套房源，这里会显示更完整的详情。</div>', unsafe_allow_html=True)
        return
    listing = agent.get_listing(st.session_state.selected_listing_id)
    if listing is None:
        st.warning("当前房源详情不可用。")
        return
    render_listing_image(listing, height=240)
    st.markdown('<div class="detail-panel">', unsafe_allow_html=True)
    st.code(agent.get_listing_detail_text(listing.listing_id), language=None)
    st.markdown("</div>", unsafe_allow_html=True)


def render_compare_section(agent: HouseRentingAgentV2) -> None:
    compare_ids = st.session_state.compare_ids
    if not compare_ids:
        st.markdown('<div class="saved-note">把你犹豫的房源加入对比，这里会自动生成横向对比表。</div>', unsafe_allow_html=True)
        return
    compare_rows = agent.get_compare_rows(compare_ids)
    if compare_rows:
        st.dataframe(compare_rows, use_container_width=True, hide_index=True)


def render_favorites_section(agent: HouseRentingAgentV2) -> None:
    favorites = agent.get_favorite_listings()
    if not favorites:
        st.markdown('<div class="saved-note">收藏夹还是空的。看到合适房源时点一下“收藏”，这里会一直保留。</div>', unsafe_allow_html=True)
        return
    for listing in reversed(favorites[-8:]):
        st.markdown(
            f"""
            <div class="favorite-line">
                <div class="favorite-title">{_safe(listing.title)}</div>
                <div class="favorite-meta">{_money(listing.monthly_rent)} · {_safe(listing.district)} · {_safe(listing.location)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_conversation_archive(agent: HouseRentingAgentV2) -> None:
    conversations = agent.get_recent_conversations(limit=8)
    if not conversations:
        st.markdown('<div class="saved-note">最近对话会沉淀在这里，方便回看筛选思路。</div>', unsafe_allow_html=True)
        return
    for item in reversed(conversations):
        st.markdown(
            f"""
            <div class="conversation-line">
                <div class="favorite-title">你：{_safe(item['query'])}</div>
                <div class="conversation-answer">巢选：{_safe(item['response'])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_knowledge_hits(result: RecommendationResult) -> None:
    if not result.knowledge_hits:
        st.caption("本轮没有额外的知识库命中。")
        return
    for hit in result.knowledge_hits:
        st.markdown(
            f"""
                <div class="knowledge-hit">
                <div class="knowledge-title">{_safe(hit.title)}</div>
                <div class="knowledge-snippet">{_safe(hit.snippet)}</div>
                <div class="knowledge-source">{_safe(hit.source)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_results(agent: HouseRentingAgentV2, result: RecommendationResult) -> None:
    st.markdown('<div class="result-shell">', unsafe_allow_html=True)
    render_summary_shell(result)

    tab_reco, tab_map, tab_detail, tab_saved, tab_parse = st.tabs(
        ["推荐房源", "地图/区域", "当前详情", "收藏/对比", "解析过程"]
    )

    with tab_reco:
        for index, listing in enumerate(result.recommendations, start=1):
            render_listing_card(agent, index, listing)

    with tab_map:
        render_market_insights(result, show_title=False)

    with tab_detail:
        render_selected_detail(agent)

    with tab_saved:
        section_left, section_right = st.columns(2, gap="large")
        with section_left:
            st.markdown("#### 对比列表")
            render_compare_section(agent)
        with section_right:
            st.markdown("#### 收藏夹")
            render_favorites_section(agent)
        st.markdown("#### 最近对话")
        render_conversation_archive(agent)

    with tab_parse:
        render_requirements(result)
        st.markdown("#### 知识参考")
        render_knowledge_hits(result)
        if result.next_steps:
            st.markdown("#### 下一步建议")
            for step in result.next_steps:
                st.markdown(f"- {step}")
        if result.thoughts:
            with st.expander("查看 Agent 执行轨迹", expanded=False):
                for thought in result.thoughts:
                    st.markdown(f"- {thought}")

    st.markdown("</div>", unsafe_allow_html=True)
