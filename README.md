# Axon Core: Unified Multi-Modal Intelligence System

## 1. Architectural Mandate and System Overview

Axon Core is a sophisticated digital intelligence platform designed for the centralized orchestration of diverse cognitive functionalities within a single, optimized service layer. The system utilizes dynamic intent routing to delegate conversational tasks to specialized Large Language Models (LLMs), thereby ensuring optimal latency, enhanced response grounding, and efficient resource allocation across all operational domains.

The platform is engineered as a monolithic **Unified API Architecture** (FastAPI) that integrates three distinct Intelligent Processing Units (IPUs): General Knowledge, Real-World Action, and High-Fidelity Private Knowledge Retrieval. With the latest iteration (v5.0.0), Axon extends its capabilities to secure, local system management and software provisioning via dual-modal client interfaces (Voice and Text).

---

## 2. Technical Stack and Component Registry

| Component | Technology | Role in the System | Engineering Rationale |
| :--- | :--- | :--- | :--- |
| **API/Service Layer** | **Python (FastAPI)** | Unified, asynchronous entry point for all client requests. | Decouples client interface from cognitive backend complexity. |
| **LLM (General/RAG)** | **Ollama (Gemma:latest)** | Localized conversational intelligence and document grounding. | Minimizes external API dependency and operational cost. |
| **LLM (Tool-Use/Action)** | **Gemini 2.5 Flash** | Intent detection, reasoning, and **Function Calling** for system interaction. | Optimizes for speed and reliability in transactional tasks. |
| **Orchestration** | **LangChain** | RAG chain construction, prompt engineering, and data serialization. | Provides deterministic control over multi-model workflows. |
| **Vector Indexing** | **FAISS (CPU-Optimized)** | High-efficiency indexing/retrieval of dense vector embeddings. | Enables rapid access to the proprietary knowledge base. |
| **System Integration** | **Subprocess / Winget / Pip** | Controlled execution of shell commands for software provisioning. | Facilitates secure, parameterized system management. |
| **Client Interface** | **Dual-Modal (Voice/Text)** | Speech-to-Text (STT), Text-to-Speech (TTS), and CLI interaction. | Offers flexible, zero-latency system engagement. |

---

## 3. Advanced Cognitive Functionality and Intent Routing

Axon employs a deterministic routing matrix to delegate queries to the most capable internal IPU.

### A. IPU 1: High-Fidelity Private Knowledge Retrieval (`/chat/rag`)

Dedicated to answering questions exclusively from the user's proprietary document index.

* **Mechanism:** **Step-Back Query Generation**.
    1.  **Abstraction:** A preparatory LLM generates a generalized version of the user's specific query.
    2.  **Context Augmentation:** The generalized query retrieves broad context from the FAISS index to mitigate "dumb retrieval" failures.
    3.  **Grounding:** The retrieved context is synthesized with the original query for a factual, hallucination-free response.

### B. IPU 2: Integrated Reasoning and Tool Execution (`/chat/tools`)

Reserved for actions requiring external execution, real-time data access, or system modification.

* **Capabilities:**
    * **Real-Time Data:** Retrieval of temporal data (Time/Date).
    * **Web Interaction:** Automated browser navigation.
    * **Secure Software Provisioning:** Automated installation of Python packages (via `pip`) and Desktop Applications (via `winget`).
* **Security Protocol (Human-in-the-Loop):**
    To prevent unauthorized system modification, Axon implements a **Secure Execution Handshake**. The server generates the shell command (e.g., `winget install VLC`) but does *not* execute it. Instead, it returns an `EXECUTE_CMD` signal to the client, forcing a blocking user-confirmation prompt before execution occurs.

### C. IPU 3: Generalized Conversational Intelligence (`/chat/ollama`)

The foundational layer for non-specialized, common knowledge tasks, utilizing locally hosted models for resource efficiency.

---

## 4. Operational Workflow and Client Architecture

The system supports dual-modal input via two specialized clients: `voice_client.py` (Speech) and `text_client.py` (CLI).

### Execution Sequence

1.  **Input Acquisition:** User provides input via Microphone (Wake Word: `Axon`) or Terminal Command.
2.  **Intent Classification (Client-Side Routing):** The client classifies the command using a keyword matrix:
    * **System/Action Keywords** (*install, package, time, open*) → **Route to `/chat/tools`**.
    * **Knowledge Keywords** (*resume, project, skills, contact*) → **Route to `/chat/rag`**.
    * **Default Fallback** → **Route to `/chat/ollama`**.
3.  **API Processing:** The Unified Server processes the request via the selected IPU.
4.  **Action Handling (If applicable):**
    * If the IPU generates a system command (e.g., software installation), the server returns an `EXECUTE_CMD` payload.
    * The Client detects this payload and pauses for user authorization (`y/n`).
    * Upon authorization, the Client executes the command via a secure `subprocess` shell.
5.  **Response Synthesis:** The final output is presented via TTS (Voice Client) or Standard Output (Text Client).

---

## 5. Deployment and Setup Guide

### Prerequisites

* Python 3.10+
* Local Ollama Server application installed and running.
* A Gemini API Key (for tool use).
* Windows OS (required for `winget` functionality; adaptable for Linux).

### Setup and Execution

1.  **Clone Repository & Install Dependencies:**
    ```bash
    git clone [REPO_URL] axon-core
    cd axon-core
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    
    # Install dependencies including RAG, Voice, and System tools
    python -m pip install fastapi uvicorn ollama google-generativeai python-dotenv pypdf faiss-cpu langchain langchain-community langchain-ollama langchain-core speechrecognition pyttsx3 requests
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
    Run the unified API server and your preferred client interface.
    
    **Terminal 1 (Unified Server):**
    ```bash
    .\.venv\Scripts\python.exe axon_main.py
    ```
    
    **Terminal 2 (Client - Choose One):**
    * **Voice Interface:**
        ```bash
        .\.venv\Scripts\python.exe voice_client.py
        ```
    * **Text/CLI Interface:**
        ```bash
        .\.venv\Scripts\python.exe text_client.py
        ```