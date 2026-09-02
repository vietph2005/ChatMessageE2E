# Implementation Plan: RAG Chatbot UI

**Branch**: `003-rag-chatbot-ui` | **Date**: 2026-09-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/003-rag-chatbot-ui/spec.md`

## Summary

Xây dựng giao diện chatbot FAQ tích hợp vào frontend React/Vite hiện có, cho phép người dùng đặt câu hỏi về ứng dụng ChatMessage và nhận câu trả lời từ RAG pipeline. Kiến trúc gồm 3 lớp: React UI (trang `/chatbot`) → Java Spring Boot (endpoint `POST /api/chatbot/ask`) → Python FastAPI microservice (endpoint `POST /ask`, bọc `rag_online.py` + ChromaDB + Gemini 2.0 Flash).

## Technical Context

**Language/Version**:
- Frontend: TypeScript 5.x + React 18
- Backend Java: Java 21 + Spring Boot 3.x
- Backend Python: Python 3.11 + FastAPI 0.111 + Uvicorn

**Primary Dependencies**:
- Frontend: React, Tailwind CSS, Axios (HTTP client)
- Java: Spring Web (RestTemplate/WebClient), Jackson
- Python: FastAPI, uvicorn, pydantic, `rag_online.py` (existing)

**Storage**: ChromaDB persistent (đã có tại `rag_data/vector_db/chroma_db/`) — Python microservice nạp vào RAM khi khởi động

**Testing**:
- Frontend: Vitest + React Testing Library
- Java: JUnit 5 + Mockito + MockMvc
- Python: pytest + httpx (FastAPI TestClient)

**Target Platform**: Local development server (localhost); cùng máy với Java Spring Boot

**Project Type**: Web application (React frontend + Java backend + Python microservice)

**Performance Goals**: Câu trả lời hiển thị trong ≤ 10 giây kể từ khi nhấn Gửi (end-to-end bao gồm embedding + vector search + Gemini generation)

**Constraints**: ChromaDB và Python microservice phải khởi động trước Java backend; CORS phải được cấu hình đúng giữa React (port 5173), Java (port 8080) và Python (port 8000)

**Scale/Scope**: Single-user chatbot FAQ, không có yêu cầu concurrency cao trong giai đoạn đầu

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Layered Architecture | ✅ PASS | Python service: router/service/domain tách biệt. Java: Controller → Service → Infrastructure (HTTP client). React: page/component/service tách biệt |
| II. Clean Code & SOLID | ✅ PASS | Mỗi class/function đơn trách nhiệm; naming rõ ràng |
| III. E2EE | ✅ PASS | Chatbot FAQ không liên quan đến message content; không có plaintext message nào được xử lý |
| IV. Honest APIs & Error Handling | ✅ PASS | Java endpoint trả về structured error; Python trả về `has_context` flag rõ ràng |
| V. Real-Time First | ✅ N/A | Chatbot FAQ dùng request-response, không cần WebSocket |
| VI. Automated Testing | ✅ PASS | Phải có unit test cho: React component hook, Java Controller (MockMvc), Python FastAPI endpoint (TestClient) |
| VII. Security & Config | ✅ PASS | GOOGLE_API_KEY trong `.env` (không commit); CORS whitelist cụ thể |
| VIII. Simplicity | ✅ PASS | Không thêm abstraction không cần thiết; FastAPI microservice nhỏ gọn |

**Constitution Check Result: PASS — Sẵn sàng Phase 0**

## Project Structure

### Documentation (this feature)

```text
specs/003-rag-chatbot-ui/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── python-api.md    # FastAPI /ask contract
│   └── java-api.md      # Java /api/chatbot/ask contract
└── tasks.md             # Phase 2 output (speckit-tasks)
```

### Source Code (repository root)

```text
# Python FastAPI Microservice (NEW)
rag_data/
├── rag_online.py          # Existing — được import bởi FastAPI
└── rag_api.py             # NEW — FastAPI server wrapping rag_online.py

# Java Backend (MODIFY existing layers)
src/main/java/org/example/chat/
├── presentation/
│   ├── controller/
│   │   └── ChatbotController.java     # NEW — POST /api/chatbot/ask
│   └── dto/
│       ├── ChatbotRequest.java        # NEW
│       └── ChatbotResponse.java       # NEW
├── application/
│   └── chatbot/
│       └── ChatbotService.java        # NEW — orchestration logic
└── infrastructure/
    └── rag/
        └── RagApiClient.java          # NEW — HTTP client gọi Python FastAPI

# React Frontend (MODIFY existing)
frontend/src/
├── pages/
│   └── ChatbotPage.tsx               # NEW — route /chatbot
├── components/
│   └── chatbot/
│       ├── ChatWindow.tsx             # NEW — danh sách tin nhắn
│       ├── MessageBubble.tsx          # NEW — tin nhắn đơn lẻ (user/bot)
│       ├── SourceBadge.tsx            # NEW — hiển thị FAQ source
│       └── ChatInput.tsx             # NEW — ô nhập liệu + nút Gửi
├── hooks/
│   └── useChatbot.ts                 # NEW — state & logic (messages, loading, send)
└── services/
    └── chatbotService.ts             # NEW — HTTP call đến Java backend

# Tests
src/test/java/org/example/chat/
└── presentation/controller/
    └── ChatbotControllerTest.java     # NEW

frontend/src/
└── components/chatbot/
    └── ChatWindow.test.tsx            # NEW

rag_data/
└── tests/
    └── test_rag_api.py               # NEW
```

**Structure Decision**: Option 2 (Web application) — 3-tier architecture: Python microservice + Java backend + React frontend. Mỗi layer có thư mục riêng theo Convention đang có của dự án.

## Complexity Tracking

> Không có vi phạm Constitution nào cần justify.
