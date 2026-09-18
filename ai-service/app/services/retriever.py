from typing import List, Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

class VectorRetriever:
    """
    Executes Parent-Document (Small-to-Big) searches:
    Searches small child chunk embeddings in pgvector, then expands and deduplicates
    to full surrounding parent context sections.
    Enforces strict tenant_id and user_id isolation on every vector search.
    """

    @staticmethod
    async def search(
        session: AsyncSession,
        query_vector: List[float],
        tenant_id: str,
        user_id: str,
        top_k: int = 5,
        threshold: float = 0.65,
        document_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        vector_str = "[" + ",".join(map(str, query_vector)) + "]"

        # Subquery finds distinct best-matching parent chunks with HNSW cosine distance
        if document_ids:
            query = text("""
                SELECT * FROM (
                    SELECT DISTINCT ON (p.id)
                        p.id AS parent_id,
                        c.id AS matched_chunk_id,
                        p.document_id,
                        d.filename AS document_title,
                        p.page_number,
                        p.content AS chunk_content,
                        c.chunk_content AS matched_snippet,
                        c.metadata,
                        1 - (c.embedding <=> :vector::vector(768)) AS similarity_score
                    FROM document_chunks c
                    JOIN parent_chunks p ON c.parent_chunk_id = p.id
                    JOIN documents d ON p.document_id = d.id
                    WHERE c.tenant_id = :tenant_id 
                      AND c.user_id = :user_id
                      AND c.document_id = ANY(:doc_ids)
                    ORDER BY p.id, (c.embedding <=> :vector::vector(768)) ASC
                ) sub
                WHERE sub.similarity_score >= :threshold
                ORDER BY sub.similarity_score DESC
                LIMIT :limit
            """)
            result = await session.execute(
                query,
                {
                    "vector": vector_str,
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                    "doc_ids": document_ids,
                    "threshold": threshold,
                    "limit": top_k
                }
            )
        else:
            query = text("""
                SELECT * FROM (
                    SELECT DISTINCT ON (p.id)
                        p.id AS parent_id,
                        c.id AS matched_chunk_id,
                        p.document_id,
                        d.filename AS document_title,
                        p.page_number,
                        p.content AS chunk_content,
                        c.chunk_content AS matched_snippet,
                        c.metadata,
                        1 - (c.embedding <=> :vector::vector(768)) AS similarity_score
                    FROM document_chunks c
                    JOIN parent_chunks p ON c.parent_chunk_id = p.id
                    JOIN documents d ON p.document_id = d.id
                    WHERE c.tenant_id = :tenant_id 
                      AND c.user_id = :user_id
                    ORDER BY p.id, (c.embedding <=> :vector::vector(768)) ASC
                ) sub
                WHERE sub.similarity_score >= :threshold
                ORDER BY sub.similarity_score DESC
                LIMIT :limit
            """)
            result = await session.execute(
                query,
                {
                    "vector": vector_str,
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                    "threshold": threshold,
                    "limit": top_k
                }
            )

        rows = result.mappings().all()
        return [
            {
                "chunk_id": str(r["matched_chunk_id"]),
                "parent_id": str(r["parent_id"]),
                "document_id": str(r["document_id"]),
                "document_title": r["document_title"],
                "page_number": r["page_number"],
                "chunk_content": r["chunk_content"],      # Full parent section for LLM
                "matched_snippet": r["matched_snippet"],  # Specific child snippet
                "metadata": r["metadata"],
                "similarity_score": float(r["similarity_score"])
            }
            for r in rows
        ]
