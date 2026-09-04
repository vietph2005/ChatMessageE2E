"""
RAG Ingestion Pipeline — ChatMessageE2E
========================================
Tự động quét toàn bộ tài liệu Markdown trong `rag_data/docs/`,
tự động phân đoạn (chunking), trích xuất Category/Question, tự sinh ID và
thực hiện nạp tăng dần (Incremental Upsert) vào ChromaDB.

Đặc điểm nổi bật:
  1. Không cần gõ ID hay format JSON thủ công.
  2. Tự động sinh ID duy nhất và mã Content Hash (SHA-256).
  3. Incremental Upsert: Chỉ gọi Gemini Embedding API cho đoạn mới hoặc đã sửa đổi.
     Các đoạn giữ nguyên sẽ được BỎ QUA 100% để tiết kiệm quota và thời gian.
  4. Tương thích 100% với cấu trúc metadata của Java Backend (RagApiClient) và Frontend.

Cách dùng:
  python rag_data/ingest.py          # Nạp tăng dần (chỉ nạp bài mới/sửa)
  python rag_data/ingest.py --force  # Xóa và nạp lại toàn bộ từ đầu
"""

import os
import sys
import re
import time
import hashlib
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# ── Nạp cấu hình .env ─────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "docs"
CHROMA_DB_DIR = BASE_DIR / "vector_db" / "chroma_db"
COLLECTION_NAME = "chatmessage_faq"

try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")
VECTOR_DIM = 3072
BATCH_SIZE = 10
MAX_RETRIES = 3
RETRY_DELAY = 2.0


