"""
RAG Chunking Pipeline — ChatMessageE2E
=======================================
Bước 2: Nhận LangChain Documents từ bước Data Preparation
và thực hiện chunking theo chiến lược Hybrid:

  - Chiến lược chính : 1 Document = 1 Chunk
                        (mỗi Q&A đã là 1 đơn vị ngữ nghĩa hoàn chỉnh)
  - Chiến lược backup: RecursiveCharacterTextSplitter
                        (chỉ kích hoạt khi entry > CHUNK_SIZE_THRESHOLD ký tự)
  - Bảo vệ cấu trúc  : Không bao giờ cắt giữa bảng (|...|) hoặc danh sách
  - Metadata          : Giữ nguyên gốc + thêm chunk_index, chunk_total, char_count

Input  : rag_data/prepared/documents.json
Output : rag_data/chunks/chunks.json
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple

# ── Cài đặt đường dẫn ────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
INPUT_PATH = BASE_DIR / "prepared" / "documents.json"
OUTPUT_DIR = BASE_DIR / "chunks"
OUTPUT_PATH = OUTPUT_DIR / "chunks.json"

# ── Tham số chunking ──────────────────────────────────────────────────────────
CHUNK_SIZE_THRESHOLD = 500    # Ký tự — entry ngắn hơn ngưỡng này → giữ nguyên
MAX_PROTECTED_LENGTH = 1200   # Ngưỡng trần tối đa: Vượt quá số này thì KHÔNG bảo vệ cấu trúc nữa mà buộc phải cắt
RECURSIVE_CHUNK_SIZE = 500    # Chunk size cho RecursiveCharacterTextSplitter
RECURSIVE_OVERLAP    = 80     # Overlap giữa 2 chunk khi phải cắt


# ── Hàm kiểm tra: có chứa bảng hoặc danh sách có thứ tự không? ───────────────
def _has_table_or_list(text: str) -> bool:
    """
    Phát hiện nếu văn bản chứa Markdown table (|...|) hoặc danh sách
    có đánh số (1. 2. 3.) hoặc danh sách ký hiệu (- item).
    → Nếu có, KHÔNG cắt để bảo vệ cấu trúc.
    """
    has_table       = bool(re.search(r"\|.+\|", text))
    has_numbered    = bool(re.search(r"^\s*\d+\.\s", text, re.MULTILINE))
    has_bullet      = bool(re.search(r"^\s*[-*]\s", text, re.MULTILINE))
    return has_table or has_numbered or has_bullet


# ── Chiến lược chính: Giữ nguyên 1 Document = 1 Chunk ────────────────────────
def _keep_as_single_chunk(
    doc: Dict[str, Any],
    original_index: int
) -> List[Dict[str, Any]]:
    """Đóng gói document thành 1 chunk duy nhất với metadata bổ sung."""
    chunk = {
        "page_content": doc["page_content"].strip(),
        "metadata": {
            **doc["metadata"],          # Giữ nguyên toàn bộ metadata gốc
            "chunk_index": 0,
            "chunk_total": 1,
            "char_count": len(doc["page_content"].strip()),
            "chunk_strategy": "single",
            "doc_index": original_index,
        }
    }
    return [chunk]


# ── Chiến lược backup: RecursiveCharacterTextSplitter ─────────────────────────
def _split_with_recursive(
    doc: Dict[str, Any],
    original_index: int
) -> List[Dict[str, Any]]:
    """
    Dùng LangChain RecursiveCharacterTextSplitter để cắt các entry quá dài.
    Thứ tự ưu tiên cắt: đoạn văn (\n\n) → dòng (\n) → câu (. ) → từ ( )
    """
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
    except ImportError:
        # Nếu chưa cài langchain, fallback về giữ nguyên
        print(f"  ⚠️  langchain chưa cài — giữ nguyên document dài #{original_index}")
        return _keep_as_single_chunk(doc, original_index)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=RECURSIVE_CHUNK_SIZE,
        chunk_overlap=RECURSIVE_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )

    raw_chunks = splitter.split_text(doc["page_content"])
    chunks = []
    for i, text in enumerate(raw_chunks):
        chunk = {
            "page_content": text.strip(),
            "metadata": {
                **doc["metadata"],          # Giữ nguyên metadata gốc
                "chunk_index": i,
                "chunk_total": len(raw_chunks),
                "char_count": len(text.strip()),
                "chunk_strategy": "recursive_split",
                "doc_index": original_index,
            }
        }
        chunks.append(chunk)
    return chunks


# ── Dispatcher: Quyết định dùng chiến lược nào cho từng document ─────────────
def chunk_document(
    doc: Dict[str, Any],
    index: int
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Logic quyết định chiến lược chunking:
      1. Entry ngắn (≤ CHUNK_SIZE_THRESHOLD)      → Giữ nguyên (single)
      2. Entry dài + có bảng/danh sách            → Giữ nguyên (protected)
      3. Entry dài + không có bảng/danh sách      → Cắt bằng Recursive
    Trả về: (danh sách chunks, tên chiến lược đã dùng)
    """
    text = doc["page_content"]
    length = len(text)

    # Trường hợp 1: Ngắn → giữ nguyên luôn
    if length <= CHUNK_SIZE_THRESHOLD:
        return _keep_as_single_chunk(doc, index), "single"

    # Trường hợp 2: Dài vừa phải (≤ MAX_PROTECTED_LENGTH) nhưng có bảng/danh sách → bảo vệ cấu trúc
    if _has_table_or_list(text) and length <= MAX_PROTECTED_LENGTH:
        chunks = _keep_as_single_chunk(doc, index)
        chunks[0]["metadata"]["chunk_strategy"] = "single_protected"
        return chunks, "single_protected"

    # Trường hợp 3: Vượt ngưỡng trần (> MAX_PROTECTED_LENGTH) HOẶC dài mà không có cấu trúc đặc biệt → cắt Recursive
    return _split_with_recursive(doc, index), "recursive_split"


