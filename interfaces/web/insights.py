from __future__ import annotations

from collections import defaultdict
from hashlib import md5

import pandas as pd
import pydeck as pdk
import streamlit as st

from homeagent.domain.models import RecommendationResult, RentalListing


DISTRICT_COORDS: dict[str, tuple[float, float]] = {
    "朝阳区": (39.9219, 116.4436),
    "海淀区": (39.9593, 116.2981),
    "丰台区": (39.8586, 116.2869),
    "东城区": (39.9288, 116.4160),
    "西城区": (39.9125, 116.3659),
    "石景山区": (39.9146, 116.2229),
    "北京经济技术开发区": (39.7960, 116.5060),
    "顺义区": (40.1301, 116.6542),
}

LOCATION_COORDS: dict[str, tuple[float, float]] = {
    "东直门": (39.9420, 116.4342),
    "青塔": (39.8805, 116.2535),
    "亦庄河西区": (39.8070, 116.5000),
    "五棵松": (39.9075, 116.2740),
    "双榆树": (39.9705, 116.3230),
    "鲁谷": (39.9070, 116.2240),
    "广安门": (39.8895, 116.3551),
    "顺义城": (40.1280, 116.6540),
    "蒲黄榆": (39.8648, 116.4333),
    "四惠": (39.9086, 116.4950),
    "方庄": (39.8655, 116.4310),
    "十里堡": (39.9220, 116.5010),
}

METRO_COORDS: dict[str, tuple[float, float]] = {
    "东直门": (39.9417, 116.4344),
    "郭庄子": (39.8807, 116.2522),
    "蒲黄榆": (39.8650, 116.4335),
    "四惠": (39.9082, 116.4952),
    "五棵松": (39.9073, 116.2738),
    "知春里": (39.9765, 116.3243),
}


def _base_coords(listing: RentalListing) -> tuple[float, float] | None:
    if listing.location in LOCATION_COORDS:
        return LOCATION_COORDS[listing.location]
    if listing.transport.nearest_metro in METRO_COORDS:
        return METRO_COORDS[listing.transport.nearest_metro]
    return DISTRICT_COORDS.get(listing.district)


def _jitter(seed: str) -> tuple[float, float]:
    digest = md5(seed.encode("utf-8")).hexdigest()
    lat_raw = int(digest[:4], 16) / 65535
    lon_raw = int(digest[4:8], 16) / 65535
    lat_delta = (lat_raw - 0.5) * 0.016
    lon_delta = (lon_raw - 0.5) * 0.02
    return lat_delta, lon_delta


def _score_color(score: float) -> list[int]:
    if score >= 8.5:
        return [52, 152, 219, 220]
    if score >= 7.8:
        return [79, 140, 255, 205]
    if score >= 7.0:
        return [116, 172, 255, 190]
    return [168, 197, 255, 178]


def _radius(score: float, rank: int) -> int:
    base = 80 + max(score - 6.0, 0) * 28
    bonus = max(0, 4 - rank) * 24
    return int((base + bonus) * 10)


def build_map_rows(listings: list[RentalListing]) -> pd.DataFrame:
    rows: list[dict] = []
    for index, listing in enumerate(listings, start=1):
        coords = _base_coords(listing)
        if coords is None:
            continue
        lat_delta, lon_delta = _jitter(listing.listing_id)
        metro_name = listing.transport.nearest_metro or "未标注"
        metro_distance = f"{listing.transport.metro_distance} 米" if listing.transport.metro_distance else "未知"
        rows.append(
            {
                "lat": coords[0] + lat_delta,
                "lon": coords[1] + lon_delta,
                "rank": index,
                "title": listing.title,
                "district": listing.district,
                "location": listing.location,
                "community": listing.community or "未标注小区",
                "price": listing.monthly_rent,
                "area": listing.area,
                "score": round(listing.match_score, 2),
                "reason": listing.reason,
                "metro": metro_name,
                "metro_distance": metro_distance,
                "fill_color": _score_color(listing.match_score),
                "line_color": [255, 255, 255, 235],
                "radius": _radius(listing.match_score, index),
                "label": str(index),
            }
        )
    return pd.DataFrame(rows)


def build_district_distribution(listings: list[RentalListing]) -> pd.DataFrame:
    grouped: dict[str, dict[str, float]] = defaultdict(lambda: {"count": 0, "rent_sum": 0, "score_sum": 0})
    for listing in listings:
        bucket = grouped[listing.district]
        bucket["count"] += 1
        bucket["rent_sum"] += listing.monthly_rent
        bucket["score_sum"] += listing.match_score

    rows = []
    for district, payload in grouped.items():
        count = int(payload["count"])
        rows.append(
            {
                "区域": district,
                "房源数": count,
                "平均租金": round(payload["rent_sum"] / count),
                "平均匹配分": round(payload["score_sum"] / count, 2),
            }
        )
    return pd.DataFrame(rows).sort_values(by=["房源数", "平均匹配分"], ascending=[False, False])


def _estimate_zoom(lat_span: float, lon_span: float) -> float:
    span = max(lat_span, lon_span)
    if span <= 0.008:
        return 13.6
    if span <= 0.015:
        return 12.8
    if span <= 0.03:
        return 11.8
    if span <= 0.06:
        return 10.8
    if span <= 0.12:
        return 9.8
    return 8.8


