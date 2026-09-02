"""
FastAPI RAG Microservice — ChatMessageE2E
==========================================
Chạy độc lập tại cổng 8000, nạp ChromaDB vào RAM một lần khi khởi động
và phục vụ endpoint /ask cho Java backend.
"""

from contextlib import asynccontextmanager
from typing import List, Optional
from pathlib import Path
import sys

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

# Thêm thư mục chứa module hiện tại vào sys.path để import rag_online
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from rag_online import get_collection, answer as run_rag_answer


# ── Pydantic Models ──────────────────────────────────────────────────────────

class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000, description="Câu hỏi người dùng")


class SourceItem(BaseModel):
    id: str
    category: str
    question: str
    similarity: float


class AskResponse(BaseModel):
    answer: str
    sources: List[SourceItem] = []
    has_context: bool


class HealthResponse(BaseModel):
    status: str
    collection_count: int


# ── Lifespan Management (Load ChromaDB một lần duy nhất) ──────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Nạp ChromaDB vào RAM khi khởi động microservice."""
    try:
        app.state.collection = get_collection()
        print(f"[FASTAPI] ✅ ChromaDB sẵn sàng với {app.state.collection.count()} tài liệu")
    except Exception as e:
        print(f"[FASTAPI] ❌ Lỗi kết nối ChromaDB: {e}")
        app.state.collection = None
    yield
    print("[FASTAPI] Dừng dịch vụ RAG microservice")


# ── Khởi tạo App ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="ChatMessage RAG Microservice",
    description="Microservice bọc ChromaDB & Gemini RAG pipeline cho ChatMessage",
    version="1.0.0",
    lifespan=lifespan,
)


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Kiểm tra tình trạng hoạt động của service và ChromaDB."""
    collection = getattr(app.state, "collection", None)
    if collection is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ChromaDB chưa được khởi tạo hoặc không khả dụng"
        )
    return HealthResponse(
        status="ok",
        collection_count=collection.count(),
    )


@app.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest):
    """
    Nhận câu hỏi từ backend, chạy pipeline RAG và trả về câu trả lời.
    """
    collection = getattr(app.state, "collection", None)
    if collection is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dịch vụ cơ sở dữ liệu tri thức tạm thời không sẵn sàng"
        )

    try:
        result = run_rag_answer(
            question=request.question,
            collection=collection,
            verbose=False,
        )
        return AskResponse(
            answer=result["answer"],
            sources=[
                SourceItem(
                    id=s["id"],
                    category=s["category"],
                    question=s["question"],
                    similarity=s["similarity"],
                )
                for s in result.get("sources", [])
            ],
            has_context=result.get("has_context", False),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Lỗi khi xử lý RAG: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("rag_api:app", host="0.0.0.0", port=8000, reload=True)
