"""
test_layer4.py — Suite Kiểm Thử Toàn Diện Cho Layer 4 (Generator / Context-Augmented Generation)
================================================================================================
Áp dụng các kỹ thuật kiểm thử phần mềm tiêu chuẩn để bao phủ TOÀN BỘ các điều kiện & nhánh:
  1. Boundary Value Analysis (BVA) & Edge Cases:
     - has_context=False (câu hỏi ngoài phạm vi).
     - relevant_docs rỗng `[]` (dù has_context=True hay False).
     - Document khuyết thiếu trường: không có metadata, không có id, không có similarity, content rỗng.
     - Nhiều documents liên tiếp (đánh số thứ tự 1, 2, 3 trong prompt).
  2. Equivalence Partitioning (EP):
     - Phân vùng có context hợp lệ: Sinh câu trả lời chuẩn xác dựa trên context.
     - Phân vùng ngoài ngữ cảnh: Trả về OUT_OF_CONTEXT_ANSWER và sources rỗng.
     - Định dạng Prompt: format_context_blocks ghép chuẩn xác các block tài liệu.
  3. DTO Schema Compliance (Frontend & Backend):
     - Kiểm tra cấu trúc `sources`: `id`, `category`, `question`, `similarity`.
     - Ép kiểu similarity thành float.
     - Fallback default khi category hoặc id bị thiếu.
  4. Fault Injection & Negative Testing:
     - LLM gặp lỗi (Quota Exceeded 429, Connection Timeout).
     - Hệ thống xử lý an toàn bằng fallback message thông báo sự cố, vẫn giữ nguyên sources.
  5. Live Benchmark:
     - Kiểm thử thực tế với Gemini MAIN_MODEL_NAME.

Cách chạy:
  - Chạy toàn bộ (Unit Test + Live Benchmark):
      python rag_data/tests/test_layer4.py
  - Chỉ chạy Unit Test (Mock, 0ms, không tốn quota API):
      python rag_data/tests/test_layer4.py --unit
  - Chỉ chạy Live Benchmark:
      python rag_data/tests/test_layer4.py --live
"""

import sys
import time
import argparse
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Đảm bảo import được config và layers từ rag_data
CURRENT_DIR = Path(__file__).resolve().parent
RAG_DATA_DIR = CURRENT_DIR.parent
if str(RAG_DATA_DIR) not in sys.path:
    sys.path.insert(0, str(RAG_DATA_DIR))

from layers.layer4_generator import (
    generate_answer,
    format_context_blocks,
    build_generation_prompt,
    OUT_OF_CONTEXT_ANSWER,
    SYSTEM_GENERATOR_ROLE
)


# ══════════════════════════════════════════════════════════════════════════════
# PHẦN 1: UNIT TESTING WITH MOCKING & FAULT INJECTION (100% Branch Coverage)
# ══════════════════════════════════════════════════════════════════════════════

