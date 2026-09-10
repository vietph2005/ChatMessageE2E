"""
ChatMessageE2E — RAG Microservice (FastAPI Server)
==================================================
Tích hợp toàn bộ 5 Layers RAG thành REST API hoàn chỉnh:
  • Layer 1: Intent Classifier (Adaptive RAG / Small-talk bypass)
  • Layer 2: Query Rewriter (RAG Fusion / Multi-Query Generation)
  • Layer 3: CRAG Retriever (RRF + Dual Storage + Document Grader)
  • Layer 4: Generator (Grounded Prompting + Sources Formatting)
  • Layer 5: Verifier (Self-RAG: Hallucination Check & Re-generation)

Tương thích 100% với DTO trong backend Java:
  org.example.chat.infrastructure.rag.RagApiClient
"""

import sys
import os
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

# Đảm bảo in tiếng Việt và Emoji mượt mà trên console Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import các thành phần cấu hình và layers
from config import init_gemini, CHROMA_DB_DIR, COLLECTION_NAME
from layers.layer1_intent_classifier import classify_intent
from layers.layer2_query_rewriter import generate_rag_fusion_queries
from layers.layer3_crag_retriever import crag_retrieve_and_grade, get_chroma_collection
from layers.layer4_generator import generate_answer
from layers.layer5_verifier import verify_and_refine

# Khởi tạo Gemini
init_gemini()

