import os
import sys
from fastapi import FastAPI
from pydantic import BaseModel

# Import the correct, modern paths we know work
from langchain_community.vectorstores import FAISS
from langchain_ollama.embeddings import OllamaEmbeddings
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# --- RAG Pipeline Setup ---
DB_PATH = "faiss_db"
EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "gemma:latest" # Use a fast model for the main answer
QUERY_LLM_MODEL = "gemma:latest" # Use a fast model for rewriting the query

# Check if DB exists
if not os.path.exists(DB_PATH):
    print(f"Vector store not found at {DB_PATH}. Please run ingest.py first.")
    sys.exit(1)

print("Loading vector store and initializing RAG chain...")

# Get Ollama host from environment variable
ollama_host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")

# 1. Load the vector store and create a retriever
embeddings = OllamaEmbeddings(model=EMBED_MODEL, base_url=ollama_host)
db = FAISS.load_local(DB_PATH, embeddings, allow_dangerous_deserialization=True)
retriever = db.as_retriever(search_kwargs={"k": 5}) # Get top 5 chunks

# 2. Define our LLMs
answer_llm = ChatOllama(model=LLM_MODEL, base_url=ollama_host)
query_llm = ChatOllama(model=QUERY_LLM_MODEL, base_url=ollama_host)

# 3. Create the "Step-Back" Prompt for query rewriting
step_back_template = """
You are an expert at query rewriting.
Your task is to take a user's question and generate a more general, "step-back" version of that question.
This new question will be used to retrieve relevant documents from a vector store.
By generating a broader question, you help the retriever find context that the specific question might miss.

Example:
User Question: "What projects are listed on Kunal's resume?"
Step-Back Question: "What is Kunal's general project experience and technical history?"

User Question: "What is Kunal's email address?"
Step-Back Question: "What are Kunal's contact details?"

Now, generate the step-back question for this:
User Question: {question}
Step-Back Question:
"""
step_back_prompt = PromptTemplate.from_template(step_back_template)

# 4. Create the main RAG prompt for the final answer
template = """
You are 'Axon', a helpful AI assistant. Answer the user's *original question* based *only* on the
following context provided from their personal documents.
If you don't know the answer from the context,
clearly state that you don't have that information.

Context:
{context}

Original Question:
{question}

Answer:
"""
prompt = PromptTemplate.from_template(template)

# 5. Build the new, smarter RAG chain
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# ======================= THIS IS THE FIX =======================
# This chain is simpler and uses RunnablePassthrough.assign()
# to correctly build up the dictionary of keys.
chain = RunnablePassthrough.assign(
    # This adds the "step_back_query" key to our dictionary
    step_back_query=step_back_prompt | query_llm | StrOutputParser()
).assign(
    # This uses the "step_back_query" key to create the "context" key
    context=(lambda x: x["step_back_query"]) | retriever | format_docs
)
# At this point, our dictionary has "question", "step_back_query", and "context"

# Pipe the final dictionary into the prompt and the LLM
rag_chain = chain | prompt | answer_llm | StrOutputParser()
# ===============================================================

print("--- Step-Back RAG Chain Ready ---")

# --- FastAPI Server ---
app = FastAPI(
    title="Axon Core API (with RAG)",
    description="Assistant using Ollama, Step-Back RAG (Phase 4).",
    version="4.2.0"
)

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    response: str
    
class ErrorResponse(BaseModel):
    error: str

@app.get("/", tags=["Status"])
def read_root():
    return {"status": "Axon Core (with RAG) is online"}

@app.post("/chat_rag",
          response_model=ChatResponse,
          tags=["Chat"],
          responses={500: {"model": ErrorResponse}})
async def chat_with_rag(request: ChatRequest):
    """
    Receives a query, runs it through the RAG chain, and returns the answer.
    """
    try:
        print(f"\n--- New RAG Query: {request.query} ---")
        # The input to our chain must be a dictionary with a "question" key
        answer = rag_chain.invoke({"question": request.query})
        print(f"--- RAG Answer: {answer} ---")
        return ChatResponse(response=answer)
    except Exception as e:
        print(f"Error in /chat_rag: {e}")
        return {"error": str(e)}, 500

# --- Server Start ---
if __name__ == "__main__":
    import uvicorn
    print("--- Starting Axon RAG Server directly ---")
    uvicorn.run(app, host="127.0.0.1", port=8000)