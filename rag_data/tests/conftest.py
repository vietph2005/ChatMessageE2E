"""
Shared test fixtures and configuration for RAG testing suite.
Follows Constitution Principle VI (Comprehensive Automated Testing).
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

# Ensure rag_data directory is on sys.path
RAG_DATA_DIR = Path(__file__).resolve().parent.parent
if str(RAG_DATA_DIR) not in sys.path:
    sys.path.insert(0, str(RAG_DATA_DIR))


def get_sample_raw_corpus() -> List[Dict[str, Any]]:
    """Returns sample raw FAQ corpus items."""
    return [
        {
            "id": "auth-001",
            "category": "Tài khoản & Xác thực",
            "question": "Làm thế nào để đăng nhập vào ChatMessage?",
            "answer": "Nhấn nút 'Đăng nhập bằng Google' trên trang chủ và hoàn tất OAuth flow.",
            "source": "spec-001"
        },
        {
            "id": "auth-002",
            "category": "Tài khoản & Xác thực",
            "question": "Tôi có thể đăng nhập bằng tài khoản khác không?",
            "answer": "Hiện tại ứng dụng chỉ hỗ trợ đăng nhập qua tài khoản Google OAuth2.",
            "source": "spec-001"
        },
        {
            "id": "block-001",
            "category": "Chặn & Bỏ chặn",
            "question": "Làm thế nào để chặn người dùng khác?",
            "answer": "Mở thông tin liên hệ và bấm Chặn liên hệ (Block Contact).",
            "source": "spec-002"
        }
    ]


def get_sample_documents() -> List[Dict[str, Any]]:
    """Returns sample LangChain formatted documents."""
    return [
        {
            "page_content": "Câu hỏi: Làm thế nào để đăng nhập vào ChatMessage?\n\nTrả lời: Nhấn nút 'Đăng nhập bằng Google' trên trang chủ và hoàn tất OAuth flow.",
            "metadata": {
                "id": "auth-001",
                "category": "Tài khoản & Xác thực",
                "question": "Làm thế nào để đăng nhập vào ChatMessage?",
                "source": "spec-001",
                "doc_type": "faq",
                "language": "vi",
                "app": "ChatMessageE2E"
            }
        },
        {
            "page_content": "Câu hỏi: Làm thế nào để chặn người dùng khác?\n\nTrả lời: Mở thông tin liên hệ và bấm Chặn liên hệ (Block Contact).",
            "metadata": {
                "id": "block-001",
                "category": "Chặn & Bỏ chặn",
                "question": "Làm thế nào để chặn người dùng khác?",
                "source": "spec-002",
                "doc_type": "faq",
                "language": "vi",
                "app": "ChatMessageE2E"
            }
        }
    ]


def generate_dummy_vector(dim: int = 3072, seed_val: float = 0.01) -> List[float]:
    """Generates a dummy float vector of dimension `dim`."""
    return [seed_val] * dim
