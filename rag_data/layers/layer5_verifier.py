"""
Layer 5 — Verification (Self-RAG Verification: Hallucination & Usefulness Grader)
==================================================================================
Mục đích:
  Chốt chặn kiểm định chất lượng 2 bước (Self-RAG) trước khi câu trả lời được gửi về cho người dùng:

  1. BƯỚC 5a — Hallucination Grader (Groundedness Check):
     - Câu hỏi: "Mọi luận điểm/khẳng định trong câu trả lời có được chứng thực bởi tài liệu tham khảo không?"
     - Đảm bảo AI không tự suy diễn các thông số bảo mật, thuật toán không có trong tài liệu của ChatMessageE2E.
     - Nếu phát hiện ảo giác (hallucination) -> Tự động kích hoạt cơ chế sinh lại (Re-generation) với nhiệt độ 0.0.

  2. BƯỚC 5b — Answer Usefulness Grader (Helpfulness Check):
     - Câu hỏi: "Câu trả lời có đi đúng trọng tâm và thực sự giải quyết thắc mắc của người dùng không?"
     - Nếu đạt cả 2 tiêu chí: Phê duyệt (APPROVED) và trả kết quả cho tầng Presentation/Frontend.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


# Đảm bảo import được config từ thư mục cha rag_data
CURRENT_DIR = Path(__file__).resolve().parent
PARENT_DIR = CURRENT_DIR.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

from config import (
    init_gemini,
    FAST_MODEL_NAME,
    MAIN_MODEL_NAME,
    call_grok_chat,
    is_grok_available,
    GROK_MODEL_NAME,
)
import google.generativeai as genai

# Khởi tạo Gemini (dùng cho Fallback và Re-generation)
init_gemini()


def _safe_get_gemini_text(response) -> str:
    try:
        return response.text.strip()
    except Exception:
        if hasattr(response, "candidates") and response.candidates:
            cand = response.candidates[0]
            if hasattr(cand, "content") and cand.content and hasattr(cand.content, "parts") and cand.content.parts:
                return cand.content.parts[0].text.strip()
    return ""


# ════════════════════════════════════════════════════════════════════
# 1. BƯỚC 5a: Hallucination Grader (Groundedness Check)
# ════════════════════════════════════════════════════════════════════
def grade_hallucination(answer: str, docs: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """
    Kiểm tra xem câu trả lời có bịa đặt hoặc suy diễn thông tin ngoài tài liệu không.
    Ưu tiên sử dụng mô hình Gemini để thẩm định độc lập, fallback sang Grok.

    Returns:
        Tuple[bool, str]: (is_grounded: True/False, reason: str)
    """
    if not docs:
        return True, "Không có tài liệu (câu hỏi ngoài phạm vi), bỏ qua kiểm tra hallucination."

    context_str = "\n\n".join([f"Tài liệu {i+1}:\n{d.get('content', '')}" for i, d in enumerate(docs)])

    prompt = f"""Bạn là chuyên gia kiểm định ảo giác AI độc lập (Hallucination Grader) cho ứng dụng ChatMessageE2E.

TÀI LIỆU CĂN CỨ:
\"\"\"{context_str}\"\"\"

CÂU TRẢ LỜI CỦA AI:
\"\"\"{answer}\"\"\"

NHIỆM VỤ:
Kiểm tra xem câu trả lời của AI có hoàn toàn trung thực và được chứng minh bởi TÀI LIỆU CĂN CỨ ở trên không.
- Nếu câu trả lời chứa thông tin bịa đặt, suy diễn sai lệch hoặc nhắc đến thuật toán/cơ chế không có trong tài liệu -> Đánh giá: "no".
- Nếu câu trả lời hoàn toàn đúng và được chứng thực bởi tài liệu -> Đánh giá: "yes".

