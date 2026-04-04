from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  
from pydantic import BaseModel
from app.services.router import route_query
from app.services.rag_chain import query_knowledge_base
from app.services.tools_engine import execute_system_command
from app.services.general_chat import get_general_response

app = FastAPI(title="Axon Core Production API", version="6.0.0")

# --- CORS CONFIGURATION ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str

@app.post("/chat/orchestrator")
async def handle_chat(request: ChatRequest):
    route = route_query(request.query)
    
    if route == "rag":
        answer = query_knowledge_base(request.query)
        return {"route_taken": "rag", "response": answer}
        
    elif route == "tools":
        answer = execute_system_command(request.query)
        return {"route_taken": "tools", "response": answer}
        
    else:
        # --- REPLACED PLACEHOLDER WITH REAL LOGIC ---
        print(f"--- Routing to General AI ---")
        answer = get_general_response(request.query)
        return {"route_taken": "general", "response": answer}

@app.get("/health")
def health_check():
    return {"status": "healthy", "architecture": "microservices"}