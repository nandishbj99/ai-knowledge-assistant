# Feature Specification: FEAT-001 - Document Ingestion Pipeline

> **Feature ID:** `FEAT-001`  
> **Feature Name:** Document Ingestion Pipeline  
> **Status:** `DESIGN_READY`  
> **Parent Spec:** [Master Project Spec](../../specs/main-spec.md)  
> **Design & ADRs:** [Design & ADRs](./design.md) | **Tasks:** [Tasks](./tasks.md) | **Testing:** [Testing](./testing.md)

---

## 1. Overview & Objective
Enables authenticated users to upload proprietary company documents (PDF, DOCX, TXT) via the Spring Boot gateway. An asynchronous, durable worker parses text, converts tables to Markdown, reconstructs charts via multimodal vision, and indexes content using **Parent-Document (Small-to-Big)** hierarchy with **Google `text-embedding-004` (768d)** in PostgreSQL (`pgvector`). Strict owner and tenant boundaries are enforced across all operations.

---

## 2. User Stories
- **US-01:** As an analyst, I want to upload documents securely so that only members of my tenant/account can query them.
- **US-02:** As a system user, I want the upload to return an immediate receipt with status `PENDING` so that large uploads do not block my client interface.
- **US-03:** As an operator, I want failed documents to automatically retry with exponential backoff and route to a Dead-Letter Queue (DLQ) if unrecoverable.
- **US-04:** As an admin, I want to delete a document and ensure all raw files, parent chunks, and vector embeddings are irreversibly cleaned up.

---

## 3. Scope & Requirements

### Functional Requirements (FR)
- **FR-01 (Upload Endpoint):** `POST /api/v1/documents/upload` accepting multipart file (max 50MB, max 100 pages), storing with `owner_id` and `tenant_id`, returning HTTP 202 Accepted.
- **FR-02 (Safety & MIME Validation):** Performs MIME magic-byte sniffing (rejects disguised executables), enforces a 50MB file size limit and a 100-page limit per document.
- **FR-03 (Parent-Document Chunking):** Chunks text into **Parent Chunks** (~1,000–1,500 tokens) for surrounding context, and **Child Chunks** (~150–200 tokens) for vector indexing.
- **FR-04 (Vector Embedding):** Embeds child chunks using **Google `text-embedding-004` (768 dimensions only)**.
- **FR-05 (pgvector Storage with Tenant Index):** Stores parent chunks in `parent_chunks` and child vectors in `document_chunks` with `vector(768)`. Both tables contain `owner_id` and `tenant_id`.
- **FR-06 (Status & Ownership Enforced):** `GET /api/v1/documents/{id}/status` returning indexing progress. Users can ONLY inspect documents they own.
- **FR-07 (Table Extraction & Markdown Formatting):** Detects tables via `pdfplumber`, converts to Markdown pipe tables, and re-injects headers across split chunks.
- **FR-08 (Multimodal Chart & Visual Processing):** Extracts chart bounding boxes, invokes `gemini-2.5-flash` vision, and stores reconstructed data tables with page citations.
- **FR-09 (Durable Ingestion Queue):** Publishes ingestion tasks to Redis with consumer group acknowledgment, idempotency checking (`idempotency_key = sha256(doc_id, file_bytes)`), max 3 retries, and a Dead-Letter Queue (`dlq:ingestion`).
- **FR-10 (Document Deletion & Lifecycle Cleanup):** `DELETE /api/v1/documents/{id}` validates ownership, cascades deletion across `documents`, `parent_chunks`, `document_chunks`, and removes the raw file from storage.

### Non-Functional Requirements (NFR) & Observed SLO
- **Ingestion SLO (Workload Dependent):**
  - **Baseline (Text & Tables, 20 pages):** Observed p95 < 25 seconds.
  - **Visual Multimodal (with charts/diagrams):** Observed p95 < 60 seconds (excludes baseline SLA due to external vision inference calls).
- **Processing Timeouts:** 30s per multimodal vision call; 5m overall timeout per document before marking `FAILED`.
- **Idempotency:** Reprocessing an identical document ID cleans up previous parent/child chunks before re-indexing.

---

## 4. API Contracts

### Upload Document
```http
POST /api/v1/documents/upload HTTP/1.1
Authorization: Bearer <JWT_TOKEN>
Content-Type: multipart/form-data; boundary=---Boundary

-----Boundary
Content-Disposition: form-data; name="file"; filename="Annual_Report.pdf"
Content-Type: application/pdf

<binary>
-----Boundary--
```

**Response (202 Accepted):**
```json
{
  "documentId": "a143b821-2e6b-4560-9ff9-0129bcfe3452",
  "filename": "Annual_Report.pdf",
  "fileSize": 3145728,
  "status": "PENDING",
  "ownerId": "d290f1ee-6c54-4b01-90e6-d701748f0851",
  "tenantId": "d290f1ee-6c54-4b01-90e6-d701748f0851",
  "uploadedAt": "2026-09-17T10:00:00Z"
}
```

### Get Document Status
```http
GET /api/v1/documents/a143b821-2e6b-4560-9ff9-0129bcfe3452/status HTTP/1.1
Authorization: Bearer <JWT_TOKEN>
```

**Response (200 OK):**
```json
{
  "documentId": "a143b821-2e6b-4560-9ff9-0129bcfe3452",
  "status": "INDEXED",
  "totalParentChunks": 14,
  "totalChildChunks": 82,
  "errorMessage": null
}
```

### Delete Document
```http
DELETE /api/v1/documents/a143b821-2e6b-4560-9ff9-0129bcfe3452 HTTP/1.1
Authorization: Bearer <JWT_TOKEN>
```

**Response:** `204 No Content`
