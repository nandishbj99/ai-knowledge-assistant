# Phased Implementation Roadmap

This document outlines the systematic, iterative engineering flow for delivering the **AI Knowledge Assistant**. Each phase builds cleanly on the preceding phase and includes concrete verification gates.

---

## Phase 1: Infrastructure & Data Foundations
**Objective:** Stand up the local execution environment, PostgreSQL with `pgvector`, and Redis.

- [ ] **1.1 Docker Compose Setup:**
  - PostgreSQL 16 image with `pgvector` pre-installed (`pgvector/pgvector:pg16`).
  - Redis 7 alpine image with persistence volume.
  - Health checks and shared network setup.
- [ ] **1.2 Database Initialization & Migrations:**
  - Run `01-init-pgvector.sql` on startup.
  - Verify vector extension, table creations, foreign keys, and HNSW indexes.
- [ ] **1.3 Environment & Config Baseline:**
  - Establish `.env.example` templates for both services (API keys, DB credentials, ports).

**Verification Gate:** Docker containers run healthy; pgvector cosine similarity test query executes successfully.

---

## Phase 2: Python AI Microservice (Ingestion & RAG Engine)
**Objective:** Build high-performance document parsing, chunking, embeddings, and citation-grounded retrieval.

- [ ] **2.1 Document Parser:**
  - PDF/DOCX/TXT extraction with page-level tracking using `pypdf` / `pdfplumber`.
  - Content sanitization and table preservation.
- [ ] **2.2 Chunking & Embedding Pipeline:**
  - Recursive chunking with configurable overlap.
  - Integration with LLM embedding provider (OpenAI or Gemini).
  - Batch insertion into `document_chunks` table.
- [ ] **2.3 Vector Search & Retriever:**
  - HNSW similarity query with distance metric `<=>`.
  - Metadata filtering by document ID list and user tenancy.
- [ ] **2.4 Grounded Prompting & Citation Synthesizer:**
  - Formulate strict grounding prompts.
  - LLM completion invocation.
  - Inline citation parser extracting `[Doc: ..., p. ...]` and assembling structured citation JSON.
- [ ] **2.5 FastAPI REST Endpoints:**
  - `POST /api/v1/ingest`
  - `POST /api/v1/rag/generate`
  - `GET /health`

**Verification Gate:** Ingestion script successfully indexes a sample multi-page PDF; querying yields relevant grounded answers with exact page citations.

---

## Phase 3: Spring Boot Core Backend (Gateway, Auth & Document Upload)
**Objective:** Implement enterprise security, rate limiting, and document management.

- [ ] **3.1 Project Scaffolding & Dependencies:**
  - Spring Boot 3.x with Spring Web, Spring Security, Spring Data JPA, Redis, Lombok, JJWT.
- [ ] **3.2 Authentication & Security:**
  - User registration & login with BCrypt password hashing.
  - JWT token generation, stateless filtering, and SecurityContext integration.
- [ ] **3.3 Distributed Redis Rate Limiter:**
  - Token Bucket rate limiting filter for sensitive endpoints (Uploads, Auth, Chat).
- [ ] **3.4 Document Lifecycle Management:**
  - Multipart upload handler saving files to storage.
  - Document JPA repository and status tracking (`PENDING`, `PROCESSING`, `INDEXED`, `FAILED`).
  - Async dispatch of ingestion jobs to the Python AI service via WebClient / REST.

**Verification Gate:** Authenticated user can upload a PDF; rate limiting blocks bursts exceeding threshold; upload status transitions correctly.

---

## Phase 4: Chat Sessions, History & End-to-End RAG Integration
**Objective:** Connect Spring Boot chat endpoints to Python AI service with multi-turn history.

- [ ] **4.1 Chat Sessions & Messages Persistence:**
  - Session creation, listing, and message archiving.
- [ ] **4.2 Proxy Service & AI Client:**
  - Spring Boot calls Python `/api/v1/rag/generate` passing user query + last $N$ turns of history.
  - Persists AI responses and structured citations in `chat_messages`.
- [ ] **4.3 Error Handling & Fallbacks:**
  - Timeout management and graceful degradation if AI service or LLM provider is slow.

**Verification Gate:** Multi-turn conversation works across sessions; previous context is retained and citations are accurately displayed.

---

## Phase 5: Containerized Orchestration & End-to-End Evaluation
**Objective:** Package entire system into unified Docker Compose with automated verification.

- [ ] **5.1 Dockerfiles:**
  - Multi-stage Dockerfile for Spring Boot.
  - Lightweight Python Dockerfile.
- [ ] **5.2 End-to-End Test Suite:**
  - End-to-end integration test (Register -> Upload Document -> Wait for Indexing -> Chat Query -> Verify Citations).
- [ ] **5.3 Operational Readiness:**
  - Swagger UI / OpenAPI documentation.
  - Prometheus / Actuator health metrics.
