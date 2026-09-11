"""
test_layer1.py — Suite Kiểm Thử Toàn Diện Cho Layer 1 (Intent Classifier)
========================================================================
Áp dụng các kỹ thuật kiểm thử phần mềm tiêu chuẩn:
  1. Boundary Value Analysis (BVA) & Edge Cases: Chuỗi rỗng, khoảng trắng, ký tự đặc biệt, câu siêu dài.
  2. Equivalence Partitioning (EP): Phân vùng tương đương (Fast Path Small-talk, LLM Small-talk, App Question).
  3. Fault Injection & Negative Testing: Giả lập lỗi API / Network timeout để kiểm tra cơ chế Fallback an toàn.
  4. Unit Testing with Mocking: Kiểm thử cô lập 100% logic không phụ thuộc mạng hay quota API.
  5. Live Performance & Accuracy Benchmark: Đánh giá độ trễ (latency) và độ chính xác (accuracy) trên tập dữ liệu thực tế.

Cách chạy:
  - Chạy toàn bộ (Unit Test + Live Benchmark):
      python rag_data/tests/test_layer1.py
  - Chỉ chạy Unit Test (Mock, nhanh, 0ms, không tốn quota API):
      python rag_data/tests/test_layer1.py --unit
  - Chỉ chạy Live Benchmark (Kiểm thử thực tế với Gemini):
      python rag_data/tests/test_layer1.py --live
"""

import sys
import time
import argparse
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Đảm bảo import được module từ rag_data
CURRENT_DIR = Path(__file__).resolve().parent
RAG_DATA_DIR = CURRENT_DIR.parent
if str(RAG_DATA_DIR) not in sys.path:
    sys.path.insert(0, str(RAG_DATA_DIR))

from layers.layer1_intent_classifier import (
    classify_intent,
    is_obvious_small_talk,
    _generate_direct_reply,
    FAST_SMALL_TALK_KEYWORDS
)


# ══════════════════════════════════════════════════════════════════════════════
# PHẦN 1: UNIT TESTING WITH MOCKING & FAULT INJECTION (Cô lập, không tốn quota)
# ══════════════════════════════════════════════════════════════════════════════

