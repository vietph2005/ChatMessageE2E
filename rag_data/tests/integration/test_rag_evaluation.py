"""
Integration & Benchmark Evaluation tests for RAG pipeline.
Follows Constitution Principle VI §4 (End-to-End & Boundary Verification).
"""

import unittest
import os
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from rag_online import answer, get_collection, CHROMA_DB_DIR


class TestRagEvaluation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not CHROMA_DB_DIR.exists():
            raise unittest.SkipTest("ChromaDB chưa tồn tại")
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            # Try load .env
            try:
                from dotenv import load_dotenv
                load_dotenv(BASE_DIR / ".env")
                api_key = os.getenv("GOOGLE_API_KEY")
            except Exception:
                pass

        if not api_key:
            raise unittest.SkipTest("Thiếu GOOGLE_API_KEY để chạy live evaluation test")

        cls.collection = get_collection()

    def test_in_scope_question_retrieval(self):
        """Câu hỏi trong phạm vi nghiệp vụ phải trả lời kèm nguồn tham khảo."""
        query = "Làm sao để tìm người dùng khác để bắt đầu chat?"
        result = answer(query, collection=self.collection, verbose=False)

        self.assertTrue(result["has_context"], "Câu hỏi hợp lệ phải tìm thấy ngữ cảnh")
        self.assertGreater(len(result["sources"]), 0, "Phải có nguồn tham khảo")
        self.assertIn("answer", result)
        self.assertGreater(len(result["answer"]), 10)

    def test_out_of_scope_question_guardrail(self):
        """Câu hỏi ngoài phạm vi (thời tiết) phải bị từ chối khéo, không bịa đặt."""
        query = "Thời tiết hôm nay thế nào?"
        result = answer(query, collection=self.collection, verbose=False)

        # Gemini phải tuân thủ System Prompt và từ chối trả lời ngoài phạm vi
        self.assertIn("chưa có thông tin", result["answer"].lower())


if __name__ == "__main__":
    unittest.main()
