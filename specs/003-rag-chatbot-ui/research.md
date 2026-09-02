# Research: RAG Chatbot UI

**Feature**: 003-rag-chatbot-ui | **Date**: 2026-09-03

## 1. Python FastAPI Microservice (bọc rag_online.py)

### Decision
Dùng **FastAPI** (không phải Flask) để wrap `rag_online.py` thành HTTP service.

### Rationale
- FastAPI tự sinh OpenAPI docs, hỗ trợ Pydantic validation mạnh, async-native
- Khởi động nhanh, dễ test với `httpx.AsyncClient`
- `rag_online.py` đã có hàm `get_collection()` và `answer()` — chỉ cần gọi lại, không cần refactor

### Pattern: Startup Lifespan (ChromaDB singleton)
```python
# Khởi tạo ChromaDB một lần khi server start, giữ trong AppState
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.collection = get_collection()  # Load ChromaDB vào RAM
    yield
    # teardown nếu cần

app = FastAPI(lifespan=lifespan)
```
→ Tránh overhead kết nối ChromaDB cho mỗi request.

### Alternatives Considered
- **Flask**: Đồng bộ, không có auto validation, ít tính năng hơn → Loại bỏ
- **Subprocess**: Java gọi `python rag_online.py` mỗi request → Overhead cao, không thể giữ ChromaDB trong RAM → Loại bỏ

---

## 2. Java Spring Boot — HTTP Client gọi Python FastAPI

### Decision
Dùng **RestTemplate** (đã có trong Spring Web, quen thuộc) với timeout cụ thể.

### Rationale
- Dự án đang dùng Spring Boot 3.x; `RestTemplate` được configure sẵn trong nhiều dự án Spring
- `WebClient` (reactive) mạnh hơn nhưng phức tạp hơn — không cần cho chatbot synchronous đơn giản
- Cần set `connectTimeout = 3s`, `readTimeout = 15s` (Gemini API cần ~5-10s)

### Pattern: Infrastructure Layer Client
```java
// RagApiClient.java (Infrastructure layer)
@Component
public class RagApiClient {
    private final RestTemplate restTemplate;
    private final String ragBaseUrl; // = "http://localhost:8000"

    public RagApiResponse ask(String question) {
        // POST http://localhost:8000/ask
        // Handle connection errors → throw RagUnavailableException
    }
}
```

### Alternatives Considered
- **WebClient (reactive)**: Overkill cho synchronous FAQ chatbot → Deferred
- **Feign Client**: Thêm dependency không cần thiết → Loại bỏ

---

## 3. React Frontend — State Management & UX

### Decision
Dùng **custom hook `useChatbot`** để quản lý state, không dùng global state (Redux/Zustand).

### Rationale
- Lịch sử hội thoại chỉ cần trong phạm vi trang `/chatbot` (session-only, không share sang trang khác)
- Custom hook đủ mạnh, đơn giản, testable
- Tailwind CSS đã có trong project — dùng consistent với Constitution (Principle I)

### Pattern: useChatbot hook
```typescript
interface Message {
  id: string;
  role: 'user' | 'bot';
  content: string;
  sources?: FaqSource[];
  hasContext?: boolean;
  timestamp: Date;
  status: 'sending' | 'done' | 'error';
}

function useChatbot() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async (question: string) => { ... }
  const clearChat = () => setMessages([]);

  return { messages, isLoading, sendMessage, clearChat };
}
```

### Auto-scroll Pattern
```typescript
const bottomRef = useRef<HTMLDivElement>(null);
useEffect(() => {
  bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
}, [messages]);
```

### Alternatives Considered
- **Zustand global store**: Không cần — chatbot state chỉ cần local → Loại bỏ
- **Redux Toolkit**: Overkill cho single-page state → Loại bỏ

---

## 4. CORS Configuration

### Decision
Cấu hình **CORS trên Java Spring Boot** cho phép origin `http://localhost:5173` (Vite dev server).

### Rationale
- Browser chặn React (port 5173) gọi Java (port 8080) nếu không có CORS header
- Java là điểm giao tiếp duy nhất với frontend; Python FastAPI không cần CORS (chỉ Java gọi nội bộ)

### Pattern
```java
@CrossOrigin(origins = "http://localhost:5173")
@RestController
@RequestMapping("/api/chatbot")
public class ChatbotController { ... }
```

---

## 5. Error Handling Strategy

| Tình huống | Python FastAPI | Java Backend | React UI |
|---|---|---|---|
| ChromaDB chưa khởi động | 503 Service Unavailable | Bắt exception → 503 → error message | Hiển thị "Chatbot tạm thời không khả dụng" |
| Gemini API lỗi/timeout | 502 Bad Gateway | Forward lỗi | Hiển thị "Lỗi kết nối AI, thử lại sau" |
| Câu hỏi ngoài phạm vi | 200 OK, `has_context: false` | Forward response | Hiển thị câu trả lời từ chối của bot |
| Câu hỏi rỗng | 422 Validation Error | 400 Bad Request | Disabled nút Gửi khi input rỗng |
| Timeout (>15s) | - | 504 Gateway Timeout | Hiển thị "Yêu cầu mất quá nhiều thời gian" |

---

## Tất cả NEEDS CLARIFICATION đã được giải quyết

Không có NEEDS CLARIFICATION nào trong spec → Research hoàn tất.
