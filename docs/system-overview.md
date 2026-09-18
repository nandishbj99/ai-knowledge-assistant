# System Overview & Architecture

## 1. High-Level Vision

The **AI Knowledge Assistant** is designed as a modular, resilient multi-service platform for enterprise document retrieval and intelligence. The system allows authenticated users to upload proprietary files (PDFs, reports, product manuals, legal agreements) and ask questions in natural language. It returns grounded answers accompanied by verifiable inline citations (e.g., *"[Document: Security_Whitepaper.pdf, Page: 14]"*).

---

## 2. Component Diagram

```mermaid
flowchart TB
    subgraph Client["Client Application"]
        UI["Web / Mobile / CLI Clients"]
    end

    subgraph SpringBoot["Backend Gateway (Spring Boot 3.x)"]
        direction TB
        SecurityFilter["Spring Security + JWT Validator"]
        RateLimiter["Redis Token Bucket Rate Limiter"]
        DocController["Document Controller (/api/v1/documents)"]
        ChatController["Chat Controller (/api/v1/chat)"]
        SessionService["Session & History Service"]
        StorageService["Physical Storage Manager (Local / S3)"]
    end

    subgraph DataStore["Persistence & Vector Layer"]
        Postgres[("PostgreSQL 16 + pgvector\n- Relational: Users, Docs, Sessions, Messages\n- Vector Chunks (HNSW Index)")]
        Redis[("Redis In-Memory Store\n- Rate Limit Tokens\n- Active Session Caching\n- Ingestion Task Queue")]
    end

    subgraph PythonAI["AI & RAG Engine (Python / FastAPI)"]
        direction TB
        IngestionWorker["Ingestion Pipeline\n- PyMuPDF Parser\n- Recursive Text Chunker\n- Embedding Client"]
        RAGRetriever["RAG Retrieval Engine\n- Cosine Similarity (<=>)\n- Metadata Filter & Re-ranker"]
        LLMOrchestrator["Prompt Orchestrator\n- Strict Grounding Rules\n- Citation Synthesizer"]
    end

    UI -->|HTTPS / Bearer Token| SecurityFilter
    SecurityFilter --> RateLimiter
    RateLimiter --> DocController
    RateLimiter --> ChatController

    DocController --> StorageService
    DocController -->|Insert Doc (PENDING)| Postgres
    DocController -->|Push Ingestion Task| Redis

    Redis -->|Consume Task| IngestionWorker
    IngestionWorker -->|Read Raw File| StorageService
    IngestionWorker -->|Insert Chunks & Vectors| Postgres
    IngestionWorker -->|Update Doc (INDEXED)| Postgres

    ChatController --> SessionService
    SessionService -->|Fetch Context History| Postgres
    ChatController -->|Forward Query + History| RAGRetriever

    RAGRetriever -->|Vector Cosine Search| Postgres
    RAGRetriever --> LLMOrchestrator
    LLMOrchestrator -->|Answer + Citations| ChatController
    ChatController -->|Save User Query & AI Answer| Postgres
```

---

## 3. Component Responsibilities

### 3.1 Backend Gateway (Spring Boot)
- **Security & Authorization:** Role-based access control (RBAC), JWT token issuance and stateless validation.
- **Distributed Rate Limiting:** Granular rate limits per user/IP using Redis token buckets (e.g., 5 document uploads per 10 minutes, 60 queries per minute).
- **Document Management:** Multi-part file upload, mime-type verification, virus scanning hook, metadata tracking.
- **Conversation State:** Stores historical sessions, threads, message turns, and feedback ratings.
- **Client Facing:** Consistent REST error formats, SSE (Server-Sent Events) streaming support for real-time token streaming.

### 3.2 AI & RAG Engine (Python FastAPI)
- **Format Parsing:** High-fidelity text, table, and metadata extraction from PDF, DOCX, Markdown, and TXT files.
- **Chunking Pipeline:** Chunk boundaries respect section headings, paragraphs, and sentence boundaries with configurable token overlaps (default: 600 tokens with 100 token overlap).
- **Vector Embeddings:** Batch embedding generation using industry standard models (OpenAI `text-embedding-3-small` / Gemini `text-embedding-004`).
- **Retriever Engine:** Executes HNSW approximate nearest neighbor search via SQL against `pgvector` with cosine distance (`<=>`), scoped by user/tenant permissions or selected document subsets.
- **LLM Grounding & Citation Engine:** Enforces system instructions compelling the LLM to ground answers exclusively in retrieved chunks, outputting citation tags linked back to specific chunk and document IDs.

---

## 4. Key Architectural Trade-offs & Decisions

| Decision | Chosen Option | Alternative Considered | Justification |
| :--- | :--- | :--- | :--- |
| **Vector Database** | PostgreSQL with `pgvector` | Dedicated Vector DB (Pinecone, Qdrant, Milvus) | Eliminates distributed transaction issues. Relational data (users, document permissions, messages) and vectors live in a single ACID-compliant database. |
| **Backend & AI Split** | Spring Boot + Python FastAPI microservices | Monolithic Spring Boot (Spring AI) or Monolithic Python | Leverages Spring Boot's enterprise security, typing, and ecosystem alongside Python's richer document parsing and AI/ML toolchains. |
| **Vector Indexing** | HNSW (Hierarchical Navigable Small World) | IVFFlat | HNSW provides higher queries-per-second (QPS) and superior recall at scale without requiring periodic retraining. |
| **Ingestion Pattern** | Asynchronous via Redis queue | Synchronous HTTP | PDF parsing and batch embedding can take several seconds to minutes; synchronous HTTP would lead to timeouts and poor UX. |
