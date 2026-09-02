# Quickstart: RAG Chatbot UI

**Feature**: 003-rag-chatbot-ui | **Date**: 2026-09-03

## Prerequisites

Trước khi chạy, đảm bảo:

- [ ] Đã chạy xong **Offline Pipeline** (4 bước): `data_preparation.py` → `chunking.py` → `embedding_pipeline.py` → `vector_db.py`
- [ ] Thư mục `rag_data/vector_db/chroma_db/` tồn tại và có dữ liệu
- [ ] File `rag_data/.env` chứa `GOOGLE_API_KEY=<your_key>`
- [ ] Python packages đã cài: `pip install fastapi uvicorn google-generativeai chromadb python-dotenv`
- [ ] Java 21 + Maven đã cài
- [ ] Node.js 18+ và npm đã cài

---

## Bước 1: Khởi động Python FastAPI Microservice

```powershell
# Từ thư mục gốc của project
cd c:\Users\phamh\IdeaProjects\TestSpec\ChatMessage\ChatMessageE2E

# Khởi động FastAPI server (port 8000)
uvicorn rag_data.rag_api:app --host 0.0.0.0 --port 8000
```

**Kiểm tra health check:**
```powershell
curl http://localhost:8000/health
# Expected: {"status": "ok", "collection_count": <số FAQ>}
```

**Kiểm tra ask endpoint:**
```powershell
curl -X POST http://localhost:8000/ask `
  -H "Content-Type: application/json" `
  -d '{"question": "Làm sao tìm bạn bè?"}'
# Expected: {"answer": "...", "sources": [...], "has_context": true}
```

---

## Bước 2: Khởi động Java Spring Boot Backend

```powershell
# Từ thư mục gốc của project
mvn spring-boot:run
# Hoặc: ./mvnw spring-boot:run
```

**Kiểm tra Java → Python integration:**
```powershell
curl -X POST http://localhost:8080/api/chatbot/ask `
  -H "Content-Type: application/json" `
  -d '{"question": "Safety code là gì?"}'
# Expected: {"answer": "...", "sources": [...], "hasContext": true}
```

---

## Bước 3: Khởi động React Frontend

```powershell
cd frontend
npm install  # Lần đầu tiên
npm run dev
# Mở trình duyệt tại http://localhost:5173/chatbot
```

---

## Validation Scenarios

### Scenario 1: Câu hỏi trong phạm vi FAQ

1. Mở `http://localhost:5173/chatbot`
2. Nhập: `"Làm sao để tìm người dùng khác?"`
3. Nhấn Gửi (hoặc Enter)
4. **Kỳ vọng**:
   - Hiển thị trạng thái "đang trả lời..." ngay lập tức
   - Trong ≤ 10 giây, câu trả lời xuất hiện với màu nền phân biệt (bubble bot)
   - Có ít nhất 1 nguồn FAQ hiển thị kèm danh mục và phần trăm độ liên quan

### Scenario 2: Câu hỏi ngoài phạm vi

1. Nhập: `"Thời tiết hôm nay thế nào?"`
2. **Kỳ vọng**:
   - Bot trả lời từ chối lịch sự (không bịa đặt thông tin)
   - Không có nguồn FAQ nào hiển thị

### Scenario 3: Gửi câu hỏi rỗng

1. Không nhập gì, click vào ô nhập liệu rồi nhấn Gửi
2. **Kỳ vọng**: Nút Gửi bị vô hiệu hóa (disabled) — không có request nào được gửi

### Scenario 4: Lịch sử hội thoại

1. Gửi 3 câu hỏi liên tiếp
2. **Kỳ vọng**:
   - Tất cả 6 tin nhắn (3 user + 3 bot) hiển thị đầy đủ theo thứ tự
   - Màn hình tự cuộn xuống tin nhắn mới nhất

### Scenario 5: Xóa hội thoại

1. Sau khi có lịch sử hội thoại, nhấn nút Clear/Xóa
2. **Kỳ vọng**: Toàn bộ lịch sử bị xóa, màn hình chat trống

### Scenario 6: Python service chưa chạy (resilience test)

1. Dừng Python FastAPI service
2. Gửi câu hỏi từ React UI
3. **Kỳ vọng**: Hiển thị thông báo lỗi thân thiện "Chatbot tạm thời không khả dụng"

---

## Tham chiếu

- **Python API Contract**: [contracts/python-api.md](./contracts/python-api.md)
- **Java API Contract**: [contracts/java-api.md](./contracts/java-api.md)
- **Data Model**: [data-model.md](./data-model.md)
- **Research**: [research.md](./research.md) — Chi tiết kỹ thuật về FastAPI pattern, CORS config
