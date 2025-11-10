# Axon Core: Unified Multi-Modal Intelligence System

## 1. Architectural Mandate and System Overview

Axon Core is a sophisticated digital intelligence platform designed for the centralized orchestration of diverse cognitive functionalities within a single, optimized service layer. The system utilizes dynamic intent routing to delegate conversational tasks to specialized Large Language Models (LLMs), thereby ensuring optimal latency, enhanced response grounding, and efficient resource allocation across all operational domains.

The platform is engineered as a monolithic **Unified API Architecture** (FastAPI) that integrates three distinct Intelligent Processing Units (IPUs): General Knowledge, Real-World Action, and High-Fidelity Private Knowledge Retrieval.

---

## 2. Technical Stack and Component Registry

| Component | Technology | Role in the System | Engineering Rationale |
| :--- | :--- | :--- | :--- |
| **API/Service Layer** | **Python (FastAPI)** | Provides a unified, asynchronous, high-throughput entry point for all client requests, maintaining service stability under high load. | Decouples client interface from cognitive backend complexity. |
| **LLM (General/RAG)** | **Ollama (Gemma:latest)** | Serves low-latency, localized conversational intelligence and private document grounding, leveraging local compute resources. | Minimizes external API dependency and cost for internal queries. |
| **LLM (Tool-Use/Action)** | **Gemini 2.5 Flash** | Manages sophisticated intent detection, high-level reasoning, and **Function Calling** for system interaction. | Optimizes for speed and reliability in transactional, external tasks. |
| **Orchestration/Flow** | **LangChain** | Manages complex data routing, RAG chain construction, prompt engineering, and input/output serialization across LLMs. | Provides deterministic, auditable control over multi-model workflow execution. |
| **Vector Indexing** | **FAISS (CPU-Optimized)** | Provides highly efficient, sub-second indexing and retrieval of dense vector embeddings from proprietary, unstructured data. | Enables rapid, local access to the personal knowledge base. |
| **Client Interface** | **Speech Recognition / PyTTSX3** | Manages client-side multi-modal I/O (Speech-to-Text, Text-to-Speech) for hands-free system engagement. | Establishes a zero-latency interactive conversational experience. |

---

## 3. Advanced Cognitive Functionality and Intent Routing

Axon's primary innovation lies in its ability to **dynamically route** a single user query to the most capable internal IPU based on linguistic intent.

### A. IPU 1: High-Fidelity Private Knowledge Retrieval (`/chat/rag`)

This is the most complex IPU, dedicated to answering questions exclusively from the user's proprietary document index (Vector Store).

* **Retrieval Mechanism:** **Step-Back Query Generation**
    1.  **Intent Parsing:** The system receives a specific question (e.g., "What is the contact email?").
    2.  **Query Abstraction:** A preparatory LLM (`Gemma:latest`) is used to generate a **broader, more generalized query** (e.g., "What are Kunal's contact details?").
    3.  **Context Augmentation:** The generalized query is executed against the FAISS index, ensuring the retrieval of broad, relevant context that the specific question might have missed.
    4.  **Grounding:** The comprehensive retrieved context and the *original, specific question* are presented to the final LLM for a precise, factual answer.
* **Result:** This technique fundamentally mitigates common "dumb retrieval" failures in standard RAG, yielding highly accurate and reliable synthesis of internal document data.

### B. IPU 2: Integrated Reasoning and Tool Execution (`/chat/tools`)

This unit is reserved for actions that require external execution or real-time data access, utilizing the superior reasoning of the Gemini model.

* **Functioning:** The model identifies an executable action (e.g., "Open YouTube," "Get Time") and translates the request into a discrete Python function call, maintaining a controlled execution sandbox.

### C. IPU 3: Generalized Conversational Intelligence (`/chat/ollama`)

This foundational layer handles all non-specialized, common knowledge tasks. It utilizes the locally hosted Ollama model to manage simple conversation, serving as the default IPU for efficient resource management.

---

## 4. Operational Workflow (Execution Sequence)

The client application follows a critical path sequence to determine the appropriate service:

1.  **Client Input:** User speaks the **Wake Word** (`Axon`).
2.  **Intent Classification (Client-Side):** The client application classifies the subsequent command using a simple keyword routing matrix:
    * **IF** keywords like *'time,' 'open,' 'date'* are detected → **Route to `/chat/tools` (Gemini)**.
    * **ELSE IF** keywords like *'resume,' 'Kunal,' 'project'* are detected → **Route to `/chat/rag` (Local RAG)**.
    * **ELSE** → **Route to `/chat/ollama` (Local General Chat)**.
3.  **API Execution:** The request is sent to the specific endpoint of the unified `axon_main.py` server.
4.  **System Response:** The appropriate IPU processes the request and returns the final synthesized answer to the client for Text-to-Speech (TTS) output.

---

## 5. Deployment and Setup Guide

### Prerequisites

* Python 3.10+
* Local Ollama Server application installed and running.
* A Gemini API Key (for tool use).

### Setup and Execution

1.  **Clone Repository & Install Dependencies:**
    ```bash
    git clone [REPO_URL] axon-core
    cd axon-core
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    
    # Install all dependencies (ensuring stability across all LLM tools)
    python -m pip install fastapi uvicorn ollama google-generativeai python-dotenv pypdf faiss-cpu langchain langchain-community langchain-ollama langchain-core
    ```

2.  **Secure API Key Configuration:**
    Create the private configuration file using the provided template:
    ```bash
    cp .env.txt .env
    # NOTE: Securely insert your GOOGLE_API_KEY into the new .env file.
    ```

3.  **Knowledge Base Provisioning (RAG):**
    Place your private PDF documents into the **`data/`** directory, then ingest the data:
    ```bash
    .\.venv\Scripts\python.exe ingest.py
    ```

4.  **Final Execution:**
    Run the unified API server and the smart client in separate terminals.
    
    **Terminal 1 (Server):**
    ```bash
    .\.venv\Scripts\python.exe axon_main.py
    ```
    
    **Terminal 2 (Client):**
    ```bash
    .\.venv\Scripts\python.exe voice_client.py
    ```