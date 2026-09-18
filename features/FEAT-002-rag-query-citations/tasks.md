# Feature Tasks & Execution Plan: FEAT-002 - Grounded RAG Query & Citations

> **Feature ID:** `FEAT-002`  
> **Status:** `COMPLETED`  
> **Current Focus / Next Action:** Grounded RAG query pipeline and opaque [SOURCE-X] citation resolution implemented and verified.  
> **Owner:** Engineering Team  
> **Last Updated:** 2026-09-17

---

## 1. Quick Status Dashboard

| Metric | Value |
| :--- | :--- |
| **Current Phase** | `Verification Complete` |
| **Tasks Completed** | 7 / 7 (100%) |
| **Blockers** | None |
| **Ready for Next Phase?** | Yes |

---

## 2. Immediate Actions Needed
- [x] Action 1: Review and approve ADR-01 and ADR-03.
- [x] Action 2: Implement Vector Retriever SQL query using `<=>`.
- [x] Action 3: Build Grounded Prompt Template and Citation Regex Parser.

---

## 3. Phased Task Breakdown

### Phase 1: Python Vector Retrieval Service
- [x] **TASK-01:** Implement `VectorRetriever.search()` in `ai-service/app/services/retriever.py` with multi-tenant filtering, parent chunk deduplication, and HNSW cosine distance (`<=>`).
- [x] **TASK-02:** Verify query vector generation via `EmbeddingService.get_query_embedding()` with 768 dimensions and unit normalization.

### Phase 2: RAG Generation & Citation Extraction
- [x] **TASK-03:** Implement `RAGService.build_prompt()` with strict grounding system prompt and server-assigned opaque keys `[SOURCE-X]`.
- [x] **TASK-04:** Implement `RAGService._extract_citations()` resolving opaque keys against authoritative server metadata and discarding hallucinations.
- [x] **TASK-05:** Implement `POST /query` endpoint in FastAPI.

### Phase 3: Spring Boot Proxy & History Persistence
- [x] **TASK-06:** Implement `RAGService` and `ChatQueryController` in Spring Boot calling Python RAG endpoint and persisting conversation turns to `chat_messages`.
- [x] **TASK-07:** Run unit tests in `ai-service/tests/test_rag.py`.
