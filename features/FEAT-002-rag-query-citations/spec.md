# Feature Specification: FEAT-002 - Grounded RAG Query & Citations

> **Feature ID:** `FEAT-002`  
> **Status:** `DESIGN_READY`  
> **Parent Spec:** [Master Project Spec](../../specs/main-spec.md)  
> **Design & ADRs:** [Design & ADRs](./design.md) | **Tasks:** [Tasks](./tasks.md) | **Testing:** [Testing](./testing.md)

---

## 1. Overview & Objective
Provides an end-to-end question answering pipeline over uploaded documents. For any natural language question, the system retrieves the top relevant context chunks via pgvector cosine search, invokes the LLM with strict grounding instructions, and formats verifiable citations citing document titles and page numbers.

---

## 2. User Stories
- **US-01:** As a user, I want to ask questions in plain English and receive answers substantiated by excerpts from my company files.
- **US-02:** As an auditor, I want each claim in an answer to have an explicit citation tag (e.g. `[Doc: filename.pdf, p. 14]`) linking to the exact source page.
- **US-03:** As a user, if the documents do not contain the answer, I want the AI to state that information is missing rather than guessing or hallucinating.

---

## 3. Scope & Requirements

### Functional Requirements (FR)
- **FR-01 (Chat Message Endpoint):** `POST /api/v1/chat/sessions/{id}/messages` accepting user query, optional document filter IDs, and topK parameter.
- **FR-02 (Vector Cosine Retrieval):** Searches `document_chunks` using `ORDER BY embedding <=> query_vector LIMIT 5`.
- **FR-03 (Strict Grounding):** LLM system prompt forbids answering from general pre-training knowledge if absent from context.
- **FR-04 (Citation Extraction):** Extracts citations and returns structured JSON containing citation index, document title, page number, chunk ID, and source snippet.
- **FR-05 (Context Windowing):** Includes up to 6 prior conversational turns for contextual disambiguation.

---

## 4. API Contract

### Request Payload
```json
{
  "query": "What are the Q3 operating expenses?",
  "documentFilterIds": ["a143b821-2e6b-4560-9ff9-0129bcfe3452"],
  "topK": 5
}
```

### Response Payload
```json
{
  "messageId": "9b12cf34-77ae-4f01-a1e4-bf45819e6231",
  "sender": "ASSISTANT",
  "answer": "Operating expenses in Q3 were $32.5M, driven primarily by R&D investments [Doc: Q3_Report.pdf, p. 18].",
  "citations": [
    {
      "citationIndex": 1,
      "documentId": "a143b821-2e6b-4560-9ff9-0129bcfe3452",
      "documentTitle": "Q3_Report.pdf",
      "pageNumber": 18,
      "snippet": "Operating expenses breakdown: R&D expenses reached $14.2M...",
      "similarityScore": 0.895
    }
  ]
}
```
