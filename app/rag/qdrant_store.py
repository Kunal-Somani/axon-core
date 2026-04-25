from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter,
    FieldCondition, MatchValue
)
import uuid
from app.rag.embedder import embedder

QDRANT_URL = "http://qdrant:6333"
COLLECTION_NAME = "axon_knowledge"
VECTOR_SIZE = 384  # all-MiniLM-L6-v2 output dimension

def get_client() -> QdrantClient:
    return QdrantClient(url=QDRANT_URL)

def ensure_collection():
    client = get_client()
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
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

def semantic_search(query: str, top_k: int = 8) -> list[dict]:
    client = get_client()
    query_vector = embedder.encode_query(query)
    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=top_k,
        with_payload=True
    )
    return [
        {
            "content": r.payload["content"],
            "source": r.payload["metadata"].get("source", "unknown"),
            "score": r.score
        }
        for r in results
    ]

def get_collection_stats() -> dict:
    try:
        client = get_client()
        info = client.get_collection(COLLECTION_NAME)
        return {"document_count": info.points_count, "status": info.status}
    except Exception as e:
        return {"document_count": 0, "status": "error", "detail": str(e)}