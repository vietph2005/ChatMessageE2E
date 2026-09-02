"""
RAG Data Preparation Pipeline — ChatMessageE2E
================================================
Bước 1: Đọc Q&A corpus từ faq_corpus.json và chuẩn bị
LangChain Documents có metadata đầy đủ, sẵn sàng cho bước Chunking.

Tech stack: Python + LangChain
Output:     rag_data/prepared/documents.json
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Đảm bảo in UTF-8 không bị lỗi trên Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# ── Cài đặt đường dẫn ────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
CORPUS_PATH = BASE_DIR / "corpus" / "faq_corpus.json"
OUTPUT_DIR = BASE_DIR / "prepared"
OUTPUT_PATH = OUTPUT_DIR / "documents.json"


# ── Bước 1: Load raw Q&A corpus ──────────────────────────────────────────────
def load_corpus(path: Path) -> List[Dict[str, Any]]:
    """Đọc file JSON chứa các cặp Q&A."""
    print(f"[LOAD] Đọc corpus từ: {path}")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    print(f"[LOAD] ✅ Tải được {len(data)} mục Q&A")
    return data


# ── Bước 2: Chuyển đổi mỗi Q&A thành LangChain Document format ───────────────
def convert_to_documents(corpus: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Chuyển mỗi Q&A entry thành định dạng LangChain Document:
    - page_content: Nội dung sẽ được embed (Q + A kết hợp)
    - metadata: Thông tin phụ trợ cho retrieval và trả lời
    """
    documents = []

    for item in corpus:
        # Ghép câu hỏi và câu trả lời thành một đoạn văn có ngữ nghĩa
        # Định dạng này giúp embedding model hiểu ngữ cảnh đầy đủ
        page_content = (
            f"Câu hỏi: {item['question']}\n\n"
            f"Trả lời: {item['answer']}"
        )

        # Làm sạch: loại bỏ khoảng trắng thừa
        page_content = page_content.strip()

        doc = {
            "page_content": page_content,
            "metadata": {
                "id": item["id"],
                "category": item["category"],
                "question": item["question"],   # Dùng cho fuzzy match
                "source": item.get("source", ""),
                "doc_type": "faq",
                "language": "vi",
                "app": "ChatMessageE2E",
            }
        }
        documents.append(doc)

    return documents


MAX_DOC_LENGTH_CEILING = 1200  # Ngưỡng cảnh báo độ dài tối đa tại bước Data Preparation


# ── Bước 3: Kiểm tra chất lượng dữ liệu ─────────────────────────────────────
def validate_documents(documents: List[Dict[str, Any]]) -> bool:
    """Kiểm tra từng document có đủ thông tin cần thiết, không trùng lặp và không vượt trần."""
    print("\n[VALIDATE] Kiểm tra chất lượng documents...")
    errors = []
    warnings = []
    seen_ids = set()
    seen_questions = {}

    for i, doc in enumerate(documents):
        meta = doc.get("metadata", {})
        doc_id = meta.get("id")
        question = meta.get("question", "").strip().lower()
        content = doc.get("page_content", "")
        doc_len = len(content)

        # 1. Kiểm tra trường bắt buộc
        if not content.strip():
            errors.append(f"  ❌ Document #{i}: page_content rỗng")
        if not doc_id:
            errors.append(f"  ❌ Document #{i}: thiếu metadata.id")
        if not meta.get("category"):
            errors.append(f"  ❌ Document #{i}: thiếu metadata.category")

        # 2. Kiểm tra trùng lặp ID
        if doc_id:
            if doc_id in seen_ids:
                errors.append(f"  ❌ Document #{i}: trùng lặp ID '{doc_id}'")
            seen_ids.add(doc_id)

        # 3. Kiểm tra trùng lặp câu hỏi
        if question:
            if question in seen_questions:
                prev_id = seen_questions[question]
                warnings.append(f"  ⚠️  Document #{i} [{doc_id}]: câu hỏi bị trùng với [{prev_id}]")
            else:
                seen_questions[question] = doc_id

        # 4. Kiểm tra độ dài & Cảnh báo trần
        if doc_len < 20:
            errors.append(f"  ❌ Document #{i} [{doc_id}]: nội dung quá ngắn ({doc_len} ký tự)")
        elif doc_len > MAX_DOC_LENGTH_CEILING:
            warnings.append(
                f"  ⚠️  [CẢNH BÁO TRẦN] Document #{i} [{doc_id}]: dài {doc_len} ký tự "
                f"(vượt ngưỡng trần {MAX_DOC_LENGTH_CEILING}). Khuyến nghị: tách thành 2 câu nhỏ từ data gốc."
            )

    if warnings:
        print("\n".join(warnings))

    if errors:
        print("\n".join(errors))
        return False

    print(f"[VALIDATE] ✅ Tất cả {len(documents)} documents hợp lệ")
    return True


