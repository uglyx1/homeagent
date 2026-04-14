from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from homeagent.config import (
    CHROMA_COLLECTION_NAME,
    CHROMA_PERSIST_DIR,
    PROCESSED_LISTINGS_PATH,
    PROJECT_NAME,
    RAW_DATA_DIR,
    VECTOR_DOCS_PATH,
)
from homeagent.infrastructure.retrieval.chroma_store import ChromaListingStore


DISTRICT_SCORES = {
    "东城区": 8.8,
    "西城区": 8.8,
    "朝阳区": 8.5,
    "海淀区": 8.4,
    "丰台区": 7.8,
    "石景山区": 7.4,
    "通州区": 7.2,
    "昌平区": 7.1,
    "大兴区": 7.0,
    "北京经济技术开发区": 7.3,
}


def normalize_room_type(layout: str) -> str:
    if layout.startswith("1室"):
        return "1bedroom"
    if layout.startswith("2室"):
        return "2bedroom"
    if layout.startswith("3室"):
        return "3bedroom"
    return "studio"


def safe_int(value: Any, default: int = 0) -> int:
    if value in (None, ""):
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def build_transport_score(distance: int | None) -> float:
    if distance is None:
        return 6.0
    if distance <= 300:
        return 9.3
    if distance <= 600:
        return 8.6
    if distance <= 1000:
        return 7.8
    return 6.8


def build_facility_score(tags: list[str], district: str) -> float:
    base = DISTRICT_SCORES.get(district, 7.0)
    bonus = 0.0
    if "近地铁" in tags:
        bonus += 0.4
    if "精装" in tags:
        bonus += 0.3
    if "押一付一" in tags or "月租" in tags:
        bonus += 0.2
    if "首次出租" in tags or "新上" in tags:
        bonus += 0.1
    return round(min(9.5, base + bonus), 1)


def build_highlight(resblock: str, bizcircle: str, tags: list[str]) -> str:
    top_tags = "、".join(tags[:3]) if tags else "基础信息完整"
    return f"{resblock}，位于{bizcircle}，标签包括{top_tags}。"


def build_vector_text(record: dict[str, Any]) -> str:
    tags = "、".join(record["tags"]) if record["tags"] else "无明显标签"
    metro_name = record["transport"]["nearest_metro"] or "未标注地铁站"
    metro_distance = record["transport"]["metro_distance"]
    metro_text = f"距离{metro_name}{metro_distance}米" if metro_distance else "地铁距离未标注"
    return (
        f"{record['title']}。"
        f"位于{record['district']}{record['location']}，小区{record.get('community', '')}。"
        f"{record['rent_type']}，户型{record['layout']}，面积{record['area']}平米，"
        f"月租{record['monthly_rent']}元，朝向{record['orientation']}。"
        f"{metro_text}。"
        f"标签有：{tags}。"
        f"亮点：{record['highlight']}"
    )


def normalize_listing(raw: dict[str, Any]) -> dict[str, Any]:
    tags = [item.get("val", "").strip() for item in raw.get("house_tags", []) if item.get("val")]
    district = raw.get("hdic_district_name", "")
    bizcircle = raw.get("hdic_bizcircle_name", "")
    resblock = raw.get("hdic_resblock_name", "")
    layout = raw.get("house_layout") or raw.get("house_title", "")
    area_value = safe_int(raw.get("rent_area"))
    rent_price = safe_int(raw.get("rent_price_listing") or raw.get("min_monthly_rent_price"))
    subway_distance_raw = safe_int(raw.get("nearest_subway_distance"))
    subway_distance = subway_distance_raw if subway_distance_raw > 0 else None

    return {
        "listing_id": raw.get("house_code", ""),
        "title": raw.get("house_title") or raw.get("app_house_title") or resblock,
        "district": district,
        "location": bizcircle or district,
        "community": resblock,
        "rent_type": raw.get("rent_type_name") or "整租",
        "room_type": normalize_room_type(layout),
        "layout": layout,
        "area": area_value,
        "monthly_rent": rent_price,
        "available_from": raw.get("sign_time") or "",
        "orientation": raw.get("frame_orientation") or "未知",
        "floor_level": raw.get("floor_level") or "",
        "image_url": raw.get("list_picture") or "",
        "tags": tags,
        "highlight": build_highlight(resblock, bizcircle or district, tags),
        "source": raw.get("app_source_brand_name") or "链家抓包",
        "source_url": f"https://m.lianjia.com{raw.get('house_url', '')}" if raw.get("house_url") else "",
        "transport": {
            "nearest_metro": raw.get("nearest_subway_station_name") or "",
            "metro_distance": subway_distance,
            "commute_hint": f"{bizcircle or district}商圈可达",
            "transport_score": build_transport_score(subway_distance),
        },
        "facilities": {
            "nearby": tags[:4],
            "facility_score": build_facility_score(tags, district),
        },
    }


def load_raw_rows(raw_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(raw_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        rows.extend(data.get("data", {}).get("recommend_list", []))
    return rows


def build_listing_index(raw_dir: Path = RAW_DATA_DIR) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    raw_rows = load_raw_rows(raw_dir)
    deduped: dict[str, dict[str, Any]] = {}
    for row in raw_rows:
        house_code = row.get("house_code")
        if house_code and house_code not in deduped:
            deduped[house_code] = row

    listings = [normalize_listing(row) for row in deduped.values()]
    listings.sort(key=lambda item: (item["district"], item["monthly_rent"], item["listing_id"]))

    vector_docs: list[dict[str, Any]] = []
    for listing in listings:
        vector_docs.append(
            {
                "id": listing["listing_id"],
                "title": listing["title"],
                "source": listing["source_url"] or f"listing://{listing['listing_id']}",
                "text": build_vector_text(listing),
                "metadata": {
                    "district": listing["district"],
                    "location": listing["location"],
                    "community": listing["community"],
                    "rent_type": listing["rent_type"],
                    "room_type": listing["room_type"],
                    "monthly_rent": listing["monthly_rent"],
                    "area": listing["area"],
                    "tags": listing["tags"],
                },
            }
        )

    return listings, vector_docs


def write_outputs(
    listings: list[dict[str, Any]],
    vector_docs: list[dict[str, Any]],
    processed_path: Path = PROCESSED_LISTINGS_PATH,
    docs_path: Path = VECTOR_DOCS_PATH,
) -> None:
    processed_path.parent.mkdir(parents=True, exist_ok=True)
    docs_path.parent.mkdir(parents=True, exist_ok=True)
    processed_path.write_text(json.dumps(listings, ensure_ascii=False, indent=2), encoding="utf-8")
    docs_path.write_text(json.dumps(vector_docs, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    listings, vector_docs = build_listing_index()
    write_outputs(listings, vector_docs)

    store = ChromaListingStore()
    count = store.rebuild(vector_docs)

    print(f"{PROJECT_NAME} 已生成 {len(listings)} 条标准化房源 -> {PROCESSED_LISTINGS_PATH}")
    print(f"{PROJECT_NAME} 已生成 {len(vector_docs)} 条向量文档 -> {VECTOR_DOCS_PATH}")
    print(
        f"Chroma 已写入 {count} 条文档 -> {CHROMA_PERSIST_DIR} "
        f"(collection={CHROMA_COLLECTION_NAME})"
    )


if __name__ == "__main__":
    main()
