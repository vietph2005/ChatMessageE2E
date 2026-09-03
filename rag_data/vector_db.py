"""
RAG Vector Database Pipeline — ChatMessageE2E
==============================================
Bước 4: Nạp toàn bộ embeddings vào ChromaDB (local, persistent)
và xây dựng hàm Retrieval thuần ngữ nghĩa (Pure Semantic Search):
  - Tìm kiếm tương đồng vector Cosine trên toàn bộ cơ sở dữ liệu
  - Áp dụng ngưỡng similarity cutoff (>= 0.55) để loại kết quả không liên quan
  - Giải quyết triệt để bài toán câu hỏi đa chủ đề / không khớp từ khóa

Input  : rag_data/embeddings/embeddings.json
Output : rag_data/vector_db/chroma_db/  (Persistent ChromaDB folder)
Config : rag_data/.env  (GOOGLE_API_KEY — dùng để embed câu hỏi khi test E2E)
"""

import json
import os
import sys
import math
from pathlib import Path
from typing import List, Dict, Any, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

# ── Đường dẫn ────────────────────────────────────────────────────────────────
BASE_DIR        = Path(__file__).parent
EMBEDDINGS_PATH = BASE_DIR / "embeddings" / "embeddings.json"
CHROMA_DB_DIR   = BASE_DIR / "vector_db" / "chroma_db"

# ── Tham số ChromaDB ──────────────────────────────────────────────────────────
COLLECTION_NAME   = "chatmessage_faq"
TOP_K_DEFAULT     = 3      # Số kết quả trả về mặc định
SIMILARITY_CUTOFF = 0.55   # Ngưỡng tối thiểu: kết quả similarity thấp hơn sẽ bị loại

# ── Tham số Embedding (dùng lại khi query) ───────────────────────────────────
EMBEDDING_MODEL = "models/gemini-embedding-001"



# ════════════════════════════════════════════════════════════════
#  PHẦN 1: KHỞI TẠO VÀ NẠP DỮ LIỆU
# ════════════════════════════════════════════════════════════════

def init_chromadb():
    """
    Khởi tạo ChromaDB persistent client.
    Dữ liệu được lưu vĩnh viễn trên disk tại CHROMA_DB_DIR.
    """
    try:
        import chromadb
    except ImportError:
        raise ImportError(
            "❌ Chưa cài chromadb. Chạy: pip install chromadb"
        )

    CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
    print(f"[INIT] ✅ ChromaDB khởi tạo tại: {CHROMA_DB_DIR}")
    return client


def get_or_create_collection(client):
    """
    Lấy collection đã có hoặc tạo mới.
    Dùng cosine distance vì embeddings của Google được tối ưu cho cosine similarity.
    """
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},  # Dùng cosine distance
    )
    print(f"[COLLECTION] ✅ Collection '{COLLECTION_NAME}' sẵn sàng")
    print(f"[COLLECTION] Số items hiện tại: {collection.count()}")
    return collection


def load_embeddings(path: Path) -> List[Dict[str, Any]]:
    """Đọc file embeddings.json từ bước Embedding."""
    print(f"\n[LOAD] Đọc embeddings từ: {path}")
    if not path.exists():
        raise FileNotFoundError(
            f"❌ Không tìm thấy file: {path}\n"
            f"   Hãy chạy bước 3 trước: python rag_data/embedding_pipeline.py"
        )
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    print(f"[LOAD] ✅ Tải được {len(data)} embeddings")
    return data


def ingest_embeddings(collection, embeddings: List[Dict[str, Any]]) -> None:
    """
    Nạp toàn bộ embeddings vào ChromaDB Collection.
    Nếu item đã tồn tại (cùng ID), dùng upsert để cập nhật thay vì lỗi duplicate.
    """
    current_count = collection.count()
    if current_count > 0:
        print(f"\n[INGEST] Collection đã có {current_count} items — dùng upsert để cập nhật")
    else:
        print(f"\n[INGEST] Bắt đầu nạp {len(embeddings)} embeddings vào ChromaDB...")

    # Chuẩn bị dữ liệu theo format ChromaDB
    ids        = []
    documents  = []
    vectors    = []
    metadatas  = []

    for item in embeddings:
        meta = item["metadata"]
        ids.append(meta["id"])
        documents.append(item["page_content"])
        vectors.append(item["embedding"])

        # ChromaDB metadata chỉ hỗ trợ str, int, float, bool
        # Loại bỏ hoặc ép kiểu các field không hợp lệ
        safe_meta = {
            "id":             meta.get("id", ""),
            "category":       meta.get("category", ""),
            "question":       meta.get("question", ""),
            "source":         meta.get("source", ""),
            "doc_type":       meta.get("doc_type", "faq"),
            "language":       meta.get("language", "vi"),
            "chunk_index":    int(meta.get("chunk_index", 0)),
            "chunk_total":    int(meta.get("chunk_total", 1)),
            "char_count":     int(meta.get("char_count", 0)),
            "chunk_strategy": meta.get("chunk_strategy", "single"),
        }
        metadatas.append(safe_meta)

    # Upsert vào ChromaDB (tự động tạo mới hoặc cập nhật)
    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=vectors,
        metadatas=metadatas,
    )

    final_count = collection.count()
    print(f"[INGEST] ✅ Hoàn tất! ChromaDB hiện có {final_count} items")


