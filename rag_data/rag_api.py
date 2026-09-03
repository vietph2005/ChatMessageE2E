"""
FastAPI RAG Microservice — ChatMessageE2E
==========================================
Chạy độc lập tại cổng 8000, nạp ChromaDB vào RAM một lần khi khởi động
và phục vụ endpoint /ask cho Java backend.
Tuân thủ tiêu chuẩn Logging có cấu trúc (Constitution Principle IV).
"""

import logging
from contextlib import asynccontextmanager
from typing import List, Optional
from pathlib import Path
import sys

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

# ── Cấu hình Structured Logging theo Constitution Principle IV ──────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("rag_api")

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
    logger.info("Initializing RAG microservice and loading ChromaDB into memory...")
    try:
        app.state.collection = get_collection()
        doc_count = app.state.collection.count()
        logger.info("ChromaDB initialized successfully with %d FAQ documents", doc_count)
    except Exception as e:
        logger.error("Failed to connect to ChromaDB: %s", str(e), exc_info=True)
        app.state.collection = None
    yield
    logger.info("RAG microservice is shutting down")


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
        logger.warning("Health check failed: ChromaDB is unavailable")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ChromaDB chưa được khởi tạo hoặc không khả dụng"
        )
    count = collection.count()
    logger.debug("Health check passed: %d documents available", count)
    return HealthResponse(
        status="ok",
        collection_count=count,
    )


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    """
    Nhận câu hỏi từ backend, chạy pipeline RAG và trả về câu trả lời.
    """
    collection = getattr(app.state, "collection", None)
    if collection is None:
        logger.error("Rejected /ask request: ChromaDB is not ready")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dịch vụ cơ sở dữ liệu tri thức tạm thời không sẵn sàng"
        )

    logger.info("Processing /ask query (chars=%d)", len(request.question))
    try:
        result = run_rag_answer(
            question=request.question,
            collection=collection,
            verbose=False,
        )

        sources_count = len(result.get("sources", []))
        has_context = result.get("has_context", False)
        logger.info(
            "RAG completed successfully: %d sources retrieved, has_context=%s",
            sources_count,
            has_context,
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
            has_context=has_context,
        )
    except Exception as e:
        logger.error("Error occurred while processing RAG pipeline: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Lỗi khi xử lý RAG: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn server on http://0.0.0.0:8000")
    uvicorn.run(
        "rag_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(BASE_DIR)],
        app_dir=str(BASE_DIR),
    )

