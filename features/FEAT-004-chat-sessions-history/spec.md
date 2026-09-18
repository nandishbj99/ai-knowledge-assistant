# Feature Specification: FEAT-004 - Chat Sessions & Conversation History

> **Feature ID:** `FEAT-004`  
> **Feature Name:** Chat Sessions & Conversation History  
> **Status:** `DESIGN_READY`  
> **Parent Spec:** [Master Project Spec](../../specs/main-spec.md)  
> **Design & ADRs:** [Design & ADRs](./design.md) | **Tasks:** [Tasks](./tasks.md) | **Testing:** [Testing](./testing.md)

---

## 1. Overview & Objective
Provides persistent multi-turn conversational session management. Users can create distinct chat sessions, review conversational history, resume discussions with sliding-window context memory, and cleanly delete sessions with all associated message turns. Every session is strictly isolated to its owner and tenant.

---

## 2. User Stories
- **US-01:** As a user, I want to create and name chat sessions so that I can organize research on different topics separately.
- **US-02:** As a user, I want follow-up questions in an ongoing session to recall prior turns (e.g. pronoun disambiguation: "What were their expenses?").
- **US-03:** As an auditor, I want each past assistant response to retain its verified citations even after the session concludes.
- **US-04:** As a user, I want to delete a conversation session and ensure all messages and history are permanently purged.

---

## 3. Scope & Requirements

### Functional Requirements (FR)
- **FR-01 (Create Session):** `POST /api/v1/chat/sessions` with optional title, initializing a session tied to `(user_id, tenant_id)`.
- **FR-02 (List Sessions):** `GET /api/v1/chat/sessions` returning paginated list of sessions owned by the authenticated user.
- **FR-03 (Get Session Messages):** `GET /api/v1/chat/sessions/{id}/messages` returning the chronological message thread with associated citations.
- **FR-04 (Sliding Context Window):** When generating answers, only the last $N$ turns (or max 4,000 conversation tokens) are forwarded to the RAG service to maintain prompt efficiency.
- **FR-05 (Session Deletion):** `DELETE /api/v1/chat/sessions/{id}` cascades deletion to all messages in `chat_messages`.
- **FR-06 (Data Retention Policy):** Configurable retention window (default 90 days); background cleanup purges expired sessions.

---

## 4. API Contracts

### Create Session
```http
POST /api/v1/chat/sessions HTTP/1.1
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
  "title": "Q3 Financial Audit"
}
```

**Response (201 Created):**
```json
{
  "sessionId": "e7b0a852-51c3-4d43-85f2-9517e4bb0234",
  "title": "Q3 Financial Audit",
  "ownerId": "d290f1ee-6c54-4b01-90e6-d701748f0851",
  "tenantId": "d290f1ee-6c54-4b01-90e6-d701748f0851",
  "createdAt": "2026-09-17T10:00:00Z"
}
```

### List Messages in Session
```http
GET /api/v1/chat/sessions/e7b0a852-51c3-4d43-85f2-9517e4bb0234/messages HTTP/1.1
Authorization: Bearer <JWT_TOKEN>
```

**Response (200 OK):**
```json
[
  {
    "id": "c1a2b3c4-...",
    "sender": "USER",
    "content": "What were our top operating expenses?",
    "citations": [],
    "createdAt": "2026-09-17T10:01:00Z"
  },
  {
    "id": "d2b3c4d5-...",
    "sender": "ASSISTANT",
    "content": "In Q3, R&D expenses reached $14.2M [SOURCE-1].",
    "citations": [
      {
        "sourceKey": "[SOURCE-1]",
        "documentId": "a143b821-...",
        "documentTitle": "Annual_Report.pdf",
        "pageNumber": 18,
        "snippet": "R&D expenditures rose to $14.2M..."
      }
    ],
    "createdAt": "2026-09-17T10:01:03Z"
  }
]
```
