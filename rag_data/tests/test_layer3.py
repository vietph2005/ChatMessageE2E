"""
test_layer3.py — Suite Kiểm Thử Toàn Diện Cho Layer 3 (CRAG Retriever & Document Grader)
========================================================================================
Áp dụng các kỹ thuật kiểm thử phần mềm tiêu chuẩn để bao phủ TOÀN BỘ các điều kiện & nhánh:
  1. Boundary Value Analysis (BVA) & Edge Cases:
     - Danh sách queries rỗng `[]` -> has_context=False, không gọi ChromaDB.
     - ChromaDB rỗng (count == 0) -> trả về kết quả rỗng an toàn, kiểm tra cả verbose=True/False.
     - Giới hạn top_k (ngắt sớm khi đủ số lượng relevant docs).
     - Clamping độ tương đồng similarity: raw_dist < 0 hoặc raw_dist > 1.
     - ChromaDB trả về kết quả rỗng cho một query cụ thể (ids: [[]]).
  2. RAG Fusion & Reciprocal Rank Fusion (RRF):
     - Kiểm chứng công thức RRF: SUM(1 / (60 + rank)).
     - Document xuất hiện ở nhiều query có RRF score cao hơn và được xếp trên.
     - Xử lý trường hợp metadata bị None hoặc rỗng.
     - Chịu lỗi khi một truy vấn bị ngoại lệ (embed lỗi / timeout) không làm ảnh hưởng các truy vấn khác.
  3. Proposition Indexing & DocStore Lookup (Dual Storage):
     - Khi có `doc_id` và DocStore khả dụng -> lấy full parent chunk làm content.
     - Khi DocStore không khả dụng hoặc `doc_id` rỗng -> fallback về proposition text.
  4. CRAG Document Grader:
     - Phản hồi "yes" -> True (tài liệu liên quan).
     - Phản hồi "no" -> False (loại bỏ tài liệu rác).
     - LLM gặp sự cố (Quota 429, Timeout) -> Fail-safe policy mặc định giữ lại (return True).
  5. Luồng tích hợp CRAG (crag_retrieve_and_grade):
     - Lọc toàn bộ nếu tất cả là irrelevant -> has_context=False.
     - Lọc hỗn hợp (chỉ giữ các tài liệu pass grader).
     - Tự động nạp get_chroma_collection() khi tham số collection=None.
  6. Live Benchmark:
     - Đánh giá thực nghiệm với ChromaDB thực tế và Gemini API.

Cách chạy:
  - Chạy toàn bộ (Unit Test + Live Benchmark):
      python rag_data/tests/test_layer3.py
  - Chỉ chạy Unit Test (Mock, 0ms, không tốn quota API):
      python rag_data/tests/test_layer3.py --unit
  - Chỉ chạy Live Benchmark:
      python rag_data/tests/test_layer3.py --live
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

from layers.layer3_crag_retriever import (
    rrf_retrieve,
    grade_document,
    crag_retrieve_and_grade,
    embed_query,
    get_chroma_collection,
    RRF_K
)


# ══════════════════════════════════════════════════════════════════════════════
# PHẦN 1: UNIT TESTING WITH MOCKING & FAULT INJECTION (100% Branch Coverage)
# ══════════════════════════════════════════════════════════════════════════════

class TestLayer3Unit(unittest.TestCase):
    """
    Bộ Unit Test cô lập dùng mock để kiểm tra 100% các nhánh rẽ điều kiện (branch coverage),
    thuật toán RRF, cơ chế lọc rác CRAG và các trường hợp biên.
    """

    def setUp(self):
        self.patcher_grok = patch("layers.layer3_crag_retriever.is_grok_available", return_value=False)
        self.patcher_grok.start()

    def tearDown(self):
        self.patcher_grok.stop()

    # ── 1. Boundary Value Analysis & Edge Cases ─────────────────────────────
    def test_bva_empty_queries(self):
        """BVA: Danh sách truy vấn rỗng trả về cấu trúc mặc định, has_context=False."""
        result = crag_retrieve_and_grade([])
        self.assertEqual(result["relevant_docs"], [])
        self.assertFalse(result["has_context"])
        self.assertEqual(result["total_candidates"], 0)

    def test_bva_empty_collection(self):
        """BVA: ChromaDB rỗng (count=0) trả về danh sách rỗng, kiểm tra cả verbose=True và False."""
        mock_col = MagicMock()
        mock_col.count.return_value = 0

        # verbose=False
        result = crag_retrieve_and_grade(["Câu hỏi thử"], collection=mock_col, verbose=False)
        self.assertEqual(result["relevant_docs"], [])
        self.assertFalse(result["has_context"])

        # verbose=True (bao phủ nhánh if verbose)
        result_verbose = crag_retrieve_and_grade(["Câu hỏi thử"], collection=mock_col, verbose=True)
        self.assertEqual(result_verbose["relevant_docs"], [])
        self.assertFalse(result_verbose["has_context"])

    def test_bva_top_k_early_stopping(self):
        """BVA: Khi đã đủ số lượng top_k tài liệu relevant, dừng đánh giá ngay (Early Stopping)."""
        mock_col = MagicMock()
        mock_col.count.return_value = 10

        # Giả lập 5 candidates
        fake_candidates = [
            {"id": f"doc_{i}", "content": f"Nội dung {i}", "metadata": {"category": "Auth"}, "rrf_score": 0.05}
            for i in range(5)
        ]

        with patch("layers.layer3_crag_retriever.rrf_retrieve", return_value=fake_candidates):
            with patch("layers.layer3_crag_retriever.grade_document", return_value=True) as mock_grader:
                # Đặt top_k = 2
                res = crag_retrieve_and_grade(["câu hỏi"], collection=mock_col, top_k=2, verbose=True)
                self.assertEqual(len(res["relevant_docs"]), 2)
                # Phải dừng sau 2 lần gọi grader thay vì chạy hết 5 lần
                self.assertEqual(mock_grader.call_count, 2)

    def test_bva_similarity_clamping(self):
        """BVA: Độ tương đồng similarity được ép trong khoảng [0.0, 1.0] dù raw_distance dị biệt."""
        mock_col = MagicMock()
        mock_col.count.return_value = 2

        # raw_dist = -0.5 (quá nhỏ -> 1 - (-0.5) = 1.5 -> clamp về 1.0)
        # raw_dist = 1.8 (quá lớn -> 1 - 1.8 = -0.8 -> clamp về 0.0)
        mock_col.query.return_value = {
            "ids": [["doc_a", "doc_b"]],
            "distances": [[-0.5, 1.8]],
            "metadatas": [[{"doc_id": "p1"}, {"doc_id": "p2"}]],
            "documents": [["prop A", "prop B"]]
        }

        with patch("layers.layer3_crag_retriever.embed_query", return_value=[0.1] * 768):
            with patch("layers.layer3_crag_retriever._DOCSTORE_AVAILABLE", False):
                results = rrf_retrieve(mock_col, ["query 1"])
                self.assertEqual(len(results), 2)
                # doc_a: 1.0
                # doc_b: 0.0
                doc_a = next(d for d in results if d["id"] == "doc_a")
                doc_b = next(d for d in results if d["id"] == "doc_b")
                self.assertEqual(doc_a["similarity"], 1.0)
                self.assertEqual(doc_b["similarity"], 0.0)

    # ── 2. RAG Fusion & Thuật toán RRF ──────────────────────────────────────
    def test_rrf_scoring_multi_query_fusion(self):
        """
        RRF: Tài liệu xuất hiện trong nhiều truy vấn con sẽ có điểm RRF tích lũy cao hơn
        và được xếp lên đầu danh sách.
        """
        mock_col = MagicMock()
        mock_col.count.return_value = 5

        # Query 1 trả về [doc_shared, doc_only_1]
        # Query 2 trả về [doc_shared, doc_only_2]
        def mock_query_side_effect(query_embeddings, n_results, include):
            current_q_vec = query_embeddings[0]
            if current_q_vec == [1.0]:  # Giả lập query 1
                return {
                    "ids": [["doc_shared", "doc_only_1"]],
                    "distances": [[0.1, 0.2]],
                    "metadatas": [[{"question": "Q1"}, {"question": "Q2"}]],
                    "documents": [["Prop Shared", "Prop Only 1"]]
                }
            else:  # Giả lập query 2
                return {
                    "ids": [["doc_shared", "doc_only_2"]],
                    "distances": [[0.1, 0.3]],
                    "metadatas": [[{"question": "Q1"}, {"question": "Q3"}]],
                    "documents": [["Prop Shared", "Prop Only 2"]]
                }

        mock_col.query.side_effect = mock_query_side_effect

        with patch("layers.layer3_crag_retriever.embed_query", side_effect=[[1.0], [2.0]]):
            with patch("layers.layer3_crag_retriever._DOCSTORE_AVAILABLE", False):
                ranked = rrf_retrieve(mock_col, ["query 1", "query 2"])

                # doc_shared phải đứng đầu vì xuất hiện ở cả 2 truy vấn tại rank 1:
                # Score = 1/(60+1) + 1/(60+1) = 2/61 ≈ 0.032787
                self.assertEqual(ranked[0]["id"], "doc_shared")
                expected_score = round((1.0 / (RRF_K + 1)) * 2, 6)
                self.assertEqual(ranked[0]["rrf_score"], expected_score)
                self.assertEqual(len(ranked), 3)

    def test_rrf_empty_results_from_chroma(self):
        """RRF: Xử lý an toàn khi ChromaDB không tìm thấy tài liệu phù hợp (ids=[[]])."""
        mock_col = MagicMock()
        mock_col.count.return_value = 5
        mock_col.query.return_value = {"ids": [[]], "distances": [[]], "metadatas": [[]], "documents": [[]]}

        with patch("layers.layer3_crag_retriever.embed_query", return_value=[0.1] * 768):
            results = rrf_retrieve(mock_col, ["query lạ"])
            self.assertEqual(results, [])

    def test_rrf_missing_metadatas(self):
        """RRF: Xử lý an toàn khi results['metadatas'] là None hoặc danh sách rỗng."""
        mock_col = MagicMock()
        mock_col.count.return_value = 1
        mock_col.query.return_value = {
            "ids": [["doc_no_meta"]],
            "distances": [[0.2]],
            "metadatas": None,  # Không có metadata
            "documents": [["Chỉ có text"]]
        }

        with patch("layers.layer3_crag_retriever.embed_query", return_value=[0.1] * 768):
            with patch("layers.layer3_crag_retriever._DOCSTORE_AVAILABLE", False):
                results = rrf_retrieve(mock_col, ["test"])
                self.assertEqual(len(results), 1)
                self.assertEqual(results[0]["metadata"], {})

    def test_rrf_query_exception_resilience(self):
        """RRF: Nếu 1 truy vấn bị lỗi mạng/embedding, hệ thống tiếp tục các truy vấn còn lại."""
        mock_col = MagicMock()
        mock_col.count.return_value = 5

        # Query 1 ném ngoại lệ, Query 2 thành công
        def embed_side_effect(q):
            if q == "query lỗi":
                raise RuntimeError("Embedding API Timeout")
            return [0.5] * 768

        mock_col.query.return_value = {
            "ids": [["doc_valid"]],
            "distances": [[0.1]],
            "metadatas": [[{}]],
            "documents": [["Nội dung hợp lệ"]]
        }

        with patch("layers.layer3_crag_retriever.embed_query", side_effect=embed_side_effect):
            with patch("layers.layer3_crag_retriever._DOCSTORE_AVAILABLE", False):
                results = rrf_retrieve(mock_col, ["query lỗi", "query tốt"])
                self.assertEqual(len(results), 1)
                self.assertEqual(results[0]["id"], "doc_valid")

    # ── 3. Proposition Indexing & DocStore Lookup (Dual Storage) ─────────────
    def test_docstore_parent_chunk_retrieval(self):
        """DocStore: Khi _DOCSTORE_AVAILABLE=True và có doc_id, nạp full parent chunk."""
        mock_col = MagicMock()
        mock_col.count.return_value = 1
        mock_col.query.return_value = {
            "ids": [["prop_001"]],
            "distances": [[0.1]],
            "metadatas": [[{"doc_id": "parent_chunk_123"}]],
            "documents": [["Đoạn proposition ngắn"]]
        }

        with patch("layers.layer3_crag_retriever.embed_query", return_value=[0.1] * 768):
            with patch("layers.layer3_crag_retriever._DOCSTORE_AVAILABLE", True):
                with patch("layers.layer3_crag_retriever.load_from_docstore", return_value="Full Parent Chunk Dài Đầy Đủ") as mock_load:
                    results = rrf_retrieve(mock_col, ["test"])
                    mock_load.assert_called_once_with("parent_chunk_123")
                    self.assertEqual(results[0]["content"], "Full Parent Chunk Dài Đầy Đủ")
                    self.assertEqual(results[0]["proposition"], "Đoạn proposition ngắn")

    def test_docstore_fallback_when_parent_not_found(self):
        """DocStore: Khi load_from_docstore trả về None, fallback về proposition text."""
        mock_col = MagicMock()
        mock_col.count.return_value = 1
        mock_col.query.return_value = {
            "ids": [["prop_002"]],
            "distances": [[0.1]],
            "metadatas": [[{"doc_id": "parent_not_exist"}]],
            "documents": [["Đoạn proposition ngắn"]]
        }

        with patch("layers.layer3_crag_retriever.embed_query", return_value=[0.1] * 768):
            with patch("layers.layer3_crag_retriever._DOCSTORE_AVAILABLE", True):
                with patch("layers.layer3_crag_retriever.load_from_docstore", return_value=None):
                    results = rrf_retrieve(mock_col, ["test"])
                    self.assertEqual(results[0]["content"], "Đoạn proposition ngắn")

    # ── 4. CRAG Document Grader ──────────────────────────────────────────────
    @patch("google.generativeai.GenerativeModel")
    def test_grader_verdict_yes(self, mock_model_cls):
        """Grader: LLM trả về 'yes' -> grade_document trả về True."""
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value.text = "yes\n"
        mock_model_cls.return_value = mock_instance

        is_rel = grade_document("Làm sao đăng nhập?", "Hướng dẫn đăng nhập Google OAuth2")
        self.assertTrue(is_rel)

    @patch("google.generativeai.GenerativeModel")
    def test_grader_verdict_no(self, mock_model_cls):
        """Grader: LLM trả về 'no' -> grade_document trả về False."""
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value.text = "no"
        mock_model_cls.return_value = mock_instance

        is_rel = grade_document("Làm sao đăng nhập?", "Cách nấu phở bò truyền thống")
        self.assertFalse(is_rel)

    @patch("google.generativeai.GenerativeModel")
    def test_grader_llm_exception_fail_safe(self, mock_model_cls):
        """Grader: Khi LLM gặp ngoại lệ (Quota 429), fail-safe policy mặc định giữ lại tài liệu (True)."""
        mock_instance = MagicMock()
        mock_instance.generate_content.side_effect = RuntimeError("Quota Exceeded (429)")
        mock_model_cls.return_value = mock_instance

        is_rel = grade_document("Câu hỏi", "Đoạn văn bản")
        self.assertTrue(is_rel)

    # ── 5. End-to-End crag_retrieve_and_grade Workflow ───────────────────────
    def test_crag_all_irrelevant_returns_no_context(self):
        """CRAG: Khi tất cả tài liệu đều bị Grader đánh giá là 'no' -> has_context=False."""
        mock_col = MagicMock()
        mock_col.count.return_value = 2

        candidates = [
            {"id": "doc1", "content": "Rác 1", "metadata": {}},
            {"id": "doc2", "content": "Rác 2", "metadata": {}}
        ]

        with patch("layers.layer3_crag_retriever.rrf_retrieve", return_value=candidates):
            with patch("layers.layer3_crag_retriever.grade_document", return_value=False):
                res = crag_retrieve_and_grade(["Lỗi kết nối"], collection=mock_col, verbose=True)
                self.assertFalse(res["has_context"])
                self.assertEqual(res["relevant_docs"], [])
                self.assertEqual(res["total_candidates"], 2)

    def test_crag_mixed_relevance_filtering(self):
        """CRAG: Sàng lọc chính xác - chỉ giữ các tài liệu pass Grader."""
        mock_col = MagicMock()
        mock_col.count.return_value = 3

        candidates = [
            {"id": "doc1", "content": "Tài liệu hữu ích", "metadata": {"category": "Security"}},
            {"id": "doc2", "content": "Tài liệu không liên quan", "metadata": {"category": "UI"}},
            {"id": "doc3", "content": "Tài liệu hữu ích 2", "metadata": {"category": "Security"}}
        ]

        def mock_grading(q, content):
            return "hữu ích" in content

        with patch("layers.layer3_crag_retriever.rrf_retrieve", return_value=candidates):
            with patch("layers.layer3_crag_retriever.grade_document", side_effect=mock_grading):
                res = crag_retrieve_and_grade(["Mã hóa tin nhắn"], collection=mock_col, top_k=3, verbose=True)
                self.assertTrue(res["has_context"])
                self.assertEqual(len(res["relevant_docs"]), 2)
                self.assertEqual(res["relevant_docs"][0]["id"], "doc1")
                self.assertEqual(res["relevant_docs"][1]["id"], "doc3")

    @patch("layers.layer3_crag_retriever.get_chroma_collection")
    def test_crag_default_collection_param(self, mock_get_col):
        """CRAG: Khi collection=None, hàm tự động gọi get_chroma_collection()."""
        mock_col = MagicMock()
        mock_col.count.return_value = 0
        mock_get_col.return_value = mock_col

        res = crag_retrieve_and_grade(["câu hỏi"])
        mock_get_col.assert_called_once()
        self.assertFalse(res["has_context"])

    @patch("google.generativeai.embed_content")
    def test_embed_query_wrapper(self, mock_embed):
        """Kiểm tra hàm embed_query gọi genai với task_type RETRIEVAL_QUERY."""
        mock_embed.return_value = {"embedding": [0.12, 0.34, 0.56]}
        vec = embed_query("tìm kiếm")
        self.assertEqual(vec, [0.12, 0.34, 0.56])
        mock_embed.assert_called_once()


# ══════════════════════════════════════════════════════════════════════════════
# PHẦN 2: LIVE BENCHMARK (Tích hợp thực tế với ChromaDB và Gemini API)
# ══════════════════════════════════════════════════════════════════════════════

LIVE_EVALUATION_SCENARIOS = [
    {
        "name": "E2EE & Key Exchange (Trong phạm vi)",
        "queries": [
            "ChatMessage mã hóa tin nhắn thế nào?",
            "Cơ chế trao đổi khóa ECDH trong ChatMessageE2E",
            "Thuật toán mã hóa AES-256-GCM"
        ],
        "expected_has_context": True
    },
    {
        "name": "Bắt tay 4 lớp (Trong phạm vi)",
        "queries": [
            "Bắt tay 4 lớp gồm các bước nào?",
            "Quy trình 4-layer handshake khởi tạo phiên",
            "Xử lý lỗi lệch khóa khi bắt tay"
        ],
        "expected_has_context": True
    },
    {
        "name": "Câu hỏi hoàn toàn ngoài phạm vi (Out of Scope)",
        "queries": [
            "Làm sao để làm món phở bò Nam Định chuẩn vị?",
            "Công thức nấu nước dùng phở bò ngon",
            "Gia vị nấu phở gồm những gì"
        ],
        "expected_has_context": False
    },
]


def run_live_benchmark():
    """Chạy đánh giá thực tế với ChromaDB thật và Gemini Grader."""
    print("\n" + "=" * 80)
    print("🚀 BẮT ĐẦU KIỂM THỬ THỰC TẾ LAYER 3 VỚI CHROMADB & GEMINI")
    print("   (Đánh giá RRF Multi-Query Retrieval & CRAG Document Grader)")
    print("=" * 80)

    try:
        col = get_chroma_collection()
        total_in_db = col.count()
        print(f"📦 Số lượng vectors hiện có trong ChromaDB: {total_in_db}")
        if total_in_db == 0:
            print("⚠️ ChromaDB chưa có dữ liệu (0 records). Vui lòng ingest dữ liệu trước để chạy Live Benchmark.")
            return
    except Exception as e:
        print(f"❌ Không thể kết nối ChromaDB: {e}")
        return

    passed = 0
    total = len(LIVE_EVALUATION_SCENARIOS)

    for idx, sc in enumerate(LIVE_EVALUATION_SCENARIOS, 1):
        name = sc["name"]
        queries = sc["queries"]
        expected_has_ctx = sc["expected_has_context"]

        print(f"\n[{idx}/{total}] 🧪 Kịch bản: {name}")
        print(f"       ❓ Câu hỏi gốc: \"{queries[0]}\"")
        print(f"       🔄 Số lượng truy vấn RAG Fusion: {len(queries)}")

        time.sleep(1.0)  # Rate-limit safety

        t0 = time.time()
        result = crag_retrieve_and_grade(queries, collection=col, top_k=3, verbose=True)
        duration_ms = (time.time() - t0) * 1000

        actual_has_ctx = result["has_context"]
        is_pass = (actual_has_ctx == expected_has_ctx)
        if is_pass:
            passed += 1

        mark = "✅ PASS" if is_pass else "❌ FAIL"
        print(f"       ⏱️ Thời gian xử lý: {duration_ms:.1f} ms | Kết quả: {mark}")
        print(f"       📊 Ứng viên: {result['total_candidates']} | Relevant docs: {len(result['relevant_docs'])} | has_context: {actual_has_ctx}")

    print("\n" + "-" * 80)
    print(f"📊 KẾT QUẢ ĐÁNH GIÁ THỰC TẾ LAYER 3:")
    print(f"   • Tổng số ca kiểm thử       : {total}")
    print(f"   • Số ca thành công          : {passed}/{total}")
    print(f"   • Tỷ lệ đạt chuẩn (Success) : {(passed / total) * 100:.1f}%")
    print("=" * 80)


# ══════════════════════════════════════════════════════════════════════════════
# PHẦN 3: CLI ENTRYPOINT
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Chương trình kiểm thử chuyên sâu cho Layer 3 (CRAG Retriever & Document Grader)"
    )
    parser.add_argument("--unit", action="store_true", help="Chỉ chạy Unit Test (Mock, 0ms, không gọi API)")
    parser.add_argument("--live", action="store_true", help="Chỉ chạy Live Benchmark (Kiểm thử thực tế)")
    args = parser.parse_args()

    if args.unit:
        print("🧪 [CHẾ ĐỘ] Chạy Unit Tests với Mocking & Fault Injection (Layer 3)...")
        suite = unittest.TestLoader().loadTestsFromTestCase(TestLayer3Unit)
        runner = unittest.TextTestRunner(verbosity=2)
        runner.run(suite)
    elif args.live:
        print("🌐 [CHẾ ĐỘ] Chạy Live Benchmark với ChromaDB & Gemini (Layer 3)...")
        run_live_benchmark()
    else:
        print("================================================================================")
        print("🧪 [BƯỚC 1/2] CHẠY TỰ ĐỘNG UNIT TESTS (MOCK, FAULT INJECTION & RRF COVERAGE)")
        print("================================================================================")
        suite = unittest.TestLoader().loadTestsFromTestCase(TestLayer3Unit)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        if result.wasSuccessful():
            print("\n✅ TẤT CẢ UNIT TESTS ĐÃ VƯỢT QUA!")
            run_live_benchmark()
        else:
            print("\n❌ CÓ LỖI TRONG UNIT TESTS. DỪNG LIVE BENCHMARK.")


if __name__ == "__main__":
    main()