def build_view_state(map_df: pd.DataFrame) -> pdk.ViewState:
    lat_min, lat_max = map_df["lat"].min(), map_df["lat"].max()
    lon_min, lon_max = map_df["lon"].min(), map_df["lon"].max()
    lat_span = max(lat_max - lat_min, 0.003)
    lon_span = max(lon_max - lon_min, 0.003)
    return pdk.ViewState(
        latitude=(lat_min + lat_max) / 2,
        longitude=(lon_min + lon_max) / 2,
        zoom=_estimate_zoom(lat_span, lon_span),
        pitch=28,
        bearing=0,
    )


def render_map_metrics(map_df: pd.DataFrame) -> None:
    best = map_df.sort_values(by="score", ascending=False).iloc[0]
    cols = st.columns(4)
    cols[0].metric("地图点位", len(map_df))
    cols[1].metric("最高匹配分", best["score"])
    cols[2].metric("最高价", f"{int(map_df['price'].max())} 元")
    cols[3].metric("覆盖区域", map_df["district"].nunique())


def render_interactive_map(map_df: pd.DataFrame) -> None:
    view_state = build_view_state(map_df)
    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position="[lon, lat]",
        get_radius="radius",
        get_fill_color="fill_color",
        get_line_color="line_color",
        line_width_min_pixels=2,
        stroked=True,
        pickable=True,
        auto_highlight=True,
        opacity=0.9,
    )
    text_layer = pdk.Layer(
        "TextLayer",
        data=map_df.head(5),
        get_position="[lon, lat]",
        get_text="label",
        get_size=14,
        get_color=[255, 255, 255, 255],
        get_alignment_baseline="'center'",
        get_text_anchor="'middle'",
        pickable=False,
    )

    tooltip = {
        "html": """
        <div style="font-family: Inter, system-ui, sans-serif; padding: 6px 8px;">
            <div style="font-size: 14px; font-weight: 700; margin-bottom: 6px;">#{rank} {title}</div>
            <div>区域：{district} · {location}</div>
            <div>小区：{community}</div>
            <div>租金：{price} 元/月 · 面积：{area} ㎡</div>
            <div>地铁：{metro} · {metro_distance}</div>
            <div>匹配分：{score}</div>
            <div style="margin-top: 4px; color: #555;">{reason}</div>
        </div>
        """,
        "style": {
            "backgroundColor": "rgba(255, 255, 255, 0.96)",
            "color": "#111827",
            "borderRadius": "12px",
            "border": "1px solid #e5e7eb",
            "boxShadow": "0 12px 30px rgba(0,0,0,0.10)",
        },
    }

    deck = pdk.Deck(
        map_style="light",
        initial_view_state=view_state,
        layers=[scatter_layer, text_layer],
        tooltip=tooltip,
    )
    st.pydeck_chart(deck, use_container_width=True, height=470)


def render_heatmap(map_df: pd.DataFrame) -> None:
    view_state = build_view_state(map_df)
    heat_layer = pdk.Layer(
        "HeatmapLayer",
        data=map_df,
        get_position="[lon, lat]",
        get_weight="score",
        aggregation="'SUM'",
        radius_pixels=65,
    )
    deck = pdk.Deck(
        map_style="light",
        initial_view_state=view_state,
        layers=[heat_layer],
    )
    st.pydeck_chart(deck, use_container_width=True, height=470)


def render_market_insights(result: RecommendationResult, show_title: bool = True) -> None:
    if not result.recommendations:
        return

    map_df = build_map_rows(result.recommendations)
    district_df = build_district_distribution(result.recommendations)

    if show_title:
        st.markdown("#### 地图与区域分布")

    map_tab, heat_tab, district_tab = st.tabs(["智能地图", "热力分布", "区域分布"])

    with map_tab:
        if map_df.empty:
            st.info("当前房源没有可用于地图展示的位置数据。")
        else:
            render_map_metrics(map_df)
            st.caption("地图点位会根据房源商圈、地铁和区域中心自动估算位置，并按匹配分调整颜色和大小。")
            render_interactive_map(map_df)
            st.dataframe(
                map_df.rename(
                    columns={
                        "rank": "排序",
                        "title": "房源",
                        "district": "区域",
                        "location": "商圈",
                        "price": "租金",
                        "area": "面积",
                        "score": "匹配分",
                        "metro": "地铁",
                        "metro_distance": "距离",
                    }
                )[
                    ["排序", "房源", "区域", "商圈", "租金", "面积", "匹配分", "地铁", "距离"]
                ],
                use_container_width=True,
                hide_index=True,
            )

    with heat_tab:
        if map_df.empty:
            st.info("当前房源没有可用于热力图展示的位置数据。")
        else:
            st.caption("热力图更适合快速看推荐点位集中在哪些商圈。")
            render_heatmap(map_df)

    with district_tab:
        if district_df.empty:
            st.info("当前还没有可展示的区域分布。")
        else:
            st.bar_chart(district_df.set_index("区域")[["房源数"]], color="#4f8cff")
            st.dataframe(district_df, use_container_width=True, hide_index=True)
