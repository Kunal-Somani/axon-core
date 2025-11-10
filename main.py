import ollama
from fastapi import FastAPI
from pydantic import BaseModel

# --- App Setup ---
app = FastAPI(
    title="Axon Core API",
    description="The core brain of the Axon assistant (Phase 1).",
    version="1.0.0"
)

# --- Pydantic Models ---
class ChatRequest(BaseModel):
    """Request model for the chat endpoint."""
    query: str
    model: str = "gemma:latest" # Using the model you have

class ChatResponse(BaseModel):
    """Response model for the chat endpoint."""
    response: str
    
class ErrorResponse(BaseModel):
    """Error response model."""
    error: str

# --- API Endpoints ---
@app.get("/", tags=["Status"])
def read_root():
    """Root endpoint to check if the API is running."""
    return {"status": "Axon Core is online"}

@app.post("/chat", 
          response_model=ChatResponse, 
          tags=["Chat"],
          responses={500: {"model": ErrorResponse}})
def chat(request: ChatRequest):
    """
    Receives a user query and returns a response from the local Ollama model.
    """
    try:
        response = ollama.chat(
            model=request.model,
            messages=[{'role': 'user', 'content': request.query}]
        )
        
        assistant_response = response['message']['content']
        
        return ChatResponse(response=assistant_response)
    
    except Exception as e:
        print(f"Ollama error: {e}")
        return {"error": str(e)}, 500

# --- Server Start Command ---
# To run this server, use the command in your terminal:
# uvicorn main:app --reload