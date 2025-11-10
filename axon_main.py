import os
import sys
import uvicorn
import datetime
import webbrowser
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv

# --- LLM and RAG Imports (Using stable LangChain Core/Ollama paths) ---
import ollama
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_ollama.embeddings import OllamaEmbeddings
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# --- Initialization ---
load_dotenv()
ollama_host = "http://127.0.0.1:11434" # Confirmed local Ollama host

# --- App Setup ---
app = FastAPI(
    title="Axon Unified Core API",
    description="One stable server for all AI functions: Ollama, Gemini Tools, and Local RAG.",
    version="5.0.0"
)

# --- Pydantic Models ---
class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    response: str
    
class ErrorResponse(BaseModel):
    error: str

# =======================================================================
# SECTION 1: SIMPLE OLLAMA CHAT (General Knowledge)
# =======================================================================
try:
    ollama_client = ollama.Client(host=ollama_host)
    print(f"--- Ollama Client Initialized (Host: {ollama_host}) ---")
except Exception as e:
    print(f"Error initializing Ollama client: {e}")
    ollama_client = None

@app.post("/chat/ollama", 
          response_model=ChatResponse, 
          tags=["1. General Chat (Ollama)"],
          summary="General chat with local Ollama (Gemma)")
def chat_ollama(request: ChatRequest):
    """Answers general questions using the local Gemma model."""
    if not ollama_client:
        return {"error": "Ollama client is not initialized or server is offline."}, 500
    try:
        response = ollama_client.chat(
            model="gemma:latest",
            messages=[{'role': 'user', 'content': request.query}]
        )
        return ChatResponse(response=response['message']['content'])
    except Exception as e:
        return {"error": f"Ollama Chat Error: {e}"}, 500


# =======================================================================
# SECTION 2: GEMINI TOOLS (Actions & Time)
# =======================================================================
# --- Tool Definitions ---
def get_current_time() -> str:
    """Returns the current date and time."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def open_url(url: str) -> str:
    """Opens a specified URL in the default web browser."""
    try:
        webbrowser.open(url, new=2)
        return f"Successfully opened {url}"
    except Exception as e:
        return f"Error opening {url}: {e}"

# --- GenAI Setup ---
try:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not found. This endpoint is disabled.")
    
    genai.configure(api_key=GOOGLE_API_KEY)

    gemini_tools = [
        {"name": "get_current_time", "description": "Get the current time and date.", "parameters": {}},
        {"name": "open_url", "description": "Open a given URL.", "parameters": {"type": "OBJECT", "properties": {"url": {"type": "STRING"}}, "required": ["url"]}}
    ]
    available_tools = {"get_current_time": get_current_time, "open_url": open_url}
    
    tools_model = genai.GenerativeModel(model_name="gemini-2.5-flash", tools=gemini_tools)
    print("--- Gemini Tools Model Initialized ---")

except ValueError as e:
    print(f"Gemini Setup Error: {e}")
    tools_model = None

@app.post("/chat/tools",
          response_model=ChatResponse,
          tags=["2. Tools/Actions (Gemini)"],
          summary="Chat with Gemini to use tools (e.g., get time, open URL)")
async def chat_with_tools(request: ChatRequest):
    """Executes external actions using the Gemini API."""
    if not tools_model:
        return {"error": "Gemini API key not configured."}, 500
    try:
        chat = tools_model.start_chat(enable_automatic_function_calling=False)
        response = chat.send_message(request.query)
        
        # Tool execution logic
        if response.candidates[0].content.parts and response.candidates[0].content.parts[0].function_call:
            function_call = response.candidates[0].content.parts[0].function_call
            tool_name = function_call.name
            tool_args = dict(function_call.args)
            
            tool_response_string = available_tools[tool_name](**tool_args) if tool_args else available_tools[tool_name]()

            response = chat.send_message(
                {"function_response": {"name": tool_name, "response": {"result": tool_response_string}}}
            )
        
        return ChatResponse(response=response.candidates[0].content.parts[0].text)

    except Exception as e:
        return {"error": f"Gemini Tool Error: {e}"}, 500


# =======================================================================
# SECTION 3: LOCAL RAG CHAT (Personal Knowledge)
# =======================================================================
DB_PATH = "faiss_db"

try:
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Vector store not found at {DB_PATH}. Please run ingest.py first.")
    
    rag_embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url=ollama_host)
    db = FAISS.load_local(DB_PATH, rag_embeddings, allow_dangerous_deserialization=True)
    retriever = db.as_retriever(search_kwargs={"k": 5})

    answer_llm = ChatOllama(model="gemma:latest", base_url=ollama_host)
    query_llm = ChatOllama(model="gemma:latest", base_url=ollama_host)

    # Step-Back Prompt (for better retrieval)
    step_back_template = "You are an expert at query rewriting. Generate a broader, 'step-back' version of this question to retrieve more general context. User Question: {question} Step-Back Question:"
    step_back_prompt = PromptTemplate.from_template(step_back_template)

    # RAG Answer Prompt
    template = "You are 'Axon'. Answer the user's *original question* based *only* on the Context. If you don't know, state it clearly. Context: {context} Original Question: {question} Answer:"
    prompt = PromptTemplate.from_template(template)

    # RAG Chain Definition
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    rag_chain = (
        RunnablePassthrough.assign(
            step_back_query=step_back_prompt | query_llm | StrOutputParser()
        ).assign(
            context=(lambda x: x["step_back_query"]) | retriever | format_docs
        )
        | prompt
        | answer_llm
        | StrOutputParser()
    )
    print("--- Step-Back RAG Chain Ready ---")

except Exception as e:
    print(f"RAG Initialization Error: {e}")
    rag_chain = None

@app.post("/chat/rag",
          response_model=ChatResponse,
          tags=["3. Personal RAG (Ollama)"],
          summary="Chat with your local documents (e.g., resume)")
async def chat_with_rag(request: ChatRequest):
    """Answers questions based on local RAG documents."""
    if not rag_chain:
        return {"error": "RAG chain is not initialized. Vector store (faiss_db) missing or Ollama offline."}, 500
    try:
        answer = rag_chain.invoke({"question": request.query})
        return ChatResponse(response=answer)
    except Exception as e:
        return {"error": f"RAG Query Error: {e}"}, 500


# =======================================================================
# ROOT ENDPOINT AND SERVER START
# =======================================================================
@app.get("/", tags=["Status"])
def read_root():
    return {"status": "Axon Unified Server is online"}

if __name__ == "__main__":
    print("--- Starting Axon Unified Server (Local) ---")
    # Note: Using "axon_main:app" to reference this file/app in uvicorn.
    uvicorn.run("axon_main:app", host="127.0.0.1", port=8000)