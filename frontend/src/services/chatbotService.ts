// ============================================================
//  CHATBOT SERVICE — Tầng giao tiếp API giữa Frontend và Backend
// ============================================================

import { ChatbotResponse } from '../types/chatbot.types';

// URL API endpoint của chatbot backend
const CHATBOT_API_URL = '/api/chatbot/ask';

export class ChatbotService {
  /**
   * Gửi câu hỏi của người dùng tới Backend RAG
   * @param question - Câu hỏi dạng chuỗi văn bản (string)
   * @returns Promise<ChatbotResponse> - Câu trả lời kèm danh sách nguồn trích dẫn
   */
  static async ask(question: string): Promise<ChatbotResponse> {
    // 1. Kiểm tra đầu vào: không gửi request nếu chuỗi rỗng
    const trimmed = question.trim();
    if (!trimmed) {
      throw new Error('Câu hỏi không được để trống.');
    }

    // 2. Gửi request HTTP POST tới Backend
    const response = await fetch(CHATBOT_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      // Chuyển body sang JSON: { "question": "..." }
      body: JSON.stringify({ question: trimmed }),
    });

    // 3. Nếu server trả về mã lỗi (4xx, 5xx), ném lỗi với thông điệp rõ ràng
    if (!response.ok) {
      let errorMessage = `Yêu cầu thất bại (Mã lỗi: ${response.status})`;
      try {
        const errorData = await response.json();
        if (errorData.message) {
          errorMessage = errorData.message;
        }
      } catch {
        // Nếu response không phải JSON thì dùng thông điệp mặc định
      }
      throw new Error(errorMessage);
    }

    // 4. Parse dữ liệu JSON trả về theo định dạng ChatbotResponse
    const data: ChatbotResponse = await response.json();
    return data;
  }
}
