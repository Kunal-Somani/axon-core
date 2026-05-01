import os
import json
import base64
import time
import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from app.rag.embedder import embedder
from app.rag.qdrant_store import ensure_collection, ingest_chunks, get_collection_stats
from app.rag.document_processor import process_file
from app.core.llm_engine import llm_engine, build_prompt
from app.core.router import semantic_router
from app.core.memory import init_db, save_message, get_history, get_full_history
from app.services.retrieval_engine import retrieve, format_context, update_bm25_index, build_bm25_from_qdrant, reranker
from app.services.tools_engine import execute_tool, get_available_tools, TOOL_GRAMMAR
from app.services.vision_engine import vision_engine
from app.services.speech_service import whisper_stt, kokoro_tts

STARTUP_TIME = time.time()

_executor = ThreadPoolExecutor(max_workers=1)

async def run_llm(prompt: str, max_tokens: int = 512) -> list[str]:
    """Run blocking LLM inference in thread pool, collect all tokens."""
    loop = asyncio.get_event_loop()
    tokens = []
    def _generate():
        for t in llm_engine.generate(prompt, max_tokens=max_tokens, stream=True):
            tokens.append(t)
    await loop.run_in_executor(_executor, _generate)
    return tokens
# TODO: upgrade to asyncio.Queue-based streaming in v4

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n=== Axon Starting Up ===")
    await init_db()
    ensure_collection()
    embedder.load()
    
    await asyncio.get_event_loop().run_in_executor(None, build_bm25_from_qdrant)
    print("=== BM25 index rebuilt from Qdrant ===")
    # Whisper and TTS load lazily — just log their status
    print(f"=== Whisper model exists: {whisper_stt.health_check()['model_exists']} ===")
    
    # Router and LLM load lazily on first use to avoid blocking startup
    # Vision loads lazily too
    print("=== Axon Ready ===\n")
    yield

app = FastAPI(title="Axon AI Backend", version="2.0.0", lifespan=lifespan)

_origins_raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
_origins = [o.strip() for o in _origins_raw.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
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
            "reranker": reranker.health_check() if hasattr(reranker, 'health_check') else {"loaded": reranker._model is not None},
            "vision": vision_engine.health_check(),
            "whisper": whisper_stt.health_check(),
            "tts": kokoro_tts.health_check(),
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

@app.post("/audio/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """Accepts audio file, returns transcription text."""
    audio_bytes = await file.read()
    loop = asyncio.get_event_loop()
    transcript = await loop.run_in_executor(
        _executor, whisper_stt.transcribe, audio_bytes, file.content_type
    )
    return {"transcript": transcript}

class SynthRequest(BaseModel):
    text: str

@app.post("/audio/synthesize")  
async def synthesize_speech(request: SynthRequest):
    """Accepts text, returns audio bytes as WAV."""
    loop = asyncio.get_event_loop()
    audio_bytes = await loop.run_in_executor(
        _executor, kokoro_tts.synthesize, request.text
    )
    return Response(content=audio_bytes, media_type="audio/wav")

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
                image_context = vision_engine.analyze(image_bytes, user_prompt=query)
                context = f"The user sent an image.\n{image_context}"
            elif route in ("personal_knowledge_query", "document_analysis"):
                results = retrieve(query, strategy="hybrid")
                context = format_context(results)
                sources = [{"source": r["source"], "score": r.get("score", 0)} for r in results]
            elif route == "system_tool_execution":
                # Use LLM to extract tool name and params
                tool_prompt = f"""<|system|>
You are a tool-calling assistant. Given the user request and available tools, 
output a valid JSON tool call.
Available tools: {get_available_tools()}
<|end|>
<|user|>
{query}
<|end|>
<|assistant|>
"""
                try:
                    raw_call = llm_engine.generate_structured(tool_prompt, TOOL_GRAMMAR, max_tokens=150)
                    tool_call = json.loads(raw_call)
                    if tool_call["tool"] not in get_available_tools():
                        full_response = f"Unknown tool requested: {tool_call['tool']}"
                    else:
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

            # Stream response via thread pool to unblock event loop
            full_response = ""
            tokens = await run_llm(prompt, max_tokens=512)
            for token in tokens:
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