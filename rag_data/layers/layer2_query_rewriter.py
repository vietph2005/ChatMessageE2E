"""
Layer 2 — Query Rewriter với kỹ thuật RAG Fusion (Multi-Query Generation)
========================================================================
Mục đích:
  - Thay vì chỉ sinh 1 câu truy vấn duy nhất, RAG Fusion sinh ra NHIỀU CÂU HỎI (3-4 góc nhìn khác nhau)
    từ câu hỏi gốc của người dùng.
  - Mỗi góc nhìn nhắm vào một khía cạnh kỹ thuật cụ thể của ChatMessageE2E:
      + Góc nhìn nguyên nhân / lỗi sự cố (Troubleshooting)
      + Góc nhìn khái niệm / kiến trúc bảo mật (Architecture / E2EE / OAuth2)
      + Góc nhìn quy trình / thao tác sử dụng (Step-by-step Guide)
  - Danh sách này bao gồm cả CÂU HỎI GỐC để đảm bảo không mất ý ban đầu.
  - Ở Layer 3, các câu hỏi này sẽ được search song song và hợp nhất bằng thuật toán:
    Reciprocal Rank Fusion (RRF).
"""

import sys
import json
from pathlib import Path
from typing import List

# Đảm bảo import được config từ thư mục cha rag_data
CURRENT_DIR = Path(__file__).resolve().parent
PARENT_DIR = CURRENT_DIR.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

from config import init_gemini, FAST_MODEL_NAME
import google.generativeai as genai

# Khởi tạo Gemini
init_gemini()

SYSTEM_RAG_FUSION_PROMPT = """Bạn là chuyên gia tối ưu câu truy vấn RAG Fusion cho hệ thống ChatMessageE2E.

Hệ sinh thái kiến thức ChatMessageE2E gồm:
1. Đăng nhập Google OAuth2, cấp JWT, hồ sơ cá nhân.
2. Mã hóa đầu cuối (E2EE): Trao đổi khóa ECDH, mã hóa đối xứng AES-256-GCM, quản lý Key Bundle.
3. Bắt tay 4 lớp (4-Layer Handshake): Khởi tạo phiên bảo mật giữa 2 người dùng qua WebSocket.
4. Gửi nhận tin nhắn, file, hình ảnh đa phương tiện được mã hóa E2EE.
5. Chặn/Bỏ chặn kết nối (Block/Unblock), thu hồi phiên và xử lý lỗi lệch khóa.

NHIỆM VỤ:
Từ câu hỏi của người dùng, hãy sinh ra chính xác {num_queries} câu truy vấn tìm kiếm khác nhau (các góc nhìn bổ trợ: nguyên nhân, cơ chế kỹ thuật, quy trình thao tác) để phục vụ tìm kiếm đa hướng (RAG Fusion).

QUY TẮC:
- Các câu hỏi phải liên quan chặt chẽ đến ứng dụng ChatMessageE2E.
- Các câu hỏi bổ trợ lẫn nhau, tiếp cận từ các khía cạnh khác nhau (khái niệm, giải pháp, cơ chế).
- Định dạng ĐẦU RA BẮT BUỘC là một JSON Array chứa danh sách các chuỗi, ví dụ:
["câu 1", "câu 2", "câu 3"]
- KHÔNG thêm bất kỳ giải thích, lời dẫn hay markdown code block nào khác."""


def generate_rag_fusion_queries(question: str, num_queries: int = 3) -> List[str]:
    """
    Sinh đa truy vấn theo phương pháp RAG Fusion.

    Args:
        question (str): Câu hỏi gốc của người dùng.
        num_queries (int): Số lượng câu hỏi biến thể cần sinh (mặc định: 3).

    Returns:
        List[str]: Danh sách gồm câu hỏi gốc + các biến thể bổ trợ.
    """
    cleaned_q = question.strip()
    if not cleaned_q:
        return [cleaned_q]

    prompt = f"""{SYSTEM_RAG_FUSION_PROMPT.format(num_queries=num_queries)}

Câu hỏi gốc của người dùng: "{cleaned_q}"

Danh sách JSON:"""

    try:
        model = genai.GenerativeModel(
            model_name=FAST_MODEL_NAME,
            generation_config={
                "temperature": 0.4,   # Độ biến thiên vừa phải để tạo góc nhìn phong phú
                "max_output_tokens": 300,
            }
        )
        response = model.generate_content(prompt)
        raw_text = response.text.strip()

        # Làm sạch markdown nếu LLM bọc trong ```json
        if "```" in raw_text:
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()

        parsed_queries = json.loads(raw_text)
        if isinstance(parsed_queries, list):
            # Luôn đưa câu hỏi gốc vào đầu danh sách, sau đó là các biến thể (loại trừ trùng lặp)
            fusion_queries = [cleaned_q]
            for q in parsed_queries:
                q_clean = str(q).strip().strip('"').strip("'")
                if q_clean and q_clean.lower() != cleaned_q.lower() and q_clean not in fusion_queries:
                    fusion_queries.append(q_clean)
            return fusion_queries

    except Exception as e:
        print(f"⚠️ [Layer 2 RAG Fusion] Lỗi parse LLM: {e}. Fallback sử dụng câu hỏi gốc.")

    # Fallback an toàn nếu LLM lỗi: trả về câu hỏi gốc
    return [cleaned_q]


def rewrite_query(question: str) -> str:
    """Hàm tiện ích tương thích ngược nếu cần lấy 1 câu query tiêu biểu."""
    queries = generate_rag_fusion_queries(question, num_queries=2)
    return queries[1] if len(queries) > 1 else queries[0]


# ── TEST NHANH LAYER 2 VỚI RAG FUSION ────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 70)
    print("🧪 KIỂM THỬ LAYER 2 — RAG FUSION (MULTI-QUERY GENERATION)")
    print("=" * 70)

    test_queries = [
        "đăng nhập bị lỗi",
        "mã hóa tin nhắn thế nào",
        "bắt tay 4 lớp là gì",
        "làm sao để chặn một ai đó"
    ]

    for q in test_queries:
        print(f"\n❓ [CÂU HỎI GỐC]: \"{q}\"")
        queries = generate_rag_fusion_queries(q, num_queries=3)
        print(f"🚀 [RAG FUSION QUERIES] ({len(queries)} biến thể):")
        for idx, sub_q in enumerate(queries, 1):
            tag = "GỐC" if idx == 1 else f"GÓC NHÌN {idx-1}"
            print(f"   {idx}. [{tag}]: \"{sub_q}\"")

    print("\n" + "=" * 70)

