// ============================================================
//  CHATBOT TYPES — Định nghĩa kiểu dữ liệu cho toàn bộ chatbot
// ============================================================

// ── 1. Một nguồn tài liệu FAQ mà AI tham khảo khi trả lời ──
//      Backend sẽ trả về mảng này trong response
export interface FaqSource {
  id: string;         // ID duy nhất của document trong vector DB
  category: string;   // Danh mục: vd "Đăng nhập", "Bảo mật"
  question: string;   // Câu hỏi gốc trong FAQ
  similarity: number; // Độ liên quan 0.0 → 1.0 (vd: 0.87 = 87%)
}

// ── 2. Response từ backend khi hỏi chatbot ──────────────────
export interface ChatbotResponse {
  answer: string;          // Câu trả lời của AI
  sources: FaqSource[];    // Tài liệu FAQ đã dùng để trả lời
  hasContext: boolean;     // true = tìm thấy tài liệu liên quan
                           // false = câu hỏi ngoài phạm vi
}

// ── 3. Một tin nhắn trong cuộc hội thoại ────────────────────
export interface ChatMessage {
  id: string;                          // ID duy nhất (tránh trùng khi render)
  role: 'user' | 'bot';               // Ai nói: người dùng hay bot
  content: string;                     // Nội dung tin nhắn
  timestamp: Date;                     // Thời điểm gửi
  status: 'sending' | 'done' | 'error'; // Trạng thái gửi
  // Chỉ có ở tin nhắn của bot:
  sources?: FaqSource[];               // Tài liệu tham khảo (nếu có)
  hasContext?: boolean;                // Có tìm được context không
}
