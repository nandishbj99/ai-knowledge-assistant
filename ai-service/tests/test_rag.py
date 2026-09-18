from app.services.rag import RAGService

def test_build_prompt_opaque_keys():
    context_chunks = [
        {
            "chunk_content": "Total revenue in Q3 reached $45.2M.",
            "document_title": "q3_report.pdf",
            "page_number": 1
        },
        {
            "chunk_content": "Operating expenses were $28.1M.",
            "document_title": "q3_report.pdf",
            "page_number": 2
        }
    ]

    system_prompt, user_content = RAGService.build_prompt(
        query="What was the revenue and expenses?",
        context_chunks=context_chunks,
        conversation_history=[]
    )

    # Verify opaque keys are injected into context
    assert "--- [SOURCE-1] ---" in user_content
    assert "--- [SOURCE-2] ---" in user_content
    assert "Total revenue in Q3 reached $45.2M." in user_content
    assert "CRITICAL RULES" in system_prompt
    assert "[SOURCE-X]" in system_prompt

def test_extract_citations_valid_and_hallucinated():
    context_chunks = [
        {
            "document_id": "doc-1",
            "document_title": "q3_report.pdf",
            "page_number": 1,
            "chunk_id": "chunk-101",
            "matched_snippet": "Total revenue in Q3 reached $45.2M.",
            "similarity_score": 0.89
        },
        {
            "document_id": "doc-1",
            "document_title": "q3_report.pdf",
            "page_number": 2,
            "chunk_id": "chunk-102",
            "matched_snippet": "Operating expenses were $28.1M.",
            "similarity_score": 0.84
        }
    ]

    # Model cites valid [SOURCE-1] and [SOURCE-2], but also hallucinated [SOURCE-99]
    answer = (
        "Q3 revenue was $45.2M [SOURCE-1] with operating expenses of $28.1M [SOURCE-2]. "
        "Also customer churn was 2% [SOURCE-99]."
    )

    citations = RAGService._extract_citations(answer, context_chunks)

    # Must resolve SOURCE-1 and SOURCE-2, and ignore hallucinated SOURCE-99
    assert len(citations) == 2
    assert citations[0]["sourceKey"] == "[SOURCE-1]"
    assert citations[0]["filename"] == "q3_report.pdf"
    assert citations[0]["pageNumber"] == 1

    assert citations[1]["sourceKey"] == "[SOURCE-2]"
    assert citations[1]["pageNumber"] == 2

    # Verify SOURCE-99 is rejected
    source_keys = [c["sourceKey"] for c in citations]
    assert "[SOURCE-99]" not in source_keys