# ════════════════════════════════════════════════════════════════
#  PHẦN 2: RETRIEVAL — PURE SEMANTIC SEARCH
# ════════════════════════════════════════════════════════════════

def search(
    collection,
    query_embedding: List[float],
    top_k: int = TOP_K_DEFAULT,
    similarity_cutoff: float = SIMILARITY_CUTOFF,
) -> List[Dict[str, Any]]:
    """
    Hàm Retrieval thuần ngữ nghĩa (Pure Semantic Search).

    Không dùng Metadata Filter cứng theo category nữa.
    Thay vào đó:
      - Lấy top_k * 3 kết quả rộng rãi từ toàn bộ DB
      - Lọc bỏ những kết quả có similarity < similarity_cutoff
      - Trả về tối đa top_k kết quả có nghĩa nhất

    Ưu điểm:
      - Xử lý đúng câu hỏi đa chủ đề (không bị First-match lệch nhóm)
      - Không bỏ sót FAQ liên quan ở nhóm khác
      - Không cần bảo trì bảng từ khóa thủ công

    Args:
        query_embedding   : Vector 768 chiều của câu hỏi người dùng
        top_k             : Số kết quả tối đa trả về
        similarity_cutoff : Ngưỡng similarity tối thiểu để giữ kết quả

    Returns:
        Danh sách kết quả đã lọc, mỗi item gồm: id, page_content, metadata,
        distance, similarity
    """
    # Lấy rộng hơn top_k để sau khi lọc theo ngưỡng vẫn còn đủ kết quả
    fetch_k = min(top_k * 3, collection.count())

    # Tìm kiếm trên TOÀN BỘ DB — không có where_clause
    raw = collection.query(
        query_embeddings=[query_embedding],
        n_results=fetch_k,
        include=["documents", "metadatas", "distances"],
    )

    results = []
    if raw["ids"] and raw["ids"][0]:
        for i in range(len(raw["ids"][0])):
            # ChromaDB cosine distance: 0.0 = giống hệt, 2.0 = đối nghịch
            # Cosine Similarity = 1 - distance
            distance   = raw["distances"][0][i]
            similarity = 1.0 - distance

            # Lọc: bỏ qua những kết quả ngữ nghĩa quá yếu
            if similarity < similarity_cutoff:
                continue

            results.append({
                "id":           raw["ids"][0][i],
                "page_content": raw["documents"][0][i],
                "metadata":     raw["metadatas"][0][i],
                "distance":     round(distance, 6),
                "similarity":   round(similarity, 6),
            })

            # Dừng khi đã đủ top_k kết quả chất lượng
            if len(results) >= top_k:
                break

    return results


# ════════════════════════════════════════════════════════════════
#  PHẦN 3: TEST E2E (Giả lập câu hỏi người dùng thực)
# ════════════════════════════════════════════════════════════════

def embed_query(query: str) -> List[float]:
    """
    Embed câu hỏi người dùng với task_type=RETRIEVAL_QUERY.
    (Phân biệt với RETRIEVAL_DOCUMENT dùng khi lưu tài liệu)
    """
    try:
        import google.generativeai as genai
    except ImportError:
        raise ImportError("❌ Chưa cài google-generativeai. Chạy: pip install google-generativeai")

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("❌ Không tìm thấy GOOGLE_API_KEY trong file .env")

    genai.configure(api_key=api_key)
    result = genai.embed_content(
        model=EMBEDDING_MODEL,
        content=query,
        task_type="RETRIEVAL_QUERY",  # ← Khác với RETRIEVAL_DOCUMENT!
    )
    return result["embedding"]


