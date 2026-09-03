"""
Integration tests for ChromaDB Vector Database.
Follows Constitution Principle VI §2 (Integration Testing with real storage).
"""

import unittest
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from vector_db import init_chromadb, get_or_create_collection, search, CHROMA_DB_DIR


class TestVectorDbIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not CHROMA_DB_DIR.exists():
            raise unittest.SkipTest("ChromaDB chưa được tạo, cần chạy pipeline offline trước")
        cls.client = init_chromadb()
        cls.collection = get_or_create_collection(cls.client)

    def test_chromadb_collection_is_populated(self):
        count = self.collection.count()
        self.assertGreater(count, 0, "ChromaDB collection không được rỗng")

    def test_chromadb_query_retrieval(self):
        # Lấy document đầu tiên từ collection để lấy vector mẫu
        sample = self.collection.get(limit=1, include=["embeddings", "metadatas", "documents"])
        self.assertTrue(sample["ids"], "Collection phải có ít nhất 1 item")

        sample_embedding = sample["embeddings"][0]
        results = search(self.collection, sample_embedding, top_k=3)

        self.assertGreater(len(results), 0, "Tìm kiếm vector phải trả về kết quả")
        top_result = results[0]
        self.assertIn("id", top_result)
        self.assertIn("similarity", top_result)
        self.assertIn("metadata", top_result)

        # Vector truy vấn chính nó phải có độ tương đồng xấp xỉ 1.0
        self.assertGreaterEqual(top_result["similarity"], 0.98)


if __name__ == "__main__":
    unittest.main()
