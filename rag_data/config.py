import os
from pathlib import Path
from dotenv import load_dotenv
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

# Tên mô hình
FAST_MODEL_NAME = os.getenv("FAST_MODEL", "gemini-1.5-flash")
MAIN_MODEL_NAME = os.getenv("MAIN_MODEL", "gemini-1.5-flash")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "models/text-embedding-004")

# Đường dẫn ChromaDB
CHROMA_DB_DIR = BASE_DIR / "vector_db" / "chroma_db"
COLLECTION_NAME = "chatmessage_faq"


def init_gemini():
    """Khởi tạo Google Gemini Client."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key.startswith("your_"):
        print("⚠️ CẢNH BÁO: Chưa cấu hình GOOGLE_API_KEY hợp lệ trong rag_data/.env")
    genai.configure(api_key=api_key)
    return genai
