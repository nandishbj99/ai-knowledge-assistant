import asyncio
import math
from app.services.embedder import EmbeddingService

async def run_embedder_tests():
    embedder = EmbeddingService()
    texts = [
        "What was the operating profit in Q3?",
        "Cloud enterprise retention reached 128%."
    ]

    vectors = await embedder.get_embeddings(texts)

    assert len(vectors) == 2, f"Expected 2 vectors, got {len(vectors)}"
    for vec in vectors:
        # Strictly verify Google text-embedding-004 768 dimensions
        assert len(vec) == 768, f"Expected 768 dimensions, got {len(vec)}"
        # Verify vector normalization (magnitude close to 1.0)
        norm = math.sqrt(sum(x * x for x in vec))
        assert abs(norm - 1.0) < 1e-3, f"Expected unit norm, got {norm}"

    query_vec = await embedder.get_query_embedding("Summarize revenue metrics")
    assert len(query_vec) == 768, f"Expected 768 dimensions, got {len(query_vec)}"

def test_embedder():
    asyncio.run(run_embedder_tests())

if __name__ == "__main__":
    test_embedder()
    print("=== ALL EMBEDDER TESTS (768d) PASSED SUCCESSFULLY! ===")