# ── Hàm trợ giúp bóc tách và làm sạch Markdown ──────────────────────────────
def slugify(text: str) -> str:
    """Tạo slug đơn giản từ chuỗi tiếng Việt để làm ID dễ đọc."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "_", text).strip("_")
    return text[:30] or "item"


def parse_markdown_file(file_path: Path) -> List[Dict[str, Any]]:
    """
    Đọc một file Markdown và phân tích thành các đơn vị ngữ nghĩa:
    - Tiêu đề cấp 1 (# Title): Dùng làm Category chung của file.
    - Tiêu đề cấp 2 (## Section/Question): Dùng làm Question / Chủ đề con.
    - Nội dung phía dưới: Dùng làm Answer / Nội dung chi tiết.
    """
    content = file_path.read_text(encoding="utf-8").strip()
    if not content:
        return []

    lines = content.splitlines()

    # Tìm Category từ tiêu đề # đầu tiên (nếu có)
    category = file_path.stem.replace("_", " ").title()
    for line in lines:
        if line.startswith("# ") and not line.startswith("## "):
            category = line[2:].strip()
            break

    # Tách các mục theo ##
    sections: List[Dict[str, Any]] = []
    current_heading = None
    current_body_lines: List[str] = []

    for line in lines:
        if line.startswith("## "):
            if current_heading is not None and current_body_lines:
                body = "\n".join(current_body_lines).strip()
                if body:
                    sections.append({
                        "question": current_heading,
                        "body": body
                    })
            current_heading = line[3:].strip()
            current_body_lines = []
        elif current_heading is not None:
            current_body_lines.append(line)
        else:
            # Nội dung phía trên ## đầu tiên (nếu có đoạn giới thiệu)
            pass

    # Thêm section cuối cùng
    if current_heading is not None and current_body_lines:
        body = "\n".join(current_body_lines).strip()
        if body:
            sections.append({
                "question": current_heading,
                "body": body
            })

    # Nếu file không có ## (chỉ là văn bản thuần), coi toàn bộ là 1 section
    if not sections:
        clean_text = "\n".join([l for l in lines if not l.startswith("# ")]).strip()
        if clean_text:
            sections.append({
                "question": category,
                "body": clean_text
            })

    # Chuyển đổi thành LangChain/RAG Document chuẩn
    documents = []
    file_stem = file_path.stem

    for idx, sec in enumerate(sections, start=1):
        q = sec["question"]
        ans = sec["body"]
        page_content = f"Câu hỏi: {q}\n\nTrả lời: {ans}".strip()

        # Tính hash nội dung (SHA-256)
        content_hash = hashlib.sha256(page_content.encode("utf-8")).hexdigest()[:16]

        # Tự sinh ID độc nhất: vd "01_dang_nhap_c01_lam_the_nao_de_a1b2c3"
        auto_id = f"{file_stem}_c{idx:02d}_{content_hash[:8]}"

        doc = {
            "id": auto_id,
            "page_content": page_content,
            "metadata": {
                "id": auto_id,
                "category": category,
                "question": q,
                "source": file_path.name,
                "doc_type": "markdown_doc",
                "language": "vi",
                "chunk_index": idx - 1,
                "chunk_total": len(sections),
                "char_count": len(page_content),
                "chunk_strategy": "markdown_section",
                "content_hash": content_hash,
            }
        }
        documents.append(doc)

    return documents


# ── Khởi tạo ChromaDB Client ─────────────────────────────────────────────────
def get_chroma_collection():
    """Khởi tạo hoặc kết nối vào ChromaDB persistent collection."""
    try:
        import chromadb
    except ImportError:
        print("❌ Chưa cài chromadb. Chạy: pip install chromadb")
        sys.exit(1)

    CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )
    return client, collection


# ── Khởi tạo Gemini Embedding API ─────────────────────────────────────────────
def get_gemini_client():
    """Khởi tạo Google GenAI Client."""
    try:
        import google.generativeai as genai
    except ImportError:
        print("❌ Chưa cài google-generativeai. Chạy: pip install google-generativeai python-dotenv")
        sys.exit(1)

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ Không tìm thấy GOOGLE_API_KEY trong file rag_data/.env hoặc biến môi trường!")
        sys.exit(1)

    genai.configure(api_key=api_key)
    return genai


def embed_texts(genai, texts: List[str]) -> List[List[float]]:
    """Gửi batch texts đến Gemini API để nhận vector embeddings."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            result = genai.embed_content(
                model=EMBEDDING_MODEL,
                content=texts,
                task_type="RETRIEVAL_DOCUMENT",
            )
            return result["embedding"]
        except Exception as e:
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                raise RuntimeError(f"Embedding failed after {MAX_RETRIES} attempts: {e}")


# ── Ingestion Pipeline Chính ─────────────────────────────────────────────────
def run_ingestion(force_reindex: bool = False):
    print("=" * 70)
    print("🚀 [RAG INGESTION] BẮT ĐẦU NẠP DỮ LIỆU TỰ ĐỘNG TỪ MARKDOWN")
    print(f"📂 Thư mục tài liệu: {DOCS_DIR}")
    print("=" * 70)

    if not DOCS_DIR.exists():
        DOCS_DIR.mkdir(parents=True, exist_ok=True)
        print(f"⚠️ Thư mục {DOCS_DIR} chưa tồn tại. Đã tạo mới.")
        print("💡 Hãy thêm các file .md vào thư mục trên và chạy lại.")
        return

    md_files = sorted(list(DOCS_DIR.glob("*.md")))
    if not md_files:
        print(f"⚠️ Không tìm thấy file .md nào trong {DOCS_DIR}.")
        return

    print(f"📄 Tìm thấy {len(md_files)} file Markdown.")

    # Đọc và bóc tách toàn bộ documents từ Markdown
    all_chunks: List[Dict[str, Any]] = []
    for f in md_files:
        chunks = parse_markdown_file(f)
        all_chunks.extend(chunks)
        print(f"   ✓ {f.name:35} -> {len(chunks)} mục (chunks)")

    print(f"\n📊 Tổng số chunks trích xuất: {len(all_chunks)}")

    # Kết nối ChromaDB
    client, collection = get_chroma_collection()

    if force_reindex:
        print("\n⚠️  [FORCE] Đang xóa toàn bộ dữ liệu cũ trong collection để nạp lại từ đầu...")
        client.delete_collection(COLLECTION_NAME)
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )

    # Lấy thông tin các chunks đã có trong ChromaDB
    existing_items = collection.get(include=["metadatas"])
    existing_hashes = set()
    if existing_items and existing_items["metadatas"]:
        for m in existing_items["metadatas"]:
            h = m.get("content_hash")
            if h:
                existing_hashes.add(h)

    print(f"📦 ChromaDB hiện tại đang lưu: {len(existing_hashes)} chunks")

    # Lọc ra các chunks mới hoặc có nội dung thay đổi
    new_chunks = []
    skipped_count = 0

    for chunk in all_chunks:
        c_hash = chunk["metadata"]["content_hash"]
        if c_hash in existing_hashes and not force_reindex:
            skipped_count += 1
        else:
            new_chunks.append(chunk)

    print(f"⚡ Đã tồn tại (Bỏ qua): {skipped_count} chunks")
    print(f"🆕 Cần embedding và nạp mới: {len(new_chunks)} chunks")

    if not new_chunks:
        print("\n✅ Không có nội dung nào thay đổi. Dữ liệu đã là mới nhất!")
        return

    # Khởi tạo Gemini client
    genai = get_gemini_client()

    # Thực hiện embed theo từng batch
    print(f"\n🧠 Đang gọi Gemini Embedding ({EMBEDDING_MODEL}) cho {len(new_chunks)} chunks...")
    batch_size = BATCH_SIZE
    total_batches = -(-len(new_chunks) // batch_size)

    for b_idx in range(0, len(new_chunks), batch_size):
        batch = new_chunks[b_idx: b_idx + batch_size]
        current_batch_num = (b_idx // batch_size) + 1
        texts = [c["page_content"] for c in batch]

        vectors = embed_texts(genai, texts)

        # Chuẩn bị nạp vào ChromaDB
        ids = [c["id"] for c in batch]
        documents = [c["page_content"] for c in batch]
        metadatas = [c["metadata"] for c in batch]

        collection.upsert(
            ids=ids,
            embeddings=vectors,
            documents=documents,
            metadatas=metadatas,
        )

        print(f"   ✓ Nạp thành công Batch {current_batch_num}/{total_batches} ({len(batch)} chunks)")
        if b_idx + batch_size < len(new_chunks):
            time.sleep(0.3)

    final_count = collection.count()
    print("\n" + "=" * 70)
    print(f"🎉 HOÀN TẤT INGESTION!")
    print(f"📈 Tổng số chunks hiện có trong ChromaDB: {final_count}")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ChatMessage RAG Incremental Ingestion")
    parser.add_argument("--force", action="store_true", help="Force re-indexing all documents from scratch")
    args = parser.parse_args()

    run_ingestion(force_reindex=args.force)
