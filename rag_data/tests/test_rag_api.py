"""
Unit tests cho FastAPI RAG Microservice (rag_api.py) dùng unittest chuẩn
"""

import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rag_api import app


class TestRagApi(unittest.TestCase):

    def setUp(self):
        self.mock_collection = MagicMock()
        self.mock_collection.count.return_value = 42
        app.state.collection = self.mock_collection
        self.client = TestClient(app)

    def test_health_check_success(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["collection_count"], 42)

    @patch("rag_api.run_rag_answer")
    def test_ask_endpoint_success(self, mock_rag_answer):
        mock_rag_answer.return_value = {
            "answer": "Để tìm bạn bè, hãy nhập email vào ô tìm kiếm.",
            "sources": [
                {
                    "id": "search-001_c00",
                    "category": "Tìm kiếm",
                    "question": "Làm thế nào để tìm bạn bè?",
                    "similarity": 0.88,
                }
            ],
            "has_context": True,
        }

        payload = {"question": "Làm sao tìm bạn bè?"}
        response = self.client.post("/ask", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("tìm bạn bè", data["answer"])
        self.assertTrue(data["has_context"])
        self.assertEqual(len(data["sources"]), 1)
        self.assertEqual(data["sources"][0]["category"], "Tìm kiếm")

    def test_ask_validation_error_empty_question(self):
        payload = {"question": ""}
        response = self.client.post("/ask", json=payload)
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()

