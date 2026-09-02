"""
RAG Online Pipeline — ChatMessageE2E
======================================
Bước 5 (Online): Nhận câu hỏi người dùng → Tìm ngữ cảnh phù hợp → Sinh câu trả lời.

Luồng hoạt động:
  1. Embed câu hỏi người dùng (text-embedding-004, RETRIEVAL_QUERY)
  2. Tìm Top-3 FAQ liên quan nhất từ ChromaDB (Pure Semantic Search, cutoff 0.55)
  3. Ghép ngữ cảnh retrieved vào Prompt theo chuẩn RAG
  4. Gọi Gemini 2.0 Flash sinh câu trả lời bằng tiếng Việt
  5. Trả về câu trả lời + metadata nguồn tham khảo

Yêu cầu:
  - Đã chạy xong Offline Pipeline (4 bước trước)
  - File rag_data/.env chứa GOOGLE_API_KEY

Cách dùng:
  python rag_data/rag_online.py
  hoặc import và gọi hàm answer(question) trong code khác
"""

import os
import math
from pathlib import Path
from typing import List, Dict, Any, Optional

# ── Load .env ─────────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

# ── Cấu hình Model ───────────────────────────────────────────────────────────
EMBEDDING_MODEL    = "models/text-embedding-004"
GENERATION_MODEL   = "gemini-2.0-flash"   # Miễn phí, nhanh, cùng API key
VECTOR_DIM         = 768

# ── Tham số Retrieval (đồng bộ với vector_db.py) ─────────────────────────────
TOP_K              = 3      # Số đoạn FAQ đưa vào ngữ cảnh
SIMILARITY_CUTOFF  = 0.55   # Ngưỡng tối thiểu (đồng bộ vector_db.py)
CHROMA_DB_DIR      = Path(__file__).parent / "vector_db" / "chroma_db"
COLLECTION_NAME    = "chatmessage_faq"

# ── System Prompt cho Gemini ──────────────────────────────────────────────────
SYSTEM_PROMPT = """Bạn là trợ lý hỗ trợ người dùng cho ứng dụng nhắn tin bảo mật ChatMessage.
Ứng dụng sử dụng mã hóa đầu cuối (E2EE), đăng nhập Google OAuth2 và quy trình xác minh 4 lớp.

Nguyên tắc trả lời:
1. Chỉ trả lời dựa trên TÀI LIỆU THAM KHẢO được cung cấp bên dưới.
2. Nếu tài liệu không đủ thông tin, hãy thành thật nói: "Tôi chưa có thông tin về vấn đề này."
3. Trả lời bằng tiếng Việt, ngắn gọn, rõ ràng, thân thiện.
4. Không bịa đặt hoặc suy diễn ngoài phạm vi tài liệu.
5. Nếu câu hỏi liên quan đến nhiều chủ đề, hãy trả lời từng phần một cách có cấu trúc."""


# ════════════════════════════════════════════════════════════════
#  PHẦN 1: KẾT NỐI CHROMADB
# ════════════════════════════════════════════════════════════════

def get_collection():
    """Lấy collection ChromaDB đã tồn tại từ offline pipeline."""
    try:
        import chromadb
    except ImportError:
        raise ImportError("❌ Chưa cài chromadb. Chạy: pip install chromadb")

    if not CHROMA_DB_DIR.exists():
        raise FileNotFoundError(
            f"❌ Không tìm thấy ChromaDB tại: {CHROMA_DB_DIR}\n"
            f"   Hãy chạy Offline Pipeline trước (4 bước)."
        )

    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
    collection = client.get_collection(name=COLLECTION_NAME)
    print(f"[DB] ✅ Kết nối ChromaDB — {collection.count()} FAQ trong database")
    return collection


# ════════════════════════════════════════════════════════════════
#  PHẦN 2: EMBED CÂU HỎI
# ════════════════════════════════════════════════════════════════

def embed_query(query: str) -> List[float]:
    """
    Chuyển câu hỏi người dùng thành vector 768 chiều.
    Dùng task_type=RETRIEVAL_QUERY để tối ưu cho bài toán tìm kiếm.
    """
    try:
        import google.generativeai as genai
    except ImportError:
        raise ImportError("❌ Chưa cài google-generativeai. Chạy: pip install google-generativeai")

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "❌ Không tìm thấy GOOGLE_API_KEY!\n"
            "   Tạo file rag_data/.env và thêm: GOOGLE_API_KEY=your_key_here"
        )

    genai.configure(api_key=api_key)
    result = genai.embed_content(
        model=EMBEDDING_MODEL,
        content=query,
        task_type="RETRIEVAL_QUERY",  # ← Khác với RETRIEVAL_DOCUMENT!
    )
    return result["embedding"]


