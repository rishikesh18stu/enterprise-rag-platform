# Enterprise Multi-Agent RAG Platform

A production-style Retrieval-Augmented Generation (RAG) platform built from scratch to learn and demonstrate modern AI engineering: multi-format document ingestion, hybrid search, a LangGraph multi-agent pipeline, JWT authentication, a full Next.js frontend, streaming responses, evaluation, monitoring, and Docker deployment.

Built as a hands-on learning project — every component was implemented, debugged, and validated end-to-end rather than scaffolded from a template.

---

## Features

- **Multi-format ingestion**: PDF, DOCX, PPTX, XLSX, TXT, Markdown, and websites(can be uploaded via terminal)
- **Hierarchical parent-child chunking** with `AutoMergingRetriever` (small chunks for precise search, large parent chunks for LLM context)
- **Hybrid search**: dense (embedding) + sparse (BM25) retrieval fused natively in Qdrant
- **Cross-encoder reranking** (`BAAI/bge-reranker-base`) to filter irrelevant retrieved chunks
- **7-agent LangGraph pipeline**: Router → Rewrite → Retrieve → Rerank → Citation → Answer → Memory
- **Conversation memory** via Redis, with real multi-turn follow-up resolution ("tell me more about that")
- **JWT authentication** with role-based users (Admin / Manager / Employee), bcrypt password hashing
- **Full Next.js frontend**: login, ChatGPT-style chat (with streaming), document upload, dashboard, analytics, settings
- **Server-Sent Events streaming** for token-by-token chat responses
- **RAGAS evaluation**: faithfulness, answer relevancy, context precision, context recall on a hand-curated eval set
- **LangSmith tracing** for automatic, code-free observability into every agent node
- **Fully Dockerized**: one `docker-compose up` spins up backend, frontend, Qdrant, Redis, and PostgreSQL

---

## Tech Stack

**Backend:** Python, FastAPI, LangGraph, LlamaIndex, PostgreSQL, Redis
**Frontend:** Next.js, React, TypeScript, Tailwind CSS
**AI:** Ollama (local LLM: `llama3.2`, embeddings: `nomic-embed-text`), Sentence Transformers (reranker)
**Vector DB:** Qdrant (hybrid dense + sparse search)
**Auth:** JWT (`python-jose`), bcrypt (`passlib`)
**Evaluation/Monitoring:** RAGAS, LangSmith
**Deployment:** Docker, Docker Compose

---

## Architecture

```
                          ┌─────────────┐
                          │   Router    │
                          └──────┬──────┘
                    ┌────────────┴────────────┐
              (retrieval)                  (direct)
                    │                           │
              ┌─────▼─────┐               ┌─────▼──────┐
              │  Rewrite  │               │Direct Answer│
              └─────┬─────┘               └─────┬──────┘
              ┌─────▼─────┐                      │
              │ Retrieve  │                      │
              │ (Hybrid)  │                      │
              └─────┬─────┘                      │
              ┌─────▼─────┐                      │
              │  Rerank   │                      │
              └─────┬─────┘                      │
              ┌─────▼─────┐                      │
              │ Citation  │                      │
              └─────┬─────┘                      │
              ┌─────▼─────┐                      │
              │  Answer   │                      │
              └─────┬─────┘                      │
              ┌─────▼─────┐                      │
              │  Memory   │◄─────────────────────┘
              │  (Redis)  │
              └───────────┘
```

Ingestion pipeline (separate from query-time flow):

```
Document/Website → Loader → Hierarchical Chunking (1024/256 tokens)
    → Embed leaf nodes → Store in Qdrant (dense + sparse)
    → Persist parent nodes in local docstore
```

---

## Project Structure

```
enterprise-rag/
├── backend/
│   ├── agents/          # LangGraph nodes, state, graph definition, rewrite agent
│   ├── api/              # FastAPI routes (chat, streaming, upload)
│   ├── auth/              # JWT auth, password hashing, protected-route dependency
│   ├── database/           # SQLAlchemy models and session management
│   ├── evaluation/          # RAGAS eval dataset and runner
│   ├── ingestion/            # Document loaders and chunking/embedding pipeline
│   ├── memory/                # Redis conversation memory
│   ├── main.py                 # FastAPI app entrypoint
│   └── requirements.txt
├── frontend/
│   └── src/app/           # Next.js pages: login, chat, upload, dashboard, analytics, settings
├── docker-compose.yml
└── README.md
```

---

## Running Locally (without Docker)

**Prerequisites:** Python 3.10+, Node.js, Docker (for Qdrant/Redis/PostgreSQL), [Ollama](https://ollama.com)

```bash
# Pull local models
ollama pull llama3.2
ollama pull nomic-embed-text

# Start infrastructure
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
docker run -p 6379:6379 redis
docker run -p 5432:5432 -e POSTGRES_PASSWORD=devpassword -e POSTGRES_DB=enterprise_rag postgres

# Backend
cd backend
python -m venv venv
venv\Scripts\Activate.ps1   # Windows; use `source venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
python init_db.py
uvicorn main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000`.

## Running with Docker

```bash
docker-compose up --build
```

Then, in a separate terminal:
```bash
docker-compose exec backend python init_db.py
```

Visit `http://localhost:3000`.

---

## Evaluation

Run the RAGAS evaluation suite against the hand-curated question set:
```bash
cd backend
python -m evaluation.run_eval
```

Latest recorded results:

| Metric | Score |
|---|---|
| Context Precision | 1.00 |
| Context Recall | 0.83 |
| Faithfulness | 0.80 |
| Answer Relevancy | 0.65 |

Context precision is strong, indicating hybrid search + reranking are effectively filtering out irrelevant chunks. Answer relevancy is the weakest metric — the current answer-generation prompt favors literal context reproduction, which can cause the model to under-address the specific phrasing of a question. Next step would be prompt refinement targeting more direct question-answering behavior.

---

## Known Limitations

Documented honestly rather than hidden — these are real architectural tradeoffs made under project scope, not oversights.

1. **Uploaded documents require a backend restart to become queryable.** The parent-node docstore is loaded once into memory at server startup for performance. New uploads correctly merge into the persisted docstore on disk, but the running process doesn't hot-reload it. Fix would involve either a database-backed docstore or a file-watcher-triggered reload.
2. **Retrieval imprecision on long, multi-topic source documents.** Vague follow-up questions (e.g., "tell me more") can occasionally retrieve a tangential section of a long document (e.g., a references list) rather than the most conceptually central content. Reranking improves *relative* ranking but doesn't guarantee the most central chunk always wins.
3. **`/chat/stats` uses Redis `KEYS`** for simplicity, which is a blocking, non-scalable pattern at production scale. `SCAN` (cursor-based, non-blocking) would be the production-correct choice.
4. **Local LLM inference is slow** (10–130+ seconds for generation depending on context size, per LangSmith traces), which is why streaming (Phase 12) was prioritized — it improves perceived responsiveness even though total latency is unchanged.

---

## Roadmap / Not Yet Implemented

- Live document indexing without backend restart
- Cloud deployment (AWS/Azure/GCP/Render)
- Long-term (cross-session) memory
- Per-role access control on documents (currently all authenticated users share one knowledge base)

---

## License

MIT (or update as preferred)
