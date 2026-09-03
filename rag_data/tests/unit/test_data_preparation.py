"""
Unit tests for data_preparation.py
Follows Constitution Principle VI (Unit Testing & Isolation).
"""

import unittest
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from data_preparation import convert_to_documents, validate_documents, MAX_DOC_LENGTH_CEILING
from tests.conftest import get_sample_raw_corpus, get_sample_documents


class TestDataPreparation(unittest.TestCase):

    def setUp(self):
        self.raw_corpus = get_sample_raw_corpus()

    def test_convert_to_documents_structure(self):
        docs = convert_to_documents(self.raw_corpus)
        self.assertEqual(len(docs), len(self.raw_corpus))

        for idx, doc in enumerate(docs):
            self.assertIn("page_content", doc)
            self.assertIn("metadata", doc)

            # Kiểm tra page_content chứa cả câu hỏi và câu trả lời
            self.assertIn("Câu hỏi:", doc["page_content"])
            self.assertIn("Trả lời:", doc["page_content"])
            self.assertIn(self.raw_corpus[idx]["question"], doc["page_content"])

            # Kiểm tra metadata đầy đủ
            meta = doc["metadata"]
            self.assertEqual(meta["id"], self.raw_corpus[idx]["id"])
            self.assertEqual(meta["category"], self.raw_corpus[idx]["category"])
            self.assertEqual(meta["source"], self.raw_corpus[idx]["source"])
            self.assertEqual(meta["doc_type"], "faq")
            self.assertEqual(meta["app"], "ChatMessageE2E")
            self.assertEqual(meta["language"], "vi")

    def test_validate_documents_success(self):
        docs = get_sample_documents()
        self.assertTrue(validate_documents(docs))

    def test_validate_documents_empty_page_content(self):
        docs = [
            {
                "page_content": "   ",
                "metadata": {
                    "id": "bad-001",
                    "category": "Test",
                    "question": "Q?",
                    "source": "s1"
                }
            }
        ]
        self.assertFalse(validate_documents(docs))

    def test_validate_documents_duplicate_id(self):
        docs = [
            {
                "page_content": "Doc 1 content",
                "metadata": {"id": "dup-001", "category": "A", "question": "Q1?", "source": "s1"}
            },
            {
                "page_content": "Doc 2 content",
                "metadata": {"id": "dup-001", "category": "A", "question": "Q2?", "source": "s2"}
            }
        ]
        self.assertFalse(validate_documents(docs))

    def test_validate_documents_too_short(self):
        docs = [
            {
                "page_content": "Ngắn",  # < 20 ký tự
                "metadata": {"id": "short-001", "category": "Test", "question": "Short?", "source": "s1"}
            }
        ]
        self.assertFalse(validate_documents(docs))

    def test_validate_documents_warning_on_exceeding_max_ceiling(self):
        # Vượt trần 1200 ký tự sinh warning nhưng không làm fail validation
        overlength_content = "A" * (MAX_DOC_LENGTH_CEILING + 50)
        docs = [
            {
                "page_content": overlength_content,
                "metadata": {"id": "long-001", "category": "Test", "question": "Long?", "source": "s1"}
            }
        ]
        self.assertTrue(validate_documents(docs))


if __name__ == "__main__":
    unittest.main()
