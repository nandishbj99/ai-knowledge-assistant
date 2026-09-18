# AI Knowledge Assistant

> Build a system where users upload company documents and ask questions — and get answers grounded in those documents, with citations.

Upload PDF, DOCX, or TXT files. The system parses them, extracts tables and charts, creates vector embeddings, and stores everything in PostgreSQL. Ask a question in plain English — the system finds the most relevant sections, sends them to an LLM, and returns a cited answer tied directly to your documents. No hallucinations. Every claim is backed by a source.

---

## How It Works

### Upload Flow

```
User uploads document (PDF / DOCX / TXT)
         │
         ▼
  MIME magic-byte validation
  File size check  (max 50 MB)
  Page count check (max 100 pages)
         │
         ▼
  Original file  ──────────────────▶  Object Storage
  Document record (status = PENDING)  PostgreSQL
         │
         ▼
  Job enqueued  ──────────────────────▶  Redis Stream
                                              │
                              ┌───────────────┘
                              ▼
                    Ingestion Worker  (async, Python)
                              │
               ┌──────────────┴──────────────┐
               ▼                             ▼
     Text + Table path             Chart / Figure path
     ─────────────────             ───────────────────
     PyMuPDF  (text)               fitz  (crop bounding box)
     pdfplumber  (tables           Gemini 2.5 Flash  (vision)
       → Markdown)                 → Markdown data table
               │                             │
               └──────────────┬──────────────┘
                              ▼
              Split into two levels:
              Parent chunks  (~1,200 tokens)  ──▶  parent_chunks table
              Child chunks   (~180 tokens)
                              │
                              ▼
              text-embedding-004  →  768-dim vectors
                              │
                              ▼
              document_chunks table  (pgvector HNSW index)
              Document status  →  INDEXED
```

### Query Flow

```
User asks a question in a chat session
         │
         ▼
  Verify session ownership  (tenant_id + user_id)
  Load last 6 messages  (max 3,000 tokens sliding window)
         │
         ▼
  text-embedding-004  →  768-dim query vector
         │
         ▼
  HNSW cosine search on  document_chunks
  (filtered strictly by tenant_id + user_id)
         │
         ▼
  Expand matched child chunks  →  full parent sections
         │
         ▼
  Label context:  [SOURCE-1]  [SOURCE-2]  ...
         │
         ▼
  Gemini 2.5 Flash  (grounded prompt, temp = 0.1)
  "Cite facts only using [SOURCE-X] tags. Do not use
   pre-training knowledge outside the provided context."
         │
         ▼
  Server validates  SOURCE  tags
  Strips any hallucinated IDs
  Resolves metadata from DB  (filename, page number, snippet)
         │
         ▼
  Answer  +  verified citations  [SOURCE-1 → Annual_Report.pdf, p.18]
  Saved to chat_messages  (citations stored as immutable JSONB snapshot)
```

---

## Tech Stack

### Backend API
| Technology | Version | Role |
| :--- | :--- | :--- |
| Spring Boot | 3.x | REST API, JWT auth, rate limiting, session management |
| Java | 21 | Application runtime |
| Apache Tika | Latest | MIME magic-byte validation on upload |

### AI Service
| Technology | Version | Role |
| :--- | :--- | :--- |
| Python + FastAPI | 3.11+ | Ingestion worker + answer engine |
| PyMuPDF (fitz) | Latest | PDF text extraction, page-by-page |
| pdfplumber | Latest | Table detection → Markdown conversion |
| Google text-embedding-004 | — | 768-dim semantic embeddings (free tier) |
| Google Gemini 2.5 Flash | — | Answer generation + chart vision analysis |

### Infrastructure
| Technology | Version | Role |
| :--- | :--- | :--- |
| PostgreSQL + pgvector | 16 + 0.7+ | Relational metadata + HNSW vector search |
| Redis | 7+ | Async job queue (Streams) + rate limiting (Lua) + JWT blacklist |
| Object Storage | — | Original uploaded files (local volume / S3-compatible) |
| Docker + Compose | Latest | Local development environment |

---

## Features

### Document Processing
- **Upload** PDF, DOCX, and TXT files (max 50 MB, 100 pages)
- **MIME validation** — magic-byte sniffing blocks disguised executables
- **Async processing** — upload returns immediately (202); status polled via `GET /documents/{id}/status`
- **Table extraction** — pdfplumber converts tables to Markdown pipe format; headers re-injected across chunk splits
- **Chart & figure analysis** — Gemini Vision reconstructs visual charts into Markdown data tables
- **Two-level chunking** — Parent chunks (~1,200 tokens) for LLM context; Child chunks (~180 tokens) for vector search
- **Resilient worker** — 3 retries with exponential backoff (5s / 15s / 45s), Dead-Letter Queue on failure
- **Idempotent re-processing** — re-uploading the same document cleans up old chunks first

### Semantic Search & RAG
- **768-dim HNSW vector index** in pgvector for fast approximate nearest-neighbour search
- **Parent-document expansion** — search finds child chunks, then delivers full parent sections to LLM for rich context
- **Zero-hallucination grounding** — LLM is forbidden from answering outside the provided document context
- **Opaque citation keys** — LLM only writes `[SOURCE-1]`, never filenames or page numbers; server resolves and verifies these
- **Immutable citation snapshots** — citations saved as JSONB at answer time; survive future document edits or deletions

### Conversations
- **Named chat sessions** — organize questions by topic
- **Multi-turn memory** — last 6 turns (max 3,000 tokens) passed to LLM for pronoun/context resolution
- **Full message history** — chronological thread with citations per message
- **Cascading deletion** — deleting a session removes all messages

