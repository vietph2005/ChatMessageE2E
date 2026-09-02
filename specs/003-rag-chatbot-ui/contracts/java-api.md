# Contract: Java Spring Boot Chatbot API

**Service**: ChatMessage Backend | **Base URL**: `http://localhost:8080` | **Date**: 2026-09-03

## Tổng quan

Endpoint chatbot trên Java Spring Boot, nhận câu hỏi từ React frontend, gọi Python FastAPI microservice và trả về kết quả. Đây là điểm giao tiếp duy nhất mà frontend sử dụng.

---

## POST /api/chatbot/ask

Gửi câu hỏi đến chatbot và nhận câu trả lời từ RAG pipeline.

### Request

```
POST http://localhost:8080/api/chatbot/ask
Content-Type: application/json
Origin: http://localhost:5173
```

**Body:**
```json
{
  "question": "Làm sao để tìm bạn bè?"
}
```

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `question` | string | ✅ | `@NotBlank`, max 1000 ký tự |

### Response — Thành công (200 OK)

```json
{
  "answer": "Để tìm bạn bè trong ChatMessage, bạn cần nhập chính xác địa chỉ Gmail...",
  "sources": [
    {
      "id": "search-001_c00",
      "category": "Tìm kiếm",
      "question": "Làm thế nào để tìm kiếm người dùng khác?",
      "similarity": 0.8842
    }
  ],
  "hasContext": true
}
```

> **Lưu ý naming convention**: Python dùng `snake_case` (`has_context`), Java/JSON trả ra frontend dùng `camelCase` (`hasContext`). Jackson tự động convert.

### Response Schema

| Field | Type | Mô tả |
|-------|------|--------|
| `answer` | string | Câu trả lời tiếng Việt |
| `sources` | array | Danh sách FAQ tham khảo (có thể rỗng) |
| `sources[].id` | string | ID chunk ChromaDB |
| `sources[].category` | string | Danh mục FAQ |
| `sources[].question` | string | Câu hỏi gốc trong FAQ |
| `sources[].similarity` | number (0–1) | Điểm tương đồng |
| `hasContext` | boolean | Có tìm được FAQ liên quan không |

### Error Responses

| HTTP Status | Tình huống | Body |
|---|---|---|
| `400 Bad Request` | `question` rỗng | `{"error": "INVALID_REQUEST", "message": "Question must not be blank"}` |
| `503 Service Unavailable` | Python RAG microservice chưa chạy hoặc không phản hồi | `{"error": "RAG_UNAVAILABLE", "message": "Chatbot service is temporarily unavailable"}` |
| `504 Gateway Timeout` | Python microservice mất quá 15s | `{"error": "RAG_TIMEOUT", "message": "Request timed out, please try again"}` |
| `500 Internal Server Error` | Lỗi không xác định | `{"error": "INTERNAL_ERROR", "message": "An unexpected error occurred"}` |

---

## CORS Configuration

```
Access-Control-Allow-Origin: http://localhost:5173
Access-Control-Allow-Methods: POST, OPTIONS
Access-Control-Allow-Headers: Content-Type
```

Java controller được annotate `@CrossOrigin(origins = "http://localhost:5173")`.

---

## Timeout Policy

| Hop | Timeout |
|-----|---------|
| React → Java | Browser default (không giới hạn; UX timeout qua loading state) |
| Java → Python FastAPI | Connect: 3s, Read: 15s |
| Python → Gemini API | Mặc định `google-generativeai` library (~30s) |
