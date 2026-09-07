// ============================================================
//  USE CHATBOT HOOK — Quản lý toàn bộ State và Logic của Chatbot
// ============================================================

import { useState, useCallback } from 'react';
import { ChatMessage } from '../types/chatbot.types';
import { ChatbotService } from '../services/chatbotService';

// Tin nhắn chào mừng mặc định khi vừa mở khung chat
const INITIAL_MESSAGE: ChatMessage = {
  id: 'welcome-msg',
  role: 'bot',
  content: 'Xin chào! Tôi là trợ lý AI hỗ trợ giải đáp thắc mắc về ứng dụng. Bạn cần hỗ trợ gì hôm nay?',
  timestamp: new Date(),
  status: 'done',
  hasContext: true,
};

export function useChatbot() {
  // 1. State danh sách tin nhắn trong cuộc trò chuyện
  const [messages, setMessages] = useState<ChatMessage[]>([INITIAL_MESSAGE]);

  // 2. State trạng thái đang đợi phản hồi từ Backend (đang suy nghĩ)
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // 3. State lưu thông báo lỗi nếu có
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  /**
   * Hàm gửi tin nhắn câu hỏi
   * Sử dụng useCallback để không bị tạo lại hàm mỗi khi component re-render
   */
  const sendMessage = useCallback(async (content: string) => {
    const trimmed = content.trim();
    if (!trimmed || isLoading) return; // Không gửi nếu rỗng hoặc đang chờ trả lời

    // Xóa lỗi cũ trước khi gửi câu hỏi mới
    setErrorMessage(null);

    // Tạo đối tượng tin nhắn của người dùng
    const userMessageId = `user-${Date.now()}`;
    const userMessage: ChatMessage = {
      id: userMessageId,
      role: 'user',
      content: trimmed,
      timestamp: new Date(),
      status: 'done',
    };

    // Đưa tin nhắn người dùng vào danh sách hiển thị ngay lập tức (optimistic UI)
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Gọi API sang backend thông qua ChatbotService
      const response = await ChatbotService.ask(trimmed);

      // Tạo tin nhắn trả lời của Bot dựa trên kết quả trả về
      const botMessage: ChatMessage = {
        id: `bot-${Date.now()}`,
        role: 'bot',
        content: response.answer,
        timestamp: new Date(),
        status: 'done',
        sources: response.sources,
        hasContext: response.hasContext,
      };

      // Đưa câu trả lời của Bot vào danh sách tin nhắn
      setMessages((prev) => [...prev, botMessage]);
    } catch (err: unknown) {
      // Bắt lỗi nếu mất mạng hoặc Backend gặp sự cố
      const errorText = err instanceof Error ? err.message : 'Có lỗi không xác định xảy ra.';
      setErrorMessage(errorText);

      // Thêm một tin nhắn lỗi từ bot để người dùng nhận biết trực tiếp trên giao diện chat
      const errorBotMessage: ChatMessage = {
        id: `err-${Date.now()}`,
        role: 'bot',
        content: `⚠️ Xin lỗi, không thể kết nối tới máy chủ AI: ${errorText}`,
        timestamp: new Date(),
        status: 'error',
      };
      setMessages((prev) => [...prev, errorBotMessage]);
    } finally {
      // Dù thành công hay thất bại, tắt trạng thái loading
      setIsLoading(false);
    }
  }, [isLoading]);

  /**
   * Hàm làm mới lại cuộc trò chuyện (xóa sạch tin nhắn cũ, giữ lại lời chào)
   */
  const clearChat = useCallback(() => {
    setMessages([
      {
        ...INITIAL_MESSAGE,
        timestamp: new Date(),
      },
    ]);
    setErrorMessage(null);
  }, []);

  return {
    messages,       // Danh sách tin nhắn để render lên UI
    isLoading,      // Cờ hiệu đang tải (để disable nút gửi, hiện hiệu ứng gõ...)
    errorMessage,   // Chuỗi thông báo lỗi (nếu cần hiển thị banner cảnh báo)
    sendMessage,    // Hàm gọi khi bấm nút gửi hoặc gõ Enter
    clearChat,      // Hàm gọi khi bấm nút "Làm mới hội thoại"
  };
}
