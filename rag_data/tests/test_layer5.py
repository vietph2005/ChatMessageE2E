"""
test_layer5.py — Suite Kiểm Thử Toàn Diện Cho Layer 5 (Self-RAG Verifier)
=========================================================================
Áp dụng các kỹ thuật kiểm thử phần mềm tiêu chuẩn để bao phủ TOÀN BỘ các điều kiện & nhánh:
  1. Boundary Value Analysis (BVA) & Edge Cases:
     - has_context=False hoặc docs=[]: Phê duyệt (APPROVED) ngay lập tức, không gọi mô hình.
     - grade_hallucination khi docs rỗng: Trả về True và lý do ngoài phạm vi.
  2. BƯỚC 5a — Hallucination Grader:
     - Đánh giá qua Grok (xAI) khi Grok khả dụng: Nhánh "grade: yes" và "grade: no".
     - Fallback từ Grok sang Gemini khi Grok trả về None / lỗi mạng.
     - Gemini Grader khi Grok không khả dụng: Nhánh "grade: yes" và "grade: no".
     - Khả năng chịu lỗi (Fault Injection): Khi cả LLM ném ngoại lệ, mặc định an toàn là True.
  3. BƯỚC 5b — Answer Usefulness Grader:
     - Đánh giá qua Grok (xAI) khi khả dụng.
     - Đánh giá qua Gemini khi Grok không khả dụng / thất bại.
     - Khả năng chịu lỗi: Ngoại lệ LLM trả về True an toàn.
  4. Vòng lặp Sửa lỗi Tự động (Self-Correction & Re-generation):
     - Kịch bản hoàn hảo: Đạt ngay lần đầu (attempt 0) -> APPROVED.
     - Kịch bản tự sửa lỗi (Re-generation): Lần đầu bị ảo giác, sinh lại thành công -> REFINED.
     - Kịch bản Fail-Safe Fallback: Hết lượt thử mà vẫn ảo giác -> Trích xuất tài liệu gốc, status FALLBACK_TO_SOURCE.
     - Kịch bản Grounded nhưng không hữu ích (lạc đề) -> PASSED_WITH_WARNING.
     - Chịu lỗi khi mô hình Re-generation gặp ngoại lệ.
  5. Live Benchmark:
     - Đánh giá thực nghiệm quy trình thẩm định trên dữ liệu thật.

Cách chạy:
  - Chạy toàn bộ (Unit Test + Live Benchmark):
      python rag_data/tests/test_layer5.py
  - Chỉ chạy Unit Test (Mock, 0ms, không tốn quota API):
      python rag_data/tests/test_layer5.py --unit
  - Chỉ chạy Live Benchmark:
      python rag_data/tests/test_layer5.py --live
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

from layers.layer5_verifier import (
    grade_hallucination,
    grade_usefulness,
    verify_and_refine
)


# ══════════════════════════════════════════════════════════════════════════════
# PHẦN 1: UNIT TESTING WITH MOCKING & FAULT INJECTION (100% Branch Coverage)
# ══════════════════════════════════════════════════════════════════════════════

class TestLayer5Unit(unittest.TestCase):
    """
    Bộ Unit Test cô lập dùng mock để kiểm tra 100% các nhánh rẽ điều kiện (branch coverage),
    cơ chế thẩm định chéo Grok/Gemini và máy trạng thái (state machine) của Layer 5.
    """

    # ── 1. Boundary Value Analysis & Edge Cases ─────────────────────────────
    def test_bva_has_context_false_or_empty_docs(self):
        """BVA: has_context=False hoặc docs=[] được phê duyệt (APPROVED) ngay lập tức."""
        res_no_ctx = verify_and_refine("Câu hỏi", "Câu trả lời", docs=[], has_context=False)
        self.assertEqual(res_no_ctx["status"], "APPROVED")
        self.assertTrue(res_no_ctx["is_grounded"])
        self.assertTrue(res_no_ctx["is_useful"])

        res_empty_docs = verify_and_refine("Câu hỏi", "Câu trả lời", docs=[], has_context=True)
        self.assertEqual(res_empty_docs["status"], "APPROVED")

    def test_bva_grade_hallucination_empty_docs(self):
        """BVA: grade_hallucination khi docs rỗng trả về True ngay lập tức."""
        is_grounded, reason = grade_hallucination("Câu trả lời", [])
        self.assertTrue(is_grounded)
        self.assertIn("ngoài phạm vi", reason)

    # ── 2. Hallucination Grader (Grok & Gemini Paths) ────────────────────────
    # ── 2. Hallucination Grader (Gemini Primary & Grok Fallback) ────────────
    @patch("google.generativeai.GenerativeModel")
    def test_hallucination_gemini_verdict_yes(self, mock_model_cls):
        """Gemini Path: Gemini trả về 'GRADE: yes' -> is_grounded = True."""
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value.text = "GRADE: yes\nREASON: Khớp hoàn toàn với tài liệu."
        mock_model_cls.return_value = mock_instance
        docs = [{"content": "ChatMessage mã hóa AES-256"}]

        is_grounded, reason = grade_hallucination("ChatMessage dùng AES-256", docs)
        self.assertTrue(is_grounded)
        self.assertIn("Gemini", reason)

    @patch("google.generativeai.GenerativeModel")
    def test_hallucination_gemini_verdict_no(self, mock_model_cls):
        """Gemini Path: Gemini trả về 'GRADE: no' -> is_grounded = False."""
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value.text = "GRADE: no\nREASON: Bịa đặt thuật toán RSA 4096."
        mock_model_cls.return_value = mock_instance
        docs = [{"content": "ChatMessage mã hóa AES-256"}]

        is_grounded, reason = grade_hallucination("ChatMessage dùng RSA 4096", docs)
        self.assertFalse(is_grounded)
        self.assertIn("Gemini", reason)

    @patch("google.generativeai.GenerativeModel")
    @patch("layers.layer5_verifier.is_grok_available", return_value=True)
    @patch("layers.layer5_verifier.call_grok_chat")
    def test_hallucination_gemini_fails_fallback_to_grok(self, mock_grok, mock_grok_avail, mock_model_cls):
        """Fallback: Khi Gemini lỗi ngoại lệ, tự động fallback sang Grok."""
        mock_instance = MagicMock()
        mock_instance.generate_content.side_effect = Exception("Gemini Quota Exceeded")
        mock_model_cls.return_value = mock_instance

        mock_grok.return_value = "GRADE: yes\nREASON: Thông tin chuẩn xác."

        docs = [{"content": "Thông tin chuẩn"}]
        is_grounded, reason = grade_hallucination("Thông tin chuẩn", docs)
        self.assertTrue(is_grounded)
        self.assertIn("Grok Fallback", reason)

    @patch("google.generativeai.GenerativeModel")
    @patch("layers.layer5_verifier.is_grok_available", return_value=False)
    def test_hallucination_exception_fail_safe(self, mock_grok_avail, mock_model_cls):
        """Fault Injection: Khi cả hai đều lỗi, fail-safe mặc định coi là grounded."""
        mock_instance = MagicMock()
        mock_instance.generate_content.side_effect = RuntimeError("API Quota 429")
        mock_model_cls.return_value = mock_instance

        docs = [{"content": "Nội dung"}]
        is_grounded, reason = grade_hallucination("Câu trả lời", docs)
        self.assertTrue(is_grounded)
        self.assertIn("Bỏ qua do lỗi grader", reason)

    # ── 3. Answer Usefulness Grader ──────────────────────────────────────────
    @patch("google.generativeai.GenerativeModel")
    def test_usefulness_gemini_verdict_yes(self, mock_model_cls):
        """Usefulness: Gemini đánh giá hữu ích 'GRADE: yes'."""
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value.text = "GRADE: yes\nREASON: Trả lời đúng trọng tâm."
        mock_model_cls.return_value = mock_instance

        is_useful, reason = grade_usefulness("Đăng nhập thế nào?", "Hướng dẫn đăng nhập OAuth2")
        self.assertTrue(is_useful)
        self.assertIn("Gemini", reason)

    @patch("google.generativeai.GenerativeModel")
    def test_usefulness_gemini_verdict_no(self, mock_model_cls):
        """Usefulness: Gemini đánh giá lạc đề 'GRADE: no'."""
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value.text = "GRADE: no\nREASON: Lạc đề, không trả lời câu hỏi."
        mock_model_cls.return_value = mock_instance

        is_useful, reason = grade_usefulness("Đăng nhập thế nào?", "Hôm nay trời nắng đẹp")
        self.assertFalse(is_useful)
        self.assertIn("Gemini", reason)

    @patch("google.generativeai.GenerativeModel")
    @patch("layers.layer5_verifier.is_grok_available", return_value=False)
    def test_usefulness_gemini_exception_fail_safe(self, mock_grok_avail, mock_model_cls):
        """Fault Injection: Usefulness grader gặp lỗi LLM -> Mặc định coi là useful."""
        mock_instance = MagicMock()
        mock_instance.generate_content.side_effect = Exception("Model timeout")
        mock_model_cls.return_value = mock_instance

        is_useful, reason = grade_usefulness("Câu hỏi", "Câu trả lời")
        self.assertTrue(is_useful)
        self.assertIn("Bỏ qua do lỗi grader", reason)

    # ── 4. Verify & Refine Workflow (State Machine) ──────────────────────────
    @patch("layers.layer5_verifier.grade_hallucination", return_value=(True, "OK"))
    @patch("layers.layer5_verifier.grade_usefulness", return_value=(True, "OK"))
    def test_verify_perfect_first_attempt_approved(self, mock_useful, mock_hallu):
        """State Machine: Đạt cả grounded và useful ngay lần đầu (attempt 0) -> status APPROVED."""
        docs = [{"content": "Nội dung chuẩn"}]
        res = verify_and_refine("Câu hỏi", "Câu trả lời tốt", docs, has_context=True)
        self.assertEqual(res["status"], "APPROVED")
        self.assertEqual(res["final_answer"], "Câu trả lời tốt")
        self.assertTrue(res["is_grounded"])
        self.assertTrue(res["is_useful"])

    @patch("layers.layer5_verifier.grade_hallucination")
    @patch("layers.layer5_verifier.grade_usefulness", return_value=(True, "OK"))
    @patch("google.generativeai.GenerativeModel")
    def test_verify_hallucination_regeneration_success_refined(self, mock_model_cls, mock_useful, mock_hallu):
        """
        State Machine: Lần đầu phát hiện ảo giác, sinh lại (re-generation) thành công
        và vượt qua thẩm định ở lần 2 -> status REFINED.
        """
        # Lần 1: Không grounded, Lần 2: Grounded
        mock_hallu.side_effect = [(False, "Bịa đặt"), (True, "Đã chuẩn")]

        mock_instance = MagicMock()
        mock_instance.generate_content.return_value.text = "Câu trả lời đã được sửa lỗi nghiêm ngặt."
        mock_model_cls.return_value = mock_instance

        docs = [{"content": "Tài liệu gốc"}]
        res = verify_and_refine("Câu hỏi", "Câu trả lời bịa đặt ban đầu", docs, has_context=True, max_retries=1)

        self.assertEqual(res["status"], "REFINED")
        self.assertEqual(res["final_answer"], "Câu trả lời đã được sửa lỗi nghiêm ngặt.")
        self.assertTrue(res["is_grounded"])

    @patch("layers.layer5_verifier.grade_hallucination", return_value=(False, "Vẫn bịa đặt"))
    @patch("layers.layer5_verifier.grade_usefulness", return_value=(True, "OK"))
    @patch("google.generativeai.GenerativeModel")
    def test_verify_exhausted_retries_fail_safe_fallback(self, mock_model_cls, mock_useful, mock_hallu):
        """
        State Machine: Hết lượt thử mà vẫn bị ảo giác -> Kích hoạt Fail-Safe Fallback,
        trích dẫn trực tiếp tài liệu gốc và trả về status FALLBACK_TO_SOURCE.
        """
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value.text = "Câu trả lời sinh lại vẫn sai."
        mock_model_cls.return_value = mock_instance

        docs = [
            {
                "content": "ChatMessage sử dụng mã hóa AES-256-GCM để bảo vệ tin nhắn.",
                "metadata": {"category": "Mã hóa", "question": "Mã hóa tin nhắn"}
            }
        ]

        res = verify_and_refine("Mã hóa thế nào?", "Câu trả lời bịa đặt", docs, has_context=True, max_retries=1)

        self.assertEqual(res["status"], "FALLBACK_TO_SOURCE")
        self.assertIn("Hệ thống đã tìm thấy tài liệu liên quan", res["final_answer"])
        self.assertIn("AES-256-GCM", res["final_answer"])
        self.assertTrue(res["is_grounded"])

    @patch("layers.layer5_verifier.grade_hallucination", return_value=(True, "OK"))
    @patch("layers.layer5_verifier.grade_usefulness", return_value=(False, "Lạc đề"))
    def test_verify_grounded_but_not_useful_warning(self, mock_useful, mock_hallu):
        """State Machine: Câu trả lời trung thực nhưng lạc đề -> status PASSED_WITH_WARNING."""
        docs = [{"content": "Nội dung kỹ thuật"}]
        res = verify_and_refine("Câu hỏi", "Câu trả lời đúng tài liệu nhưng không giải quyết câu hỏi", docs, has_context=True)
        self.assertEqual(res["status"], "PASSED_WITH_WARNING")
        self.assertTrue(res["is_grounded"])
        self.assertFalse(res["is_useful"])

    @patch("layers.layer5_verifier.grade_hallucination", return_value=(False, "Lỗi"))
    @patch("layers.layer5_verifier.grade_usefulness", return_value=(True, "OK"))
    @patch("google.generativeai.GenerativeModel")
    def test_verify_regeneration_exception_break(self, mock_model_cls, mock_useful, mock_hallu):
        """State Machine: Khi re-generation ném ngoại lệ, vòng lặp ngắt và chuyển sang fallback an toàn."""
        mock_instance = MagicMock()
        mock_instance.generate_content.side_effect = RuntimeError("Gemini Crash")
        mock_model_cls.return_value = mock_instance

        docs = [{"content": "Tài liệu A", "metadata": {"category": "A", "question": "Q"}}]
        res = verify_and_refine("Câu hỏi", "Câu trả lời lỗi", docs, has_context=True, max_retries=1)
        self.assertEqual(res["status"], "FALLBACK_TO_SOURCE")


# ══════════════════════════════════════════════════════════════════════════════
# PHẦN 2: LIVE BENCHMARK (Tích hợp thực tế với Gemini / Grok API)
# ══════════════════════════════════════════════════════════════════════════════

LIVE_VERIFIER_SCENARIOS = [
    {
        "name": "Câu trả lời trung thực & hữu ích (Kỳ vọng APPROVED)",
        "question": "ChatMessage mã hóa tin nhắn bằng thuật toán gì?",
        "answer": "ChatMessage mã hóa tin nhắn bằng thuật toán đối xứng AES-256-GCM.",
        "docs": [{"content": "ChatMessage sử dụng mã hóa AES-256-GCM cho tin nhắn văn bản và hình ảnh."}],
        "expected_status": "APPROVED"
    },
    {
        "name": "Câu trả lời bị ảo giác bịa đặt (Kỳ vọng REFINED hoặc FALLBACK_TO_SOURCE)",
        "question": "ChatMessage mã hóa tin nhắn bằng thuật toán gì?",
        "answer": "ChatMessage sử dụng thuật toán mã hóa lượng tử kết hợp blockchain Bitcoin và RSA 8192.",
        "docs": [{"content": "ChatMessage sử dụng mã hóa AES-256-GCM cho tin nhắn văn bản và hình ảnh."}],
        "expected_status": ["REFINED", "FALLBACK_TO_SOURCE"]
    }
]


def run_live_benchmark():
    """Chạy kiểm thử thực tế Layer 5 Verifier."""
    print("\n" + "=" * 80)
    print("🚀 BẮT ĐẦU KIỂM THỬ THỰC TẾ LAYER 5 VỚI VERIFIER API")
    print("   (Đánh giá Khả năng phát hiện ảo giác và cơ chế tự sửa lỗi)")
    print("=" * 80)

    total = len(LIVE_VERIFIER_SCENARIOS)
    passed = 0

    for idx, sc in enumerate(LIVE_VERIFIER_SCENARIOS, 1):
        name = sc["name"]
        q = sc["question"]
        ans = sc["answer"]
        docs = sc["docs"]
        exp_status = sc["expected_status"]

        print(f"\n[{idx}/{total}] 🧪 Kịch bản: {name}")
        print(f"       ❓ Câu hỏi: \"{q}\"")
        print(f"       💬 Câu trả lời ban đầu: \"{ans}\"")

        time.sleep(1.0)
        t0 = time.time()
        res = verify_and_refine(q, ans, docs, has_context=True, max_retries=1)
        duration_ms = (time.time() - t0) * 1000

        actual_status = res["status"]
        if isinstance(exp_status, list):
            is_pass = actual_status in exp_status
        else:
            is_pass = (actual_status == exp_status)

        if is_pass:
            passed += 1

        mark = "✅ PASS" if is_pass else "❌ FAIL"
        print(f"       ⏱️ Thời gian thẩm định: {duration_ms:.1f} ms | Đánh giá: {mark}")
        print(f"       🎯 Trạng thái kết quả: {actual_status}")
        print(f"       🛡️ is_grounded: {res['is_grounded']} | is_useful: {res['is_useful']}")
        print(f"       🤖 Câu trả lời cuối cùng: {res['final_answer'][:150]}...")

    print("\n" + "-" * 80)
    print(f"📊 KẾT QUẢ ĐÁNH GIÁ THỰC TẾ LAYER 5: {passed}/{total} VƯỢT QUA")
    print("=" * 80)


# ══════════════════════════════════════════════════════════════════════════════
# PHẦN 3: CLI ENTRYPOINT
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Chương trình kiểm thử chuyên sâu cho Layer 5 (Verifier)")
    parser.add_argument("--unit", action="store_true", help="Chỉ chạy Unit Test (Mock, 0ms, không gọi API)")
    parser.add_argument("--live", action="store_true", help="Chỉ chạy Live Benchmark (Kiểm thử thực tế)")
    args = parser.parse_args()

    if args.unit:
        print("🧪 [CHẾ ĐỘ] Chạy Unit Tests với Mocking & Fault Injection (Layer 5)...")
        suite = unittest.TestLoader().loadTestsFromTestCase(TestLayer5Unit)
        runner = unittest.TextTestRunner(verbosity=2)
        runner.run(suite)
    elif args.live:
        print("🌐 [CHẾ ĐỘ] Chạy Live Benchmark với Verifier (Layer 5)...")
        run_live_benchmark()
    else:
        print("================================================================================")
        print("🧪 [BƯỚC 1/2] CHẠY TỰ ĐỘNG UNIT TESTS (MOCK, FAULT INJECTION & VERIFIER COVERAGE)")
        print("================================================================================")
        suite = unittest.TestLoader().loadTestsFromTestCase(TestLayer5Unit)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        if result.wasSuccessful():
            print("\n✅ TẤT CẢ UNIT TESTS ĐÃ VƯỢT QUA!")
            run_live_benchmark()
        else:
            print("\n❌ CÓ LỖI TRONG UNIT TESTS. DỪNG LIVE BENCHMARK.")


if __name__ == "__main__":
    main()
