# API Contracts & REST Specifications

This document defines the REST API interfaces for both the **Spring Boot Core Gateway** (client-facing) and the **Python AI Microservice** (internal service-to-service).

---

## 1. Spring Boot Gateway APIs (Client Facing)

Base URL: `/api/v1`

### 1.1 Authentication Endpoints

#### `POST /auth/register`
Creates a new user account.
```json
// Request Body
{
  "email": "analyst@company.com",
  "password": "SecurePassword123!",
  "fullName": "Jane Doe"
}

// Response: 201 Created
{
  "userId": "d290f1ee-6c54-4b01-90e6-d701748f0851",
  "email": "analyst@company.com",
  "fullName": "Jane Doe",
  "createdAt": "2026-09-14T10:00:00Z"
}
```

#### `POST /auth/login`
Authenticates user and returns JWT bearer token.
```json
// Request Body
{
  "email": "analyst@company.com",
  "password": "SecurePassword123!"
}

// Response: 200 OK
{
  "tokenType": "Bearer",
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expiresInSeconds": 86400
}
```

---

### 1.2 Document Management Endpoints

All document endpoints require `Authorization: Bearer <token>`.

#### `POST /documents/upload`
Uploads a document file for asynchronous ingestion.
- **Content-Type:** `multipart/form-data`
- **Form Fields:**
  - `file`: Binary file (PDF, DOCX, TXT)
  - `description` (optional): String

```json
// Response: 202 Accepted
{
  "documentId": "a143b821-2e6b-4560-9ff9-0129bcfe3452",
  "filename": "Q3_Financial_Report.pdf",
  "fileSize": 2415904,
  "status": "PENDING",
  "uploadedAt": "2026-09-14T10:05:00Z"
}
```

#### `GET /documents`
Lists documents uploaded by the authenticated user.
- **Query Params:** `page` (default 0), `size` (default 20), `status` (optional)

```json
// Response: 200 OK
{
  "content": [
    {
      "id": "a143b821-2e6b-4560-9ff9-0129bcfe3452",
      "filename": "Q3_Financial_Report.pdf",
      "fileSize": 2415904,
      "status": "INDEXED",
      "totalChunks": 42,
      "createdAt": "2026-09-14T10:05:00Z"
    }
  ],
  "totalElements": 1,
  "totalPages": 1
}
```

#### `GET /documents/{documentId}/status`
Checks the indexing progress of a document.
```json
// Response: 200 OK
{
  "documentId": "a143b821-2e6b-4560-9ff9-0129bcfe3452",
  "status": "INDEXED", // PENDING | PROCESSING | INDEXED | FAILED
  "totalChunks": 42,
  "errorMessage": null
}
```

#### `DELETE /documents/{documentId}`
Deletes a document and cascades deletion of its vector embeddings.
```json
// Response: 204 No Content
```

---

### 1.3 Chat & RAG Query Endpoints

#### `POST /chat/sessions`
Initializes a new chat session.
```json
// Request Body
{
  "title": "Q3 Revenue Analysis"
}

// Response: 201 Created
{
  "sessionId": "e7b0a852-51c3-4d43-85f2-9517e4bb0234",
  "title": "Q3 Revenue Analysis",
  "createdAt": "2026-09-14T10:10:00Z"
}
```

#### `POST /chat/sessions/{sessionId}/messages`
Sends a query in the session context, executes grounded RAG retrieval, and generates an answer with citations.
```json
// Request Body
{
  "query": "What were our top 3 operating expenses in Q3?",
  "documentFilterIds": ["a143b821-2e6b-4560-9ff9-0129bcfe3452"], // Optional filter
  "topK": 5
}

// Response: 200 OK
{
  "messageId": "9b12cf34-77ae-4f01-a1e4-bf45819e6231",
  "sender": "ASSISTANT",
  "answer": "According to the report, the top three operating expenses in Q3 were Research & Development ($14.2M), Sales & Marketing ($11.8M), and General Administrative ($6.5M) [Doc 1, p. 18].",
  "citations": [
    {
      "citationIndex": 1,
      "documentId": "a143b821-2e6b-4560-9ff9-0129bcfe3452",
      "documentTitle": "Q3_Financial_Report.pdf",
      "pageNumber": 18,
      "snippet": "Operating expenses summary: Research & Development reached $14.2M, followed by Sales & Marketing at $11.8M, and General Administrative costs at $6.5M...",
      "similarityScore": 0.892
    }
  ],
  "createdAt": "2026-09-14T10:10:04Z"
}
```

#### `GET /chat/sessions/{sessionId}/messages`
Retrieves conversational history for a session.
```json
// Response: 200 OK
[
  {
    "id": "c1...",
    "sender": "USER",
    "content": "What were our top 3 operating expenses in Q3?",
    "createdAt": "2026-09-14T10:10:01Z"
  },
  {
    "id": "9b...",
    "sender": "ASSISTANT",
    "content": "According to the report...",
    "citations": [...],
    "createdAt": "2026-09-14T10:10:04Z"
  }
]
```

---

## 2. Python AI Microservice APIs (Internal / Service-to-Service)

Base URL: `http://ai-service:8001/api/v1`

### 2.1 Ingestion Endpoint

#### `POST /ingest`
Triggers parsing, chunking, embedding, and vector insertion for a file.
```json
// Request Body
{
  "documentId": "a143b821-2e6b-4560-9ff9-0129bcfe3452",
  "filePath": "/shared/storage/uploads/a143b821.pdf",
  "filename": "Q3_Financial_Report.pdf",
  "chunkSize": 600,
  "chunkOverlap": 100
}

// Response: 200 OK
{
  "documentId": "a143b821-2e6b-4560-9ff9-0129bcfe3452",
  "status": "COMPLETED",
  "totalChunks": 42,
  "timeElapsedMs": 1420
}
```

### 2.2 RAG Query & Citation Endpoint

#### `POST /rag/generate`
Performs vector similarity search against `pgvector`, prepares grounded prompt, calls LLM, and formats citations.
```json
// Request Body
{
  "query": "What were our top 3 operating expenses in Q3?",
  "conversationHistory": [
    {"role": "user", "content": "Hello, I need help analyzing Q3 figures."},
    {"role": "assistant", "content": "Certainly! What would you like to know?"}
  ],
  "documentIds": ["a143b821-2e6b-4560-9ff9-0129bcfe3452"], // Optional
  "topK": 5,
  "temperature": 0.1
}

// Response: 200 OK
{
  "answer": "According to the report, the top three operating expenses in Q3 were Research & Development ($14.2M), Sales & Marketing ($11.8M), and General Administrative ($6.5M) [Doc 1, p. 18].",
  "citations": [
    {
      "citationIndex": 1,
      "documentId": "a143b821-2e6b-4560-9ff9-0129bcfe3452",
      "documentTitle": "Q3_Financial_Report.pdf",
      "pageNumber": 18,
      "chunkId": "f908...",
      "snippet": "Operating expenses summary: Research & Development reached $14.2M...",
      "score": 0.892
    }
  ],
  "tokenUsage": {
    "promptTokens": 540,
    "completionTokens": 62,
    "totalTokens": 602
  }
}
```

### 2.3 Health & Readiness
#### `GET /health`
```json
// Response: 200 OK
{
  "status": "UP",
  "pgvectorConnected": true,
  "embeddingModel": "text-embedding-3-small"
}
```
