import asyncio
import json
import logging
import time
from typing import Dict, Any
import redis.asyncio as aioredis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.services.parser import DocumentParser
from app.services.chunker import ParentDocumentChunker
from app.services.embedder import EmbeddingService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ingestion-worker")

STREAM_KEY = "ingestion:tasks"
GROUP_NAME = "ingestion-workers"
CONSUMER_NAME = "worker-1"
DLQ_KEY = "dlq:ingestion"
MAX_RETRIES = 3

async def process_task(task_data: Dict[str, str], db: AsyncSession):
    doc_id = task_data.get("document_id")
    tenant_id = task_data.get("tenant_id")
    user_id = task_data.get("user_id")
    file_path = task_data.get("file_path")
    filename = task_data.get("filename", "unknown")

    logger.info(f"Starting ingestion for document_id={doc_id}, file={filename}")

    # 1. Update status to PROCESSING
    update_proc_sql = text("""
        UPDATE documents
        SET status = 'PROCESSING', updated_at = CURRENT_TIMESTAMP
        WHERE id = :doc_id
    """)
    await db.execute(update_proc_sql, {"doc_id": doc_id})
    await db.commit()

    # 2. Parse pages (with Markdown tables and vision chart extraction)
    pages = DocumentParser.parse(file_path)
    if not pages:
        raise ValueError("No readable text found in document")

    # 3. Chunk with Parent-Document (Small-to-Big) Hierarchy
    chunker = ParentDocumentChunker()
    parent_chunks, child_chunks = chunker.chunk_document(pages, doc_id, tenant_id, user_id, filename)

    if not child_chunks:
        raise ValueError("Document yielded 0 child chunks")

    # 4. Insert Parent Chunks
    insert_parent_sql = text("""
        INSERT INTO parent_chunks (id, document_id, user_id, tenant_id, page_number, section_title, content)
        VALUES (:id, :doc_id, :user_id, :tenant_id, :page_num, :section_title, :content)
    """)
    for parent in parent_chunks:
        await db.execute(
            insert_parent_sql,
            {
                "id": parent["id"],
                "doc_id": doc_id,
                "user_id": user_id,
                "tenant_id": tenant_id,
                "page_num": parent["page_number"],
                "section_title": parent["section_title"],
                "content": parent["content"]
            }
        )

    # 5. Generate 768d embeddings for child chunks
    embedder = EmbeddingService()
    child_texts = [c["chunk_content"] for c in child_chunks]
    embeddings = await embedder.get_embeddings(child_texts, task_type="RETRIEVAL_DOCUMENT")

    # 6. Insert Child Chunks with vectors
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
                "doc_id": doc_id,
                "user_id": user_id,
                "tenant_id": tenant_id,
                "chunk_idx": chunk["chunk_index"],
                "page_num": chunk["page_number"],
                "content": chunk["chunk_content"],
                "metadata": json.dumps(chunk["metadata"]),
                "vec": vec_str
            }
        )

    # 7. Update document status to INDEXED
    update_indexed_sql = text("""
        UPDATE documents
        SET status = 'INDEXED', 
            total_parent_chunks = :parent_count,
            total_child_chunks = :child_count,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = :doc_id
    """)
    await db.execute(
        update_indexed_sql,
        {
            "doc_id": doc_id,
            "parent_count": len(parent_chunks),
            "child_count": len(child_chunks)
        }
    )
    await db.commit()
    logger.info(f"Successfully indexed document_id={doc_id}: {len(parent_chunks)} parents, {len(child_chunks)} children")

async def run_worker():
    while True:
        try:
            logger.info(f"Connecting to Redis at {settings.REDIS_URL}")
            r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

            # Create consumer group if not exists
            try:
                await r.xgroup_create(STREAM_KEY, GROUP_NAME, id="0", mkstream=True)
                logger.info(f"Created consumer group {GROUP_NAME} on stream {STREAM_KEY}")
            except Exception as e:
                if "BUSYGROUP" not in str(e):
                    logger.debug(f"Consumer group info: {e}")

            logger.info("Worker started, listening for ingestion tasks...")

            while True:
                entries = await r.xreadgroup(
                    GROUP_NAME,
                    CONSUMER_NAME,
                    {STREAM_KEY: ">"},
                    count=1,
                    block=2000
                )

                if not entries:
                    await asyncio.sleep(0.5)
                    continue

                for stream, messages in entries:
                    for msg_id, data in messages:
                        doc_id = data.get("document_id")
                        retry_key = f"ingest:retries:{doc_id}"
                        current_retries = int(await r.get(retry_key) or 0)

                        async with AsyncSessionLocal() as db:
                            try:
                                await process_task(data, db)
                                await r.xack(STREAM_KEY, GROUP_NAME, msg_id)
                                await r.delete(retry_key)
                            except Exception as ex:
                                logger.error(f"Error processing doc_id={doc_id}: {ex}", exc_info=True)
                                await db.rollback()
                                current_retries += 1
                                await r.set(retry_key, current_retries, ex=86400)

                                if current_retries >= MAX_RETRIES:
                                    logger.error(f"Doc {doc_id} exceeded max retries ({MAX_RETRIES}). Moving to DLQ.")
                                    data["error"] = str(ex)
                                    await r.xadd(DLQ_KEY, data)
                                    await r.xack(STREAM_KEY, GROUP_NAME, msg_id)

                                    fail_sql = text("""
                                        UPDATE documents
                                        SET status = 'FAILED', error_message = :err, updated_at = CURRENT_TIMESTAMP
                                        WHERE id = :doc_id
                                    """)
                                    await db.execute(fail_sql, {"doc_id": doc_id, "err": str(ex)})
                                    await db.commit()
                                else:
                                    logger.info(f"Retrying doc {doc_id} (attempt {current_retries}/{MAX_RETRIES})...")
                                    await asyncio.sleep(2 ** current_retries)

        except asyncio.CancelledError:
            logger.info("Worker loop cancelled.")
            break
        except Exception as e:
            logger.warning(f"Redis connection / worker loop unavailable: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(run_worker())
