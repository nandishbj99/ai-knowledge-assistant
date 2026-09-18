from app.services.chunker import ParentDocumentChunker

def test_parent_child_chunking():
    chunker = ParentDocumentChunker(
        parent_chunk_size=300,
        parent_overlap=50,
        child_chunk_size=80,
        child_overlap=15
    )

    sample_pages = [
        {
            "page_number": 1,
            "text": (
                "Section 1: Company Financial Overview.\n\n"
                "In Q3 2026, total revenue reached $45.2M, representing a 14% year-over-year increase. "
                "Operating expenses remained stable at $28.1M, yielding an operating margin of 37.8%.\n\n"
                "Section 2: Enterprise Cloud Expansion.\n\n"
                "Our enterprise customer base grew to 1,240 organizations. "
                "Net dollar retention reached 128%, driven by expansion in AI microservices and knowledge retrieval."
            )
        }
    ]

    doc_id = "doc-test-123"
    tenant_id = "tenant-test-456"
    user_id = "user-test-789"
    filename = "q3_report.pdf"

    parent_chunks, child_chunks = chunker.chunk_document(
        sample_pages, doc_id, tenant_id, user_id, filename
    )

    # Validate Parent Chunks
    assert len(parent_chunks) >= 1
    for p in parent_chunks:
        assert p["document_id"] == doc_id
        assert p["tenant_id"] == tenant_id
        assert p["user_id"] == user_id
        assert p["page_number"] == 1
        assert len(p["content"]) > 0

    # Validate Child Chunks
    assert len(child_chunks) >= len(parent_chunks)
    for c in child_chunks:
        assert c["document_id"] == doc_id
        assert c["tenant_id"] == tenant_id
        assert c["user_id"] == user_id
        assert c["parent_chunk_id"] in [p["id"] for p in parent_chunks]
        assert c["metadata"]["filename"] == filename
        assert len(c["chunk_content"]) > 0