# ════════════════════════════════════════════════════════════════
#  PHẦN 3: TÌM KIẾM THUẦN NGỮ NGHĨA
# ════════════════════════════════════════════════════════════════

def retrieve(collection, query_embedding: List[float]) -> List[Dict[str, Any]]:
    """
    Tìm tối đa TOP_K đoạn FAQ có độ tương đồng ngữ nghĩa cao nhất.
    Áp dụng ngưỡng SIMILARITY_CUTOFF để loại kết quả không liên quan.
    """
    fetch_k = min(TOP_K * 3, collection.count())

    raw = collection.query(
        query_embeddings=[query_embedding],
        n_results=fetch_k,
        include=["documents", "metadatas", "distances"],
    )

    results = []
    if raw["ids"] and raw["ids"][0]:
        for i in range(len(raw["ids"][0])):
            distance   = raw["distances"][0][i]
            similarity = round(1.0 - distance, 6)

            # Loại kết quả dưới ngưỡng
            if similarity < SIMILARITY_CUTOFF:
                continue

            results.append({
                "id":           raw["ids"][0][i],
                "page_content": raw["documents"][0][i],
                "metadata":     raw["metadatas"][0][i],
                "similarity":   similarity,
            })

            if len(results) >= TOP_K:
                break

    return results


# ════════════════════════════════════════════════════════════════
#  PHẦN 4: XÂY DỰNG PROMPT & SINH CÂU TRẢ LỜI
# ════════════════════════════════════════════════════════════════

def build_prompt(query: str, contexts: List[Dict[str, Any]]) -> str:
    """
    Ghép ngữ cảnh retrieved (RAG context) vào prompt theo chuẩn RAG.

    Cấu trúc prompt:
      - System: Vai trò và nguyên tắc của AI
      - Tài liệu tham khảo: Các đoạn FAQ retrieved có đánh số + điểm similarity
      - Câu hỏi: Câu hỏi gốc của người dùng
    """
    if not contexts:
        # Không tìm thấy ngữ cảnh liên quan
        return (
            f"{SYSTEM_PROMPT}\n\n"
            f"[KHÔNG CÓ TÀI LIỆU THAM KHẢO PHÙ HỢP]\n\n"
            f"Câu hỏi của người dùng: {query}"
        )

    # Ghép các đoạn FAQ thành khối ngữ cảnh
    context_blocks = []
    for i, ctx in enumerate(contexts, 1):
        cat        = ctx["metadata"].get("category", "?")
        similarity = ctx["similarity"]
        content    = ctx["page_content"].strip()
        context_blocks.append(
            f"[Tài liệu {i}] Danh mục: {cat} | Độ liên quan: {similarity:.0%}\n"
            f"{content}"
        )

    context_str = "\n\n---\n\n".join(context_blocks)

    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"{'=' * 60}\n"
        f"TÀI LIỆU THAM KHẢO:\n"
        f"{'=' * 60}\n"
        f"{context_str}\n"
        f"{'=' * 60}\n\n"
        f"Câu hỏi của người dùng: {query}\n\n"
        f"Câu trả lời (dựa trên tài liệu trên):"
    )
    return prompt


def generate_answer(prompt: str) -> str:
    """
    Gọi Gemini 2.0 Flash để sinh câu trả lời từ prompt đã được chuẩn bị.
    """
    try:
        import google.generativeai as genai
    except ImportError:
        raise ImportError("❌ Chưa cài google-generativeai.")

    api_key = os.getenv("GOOGLE_API_KEY")
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(
        model_name=GENERATION_MODEL,
        generation_config={
            "temperature":       0.2,   # Thấp → câu trả lời chắc chắn, ít lang man
            "max_output_tokens": 1024,
            "top_p":             0.8,
        }
    )

    response = model.generate_content(prompt)
    return response.text.strip()


# ════════════════════════════════════════════════════════════════
#  PHẦN 5: HÀM CHÍNH — ANSWER (ĐIỂM TÍCH HỢP CHO BACKEND)
# ════════════════════════════════════════════════════════════════