class TestLayer1Unit(unittest.TestCase):
    """
    Bộ Unit Test cô lập dùng mock để kiểm tra logic rẽ nhánh,
    giá trị biên và khả năng chịu lỗi (fault tolerance).
    """

    def setUp(self):
        self.patcher_grok = patch("layers.layer1_intent_classifier.is_grok_available", return_value=False)
        self.patcher_grok.start()

    def tearDown(self):
        self.patcher_grok.stop()

    # ── 1. Boundary Value Analysis & Edge Cases ─────────────────────────────
    def test_bva_empty_string(self):
        """BVA: Chuỗi rỗng phải được coi là small_talk và trả lời mặc định, không gọi LLM."""
        result = classify_intent("")
        self.assertEqual(result["intent"], "small_talk")
        self.assertTrue(result["is_small_talk"])
        self.assertIsNotNone(result["direct_reply"])

    def test_bva_whitespace_only(self):
        """BVA: Chuỗi chỉ có khoảng trắng phải được xử lý như chuỗi rỗng."""
        result = classify_intent("     \n\t   ")
        self.assertEqual(result["intent"], "small_talk")
        self.assertTrue(result["is_small_talk"])
        self.assertIsNotNone(result["direct_reply"])

    def test_bva_very_long_input(self):
        """BVA: Chuỗi siêu dài (> 2000 ký tự) không làm crash bộ phân loại."""
        long_text = "Tại sao ứng dụng lỗi? " * 100
        with patch("google.generativeai.GenerativeModel") as mock_model_cls:
            mock_instance = MagicMock()
            mock_instance.generate_content.return_value.text = "app_question"
            mock_model_cls.return_value = mock_instance

            result = classify_intent(long_text)
            self.assertEqual(result["intent"], "app_question")
            self.assertFalse(result["is_small_talk"])

    # ── 2. Equivalence Partitioning: Fast Path (Rule-based) ─────────────────
    def test_ep_fast_path_exact_keywords(self):
        """EP: Các từ khóa trong FAST_SMALL_TALK_KEYWORDS phải đi qua Fast Path (0ms, không gọi LLM)."""
        sample_keywords = ["xin chào", "hello", "cảm ơn", "tạm biệt", "bạn là ai"]
        for kw in sample_keywords:
            with self.subTest(keyword=kw):
                self.assertTrue(
                    is_obvious_small_talk(kw),
                    f"Từ khóa '{kw}' phải được nhận diện là obvious small talk"
                )

    def test_ep_fast_path_case_insensitivity(self):
        """EP: Fast Path phải không phân biệt hoa thường (Case-insensitive)."""
        variants = ["XIN CHÀO", "Hello", "CẢM ƠN", "tẠm BiỆt"]
        for v in variants:
            with self.subTest(variant=v):
                self.assertTrue(is_obvious_small_talk(v))

    # ── 3. Equivalence Partitioning: LLM Path (Mocked) ──────────────────────
    @patch("google.generativeai.GenerativeModel")
    def test_ep_llm_classified_as_small_talk(self, mock_model_cls):
        """EP: Khi LLM phán đoán 'small_talk', hệ thống phải trả lời trực tiếp."""
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value.text = "small_talk"
        mock_model_cls.return_value = mock_instance

        # Mock reply generator
        with patch("layers.layer1_intent_classifier._generate_direct_reply", return_value="Chào bạn nha!"):
            result = classify_intent("Hôm nay thời tiết đẹp quá nhỉ")
            self.assertEqual(result["intent"], "small_talk")
            self.assertTrue(result["is_small_talk"])
            self.assertEqual(result["direct_reply"], "Chào bạn nha!")

    @patch("google.generativeai.GenerativeModel")
    def test_ep_llm_classified_as_app_question(self, mock_model_cls):
        """EP: Khi LLM phán đoán 'app_question', hệ thống chuyển tiếp sang RAG Layer 2."""
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value.text = "app_question"
        mock_model_cls.return_value = mock_instance

        result = classify_intent("Mã hóa E2EE trong ChatMessage hoạt động thế nào?")
        self.assertEqual(result["intent"], "app_question")
        self.assertFalse(result["is_small_talk"])
        self.assertIsNone(result["direct_reply"])

    # ── 4. Fault Injection & Resilience Testing ─────────────────────────────
    @patch("google.generativeai.GenerativeModel")
    def test_fault_injection_llm_exception_fallback(self, mock_model_cls):
        """
        Fault Injection: Giả lập LLM ném ngoại lệ (Quota Exceeded / Connection Error).
        Hệ thống PHẢI fallback an toàn về 'app_question' để không làm rơi câu hỏi của user vào RAG.
        """
        mock_instance = MagicMock()
        mock_instance.generate_content.side_effect = RuntimeError("API Quota Exceeded (429)")
        mock_model_cls.return_value = mock_instance

        result = classify_intent("Tôi không đăng nhập được")
        # Phải fallback sang app_question thay vì sập
        self.assertEqual(result["intent"], "app_question")
        self.assertFalse(result["is_small_talk"])
        self.assertIsNone(result["direct_reply"])

    @patch("google.generativeai.GenerativeModel")
    def test_direct_reply_fallback_on_error(self, mock_model_cls):
        """Kiểm tra hàm _generate_direct_reply fallback câu thoại mặc định khi LLM gặp sự cố."""
        mock_instance = MagicMock()
        mock_instance.generate_content.side_effect = Exception("Model timeout")
        mock_model_cls.return_value = mock_instance

        reply = _generate_direct_reply("Chào bạn")
        self.assertIn("ChatMessage", reply)


# ══════════════════════════════════════════════════════════════════════════════
# PHẦN 2: LIVE PERFORMANCE & ACCURACY BENCHMARK (Tích hợp thực tế với Gemini)
# ══════════════════════════════════════════════════════════════════════════════

LIVE_EVALUATION_DATASET = [
    {"query": "Xin chào", "expected": "small_talk", "type": "Fast-Path SmallTalk"},
    {"query": "Cảm ơn bạn", "expected": "small_talk", "type": "Fast-Path SmallTalk"},
    {"query": "Tạm biệt", "expected": "small_talk", "type": "Fast-Path SmallTalk"},
    {"query": "hello", "expected": "small_talk", "type": "Fast-Path SmallTalk"},
    {"query": "Hôm nay trời có mưa không bạn?", "expected": "small_talk", "type": "Semantic SmallTalk"},
    {"query": "Bạn tên gì và bao nhiêu tuổi?", "expected": "small_talk", "type": "Semantic SmallTalk"},
    {"query": "Kể cho tôi một câu chuyện cười đi", "expected": "small_talk", "type": "Semantic SmallTalk"},
    {"query": "Bạn có người yêu chưa?", "expected": "small_talk", "type": "Semantic SmallTalk"},
    {"query": "Làm sao để đăng nhập bằng tài khoản Google?", "expected": "app_question", "type": "App Feature"},
    {"query": "ChatMessage mã hóa tin nhắn bằng thuật toán gì?", "expected": "app_question", "type": "Security & E2EE"},
    {"query": "Bắt tay 4 lớp là gì và gồm những bước nào?", "expected": "app_question", "type": "Architecture"},
    {"query": "Tôi bị lỗi không gửi được ảnh dung lượng lớn", "expected": "app_question", "type": "Troubleshooting"},
    {"query": "Cách xóa tin nhắn và thu hồi tin nhắn", "expected": "app_question", "type": "App Feature"},
    {"query": "", "expected": "small_talk", "type": "Edge Case (Empty)"},
]


