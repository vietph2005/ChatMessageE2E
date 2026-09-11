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
    pipeline_start = time.time()
    cleaned_q = question.strip()

    if verbose:
        print("\n" + "=" * 70)
        print(f"📥 [RAG Pipeline] Nhận câu hỏi: \"{cleaned_q}\"")
        print("=" * 70)

    # ── LAYER 1: INTENT CLASSIFIER ──────────────────────────────────
    t1_start = time.time()
    intent_res = classify_intent(cleaned_q)
    t1_elapsed = round(time.time() - t1_start, 3)

    if intent_res.get("is_small_talk"):
        total_elapsed = round(time.time() - pipeline_start, 3)
        if verbose:
            print(f"\n[1/5] ⚡ LAYER 1 (⏱️ {t1_elapsed}s): Phân loại -> XÃ GIAO / SMALL_TALK")
            print(f"      ↪️ Bypass RAG, trả lời trực tiếp trong {total_elapsed}s")
            print("=" * 70 + "\n")
        return {
            "answer": intent_res.get("direct_reply", "Xin chào! Tôi có thể hỗ trợ gì cho bạn?"),
            "sources": [],
            "has_context": False,
            "status": "SMALL_TALK_BYPASS"
        }

    if verbose:
        print(f"\n[1/5] 🧭 LAYER 1 (⏱️ {t1_elapsed}s): CÂU HỎI NGHIỆP VỤ (app_question) -> Tiếp tục Layer 2")

    # ── LAYER 2: QUERY REWRITER (RAG FUSION) ────────────────────────
    t2_start = time.time()
    queries = generate_rag_fusion_queries(cleaned_q, num_queries=3)
    t2_elapsed = round(time.time() - t2_start, 3)

    if verbose:
        print(f"\n[2/5] 🔄 LAYER 2 (⏱️ {t2_elapsed}s): RAG Fusion đã sinh {len(queries)} câu truy vấn đa hướng:")
        for idx, q in enumerate(queries, 1):
            tag = "GỐC" if idx == 1 else f"GÓC NHÌN {idx-1}"
            print(f"      {idx}. [{tag}]: \"{q}\"")

    # ── LAYER 3: CRAG RETRIEVER & DOCUMENT GRADER ───────────────────
    t3_start = time.time()
    if chroma_collection is None:
        chroma_collection = get_chroma_collection()

    if verbose:
        print(f"\n[3/5] 🔍 LAYER 3: Đang tìm kiếm ChromaDB & chạy CRAG Document Grader...")

    crag_res = crag_retrieve_and_grade(
        queries=queries,
        collection=chroma_collection,
        top_k=3,
        verbose=verbose
    )

    relevant_docs = crag_res.get("relevant_docs", [])
    has_context = crag_res.get("has_context", False)
    t3_elapsed = round(time.time() - t3_start, 3)

    if verbose:
        print(f"      🎯 Kết quả Layer 3 (⏱️ {t3_elapsed}s): {len(relevant_docs)}/{crag_res.get('total_candidates', 0)} tài liệu đạt chuẩn RELEVANT (has_context={has_context})")

    # ── LAYER 4: GENERATOR ──────────────────────────────────────────
    t4_start = time.time()
    gen_res = generate_answer(
        question=cleaned_q,
        relevant_docs=relevant_docs,
        has_context=has_context
    )
    t4_elapsed = round(time.time() - t4_start, 3)

    # Nếu hoàn toàn ngoài phạm vi, không cần chạy Layer 5
    if not has_context or not relevant_docs:
        total_elapsed = round(time.time() - pipeline_start, 3)
        if verbose:
            print(f"\n[4/5] ℹ️ LAYER 4 (⏱️ {t4_elapsed}s): Không có dữ liệu phù hợp (Out of Context)")
            print(f"⏱️ Hoàn tất xử lý ngoài phạm vi trong {total_elapsed}s")
            print("=" * 70 + "\n")
        return {
            "answer": gen_res["answer"],
            "sources": [],
            "has_context": False,
            "status": "OUT_OF_CONTEXT"
        }

    if verbose:
        print(f"\n[4/5] 🤖 LAYER 4 (⏱️ {t4_elapsed}s): Đã sinh câu trả lời thành công ({len(gen_res.get('sources', []))} thẻ nguồn tham khảo)")

    # ── LAYER 5: VERIFIER (SELF-RAG: HALLUCINATION & USEFULNESS) ────
    t5_start = time.time()
    if verbose:
        print(f"\n[5/5] 🛡️ LAYER 5: Đang thẩm định Ảo giác (Hallucination) & Độ hữu ích (Usefulness)...")

    verify_res = verify_and_refine(
        question=cleaned_q,
        answer=gen_res["answer"],
        docs=relevant_docs,
        has_context=True,
        max_retries=1
    )
    t5_elapsed = round(time.time() - t5_start, 3)
    total_elapsed = round(time.time() - pipeline_start, 3)

    if verbose:
        print(f"      🏁 Kết quả Layer 5 (⏱️ {t5_elapsed}s): Trạng thái -> {verify_res.get('status')}")
        print(f"⏱️ Tổng thời gian pipeline 5 Layers: {total_elapsed}s")
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
