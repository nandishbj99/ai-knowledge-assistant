# Feature Tasks & Execution Plan: FEAT-004 - Chat Sessions & Conversation History

> **Feature ID:** `FEAT-004`  
> **Status:** `COMPLETED`  
> **Current Focus / Next Action:** Chat session and history management implemented and verified in Spring Boot backend.  
> **Owner:** Engineering Team  
> **Last Updated:** 2026-09-17

---

## 1. Quick Status Dashboard

| Metric | Value |
| :--- | :--- |
| **Current Phase** | `Verification Complete` |
| **Tasks Completed** | 8 / 8 (100%) |
| **Blockers** | None |
| **Ready for Next Phase?** | Yes |

---

## 2. Immediate Actions Needed
- [x] Action 1: Review and sign off on ADR-01 through ADR-04 in [design.md](./design.md).
- [x] Action 2: Apply `chat_sessions` and `chat_messages` schemas with tenant scoping.
- [x] Action 3: Implement `ChatSessionController` and sliding context window service in Spring Boot.

---

## 3. Phased Task Breakdown

### Phase 1: Database & Entities
- [x] **TASK-01:** Create `ChatSession` and `ChatMessage` JPA entities with `(tenant_id, user_id)` scoping and foreign key cascading.
- [x] **TASK-02:** Implement `ChatSessionRepository` and `ChatMessageRepository` with tenant-isolated query methods.

### Phase 2: Session Management REST APIs
- [x] **TASK-03:** Implement `POST /api/v1/chat/sessions` (create session) and `GET /api/v1/chat/sessions` (list user's sessions).
- [x] **TASK-04:** Implement `GET /api/v1/chat/sessions/{id}/messages` and `DELETE /api/v1/chat/sessions/{id}` with ownership validation.

### Phase 3: Sliding Context Window Service
- [x] **TASK-05:** Implement `ChatSessionService.getRecentContext` fetching last turns (max 6 messages / <3,000 tokens) formatted for RAG prompt consumption.
- [x] **TASK-06:** Implement immutable citation snapshot persistence into `chat_messages.citations`.

### Phase 4: Verification & Testing
- [x] **TASK-07:** Verify compiling entity and controller suite with `mvn compile`.
- [x] **TASK-08:** Update status to `COMPLETED` in `specs/main-spec.md`.
