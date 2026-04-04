import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings import OllamaEmbeddings
from qdrant_client import QdrantClient

# Configurations
QDRANT_URL = "http://qdrant:6333"
COLLECTION_NAME = "axon_knowledge"
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://172.17.0.1:11434")

def ingest_documents(data_path: str):
    print(f"--- Scanning directory: {data_path} ---")
    
    # 1. Load PDFs and Text files specifically
    pdf_loader = DirectoryLoader(data_path, glob="./*.pdf", loader_cls=PyPDFLoader)
    txt_loader = DirectoryLoader(data_path, glob="./*.txt", loader_cls=TextLoader)
    
    # Combine all found documents
    documents = pdf_loader.load() + txt_loader.load()
    
    if not documents:
        print("No documents found to ingest! Check your /data folder.")
        return

    for doc in documents:
        print(f"Successfully Loaded: {doc.metadata.get('source')}")

    # 2. Split text into manageable chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = text_splitter.split_documents(documents)
    
    print(f"Total chunks created: {len(chunks)}")
    
    # 3. Initialize Embeddings and Vector Store
    embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url=OLLAMA_HOST)
    
    print(f"Ingesting into Qdrant at {QDRANT_URL}...")
    
    Qdrant.from_documents(
        chunks,
        embeddings,
        url=QDRANT_URL,
        collection_name=COLLECTION_NAME,
        force_recreate=True  # Wipes old data to ensure the new files are active
    )
    print("--- Ingestion complete! Axon's memory is updated. ---")

def get_retriever():
    client = QdrantClient(url=QDRANT_URL)
    embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url=OLLAMA_HOST)
    qdrant = Qdrant(client=client, collection_name=COLLECTION_NAME, embeddings=embeddings)
    
    # Return top 10 results for better accuracy
    return qdrant.as_retriever(search_kwargs={"k": 10})