# Cache ChromaDB collection
chroma_collection = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Khởi tạo tài nguyên khi server khởi động."""
    global chroma_collection
    print("🚀 [FastAPI] Đang khởi động ChatMessageE2E RAG Service...")
    try:
        chroma_collection = get_chroma_collection()
        total_docs = chroma_collection.count()
        print(f"✅ [FastAPI] Kết nối ChromaDB thành công! Collection: '{COLLECTION_NAME}' ({total_docs} chunks/propositions).")
    except Exception as e:
        print(f"⚠️ [FastAPI] Không thể kết nối ChromaDB lúc khởi động: {e}")
    yield
    print("🛑 [FastAPI] RAG Service đang dừng...")


app = FastAPI(
    title="ChatMessageE2E RAG Microservice",
    description="Microservice 5-Layer Adaptive RAG hỗ trợ Chatbot thông minh cho ChatMessageE2E",
    version="1.0.0",
    lifespan=lifespan
)

# Cấu hình CORS để Spring Boot hoặc Frontend gọi trực tiếp không bị chặn
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ════════════════════════════════════════════════════════════════════
# PYDANTIC SCHEMAS (Tương thích 100% với Spring Boot RagApiClient)
# ════════════════════════════════════════════════════════════════════
class QuestionRequest(BaseModel):
    question: str = Field(..., description="Câu hỏi từ người dùng", example="Mã hóa tin nhắn hoạt động như thế nào?")


class SourceItem(BaseModel):
    id: str
    category: str
    question: str
    similarity: float


class AskResponse(BaseModel):
    answer: str
    sources: List[SourceItem] = []
    has_context: bool = Field(..., alias="has_context")

    class Config:
        populate_by_name = True


# ════════════════════════════════════════════════════════════════════
# PIPELINE ĐIỀU PHỐI 5 LAYERS
# ════════════════════════════════════════════════════════════════════
def run_rag_pipeline(question: str, verbose: bool = True) -> Dict[str, Any]:
    """
    Điều phối luồng dữ liệu tuần tự qua cả 5 Layers RAG:
      Layer 1 -> Layer 2 -> Layer 3 -> Layer 4 -> Layer 5
    """
    global chroma_collection
    start_time = time.time()
    cleaned_q = question.strip()

    if verbose:
        print("\n" + "=" * 70)
        print(f"📥 [RAG Pipeline] Nhận câu hỏi: \"{cleaned_q}\"")

    # ── LAYER 1: INTENT CLASSIFIER ──────────────────────────────────
    intent_res = classify_intent(cleaned_q)
    if intent_res.get("is_small_talk"):
        elapsed = round(time.time() - start_time, 3)
        if verbose:
            print(f"⚡ [Layer 1] Phân loại: XÃ GIAO / SMALL_TALK (Bypass RAG trong {elapsed}s)")
        return {
            "answer": intent_res.get("direct_reply", "Xin chào! Tôi có thể hỗ trợ gì cho bạn?"),
            "sources": [],
            "has_context": False,
            "status": "SMALL_TALK_BYPASS"
        }

    if verbose:
        print("🔍 [Layer 1] Phân loại: CÂU HỎI NGHIỆP VỤ (APP_QUESTION) -> Chuyển Layer 2")

    # ── LAYER 2: QUERY REWRITER (RAG FUSION) ────────────────────────
    queries = generate_rag_fusion_queries(cleaned_q, num_queries=3)
    if verbose:
        print(f"🔄 [Layer 2] Đã sinh {len(queries)} câu truy vấn mở rộng:")
        for idx, q in enumerate(queries, 1):
            print(f"   {idx}. {q}")

    # ── LAYER 3: CRAG RETRIEVER & DOCUMENT GRADER ───────────────────
    if chroma_collection is None:
        chroma_collection = get_chroma_collection()

    crag_res = crag_retrieve_and_grade(
        queries=queries,
        collection=chroma_collection,
        top_k=3,
        verbose=verbose
    )

    relevant_docs = crag_res.get("relevant_docs", [])
    has_context = crag_res.get("has_context", False)

    if verbose:
        print(f"🎯 [Layer 3] Thu được {len(relevant_docs)} tài liệu sạch sau thẩm định (has_context={has_context})")

    # ── LAYER 4: GENERATOR ──────────────────────────────────────────
    gen_res = generate_answer(
        question=cleaned_q,
        relevant_docs=relevant_docs,
        has_context=has_context
    )

    # Nếu hoàn toàn ngoài phạm vi, không cần chạy Layer 5
    if not has_context or not relevant_docs:
        elapsed = round(time.time() - start_time, 3)
        if verbose:
            print(f"ℹ️ [Layer 4] Không có dữ liệu phù hợp (Out of Context) -> Hoàn tất trong {elapsed}s")
        return {
            "answer": gen_res["answer"],
            "sources": [],
            "has_context": False,
            "status": "OUT_OF_CONTEXT"
        }

    # ── LAYER 5: VERIFIER (SELF-RAG: HALLUCINATION & USEFULNESS) ────
    verify_res = verify_and_refine(
        question=cleaned_q,
        answer=gen_res["answer"],
        docs=relevant_docs,
        has_context=True,
        max_retries=1
    )

    elapsed = round(time.time() - start_time, 3)
    if verbose:
        print(f"🛡️ [Layer 5] Trạng thái kiểm định: {verify_res.get('status')} | Tổng thời gian: {elapsed}s")
        print("=" * 70 + "\n")

    return {
        "answer": verify_res.get("final_answer", gen_res["answer"]),
        "sources": gen_res.get("sources", []),
        "has_context": True,
        "status": verify_res.get("status", "APPROVED")
    }


# ════════════════════════════════════════════════════════════════════
# REST API ENDPOINTS
# ════════════════════════════════════════════════════════════════════
@app.get("/")
def read_root():
    """Endpoint giới thiệu hệ thống."""
    return {
        "service": "ChatMessageE2E RAG Microservice",
        "status": "running",
        "layers": [
            "Layer 1: Intent Classifier",
            "Layer 2: Query Rewriter (RAG Fusion)",
            "Layer 3: CRAG Retriever",
            "Layer 4: Generator",
            "Layer 5: Verifier (Self-RAG)"
        ],
        "endpoints": {
            "ask": "POST /ask",
            "health": "GET /health"
        }
    }


@app.get("/health")
def health_check():
    """Endpoint kiểm tra sức khỏe hệ thống."""
    global chroma_collection
    doc_count = 0
    chroma_ok = False

    try:
        if chroma_collection is None:
            chroma_collection = get_chroma_collection()
        doc_count = chroma_collection.count()
        chroma_ok = True
    except Exception as e:
        chroma_ok = False

    return {
        "status": "healthy" if chroma_ok else "degraded",
        "chroma_connected": chroma_ok,
        "chroma_docs_count": doc_count,
        "chroma_collection": COLLECTION_NAME
    }


@app.post("/ask", response_model=AskResponse)
def ask(req: QuestionRequest):
    """
    Endpoint chính tiếp nhận câu hỏi từ Java Backend (RagApiClient).
    """
    if not req.question or not req.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Câu hỏi không được để trống"
        )

    try:
        result = run_rag_pipeline(req.question.strip(), verbose=True)

        return AskResponse(
            answer=result["answer"],
            sources=[
                SourceItem(
                    id=s["id"],
                    category=s.get("category", "Chung"),
                    question=s.get("question", ""),
                    similarity=s.get("similarity", 0.0)
                )
                for s in result.get("sources", [])
            ],
            has_context=result.get("has_context", False)
        )
    except Exception as e:
        print(f"❌ [FastAPI] Lỗi xử lý /ask: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi xử lý RAG: {str(e)}"
        )


if __name__ == "__main__":
    # Chạy trực tiếp: python rag_data/main.py
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