def test_e2e_query(collection, test_queries: List[str]) -> None:
    """
    Giả lập toàn bộ luồng thực tế của chatbot:
    Câu hỏi người dùng → Embed → Pure Semantic Search → Lọc ngưỡng → In kết quả
    """
    print("\n" + "═" * 60)
    print("  🧪 TEST E2E — Pure Semantic Search (Không metadata filter)")
    print("═" * 60)

    for i, query in enumerate(test_queries, 1):
        print(f"\n[Query {i}] 👤 \"{query}\"")
        print(f"  🔍 Tìm kiếm thuần ngữ nghĩa trên toàn bộ DB (ngưỡng similarity ≥ {SIMILARITY_CUTOFF})")

        # Bước 1: Embed câu hỏi (RETRIEVAL_QUERY)
        try:
            query_vec = embed_query(query)
        except Exception as e:
            print(f"  ⚠️  Không thể embed query (thiếu API key?): {e}")
            print(f"  → Bỏ qua test query này\n")
            continue

        # Bước 2: Pure semantic search — không filter theo category
        results = search(collection, query_vec, top_k=3)

        # Bước 3: In kết quả
        if not results:
            print(f"  ❌ Không tìm thấy kết quả phù hợp (similarity < {SIMILARITY_CUTOFF})")
            continue

        print(f"  🎯 Top {len(results)} kết quả:")
        for j, r in enumerate(results, 1):
            angle = math.degrees(math.acos(max(-1.0, min(1.0, r["similarity"]))))
            content_preview = r["page_content"][:120].replace("\n", " ") + "..."
            print(f"\n  [{j}] ID: {r['id']} | Similarity: {r['similarity']:.4f} (góc: {angle:.1f}°)")
            print(f"       Category: {r['metadata']['category']}")
            print(f"       Preview: {content_preview}")


# ════════════════════════════════════════════════════════════════
#  PHẦN 4: VERIFY INDEX
# ════════════════════════════════════════════════════════════════

def verify_index(collection, embeddings: List[Dict[str, Any]]) -> bool:
    """Kiểm tra số lượng items và thử query giả bằng vector của item đầu tiên."""
    print("\n[VERIFY] Kiểm tra Vector DB...")
    errors = []

    # 1. Số lượng phải khớp
    actual_count = collection.count()
    expected_count = len(embeddings)
    if actual_count != expected_count:
        errors.append(
            f"  ❌ Số lượng không khớp: DB có {actual_count}, kỳ vọng {expected_count}"
        )

    # 2. Thử query giả với vector của item đầu tiên
    try:
        test_vec = embeddings[0]["embedding"]
        test_results = search(collection, test_vec, top_k=1)
        if not test_results:
            errors.append("  ❌ Query thử nghiệm không trả về kết quả")
        elif test_results[0]["similarity"] < 0.99:
            errors.append(
                f"  ⚠️  Query chính item đầu tiên nhưng similarity chỉ "
                f"{test_results[0]['similarity']:.4f} (kỳ vọng > 0.99)"
            )
        else:
            print(f"  ✅ Query thử nghiệm: top-1 = '{test_results[0]['id']}' "
                  f"(similarity={test_results[0]['similarity']:.4f})")
    except Exception as e:
        errors.append(f"  ❌ Query thử nghiệm thất bại: {e}")

    if errors:
        print("\n".join(errors))
        return False

    print(f"[VERIFY] ✅ Vector DB hợp lệ — {actual_count} items, query hoạt động tốt")
    return True


def print_db_statistics(collection, embeddings: List[Dict[str, Any]]) -> None:
    """In thống kê tổng quan về Vector DB."""
    from collections import Counter
    cats = Counter(
        item["metadata"].get("category", "?") for item in embeddings
    )

    print("\n" + "═" * 60)
    print("  📊 THỐNG KÊ VECTOR DATABASE")
    print("═" * 60)
    print(f"  Collection : {COLLECTION_NAME}")
    print(f"  Tổng items : {collection.count()}")
    print(f"  Lưu tại    : {CHROMA_DB_DIR}")
    print(f"  Distance   : Cosine")
    print(f"\n  Phân bổ theo category:")
    for cat, count in sorted(cats.items()):
        bar = "█" * count
        print(f"    {cat:<40} {bar} ({count})")
    print("═" * 60)


# ════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════

def main():
    print("═" * 60)
    print("  🗄️  RAG VECTOR DATABASE — ChatMessageE2E (ChromaDB)")
    print("═" * 60)

    # 1. Khởi tạo ChromaDB
    client = init_chromadb()
    collection = get_or_create_collection(client)

    # 2. Load embeddings từ bước 3
    embeddings = load_embeddings(EMBEDDINGS_PATH)

    # 3. Nạp vào ChromaDB
    ingest_embeddings(collection, embeddings)

    # 4. Verify
    is_valid = verify_index(collection, embeddings)
    if not is_valid:
        print("\n❌ Vector DB có lỗi. Kiểm tra lại embeddings.json")
        return

    # 5. Thống kê
    print_db_statistics(collection, embeddings)

    print("\n✅ Vector Database hoàn tất!")
    print("🚀 Offline Pipeline (4 bước) đã hoàn chỉnh!")
    print("📋 Bước tiếp theo: Online Pipeline — nhận câu hỏi → retrieve → LLM → trả lời")


if __name__ == "__main__":
    main()
