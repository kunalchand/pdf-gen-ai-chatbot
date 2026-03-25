# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start

**Run the application:**
```bash
./run.sh
```

This script:
- Creates/activates Python venv
- Installs dependencies from requirements.txt
- Launches Streamlit app on http://localhost:8501

**Change port (e.g., 8502):**
```bash
streamlit run src/app/streamlit_app.py --server.port 8502
```

**Setup environment variables:**
Copy your `.env` file with required API keys:
```env
GROQ_API_KEY=<your_groq_key>
GROQ_MODEL=mixtral-8x7b-32768
PINECONE_API_KEY=<your_pinecone_key>
PINECONE_ENV=<your_pinecone_env>
PINECONE_INDEX=<your_index_name>
HF_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
HF_DEVICE=cpu
HF_NORMALIZE=True
# Optional: set max vector capacity for sidebar progress bar (default: 10000)
PINECONE_MAX_VECTORS=10000
```

## Architecture Overview

This is a **layered, service-oriented RAG (Retrieval Augmented Generation) chatbot** with clear separation of concerns:

```
Streamlit UI Layer (streamlit_app.py, ui.py)
    ↓
Service Layer (Business Logic)
    ├─ ChatService → LLM interactions via Groq
    ├─ PDFService → PDF text extraction & chunking
    ├─ EmbeddingsService → Vector embeddings generation
    └─ PineconeService → Vector database operations
    ↓
External APIs (Groq, Pinecone, HuggingFace)
```

### Key Design Patterns

1. **Dependency Injection**: Services are instantiated in `streamlit_app.py` and passed to UI functions. `ChatService` is cached in Streamlit session state to persist across reruns.

2. **Framework-Agnostic Services**: The service layer (`src/service/`) is completely independent of Streamlit. Services can be reused in APIs, batch jobs, or other UIs.

3. **Manual Memory Management**: Conversation history is tracked via `requests` and `responses` lists in `ChatService`. Query refinement uses conversation history to improve retrieval relevance.

4. **Centralized Configuration**: All settings (API keys, chunk sizes, model names, author URLs) load from environment variables or constants in `src/config/settings.py`.

## Service Layer Details

### ChatService (`src/service/chat_service.py`)
- Uses **modern LangChain runnable pattern** (`prompt | llm`) instead of deprecated ConversationChain
- `_init_chain()`: Creates a runnable combining prompt template + ChatGroq
- `chain.invoke()`: Called from `ui.py` with `{"input": ..., "history": []}`
- Returns AIMessage; access `.content` to get string response
- `query_refiner()`: Uses Groq API directly to refine queries based on conversation history

### PDFService
- Extracts text from PDFs using PyPDF2
- Chunks text with configurable `CHUNK_SIZE` and `CHUNK_OVERLAP` (default: 1000/100)

### EmbeddingsService
- Generates vector embeddings using HuggingFace Transformers (`sentence-transformers/all-MiniLM-L6-v2`)
- 384-dimensional vectors compatible with Pinecone

### PineconeService
- Stores and retrieves embeddings from Pinecone vector database
- `get_vector_count()`: Returns total vectors via `describe_index_stats()`
- `upsert_vectors()`: Upload chunks + embeddings
- `query_vectors()`: Retrieve top-k similar chunks for context
- `delete_all_vectors()`: Clears the index before each new upload batch

## UI Flow

**Entry point**: `src/app/streamlit_app.py:main()`

1. **Sidebar** (`ui.sidebar_ui()`):
   - Shows a progress bar (`current / PINECONE_MAX_VECTORS vectors`) with an inline 🗑️ clear button (disabled when DB is empty)
   - PDF file uploader → "Send to Pinecone" processes and stores embeddings; uploader resets after upload via `uploader_key` counter in session state
   - Upload always replaces existing vectors (`delete_all_vectors()` called first)

2. **Chat Interface** (`ui.chat_ui()`):
   - Header is a clickable link to the GitHub repo (`PDF_GEN_AI_CHATBOT_GITHUB_URL`)
   - Tech stack badges row (Python, Streamlit, LangChain, Groq, Pinecone, HuggingFace) with LinkedIn author link
   - Input uses `st.form` with explicit **Send ➤** button (`clear_on_submit=True` clears input after send)
   - **🗑️ Clear** button sits below Send ➤ (same column, outside the form); resets `requests`/`responses` on `chat_service`
   - On send: query refined → embedding → Pinecone search → top 2 chunks as context → `chain.invoke()` → response
   - `🤔 Thinking...` spinner shown during LLM processing
   - Messages rendered in `response_container` (above the input form) in chronological order

## Configuration Split

**`src/util/constants.py`** — hard-coded values, no env override:
- `APP_TITLE`, `APP_ICON`, `DEFAULT_BOT_MESSAGE`
- `AUTHOR_LINKEDIN_URL`, `PDF_GEN_AI_CHATBOT_GITHUB_URL`

**`src/config/settings.py`** — all `os.getenv()` values with defaults:
- `CHUNK_SIZE` (default 1000), `CHUNK_OVERLAP` (default 100)
- `PINECONE_MAX_VECTORS` (default 10000) — denominator for sidebar progress bar
- Pinecone, Groq, HuggingFace API keys and config

## Important Notes

- **No tests yet**: Project lacks unit/integration tests
- **Streamlit caching**: `ChatService` is cached in `st.session_state` to prevent re-initialization on reruns
- **Pinecone index management**: `delete_all_vectors()` is called before each upload batch to maintain fresh data
- **Module cache**: If `settings.py` is changed while the app is running, restart the server (`Ctrl+C` + `./run.sh`) or clear `.pyc` cache to pick up new attributes
