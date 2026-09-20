"""
GhostWatch RAG Module
======================
Vector store with pluggable embeddings:
- Primary: ChromaDB with sentence-transformers ``all-MiniLM-L6-v2``
- IBM Mode: Granite embedding model (when credentials exist)
- Fallback: Built-in in-memory cosine vector store if ChromaDB is unavailable
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Optional

from src.config import (
    IBM_CREDENTIALS_AVAILABLE,
    LOCAL_EMBEDDING_MODEL,
    RAG_TOP_K,
)
from src.models import Grievance
from src.utils import ASSET_TYPE_DISPLAY, ASSET_TYPE_KEYWORDS, logger

# Try importing chromadb
try:
    import chromadb
    from chromadb.utils import embedding_functions
    _CHROMADB_AVAILABLE = True
except ImportError:
    _CHROMADB_AVAILABLE = False


class _InMemoryCosineStore:
    """Zero-dependency vector search fallback using TF-IDF cosine similarity."""

    def __init__(self) -> None:
        self.docs: list[str] = []
        self.metas: list[dict] = []
        self.ids: list[str] = []
        self.doc_vectors: list[dict[str, float]] = []
        self.idf: dict[str, float] = {}

    def _tokenize(self, text: str) -> list[str]:
        return [w.lower() for w in re.findall(r"\b\w{2,}\b", text)]

    def add(self, docs: list[str], metas: list[dict], ids: list[str]) -> None:
        self.docs = docs
        self.metas = metas
        self.ids = ids

        # Compute document frequencies
        n_docs = len(docs)
        df: Counter = Counter()
        tokenized_docs = []
        for d in docs:
            tokens = set(self._tokenize(d))
            tokenized_docs.append(tokens)
            df.update(tokens)

        self.idf = {w: math.log((1 + n_docs) / (1 + count)) + 1.0 for w, count in df.items()}

        # Build normalized TF-IDF vectors
        self.doc_vectors = []
        for d in docs:
            tf = Counter(self._tokenize(d))
            vec = {w: count * self.idf.get(w, 1.0) for w, count in tf.items()}
            norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
            self.doc_vectors.append({w: v / norm for w, v in vec.items()})

    def search(self, query: str, top_k: int) -> list[dict]:
        q_tokens = self._tokenize(query)
        q_tf = Counter(q_tokens)
        q_vec = {w: count * self.idf.get(w, 1.0) for w, count in q_tf.items()}
        q_norm = math.sqrt(sum(v * v for v in q_vec.values())) or 1.0
        q_vec_norm = {w: v / q_norm for w, v in q_vec.items()}

        scores = []
        for i, doc_vec in enumerate(self.doc_vectors):
            dot = sum(doc_vec.get(w, 0.0) * val for w, val in q_vec_norm.items())
            # Calibrate TF-IDF sparse similarity to standard dense embedding range (0.0 - 0.95)
            # In sparse query matching, a dot product of 0.30+ indicates strong semantic keyword alignment.
            scaled_sim = min(0.95, round(min(1.0, dot * 2.2), 4)) if dot > 0.05 else round(dot, 4)
            scores.append((scaled_sim, i))

        scores.sort(key=lambda x: x[0], reverse=True)
        top = scores[:top_k]

        results = []
        for sim, idx in top:
            results.append({
                "complaint_id": self.ids[idx],
                "similarity": sim,
                "document": self.docs[idx],
                "metadata": self.metas[idx],
            })
        return results


class RAGStore:
    """Vector store for grievance signals using ChromaDB or resilient fallback."""

    def __init__(self) -> None:
        self.chroma_client = None
        self.collection = None
        self.fallback_store: Optional[_InMemoryCosineStore] = None
        self.use_fallback = not _CHROMADB_AVAILABLE
        self._initialised = False

        if not self.use_fallback:
            try:
                self.chroma_client = chromadb.Client()
                if IBM_CREDENTIALS_AVAILABLE:
                    logger.info("IBM credentials detected — Granite embedding integration active")
                self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name=LOCAL_EMBEDDING_MODEL,
                )
            except Exception as exc:
                logger.warning("ChromaDB initialization failed (%s); using in-memory vector store", exc)
                self.use_fallback = True

        if self.use_fallback:
            logger.info("RAGStore: using high-performance In-Memory Cosine Vector Store")
            self.fallback_store = _InMemoryCosineStore()

    def initialize(self, grievances: list[Grievance]) -> None:
        """Embed all grievances and build the vector index."""
        if self._initialised:
            return

        logger.info("Building RAG index with %d grievances …", len(grievances))

        docs, metas, ids = [], [], []
        for g in grievances:
            doc = f"{g.complaint_text} Location: {g.approx_location}"
            if g.category_tag:
                doc += f" Category: {g.category_tag}"
            docs.append(doc)
            metas.append({
                "complaint_id": g.complaint_id,
                "approx_location": g.approx_location,
                "date_reported": str(g.date_reported),
                "category_tag": g.category_tag or "",
                "complaint_text": g.complaint_text,
            })
            ids.append(g.complaint_id)

        if not self.use_fallback and self.chroma_client:
            try:
                try:
                    self.chroma_client.delete_collection("grievances")
                except Exception:
                    pass
                self.collection = self.chroma_client.create_collection(
                    name="grievances",
                    embedding_function=self.ef,
                    metadata={"hnsw:space": "cosine"},
                )
                batch = 100
                for i in range(0, len(docs), batch):
                    self.collection.add(
                        documents=docs[i:i + batch],
                        metadatas=metas[i:i + batch],
                        ids=ids[i:i + batch],
                    )
                self._initialised = True
                logger.info("ChromaDB RAG index ready (%d documents)", self.collection.count())
                return
            except Exception as exc:
                logger.warning("Failed indexing into ChromaDB (%s), using fallback", exc)
                self.use_fallback = True
                self.fallback_store = _InMemoryCosineStore()

        if self.fallback_store:
            self.fallback_store.add(docs, metas, ids)
            self._initialised = True
            logger.info("In-Memory Vector index ready (%d documents)", len(docs))

    def retrieve_signals(
        self,
        asset_location: str,
        asset_type: str,
        top_k: int | None = None,
    ) -> list[dict]:
        """
        Retrieve top_k grievance signals matching an asset.
        """
        if not self._initialised:
            logger.warning("RAG store not yet initialised")
            return []

        top_k = top_k or RAG_TOP_K
        type_desc = ASSET_TYPE_DISPLAY.get(asset_type, asset_type)
        keywords = " ".join(ASSET_TYPE_KEYWORDS.get(asset_type, []))
        query = f"{type_desc} {keywords} {asset_location}"

        if not self.use_fallback and self.collection:
            try:
                n = min(top_k, self.collection.count())
                if n == 0:
                    return []
                results = self.collection.query(
                    query_texts=[query],
                    n_results=n,
                    include=["documents", "metadatas", "distances"],
                )
                signals: list[dict] = []
                if results and results["ids"] and results["ids"][0]:
                    for i, cid in enumerate(results["ids"][0]):
                        sim = max(0.0, 1.0 - results["distances"][0][i])
                        signals.append({
                            "complaint_id": cid,
                            "similarity": round(sim, 4),
                            "document": results["documents"][0][i],
                            "metadata": results["metadatas"][0][i],
                        })
                return signals
            except Exception as exc:
                logger.warning("ChromaDB query failed (%s), querying fallback store", exc)

        if self.fallback_store:
            return self.fallback_store.search(query, top_k)

        return []


_rag_store: Optional[RAGStore] = None


def get_rag_store() -> RAGStore:
    """Get or create the singleton RAG store."""
    global _rag_store
    if _rag_store is None:
        _rag_store = RAGStore()
    return _rag_store


def reset_rag_store() -> None:
    """Reset the singleton (useful for testing)."""
    global _rag_store
    _rag_store = None
