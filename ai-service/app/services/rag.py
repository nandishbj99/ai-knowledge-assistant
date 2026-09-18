import re
from typing import List, Dict, Any, Tuple
from app.core.config import settings

class RAGService:
    """
    Orchestrates prompt assembly with server-assigned opaque citation keys [SOURCE-X],
    grounded LLM generation via Gemini 2.5 Flash, and authoritative metadata resolution.
    """

    @staticmethod
    def build_prompt(
        query: str,
        context_chunks: List[Dict[str, Any]],
        conversation_history: List[Dict[str, str]]
    ) -> Tuple[str, str]:
        system_instruction = (
            "You are an expert Enterprise AI Knowledge Assistant.\n"
            "Answer the user's question using ONLY the provided context sources below.\n\n"
            "CRITICAL RULES:\n"
            "1. Grounding: If the question cannot be answered strictly using the provided context, respond with:\n"
            "   'I am sorry, but the uploaded documents do not contain sufficient information to answer this question.'\n"
            "   Do not extrapolate, assume, or bring in outside knowledge.\n"
            "2. Citations: Every statement of fact MUST include an inline citation formatted exactly as [SOURCE-X], "
            "where X corresponds to the source number from which the information was derived.\n"
            "   Example: 'Operating profit grew 12.4% year-over-year [SOURCE-1].'\n"
            "   Never invent new source numbers or modify the citation format.\n"
            "3. Objectivity: Maintain an objective, concise, and professional tone."
        )

        context_str = ""
        for idx, chunk in enumerate(context_chunks, start=1):
            content = chunk.get("chunk_content", "")
            context_str += f"\n--- [SOURCE-{idx}] ---\n{content}\n"

        history_str = ""
        if conversation_history:
            for msg in conversation_history[-6:]:
                role = msg.get("sender", msg.get("role", "user")).capitalize()
                content = msg.get("content", "")
                history_str += f"{role}: {content}\n"

        user_content = (
            f"PROVIDED SOURCES:\n{context_str or 'No relevant sources found.'}\n\n"
            f"CONVERSATION HISTORY:\n{history_str or 'None'}\n\n"
            f"USER QUESTION:\n{query}"
        )

        return system_instruction, user_content

    @staticmethod
    async def generate_response(
        query: str,
        context_chunks: List[Dict[str, Any]],
        conversation_history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        system_prompt, user_content = RAGService.build_prompt(
            query, context_chunks, conversation_history
        )

        if settings.GEMINI_API_KEY:
            answer = await RAGService._call_gemini(system_prompt, user_content)
        elif settings.OPENAI_API_KEY:
            answer = await RAGService._call_openai(system_prompt, user_content)
        else:
            # Deterministic mock grounded answer for local dev / testing
            if not context_chunks:
                answer = "I am sorry, but the uploaded documents do not contain sufficient information to answer this question."
            else:
                top = context_chunks[0]
                answer = (
                    f"Based on the documents, here is the relevant excerpt: \"{top['chunk_content'][:200]}...\" [SOURCE-1]."
                )

        citations = RAGService._extract_citations(answer, context_chunks)
        return {
            "answer": answer,
            "citations": citations
        }

    @staticmethod
    async def _call_gemini(system_prompt: str, user_content: str) -> str:
        from google import genai
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=settings.LLM_MODEL or "gemini-2.5-flash",
            contents=f"{system_prompt}\n\n{user_content}"
        )
        return response.text or ""

    @staticmethod
    async def _call_openai(system_prompt: str, user_content: str) -> str:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL or "gpt-4o-mini",
            temperature=0.1,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
        )
        return response.choices[0].message.content or ""

    @staticmethod
    def _extract_citations(answer: str, context_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        ADR-04: Resolves [SOURCE-X] opaque citation keys against authoritative server metadata.
        Rejects hallucinated source numbers.
        """
        pattern = r'\[SOURCE-(\d+)\]'
        matches = re.findall(pattern, answer)

        citations = []
        seen_indices = set()

        for match_str in matches:
            idx = int(match_str)
            if idx in seen_indices:
                continue

            # Validate index exists in retrieved set (1-based)
            if 1 <= idx <= len(context_chunks):
                seen_indices.add(idx)
                source_chunk = context_chunks[idx - 1]
                snippet_text = source_chunk.get("matched_snippet") or source_chunk.get("chunk_content", "")
                if len(snippet_text) > 300:
                    snippet_text = snippet_text[:300] + "..."

                citations.append({
                    "sourceKey": f"[SOURCE-{idx}]",
                    "citationIndex": len(citations) + 1,
                    "documentId": source_chunk.get("document_id"),
                    "filename": source_chunk.get("document_title"),
                    "pageNumber": source_chunk.get("page_number", 1),
                    "chunkId": source_chunk.get("chunk_id"),
                    "snippet": snippet_text,
                    "similarityScore": source_chunk.get("similarity_score", 1.0)
                })

        return citations
