"""
Layer 4 — Generator (Context-Augmented Generation)
==================================================
Mục đích:
  - Tiếp nhận danh sách tài liệu sạch đã được CRAG phê duyệt từ Layer 3.
  - Xây dựng prompt có cấu trúc chặt chẽ (Grounded Prompting):
      + Định hình vai trò trợ lý kỹ thuật ChatMessageE2E.
      + Cung cấp ngữ cảnh tài liệu kèm nguồn tham khảo rõ ràng.
      + Nguyên tắc bất biến: Chỉ trả lời dựa trên tài liệu, KHÔNG tự ý suy diễn ngoài ngữ cảnh.
  - Sử dụng Gemini (MAIN_MODEL_NAME) với nhiệt độ thấp (temperature=0.2) để đảm bảo tính khách quan,
    chính xác và trình bày mạch lạc (gạch đầu dòng, in đậm từ khóa quan trọng).
  - Định dạng sẵn danh sách `sources` tương thích 100% với Frontend TypeScript và Java DTO.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

# Đảm bảo import được config từ thư mục cha rag_data
CURRENT_DIR = Path(__file__).resolve().parent
PARENT_DIR = CURRENT_DIR.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

from config import init_gemini, MAIN_MODEL_NAME
import google.generativeai as genai

# Khởi tạo Gemini
init_gemini()

SYSTEM_GENERATOR_ROLE = """Bạn là trợ lý AI thông minh chuyên hỗ trợ kỹ thuật và giải đáp thắc mắc cho ứng dụng nhắn tin bảo mật ChatMessageE2E.

VAI TRÒ & NGUYÊN TẮC BẮT BUỘC:
1. TRUNG THỰC VỚI TÀI LIỆU (GROUNDED):
   - Chỉ sử dụng các thông tin, sự thật và số liệu có trong phần TÀI LIỆU THAM KHẢO dưới đây.
   - Tuyệt đối KHÔNG tự sáng tác, bịa đặt hoặc suy diễn các thông số bảo mật không có trong tài liệu.
   - Nếu tài liệu không đủ dữ liệu để trả lời trọn vẹn, hãy thẳng thắn thừa nhận phần thông tin chưa được đề cập.

2. TRÌNH BÀY CHUYÊN NGHIỆP:
   - Trả lời bằng tiếng Việt tự nhiên, rõ ràng, gãy gọn.
   - Sử dụng định dạng Markdown (gạch đầu dòng, đánh số bước, in đậm các thuật ngữ kỹ thuật như **ECDH**, **AES-256-GCM**, **OAuth2**, **Handshake 4 lớp**).
   - Đi thẳng vào trọng tâm câu hỏi của người dùng."""

OUT_OF_CONTEXT_ANSWER = (
    "Tôi chưa có thông tin về vấn đề này trong cơ sở dữ liệu của ChatMessageE2E.\n\n"
    "Hiện tại tôi được huấn luyện để hỗ trợ các chủ đề chính sau:\n"
    "• **Đăng nhập & Tài khoản**: Xác thực Google OAuth2, bảo vệ JWT token.\n"
    "• **Bảo mật & Mã hóa E2EE**: Thuật toán ECDH, AES-256-GCM, quản lý Key Bundle.\n"
    "• **Cơ chế bắt tay (Handshake 4 lớp)**: Khởi tạo phiên mã hóa 1-1.\n"
    "• **Nhắn tin & Media**: Gửi văn bản, hình ảnh, file đính kèm đã mã hóa.\n"
    "• **Chặn kết nối & Khắc phục sự cố**: Block/Unblock, lỗi mất khóa giải mã.\n\n"
    "Bạn vui lòng kiểm tra lại câu hỏi hoặc hỏi về các tính năng trên nhé!"
)


def format_context_blocks(docs: List[Dict[str, Any]]) -> str:
    """Ghép các đoạn tài liệu tham khảo thành khối văn bản có đánh số rõ ràng."""
    blocks = []
    for idx, d in enumerate(docs, start=1):
        cat = d.get("metadata", {}).get("category", "Tài liệu kỹ thuật")
        q_origin = d.get("metadata", {}).get("question", "")
        content = d.get("content", "").strip()

        block = (
            f"--- [TÀI LIỆU {idx}] ---\n"
            f"Danh mục: {cat}\n"
            f"Chủ đề gốc: {q_origin}\n"
            f"Nội dung:\n{content}"
        )
        blocks.append(block)

    return "\n\n".join(blocks)


def build_generation_prompt(question: str, docs: List[Dict[str, Any]]) -> str:
    """Tạo prompt hoàn chỉnh cho Gemini sinh câu trả lời."""
    context_str = format_context_blocks(docs)

    prompt = f"""{SYSTEM_GENERATOR_ROLE}

======================================================================
TÀI LIỆU THAM KHẢO TỪ HỆ THỐNG:
======================================================================
{context_str}
======================================================================

CÂU HỎI CỦA NGƯỜI DÙNG:
"{question}"

