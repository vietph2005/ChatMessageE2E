"""
Layer 3 — CRAG Retriever (Reciprocal Rank Fusion + Document Grader)
===================================================================
Mục đích:
  1. RAG FUSION (Reciprocal Rank Fusion - RRF):
     - Nhận danh sách đa truy vấn từ Layer 2: [câu gốc, biến thể 1, biến thể 2, ...].
     - Truy vấn ChromaDB song song cho từng câu hỏi để lấy các ứng viên tiềm năng.
     - Áp dụng công thức RRF: RRF_Score(doc) = SUM( 1 / (60 + rank(doc, query)) )
       để sắp xếp các chunk tài liệu xuất hiện nhiều nhất ở vị trí cao.

  2. CRAG DOCUMENT GRADER (Yan et al. 2024):
     - Vector Search luôn trả về Top-K dù tài liệu có thể hoàn toàn vô nghĩa đối với câu hỏi.
     - LLM Grader (nhanh, rẻ) kiểm tra từng chunk: "Tài liệu này có liên quan và giúp ích
       để trả lời câu hỏi không?" (yes/no).
     - Loại bỏ toàn bộ chunk rác (irrelevant), chỉ giữ lại chunk sạch (relevant).
     - Xác định cờ has_context:
         + True : Tìm thấy tài liệu liên quan -> Chuyển sang Layer 4 (Generator).
         + False: Không có tài liệu nào phù hợp -> Báo ngoài phạm vi, KHÔNG bịa đặt.
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple
from collections import defaultdict

# Đảm bảo import được config từ thư mục cha rag_data
CURRENT_DIR = Path(__file__).resolve().parent
PARENT_DIR = CURRENT_DIR.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

from config import init_gemini, FAST_MODEL_NAME, EMBEDDING_MODEL_NAME, CHROMA_DB_DIR, COLLECTION_NAME, is_grok_available, call_grok_chat
import google.generativeai as genai
import chromadb

# Import DocStore helper tu Proposition Indexer
# De tra cuu full parent chunk theo doc_id sau khi RRF tim duoc proposition
try:
    from proposition_indexer import load_from_docstore
    _DOCSTORE_AVAILABLE = True
except ImportError:
    _DOCSTORE_AVAILABLE = False

# Khởi tạo Gemini
init_gemini()

# Hằng số chuẩn cho thuật toán Reciprocal Rank Fusion
RRF_K = 60


def get_chroma_collection():
    """Lấy hoặc khởi tạo kết nối Persistent ChromaDB."""
    CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )


def embed_query(query: str) -> List[float]:
    """Sinh vector embedding cho câu truy vấn bằng text-embedding-004."""
    result = genai.embed_content(
        model=EMBEDDING_MODEL_NAME,
        content=query,
        task_type="RETRIEVAL_QUERY",
    )
    return result["embedding"]


# ════════════════════════════════════════════════════════════════════
# 1. RAG FUSION: Multi-Query Search & Reciprocal Rank Fusion (RRF)
# ════════════════════════════════════════════════════════════════════
def rrf_retrieve(collection, queries: List[str], top_candidates_per_query: int = 4) -> List[Dict[str, Any]]:
    """
    Tìm kiếm song song cho nhiều truy vấn và kết hợp thứ hạng bằng thuật toán RRF.

    Args:
        collection: ChromaDB Collection.
        queries (List[str]): Danh sách câu hỏi từ Layer 2.
        top_candidates_per_query (int): Số lượng kết quả lấy từ mỗi câu hỏi.

    Returns:
        List[Dict[str, Any]]: Danh sách các documents duy nhất đã được xếp hạng lại theo RRF score.
    """
    total_docs = collection.count()
    if total_docs == 0:
        return []

    fetch_k = min(top_candidates_per_query, total_docs)
    doc_lookup: Dict[str, Dict[str, Any]] = {}
    rrf_scores: Dict[str, float] = defaultdict(float)

    for q in queries:
        try:
            q_vec = embed_query(q)
            results = collection.query(
                query_embeddings=[q_vec],
                n_results=fetch_k,
                include=["documents", "metadatas", "distances"]
            )

            if results["ids"] and results["ids"][0]:
                for rank, doc_id in enumerate(results["ids"][0], start=1):
                    # Công thức Reciprocal Rank Fusion
                    rrf_scores[doc_id] += 1.0 / (RRF_K + rank)

                    if doc_id not in doc_lookup:
                        raw_dist = results["distances"][0][rank - 1]
                        sim = max(0.0, min(1.0, 1.0 - raw_dist))
                        meta = results["metadatas"][0][rank - 1] if results["metadatas"] else {}
                        proposition_text = results["documents"][0][rank - 1]

                        # ── Proposition Indexing: Dual Storage Lookup ──────────────
                        # ChromaDB luu proposition ngan -> lay doc_id -> tra DocStore
                        # -> lay full parent chunk de CRAG Grader va Generator co du ngu canh
                        parent_content = None
                        if _DOCSTORE_AVAILABLE:
                            chunk_doc_id = meta.get("doc_id")
                            if chunk_doc_id:
                                parent_content = load_from_docstore(chunk_doc_id)

                        doc_lookup[doc_id] = {
                            "id": doc_id,
                            # Neu co DocStore: dung full parent chunk
                            # Fallback: dung proposition text (schema cu / chua ingest lai)
                            "content": parent_content if parent_content else proposition_text,
                            "proposition": proposition_text,  # giu lai de debug/log
                            "metadata": meta,
                            "similarity": round(sim, 4),
                        }
        except Exception as e:
            print(f"⚠️ [Layer 3] Lỗi khi search query '{q}': {e}")
            continue

    # Sắp xếp theo điểm RRF giảm dần
    sorted_doc_ids = sorted(rrf_scores.keys(), key=lambda d_id: rrf_scores[d_id], reverse=True)

    ranked_docs = []
    for d_id in sorted_doc_ids:
        doc_item = doc_lookup[d_id]
        doc_item["rrf_score"] = round(rrf_scores[d_id], 6)
        ranked_docs.append(doc_item)

    return ranked_docs


# ════════════════════════════════════════════════════════════════════
# 2. CRAG: Document Grader (Đánh giá & Lọc sạch tài liệu rác)
# ════════════════════════════════════════════════════════════════════
def grade_document(question: str, doc_content: str) -> bool:
    """
    Sử dụng LLM nhỏ để đánh giá xem 1 document cụ thể có liên quan đến câu hỏi không.
    Trả về True nếu liên quan, False nếu không liên quan.
    """
    prompt = f"""Bạn là chuyên gia đánh giá mức độ liên quan của tài liệu (Document Grader) cho ứng dụng ChatMessageE2E.

