# Feature Tasks & Execution Plan: FEAT-001 - Document Ingestion Pipeline

> **Feature ID:** `FEAT-001`  
> **Status:** `COMPLETED`  
> **Current Focus / Next Action:** Implementation complete across Spring Boot gateway, Redis Streams worker, Parent-Child chunker, and 768d Gemini embedder.  
> **Owner:** Engineering Team  
> **Last Updated:** 2026-09-17

---

## 1. Quick Status Dashboard

| Metric | Value |
| :--- | :--- |
| **Current Phase** | `Implementation & Unit Tests Complete` |
| **Tasks Completed** | 14 / 14 (100%) |
| **Blockers** | None |
| **Ready for Next Phase?** | Yes |

---

## 2. Immediate Actions Needed
- [x] Action 1: Confirm user sign-off on revised ADR-01 through ADR-11.
- [x] Action 2: Apply multi-tenant schema to `01-init-pgvector.sql` (Parent/Child + 768d + Tenant Scoping).
- [x] Action 3: Implement durable Redis Streams worker and Spring Boot upload publisher.

---

## 3. Phased Task Breakdown

### Phase 1: Database DDL & Multi-Tenant Schema Setup
- [x] **TASK-01:** Apply database schema in `docker/init-db/01-init-pgvector.sql` with `users`, `documents`, `parent_chunks`, and `document_chunks` (vector 768d, `user_id`, `tenant_id`, and `idx_chunks_embedding_hnsw`).
- [x] **TASK-02:** Verify PostgreSQL + pgvector schema structure and composite indexes `(tenant_id, user_id)`.

### Phase 2: Ingestion Safety & Gateway Dispatch (Spring Boot)
- [x] **TASK-03:** Implement MIME magic-byte sniffing (Apache Tika) rejecting invalid or disguised file formats.
- [x] **TASK-04:** Implement file upload limits enforcement (max 50MB) and tenant-partitioned storage directory.
- [x] **TASK-05:** Implement `POST /api/v1/documents/upload` inserting document record (`status = 'PENDING'`, `user_id`, `tenant_id`) and publishing task to Redis Stream `ingestion:tasks`.
- [x] **TASK-06:** Implement `GET /api/v1/documents/{id}/status` strictly verifying tenant/owner authorization before returning progress.
- [x] **TASK-07:** Implement `DELETE /api/v1/documents/{id}` enforcing ownership, cascading DB deletion of parent/child chunks, and removing raw file.

### Phase 3: Resilient AI Ingestion Worker (Python / Redis Streams)
- [x] **TASK-08:** Implement Redis Streams consumer group worker (`worker.py`) with acknowledgment (`XACK`).
- [x] **TASK-09:** Implement exponential backoff retry loop (max 3 attempts) and Dead-Letter Queue (`dlq:ingestion`) handler.
- [x] **TASK-10:** Implement `ParentDocumentChunker` producing parent chunks (~1,200 tokens) and child chunks (~180 tokens) with tenant tagging.
- [x] **TASK-11:** Integrate `DocumentParser` extracting clean page sections.
- [x] **TASK-12:** Integrate Google `text-embedding-004` (768d) batch embedding for child chunks and transactional persistence.

### Phase 4: Verification & Sign-Off
- [x] **TASK-13:** Execute verification unit tests (`test_chunker.py`, `test_embedder.py`).
- [x] **TASK-14:** Mark feature as `COMPLETED` in `specs/main-spec.md`.
