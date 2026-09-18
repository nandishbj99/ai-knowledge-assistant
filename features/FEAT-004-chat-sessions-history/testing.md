# Feature Testing & Verification: FEAT-004 - Chat Sessions & Conversation History

> **Feature ID:** `FEAT-004`  
> **Status:** `PENDING_EXECUTION`  
> **Spec Reference:** [Feature Spec](./spec.md) | [Design & ADRs](./design.md)

---

## 1. Verification Strategy
1. **Ownership & Tenant Isolation:** User B cannot read, message into, or delete User A's session.
2. **Context Truncation:** History beyond 6 turns or 3,000 tokens is cleanly truncated from the prompt while retaining recent turns.
3. **Citation Snapshot Integrity:** Citations stored in `chat_messages` remain accessible and intact even if referenced document chunks are altered.
4. **Cascading Deletion:** Deleting a session deletes all child messages in PostgreSQL.

---

## 2. Test Case Matrix

| Test ID | Test Scenario | Target Component | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| `TC-01` | Create new chat session | `ChatSessionController` | Returns 201 Created with `sessionId` and current user's `ownerId` | `PENDING` |
| `TC-02` | Unauthorized session access (User B queries User A's session) | `ChatSessionController` | Returns 404 Not Found (or 403 Forbidden) | `PENDING` |
| `TC-03` | Sliding context window truncation (10 turns in thread) | `ConversationMemoryService` | Only last 6 turns (or <3,000 tokens) are provided to prompt | `PENDING` |
| `TC-04` | Multi-turn conversational resolution | `RAGService` | Model accurately resolves ambiguous pronouns ("they", "that expense") using prior turn | `PENDING` |
| `TC-05` | Cascading session deletion | `ChatSessionController` | `chat_messages` rows associated with `sessionId` are completely deleted | `PENDING` |

---

## 3. Manual Verification Steps (cURL)

```bash
# 1. Create Session
curl -i -X POST http://localhost:8080/api/v1/chat/sessions \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Audit Session"}'
# Expected: 201 Created {"sessionId": "..."}

# 2. Unauthorized access test
curl -i http://localhost:8080/api/v1/chat/sessions/<SESSION_ID>/messages \
  -H "Authorization: Bearer <DIFFERENT_USER_JWT>"
# Expected: 404 Not Found

# 3. Delete Session
curl -i -X DELETE http://localhost:8080/api/v1/chat/sessions/<SESSION_ID> \
  -H "Authorization: Bearer <JWT_TOKEN>"
# Expected: 204 No Content
```
