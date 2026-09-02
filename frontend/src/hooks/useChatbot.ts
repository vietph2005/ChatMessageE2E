import { useState, useCallback } from 'react';
import { ChatMessageItem } from '../components/chatbot/MessageBubble';
import { ChatbotService } from '../services/chatbotService';

export function useChatbot() {
  const [messages, setMessages] = useState<ChatMessageItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const sendMessage = useCallback(async (question: string) => {
    const trimmed = question.trim();
    if (!trimmed || isLoading) return;

    setErrorMessage(null);

    const userMessage: ChatMessageItem = {
      id: `user-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      role: 'user',
      content: trimmed,
      timestamp: new Date(),
      status: 'sending',
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await ChatbotService.ask(trimmed);

      const botMessage: ChatMessageItem = {
        id: `bot-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
        role: 'bot',
        content: response.answer,
        sources: response.sources,
        hasContext: response.hasContext,
        timestamp: new Date(),
        status: 'done',
      };

      setMessages((prev) => [
        ...prev.map((msg) =>
          msg.id === userMessage.id ? { ...msg, status: 'done' as const } : msg
        ),
        botMessage,
      ]);
    } catch (err: any) {
      console.error('[CHATBOT-HOOK] Error querying chatbot:', err);
      const friendlyError = err.message || 'Không thể kết nối đến máy chủ trợ lý ảo.';
      setErrorMessage(friendlyError);

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === userMessage.id ? { ...msg, status: 'error' as const } : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  }, [isLoading]);

  const clearChat = useCallback(() => {
    setMessages([]);
    setErrorMessage(null);
  }, []);

  return {
    messages,
    isLoading,
    errorMessage,
    sendMessage,
    clearChat,
  };
}