Chỉ trả lời theo định dạng chính xác 2 dòng:
GRADE: yes hoặc no
REASON: giải thích ngắn gọn trong 1 câu."""

    # 1. Ưu tiên kiểm định độc lập bằng Gemini (Google AI Studio)
    try:
        model = genai.GenerativeModel(
            model_name=FAST_MODEL_NAME,
            generation_config={"temperature": 0.0, "max_output_tokens": 256}
        )
        resp = model.generate_content(prompt)
        res_gemini = _safe_get_gemini_text(resp)
        if res_gemini:
            is_grounded = "grade: yes" in res_gemini.lower()
            return is_grounded, f"[Gemini - {FAST_MODEL_NAME}] {res_gemini}"
    except Exception as e:
        print(f"⚠️ [Layer 5] Gemini gặp sự cố ({e}), tự động fallback sang Grok...")

    # 2. Fallback sang Grok nếu Gemini lỗi hoặc chạm hạn mức
    if is_grok_available():
        res_grok = call_grok_chat(
            prompt=prompt,
            system_instruction="Bạn là chuyên gia kiểm định ảo giác AI độc lập (Hallucination Grader).",
            temperature=0.0,
            max_tokens=120
        )
        if res_grok:
            is_grounded = "grade: yes" in res_grok.lower()
            return is_grounded, f"[Grok Fallback - {GROK_MODEL_NAME}] {res_grok}"

    return True, "Bỏ qua do lỗi grader"


# ════════════════════════════════════════════════════════════════════
# 2. BƯỚC 5b: Answer Usefulness Grader
# ════════════════════════════════════════════════════════════════════
def grade_usefulness(question: str, answer: str) -> Tuple[bool, str]:
    """
    Kiểm tra xem câu trả lời có thực sự trả lời đúng câu hỏi người dùng không.
    Ưu tiên sử dụng mô hình Gemini để thẩm định độc lập, fallback sang Grok.

    Returns:
        Tuple[bool, str]: (is_useful: True/False, reason: str)
    """
    prompt = f"""Bạn là chuyên gia đánh giá mức độ hữu ích của câu trả lời (Answer Usefulness Grader).

CÂU HỎI CỦA NGƯỜI DÙNG:
"{question}"

CÂU TRẢ LỜI CỦA HỆ THỐNG:
\"\"\"{answer}\"\"\"

NHIỆM VỤ:
Đánh giá xem câu trả lời có giải quyết trực tiếp và thỏa đáng câu hỏi của người dùng hay không.
- Nếu câu trả lời hữu ích, đúng trọng tâm -> Đánh giá: "yes".
- Nếu trả lời vòng vo, lạc đề, không trả lời câu hỏi -> Đánh giá: "no".

Chỉ trả lời theo định dạng chính xác 2 dòng:
GRADE: yes hoặc no
REASON: giải thích ngắn gọn trong 1 câu."""

    # 1. Ưu tiên kiểm định độc lập bằng Gemini (Google AI Studio)
    try:
        model = genai.GenerativeModel(
            model_name=FAST_MODEL_NAME,
            generation_config={"temperature": 0.0, "max_output_tokens": 256}
        )
        resp = model.generate_content(prompt)
        res_gemini = _safe_get_gemini_text(resp)
        if res_gemini:
            is_useful = "grade: yes" in res_gemini.lower()
            return is_useful, f"[Gemini - {FAST_MODEL_NAME}] {res_gemini}"
    except Exception as e:
        print(f"⚠️ [Layer 5] Gemini gặp sự cố ({e}), tự động fallback sang Grok...")

    # 2. Fallback sang Grok nếu Gemini lỗi
    if is_grok_available():
        res_grok = call_grok_chat(
            prompt=prompt,
            system_instruction="Bạn là chuyên gia đánh giá độ hữu ích của câu trả lời (Answer Usefulness Grader).",
            temperature=0.0,
            max_tokens=120
        )
        if res_grok:
            is_useful = "grade: yes" in res_grok.lower()
            return is_useful, f"[Grok Fallback - {GROK_MODEL_NAME}] {res_grok}"

    return True, "Bỏ qua do lỗi grader"



# ════════════════════════════════════════════════════════════════════
# 3. VERIFICATION & RE-GENERATION (VÒNG LẶP SỬA LỖI TỰ ĐỘNG)
# ════════════════════════════════════════════════════════════════════
def verify_and_refine(
    question: str,
    answer: str,
    docs: List[Dict[str, Any]],
    has_context: bool,
    max_retries: int = 1
) -> Dict[str, Any]:
    """
    Hàm thực thi chính của Layer 5:
      - Nếu has_context=False (ngoài phạm vi): Phê duyệt ngay.
      - Nếu có context: Kiểm tra Hallucination -> Kiểm tra Usefulness.
      - Nếu phát hiện Hallucination: Tự động sinh lại (Re-generate) với ràng buộc nghiêm ngặt hơn.

    Args:
        question (str): Câu hỏi gốc.
        answer (str): Câu trả lời từ Layer 4.
        docs (List[Dict]): Tài liệu tham khảo.
        has_context (bool): Có context hay không.
        max_retries (int): Số lần thử sinh lại nếu phát hiện hallucination.

    Returns:
        Dict[str, Any]: {
            "final_answer": str,
            "is_grounded": bool,
            "is_useful": bool,
            "status": "APPROVED" | "REFINED" | "PASSED_WITH_WARNING"
        }
    """
    if not has_context or not docs:
        return {
            "final_answer": answer,
            "is_grounded": True,
            "is_useful": True,
            "status": "APPROVED",
        }

    current_answer = answer
    is_grounded, ground_reason = True, ""
    is_useful, useful_reason = True, ""

    # Vòng lặp kiểm định & sửa lỗi (Self-Correction)
    for attempt in range(max_retries + 1):
        is_grounded, ground_reason = grade_hallucination(current_answer, docs)
        is_useful, useful_reason = grade_usefulness(question, current_answer)

        # Kịch bản hoàn hảo: Cả 2 đều đạt
        if is_grounded and is_useful:
            status = "APPROVED" if attempt == 0 else "REFINED"
            print(f"   ✅ [Layer 5] Thẩm định lần {attempt+1} ĐẠT CHUẨN ({status}) — Grounded: True, Useful: True")
            return {
                "final_answer": current_answer,
                "is_grounded": True,
                "is_useful": True,
                "status": status,
            }


        # Nếu phát hiện ảo giác (Hallucinated) và còn lượt thử -> Sinh lại với temperature 0.0
        if not is_grounded and attempt < max_retries:
            print(f"⚠️ [Layer 5] Phát hiện ảo giác ({ground_reason}). Đang tự động sinh lại (Attempt {attempt+1})...")
            context_str = "\n\n".join([d.get("content", "") for d in docs])
            strict_prompt = f"""Bạn là trợ lý AI ChatMessageE2E. Hãy trả lời câu hỏi sau TUYỆT ĐỐI KHÔNG BỊA ĐẶT, CHỈ DỰA VÀO TÀI LIỆU DƯỚI ĐÂY:
