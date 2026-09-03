"""
Contract and API tests for FastAPI RAG Microservice (rag_api.py).
Follows Constitution Principle VI §3 (API / Contract Testing).
"""

import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from rag_api import app


class TestRagApiContract(unittest.TestCase):

    def setUp(self):
        self.mock_collection = MagicMock()
        self.mock_collection.count.return_value = 37
        app.state.collection = self.mock_collection
        self.client = TestClient(app)

    def test_health_check_contract_success(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertIn("collection_count", data)
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["collection_count"], 37)

    def test_health_check_contract_unavailable(self):
        app.state.collection = None
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 503)
        self.assertIn("detail", response.json())

    @patch("rag_api.run_rag_answer")
    def test_ask_endpoint_contract_success(self, mock_rag_answer):
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
        # Verify contract schema fields
        self.assertIn("answer", data)
        self.assertIn("sources", data)
        self.assertIn("has_context", data)

        self.assertIsInstance(data["answer"], str)
        self.assertIsInstance(data["sources"], list)
        self.assertIsInstance(data["has_context"], bool)

        source = data["sources"][0]
        self.assertIn("id", source)
        self.assertIn("category", source)
        self.assertIn("question", source)
        self.assertIn("similarity", source)

    def test_ask_contract_validation_error_empty_question(self):
        payload = {"question": ""}
        response = self.client.post("/ask", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_ask_contract_service_unavailable_when_no_db(self):
        app.state.collection = None
        payload = {"question": "Có ai ở đây không?"}
        response = self.client.post("/ask", json=payload)
        self.assertEqual(response.status_code, 503)


if __name__ == "__main__":
    unittest.main()
