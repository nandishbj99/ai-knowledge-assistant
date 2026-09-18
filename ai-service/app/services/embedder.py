from typing import List, Optional
import math
from app.core.config import settings

class EmbeddingService:
    """Generates vector embeddings using Google text-embedding-004 (768 dimensions)."""

    def __init__(self):
        self.model = settings.EMBEDDING_MODEL or "text-embedding-004"
        self.dimension = 768

    async def get_embeddings(self, texts: List[str], task_type: str = "RETRIEVAL_DOCUMENT") -> List[List[float]]:
        if not texts:
            return []

        if settings.GEMINI_API_KEY:
            return await self._get_gemini_embeddings(texts, task_type=task_type)
        else:
            # Fallback deterministic pseudo-vector (768d) for local unit testing without API key
            return [self._mock_vector(len(t), dim=768) for t in texts]

    async def get_query_embedding(self, query: str) -> List[float]:
        vectors = await self.get_embeddings([query], task_type="RETRIEVAL_QUERY")
        return vectors[0]

    async def _get_gemini_embeddings(self, texts: List[str], task_type: str = "RETRIEVAL_DOCUMENT") -> List[List[float]]:
        from google import genai
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        all_embeddings = []

        for text in texts:
            response = client.models.embed_content(
                model=self.model,
                contents=text,
                config={"task_type": task_type}
            )
            # Ensure embedding values are float
            vec = [float(v) for v in response.embedding.values]
            all_embeddings.append(vec)

        return all_embeddings

    def _mock_vector(self, seed: int, dim: int = 768) -> List[float]:
        # Unit-length normalized pseudo-vector of dimension 768
        raw = [math.sin(seed + i * 0.1) for i in range(dim)]
        norm = math.sqrt(sum(x * x for x in raw)) or 1.0
        return [x / norm for x in raw]
