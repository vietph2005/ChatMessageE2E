import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Đảm bảo in tiếng Việt và Emoji mượt mà trên console Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# NOTE: google.generativeai sẽ deprecated. Cân nâng lên google.genai khi API ổn định.
import google.generativeai as genai

# Đường dẫn thư mục gốc rag_data
BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    load_dotenv()

# Cấu hình API Key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# Cấu hình xAI Grok / Groq LPU API Key
GROK_API_KEY = os.getenv("GROK_API_KEY", os.getenv("XAI_API_KEY", ""))

# Tự động điều chỉnh endpoint & model theo nhà cung cấp (xAI hay Groq)
if GROK_API_KEY.startswith("gsk_"):
    # Người dùng dùng Groq Cloud (LPU siêu tốc)
    DEFAULT_GROK_MODEL = "qwen/qwen3.8-27b"
    DEFAULT_GROK_URL = "https://api.groq.com/openai/v1"
else:
    # Mặc định là xAI Grok
    DEFAULT_GROK_MODEL = "grok-beta"
    DEFAULT_GROK_URL = "https://api.x.ai/v1"

GROK_MODEL_NAME = os.getenv("GROK_MODEL", DEFAULT_GROK_MODEL)
GROK_API_BASE_URL = os.getenv("GROK_API_BASE_URL", DEFAULT_GROK_URL)

# Tên mô hình Gemini (Cập nhật phiên bản tương thích với API key của bạn)
FAST_MODEL_NAME = os.getenv("FAST_MODEL", "gemini-3.6-flash")
MAIN_MODEL_NAME = os.getenv("MAIN_MODEL", "gemini-3.6-flash")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")

# Đường dẫn ChromaDB
CHROMA_DB_DIR = BASE_DIR / "vector_db" / "chroma_db"
COLLECTION_NAME = "chatmessage_faq"

# ── Proposition Indexing (Dual Storage) ──────────────────────────────
# ByteStore: lưu full parent chunk, liên kết với ChromaDB qua doc_id
DOCSTORE_DIR = BASE_DIR / "docstore"
# Số mệnh đề tối đa sinh ra từ mỗi parent chunk
PROPOSITION_MAX_PER_CHUNK = 8
# Bỏ qua proposition quá ngắn (< N từ) — thường là câu không đủ nghĩa
PROPOSITION_MIN_WORDS = 8
# Số propositions embed mỗi batch (tránh rate limit Gemini API)
PROPOSITION_BATCH_SIZE = 5


def init_gemini():
    """Khởi tạo Google Gemini Client."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key.startswith("your_"):
        print("⚠️ CẢNH BÁO: Chưa cấu hình GOOGLE_API_KEY hợp lệ trong rag_data/.env")
    genai.configure(api_key=api_key)
    return genai


def is_grok_available() -> bool:
    """Kiểm tra xem API key của Grok/Groq đã được cấu hình hay chưa."""
    return bool(GROK_API_KEY and not GROK_API_KEY.startswith("your_"))


def call_grok_chat(
    prompt: str,
    system_instruction: str = "",
    temperature: float = 0.0,
    max_tokens: int = 200,
    timeout: float = 15.0
):
    """
    Gọi Grok (xAI) hoặc Groq (LPU) Chat Completion API (chuẩn tương thích OpenAI REST).
    Trả về chuỗi kết quả hoặc None nếu lỗi.
    """
    import httpx

    if not is_grok_available():
        return None

    url = f"{GROK_API_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json",
    }

    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": prompt})

    # Nếu dùng Groq key mà model đang để grok-beta thì đổi sang model hợp lệ của Groq
    model_to_use = GROK_MODEL_NAME
    if GROK_API_KEY.startswith("gsk_") and "grok" in model_to_use.lower():
        model_to_use = "qwen/qwen3.8-27b"

    payload = {
        "model": model_to_use,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"⚠️ [Verifier Model API Error]: {e}")
        return None