CÂU TRẢ LỜI CỦA BẠN (Dựa trên các tài liệu trên):"""

    return prompt


def generate_answer(
    question: str,
    relevant_docs: List[Dict[str, Any]],
    has_context: bool = True
) -> Dict[str, Any]:
    """
    Hàm thực thi chính của Layer 4: Sinh câu trả lời dựa trên context.

    Args:
        question (str): Câu hỏi của người dùng.
        relevant_docs (List[Dict]): Danh sách tài liệu liên quan đã qua lọc CRAG.
        has_context (bool): Cờ báo hiệu có context hay không từ Layer 3.

    Returns:
        Dict[str, Any]: {
            "answer": str,              # Nội dung câu trả lời
            "sources": List[Dict],      # Danh sách metadata nguồn trích dẫn
            "has_context": bool         # True/False
        }
    """
    # 1. Kịch bản: Không tìm thấy tài liệu phù hợp (Out of Scope)
    if not has_context or not relevant_docs:
        return {
            "answer": OUT_OF_CONTEXT_ANSWER,
            "sources": [],
            "has_context": False,
        }

    # 2. Kịch bản: Có tài liệu tham khảo -> Gọi LLM sinh câu trả lời
    prompt = build_generation_prompt(question, relevant_docs)

    try:
        model = genai.GenerativeModel(
            model_name=MAIN_MODEL_NAME,
            generation_config={
                "temperature": 0.2,       # Nhiệt độ thấp đảm bảo bám sát sự thật
                "max_output_tokens": 1024, # Đủ dài cho câu trả lời chi tiết
                "top_p": 0.8,
            }
        )
        response = model.generate_content(prompt)
        answer_text = response.text.strip()

    except Exception as e:
        print(f"⚠️ [Layer 4 Generator] Lỗi khi gọi Gemini: {e}")
        answer_text = (
            "Xin lỗi bạn, hệ thống AI tạm thời gặp sự cố khi xử lý câu trả lời. "
            "Tuy nhiên, tài liệu liên quan đã được tìm thấy, bạn có thể tham khảo mục nguồn bên dưới."
        )

    # 3. Chuẩn hóa format `sources` đúng chuẩn với Java/Frontend DTO
    sources = [
        {
            "id": doc.get("id", f"src_{i}"),
            "category": doc.get("metadata", {}).get("category", "Chung"),
            "question": doc.get("metadata", {}).get("question", ""),
            "similarity": float(doc.get("similarity", 0.0)),
        }
        for i, doc in enumerate(relevant_docs)
    ]

    return {
        "answer": answer_text,
        "sources": sources,
        "has_context": True,
    }


# ── TEST NHANH LAYER 4 ───────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 70)
    print("🧪 KIỂM THỬ LAYER 4 — GENERATOR")
    print("=" * 70)

    # Giả lập tài liệu relevant từ Layer 3
    mock_docs = [
        {
            "id": "sec_01",
            "content": (
                "ChatMessageE2E sử dụng cơ chế bắt tay 4 lớp (4-Layer Handshake) trước khi nhắn tin:\n"
                "1. Bước 1: Trao đổi khóa công khai ECDH (X25519) giữa Alice và Bob.\n"
                "2. Bước 2: Hai bên tính toán Secret Key chung bằng hàm HKDF-SHA256.\n"
                "3. Bước 3: Xác thực tính toàn vẹn danh tính bằng chữ ký Ed25519.\n"
                "4. Bước 4: Thiết lập phiên chat và bắt đầu mã hóa từng tin nhắn bằng AES-256-GCM."
            ),
            "metadata": {
                "category": "Bảo mật & Bắt tay",
                "question": "Quy trình bắt tay 4 lớp diễn ra như thế nào?"
            },
            "similarity": 0.9412
        }
    ]

    # Test 1: Có context
    print("\n--- TEST 1: CÂU HỎI CÓ TÀI LIỆU LIÊN QUAN ---")
    q1 = "Bắt tay 4 lớp trong ChatMessage hoạt động thế nào?"
    print(f"❓ Câu hỏi: {q1}")
    res1 = generate_answer(q1, mock_docs, has_context=True)
    print(f"\n🤖 Câu trả lời:\n{res1['answer']}")
    print(f"\n📚 Nguồn tham khảo ({len(res1['sources'])} nguồn):")
    for s in res1["sources"]:
        print(f"   • [{s['category']}] {s['question']} (Độ liên quan: {s['similarity']:.1%})")

    # Test 2: Ngoài phạm vi (Out of context)
    print("\n--- TEST 2: CÂU HỎI NGOÀI PHẠM VI (KHÔNG CÓ CONTEXT) ---")
    q2 = "Hôm nay chứng khoán tăng hay giảm?"
    print(f"❓ Câu hỏi: {q2}")
    res2 = generate_answer(q2, [], has_context=False)
    print(f"\n🤖 Câu trả lời:\n{res2['answer']}")
    print(f"   has_context: {res2['has_context']}")

    print("\n" + "=" * 70)
