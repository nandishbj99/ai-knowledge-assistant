# Feature Registry Dashboard: AI Knowledge Assistant

> **Status:** Active Project Tracking  
> **Workflow Pattern:** [Spec-Driven Development (`/go`)](../.agents/skills/spec-driven-development/SKILL.md)

This directory contains modular feature packages for each capability in the system. Each feature contains:
- `spec.md`: User stories, functional and non-functional requirements, input/output schemas.
- `design.md`: High-Level Design (HLD) diagrams, sequence flows, and **Architecture Decision Records (ADRs)**.
- `tasks.md`: Status, current focus/next action, phased task checklist, and blockers.
- `testing.md`: Test strategy, test cases, and verification criteria.

---

## Active & Registered Features

| Feature ID | Feature Title | Status | Implementation Highlights | Directory Link |
| :--- | :--- | :--- | :--- | :--- |
| `FEAT-001` | Document Ingestion Pipeline | `COMPLETED` | Apache Tika magic sniffing, Redis Streams worker (`ingestion:tasks`), Parent-Child chunking, 768d Gemini embeddings | [`FEAT-001`](./FEAT-001-document-ingestion/design.md) |
| `FEAT-002` | Grounded RAG Query & Citations | `COMPLETED` | Tenant-isolated HNSW vector search, parent chunk expansion, opaque `[SOURCE-X]` citations with Gemini 2.5 Flash | [`FEAT-002`](./FEAT-002-rag-query-citations/design.md) |
| `FEAT-003` | JWT Auth & Redis Rate Limiting | `COMPLETED` | Spring Security 6, 15m access token, 7d refresh rotation, Redis blacklist, atomic Lua token bucket | [`FEAT-003`](./FEAT-003-auth-and-rate-limiting/design.md) |
| `FEAT-004` | Chat Sessions & Conversation History | `COMPLETED` | Tenant-scoped session CRUD, sliding window context (<3,000 tokens), immutable citation snapshot persistence | [`FEAT-004`](./FEAT-004-chat-sessions-history/design.md) |

---

## Lifecycle Workflow (`/go`)

All features have transitioned through:
1. **Scaffold / Check:** Scans `features/` and reports current status.
2. **ADR Review:** Creates and reviews ADRs before touching any code.
3. **Execution:** Works through `tasks.md` item by item.
4. **Verification:** Validates test cases in `testing.md`.
