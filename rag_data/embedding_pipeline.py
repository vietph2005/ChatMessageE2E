"""
RAG Embedding Pipeline — ChatMessageE2E
========================================
Bước 3: Chuyển đổi toàn bộ chunks thành vector embeddings
sử dụng Google text-embedding-004 (Free Gemini API).

Chiến lược:
  - task_type=RETRIEVAL_DOCUMENT khi embed chunks (lưu vào DB)
  - task_type=RETRIEVAL_QUERY khi embed câu hỏi người dùng (runtime)
  - Batch embedding: gửi nhiều chunks cùng lúc để tiết kiệm thời gian
  - Retry tự động nếu gặp lỗi mạng/rate limit

Input  : rag_data/chunks/chunks.json
Output : rag_data/embeddings/embeddings.json
Config : rag_data/.env  (GOOGLE_API_KEY)
"""

import json
import os
import time
from pathlib import Path
from typing import List, Dict, Any

# ── Load API Key từ file .env ─────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    # Tìm file .env trong cùng thư mục với script này
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass  # dotenv chưa cài — dùng biến môi trường hệ thống

# ── Cài đặt đường dẫn ────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
INPUT_PATH  = BASE_DIR / "chunks" / "chunks.json"
OUTPUT_DIR  = BASE_DIR / "embeddings"
OUTPUT_PATH = OUTPUT_DIR / "embeddings.json"

# ── Tham số Embedding ─────────────────────────────────────────────────────────
EMBEDDING_MODEL = "models/text-embedding-004"
VECTOR_DIM      = 768    # Số chiều vector của text-embedding-004
BATCH_SIZE      = 20     # Số chunks gửi mỗi lần gọi API
MAX_RETRIES     = 3      # Số lần thử lại nếu gặp lỗi
RETRY_DELAY     = 2.0    # Giây chờ giữa các lần retry


# ── Khởi tạo Google Generative AI client ────────────────────────────────────
def init_google_client():
    """Khởi tạo client với API key từ .env hoặc biến môi trường."""
    try:
        import google.generativeai as genai
    except ImportError:
        print("❌ Chưa cài google-generativeai. Chạy: pip install google-generativeai python-dotenv")
        raise

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "❌ Không tìm thấy GOOGLE_API_KEY!\n"
            "   Tạo file rag_data/.env và thêm dòng:\n"
            "   GOOGLE_API_KEY=your_key_here"
        )

    genai.configure(api_key=api_key)
    print(f"[INIT] ✅ Google Gemini API đã được khởi tạo")
    print(f"[INIT] Model: {EMBEDDING_MODEL} ({VECTOR_DIM} chiều)")
    return genai


