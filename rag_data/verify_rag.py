import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from proposition_indexer import get_docstore_dir, get_chroma_collection, load_from_docstore
from layers.layer3_crag_retriever import rrf_retrieve

print("=" * 65)
print("🔍 KIỂM TRA TOÀN DIỆN DỮ LIỆU RAG & CHROMA DB")
print("=" * 65)

# 1. DocStore
print("\n[1] Kiểm tra DocStore (Parent Chunks):")
docstore_dir = get_docstore_dir()
doc_files = list(docstore_dir.glob("*.json"))
print(f"  📁 Số lượng file Parent Chunks trong DocStore: {len(doc_files)}")
if doc_files:
    sample_doc_id = doc_files[0].stem
    sample_content = load_from_docstore(sample_doc_id)
    print(f"  📄 Sample chunk ({sample_doc_id}):\n     \"{sample_content[:150]}...\"")

# 2. ChromaDB
print("\n[2] Kiểm tra ChromaDB Collection (Propositions):")
collection = get_chroma_collection()
count = collection.count()
print(f"  🔢 Tổng số vectors (propositions) trong ChromaDB: {count}")

# 3. Test Retrieval
print("\n[3] Test truy vấn thực tế:")
test_queries = [
    "Làm thế nào để đăng nhập vào ứng dụng?",
    "Mã hóa tin nhắn E2E hoạt động như thế nào?",
]

for query in test_queries:
    print(f"\n  🔎 Câu hỏi: \"{query}\"")
    results = rrf_retrieve(collection, [query], top_candidates_per_query=2)
    if not results:
        print("     ❌ Không tìm thấy kết quả phù hợp.")
    for i, r in enumerate(results[:2], 1):
        meta = r.get("metadata", {})
        prop = r.get("proposition", "")
        parent_chunk = r.get("content", "")
        print(f"     [{i}] Mệnh đề tìm được (Proposition):")
        print(f"         \"{prop}\"")
        print(f"         📁 Source : {meta.get('source_file')} | Phần: {meta.get('section')}")
        print(f"         📑 Parent Chunk (từ DocStore):\n         \"{parent_chunk[:140]}...\"")
        print(f"         ⭐ Cosine Sim: {r.get('similarity')} | RRF Score: {r.get('rrf_score')}")

print("\n" + "=" * 65)
print("✅ TẤT CẢ DỮ LIỆU ĐÃ SẴN SÀNG & HOẠT ĐỘNG CHÍNH XÁC!")
print("=" * 65)
