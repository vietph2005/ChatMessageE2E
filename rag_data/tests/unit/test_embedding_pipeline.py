"""
Unit tests for embedding_pipeline.py
Follows Constitution Principle VI (Unit Testing & Isolation).
"""

import unittest
from pathlib import Path
import json
import sys

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from embedding_pipeline import (
    cosine_similarity,
    validate_embeddings,
    VECTOR_DIM
)
from tests.conftest import generate_dummy_vector


class TestEmbeddingPipeline(unittest.TestCase):

    def test_cosine_similarity_identical_vectors(self):
        vec_a = [1.0, 2.0, 3.0]
        vec_b = [1.0, 2.0, 3.0]
        self.assertAlmostEqual(cosine_similarity(vec_a, vec_b), 1.0, places=5)

    def test_cosine_similarity_orthogonal_vectors(self):
        vec_a = [1.0, 0.0]
        vec_b = [0.0, 1.0]
        self.assertAlmostEqual(cosine_similarity(vec_a, vec_b), 0.0, places=5)

    def test_cosine_similarity_opposite_vectors(self):
        vec_a = [1.0, 0.0]
        vec_b = [-1.0, 0.0]
        self.assertAlmostEqual(cosine_similarity(vec_a, vec_b), -1.0, places=5)

    def test_cosine_similarity_zero_vector(self):
        vec_a = [0.0, 0.0]
        vec_b = [1.0, 2.0]
        self.assertEqual(cosine_similarity(vec_a, vec_b), 0.0)

    def test_validate_embeddings_success(self):
        valid_items = [
            {
                "id": "test-001",
                "embedding": generate_dummy_vector(dim=VECTOR_DIM, seed_val=0.05),
                "metadata": {"id": "test-001"}
            }
        ]
        self.assertTrue(validate_embeddings(valid_items, original_count=1))

    def test_validate_embeddings_wrong_dimension(self):
        invalid_items = [
            {
                "id": "test-001",
                "embedding": [0.1, 0.2, 0.3],  # Chỉ có 3 chiều thay vì VECTOR_DIM (3072)
                "metadata": {"id": "test-001"}
            }
        ]
        self.assertFalse(validate_embeddings(invalid_items, original_count=1))

    def test_validate_embeddings_count_mismatch(self):
        valid_items = [
            {
                "id": "test-001",
                "embedding": generate_dummy_vector(dim=VECTOR_DIM),
                "metadata": {"id": "test-001"}
            }
        ]
        self.assertFalse(validate_embeddings(valid_items, original_count=2))

    def test_corpus_semantic_similarity_benchmark(self):
        """
        Kiểm tra tính nhất quán ngữ nghĩa từ file embeddings.json đã sinh:
        Cùng chủ đề (auth-001 vs auth-002) phải có độ tương đồng cao hơn khác chủ đề (auth-001 vs block-001).
        """
        embeddings_file = BASE_DIR / "embeddings" / "embeddings.json"
        if not embeddings_file.exists():
            self.skipTest("Chưa có file embeddings.json để kiểm tra benchmark")

        with open(embeddings_file, encoding="utf-8") as f:
            embedded_chunks = json.load(f)

        by_id = {item["metadata"]["id"]: item for item in embedded_chunks}
        if "auth-001" in by_id and "auth-002" in by_id and "block-001" in by_id:
            sim_same_topic = cosine_similarity(by_id["auth-001"]["embedding"], by_id["auth-002"]["embedding"])
            sim_diff_topic = cosine_similarity(by_id["auth-001"]["embedding"], by_id["block-001"]["embedding"])

            self.assertGreater(
                sim_same_topic,
                sim_diff_topic,
                f"Cùng chủ đề ({sim_same_topic:.4f}) phải có similarity cao hơn khác chủ đề ({sim_diff_topic:.4f})"
            )


if __name__ == "__main__":
    unittest.main()
