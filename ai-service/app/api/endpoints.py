import json
import time
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.session import get_db
from app.services.parser import DocumentParser
from app.services.chunker import ParentDocumentChunker
from app.services.embedder import EmbeddingService
from app.services.retriever import VectorRetriever
from app.services.rag import RAGService

router = APIRouter()

# ----------------- DTOs -----------------
class IngestionRequest(BaseModel):
    documentId: str
    tenantId: str
    userId: str
    filePath: str
    filename: str

class IngestionResponse(BaseModel):
    documentId: str
    status: str
    totalParentChunks: int
    totalChildChunks: int
    timeElapsedMs: int

class ChatHistoryItem(BaseModel):
    sender: str
    content: str

class QueryPayload(BaseModel):
    query: str
    session_id: Optional[str] = None
    user_id: str
    tenant_id: str
    history: Optional[List[ChatHistoryItem]] = []
    top_k: Optional[int] = 5
    document_ids: Optional[List[str]] = None

class QueryResponse(BaseModel):
    answer: str
    citations: List[Dict[str, Any]]

# ----------------- Endpoints -----------------

@router.post("/query", response_model=QueryResponse)
async def handle_query(req: QueryPayload, db: AsyncSession = Depends(get_db)):
    try:
        # 1. Embed query (768 dimensions)
        embedder = EmbeddingService()
        query_vector = await embedder.get_query_embedding(req.query)

        # 2. Vector search strictly isolated to tenant_id and user_id
        matched_chunks = await VectorRetriever.search(
            session=db,
            query_vector=query_vector,
            tenant_id=req.tenant_id,
            user_id=req.user_id,
            top_k=req.top_k or 5,
            document_ids=req.document_ids
        )

        # 3. Grounded generation with server-assigned opaque citation keys [SOURCE-X]
        history = [msg.model_dump() for msg in req.history] if req.history else []
        result = await RAGService.generate_response(
            query=req.query,
            context_chunks=matched_chunks,
            conversation_history=history
        )

        return QueryResponse(
            answer=result["answer"],
            citations=result["citations"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

@router.post("/ingest", response_model=IngestionResponse)
async def ingest_document_direct(req: IngestionRequest, db: AsyncSession = Depends(get_db)):
    start_time = time.time()
    try:
        # 1. Parse pages
        pages = DocumentParser.parse(req.filePath)
        if not pages:
            raise HTTPException(status_code=400, detail="No readable text found in document")

        # 2. Chunk text with Parent-Document (Small-to-Big) Hierarchy
        chunker = ParentDocumentChunker()
        parent_chunks, child_chunks = chunker.chunk_document(pages, req.documentId, req.tenantId, req.userId, req.filename)

        if not child_chunks:
            raise HTTPException(status_code=400, detail="Document produced 0 chunks")

        # 3. Insert Parent Chunks into PostgreSQL
        insert_parent_sql = text("""
            INSERT INTO parent_chunks (id, document_id, user_id, tenant_id, page_number, section_title, content)
            VALUES (:id, :doc_id, :user_id, :tenant_id, :page_num, :section_title, :content)
        """)
        for parent in parent_chunks:
            await db.execute(
                insert_parent_sql,
                {
                    "id": parent["id"],
                    "doc_id": parent["document_id"],
                    "user_id": parent["user_id"],
                    "tenant_id": parent["tenant_id"],
                    "page_num": parent["page_number"],
                    "section_title": parent["section_title"],
                    "content": parent["content"]
                }
            )

        # 4. Generate 768d embeddings for granular Child Chunks
        embedder = EmbeddingService()
        child_texts = [c["chunk_content"] for c in child_chunks]
        embeddings = await embedder.get_embeddings(child_texts, task_type="RETRIEVAL_DOCUMENT")

        # 5. Insert Child Chunks with vectors into PostgreSQL pgvector
        insert_child_sql = text("""
            INSERT INTO document_chunks 
            (id, parent_chunk_id, document_id, user_id, tenant_id, chunk_index, page_number, chunk_content, metadata, embedding)
            VALUES 
            (:id, :parent_id, :doc_id, :user_id, :tenant_id, :chunk_idx, :page_num, :content, :metadata::jsonb, :vec::vector)
        """)

        for chunk, vec in zip(child_chunks, embeddings):
            vec_str = "[" + ",".join(map(str, vec)) + "]"
            await db.execute(
                insert_child_sql,
                {
                    "id": chunk["id"],
                    "parent_id": chunk["parent_chunk_id"],
                    "doc_id": req.documentId,
                    "user_id": req.userId,
                    "tenant_id": req.tenantId,
                    "chunk_idx": chunk["chunk_index"],
                    "page_num": chunk["page_number"],
                    "content": chunk["chunk_content"],
                    "metadata": json.dumps(chunk["metadata"]),
                    "vec": vec_str
                }
            )

        # Update document status to INDEXED
        update_doc_sql = text("""
            UPDATE documents 
            SET status = 'INDEXED', 
                total_parent_chunks = :parent_count,
                total_child_chunks = :child_count,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :doc_id
        """)
        await db.execute(
            update_doc_sql,
            {
                "doc_id": req.documentId,
                "parent_count": len(parent_chunks),
                "child_count": len(child_chunks)
            }
        )
        await db.commit()

        elapsed = int((time.time() - start_time) * 1000)
        return IngestionResponse(
            documentId=req.documentId,
            status="INDEXED",
            totalParentChunks=len(parent_chunks),
            totalChildChunks=len(child_chunks),
            timeElapsedMs=elapsed
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@router.get("/health")
async def health_check():
    return {"status": "UP", "service": "ai-service", "models": {"embedding": "text-embedding-004 (768d)", "generation": "gemini-2.5-flash"}}
