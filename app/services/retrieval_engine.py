from rank_bm25 import BM25Okapi
from app.rag.qdrant_store import semantic_search
from typing import Optional

# In-memory BM25 index — rebuilt on ingest
_bm25_index: Optional[BM25Okapi] = None
_bm25_corpus: list[dict] = []

def update_bm25_index(chunks: list[dict]):
    global _bm25_index, _bm25_corpus
    _bm25_corpus = chunks
    tokenized = [c["content"].lower().split() for c in chunks]
    _bm25_index = BM25Okapi(tokenized)
    print(f"[BM25] Index updated with {len(chunks)} chunks")

def bm25_search(query: str, top_k: int = 8) -> list[dict]:
    if _bm25_index is None or not _bm25_corpus:
        return []
    tokenized_query = query.lower().split()
    scores = _bm25_index.get_scores(tokenized_query)
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
    return [
        {
            "content": _bm25_corpus[i]["content"],
            "source": _bm25_corpus[i].get("metadata", {}).get("source", "unknown"),
            "score": float(scores[i]),
            "retrieval_method": "bm25"
        }
        for i in top_indices if scores[i] > 0
    ]

def reciprocal_rank_fusion(dense_results: list[dict], sparse_results: list[dict], k: int = 60, top_n: int = 5) -> list[dict]:
    scores: dict[str, float] = {}
    docs: dict[str, dict] = {}

    for rank, doc in enumerate(dense_results):
        key = doc["content"][:100]
        scores[key] = scores.get(key, 0) + 1.0 / (k + rank + 1)
        docs[key] = {**doc, "retrieval_method": "hybrid_rrf"}

    for rank, doc in enumerate(sparse_results):
        key = doc["content"][:100]
        scores[key] = scores.get(key, 0) + 1.0 / (k + rank + 1)
        if key not in docs:
            docs[key] = {**doc, "retrieval_method": "hybrid_rrf"}

    sorted_keys = sorted(scores, key=lambda k: scores[k], reverse=True)
    return [docs[k] for k in sorted_keys[:top_n]]

def retrieve(query: str, strategy: str = "hybrid") -> list[dict]:
    if strategy == "dense":
        return semantic_search(query, top_k=8)
    elif strategy == "sparse":
        return bm25_search(query, top_k=8)
    else:  # hybrid (default)
        dense = semantic_search(query, top_k=8)
        sparse = bm25_search(query, top_k=8)
        return reciprocal_rank_fusion(dense, sparse)

def format_context(results: list[dict]) -> str:
    if not results:
        return ""
    parts = []
    for i, r in enumerate(results):
        parts.append(f"[Source {i+1}: {r.get('source','unknown')}]\n{r['content']}")
    return "\n\n".join(parts)
