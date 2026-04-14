from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from homeagent.config import CHROMA_TOP_K, VECTOR_DOCS_PATH, VECTOR_STORE_DIR
from homeagent.domain.models import KnowledgeHit
from homeagent.infrastructure.retrieval.chroma_store import ChromaListingStore


@dataclass(frozen=True)
class _BuiltinKnowledgeDoc:
    title: str
    snippet: str
    source: str
    keywords: tuple[str, ...]


class RentalKnowledgeBase:
    BUILTIN_DOCS = (
        _BuiltinKnowledgeDoc(
            title="签约前先核验房东身份和产权",
            snippet="签约前至少核验房东身份证明、房产证或授权委托书，并确认收款账户和合同主体一致。",
            source="builtin://signing-checklist",
            keywords=("签约", "合同", "房东", "中介", "产权", "押金"),
        ),
        _BuiltinKnowledgeDoc(
            title="看房现场检查清单",
            snippet="看房时重点确认采光、噪音、水压、热水、空调、门锁、网络和卫生间返味，避免只看图片就签约。",
            source="builtin://viewing-checklist",
            keywords=("看房", "采光", "噪音", "水压", "热水", "卫生间"),
        ),
        _BuiltinKnowledgeDoc(
            title="合租前先确认室友和公共区域规则",
            snippet="合租要确认室友作息、公共区域卫生、是否允许带人留宿，以及水电网如何分摊。",
            source="builtin://shared-rent-guide",
            keywords=("合租", "次卧", "室友", "分摊"),
        ),
        _BuiltinKnowledgeDoc(
            title="整租预算不能只看挂牌月租",
            snippet="整租时除了月租，还要确认押几付几、服务费、物业费、停车费和是否有中介佣金。",
            source="builtin://whole-rent-budget",
            keywords=("整租", "月付", "押一付三", "服务费", "物业费"),
        ),
        _BuiltinKnowledgeDoc(
            title="通勤和地铁距离要一起看",
            snippet="近地铁不一定通勤快，最好同时比较步行到站时间、换乘次数和早晚高峰拥挤程度。",
            source="builtin://commute-guide",
            keywords=("地铁", "通勤", "近地铁", "上班", "换乘"),
        ),
        _BuiltinKnowledgeDoc(
            title="宠物友好房源最好写进合同",
            snippet="如果需要养猫养狗，最好把宠物条款写进合同，明确押金、清洁责任和退租恢复要求。",
            source="builtin://pet-friendly-rent",
            keywords=("宠物", "养猫", "养狗"),
        ),
    )

    def __init__(self, persist_directory=VECTOR_STORE_DIR, docs_path=VECTOR_DOCS_PATH) -> None:
        self.persist_directory = persist_directory
        self.docs_path = Path(docs_path)
        self.listing_docs = self._load_listing_docs()
        self.chroma = ChromaListingStore(persist_directory=persist_directory)

    def _load_listing_docs(self) -> list[dict]:
        if not self.docs_path.exists():
            return []
        try:
            return json.loads(self.docs_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []

    def search(self, query: str, top_k: int = CHROMA_TOP_K) -> list[KnowledgeHit]:
        listing_hits = self._search_with_chroma(query, top_k=top_k)
        if not listing_hits:
            listing_hits = self._search_listing_docs_fallback(query, top_k=top_k)

        builtin_hits = self._search_builtin_docs(query, top_k=max(1, top_k - len(listing_hits)))
        return (listing_hits + builtin_hits)[:top_k]

    def _search_with_chroma(self, query: str, top_k: int) -> list[KnowledgeHit]:
        rows = self.chroma.search(query, top_k=top_k)
        hits: list[KnowledgeHit] = []
        for row in rows:
            hits.append(
                KnowledgeHit(
                    title=f"房源卡片：{row['title']}",
                    snippet=self._truncate(str(row.get("text", "")), 120),
                    source=str(row.get("source", "")),
                )
            )
        return hits

    def _search_builtin_docs(self, query: str, top_k: int) -> list[KnowledgeHit]:
        scored_docs: list[tuple[int, _BuiltinKnowledgeDoc]] = []
        for doc in self.BUILTIN_DOCS:
            score = sum(1 for keyword in doc.keywords if keyword in query)
            if score > 0:
                scored_docs.append((score, doc))

        if not scored_docs:
            scored_docs = [(1, self.BUILTIN_DOCS[0]), (1, self.BUILTIN_DOCS[1])]

        scored_docs.sort(key=lambda item: item[0], reverse=True)
        return [
            KnowledgeHit(title=doc.title, snippet=doc.snippet, source=doc.source)
            for _, doc in scored_docs[:top_k]
        ]

    def _search_listing_docs_fallback(self, query: str, top_k: int = 3) -> list[KnowledgeHit]:
        if not self.listing_docs:
            return []

        query_terms = self._extract_query_terms(query)
        budget_max = self._extract_budget_max(query)
        preferred_room = self._extract_preferred_room(query)
        preferred_districts = self._extract_preferred_districts(query)
        scored: list[tuple[int, dict]] = []

        for doc in self.listing_docs:
            metadata = doc.get("metadata", {})
            score = 0
            title = str(doc.get("title", ""))
            text = str(doc.get("text", ""))

            if title and title in query:
                score += 4

            for key in ("district", "location", "community", "rent_type"):
                value = str(metadata.get(key, ""))
                if value and value in query:
                    score += 2

            district = str(metadata.get("district", ""))
            if preferred_districts:
                score += 4 if district in preferred_districts else -2

            tags = metadata.get("tags", [])
            if isinstance(tags, list):
                for tag in tags:
                    if tag and tag in query:
                        score += 2

            for term in query_terms:
                if term in text:
                    score += 2

            monthly_rent = metadata.get("monthly_rent")
            if budget_max is not None and isinstance(monthly_rent, int):
                if monthly_rent <= budget_max:
                    score += 2
                elif monthly_rent <= int(budget_max * 1.1):
                    score += 1
                else:
                    score -= 2

            if preferred_room:
                if preferred_room in text:
                    score += 5
                elif any(other in text for other in self._other_room_terms(preferred_room)):
                    score -= 6

            if score > 0:
                scored.append((score, doc))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            KnowledgeHit(
                title=f"房源卡片：{doc['title']}",
                snippet=self._truncate(str(doc.get("text", "")), 120),
                source=str(doc.get("source", "")),
            )
            for _, doc in scored[:top_k]
        ]

    @staticmethod
    def _truncate(text: str, limit: int) -> str:
        if len(text) <= limit:
            return text
        return text[:limit] + "..."

    @staticmethod
    def _extract_budget_max(query: str) -> int | None:
        match = re.search(r"(?:预算|租金)\s*(\d{3,5})", query)
        if match:
            return int(match.group(1))
        return None

    @staticmethod
    def _extract_query_terms(query: str) -> list[str]:
        known_terms = [
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
            "开间",
            "一室",
            "一居",
            "两室",
            "两居",
            "三室",
            "三居",
            "整租",
            "合租",
            "近地铁",
            "精装",
            "押一付一",
            "月租",
            "集中供暖",
            "随时看房",
        ]
        terms = [term for term in known_terms if term in query]
        raw_parts = re.findall(r"[\u4e00-\u9fffA-Za-z0-9]+", query)
        for part in raw_parts:
            if len(part) >= 2 and part not in terms:
                terms.append(part)
        return terms

    @staticmethod
    def _extract_preferred_districts(query: str) -> list[str]:
        known_districts = [
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
        return [district for district in known_districts if district in query]

    @staticmethod
    def _extract_preferred_room(query: str) -> str | None:
        room_terms = ["开间", "一室", "一居", "两室", "两居", "三室", "三居"]
        for term in room_terms:
            if term in query:
                return term
        return None

    @staticmethod
    def _other_room_terms(preferred_room: str) -> list[str]:
        room_groups = {
            "开间": ["一室", "一居", "两室", "两居", "三室", "三居"],
            "一室": ["两室", "两居", "三室", "三居"],
            "一居": ["两室", "两居", "三室", "三居"],
            "两室": ["一室", "一居", "三室", "三居"],
            "两居": ["一室", "一居", "三室", "三居"],
            "三室": ["一室", "一居", "两室", "两居"],
            "三居": ["一室", "一居", "两室", "两居"],
        }
        return room_groups.get(preferred_room, [])

    def status(self) -> str:
        listing_count = self.chroma.count()
        if listing_count:
            return (
                f"知识库已接入 Chroma，当前有 {listing_count} 条房源向量文档，"
                f"持久化目录为 {self.persist_directory}。"
            )
        if self.listing_docs:
            return (
                f"当前已加载 {len(self.listing_docs)} 条向量就绪文档，但 Chroma 还没有索引数据。"
            )
        return f"知识库暂时为空，后续可以继续导入 PDF 或更多房源数据到 {self.persist_directory}。"