Nhiệm vụ: Đánh giá xem đoạn tài liệu tham khảo dưới đây có chứa thông tin hữu ích giúp trả lời câu hỏi của người dùng hay không.

Câu hỏi của người dùng:
"{question}"

Tài liệu tham khảo:
\"\"\"{doc_content}\"\"\"

Đoạn tài liệu này có hữu ích và liên quan trực tiếp đến câu hỏi không?
Chỉ trả lời duy nhất: "yes" hoặc "no"."""

    # 1. Ưu tiên sử dụng Grok Cloud siêu tốc
    if is_grok_available():
        res_grok = call_grok_chat(prompt=prompt, temperature=0.0, max_tokens=15)
        if res_grok:
            verdict = res_grok.strip().lower()
            return "yes" in verdict

    # 2. Fallback sang Gemini
    try:
        model = genai.GenerativeModel(
            model_name=FAST_MODEL_NAME,
            generation_config={
                "temperature": 0.0,
                "max_output_tokens": 15,
            }
        )
        response = model.generate_content(prompt)
        verdict = ""
        try:
            verdict = response.text.strip().lower()
        except Exception:
            if response.candidates and response.candidates[0].content.parts:
                verdict = response.candidates[0].content.parts[0].text.strip().lower()
            else:
                verdict = "yes"
        return "yes" in verdict
    except Exception as e:
        print(f"⚠️ [Layer 3 CRAG Grader] Lỗi LLM grading: {e}. Mặc định giữ lại.")
        return True



def crag_retrieve_and_grade(
    queries: List[str],
    collection=None,
    top_k: int = 3,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Hàm thực thi chính của Layer 3:
      1. RRF Multi-Query Search trong ChromaDB
      2. LLM Grader lọc tài liệu (CRAG)

    Args:
        queries (List[str]): Danh sách câu hỏi từ Layer 2 (câu đầu tiên là câu hỏi gốc).
        collection: ChromaDB collection (nếu None sẽ tự nạp).
        top_k (int): Số lượng tài liệu liên quan tối đa cần giữ lại.
        verbose (bool): In chi tiết log khi chạy.

    Returns:
        Dict[str, Any]: {
            "relevant_docs": List[Dict], # Danh sách tài liệu đã qua sàng lọc
            "has_context": bool,         # True nếu có ít nhất 1 doc relevant
            "total_candidates": int      # Số ứng viên trước khi lọc
        }
    """
    if not queries:
        return {"relevant_docs": [], "has_context": False, "total_candidates": 0}

    original_question = queries[0]

    if collection is None:
        collection = get_chroma_collection()

    if collection.count() == 0:
        if verbose:
            print("⚠️ [Layer 3] ChromaDB hiện đang rỗng (chưa ingest dữ liệu).")
        return {"relevant_docs": [], "has_context": False, "total_candidates": 0}

    # 1. RAG Fusion Retrieval (RRF)
    candidates = rrf_retrieve(collection, queries, top_candidates_per_query=4)
    if verbose:
        print(f"🔍 [Layer 3 RRF] Tìm thấy {len(candidates)} ứng viên từ {len(queries)} truy vấn.")

    # 2. CRAG Document Grading
    graded_docs = []
    for doc in candidates:
        is_relevant = grade_document(original_question, doc["content"])
        if verbose:
            cat = doc["metadata"].get("category", "FAQ")
            q_src = doc["metadata"].get("question", "")[:40]
            status = "✅ RELEVANT" if is_relevant else "❌ IRRELEVANT"
            print(f"   [{status}] [{cat}] {q_src}... (RRF: {doc.get('rrf_score')})")

        if is_relevant:
            graded_docs.append(doc)
            if len(graded_docs) >= top_k:
                break

    return {
        "relevant_docs": graded_docs,
        "has_context": len(graded_docs) > 0,
        "total_candidates": len(candidates)
    }