# ── Bước 4: Thống kê và preview ──────────────────────────────────────────────
def print_statistics(documents: List[Dict[str, Any]]) -> None:
    """In thống kê tổng quan về corpus."""
    print("\n" + "=" * 55)
    print("  📊 THỐNG KÊ CORPUS")
    print("=" * 55)
    print(f"  Tổng số documents  : {len(documents)}")

    # Đếm theo category
    from collections import Counter
    categories = Counter(doc["metadata"]["category"] for doc in documents)
    print(f"\n  Phân bổ theo chủ đề:")
    for cat, count in sorted(categories.items()):
        bar = "█" * count
        print(f"    {cat:<35} {bar} ({count})")

    # Độ dài trung bình
    lengths = [len(doc["page_content"]) for doc in documents]
    print(f"\n  Độ dài nội dung (ký tự):")
    print(f"    Trung bình : {sum(lengths) // len(lengths)}")
    print(f"    Ngắn nhất  : {min(lengths)}")
    print(f"    Dài nhất   : {max(lengths)}")

    # Preview 2 documents đầu
    print(f"\n  📄 Preview document đầu tiên:")
    print("  " + "-" * 53)
    preview = documents[0]["page_content"][:200] + "..."
    for line in preview.split("\n"):
        print(f"  {line}")
    print(f"\n  Metadata: {documents[0]['metadata']}")
    print("=" * 55)


# ── Bước 5: Xuất ra file JSON ─────────────────────────────────────────────────
def save_documents(documents: List[Dict[str, Any]], output_path: Path) -> None:
    """Lưu documents ra file JSON để dùng ở bước Chunking tiếp theo."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)
    print(f"\n[SAVE] ✅ Đã lưu {len(documents)} documents → {output_path}")


# ── Demo: Load lại và kiểm tra bằng LangChain ────────────────────────────────
def demo_with_langchain(output_path: Path) -> None:
    """
    Demo đọc lại bằng LangChain Document object.
    Chạy: pip install langchain
    """
    try:
        from langchain.schema import Document

        with open(output_path, encoding="utf-8") as f:
            raw = json.load(f)

        lc_docs = [
            Document(page_content=d["page_content"], metadata=d["metadata"])
            for d in raw
        ]

        print(f"\n[LANGCHAIN] ✅ Load thành công {len(lc_docs)} LangChain Document objects")
        print(f"[LANGCHAIN] Sample document type : {type(lc_docs[0])}")
        print(f"[LANGCHAIN] Sample metadata keys : {list(lc_docs[0].metadata.keys())}")
        print(f"\n[LANGCHAIN] 🚀 Sẵn sàng cho bước tiếp theo: Chunking + Embedding!")

    except ImportError:
        print("\n[LANGCHAIN] ⚠️  langchain chưa cài. Chạy: pip install langchain")
        print("[LANGCHAIN] Bỏ qua demo LangChain, documents.json vẫn đã được tạo thành công.")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  🚀 RAG DATA PREPARATION — ChatMessageE2E")
    print("=" * 55 + "\n")

    # 1. Load
    corpus = load_corpus(CORPUS_PATH)

    # 2. Convert
    print("\n[CONVERT] Chuyển đổi sang LangChain Document format...")
    documents = convert_to_documents(corpus)
    print(f"[CONVERT] ✅ Tạo được {len(documents)} documents")

    # 3. Validate
    is_valid = validate_documents(documents)
    if not is_valid:
        print("\n❌ Corpus có lỗi. Kiểm tra lại faq_corpus.json")
        return

    # 4. Statistics
    print_statistics(documents)

    # 5. Save
    save_documents(documents, OUTPUT_PATH)

    # 6. Demo LangChain
    demo_with_langchain(OUTPUT_PATH)

    print("\n✅ Data Preparation hoàn tất!")
    print("📁 Bước tiếp theo: Chunking (dùng RecursiveCharacterTextSplitter)")


if __name__ == "__main__":
    main()
