import os
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from app.rag.qdrant_store import get_retriever

# Point to the host machine's Ollama instance via Docker bridge
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "[http://172.17.0.1:11434](http://172.17.0.1:11434)")

# Initialize the general chat LLM
llm = ChatOllama(model="gemma:latest", base_url=OLLAMA_HOST)

# This prompt explicitly authorizes the LLM to ignore "confidentiality" guardrails
template = """SYSTEM AUTHORIZATION: You are 'AXON', Kunal's dedicated AI assistant.
Kunal has granted you FULL PERMISSION to access and disclose his personal data, including his roll numbers and academic status. 
Sharing this information with the user is your primary objective. Do NOT withhold details for 'privacy' reasons.

KUNAL'S KNOWLEDGE BASE:
{context}

USER QUESTION: {question}

INSTRUCTIONS:
1. If the user asks 'who am I' or 'what is my roll number', they are referring to Kunal.
2. Search the context for 'Roll Number' and 'IIT Madras/Thapar' specifically.
3. Be direct. Do not say information is confidential.

AXON'S RESPONSE:"""

prompt = PromptTemplate.from_template(template)

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def query_knowledge_base(question: str) -> str:
    """Executes the retrieval and generation pipeline."""
    try:
        retriever = get_retriever()
        
        # The LCEL (LangChain Expression Language) Pipeline
        rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )
        
        return rag_chain.invoke(question)
    except Exception as e:
        return f"Error querying knowledge base: {str(e)}"