### Security
- **JWT authentication** — 15-min access tokens + 7-day rotating refresh tokens
- **Token revocation** — logout writes to Redis blacklist; tokens rejected immediately
- **Multi-tenant isolation** — every DB query is filtered by `(tenant_id, user_id)`; cross-tenant access returns 404
- **Redis rate limiting** — atomic Lua token bucket per endpoint:
  - Auth: 10 req / min per IP
  - Uploads: 5 req / hour per user
  - Chat: 30 req / min per user

---

## AI Models

| Capability | Primary Model | Fallback |
| :--- | :--- | :--- |
| Text embeddings | Google `text-embedding-004` (768-dim) | OpenAI `text-embedding-3-small` (1536-dim) |
| Answer generation | Google `gemini-2.5-flash` | `gemini-2.5-pro` / `gpt-4o-mini` |
| Chart & figure analysis | Google `gemini-2.5-flash` (vision) | OpenAI `gpt-4o-mini` |

> All primary models run on **Google AI Studio free tier** — zero cost to prototype and run.

---

## Ingestion Strategies

### Strategy A — Default (CPU, free tier)

The default pipeline. Works on any machine.

- Parent chunks (~1,200 tokens) stored as plain text in `parent_chunks` — no embedding
- Child chunks (~180 tokens) embedded as 768-dim vectors in `document_chunks`
- Vector search finds child chunks → query expands to full parent for LLM context
- Tables kept intact in parent; header rows re-injected into split chunks
- Charts analyzed by Gemini Vision → stored as descriptive Markdown chunks

### Strategy B — Visual RAG / ColPali (GPU required)

An advanced alternative for visually complex documents.

- Renders each PDF page as a high-resolution image (150–300 DPI)
- ColPali (PaliGemma) generates ~1,024 visual patch vectors per page
- Queries matched against patch vectors via late interaction (MaxSim)
- Full page images fed directly to Gemini 2.5 Flash — no text parsing at all

Enable with: `INGESTION_STRATEGY=colpali`

---

## API Endpoints

### Auth
| Method | Path | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | Create account |
| `POST` | `/api/v1/auth/login` | Login → access + refresh tokens |
| `POST` | `/api/v1/auth/refresh` | Refresh access token |
| `POST` | `/api/v1/auth/logout` | Revoke token (Redis blacklist) |

### Documents
| Method | Path | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/documents/upload` | Upload document → 202 Accepted |
| `GET` | `/api/v1/documents/{id}/status` | Poll indexing status |
| `DELETE` | `/api/v1/documents/{id}` | Delete document + all chunks + file |

### Chat
| Method | Path | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/chat/sessions` | Create chat session |
| `GET` | `/api/v1/chat/sessions` | List your sessions |
| `GET` | `/api/v1/chat/sessions/{id}/messages` | Get message thread |
| `POST` | `/api/v1/chat/sessions/{id}/messages` | Ask a question |
| `DELETE` | `/api/v1/chat/sessions/{id}` | Delete session + messages |

---

## Project Structure

```
ai-knowledge-assistant/
├── README.md
├── .env.example                         # Environment variable template
├── docker/
│   ├── docker-compose.yml               # Full local stack
│   └── init-db/01-init-pgvector.sql     # Schema, extensions, HNSW index
├── backend/                             # Spring Boot API (Java 21)
│   ├── Dockerfile
│   ├── pom.xml
│   └── src/
├── ai-service/                          # Python FastAPI RAG service
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
├── specs/
│   └── main-spec.md                     # Full architecture specification
└── features/
    ├── README.md                        # Feature status dashboard
    ├── FEAT-001-document-ingestion/
    ├── FEAT-002-rag-query-citations/
    ├── FEAT-003-auth-and-rate-limiting/
    └── FEAT-004-chat-sessions-history/
```

---

## Quick Start

```bash
# 1. Copy environment variables
cp .env.example .env
# Add your GOOGLE_API_KEY

# 2. Start the full stack
docker compose -f docker/docker-compose.yml up -d

# 3. Register and get a token
curl -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@company.com","password":"Password123!","fullName":"Your Name"}'

# 4. Upload a document
curl -X POST http://localhost:8080/api/v1/documents/upload \
  -H "Authorization: Bearer <TOKEN>" \
  -F "file=@./report.pdf"
# → Returns documentId + status: "PENDING"

# 5. Poll until INDEXED
curl http://localhost:8080/api/v1/documents/<ID>/status \
  -H "Authorization: Bearer <TOKEN>"

# 6. Create a session and ask a question
curl -X POST http://localhost:8080/api/v1/chat/sessions \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Q3 Analysis"}'

curl -X POST http://localhost:8080/api/v1/chat/sessions/<SESSION_ID>/messages \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"query":"What were our top operating expenses in Q3?"}'
```

---

## Documentation

- [Full Architecture Specification](specs/main-spec.md)
- [Feature Registry & Status](features/README.md)
- [FEAT-001: Document Ingestion — Design & ADRs](features/FEAT-001-document-ingestion/design.md)
- [FEAT-002: RAG Query & Citations — Design & ADRs](features/FEAT-002-rag-query-citations/design.md)
- [FEAT-003: Auth & Rate Limiting — Design & ADRs](features/FEAT-003-auth-and-rate-limiting/design.md)
- [FEAT-004: Chat Sessions & History — Design & ADRs](features/FEAT-004-chat-sessions-history/design.md)
