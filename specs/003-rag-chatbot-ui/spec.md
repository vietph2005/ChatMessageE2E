# Feature Specification: RAG Chatbot UI

**Feature Branch**: `003-rag-chatbot-ui`

**Created**: 2026-09-03

**Status**: Draft

**Input**: User description: "Giao diện để người dùng tương tác hỏi chatbot sử dụng RAG pipeline"

## Clarifications

### Session 2026-09-03

- Q: Giao diện chatbot sẽ được triển khai theo hình thức nào? → A: Tích hợp vào frontend React/Vite hiện có (`/frontend`), dùng Tailwind CSS, thêm trang `/chatbot`.
- Q: Frontend sẽ giao tiếp với RAG backend thông qua cơ chế nào? → A: Frontend gọi qua **Java Spring Boot backend** (REST API JSON); Java backend tích hợp trực tiếp với Python RAG pipeline (`rag_online.py`) thông qua subprocess hoặc HTTP nội bộ.
- Q: Java Spring Boot sẽ tích hợp với Python RAG pipeline thông qua cơ chế nào? → A: **Python FastAPI microservice** chạy song song tại `http://localhost:8000`; Java gọi HTTP nội bộ đến endpoint `/ask`, Python giữ ChromaDB trong bộ nhớ.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Gửi câu hỏi và nhận câu trả lời từ chatbot (Priority: P1)

Người dùng mở giao diện chatbot, nhập câu hỏi về ứng dụng ChatMessage (ví dụ: "Làm sao để tìm bạn bè?"), gửi đi và nhận lại câu trả lời mạch lạc từ hệ thống RAG trong vòng vài giây. Nguồn tài liệu tham khảo (FAQ) được hiển thị kèm theo câu trả lời.

**Why this priority**: Đây là chức năng cốt lõi duy nhất của tính năng — nếu không có nó, toàn bộ chatbot không có giá trị.

**Independent Test**: Có thể test độc lập bằng cách mở trang chatbot, gõ bất kỳ câu hỏi liên quan đến ứng dụng và xem câu trả lời xuất hiện đúng.

**Acceptance Scenarios**:

1. **Given** người dùng mở trang chatbot, **When** người dùng nhập câu hỏi liên quan đến ChatMessage và nhấn Gửi, **Then** hệ thống hiển thị câu trả lời trong dưới 10 giây kèm tên danh mục FAQ nguồn.
2. **Given** người dùng đã gửi câu hỏi, **When** hệ thống đang xử lý, **Then** giao diện hiển thị trạng thái "đang trả lời..." để tránh người dùng gửi trùng lặp.
3. **Given** người dùng nhấn Gửi, **When** ô nhập liệu đang trống, **Then** hệ thống không gửi yêu cầu và hiển thị gợi ý nhập câu hỏi.

---

### User Story 2 - Lịch sử hội thoại trong phiên làm việc (Priority: P2)

Người dùng có thể xem lại toàn bộ các câu hỏi và câu trả lời đã trao đổi kể từ khi mở trang chatbot trong phiên hiện tại. Các tin nhắn được hiển thị theo thứ tự thời gian, phân biệt rõ ràng giữa tin nhắn của người dùng và câu trả lời của bot.

**Why this priority**: Cho phép người dùng tham chiếu lại câu trả lời trước đó mà không cần đặt lại câu hỏi, nâng cao trải nghiệm sử dụng đáng kể.

**Independent Test**: Gửi ít nhất 3 câu hỏi liên tiếp và kiểm tra tất cả đều hiển thị đúng thứ tự với nội dung chính xác trong cùng phiên.

**Acceptance Scenarios**:

1. **Given** người dùng đã gửi nhiều câu hỏi trong cùng phiên, **When** xem màn hình chat, **Then** tất cả tin nhắn cũ vẫn hiện đầy đủ theo thứ tự thời gian.
2. **Given** có lịch sử hội thoại dài, **When** có câu trả lời mới xuất hiện, **Then** màn hình tự cuộn xuống câu trả lời mới nhất.

---

### User Story 3 - Xử lý câu hỏi ngoài phạm vi (Priority: P3)

Khi người dùng đặt câu hỏi không liên quan đến ứng dụng ChatMessage (ví dụ: "Thời tiết hôm nay thế nào?"), chatbot từ chối lịch sự và hướng dẫn người dùng đặt câu hỏi đúng chủ đề thay vì trả lời sai lệch.

**Why this priority**: Bảo vệ tính tin cậy của chatbot — tránh trường hợp bot nói nhảm làm người dùng mất tin tưởng.

**Independent Test**: Gõ một câu hỏi hoàn toàn ngoài lĩnh vực ứng dụng và kiểm tra bot từ chối lịch sự thay vì bịa đặt.

**Acceptance Scenarios**:

1. **Given** người dùng nhập câu hỏi không liên quan đến ChatMessage, **When** hệ thống không tìm thấy tài liệu phù hợp, **Then** chatbot trả lời thông báo từ chối lịch sự và gợi ý phạm vi câu hỏi phù hợp.
2. **Given** chatbot trả về thông báo từ chối, **When** người dùng xem trả lời, **Then** không có nguồn FAQ nào được hiển thị kèm theo.

---

### Edge Cases

