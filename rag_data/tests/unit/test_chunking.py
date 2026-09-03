"""
Unit tests for chunking.py
Follows Constitution Principle VI (Unit Testing & Isolation).
"""

import unittest
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from chunking import (
    _has_table_or_list,
    _keep_as_single_chunk,
    _split_with_recursive,
    run_chunking,
    validate_chunks,
    CHUNK_SIZE_THRESHOLD
)
from tests.conftest import get_sample_documents


class TestChunking(unittest.TestCase):

    def test_has_table_or_list_detection(self):
        # Table detection
        table_text = "Dưới đây là bảng so sánh:\n| Tính năng | Hỗ trợ |\n|---|---|\n| E2EE | Có |"
        self.assertTrue(_has_table_or_list(table_text))

        # Numbered list detection
        numbered_text = "Quy trình thực hiện:\n1. Bước một\n2. Bước hai"
        self.assertTrue(_has_table_or_list(numbered_text))

        # Bullet list detection
        bullet_text = "Các điều kiện:\n- Điều kiện A\n- Điều kiện B"
        self.assertTrue(_has_table_or_list(bullet_text))

        # Plain text
        plain_text = "Đây là văn bản hoàn toàn bình thường không có danh sách hay bảng biểu."
        self.assertFalse(_has_table_or_list(plain_text))

    def test_keep_as_single_chunk(self):
        sample_doc = get_sample_documents()[0]
        chunks = _keep_as_single_chunk(sample_doc, original_index=0)

        self.assertEqual(len(chunks), 1)
        chunk = chunks[0]
        self.assertEqual(chunk["page_content"], sample_doc["page_content"].strip())
        self.assertEqual(chunk["metadata"]["chunk_index"], 0)
        self.assertEqual(chunk["metadata"]["chunk_total"], 1)
        self.assertEqual(chunk["metadata"]["chunk_strategy"], "single")
        self.assertEqual(chunk["metadata"]["doc_index"], 0)
        self.assertEqual(chunk["metadata"]["char_count"], len(sample_doc["page_content"].strip()))

    def test_split_with_recursive_mocked(self):
        long_text = "Câu hỏi: Chi tiết chính sách bảo mật?\n\nTrả lời: " + ("Thông tin rất dài. " * 50)
        doc = {
            "page_content": long_text,
            "metadata": {"id": "sec-001", "category": "Security", "question": "Q?", "source": "s1"}
        }

        mock_splitter_class = unittest.mock.MagicMock()
        mock_splitter_instance = unittest.mock.MagicMock()
        mock_splitter_instance.split_text.return_value = ["Đoạn 1", "Đoạn 2", "Đoạn 3"]
        mock_splitter_class.return_value = mock_splitter_instance

        mock_module = unittest.mock.MagicMock()
        mock_module.RecursiveCharacterTextSplitter = mock_splitter_class

        with unittest.mock.patch.dict("sys.modules", {"langchain.text_splitter": mock_module}):
            chunks = _split_with_recursive(doc, original_index=1)
            self.assertEqual(len(chunks), 3)
            for i, c in enumerate(chunks):
                self.assertEqual(c["metadata"]["chunk_index"], i)
                self.assertEqual(c["metadata"]["chunk_total"], 3)
                self.assertEqual(c["page_content"], f"Đoạn {i+1}")
                self.assertIn("id", c["metadata"])

    def test_split_with_recursive_fallback_when_uninstalled(self):
        doc = {
            "page_content": "Văn bản mẫu dài",
            "metadata": {"id": "sec-002", "category": "Security", "question": "Q?", "source": "s1"}
        }
        with unittest.mock.patch.dict("sys.modules", {"langchain.text_splitter": None}):
            chunks = _split_with_recursive(doc, original_index=2)
            self.assertEqual(len(chunks), 1)
            self.assertEqual(chunks[0]["metadata"]["chunk_strategy"], "single")

    def test_run_chunking_and_validate(self):
        docs = get_sample_documents()
        chunks, strategy_counts = run_chunking(docs)

        self.assertGreaterEqual(len(chunks), len(docs))
        self.assertTrue(validate_chunks(chunks))


if __name__ == "__main__":
    unittest.main()
