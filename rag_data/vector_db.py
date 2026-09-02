"""
RAG Vector Database Pipeline — ChatMessageE2E
==============================================
Bước 4: Nạp toàn bộ embeddings vào ChromaDB (local, persistent)
và xây dựng hàm Retrieval với chiến lược 2 lớp:
  - Lớp 1: Metadata filter theo category
  - Lớp 2: Vector similarity Top-K trong nhóm đã lọc

Input  : rag_data/embeddings/embeddings.json
Output : rag_data/vector_db/chroma_db/  (Persistent ChromaDB folder)
Config : rag_data/.env  (GOOGLE_API_KEY — dùng để embed câu hỏi khi test E2E)
"""

import json
import os
import math
from pathlib import Path
from typing import List, Dict, Any, Optional

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
COLLECTION_NAME = "chatmessage_faq"
TOP_K_DEFAULT   = 3      # Số kết quả trả về mặc định

# ── Tham số Embedding (dùng lại khi query) ───────────────────────────────────
EMBEDDING_MODEL = "models/text-embedding-004"


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
#  PHẦN 2: RETRIEVAL — TÌM KIẾM 2 LỚP
# ════════════════════════════════════════════════════════════════

def search(
    collection,
    query_embedding: List[float],
    category: Optional[str] = None,
    top_k: int = TOP_K_DEFAULT,
) -> List[Dict[str, Any]]:
    """
    Hàm Retrieval chính: Tìm kiếm 2 lớp.

    Lớp 1: Nếu category được cung cấp → Lọc theo metadata.category trước.
    Lớp 2: So sánh vector similarity trong tập đã lọc → Lấy top_k gần nhất.

    Args:
        query_embedding: Vector 768 chiều của câu hỏi người dùng
        category: Tên danh mục để filter (None = tìm toàn bộ DB)
        top_k: Số kết quả trả về

    Returns:
        Danh sách kết quả, mỗi item gồm: page_content, metadata, distance
    """
    # Xây dựng điều kiện filter
    where_clause = None
    if category:
        where_clause = {"category": {"$eq": category}}

    # Gọi ChromaDB query
    raw = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where_clause,
        include=["documents", "metadatas", "distances"],
    )

    # Đóng gói kết quả theo format dễ dùng
    results = []
    if raw["ids"] and raw["ids"][0]:
        for i in range(len(raw["ids"][0])):
            # ChromaDB cosine distance: 0.0 = giống hệt, 2.0 = đối nghịch
            # Cosine Similarity = 1 - distance
            distance   = raw["distances"][0][i]
            similarity = 1.0 - distance

            results.append({
                "id":           raw["ids"][0][i],
                "page_content": raw["documents"][0][i],
                "metadata":     raw["metadatas"][0][i],
                "distance":     round(distance, 6),
                "similarity":   round(similarity, 6),
            })

    return results


def detect_category(query: str) -> Optional[str]:
    """
    Phát hiện sơ bộ category của câu hỏi người dùng dựa trên từ khóa.
    Giúp kích hoạt Metadata Filter ở Lớp 1 của Retrieval.
    Trả về None nếu không xác định được → tìm toàn bộ DB.
    """
    query_lower = query.lower()

    keyword_map = {
        "Đăng nhập": [
            "đăng nhập", "login", "sign in", "google account",
            "tài khoản", "xác thực", "phiên", "session"
        ],
        "Tìm kiếm": [
            "tìm kiếm", "tìm", "search", "gmail", "địa chỉ",
            "khám phá", "find"
        ],
        "Kết nối & Handshake": [
            "kết nối", "handshake", "lời mời", "chấp nhận",
            "xác minh", "safety code", "mã an toàn", "4 lớp",
            "bắt đầu chat", "verify"
        ],
        "Nhắn tin": [
            "nhắn tin", "gửi tin", "tin nhắn", "message",
            "chat", "trả lời", "đọc", "gửi"
        ],
        "Gửi hình ảnh": [
            "hình ảnh", "ảnh", "image", "photo", "file", "jpg",
            "png", "gif", "đính kèm", "attachment"
        ],
        "Thu hồi & Xóa tin nhắn": [
            "thu hồi", "xóa", "unsend", "delete", "recall",
            "xóa tin nhắn", "thu hồi tin nhắn"
        ],
        "Bảo mật & Mã hóa": [
            "bảo mật", "mã hóa", "encrypt", "e2ee", "private key",
            "khóa", "zero knowledge", "an toàn", "security"
        ],
        "Chặn & Bỏ chặn": [
            "chặn", "block", "bỏ chặn", "unblock", "khóa liên hệ"
        ],
        "Xác minh lại (Re-handshake)": [
            "xác minh lại", "re-handshake", "re-verify",
            "khóa thay đổi", "key changed", "thiết bị mới"
        ],
        "Trạng thái & Chỉ báo": [
            "đang gõ", "typing", "online", "offline",
            "trạng thái", "chỉ báo", "indicator"
        ],
        "Giao diện": [
            "giao diện", "ui", "màn hình", "điện thoại", "mobile",
            "responsive", "dark mode", "sidebar"
        ],
        "Lỗi thường gặp": [
            "lỗi", "error", "không giải mã", "mất kết nối",
            "hết hạn", "expired", "decrypt"
        ],
    }

    for category, keywords in keyword_map.items():
        if any(kw in query_lower for kw in keywords):
            return category

    return None  # Không xác định được → tìm toàn bộ DB


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
    Câu hỏi người dùng → Embed → Detect Category → Search → In kết quả
    """
    print("\n" + "═" * 60)
    print("  🧪 TEST E2E — Giả lập Câu Hỏi Người Dùng")
    print("═" * 60)

    for i, query in enumerate(test_queries, 1):
        print(f"\n[Query {i}] 👤 \"{query}\"")

        # Bước 1: Phát hiện category
        detected_cat = detect_category(query)
        if detected_cat:
            print(f"  📂 Detected category: \"{detected_cat}\" → Kích hoạt metadata filter")
        else:
            print(f"  📂 Không xác định category → Tìm toàn bộ DB")

        # Bước 2: Embed câu hỏi (RETRIEVAL_QUERY)
        try:
            query_vec = embed_query(query)
        except Exception as e:
            print(f"  ⚠️  Không thể embed query (thiếu API key?): {e}")
            print(f"  → Bỏ qua test query này\n")
            continue

        # Bước 3: Search với 2 lớp
        results = search(collection, query_vec, category=detected_cat, top_k=3)

        # Bước 4: In kết quả
        if not results:
            print(f"  ❌ Không tìm thấy kết quả phù hợp")
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

    # 6. Test E2E với 3 câu hỏi mẫu thực tế
    sample_queries = [
        "Tôi muốn tìm bạn bè thì làm thế nào?",
        "Làm sao để thu hồi tin nhắn đã gửi?",
        "Safety code là cái gì và tại sao cần xác minh?",
    ]
    test_e2e_query(collection, sample_queries)

    print("\n✅ Vector Database hoàn tất!")
    print("🚀 Offline Pipeline (4 bước) đã hoàn chỉnh!")
    print("📋 Bước tiếp theo: Online Pipeline — nhận câu hỏi → retrieve → LLM → trả lời")


if __name__ == "__main__":
    main()
