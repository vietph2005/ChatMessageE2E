import sys
from pathlib import Path

# Cấu hình UTF-8 cho console Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from config import (
    GOOGLE_API_KEY,
    GROK_API_KEY,
    FAST_MODEL_NAME,
    GROK_MODEL_NAME,
    call_grok_chat,
    is_grok_available,
    init_gemini,
)
import google.generativeai as genai

print("=" * 65)
print("🔍 KIỂM TRA TRẠNG THÁI KẾT NỐI API KEYS (GEMINI & GROK)")
print("=" * 65)

# 1. KIỂM TRA GOOGLE GEMINI KEY
print("\n[1] Kiểm tra Google Gemini API:")
if not GOOGLE_API_KEY or GOOGLE_API_KEY.startswith("your_"):
    print("  ❌ GOOGLE_API_KEY chưa được điền trong rag_data/.env")
    print("     (Hiện tại file .env vẫn lưu giá trị mẫu: 'your_google_gemini_api_key_here')")
    print("     👉 Nếu bạn vừa dán key vào .env, hãy bấm Ctrl + S trong IDE để lưu file!")
else:
    masked_key = GOOGLE_API_KEY[:6] + "..." + GOOGLE_API_KEY[-4:]
    print(f"  🔑 Phát hiện key: {masked_key}")
    try:
        init_gemini()
        model = genai.GenerativeModel(FAST_MODEL_NAME)
        res = model.generate_content("Trả lời ngắn gọn đúng 1 từ: OK")
        print(f"  ✅ Kết nối Gemini ({FAST_MODEL_NAME}) THÀNH CÔNG!")
        print(f"     Phản hồi từ Gemini: \"{res.text.strip()}\"")
    except Exception as e:
        print(f"  ❌ Lỗi khi gọi Gemini: {e}")

# 2. KIỂM TRA XAI GROK KEY
print("\n[2] Kiểm tra xAI Grok API:")
if not is_grok_available():
    print("  ⚪ GROK_API_KEY chưa được cấu hình (hoặc vẫn là giá trị mẫu).")
    print("     (Layer 5 sẽ tự động chạy ở chế độ Fallback dùng Gemini)")
else:
    masked_grok = GROK_API_KEY[:6] + "..." + GROK_API_KEY[-4:]
    print(f"  🔑 Phát hiện key: {masked_grok}")
    try:
        res_grok = call_grok_chat(
            prompt="Trả lời đúng 1 từ: OK",
            system_instruction="Trả lời siêu ngắn.",
            max_tokens=10
        )
        if res_grok:
            print(f"  ✅ Kết nối Grok ({GROK_MODEL_NAME}) THÀNH CÔNG!")
            print(f"     Phản hồi từ Grok: \"{res_grok}\"")
        else:
            print("  ❌ Grok không phản hồi hoặc trả về rỗng.")
    except Exception as e:
        print(f"  ❌ Lỗi khi gọi Grok: {e}")

print("\n" + "=" * 65)