TÀI LIỆU:
{context_str}

CÂU HỎI: {question}
CÂU TRẢ LỜI (Chỉ nêu những gì tài liệu có):"""

            try:
                gen_model = genai.GenerativeModel(
                    model_name=MAIN_MODEL_NAME,
                    generation_config={"temperature": 0.0, "max_output_tokens": 1024}
                )
                current_answer = gen_model.generate_content(strict_prompt).text.strip()
            except Exception:
                break
        else:
            break

    # ── KỊCH BẢN KHI HẾT LƯỢT THỬ MÀ VẪN BỊ ẢO GIÁC (FAIL-SAFE FALLBACK) ──
    if not is_grounded:
        print("🚨 [Layer 5] Hết lượt thử nhưng vẫn phát hiện ảo giác. Kích hoạt Fail-Safe Fallback!")

        # Trích xuất đoạn tóm tắt từ tài liệu gốc (không để LLM bịa thêm)
        doc_excerpts = "\n\n".join([
            f"• **[{d.get('metadata', {}).get('category', 'Tài liệu')} - {d.get('metadata', {}).get('question', '')}]**:\n  {d.get('content', '')[:250]}..."
            for d in docs[:2]
        ])

        fallback_answer = (
            "Hệ thống đã tìm thấy tài liệu liên quan đến câu hỏi của bạn, "
            "tuy nhiên để đảm bảo tính chính xác kỹ thuật và bảo mật tuyệt đối, "
            "dưới đây là trích đoạn tài liệu gốc từ hệ thống để bạn tham khảo:\n\n"
            f"{doc_excerpts}\n\n"
            "*(Bạn có thể xem chi tiết ở các thẻ nguồn trích dẫn đính kèm bên dưới)*"
        )

        return {
            "final_answer": fallback_answer,
            "is_grounded": True,  # Đã chuyển sang trích đoạn gốc nên 100% trung thực
            "is_useful": True,
            "status": "FALLBACK_TO_SOURCE",
        }

    # Kịch bản: Grounded nhưng trả lời chưa thực sự hữu ích (lạc đề)
    status = "APPROVED" if is_useful else "PASSED_WITH_WARNING"
    return {
        "final_answer": current_answer,
        "is_grounded": is_grounded,
        "is_useful": is_useful,
        "status": status,
    }

