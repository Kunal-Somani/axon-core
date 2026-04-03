from langchain_community.document_loaders import PyPDFLoader
from langchain_textsplitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
import os
import sys

DATA_PATH = "data"
DB_PATH = "faiss_db"
EMBED_MODEL = "nomic-embed-text" # A good, fast embedding model

def build_vector_store():
    """Scans 'data' folder, processes PDFs, and saves them to a FAISS vector store."""
    if not os.path.exists(DATA_PATH):
        print(f"Data path '{DATA_PATH}' not found. Creating it.")
        os.makedirs(DATA_PATH)
        print("Please add some PDF files to the 'data' directory and run again.")
        return

    print("Loading documents from 'data' folder...")
    documents = []
    for f in os.listdir(DATA_PATH):
        if f.endswith(".pdf"):
            pdf_path = os.path.join(DATA_PATH, f)
            print(f"Loading {pdf_path}...")
            loader = PyPDFLoader(pdf_path)
            documents.extend(loader.load())
    
    if not documents:
        print("No PDF documents found in the 'data' directory. Exiting.")
        return

    print(f"Loaded {len(documents)} document pages.")
    
    print("Splitting documents into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    texts = text_splitter.split_documents(documents)
    
    if not texts:
        print("No text could be extracted from the documents. Exiting.")
        return
        
    print(f"Split into {len(texts)} chunks.")

    print(f"Initializing embeddings model ({EMBED_MODEL}). This may take a moment...")
    # This uses your local Ollama. Make sure Ollama is running!
    try:
        # We must point this to the Ollama server, just in case
        ollama_host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
        embeddings = OllamaEmbeddings(model=EMBED_MODEL, base_url=ollama_host)
    except Exception as e:
        print(f"Error initializing Ollama embeddings. Is Ollama running?")
        print(f"Error: {e}")
        sys.exit(1)
        
    print("Creating and saving vector store (FAISS)...")
    db = FAISS.from_documents(texts, embeddings)
    db.save_local(DB_PATH)
    
    print(f"--- Vector store successfully built at '{DB_PATH}' ---")

if __name__ == "__main__":
    print("--- Axon RAG Ingestion ---")
    print(f"Pulling embedding model '{EMBED_MODEL}'...")
    # Make sure Ollama server is running
    os.system(f"ollama pull {EMBED_MODEL}")
    
    build_vector_store()