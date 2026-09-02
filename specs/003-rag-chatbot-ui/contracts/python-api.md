# Contract: Python FastAPI RAG Microservice

**Service**: RAG API | **Base URL**: `http://localhost:8000` | **Date**: 2026-09-03

## Tổng quan

Python FastAPI microservice nhỏ gọn, bọc `rag_online.py`. Chỉ có **1 endpoint duy nhất**. Chỉ được gọi từ Java Spring Boot — không phải từ frontend trực tiếp.

---

## POST /ask

Nhận câu hỏi, chạy RAG pipeline (embed → retrieve → generate) và trả về câu trả lời.

### Request

```
POST http://localhost:8000/ask
Content-Type: application/json
```

**Body:**
```json
{
  "question": "Làm sao để tìm bạn bè?"
}
```

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `question` | string | ✅ | min_length=1, max_length=1000 |

### Response — Thành công (200 OK)

```json
{
  "answer": "Để tìm bạn bè trong ChatMessage, bạn cần nhập chính xác địa chỉ Gmail của họ vào thanh tìm kiếm...",
  "sources": [
    {
      "id": "search-001_c00",
      "category": "Tìm kiếm",
      "question": "Làm thế nào để tìm kiếm người dùng khác?",
      "similarity": 0.8842
    }
  ],
  "has_context": true
}
```

**Response — Không có FAQ liên quan (200 OK, has_context=false):**
```json
{
  "answer": "Tôi chưa có thông tin về vấn đề này trong hệ thống. Tôi là trợ lý hỗ trợ ứng dụng ChatMessage...",
  "sources": [],
  "has_context": false
}
```

### Response Schema

| Field | Type | Mô tả |
|-------|------|--------|
| `answer` | string | Câu trả lời tiếng Việt từ Gemini |
| `sources` | array | Danh sách FAQ tham khảo (rỗng nếu `has_context=false`) |
| `sources[].id` | string | ID chunk trong ChromaDB |
| `sources[].category` | string | Danh mục FAQ |
| `sources[].question` | string | Câu hỏi gốc trong FAQ |
| `sources[].similarity` | float (0–1) | Điểm tương đồng ngữ nghĩa |
| `has_context` | boolean | `true` nếu tìm được ít nhất 1 FAQ >= 0.55 similarity |

### Error Responses

| HTTP Status | Tình huống | Body |
|---|---|---|
| `422 Unprocessable Entity` | `question` rỗng hoặc vi phạm validation | `{"detail": [{"msg": "..."}]}` (Pydantic default) |
| `503 Service Unavailable` | ChromaDB chưa sẵn sàng | `{"detail": "ChromaDB not initialized"}` |
| `502 Bad Gateway` | Gemini API lỗi / không khả dụng | `{"detail": "LLM generation failed: ..."}` |

---

## GET /health

Endpoint kiểm tra sức khỏe service (dùng cho Java backend trước khi forward request).

**Response (200 OK):**
```json
{
  "status": "ok",
  "collection_count": 47
}
```

---

## Khởi động Service

```bash
cd c:\Users\phamh\IdeaProjects\TestSpec\ChatMessage\ChatMessageE2E
uvicorn rag_data.rag_api:app --host 0.0.0.0 --port 8000 --reload
```

Service nạp ChromaDB vào RAM khi khởi động (một lần duy nhất). Mọi request sau đó tái sử dụng kết nối này.
