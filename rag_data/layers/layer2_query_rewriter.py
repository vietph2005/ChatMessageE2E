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

from config import init_gemini, FAST_MODEL_NAME, is_grok_available, call_grok_chat
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

    raw_text = ""
    # 1. Ưu tiên sử dụng Grok Cloud siêu tốc
    if is_grok_available():
        res_grok = call_grok_chat(
            prompt=prompt,
            system_instruction="Bạn là chuyên gia RAG Fusion tối ưu câu truy vấn. Trả về định dạng JSON array hợp lệ.",
            temperature=0.4,
            max_tokens=500,
        )
        if res_grok:
            raw_text = res_grok.strip()

    # 2. Fallback sang Gemini nếu Grok chưa cấu hình hoặc gặp sự cố
    if not raw_text:
        try:
            model = genai.GenerativeModel(
                model_name=FAST_MODEL_NAME,
                generation_config={
                    "temperature": 0.4,   # Độ biến thiên vừa phải để tạo góc nhìn phong phú
                    "max_output_tokens": 500,
                }
            )
            response = model.generate_content(prompt)
            try:
                raw_text = response.text.strip()
            except Exception:
                if response.candidates and response.candidates[0].content.parts:
                    raw_text = response.candidates[0].content.parts[0].text.strip()
        except Exception as e:
            print(f"⚠️ [Layer 2 RAG Fusion] Lỗi gọi Gemini: {e}")

    try:
        if not raw_text:
            return [cleaned_q]

        # Làm sạch markdown nếu LLM bọc trong ```json ... ```
        clean_json = raw_text
        if "```" in clean_json:
            clean_json = clean_json.split("```")[1].lstrip("json").strip()

        parsed_queries = json.loads(clean_json)

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


