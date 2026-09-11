"""
test_layer2.py — Suite Kiểm Thử Toàn Diện Cho Layer 2 (Query Rewriter / RAG Fusion)
==================================================================================
Áp dụng các kỹ thuật kiểm thử phần mềm tiêu chuẩn để bao phủ TOÀN BỘ các điều kiện & nhánh:
  1. Boundary Value Analysis (BVA) & Edge Cases:
     - Chuỗi rỗng, chuỗi chỉ chứa khoảng trắng, tab, newline.
     - Chuỗi siêu dài (> 2000 ký tự).
     - Chuỗi chứa ký tự đặc biệt, unicode, emoji.
     - Biến thiên tham số num_queries (1, 3, 5).
  2. Equivalence Partitioning (EP) - Xử lý định dạng phản hồi từ LLM:
     - Phản hồi JSON thuần (Clean JSON array).
     - Phản hồi bọc trong Markdown code block ```json ... ```.
     - Phản hồi bọc trong Markdown code block không có chữ json ``` ... ```.
     - Làm sạch khoảng trắng và dấu ngoặc kép/đơn bao quanh từng phần tử.
  3. Deduplication & Sanitization:
     - Loại bỏ câu hỏi trùng hoàn toàn với câu hỏi gốc.
     - Loại bỏ câu hỏi trùng với câu hỏi gốc nhưng khác chữ hoa/thường (Case-insensitive).
     - Loại bỏ các câu hỏi trùng lặp lẫn nhau do LLM sinh ra.
     - Loại bỏ phần tử rỗng hoặc chỉ có khoảng trắng trong mảng JSON.
     - Xử lý an toàn với các phần tử không phải chuỗi (số, null).
  4. Fault Injection & Negative Testing (Khả năng chịu lỗi & Fallback an toàn):
     - LLM ném ngoại lệ (Quota Exceeded 429, Connection Timeout, Network Error).
     - LLM trả về cú pháp JSON không hợp lệ (Syntax Error, Truncated JSON).
     - LLM trả về JSON Object / Dictionary thay vì JSON List (isinstance check).
     - Phản hồi LLM trả về None hoặc gây lỗi khi truy cập .text.
  5. Kiểm thử hàm tiện ích `rewrite_query`:
     - Trả về câu biến thể (queries[1]) khi sinh thành công (len > 1).
     - Fallback về câu gốc (queries[0]) khi input rỗng hoặc LLM gặp lỗi (len <= 1).
  6. Live Performance & Diversity Benchmark (Kiểm thử thực tế với Gemini API):
     - Đo lường độ trễ (latency), số lượng biến thể hợp lệ, tính đa dạng của câu hỏi.

Cách chạy:
  - Chạy toàn bộ (Unit Test + Live Benchmark):
      python rag_data/tests/test_layer2.py
  - Chỉ chạy Unit Test (Mock, nhanh, 0ms, không tốn quota API):
      python rag_data/tests/test_layer2.py --unit
  - Chỉ chạy Live Benchmark (Kiểm thử thực tế với Gemini):
      python rag_data/tests/test_layer2.py --live
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

from layers.layer2_query_rewriter import (
    generate_rag_fusion_queries,
    rewrite_query,
    SYSTEM_RAG_FUSION_PROMPT
)


# ══════════════════════════════════════════════════════════════════════════════
# PHẦN 1: UNIT TESTING WITH MOCKING & FAULT INJECTION (Cô lập, 100% Coverage)
# ══════════════════════════════════════════════════════════════════════════════

class TestLayer2Unit(unittest.TestCase):
    """
    Bộ Unit Test cô lập dùng mock để kiểm tra 100% các nhánh rẽ điều kiện (branch coverage),
    giá trị biên, cơ chế lọc trùng lặp và khả năng phục hồi lỗi (fault tolerance).
    """

    def setUp(self):
        self.patcher_grok = patch("layers.layer2_query_rewriter.is_grok_available", return_value=False)
        self.patcher_grok.start()

    def tearDown(self):
        self.patcher_grok.stop()

    # ── 1. Boundary Value Analysis & Edge Cases ─────────────────────────────
    def test_bva_empty_string(self):
        """BVA: Chuỗi rỗng phải trả về danh sách chứa chuỗi rỗng ngay lập tức, không gọi LLM."""
        with patch("google.generativeai.GenerativeModel") as mock_model_cls:
            result = generate_rag_fusion_queries("")
            self.assertEqual(result, [""])
            mock_model_cls.assert_not_called()

    def test_bva_whitespace_only(self):
        """BVA: Chuỗi chỉ chứa khoảng trắng/tab/newline phải xử lý như rỗng, không gọi LLM."""
        with patch("google.generativeai.GenerativeModel") as mock_model_cls:
            result = generate_rag_fusion_queries("   \n\t   ")
            self.assertEqual(result, [""])
            mock_model_cls.assert_not_called()

    @patch("google.generativeai.GenerativeModel")
    def test_bva_very_long_input(self, mock_model_cls):
        """BVA: Chuỗi câu hỏi siêu dài (> 2000 ký tự) không gây lỗi format prompt."""
        long_query = "Lỗi đăng nhập Google OAuth2 trong ChatMessageE2E " * 50
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value.text = '["Góc nhìn 1", "Góc nhìn 2"]'
        mock_model_cls.return_value = mock_instance

        result = generate_rag_fusion_queries(long_query)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], long_query.strip())
        self.assertIn("Góc nhìn 1", result)

    @patch("google.generativeai.GenerativeModel")
    def test_bva_special_characters_and_emojis(self, mock_model_cls):
        """BVA: Câu hỏi chứa emoji và ký tự đặc biệt được giữ nguyên toàn vẹn."""
        query = "🔐 Mã hóa E2EE bị lỗi: Key mismatch & handshake failed!? #123"
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value.text = '["Cơ chế sửa lỗi lệch khóa", "Quy trình bắt tay 4 lớp"]'
        mock_model_cls.return_value = mock_instance

        result = generate_rag_fusion_queries(query)
        self.assertEqual(result[0], query)
        self.assertEqual(len(result), 3)

    @patch("google.generativeai.GenerativeModel")
    def test_bva_num_queries_parameter(self, mock_model_cls):
        """BVA: Tham số num_queries được truyền chính xác vào prompt gửi cho LLM."""
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value.text = '["Query A", "Query B", "Query C", "Query D", "Query E"]'
        mock_model_cls.return_value = mock_instance

        generate_rag_fusion_queries("Bắt tay 4 lớp là gì?", num_queries=5)
        call_args = mock_instance.generate_content.call_args[0][0]
        self.assertIn("chính xác 5 câu truy vấn", call_args)

    # ── 2. Equivalence Partitioning: Định dạng phản hồi LLM ──────────────────
    @patch("google.generativeai.GenerativeModel")
    def test_ep_clean_json_array(self, mock_model_cls):
        """EP: LLM trả về chuỗi JSON mảng chuẩn không có markdown."""
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value.text = '["Nguyên nhân lỗi đăng nhập", "Cách cấp lại mã JWT"]'
        mock_model_cls.return_value = mock_instance

        result = generate_rag_fusion_queries("Lỗi đăng nhập")
        self.assertEqual(result, ["Lỗi đăng nhập", "Nguyên nhân lỗi đăng nhập", "Cách cấp lại mã JWT"])

    @patch("google.generativeai.GenerativeModel")
    def test_ep_markdown_code_block_with_json_tag(self, mock_model_cls):
        """EP: LLM bọc kết quả trong ```json ... ``` phải bóc tách đúng JSON."""
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value.text = """```json
[
  "Thuật toán mã hóa AES-256-GCM",
  "Trao đổi khóa ECDH trong E2EE"
]
```"""
        mock_model_cls.return_value = mock_instance

        result = generate_rag_fusion_queries("Mã hóa tin nhắn thế nào")
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], "Mã hóa tin nhắn thế nào")
        self.assertIn("Thuật toán mã hóa AES-256-GCM", result)
        self.assertIn("Trao đổi khóa ECDH trong E2EE", result)

    @patch("google.generativeai.GenerativeModel")
    def test_ep_markdown_code_block_without_tag(self, mock_model_cls):
        """EP: LLM bọc kết quả trong ``` ... ``` (không có chữ json) phải bóc tách đúng."""
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value.text = """```
["Bước 1 bắt tay 4 lớp", "Bước 2 khởi tạo phiên"]
```"""
        mock_model_cls.return_value = mock_instance

        result = generate_rag_fusion_queries("Bắt tay 4 lớp")
        self.assertEqual(result, ["Bắt tay 4 lớp", "Bước 1 bắt tay 4 lớp", "Bước 2 khởi tạo phiên"])

    @patch("google.generativeai.GenerativeModel")
    def test_ep_strip_spaces_and_quotes(self, mock_model_cls):
        """EP: Làm sạch khoảng trắng thừa và dấu nháy đơn/kép bao quanh phần tử."""
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value.text = '["  \'Câu truy vấn 1\'  ", "  \\"Câu truy vấn 2\\"  "]'
        mock_model_cls.return_value = mock_instance

        result = generate_rag_fusion_queries("Câu hỏi gốc")
        self.assertEqual(result, ["Câu hỏi gốc", "Câu truy vấn 1", "Câu truy vấn 2"])

    # ── 3. Deduplication & Sanitization ──────────────────────────────────────
    @patch("google.generativeai.GenerativeModel")
    def test_dedup_exact_match_with_original(self, mock_model_cls):
        """Dedup: Câu hỏi do LLM sinh ra trùng khớp hoàn toàn với câu hỏi gốc sẽ bị bỏ qua."""
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value.text = '["đăng nhập lỗi", "sửa lỗi đăng nhập google"]'
        mock_model_cls.return_value = mock_instance

        result = generate_rag_fusion_queries("đăng nhập lỗi")
        self.assertEqual(result, ["đăng nhập lỗi", "sửa lỗi đăng nhập google"])
        self.assertEqual(len(result), 2)

    @patch("google.generativeai.GenerativeModel")
    def test_dedup_case_insensitive_match_with_original(self, mock_model_cls):
        """Dedup: Câu hỏi do LLM sinh ra trùng với câu gốc nhưng khác hoa/thường (Case-insensitive) sẽ bị bỏ qua."""
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value.text = '["ĐĂNG NHẬP LỖI", "Nguyên nhân không đăng nhập được"]'
        mock_model_cls.return_value = mock_instance

        result = generate_rag_fusion_queries("đăng nhập lỗi")
        self.assertEqual(result, ["đăng nhập lỗi", "Nguyên nhân không đăng nhập được"])
        self.assertEqual(len(result), 2)

    @patch("google.generativeai.GenerativeModel")
    def test_dedup_duplicate_queries_among_generated(self, mock_model_cls):
        """Dedup: Loại bỏ các câu hỏi bị lặp lại trong danh sách do LLM trả về."""
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value.text = '["Biến thể A", "Biến thể A", "Biến thể B"]'
        mock_model_cls.return_value = mock_instance

        result = generate_rag_fusion_queries("Câu gốc")
        self.assertEqual(result, ["Câu gốc", "Biến thể A", "Biến thể B"])
        self.assertEqual(len(result), 3)

    @patch("google.generativeai.GenerativeModel")
    def test_sanitization_empty_or_whitespace_elements(self, mock_model_cls):
        """Sanitization: Bỏ qua các phần tử rỗng hoặc chỉ chứa khoảng trắng trong mảng JSON."""
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value.text = '["", "   ", "Câu hợp lệ 1", "  \'\'  ", "Câu hợp lệ 2"]'
        mock_model_cls.return_value = mock_instance

        result = generate_rag_fusion_queries("Câu gốc")
        self.assertEqual(result, ["Câu gốc", "Câu hợp lệ 1", "Câu hợp lệ 2"])

    @patch("google.generativeai.GenerativeModel")
    def test_sanitization_non_string_elements(self, mock_model_cls):
        """Sanitization: Xử lý an toàn nếu mảng JSON chứa phần tử số hoặc null."""
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value.text = '[123, null, "Biến thể hợp lệ"]'
        mock_model_cls.return_value = mock_instance

        result = generate_rag_fusion_queries("Câu gốc")
        self.assertIn("Biến thể hợp lệ", result)
        self.assertEqual(result[0], "Câu gốc")

    # ── 4. Fault Injection & Negative Testing (Resilience) ───────────────────
    @patch("google.generativeai.GenerativeModel")
    def test_fault_injection_llm_api_exception(self, mock_model_cls):
        """
        Fault Injection: Giả lập LLM ném ngoại lệ (Quota Exceeded 429 / Connection Error).
        Hệ thống PHẢI bắt lỗi an toàn và fallback trả về danh sách chứa câu hỏi gốc.
        """
        mock_instance = MagicMock()
        mock_instance.generate_content.side_effect = RuntimeError("ResourceExhausted: 429 Quota exceeded")
        mock_model_cls.return_value = mock_instance

        result = generate_rag_fusion_queries("Lỗi đăng nhập OAuth2")
        self.assertEqual(result, ["Lỗi đăng nhập OAuth2"])

    @patch("google.generativeai.GenerativeModel")
    def test_fault_injection_invalid_json_syntax(self, mock_model_cls):
        """Fault Injection: LLM trả về văn bản không phải JSON (JSONDecodeError)."""
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value.text = "Xin chào, đây là các câu hỏi tôi đề xuất: 1. Câu A 2. Câu B"
        mock_model_cls.return_value = mock_instance

        result = generate_rag_fusion_queries("Làm sao để chặn ai đó")
        self.assertEqual(result, ["Làm sao để chặn ai đó"])

    @patch("google.generativeai.GenerativeModel")
    def test_fault_injection_json_dict_instead_of_list(self, mock_model_cls):
        """Fault Injection: LLM trả về JSON Object thay vì JSON List (isinstance check fail)."""
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value.text = '{"queries": ["câu 1", "câu 2"]}'
        mock_model_cls.return_value = mock_instance

        result = generate_rag_fusion_queries("Bắt tay 4 lớp")
        self.assertEqual(result, ["Bắt tay 4 lớp"])

    @patch("google.generativeai.GenerativeModel")
    def test_fault_injection_truncated_json(self, mock_model_cls):
        """Fault Injection: LLM trả về JSON bị cắt ngắn giữa chừng (Token limit hit)."""
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value.text = '["Câu biến thể 1", "Câu biến thể 2'
        mock_model_cls.return_value = mock_instance

        result = generate_rag_fusion_queries("Mã hóa đầu cuối")
        self.assertEqual(result, ["Mã hóa đầu cuối"])

    # ── 5. Kiểm thử hàm tiện ích rewrite_query ───────────────────────────────
    @patch("layers.layer2_query_rewriter.generate_rag_fusion_queries")
    def test_rewrite_query_success_branch(self, mock_generate):
        """Hàm rewrite_query: Trả về queries[1] khi danh sách có nhiều hơn 1 câu hỏi."""
        mock_generate.return_value = ["câu gốc", "câu biến thể tiêu biểu"]

        rewritten = rewrite_query("câu gốc")
        self.assertEqual(rewritten, "câu biến thể tiêu biểu")
        mock_generate.assert_called_once_with("câu gốc", num_queries=2)

    @patch("layers.layer2_query_rewriter.generate_rag_fusion_queries")
    def test_rewrite_query_fallback_branch(self, mock_generate):
        """Hàm rewrite_query: Fallback về queries[0] khi danh sách chỉ có đúng 1 câu (do lỗi hoặc rỗng)."""
        mock_generate.return_value = ["câu gốc"]

        rewritten = rewrite_query("câu gốc")
        self.assertEqual(rewritten, "câu gốc")


# ══════════════════════════════════════════════════════════════════════════════
# PHẦN 2: LIVE PERFORMANCE & DIVERSITY BENCHMARK (Tích hợp thực tế với Gemini)
# ══════════════════════════════════════════════════════════════════════════════

LIVE_EVALUATION_DATASET = [
    {
        "query": "đăng nhập bị lỗi",
        "category": "Google OAuth2 & JWT",
        "description": "Kiểm thử mở rộng câu hỏi mơ hồ về lỗi đăng nhập"
    },
    {
        "query": "mã hóa tin nhắn thế nào",
        "category": "E2EE & ECDH & AES",
        "description": "Kiểm thử đa góc nhìn kiến trúc mã hóa đầu cuối"
    },
    {
        "query": "bắt tay 4 lớp là gì",
        "category": "4-Layer Handshake",
        "description": "Kiểm thử góc nhìn quy trình và cơ chế bắt tay bảo mật"
    },
    {
        "query": "làm sao để chặn một ai đó",
        "category": "Block & Session Revocation",
        "description": "Kiểm thử quy trình chặn và thu hồi phiên người dùng"
    },
    {
        "query": "gửi file ảnh dung lượng lớn bị hỏng",
        "category": "Multimedia Encryption",
        "description": "Kiểm thử sự cố mã hóa và truyền tải file/hình ảnh"
    },
]


def run_live_benchmark():
    """Chạy đánh giá thực tế với Gemini API để kiểm tra chất lượng sinh đa truy vấn RAG Fusion."""
    print("\n" + "=" * 80)
    print("🚀 BẮT ĐẦU KIỂM THỬ THỰC TẾ LAYER 2 VỚI GEMINI API")
    print("   (Đánh giá RAG Fusion Multi-Query, Độ trễ và Tính đa góc nhìn)")
    print("=" * 80)

    total = len(LIVE_EVALUATION_DATASET)
    passed = 0
    latencies = []

    for idx, item in enumerate(LIVE_EVALUATION_DATASET, 1):
        q = item["query"]
        category = item["category"]
        desc = item["description"]

        print(f"\n[{idx}/{total}] ❓ CÂU HỎI GỐC: \"{q}\"")
        print(f"       📂 Chủ đề: {category} | {desc}")

        time.sleep(1.0)

        t0 = time.time()
        queries = generate_rag_fusion_queries(q, num_queries=3)
        duration_ms = (time.time() - t0) * 1000
        latencies.append(duration_ms)

        is_list = isinstance(queries, list)
        has_min_queries = len(queries) >= 2
        starts_with_original = len(queries) > 0 and queries[0] == q
        all_unique = len(queries) == len(set(q_item.lower() for q_item in queries))

        is_pass = is_list and has_min_queries and starts_with_original and all_unique
        if is_pass:
            passed += 1

        mark = "✅ PASS" if is_pass else "❌ FAIL"
        print(f"       ⏱️ Thời gian phản hồi: {duration_ms:.1f} ms | Đánh giá: {mark}")
        print(f"       🚀 Danh sách truy vấn RAG Fusion ({len(queries)} biến thể):")
        for q_idx, sub_q in enumerate(queries, 1):
            tag = "GỐC" if q_idx == 1 else f"GÓC NHÌN {q_idx-1}"
            print(f"          {q_idx}. [{tag}]: \"{sub_q}\"")

        rewritten = rewrite_query(q)
        print(f"       🔄 [rewrite_query() tiêu biểu]: \"{rewritten}\"")

    print("\n" + "-" * 80)
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    success_rate = (passed / total) * 100

    print(f"📊 KẾT QUẢ ĐÁNH GIÁ THỰC TẾ LAYER 2:")
    print(f"   • Tổng số ca kiểm thử       : {total}")
    print(f"   • Số ca thành công          : {passed}/{total}")
    print(f"   • Tỷ lệ đạt chuẩn (Success) : {success_rate:.1f}%")
    print(f"   • Thời gian phản hồi TB     : {avg_latency:.2f} ms")
    print("=" * 80)


# ══════════════════════════════════════════════════════════════════════════════
# PHẦN 3: CLI ENTRYPOINT
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Chương trình kiểm thử chuyên sâu cho Layer 2 (Query Rewriter với RAG Fusion)"
    )
    parser.add_argument("--unit", action="store_true", help="Chỉ chạy Unit Test (Mock, 0ms, không gọi API)")
    parser.add_argument("--live", action="store_true", help="Chỉ chạy Live Benchmark (Kiểm thử thực tế với Gemini)")
    args = parser.parse_args()

    if args.unit:
        print("🧪 [CHẾ ĐỘ] Chạy Unit Tests với Mocking & Fault Injection (Layer 2)...")
        suite = unittest.TestLoader().loadTestsFromTestCase(TestLayer2Unit)
        runner = unittest.TextTestRunner(verbosity=2)
        runner.run(suite)
    elif args.live:
        print("🌐 [CHẾ ĐỘ] Chạy Live Benchmark với Gemini API (Layer 2)...")
        run_live_benchmark()
    else:
        print("================================================================================")
        print("🧪 [BƯỚC 1/2] CHẠY TỰ ĐỘNG UNIT TESTS (MOCK, FAULT INJECTION & BOUNDARY CASES)")
        print("================================================================================")
        suite = unittest.TestLoader().loadTestsFromTestCase(TestLayer2Unit)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        if result.wasSuccessful():
            print("\n✅ TẤT CẢ UNIT TESTS ĐÃ VƯỢT QUA!")
            run_live_benchmark()
        else:
            print("\n❌ CÓ LỖI TRONG UNIT TESTS. DỪNG LIVE BENCHMARK.")


if __name__ == "__main__":
    main()