# ── Embed một batch chunks ────────────────────────────────────────────────────
def embed_batch(
    genai,
    texts: List[str],
    batch_num: int,
    total_batches: int
) -> List[List[float]]:
    """
    Gửi một batch văn bản đến Google API và nhận về danh sách vectors.
    task_type=RETRIEVAL_DOCUMENT: Tối ưu cho việc lưu trữ tài liệu vào DB.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            result = genai.embed_content(
                model=EMBEDDING_MODEL,
                content=texts,
                task_type="RETRIEVAL_DOCUMENT",
            )
            vectors = result["embedding"]
            print(f"  ✅ Batch {batch_num}/{total_batches} — {len(texts)} chunks → {len(vectors)} vectors")
            return vectors

        except Exception as e:
            if attempt < MAX_RETRIES:
                print(f"  ⚠️  Batch {batch_num} lỗi (lần {attempt}/{MAX_RETRIES}): {e}")
                print(f"  ⏳ Chờ {RETRY_DELAY}s rồi thử lại...")
                time.sleep(RETRY_DELAY)
            else:
                print(f"  ❌ Batch {batch_num} thất bại sau {MAX_RETRIES} lần thử: {e}")
                raise


# ── Main embedding pipeline ───────────────────────────────────────────────────
def run_embedding(genai, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Chạy embedding cho toàn bộ chunks theo batch."""
    print(f"\n[EMBED] Bắt đầu embedding {len(chunks)} chunks...")
    print(f"[EMBED] Batch size: {BATCH_SIZE} | Tổng batches: {-(-len(chunks) // BATCH_SIZE)}")

    results = []
    total_batches = -(-len(chunks) // BATCH_SIZE)  # Ceiling division

    for batch_idx in range(0, len(chunks), BATCH_SIZE):
        batch_chunks = chunks[batch_idx: batch_idx + BATCH_SIZE]
        batch_num    = batch_idx // BATCH_SIZE + 1

        # Lấy nội dung text của từng chunk trong batch
        texts = [c["page_content"] for c in batch_chunks]

        # Gọi Google API
        vectors = embed_batch(genai, texts, batch_num, total_batches)

        # Ghép vector vào từng chunk
        for chunk, vector in zip(batch_chunks, vectors):
            results.append({
                "page_content": chunk["page_content"],
                "metadata":     chunk["metadata"],
                "embedding":    vector,     # Vector 768 chiều
            })

        # Tránh rate limit: nghỉ nhỏ giữa các batches
        if batch_idx + BATCH_SIZE < len(chunks):
            time.sleep(0.3)

    return results


# ── Validate kết quả embedding ────────────────────────────────────────────────
def validate_embeddings(embedded_chunks: List[Dict[str, Any]], original_count: int) -> bool:
    """Kiểm tra tất cả embeddings đều hợp lệ."""
    print("\n[VALIDATE] Kiểm tra kết quả embedding...")
    errors = []

    # 1. Số lượng phải khớp
    if len(embedded_chunks) != original_count:
        errors.append(f"  ❌ Số lượng không khớp: {len(embedded_chunks)} embeddings / {original_count} chunks")

    for i, item in enumerate(embedded_chunks):
        vec = item.get("embedding", [])
        doc_id = item.get("metadata", {}).get("id", f"#{i}")

        # 2. Vector không được rỗng
        if not vec:
            errors.append(f"  ❌ [{doc_id}]: embedding rỗng")
            continue

        # 3. Đúng số chiều
        if len(vec) != VECTOR_DIM:
            errors.append(f"  ❌ [{doc_id}]: sai số chiều — nhận {len(vec)}, kỳ vọng {VECTOR_DIM}")

        # 4. Tất cả values là float
        if not all(isinstance(v, float) for v in vec[:5]):
            errors.append(f"  ❌ [{doc_id}]: vector không phải kiểu float")

    if errors:
        print("\n".join(errors))
        return False

    print(f"[VALIDATE] ✅ Tất cả {len(embedded_chunks)} embeddings hợp lệ ({VECTOR_DIM} chiều)")
    return True


# ── Kiểm tra cosine similarity (Manual Verification) ─────────────────────────
def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Tính cosine similarity giữa 2 vectors."""
    import math
    dot   = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = math.sqrt(sum(a ** 2 for a in vec_a))
    mag_b = math.sqrt(sum(b ** 2 for b in vec_b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def run_similarity_check(embedded_chunks: List[Dict[str, Any]]) -> None:
    """
    Kiểm tra thủ công chất lượng embedding:
    - 2 câu hỏi cùng chủ đề phải có similarity CAO (> 0.85)
    - 2 câu hỏi khác chủ đề phải có similarity THẤP (< 0.7)
    """
    print("\n[VERIFY] Kiểm tra chất lượng Embedding qua Cosine Similarity...")

    # Tạo dict để tra cứu theo ID
    by_id = {item["metadata"]["id"]: item for item in embedded_chunks}

    tests = [
        # (ID_1, ID_2, Kỳ vọng, Mô tả)
        ("auth-001", "auth-002", "CAO",   "Cùng chủ đề Đăng nhập"),
        ("auth-001", "block-001", "THẤP", "Khác chủ đề: Đăng nhập vs Chặn"),
        ("msg-001",  "msg-002",  "CAO",   "Cùng chủ đề Nhắn tin"),
        ("unsend-001", "search-001", "THẤP", "Khác chủ đề: Thu hồi vs Tìm kiếm"),
    ]

    print(f"  {'ID 1':<15} {'ID 2':<15} {'Similarity':>12}  {'Kỳ vọng':<8}  Đánh giá")
    print("  " + "-" * 65)

    for id1, id2, expected, desc in tests:
        if id1 not in by_id or id2 not in by_id:
            print(f"  ⚠️  Không tìm thấy {id1} hoặc {id2} — bỏ qua")
            continue

        sim = cosine_similarity(by_id[id1]["embedding"], by_id[id2]["embedding"])

        if expected == "CAO":
            status = "✅ Đúng" if sim >= 0.80 else "⚠️  Thấp hơn kỳ vọng"
        else:
            status = "✅ Đúng" if sim < 0.80 else "⚠️  Cao hơn kỳ vọng"

        print(f"  {id1:<15} {id2:<15} {sim:>12.4f}  {expected:<8}  {status}  ({desc})")


# ── Thống kê ─────────────────────────────────────────────────────────────────
def print_statistics(embedded_chunks: List[Dict[str, Any]]) -> None:
    print("\n" + "=" * 57)
    print("  📊 KẾT QUẢ EMBEDDING")
    print("=" * 57)
    print(f"  Tổng chunks đã embed   : {len(embedded_chunks)}")
    print(f"  Model                  : {EMBEDDING_MODEL}")
    print(f"  Số chiều vector        : {VECTOR_DIM}")

    # Phân bổ theo category
    from collections import Counter
    cats = Counter(c["metadata"].get("category", "?") for c in embedded_chunks)
    print(f"\n  Phân bổ theo chủ đề:")
    for cat, count in sorted(cats.items()):
        print(f"    {cat:<35} {count} chunks")

    # Preview vector đầu tiên
    first_vec = embedded_chunks[0]["embedding"]
    print(f"\n  📐 Preview vector đầu tiên (5 chiều đầu):")
    print(f"    {[round(v, 6) for v in first_vec[:5]]} ...")
    print("=" * 57)


# ── Load & Save ───────────────────────────────────────────────────────────────
def load_chunks(path: Path) -> List[Dict[str, Any]]:
    print(f"[LOAD] Đọc chunks từ: {path}")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    print(f"[LOAD] ✅ Tải được {len(data)} chunks")
    return data


def save_embeddings(data: List[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    size_kb = path.stat().st_size / 1024
    print(f"\n[SAVE] ✅ Đã lưu {len(data)} embeddings → {path} ({size_kb:.1f} KB)")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 57)
    print("  🔢 RAG EMBEDDING PIPELINE — ChatMessageE2E")
    print("=" * 57)

    # 1. Khởi tạo Google client
    genai = init_google_client()

    # 2. Load chunks
    chunks = load_chunks(INPUT_PATH)

    # 3. Chạy embedding
    embedded = run_embedding(genai, chunks)

    # 4. Validate
    is_valid = validate_embeddings(embedded, len(chunks))
    if not is_valid:
        print("\n❌ Embedding có lỗi. Kiểm tra lại API key và dữ liệu.")
        return

    # 5. Thống kê
    print_statistics(embedded)

    # 6. Kiểm tra cosine similarity
    run_similarity_check(embedded)

    # 7. Lưu ra file
    save_embeddings(embedded, OUTPUT_PATH)

    print("\n✅ Embedding hoàn tất!")
    print("📁 Bước tiếp theo: Vector Database (nạp embeddings.json vào ChromaDB/Qdrant)")


if __name__ == "__main__":
    main()
