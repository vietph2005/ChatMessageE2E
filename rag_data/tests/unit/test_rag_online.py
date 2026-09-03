"""
Unit tests for rag_online.py
Follows Constitution Principle VI (Unit Testing & Isolation with Mocking).
"""

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from rag_online import build_prompt, answer, SYSTEM_PROMPT


class TestRagOnline(unittest.TestCase):

    def test_build_prompt_with_contexts(self):
        query = "Làm sao để đăng nhập?"
        contexts = [
            {
                "id": "auth-001",
                "page_content": "Nhấn nút đăng nhập bằng Google trên màn hình.",
                "metadata": {"category": "Tài khoản & Xác thực"},
                "similarity": 0.9123
            }
        ]

        prompt = build_prompt(query, contexts)

        self.assertIn(SYSTEM_PROMPT, prompt)
        self.assertIn("TÀI LIỆU THAM KHẢO:", prompt)
        self.assertIn("[Tài liệu 1]", prompt)
        self.assertIn("Tài khoản & Xác thực", prompt)
        self.assertIn("Độ liên quan: 91%", prompt)
        self.assertIn("Nhấn nút đăng nhập bằng Google", prompt)
        self.assertIn(f"Câu hỏi của người dùng: {query}", prompt)

    def test_build_prompt_empty_contexts(self):
        query = "Thời tiết hôm nay thế nào?"
        contexts = []

        prompt = build_prompt(query, contexts)

        self.assertIn(SYSTEM_PROMPT, prompt)
        self.assertIn("[KHÔNG CÓ TÀI LIỆU THAM KHẢO PHÙ HỢP]", prompt)
        self.assertIn(f"Câu hỏi của người dùng: {query}", prompt)

    @patch("rag_online.embed_query")
    @patch("rag_online.retrieve")
    @patch("rag_online.generate_answer")
    def test_answer_flow_success(self, mock_gen, mock_ret, mock_embed):
        mock_embed.return_value = [0.01] * 3072
        mock_ret.return_value = [
            {
                "id": "msg-001",
                "page_content": "Nội dung hướng dẫn gửi tin nhắn.",
                "metadata": {"category": "Nhắn tin", "question": "Gửi tin nhắn thế nào?"},
                "similarity": 0.89
            }
        ]
        mock_gen.return_value = "Để gửi tin nhắn, bạn hãy nhấn nút gửi màu xanh."

        mock_collection = MagicMock()
        res = answer("Gửi tin nhắn thế nào?", collection=mock_collection, verbose=False)

        self.assertEqual(res["answer"], "Để gửi tin nhắn, bạn hãy nhấn nút gửi màu xanh.")
        self.assertTrue(res["has_context"])
        self.assertEqual(len(res["sources"]), 1)
        self.assertEqual(res["sources"][0]["id"], "msg-001")
        self.assertEqual(res["sources"][0]["category"], "Nhắn tin")
        self.assertEqual(res["sources"][0]["similarity"], 0.89)

    @patch("rag_online.embed_query")
    @patch("rag_online.retrieve")
    @patch("rag_online.generate_answer")
    def test_answer_flow_no_context(self, mock_gen, mock_ret, mock_embed):
        mock_embed.return_value = [0.01] * 3072
        mock_ret.return_value = []
        mock_gen.return_value = "Tôi chưa có thông tin về vấn đề này."

        mock_collection = MagicMock()
        res = answer("Thời tiết ngày mai?", collection=mock_collection, verbose=False)

        self.assertEqual(res["answer"], "Tôi chưa có thông tin về vấn đề này.")
        self.assertFalse(res["has_context"])
        self.assertEqual(len(res["sources"]), 0)


if __name__ == "__main__":
    unittest.main()