def run_live_benchmark():
    """Chạy đánh giá thực tế với Gemini API để đo lường Độ chính xác và Độ trễ."""
    print("\n" + "=" * 80)
    print("🚀 BẮT ĐẦU KIỂM THỬ THỰC TẾ LAYER 1 VỚI GEMINI API")
    print("   (Đánh giá Accuracy, Phân loại Intent và Thời gian phản hồi)")
    print("=" * 80)

    total = len(LIVE_EVALUATION_DATASET)
    passed = 0
    latencies = []
    fast_path_latencies = []
    llm_path_latencies = []

    print(f"\n{'STT':<4} | {'Loại Test':<22} | {'Kỳ vọng':<12} | {'Kết quả':<12} | {'Thời gian':<10} | {'Đánh giá'}")
    print("-" * 80)

    for idx, item in enumerate(LIVE_EVALUATION_DATASET, 1):
        q = item["query"]
        expected = item["expected"]
        test_type = item["type"]

        if not ("Fast-Path" in test_type or test_type.startswith("Edge Case")):
            time.sleep(1.0)

        t0 = time.time()
        res = classify_intent(q)
        duration_ms = (time.time() - t0) * 1000

        actual = res["intent"]
        is_pass = (actual == expected)
        if is_pass:
            passed += 1

        latencies.append(duration_ms)
        if "Fast-Path" in test_type or test_type.startswith("Edge Case"):
            fast_path_latencies.append(duration_ms)
        else:
            llm_path_latencies.append(duration_ms)

        mark = "✅ PASS" if is_pass else "❌ FAIL"
        display_q = f"\"{q[:25]}...\"" if len(q) > 25 else (f"\"{q}\"" if q else "\"<rỗng>\"")
        print(f"{idx:<4} | {test_type:<22} | {expected:<12} | {actual:<12} | {duration_ms:>7.1f}ms | {mark}")
        if not is_pass:
            print(f"     ⚠️ Chi tiết câu hỏi: {q}")
        elif res.get("direct_reply"):
            print(f"     💬 Trả lời trực tiếp: {res['direct_reply'][:60]}...")

    print("-" * 80)
    accuracy = (passed / total) * 100
    avg_total = sum(latencies) / len(latencies) if latencies else 0
    avg_fast = sum(fast_path_latencies) / len(fast_path_latencies) if fast_path_latencies else 0
    avg_llm = sum(llm_path_latencies) / len(llm_path_latencies) if llm_path_latencies else 0

    print(f"📊 KẾT QUẢ ĐÁNH GIÁ:")
    print(f"   • Tổng số ca kiểm thử    : {total}")
    print(f"   • Số ca thành công       : {passed}/{total}")
    print(f"   • Độ chính xác (Accuracy): {accuracy:.1f}%")
    print(f"   • Độ trễ Fast Path (TB)  : {avg_fast:.2f} ms")
    print(f"   • Độ trễ LLM Path (TB)   : {avg_llm:.2f} ms")
    print(f"   • Độ trễ trung bình tổng : {avg_total:.2f} ms")
    print("=" * 80)


# ══════════════════════════════════════════════════════════════════════════════
# PHẦN 3: CLI ENTRYPOINT
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Chương trình kiểm thử chuyên sâu cho Layer 1 (Intent Classifier)")
    parser.add_argument("--unit", action="store_true", help="Chỉ chạy Unit Test (Mock, 0ms, không gọi API)")
    parser.add_argument("--live", action="store_true", help="Chỉ chạy Live Benchmark (Kiểm thử thực tế với Gemini)")
    args = parser.parse_args()

    if args.unit:
        print("🧪 [CHẾ ĐỘ] Chạy Unit Tests với Mocking & Fault Injection (Layer 1)...")
        suite = unittest.TestLoader().loadTestsFromTestCase(TestLayer1Unit)
        runner = unittest.TextTestRunner(verbosity=2)
        runner.run(suite)
    elif args.live:
        print("🌐 [CHẾ ĐỘ] Chạy Live Benchmark với Gemini API (Layer 1)...")
        run_live_benchmark()
    else:
        print("================================================================================")
        print("🧪 [BƯỚC 1/2] CHẠY TỰ ĐỘNG UNIT TESTS (MOCK, FAULT INJECTION & BOUNDARY CASES)")
        print("================================================================================")
        suite = unittest.TestLoader().loadTestsFromTestCase(TestLayer1Unit)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        if result.wasSuccessful():
            print("\n✅ TẤT CẢ UNIT TESTS ĐÃ VƯỢT QUA!")
            run_live_benchmark()
        else:
            print("\n❌ CÓ LỖI TRONG UNIT TESTS. DỪNG LIVE BENCHMARK.")


if __name__ == "__main__":
    main()