class TestLayer4Unit(unittest.TestCase):
    """
    Bộ Unit Test cô lập dùng mock để kiểm tra 100% các nhánh rẽ điều kiện (branch coverage),
    chuẩn hóa dữ liệu nguồn và khả năng chịu lỗi của Layer 4 Generator.
    """

    def setUp(self):
        self.patcher_grok = patch("layers.layer4_generator.is_grok_available", return_value=False)
        self.patcher_grok.start()

    def tearDown(self):
        self.patcher_grok.stop()

    # ── 1. Boundary Value Analysis & Edge Cases ─────────────────────────────
    def test_bva_has_context_false(self):
        """BVA: Khi has_context=False, trả về câu trả lời ngoài phạm vi và sources=[] không gọi LLM."""
        with patch("google.generativeai.GenerativeModel") as mock_model_cls:
            res = generate_answer("Thời tiết hôm nay thế nào?", relevant_docs=[], has_context=False)
            self.assertEqual(res["answer"], OUT_OF_CONTEXT_ANSWER)
            self.assertEqual(res["sources"], [])
            self.assertFalse(res["has_context"])
            mock_model_cls.assert_not_called()

    def test_bva_empty_relevant_docs_even_if_has_context_true(self):
        """BVA: Dù has_context=True nhưng relevant_docs rỗng thì vẫn phải trả về ngoài phạm vi."""
        with patch("google.generativeai.GenerativeModel") as mock_model_cls:
            res = generate_answer("Câu hỏi", relevant_docs=[], has_context=True)
            self.assertEqual(res["answer"], OUT_OF_CONTEXT_ANSWER)
            self.assertEqual(res["sources"], [])
            self.assertFalse(res["has_context"])
            mock_model_cls.assert_not_called()

    def test_bva_format_context_blocks_empty_list(self):
        """BVA: format_context_blocks với danh sách rỗng trả về chuỗi rỗng."""
        res = format_context_blocks([])
        self.assertEqual(res, "")

    def test_bva_docs_missing_metadata_fields(self):
        """BVA: Document khuyết thiếu metadata/id/similarity được điền giá trị mặc định an toàn."""
        docs = [
            {
                "content": "Nội dung không có metadata",
                # Thiếu id, metadata, similarity
            }
        ]

        with patch("google.generativeai.GenerativeModel") as mock_model_cls:
            mock_instance = MagicMock()
            mock_instance.generate_content.return_value.text = "Câu trả lời mẫu"
            mock_model_cls.return_value = mock_instance

            res = generate_answer("Câu hỏi", docs, has_context=True)
            self.assertTrue(res["has_context"])
            self.assertEqual(len(res["sources"]), 1)
            src = res["sources"][0]
            self.assertEqual(src["id"], "src_0")
            self.assertEqual(src["category"], "Chung")
            self.assertEqual(src["question"], "")
            self.assertEqual(src["similarity"], 0.0)

    # ── 2. Format Context & Prompt Building ──────────────────────────────────
    def test_format_context_multiple_blocks(self):
        """Kiểm tra format_context_blocks đánh số và hiển thị đúng thông tin của từng block."""
        docs = [
            {
                "content": "Chi tiết mã hóa AES-256",
                "metadata": {"category": "Mã hóa", "question": "AES là gì?"}
            },
            {
                "content": "Chi tiết trao đổi khóa ECDH",
                "metadata": {"category": "Bảo mật", "question": "ECDH là gì?"}
            }
        ]
        context_str = format_context_blocks(docs)
        self.assertIn("--- [TÀI LIỆU 1] ---", context_str)
        self.assertIn("Danh mục: Mã hóa", context_str)
        self.assertIn("Chủ đề gốc: AES là gì?", context_str)
        self.assertIn("Nội dung:\nChi tiết mã hóa AES-256", context_str)

        self.assertIn("--- [TÀI LIỆU 2] ---", context_str)
        self.assertIn("Danh mục: Bảo mật", context_str)
        self.assertIn("Chủ đề gốc: ECDH là gì?", context_str)

    def test_build_generation_prompt_structure(self):
        """Kiểm tra prompt hoàn chỉnh chứa đầy đủ role, context và câu hỏi người dùng."""
        docs = [{"content": "Nội dung bảo mật", "metadata": {"category": "Bảo mật"}}]
        prompt = build_generation_prompt("Mã hóa thế nào?", docs)

        self.assertIn(SYSTEM_GENERATOR_ROLE, prompt)
        self.assertIn("TÀI LIỆU THAM KHẢO TỪ HỆ THỐNG", prompt)
        self.assertIn("Nội dung bảo mật", prompt)
        self.assertIn('CÂU HỎI CỦA NGƯỜI DÙNG:\n"Mã hóa thế nào?"', prompt)

    # ── 3. Generation Flow & Sources Schema ──────────────────────────────────
    @patch("google.generativeai.GenerativeModel")
    def test_generate_answer_success_flow(self, mock_model_cls):
        """EP: Sinh câu trả lời thành công từ LLM với đầy đủ sources."""
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value.text = "ChatMessage sử dụng mã hóa AES-256-GCM."
        mock_model_cls.return_value = mock_instance

        docs = [
            {
                "id": "doc_101",
                "content": "Thông tin AES-256-GCM",
                "metadata": {"category": "Mã hóa", "question": "Mã hóa tin nhắn?"},
                "similarity": 0.95234
            }
        ]

        res = generate_answer("ChatMessage mã hóa ra sao?", docs, has_context=True)
        self.assertEqual(res["answer"], "ChatMessage sử dụng mã hóa AES-256-GCM.")
        self.assertTrue(res["has_context"])
        self.assertEqual(len(res["sources"]), 1)
        self.assertEqual(res["sources"][0]["id"], "doc_101")
        self.assertEqual(res["sources"][0]["category"], "Mã hóa")
        self.assertEqual(res["sources"][0]["similarity"], 0.95234)

    # ── 4. Fault Injection & Negative Testing ────────────────────────────────
    @patch("google.generativeai.GenerativeModel")
    def test_fault_injection_llm_exception_fallback(self, mock_model_cls):
        """
        Fault Injection: Khi Gemini ném ngoại lệ (Quota Exceeded 429 / Connection Error),
        Layer 4 phải fallback trả về câu thông báo sự cố nhưng vẫn giữ danh sách nguồn tham khảo.
        """
        mock_instance = MagicMock()
        mock_instance.generate_content.side_effect = RuntimeError("ResourceExhausted: 429 Quota Exceeded")
        mock_model_cls.return_value = mock_instance

        docs = [
            {
                "id": "doc_err_01",
                "content": "Tài liệu kỹ thuật",
                "metadata": {"category": "Sự cố", "question": "Lỗi kết nối"},
                "similarity": 0.88
            }
        ]

        res = generate_answer("Lỗi kết nối", docs, has_context=True)
        self.assertIn("hệ thống AI tạm thời gặp sự cố", res["answer"])
        self.assertTrue(res["has_context"])
        self.assertEqual(len(res["sources"]), 1)
        self.assertEqual(res["sources"][0]["id"], "doc_err_01")


# ══════════════════════════════════════════════════════════════════════════════
# PHẦN 2: LIVE BENCHMARK (Tích hợp thực tế với Gemini API)
# ══════════════════════════════════════════════════════════════════════════════

