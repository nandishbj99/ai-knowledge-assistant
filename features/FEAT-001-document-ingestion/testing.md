# Feature Testing & Verification: FEAT-001 - Document Ingestion Pipeline

> **Feature ID:** `FEAT-001`  
> **Status:** `PENDING_EXECUTION`  
> **Spec Reference:** [Feature Spec](./spec.md) | [Design & ADRs](./design.md)

---

## 1. Verification Strategy
Verification covers four critical dimensions:
1. **Security & Input Validation:** Magic-byte sniffing, size limits, page limits, tenant isolation.
2. **Resilience & Queue Processing:** Redis Streams consumer group processing, idempotency, retry backoff, and DLQ routing.
3. **Parent-Document Chunking & Vector Dimension:** Validation that parent chunks (~1200t) and child chunks (~180t) are correctly formed, and child embeddings are strictly **768 dimensions** (Google `text-embedding-004`).
4. **Lifecycle & Cleanup:** Verification that deleting a document cascades across parent and child chunks and removes the raw file.

---

## 2. Test Case Matrix

| Test ID | Test Scenario | Target Component | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| `TC-01` | Upload valid PDF (5 pages) | `DocumentController` ➔ Redis ➔ Worker | Returns 202 Accepted, transitions to `INDEXED`, produces parent and child chunks | `PENDING` |
| `TC-02` | MIME spoofing (Rename `.exe` to `.pdf`) | Ingestion Validator (Magic Bytes) | Sniffing detects invalid magic bytes, rejects with HTTP 400 Bad Request | `PENDING` |
| `TC-03` | File exceeds limits (>50MB or >100 pages) | `DocumentController` | Returns HTTP 413 Payload Too Large / 400 with descriptive error | `PENDING` |
| `TC-04` | Page Number Accuracy Verification | `DocumentParser` | Parent and child chunk metadata matches original PDF page numbers exactly | `PENDING` |
| `TC-05` | Vector Dimension Verification (Gemini 768d) | `document_chunks` table | Vector column contains strictly **768 floating point values** | `PENDING` |
| `TC-06` | Multi-Tenant Authorization Enforcement | Status & Retrieval Endpoints | User B cannot view status or query chunks belonging to User A (returns 404 / empty) | `PENDING` |
| `TC-07` | Worker Failure & DLQ Routing | Worker Retry Handler | After 3 failed attempts, task routes to `dlq:ingestion`, document status marks `FAILED` | `PENDING` |
| `TC-08` | Idempotent Reprocessing | Ingestion Worker | Reprocessing same doc ID purges old parent/child chunks before inserting new ones | `PENDING` |
| `TC-09` | Lifecycle Deletion Cleanup | `DELETE /api/v1/documents/{id}` | DB cascades delete on parent/child chunks; physical file is purged from storage | `PENDING` |

---

## 3. Manual Verification Steps (cURL)

```bash
# 1. Upload sample document
curl -i -X POST http://localhost:8080/api/v1/documents/upload \
  -H "Authorization: Bearer <USER_A_JWT>" \
  -F "file=@./test-sample.pdf"

# Expected: HTTP 202 Accepted {"documentId": "...", "status": "PENDING", "ownerId": "..."}

# 2. Poll Status as Owner (User A)
curl -i http://localhost:8080/api/v1/documents/<DOCUMENT_ID>/status \
  -H "Authorization: Bearer <USER_A_JWT>"
# Expected: HTTP 200 OK {"status": "INDEXED", "totalParentChunks": 4, "totalChildChunks": 24}

# 3. Unauthorized Cross-Tenant Poll (User B)
curl -i http://localhost:8080/api/v1/documents/<DOCUMENT_ID>/status \
  -H "Authorization: Bearer <USER_B_JWT>"
# Expected: HTTP 404 Not Found (or 403 Forbidden)

# 4. Check Vector Dimensions in Postgres
docker exec -it assistant_postgres psql -U postgres -d knowledge_assistant -c \
  "SELECT id, vector_dims(embedding) FROM document_chunks LIMIT 1;"
# Expected: 768

# 5. Delete Document and Assert Cleanup
curl -i -X DELETE http://localhost:8080/api/v1/documents/<DOCUMENT_ID> \
  -H "Authorization: Bearer <USER_A_JWT>"
# Expected: HTTP 204 No Content
```

---

## 4. Acceptance Criteria Checklist
- [ ] Multi-page PDF uploads succeed asynchronously through Redis Streams.
- [ ] Parent and child chunks are created and linked by `parent_chunk_id`.
- [ ] Child embeddings strictly match 768 dimensions.
- [ ] Cross-tenant access attempts are completely blocked.
- [ ] File deletion cascades cleanly across database and disk.
