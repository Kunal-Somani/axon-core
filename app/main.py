from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.services.router import route_query

app = FastAPI(title="Axon Core Production API", version="6.0.0")

class ChatRequest(BaseModel):
    query: str

@app.post("/chat/orchestrator")
async def handle_chat(request: ChatRequest):
    # 1. Semantically route the query
    route = route_query(request.query)
    
    # 2. Delegate to the specific service based on the route
    if route == "tools":
        # TODO: Call your Gemini tool-calling logic here
        return {"route_taken": "tools", "status": "pending_implementation"}
        
    elif route == "rag":
        # TODO: Call your new Qdrant RAG pipeline here
        return {"route_taken": "rag", "status": "pending_implementation"}
        
    else:
        # TODO: Call Ollama general chat here
        return {"route_taken": "general", "status": "pending_implementation"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "architecture": "microservices"}