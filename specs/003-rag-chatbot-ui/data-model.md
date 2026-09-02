# Data Model: RAG Chatbot UI

**Feature**: 003-rag-chatbot-ui | **Date**: 2026-09-03

## Entities

### 1. ChatMessage (Frontend only — in-memory session state)

Đơn vị hội thoại trong một phiên làm việc. **Không được lưu xuống database.**

| Field | Type | Mô tả |
|-------|------|--------|
| `id` | `string` (UUID) | Định danh duy nhất trong session |
| `role` | `'user' \| 'bot'` | Phân biệt tin nhắn người dùng vs chatbot |
| `content` | `string` | Nội dung văn bản của tin nhắn |
| `sources` | `FaqSource[]` (optional) | Danh sách tài liệu FAQ tham khảo (chỉ có ở `role='bot'`) |
| `hasContext` | `boolean` (optional) | `false` nếu bot không tìm được FAQ liên quan |
| `timestamp` | `Date` | Thời điểm tin nhắn được tạo |
| `status` | `'sending' \| 'done' \| 'error'` | Trạng thái xử lý của tin nhắn |

**Validation rules:**
- `content` không được rỗng khi `role = 'user'`
- `sources` chỉ hợp lệ khi `role = 'bot'`

**State transitions:**
```
[user gửi] → status: 'sending'
    ↓ (API thành công)
status: 'done', role: 'bot' message thêm vào
    ↓ (API lỗi)
status: 'error' (user message bị đánh dấu lỗi)
```

---

### 2. FaqSource (Frontend only — embedded trong ChatMessage)

Tài liệu FAQ tham khảo kèm theo câu trả lời của bot.

| Field | Type | Mô tả |
|-------|------|--------|
| `id` | `string` | ID của chunk trong ChromaDB (e.g., `"search-001_c00"`) |
| `category` | `string` | Danh mục FAQ (e.g., `"Tìm kiếm"`, `"Bảo mật"`) |
| `question` | `string` | Câu hỏi gốc trong tài liệu FAQ |
| `similarity` | `number` (0–1) | Độ tương đồng ngữ nghĩa với câu hỏi người dùng |

---

### 3. ChatbotRequest (Java DTO — Request body)

| Field | Type | Validation | Mô tả |
|-------|------|------------|--------|
| `question` | `String` | `@NotBlank`, max 1000 ký tự | Câu hỏi người dùng |

---

### 4. ChatbotResponse (Java DTO — Response body)

| Field | Type | Mô tả |
|-------|------|--------|
| `answer` | `String` | Câu trả lời từ Gemini (tiếng Việt) |
| `sources` | `List<SourceDto>` | Danh sách FAQ nguồn (có thể rỗng) |
| `hasContext` | `boolean` | `false` nếu không tìm được FAQ liên quan |

---

### 5. SourceDto (Java DTO — Embedded trong ChatbotResponse)

| Field | Type | Mô tả |
|-------|------|--------|
| `id` | `String` | ID chunk trong ChromaDB |
| `category` | `String` | Danh mục FAQ |
| `question` | `String` | Câu hỏi gốc trong FAQ |
| `similarity` | `Double` | Điểm tương đồng (0.0–1.0) |

---

### 6. RagAskRequest (Python Pydantic — gửi từ Java đến FastAPI)

| Field | Type | Validation | Mô tả |
|-------|------|------------|--------|
| `question` | `str` | `min_length=1`, `max_length=1000` | Câu hỏi cần trả lời |

---

### 7. RagAskResponse (Python Pydantic — FastAPI trả về cho Java)

| Field | Type | Mô tả |
|-------|------|--------|
| `answer` | `str` | Câu trả lời sinh bởi Gemini |
| `sources` | `List[RagSource]` | Danh sách tài liệu tham khảo |
| `has_context` | `bool` | `True` nếu tìm được FAQ liên quan |

---

### 8. RagSource (Python Pydantic — Embedded trong RagAskResponse)

| Field | Type | Mô tả |
|-------|------|--------|
| `id` | `str` | ID chunk ChromaDB |
| `category` | `str` | Danh mục FAQ |
| `question` | `str` | Câu hỏi gốc |
| `similarity` | `float` | Điểm similarity (0.0–1.0) |

---

## Data Flow Summary

```
React (ChatMessage + FaqSource)
    ↕ HTTP JSON (ChatbotRequest / ChatbotResponse)
Java (ChatbotRequest DTO, ChatbotResponse DTO, SourceDto)
    ↕ HTTP JSON (RagAskRequest / RagAskResponse)
Python FastAPI (RagAskRequest, RagAskResponse, RagSource)
    ↕ In-process function call
rag_online.answer() → { answer, sources, has_context }
    ↕ In-process
ChromaDB (disk) + Gemini API
```

## Session Lifecycle

```
[Người dùng mở /chatbot] → ConversationSession bắt đầu (messages = [])
[Gửi câu hỏi] → ChatMessage (role='user') thêm vào messages
[API trả về] → ChatMessage (role='bot') thêm vào messages
[Người dùng nhấn Clear] → messages = [] (reset session)
[Người dùng đóng tab] → session kết thúc, mọi dữ liệu mất
```
