import os
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://172.17.0.1:11434")
llm = ChatOllama(model="gemma:latest", base_url=OLLAMA_HOST)

prompt = ChatPromptTemplate.from_template("""
You are Axon, a helpful and intelligent AI assistant. 
Answer the following user query directly and conversationally.

User: {query}
Axon:""")

def get_general_response(query: str) -> str:
    """Straight connection to Gemma for non-RAG/non-Tool queries."""
    try:
        chain = prompt | llm | StrOutputParser()
        return chain.invoke({"query": query})
    except Exception as e:
        return f"General chat engine error: {str(e)}"