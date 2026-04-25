import json
import base64
import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.rag.embedder import embedder
from app.rag.qdrant_store import ensure_collection, ingest_chunks, get_collection_stats
from app.rag.document_processor import process_file
from app.core.llm_engine import llm_engine, build_prompt
from app.core.router import semantic_router
from app.core.memory import init_db, save_message, get_history, get_full_history
from app.services.retrieval_engine import retrieve, format_context, update_bm25_index
from app.services.tools_engine import execute_tool, get_available_tools
from app.services.vision_engine import vision_engine

STARTUP_TIME = time.time()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n=== Axon Starting Up ===")
    await init_db()
    ensure_collection()
    embedder.load()
    # Router and LLM load lazily on first use to avoid blocking startup
    # Vision loads lazily too
    print("=== Axon Ready ===\n")
    yield

app = FastAPI(title="Axon AI Backend", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "uptime_seconds": round(time.time() - STARTUP_TIME),
        "models": {
            "embedder": embedder.health_check() if hasattr(embedder, 'health_check') else {"loaded": embedder._model is not None},
            "llm": llm_engine.health_check(),
            "router": semantic_router.health_check(),
            "vision": vision_engine.health_check(),
        },
        "qdrant": get_collection_stats(),
        "available_tools": get_available_tools(),
    }

@app.post("/ingest")
async def ingest_file(file: UploadFile = File(...)):
    content = await file.read()
    chunks = process_file(content, file.filename)
    if not chunks:
        raise HTTPException(status_code=400, detail="No content could be extracted from this file.")
    stats = ingest_chunks(chunks)
    # Rebuild BM25 index with new chunks
    update_bm25_index(chunks)
    return {"filename": file.filename, "chunks_found": len(chunks), **stats}

@app.get("/sessions/{session_id}/history")
async def session_history(session_id: str):
    history = await get_full_history(session_id)
    return {"session_id": session_id, "messages": history}

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            raw = await websocket.receive_text()
            payload = json.loads(raw)
            query = payload.get("query", "").strip()
            session_id = payload.get("session_id", str(uuid.uuid4()))
            image_b64 = payload.get("image_base64")

            if not query:
                await websocket.send_text(json.dumps({"type": "error", "message": "Empty query"}))
                continue

            await save_message(session_id, "user", query)

            # Route the query
            routing = semantic_router.route(query)
            route = routing["route"]
            confidence = routing["confidence"]
            sources = []

            # Handle image if present
            if image_b64:
                route = "image_analysis"
                image_bytes = base64.b64decode(image_b64)
                image_context = vision_engine.analyze(image_bytes)
                context = f"The user sent an image.\n{image_context}"
            elif route in ("personal_knowledge_query", "document_analysis"):
                results = retrieve(query, strategy="hybrid")
                context = format_context(results)
                sources = [{"source": r["source"], "score": r.get("score", 0)} for r in results]
            elif route == "system_tool_execution":
                # Use LLM to extract tool name and params
                tool_prompt = f"""You have these tools: {get_available_tools()}
User request: "{query}"
Output ONLY valid JSON: {{"tool": "tool_name", "params": {{}}}}"""
                tool_response = llm_engine.generate(tool_prompt, max_tokens=100)
                try:
                    cleaned = tool_response.strip().split("```")[-1] if "```" in tool_response else tool_response
                    tool_call = json.loads(cleaned)
                    tool_result = execute_tool(tool_call["tool"], tool_call.get("params", {}))
                    full_response = f"Tool: `{tool_call['tool']}`\n\nResult:\n```json\n{json.dumps(tool_result, indent=2)}\n```"
                except Exception as e:
                    full_response = f"Could not parse tool request: {e}"
                await websocket.send_text(json.dumps({"type": "token", "data": full_response}))
                await websocket.send_text(json.dumps({"type": "done", "route": route, "confidence": confidence, "sources": []}))
                await save_message(session_id, "assistant", full_response, route_taken=route)
                continue
            else:
                context = ""

            # Build prompt with history
            history = await get_history(session_id, limit=12)
            prompt = build_prompt(query, context=context, history=history)

            # Stream response
            full_response = ""
            for token in llm_engine.generate(prompt, max_tokens=512, stream=True):
                full_response += token
                await websocket.send_text(json.dumps({"type": "token", "data": token}))

            await websocket.send_text(json.dumps({
                "type": "done",
                "route": route,
                "confidence": confidence,
                "sources": sources
            }))

            await save_message(session_id, "assistant", full_response, route_taken=route, sources=sources)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
        except Exception:
            pass