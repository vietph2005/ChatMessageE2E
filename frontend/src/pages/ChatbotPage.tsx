// ============================================================
//  CHATBOT PAGE — Trang giao diện chính của Trợ lý AI (RAG)
// ============================================================

import React, { useRef, useEffect } from 'react';
import { Bot, RotateCcw, ArrowLeft, Sparkles } from 'lucide-react';
import { useChatbot } from '../hooks/useChatbot';
import { MessageBubble } from '../components/chatbot/MessageBubble';
import { ChatInput } from '../components/chatbot/ChatInput';

interface ChatBotPageProps {
  onBack?: () => void; // Callback tuỳ chọn nếu muốn quay lại màn hình chat chính
}

export const ChatBotPage: React.FC<ChatBotPageProps> = ({ onBack }) => {
  // Lấy toàn bộ state và hàm từ custom hook useChatbot
  const { messages, isLoading, sendMessage, clearChat } = useChatbot();

  // Ref tham chiếu tới phần tử cuối danh sách tin nhắn để tự động cuộn xuống
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Mỗi khi danh sách messages thay đổi hoặc bot bắt đầu suy nghĩ, tự động cuộn xuống dưới cùng
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="flex flex-col h-full w-full bg-slate-950 text-slate-100 relative overflow-hidden">
      {/* Hiệu ứng ánh sáng nền mờ (Ambient Glow) */}
      <div className="absolute top-0 left-1/3 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-10 right-1/4 w-80 h-80 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* ── 1. HEADER: Thông tin bot và các nút thao tác ── */}
      <header className="h-16 px-4 md:px-6 border-b border-slate-800 bg-slate-900/80 backdrop-blur-md flex items-center justify-between z-10 shrink-0">
        <div className="flex items-center gap-3">
          {/* Nút quay lại (nếu có truyền prop onBack) */}
          {onBack && (
            <button
              onClick={onBack}
              aria-label="Quay lại"
              className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <ArrowLeft size={18} />
            </button>
          )}

          {/* Avatar của Bot với đèn báo trực tuyến */}
          <div className="relative">
            <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-blue-600 to-emerald-500 flex items-center justify-center text-white shadow-lg shadow-blue-500/20">
              <Bot size={22} />
            </div>
            {/* Chấm tròn xanh báo trạng thái sẵn sàng */}
            <span className="absolute bottom-0 right-0 w-3 h-3 rounded-full bg-emerald-500 ring-2 ring-slate-900 animate-pulse" />
          </div>

          {/* Tên và trạng thái của Trợ lý AI */}
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm md:text-base font-semibold text-white">
                Trợ lý AI (RAG Assistant)
              </h2>
              <span className="hidden sm:inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                <Sparkles size={11} />
                Knowledge Base
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Hỏi đáp thông tin về mã hoá, tài khoản và cách dùng ứng dụng
            </p>
          </div>
        </div>

        {/* Nút làm mới cuộc hội thoại */}
        <button
          type="button"
          onClick={clearChat}
          title="Làm mới đoạn hội thoại"
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700/80 rounded-xl transition-all shadow-sm active:scale-95"
        >
          <RotateCcw size={14} />
          <span className="hidden sm:inline">Làm mới</span>
        </button>
      </header>

      {/* ── 2. BODY: Khu vực hiển thị danh sách tin nhắn ── */}
      <main className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4">
        {/* Render danh sách tin nhắn */}
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {/* Bong bóng báo trạng thái Bot đang suy nghĩ */}
        {isLoading && (
          <div className="flex items-start gap-3 my-3">
            <div className="w-9 h-9 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center justify-center shrink-0">
              <Bot size={18} />
            </div>
            <div className="bg-slate-800/90 border border-slate-700/60 rounded-2xl rounded-tl-none px-4 py-3 text-sm text-slate-400 flex items-center gap-2">
              <span className="text-xs">AI đang tra cứu tài liệu & soạn câu trả lời</span>
              <span className="flex gap-1">
                <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
                <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
                <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-bounce" />
              </span>
            </div>
          </div>
        )}

        {/* Điểm neo để cuộn xuống cuối */}
        <div ref={messagesEndRef} />
      </main>

      {/* ── 3. FOOTER: Ô nhập câu hỏi và nút gửi ── */}
      <ChatInput onSend={sendMessage} isLoading={isLoading} />
    </div>
  );
};

export default ChatBotPage;