def answer(
    question: str,
    collection=None,
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Hàm tích hợp chính: nhận câu hỏi → trả về câu trả lời + metadata nguồn.

    Args:
        question   : Câu hỏi bằng ngôn ngữ tự nhiên của người dùng
        collection : ChromaDB collection (tái sử dụng kết nối nếu đã có)
        verbose    : In chi tiết quá trình nếu True

    Returns:
        {
            "answer"     : "Câu trả lời của AI...",
            "sources"    : [{"id": ..., "category": ..., "similarity": ...}],
            "has_context": True/False
        }
    """
    # Bước 1: Kết nối ChromaDB nếu chưa có
    if collection is None:
        collection = get_collection()

    if verbose:
        print(f"\n[RAG] Câu hỏi: \"{question}\"")

    # Bước 2: Embed câu hỏi
    query_vec = embed_query(question)
    if verbose:
        print(f"[RAG] ✅ Đã embed câu hỏi → vector {len(query_vec)} chiều")

    # Bước 3: Retrieve ngữ cảnh liên quan
    contexts = retrieve(collection, query_vec)
    if verbose:
        if contexts:
            print(f"[RAG] ✅ Tìm thấy {len(contexts)} đoạn FAQ liên quan:")
            for i, ctx in enumerate(contexts, 1):
                print(f"       [{i}] {ctx['metadata'].get('category')} — similarity: {ctx['similarity']:.4f}")
        else:
            print(f"[RAG] ⚠️  Không có ngữ cảnh liên quan (dưới ngưỡng {SIMILARITY_CUTOFF})")

    # Bước 4: Xây dựng prompt và sinh câu trả lời
    prompt   = build_prompt(question, contexts)
    response = generate_answer(prompt)

    if verbose:
        print(f"[RAG] ✅ Gemini đã trả lời ({len(response)} ký tự)")

    # Đóng gói kết quả
    sources = [
        {
            "id":         ctx["id"],
            "category":   ctx["metadata"].get("category", ""),
            "question":   ctx["metadata"].get("question", ""),
            "similarity": ctx["similarity"],
        }
        for ctx in contexts
    ]

    return {
        "answer":      response,
        "sources":     sources,
        "has_context": len(contexts) > 0,
    }


# ════════════════════════════════════════════════════════════════
#  DEMO: Chạy thử các câu hỏi mẫu
# ════════════════════════════════════════════════════════════════

def main():
    print("=" * 65)
    print("  🤖  RAG ONLINE PIPELINE — ChatMessageE2E")
    print(f"  📡  Generation Model : {GENERATION_MODEL}")
    print(f"  🔍  Embedding Model  : {EMBEDDING_MODEL}")
    print(f"  🎯  Similarity Cutoff: {SIMILARITY_CUTOFF}")
    print("=" * 65)

    # Kết nối ChromaDB một lần, tái sử dụng cho tất cả câu hỏi
    collection = get_collection()

    # Các câu hỏi thử nghiệm — đơn nhóm, đa nhóm, và lạc đề
    test_questions = [
        "Làm sao để tìm người dùng khác để bắt đầu chat?",
        "Tin nhắn bị lỗi không gửi được, tôi phải làm sao?",
        "Safety code là gì và tại sao tôi phải xác nhận nó?",
        "Nếu tôi đăng nhập máy mới thì tin nhắn cũ có còn không và bảo mật ra sao?",
        "Thời tiết hôm nay thế nào?",   # Câu lạc đề — kỳ vọng từ chối khéo
    ]

    for i, q in enumerate(test_questions, 1):
        print(f"\n{'─' * 65}")
        print(f"[Câu hỏi {i}] 👤 {q}")
        print("─" * 65)

        result = answer(q, collection=collection, verbose=True)

        print(f"\n🤖 Trả lời:\n{result['answer']}")

        if result["sources"]:
            print(f"\n📚 Nguồn tham khảo ({len(result['sources'])} đoạn):")
            for src in result["sources"]:
                print(f"   • [{src['category']}] {src['question'][:60]}... ({src['similarity']:.0%})")
        else:
            print("📚 Không có nguồn tham khảo (câu hỏi ngoài phạm vi)")

    print(f"\n{'=' * 65}")
    print("✅ Online Pipeline hoàn tất!")


if __name__ == "__main__":
    main()