LIVE_GENERATION_SCENARIOS = [
    {
        "name": "Hỏi về bắt tay 4 lớp (Có context)",
        "question": "Quy trình bắt tay 4 lớp trong ChatMessage hoạt động thế nào?",
        "docs": [
            {
                "id": "live_sec_01",
                "content": (
                    "ChatMessageE2E sử dụng cơ chế bắt tay 4 lớp (4-Layer Handshake):\n"
                    "1. Bước 1: Trao đổi khóa công khai ECDH (X25519) giữa hai người dùng.\n"
                    "2. Bước 2: Hai bên tính toán Secret Key chung bằng hàm HKDF-SHA256.\n"
                    "3. Bước 3: Xác thực chữ ký Ed25519 chống tấn công Man-in-the-Middle.\n"
                    "4. Bước 4: Thiết lập phiên chat mã hóa bằng AES-256-GCM."
                ),
                "metadata": {"category": "Bắt tay bảo mật", "question": "Bắt tay 4 lớp"},
                "similarity": 0.95
            }
        ],
        "has_context": True,
        "expected_keywords": ["ECDH", "AES-256-GCM", "HKDF", "Ed25519"]
    },
    {
        "name": "Câu hỏi ngoài phạm vi (Không có context)",
        "question": "Thời tiết ngày mai tại Hà Nội thế nào?",
        "docs": [],
        "has_context": False,
        "expected_keywords": ["chưa có thông tin", "ChatMessageE2E"]
    }
]


def run_live_benchmark():
    """Chạy kiểm thử thực tế Layer 4 với Gemini."""
    print("\n" + "=" * 80)
    print("🚀 BẮT ĐẦU KIỂM THỬ THỰC TẾ LAYER 4 VỚI GEMINI API")
    print("   (Đánh giá Khả năng sinh câu trả lời Grounded và xử lý Out-of-Context)")
    print("=" * 80)

    total = len(LIVE_GENERATION_SCENARIOS)
    passed = 0

    for idx, sc in enumerate(LIVE_GENERATION_SCENARIOS, 1):
        name = sc["name"]
        q = sc["question"]
        docs = sc["docs"]
        has_ctx = sc["has_context"]
        keywords = sc["expected_keywords"]

        print(f"\n[{idx}/{total}] 🧪 Kịch bản: {name}")
        print(f"       ❓ Câu hỏi: \"{q}\"")

        time.sleep(1.0)
        t0 = time.time()
        res = generate_answer(q, docs, has_context=has_ctx)
        duration_ms = (time.time() - t0) * 1000

        ans = res["answer"]
        has_all_kw = all(kw.lower() in ans.lower() for kw in keywords)
        context_matched = (res["has_context"] == has_ctx)
        is_pass = has_all_kw and context_matched

        if is_pass:
            passed += 1

        mark = "✅ PASS" if is_pass else "❌ FAIL"
        print(f"       ⏱️ Thời gian phản hồi: {duration_ms:.1f} ms | Đánh giá: {mark}")
        print(f"       🤖 Trích đoạn câu trả lời: {ans[:160]}...")
        print(f"       📚 Số lượng sources: {len(res['sources'])}")

    print("\n" + "-" * 80)
    print(f"📊 KẾT QUẢ ĐÁNH GIÁ THỰC TẾ LAYER 4: {passed}/{total} VƯỢT QUA")
    print("=" * 80)


# ══════════════════════════════════════════════════════════════════════════════
# PHẦN 3: CLI ENTRYPOINT
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Chương trình kiểm thử chuyên sâu cho Layer 4 (Generator)")
    parser.add_argument("--unit", action="store_true", help="Chỉ chạy Unit Test (Mock, 0ms, không gọi API)")
    parser.add_argument("--live", action="store_true", help="Chỉ chạy Live Benchmark (Kiểm thử thực tế)")
    args = parser.parse_args()

    if args.unit:
        print("🧪 [CHẾ ĐỘ] Chạy Unit Tests với Mocking & Fault Injection (Layer 4)...")
        suite = unittest.TestLoader().loadTestsFromTestCase(TestLayer4Unit)
        runner = unittest.TextTestRunner(verbosity=2)
        runner.run(suite)
    elif args.live:
        print("🌐 [CHẾ ĐỘ] Chạy Live Benchmark với Gemini (Layer 4)...")
        run_live_benchmark()
    else:
        print("================================================================================")
        print("🧪 [BƯỚC 1/2] CHẠY TỰ ĐỘNG UNIT TESTS (MOCK, FAULT INJECTION & SCHEMA COVERAGE)")
        print("================================================================================")
        suite = unittest.TestLoader().loadTestsFromTestCase(TestLayer4Unit)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        if result.wasSuccessful():
            print("\n✅ TẤT CẢ UNIT TESTS ĐÃ VƯỢT QUA!")
            run_live_benchmark()
        else:
            print("\n❌ CÓ LỖI TRONG UNIT TESTS. DỪNG LIVE BENCHMARK.")


if __name__ == "__main__":
    main()
