import torch
from pathlib import Path
from rank_bm25 import BM25Okapi
from transformers import AutoModelForSequenceClassification, AutoTokenizer
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

def build_bm25_from_qdrant() -> None:
    from app.rag.qdrant_store import get_client, COLLECTION_NAME
    try:
        client = get_client()
        chunks = []
        offset = None
        while True:
            scroll_result, next_offset = client.scroll(
                collection_name=COLLECTION_NAME,
                limit=1000,
                with_payload=True,
                offset=offset
            )
            for point in scroll_result:
                if point.payload:
                    chunks.append(point.payload)
            if next_offset is None:
                break
            offset = next_offset
            
        if chunks:
            update_bm25_index(chunks)
            print(f"[BM25] Rebuilt from Qdrant: {len(chunks)} chunks")
        else:
            print("[BM25] Qdrant collection is empty. BM25 not built.")
    except Exception as e:
        print(f"[BM25] Warning: Could not rebuild BM25 index from Qdrant: {e}")

MODEL_PATH_RERANKER = Path(__file__).parent.parent.parent / "models" / "reranker"

class CrossEncoderReranker:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._model = None
            cls._instance._tokenizer = None
        return cls._instance

    def load(self):
        if self._model is None:
            print(f"[Reranker] Loading from {MODEL_PATH_RERANKER}...")
            self._tokenizer = AutoTokenizer.from_pretrained(str(MODEL_PATH_RERANKER))
            self._model = AutoModelForSequenceClassification.from_pretrained(str(MODEL_PATH_RERANKER))
            self._model.eval()
            print("[Reranker] Ready.")

    def rerank(self, query: str, candidates: list[dict], top_n: int = 5) -> list[dict]:
        if not candidates:
            return []
            
        if self._model is None:
            self.load()

        pairs = [[query, doc["content"]] for doc in candidates]
        
        inputs = self._tokenizer(
            pairs, 
            padding=True, 
            truncation=True, 
            max_length=512, 
            return_tensors="pt"
        )
        
        with torch.no_grad():
            logits = self._model(**inputs).logits
            
        scores = torch.sigmoid(logits).squeeze().tolist()
        
        if isinstance(scores, float):
            scores = [scores]
            
        for doc, score in zip(candidates, scores):
            doc["rerank_score"] = float(score)
            
        candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
        return candidates[:top_n]

    def health_check(self) -> dict:
        return {
            "loaded": self._model is not None,
            "model_path": str(MODEL_PATH_RERANKER),
            "model_exists": MODEL_PATH_RERANKER.exists()
        }

reranker = CrossEncoderReranker()

def retrieve(query: str, strategy: str = "hybrid") -> list[dict]:
    if strategy == "dense":
        results = semantic_search(query, top_k=15)
    elif strategy == "sparse":
        results = bm25_search(query, top_k=15)
    else:  # hybrid (default)
        dense = semantic_search(query, top_k=15)
        sparse = bm25_search(query, top_k=15)
        results = reciprocal_rank_fusion(dense, sparse, top_n=15)

    if reranker._model is not None:
        return reranker.rerank(query, results, top_n=5)
    else:
        print("[Reranker] Warning: Reranker not loaded. Returning results as-is.")
        return results[:5]

def format_context(results: list[dict]) -> str:
    if not results:
        return ""
    parts = []
    for i, r in enumerate(results):
        parts.append(f"[Source {i+1}: {r.get('source','unknown')}]\n{r['content']}")
    return "\n\n".join(parts)