- Điều gì xảy ra khi người dùng gửi câu hỏi cực kỳ dài (> 500 ký tự)?
- Điều gì xảy ra khi kết nối mạng bị gián đoạn trong lúc chờ câu trả lời?
- Hệ thống xử lý thế nào khi người dùng liên tục gửi nhiều câu hỏi cùng lúc?
- Điều gì xảy ra khi chatbot backend không phản hồi trong khoảng thời gian quy định?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống PHẢI cung cấp ô nhập liệu văn bản để người dùng gõ câu hỏi.
- **FR-002**: Hệ thống PHẢI có nút Gửi để người dùng khởi tạo yêu cầu hỏi đáp; người dùng cũng có thể nhấn Enter để gửi.
- **FR-003**: Hệ thống PHẢI hiển thị trạng thái "đang xử lý" trong lúc chờ phản hồi từ RAG backend và vô hiệu hóa ô nhập liệu trong thời gian này.
- **FR-004**: Hệ thống PHẢI hiển thị câu trả lời của chatbot kèm danh sách nguồn FAQ tham khảo (tên danh mục và mức độ liên quan tính theo phần trăm) khi có ngữ cảnh.
- **FR-005**: Hệ thống PHẢI hiển thị thông báo từ chối thân thiện khi RAG backend không tìm được ngữ cảnh liên quan (trường `has_context = false`).
- **FR-006**: Hệ thống PHẢI duy trì lịch sử toàn bộ hội thoại trong phiên làm việc hiện tại và tự động cuộn đến tin nhắn mới nhất.
- **FR-007**: Hệ thống PHẢI hiển thị thông báo lỗi thân thiện khi không thể kết nối đến chatbot backend.
- **FR-008**: Hệ thống PHẢI hỗ trợ giao diện responsive trên màn hình máy tính và điện thoại di động.
- **FR-009**: Giao diện PHẢI phân biệt trực quan rõ ràng tin nhắn của người dùng và câu trả lời của chatbot (vị trí, màu sắc khác nhau).
- **FR-010**: Người dùng PHẢI có khả năng xóa lịch sử hội thoại và bắt đầu cuộc hội thoại mới.
- **FR-011**: Hệ thống PHẢI cung cấp REST endpoint trên Java Spring Boot backend (`POST /api/chatbot/ask`) để nhận câu hỏi từ frontend và trả về kết quả JSON gồm `answer`, `sources`, và `has_context`.
- **FR-012**: Python RAG PHẢI được triển khai dưới dạng **FastAPI microservice** riêng biệt, cung cấp endpoint `POST /ask` tại `http://localhost:8000`; Java backend gọi HTTP nội bộ đến microservice này khi xử lý câu hỏi.

### Key Entities

- **Message**: Đơn vị hội thoại — bao gồm loại (người dùng / bot), nội dung văn bản, thời điểm gửi, danh sách nguồn FAQ (chỉ có ở tin nhắn bot), trạng thái (đang gửi / đã nhận / lỗi).
- **Conversation Session**: Tập hợp các tin nhắn trong một phiên làm việc — bắt đầu khi mở trang, kết thúc khi đóng trang hoặc xóa hội thoại.
- **FAQ Source**: Tài liệu tham khảo kèm theo câu trả lời — bao gồm danh mục (category), câu hỏi gốc trong FAQ, mức độ liên quan (similarity %).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Người dùng nhận được câu trả lời hiển thị đầy đủ trong vòng 10 giây kể từ khi nhấn Gửi trong điều kiện mạng bình thường.
- **SC-002**: 100% câu hỏi ngoài phạm vi (không có tài liệu liên quan) đều nhận thông báo từ chối lịch sự thay vì câu trả lời bịa đặt.
- **SC-003**: Giao diện hiển thị và sử dụng được trên màn hình có độ rộng từ 320px (điện thoại nhỏ) đến 1920px (desktop).
- **SC-004**: Toàn bộ lịch sử hội thoại trong phiên (tối thiểu 20 lượt hỏi đáp) được hiển thị đầy đủ không bị mất.
- **SC-005**: Trạng thái "đang xử lý" xuất hiện trong vòng 200ms sau khi người dùng nhấn Gửi để phản hồi tương tác tức thì.

## Assumptions

- Frontend sẽ giao tiếp với Python RAG backend thông qua một API endpoint HTTP (FastAPI hoặc Flask) sẽ bọc module `rag_online.py`, không gọi Python script trực tiếp.
- Lịch sử hội thoại chỉ được duy trì trong bộ nhớ phiên làm việc hiện tại (session-only), không lưu vào cơ sở dữ liệu bền vững.
- Giao diện chatbot được tích hợp vào ứng dụng **React/Vite** hiện có trong thư mục `/frontend`, sử dụng **Tailwind CSS** theo đúng Constitution (Principle I), được truy cập qua route `/chatbot`.
- **Luồng giao tiếp đầy đủ**: Frontend React → `POST /api/chatbot/ask` → Java Spring Boot → `POST http://localhost:8000/ask` → Python FastAPI (bọc `rag_online.py`) → ChromaDB + Gemini API.
- Python RAG chạy dưới dạng **FastAPI microservice** riêng biệt song song với Java; nạp ChromaDB vào bộ nhớ một lần khi khởi động, giữ kết nối trong suốt vòng đời của service.
- Lịch sử hội thoại chỉ được duy trì trong bộ nhớ phiên làm việc hiện tại (session-only), không lưu vào cơ sở dữ liệu bền vững.
- Người dùng đã có kết nối internet để chatbot gọi Gemini API sinh câu trả lời.
- Không yêu cầu xác thực người dùng cho tính năng này — chatbot mở cho mọi người truy cập.