# ── Main chunking pipeline ───────────────────────────────────────────────────
def run_chunking(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Chạy chunking cho toàn bộ danh sách documents."""
    print("\n[CHUNK] Bắt đầu chunking...")
    print(f"[CHUNK] Ngưỡng cắt: {CHUNK_SIZE_THRESHOLD} ký tự")

    all_chunks = []
    strategy_counts = {"single": 0, "single_protected": 0, "recursive_split": 0}

    for i, doc in enumerate(documents):
        doc_id = doc["metadata"].get("id", f"doc_{i}")
        chunks, strategy = chunk_document(doc, i)

        strategy_counts[strategy] += 1
        all_chunks.extend(chunks)

        # Log chi tiết cho từng document
        char_count = len(doc["page_content"])
        status = "✂️ " if strategy == "recursive_split" else ("🛡️ " if strategy == "single_protected" else "✅")
        print(f"  {status} [{doc_id}] {char_count} ký tự → {len(chunks)} chunk ({strategy})")

    return all_chunks, strategy_counts


# ── Validate chunks ───────────────────────────────────────────────────────────
def validate_chunks(chunks: List[Dict[str, Any]]) -> bool:
    """Đảm bảo mọi chunk đều có đủ các trường bắt buộc."""
    print("\n[VALIDATE] Kiểm tra chunks...")
    errors = []
    required_metadata = ["id", "category", "chunk_index", "chunk_total", "char_count"]

    for i, chunk in enumerate(chunks):
        if not chunk.get("page_content", "").strip():
            errors.append(f"  ❌ Chunk #{i}: page_content rỗng")
        for field in required_metadata:
            if field not in chunk.get("metadata", {}):
                errors.append(f"  ❌ Chunk #{i}: thiếu metadata.{field}")

    if errors:
        print("\n".join(errors))
        return False

    print(f"[VALIDATE] ✅ Tất cả {len(chunks)} chunks hợp lệ")
    return True


# ── Thống kê kết quả ──────────────────────────────────────────────────────────
def print_chunk_statistics(
    chunks: List[Dict[str, Any]],
    strategy_counts: Dict[str, int],
    original_count: int
) -> None:
    """In báo cáo thống kê sau khi chunking."""
    lengths = [c["metadata"]["char_count"] for c in chunks]
    single_chunks = [c for c in chunks if c["metadata"]["chunk_total"] == 1]
    split_chunks  = [c for c in chunks if c["metadata"]["chunk_total"] > 1]

    print("\n" + "=" * 57)
    print("  📊 KẾT QUẢ CHUNKING")
    print("=" * 57)
    print(f"  Documents ban đầu       : {original_count}")
    print(f"  Tổng chunks tạo ra      : {len(chunks)}")
    print(f"  Tỷ lệ mở rộng           : {len(chunks)/original_count:.2f}x")
    print(f"\n  Phân loại theo chiến lược:")
    print(f"    ✅ Giữ nguyên (single)   : {strategy_counts['single']} documents")
    print(f"    🛡️  Bảo vệ cấu trúc      : {strategy_counts['single_protected']} documents")
    print(f"    ✂️  Cắt Recursive         : {strategy_counts['recursive_split']} documents")
    print(f"\n  Độ dài chunk (ký tự):")
    print(f"    Trung bình : {sum(lengths) // len(lengths)}")
    print(f"    Ngắn nhất  : {min(lengths)}")
    print(f"    Dài nhất   : {max(lengths)}")

    # Preview 1 chunk điển hình
    print(f"\n  📄 Preview chunk đầu tiên:")
    print("  " + "-" * 55)
    c = chunks[0]
    preview = c["page_content"][:200].replace("\n", " ") + "..."
    print(f"  {preview}")
    print(f"\n  Metadata: {c['metadata']}")
    print("=" * 57)


# ── Load và Save ──────────────────────────────────────────────────────────────
def load_documents(path: Path) -> List[Dict[str, Any]]:
    print(f"[LOAD] Đọc documents từ: {path}")
    with open(path, encoding="utf-8") as f:
        docs = json.load(f)
    print(f"[LOAD] ✅ Tải được {len(docs)} documents")
    return docs


def save_chunks(chunks: List[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    print(f"\n[SAVE] ✅ Đã lưu {len(chunks)} chunks → {path}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 57)
    print("  ✂️  RAG CHUNKING PIPELINE — ChatMessageE2E")
    print("=" * 57)

    # 1. Load documents từ bước Data Preparation
    documents = load_documents(INPUT_PATH)

    # 2. Chạy chunking
    all_chunks, strategy_counts = run_chunking(documents)

    # 3. Validate
    is_valid = validate_chunks(all_chunks)
    if not is_valid:
        print("\n❌ Chunking có lỗi. Kiểm tra lại dữ liệu.")
        return

    # 4. Thống kê
    print_chunk_statistics(all_chunks, strategy_counts, len(documents))

    # 5. Lưu ra file
    save_chunks(all_chunks, OUTPUT_PATH)

    print("\n✅ Chunking hoàn tất!")
    print("📁 Bước tiếp theo: Embedding Model (embed từng chunk → vector)")


if __name__ == "__main__":
    main()
