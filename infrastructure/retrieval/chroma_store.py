from __future__ import annotations

import hashlib
import math
import re
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings

from homeagent.config import CHROMA_COLLECTION_NAME, CHROMA_PERSIST_DIR, CHROMA_TOP_K


EMBEDDING_DIMENSION = 256


def _tokenize(text: str) -> list[str]:
    lowered = text.lower()
    english_tokens = re.findall(r"[a-z0-9]+", lowered)
    chinese_chars = re.findall(r"[\u4e00-\u9fff]", text)

    tokens: list[str] = []
    tokens.extend(english_tokens)
    tokens.extend(chinese_chars)
    tokens.extend(
        chinese_chars[index] + chinese_chars[index + 1]
        for index in range(len(chinese_chars) - 1)
    )
    return tokens


def _hash_index(token: str, dimension: int = EMBEDDING_DIMENSION) -> int:
    digest = hashlib.md5(token.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % dimension


def embed_text(text: str, dimension: int = EMBEDDING_DIMENSION) -> list[float]:
    vector = [0.0] * dimension
    for token in _tokenize(text):
        index = _hash_index(token, dimension)
        weight = 1.0 + min(2.0, len(token) * 0.18)
        vector[index] += weight

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


class ChromaListingStore:
    def __init__(
        self,
        persist_directory: Path | str = CHROMA_PERSIST_DIR,
        collection_name: str = CHROMA_COLLECTION_NAME,
    ) -> None:
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self.client = chromadb.Client(
            Settings(
                chroma_api_impl="chromadb.api.segment.SegmentAPI",
                is_persistent=True,
                persist_directory=str(self.persist_directory),
            )
        )
        self.collection = self.client.get_or_create_collection(name=self.collection_name)

    def rebuild(self, vector_docs: list[dict[str, Any]]) -> int:
        try:
            self.client.delete_collection(name=self.collection_name)
        except Exception:
            pass

        self.collection = self.client.get_or_create_collection(name=self.collection_name)
        if not vector_docs:
            return 0

        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []
        embeddings: list[list[float]] = []

        for doc in vector_docs:
            doc_id = str(doc["id"])
            document = str(doc.get("text", ""))
            metadata = self._clean_metadata(doc)

            ids.append(doc_id)
            documents.append(document)
            metadatas.append(metadata)
            embeddings.append(embed_text(document))

        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )
        return self.collection.count()

    def search(self, query: str, top_k: int = CHROMA_TOP_K) -> list[dict[str, Any]]:
        if self.count() == 0:
            return []

        result = self.collection.query(
            query_embeddings=[embed_text(query)],
            n_results=max(1, top_k),
            include=["documents", "metadatas", "distances"],
        )

        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        rows: list[dict[str, Any]] = []
        for index, item_id in enumerate(ids):
            metadata = metadatas[index] if index < len(metadatas) else {}
            rows.append(
                {
                    "id": item_id,
                    "text": documents[index] if index < len(documents) else "",
                    "distance": distances[index] if index < len(distances) else None,
                    "metadata": metadata or {},
                    "title": metadata.get("title", item_id),
                    "source": metadata.get("source", f"listing://{item_id}"),
                }
            )
        return rows

    def count(self) -> int:
        try:
            return self.collection.count()
        except Exception:
            return 0

    def status(self) -> str:
        return (
            f"Chroma 集合 {self.collection_name} 已持久化到 {self.persist_directory}，"
            f"当前共有 {self.count()} 条向量文档。"
        )

    @staticmethod
    def _clean_metadata(doc: dict[str, Any]) -> dict[str, Any]:
        raw_metadata = dict(doc.get("metadata", {}))
        tags = raw_metadata.pop("tags", [])
        if isinstance(tags, list):
            raw_metadata["tags"] = "、".join(str(tag) for tag in tags if tag)
        elif tags:
            raw_metadata["tags"] = str(tags)
        else:
            raw_metadata["tags"] = ""

        raw_metadata["title"] = str(doc.get("title", ""))
        raw_metadata["source"] = str(doc.get("source", ""))
        return raw_metadata
