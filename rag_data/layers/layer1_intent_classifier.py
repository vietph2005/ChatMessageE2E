"""
Layer 1 — Intent Classifier (Adaptive RAG)
===========================================
Mục đích:
  - Phân loại câu hỏi của người dùng thành:
      1. "small_talk": Trò chuyện thông thường (chào hỏi, cảm ơn, làm quen, thời tiết...)
         -> Trả lời trực tiếp ngay lập tức, BYPASS toàn bộ RAG (tiết kiệm chi phí, latency < 0.3s).
      2. "app_question": Câu hỏi về ứng dụng ChatMessage (tính năng, bảo mật E2EE, lỗi, tài khoản...)
         -> Chuyển tiếp vào Layer 2 (Query Rewriter).
"""

import sys
from pathlib import Path
from typing import Dict, Any

# Đảm bảo import được config từ thư mục cha rag_data
CURRENT_DIR = Path(__file__).resolve().parent
PARENT_DIR = CURRENT_DIR.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

from config import init_gemini, FAST_MODEL_NAME, call_grok_chat, is_grok_available
import google.generativeai as genai

# Khởi tạo Gemini
init_gemini()

# Danh sách một số từ khóa xã giao phổ biến (Rule-based Fast Path để giảm latency về 0ms)
FAST_SMALL_TALK_KEYWORDS = {
    "chào", "hello", "hi", "xin chào", "chào bạn", "hey",
    "cảm ơn", "thanks", "thank you", "cảm ơn bạn",
    "tạm biệt", "bye", "goodbye", "bạn là ai", "bạn tên gì"
}


def is_obvious_small_talk(question: str) -> bool:
    """Kiểm tra nhanh bằng rule-based để không cần gọi LLM nếu chỉ là câu chào đơn giản."""
    normalized = question.strip().strip("!?.,~ ").lower()
    return normalized in FAST_SMALL_TALK_KEYWORDS


def classify_intent(question: str) -> Dict[str, Any]:
    """
    Phân loại ý định người dùng (Intent Classification).

    Args:
        question (str): Câu hỏi của người dùng.

    Returns:
        Dict[str, Any]: {
            "intent": "small_talk" | "app_question",
            "is_small_talk": bool,
            "direct_reply": Optional[str] # Có nếu là small_talk
        }
    """
    cleaned_q = question.strip()
    if not cleaned_q:
        return {
            "intent": "small_talk",
            "is_small_talk": True,
            "direct_reply": "Xin chào! Tôi có thể giúp gì cho bạn về ứng dụng ChatMessage?"
        }

    # 1. Fast Path: Rule-based
    if is_obvious_small_talk(cleaned_q):
        return {
            "intent": "small_talk",
            "is_small_talk": True,
            "direct_reply": _generate_direct_reply(cleaned_q)
        }

    # 2. LLM Path: Adaptive Classifier
    prompt = f"""Bạn là bộ phân loại ý định (Intent Classifier) cho ứng dụng nhắn tin ChatMessageE2E.

Nhiệm vụ: Phân loại câu hỏi của người dùng vào 1 trong 2 nhóm:
- "small_talk": Câu chào hỏi, cảm ơn, khen chê, trò chuyện xã giao hoặc không liên quan đến ứng dụng.
- "app_question": Câu hỏi về tính năng, bảo mật E2EE, bắt tay 4 lớp, đăng nhập Google, lỗi kỹ thuật, tài khoản hoặc cách dùng ChatMessage (kể cả khi không nhắc rõ từ ChatMessage).

Câu hỏi: "{cleaned_q}"

Chỉ trả lời duy nhất một từ: "small_talk" hoặc "app_question"."""

    # Ưu tiên sử dụng Grok Cloud siêu tốc
    if is_grok_available():
        res_grok = call_grok_chat(prompt=prompt, temperature=0.0, max_tokens=10)
        if res_grok:
            verdict = res_grok.strip().lower()
            is_small_talk = "small_talk" in verdict
            if is_small_talk:
                return {
                    "intent": "small_talk",
                    "is_small_talk": True,
                    "direct_reply": _generate_direct_reply(cleaned_q)
                }
            else:
                return {
                    "intent": "app_question",
                    "is_small_talk": False,
                    "direct_reply": None
                }

    # Fallback sang Gemini
    try:
        model = genai.GenerativeModel(FAST_MODEL_NAME)
        response = model.generate_content(prompt)
        verdict = response.text.strip().lower()
        is_small_talk = "small_talk" in verdict

        if is_small_talk:
            return {
                "intent": "small_talk",
                "is_small_talk": True,
                "direct_reply": _generate_direct_reply(cleaned_q)
            }
        else:
            return {
                "intent": "app_question",
                "is_small_talk": False,
                "direct_reply": None
            }

    except Exception as e:
        # Nếu LLM lỗi, fallback an toàn chuyển sang RAG để không bỏ sót câu hỏi của user
        print(f"⚠️ [Layer 1] Classifier fallback to app_question do lỗi: {e}")
        return {
            "intent": "app_question",
            "is_small_talk": False,
            "direct_reply": None
        }


def _generate_direct_reply(question: str) -> str:
    """Sinh câu trả lời thân thiện cho small talk."""
    prompt = f"""Bạn là trợ lý AI hỗ trợ kỹ thuật của ChatMessageE2E.
Hãy trả lời câu giao tiếp sau một cách ngắn gọn, thân thiện, lịch sự và gợi mở người dùng hỏi về ứng dụng ChatMessage:
User: "{question}"
Bot:"""

    if is_grok_available():
        res = call_grok_chat(prompt=prompt, temperature=0.3, max_tokens=150)
        if res:
            return res.strip()

    try:
        model = genai.GenerativeModel(FAST_MODEL_NAME)
        res = model.generate_content(prompt)
        return res.text.strip()
    except Exception:
        return "Xin chào! Tôi là trợ lý ảo hỗ trợ ứng dụng ChatMessage. Tôi có thể giúp gì cho bạn hôm nay?"


