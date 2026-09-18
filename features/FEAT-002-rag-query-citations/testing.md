# Feature Testing & Verification: FEAT-002 - Grounded RAG Query & Citations

> **Feature ID:** `FEAT-002`  
> **Status:** `PENDING_EXECUTION`  
> **Spec Reference:** [Feature Spec](./spec.md) | [Design & ADRs](./design.md)

---

## 1. Verification Strategy
1. **Retrieval Precision Test:** Verify that queries correctly fetch the highest-scoring cosine similarity chunks.
2. **Grounding Verification:** Test queries about information completely absent from the indexed documents; assert the model answers with the insufficiency disclaimer.
3. **Citation Formatting:** Assert that response JSON contains non-empty `citations` array with accurate `documentTitle` and `pageNumber`.

---

## 2. Test Case Matrix

| Test ID | Test Scenario | Target Component | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| `TC-01` | Query with direct factual match in indexed document | `RAGService` | Returns answer with inline citation `[Doc: ..., p. ...]` and non-empty `citations` array | `PENDING` |
| `TC-02` | Out-of-domain query (e.g. "Who won the 1994 World Cup?") | `RAGService` | Returns refusal message: "I am sorry, but the uploaded documents do not contain..." | `PENDING` |
| `TC-03` | Multi-turn conversational query (resolving pronoun "they") | `RAGService` | Correctly incorporates conversation history to resolve context | `PENDING` |
| `TC-04` | Specific Document ID Filter | `VectorRetriever` | Only chunks belonging to the specified `documentIds` are returned | `PENDING` |

---

## 3. Manual Verification Steps (cURL)

```bash
# Ask question in session
curl -i -X POST http://localhost:8080/api/v1/chat/sessions/<SESSION_ID>/messages \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are our top 3 operating expenses?",
    "topK": 5
  }'

# Assert response structure contains "answer" and "citations" with page numbers
```
