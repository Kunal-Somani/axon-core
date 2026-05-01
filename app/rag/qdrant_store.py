import uuid
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter,
    FieldCondition, MatchValue
)
from app.rag.embedder import embedder

QDRANT_URL = "http://qdrant:6333"
COLLECTION_NAME = "axon_knowledge"

def get_client() -> QdrantClient:
    return QdrantClient(url=QDRANT_URL)

def ensure_collection():
    client = get_client()
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in existing:
        # NOTE: embedder.load() must be called before ensure_collection()
        vector_size = embedder.embedding_dim
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
        print(f"[Qdrant] Created collection '{COLLECTION_NAME}'")
    return client

def ingest_chunks(chunks: list[dict]) -> dict:
    client = ensure_collection()
    new_count = 0
    skipped_count = 0
    points = []

    # Get existing hashes to skip duplicates
    existing_hashes = set()
    try:
        scroll_result = client.scroll(collection_name=COLLECTION_NAME, limit=10000, with_payload=True)
        for point in scroll_result[0]:
            h = point.payload.get("metadata", {}).get("hash")
            if h:
                existing_hashes.add(h)
    except Exception:
        pass

    texts = [c["content"] for c in chunks]
    vectors = embedder.encode_texts(texts)

    for chunk, vector in zip(chunks, vectors):
        chunk_hash = chunk["metadata"]["hash"]
        if chunk_hash in existing_hashes:
            skipped_count += 1
            continue
        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={"content": chunk["content"], "metadata": chunk["metadata"]}
        ))
        new_count += 1

    if points:
        client.upsert(collection_name=COLLECTION_NAME, points=points)

    return {"ingested": new_count, "skipped": skipped_count}

def semantic_search(query: str, top_k: int = 8, score_threshold: float = 0.35) -> list[dict]:
    client = get_client()
    query_vector = embedder.encode_query(query)
    try:
        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=top_k,
            with_payload=True,
            score_threshold=score_threshold
        )
    except Exception:
        return []
        
    return [
        {
            "content": r.payload["content"],
            "source": r.payload["metadata"].get("source", "unknown"),
            "score": r.score
        }
        for r in results
    ]

def max_marginal_relevance_search(query: str, top_k: int = 5, fetch_k: int = 20, lambda_mult: float = 0.5) -> list[dict]:
    client = get_client()
    query_vector = embedder.encode_query(query)
    try:
        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=fetch_k,
            with_payload=True,
            with_vectors=True
        )
    except Exception:
        return []

    if not results:
        return []

    doc_vectors = np.array([r.vector for r in results])
    q_vec = np.array(query_vector)

    sim_to_query = np.dot(doc_vectors, q_vec)

    selected_indices = [int(np.argmax(sim_to_query))]
    remaining_indices = list(range(len(results)))
    remaining_indices.remove(selected_indices[0])

    while len(selected_indices) < top_k and remaining_indices:
        selected_vectors = doc_vectors[selected_indices]
        remaining_vectors = doc_vectors[remaining_indices]

        sim_to_selected = np.dot(remaining_vectors, selected_vectors.T)
        max_sim_to_selected = np.max(sim_to_selected, axis=1)

        mmr_scores = lambda_mult * sim_to_query[remaining_indices] - (1 - lambda_mult) * max_sim_to_selected

        best_remaining_idx = int(np.argmax(mmr_scores))
        best_idx = remaining_indices[best_remaining_idx]

        selected_indices.append(best_idx)
        remaining_indices.pop(best_remaining_idx)

    return [
        {
            "content": results[idx].payload["content"],
            "source": results[idx].payload["metadata"].get("source", "unknown"),
            "score": float(sim_to_query[idx])
        }
        for idx in selected_indices
    ]

def get_collection_stats() -> dict:
    try:
        client = get_client()
        info = client.get_collection(COLLECTION_NAME)
        vector_size = None
        if hasattr(info, 'config') and hasattr(info.config, 'params') and hasattr(info.config.params, 'vectors'):
            vector_size = info.config.params.vectors.size
        return {
            "document_count": info.points_count, 
            "status": str(info.status),
            "vector_size": vector_size
        }
    except Exception as e:
        return {"document_count": 0, "status": "error", "detail": str(e), "vector_size": None}