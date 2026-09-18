import re
import uuid
from typing import List, Dict, Any, Tuple

class ParentDocumentChunker:
    """
    Implements Parent-Child (Small-to-Big) Chunking:
    - Parent Chunks: Large contextual sections (~1000-1500 tokens) for LLM synthesis.
    - Child Chunks: Granular semantic windows (~150-200 tokens) for sharp pgvector search.
    - Strictly scoped with tenant_id and user_id to prevent cross-tenant vector leakage.
    """

    def __init__(
        self,
        parent_chunk_size: int = 1200,
        parent_overlap: int = 100,
        child_chunk_size: int = 180,
        child_overlap: int = 30
    ):
        self.parent_chunk_size = parent_chunk_size
        self.parent_overlap = parent_overlap
        self.child_chunk_size = child_chunk_size
        self.child_overlap = child_overlap

    def chunk_document(
        self,
        pages: List[Dict[str, Any]],
        document_id: str,
        tenant_id: str,
        user_id: str,
        filename: str
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Takes parsed pages and produces:
        (parent_chunks, child_chunks)
        """
        parent_chunks = []
        child_chunks = []
        global_child_idx = 0

        for page in pages:
            page_num = page.get("page_number", 1)
            raw_text = page.get("text", "").strip()
            if not raw_text:
                continue

            # 1. Create Parent Chunks (~1200 tokens) for this page
            page_parent_texts = self._split_text(
                raw_text,
                max_chars=self.parent_chunk_size * 4,
                overlap_chars=self.parent_overlap * 4
            )

            for p_idx, parent_content in enumerate(page_parent_texts):
                parent_id = str(uuid.uuid4())
                parent_chunk = {
                    "id": parent_id,
                    "document_id": document_id,
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                    "page_number": page_num,
                    "section_title": f"Page {page_num} - Section {p_idx + 1}",
                    "content": parent_content
                }
                parent_chunks.append(parent_chunk)

                # 2. Subdivide parent into granular Child Chunks (~180 tokens)
                child_texts = self._split_text(
                    parent_content,
                    max_chars=self.child_chunk_size * 4,
                    overlap_chars=self.child_overlap * 4
                )

                for c_text in child_texts:
                    child_chunks.append({
                        "id": str(uuid.uuid4()),
                        "parent_chunk_id": parent_id,
                        "document_id": document_id,
                        "tenant_id": tenant_id,
                        "user_id": user_id,
                        "page_number": page_num,
                        "chunk_index": global_child_idx,
                        "chunk_content": c_text,
                        "metadata": {
                            "filename": filename,
                            "page_number": page_num,
                            "parent_id": parent_id,
                            "char_count": len(c_text)
                        }
                    })
                    global_child_idx += 1

        return parent_chunks, child_chunks

    def _split_text(self, text: str, max_chars: int, overlap_chars: int) -> List[str]:
        # Priority 1: Double line breaks / Markdown sections
        paragraphs = text.split("\n\n")
        chunks = []
        current = ""

        for p in paragraphs:
            p = p.strip()
            if not p:
                continue

            if len(current) + len(p) + 2 <= max_chars:
                current = f"{current}\n\n{p}".strip()
            else:
                if current:
                    chunks.append(current)
                    current = current[-overlap_chars:] + "\n\n" + p if len(current) > overlap_chars else p
                else:
                    sentence_chunks = self._split_sentences(p, max_chars, overlap_chars)
                    chunks.extend(sentence_chunks)
                    current = ""

        if current.strip():
            chunks.append(current.strip())

        return chunks

    def _split_sentences(self, text: str, max_chars: int, overlap_chars: int) -> List[str]:
        sentences = re.split(r'(?<=[.?!])\s+', text)
        result = []
        curr = ""
        for s in sentences:
            if len(curr) + len(s) + 1 <= max_chars:
                curr = f"{curr} {s}".strip()
            else:
                if curr:
                    result.append(curr)
                    curr = s
                else:
                    for i in range(0, len(s), max_chars - overlap_chars):
                        result.append(s[i:i + max_chars])
                    curr = ""
        if curr.strip():
            result.append(curr.strip())
        return result
