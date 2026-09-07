// ============================================================
//  CHAT INPUT — Khung nhập câu hỏi và nút gửi tin nhắn
// ============================================================

import React, { useState, useRef, useEffect, KeyboardEvent } from 'react';
import { Send, Loader2, Sparkles } from 'lucide-react';

interface ChatInputProps {
  onSend: (content: string) => void;  // Hàm callback khi người dùng gửi câu hỏi
  isLoading: boolean;                 // Trạng thái đang tải (disable input & button)
  placeholder?: string;               // Chuỗi placeholder tuỳ chọn
}

// Một vài câu hỏi gợi ý nhanh giúp người dùng tiện thử nghiệm RAG
const QUICK_PROMPTS = [
  'Làm sao để kết bạn mới?',
  'Dữ liệu tin nhắn có được mã hoá E2E không?',
  'Tôi quên mật khẩu thì lấy lại như thế nào?',
];

export const ChatInput: React.FC<ChatInputProps> = ({
  onSend,
  isLoading,
  placeholder = 'Nhập câu hỏi của bạn về hệ thống... (Nhấn Enter để gửi)',
}) => {
  const [text, setText] = useState<string>('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Tự động điều chỉnh chiều cao của textarea theo độ dài văn bản
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      // Giới hạn chiều cao tối đa khoảng 120px (khoảng 4-5 dòng)
      textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
    }
  }, [text]);

  // Xử lý gửi tin nhắn
  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed || isLoading) return;

    onSend(trimmed);
    setText(''); // Xoá ô nhập sau khi gửi

    // Reset chiều cao textarea về 1 dòng
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  // Bắt sự kiện phím: Enter = Gửi, Shift + Enter = Xuống dòng
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault(); // Ngăn trình duyệt nhảy dòng mới mặc định
      handleSend();
    }
  };

  return (
    <div className="border-t border-slate-800 bg-slate-900/90 backdrop-blur-md p-4">
      {/* ── 1. Gợi ý câu hỏi nhanh (Quick Prompts) ── */}
      <div className="flex items-center gap-2 mb-3 overflow-x-auto pb-1 text-xs no-scrollbar">
        <span className="flex items-center gap-1 text-slate-500 shrink-0 font-medium">
          <Sparkles size={13} className="text-amber-400" />
          Gợi ý:
        </span>
        {QUICK_PROMPTS.map((prompt, idx) => (
          <button
            key={idx}
            type="button"
            disabled={isLoading}
            onClick={() => onSend(prompt)}
            className="shrink-0 px-2.5 py-1 rounded-full bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/60 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* ── 2. Khung soạn thảo & Nút gửi ── */}
      <div className="flex items-end gap-2 bg-slate-800/80 border border-slate-700/70 focus-within:border-blue-500 rounded-2xl p-2 transition-colors shadow-inner">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={isLoading}
          rows={1}
          className="flex-1 bg-transparent text-slate-100 placeholder-slate-400 text-sm resize-none focus:outline-none px-2 py-1.5 max-h-[120px] disabled:opacity-50"
        />

        {/* Nút gửi */}
        <button
          type="button"
          onClick={handleSend}
          disabled={!text.trim() || isLoading}
          aria-label="Gửi tin nhắn"
          className="w-9 h-9 rounded-xl flex items-center justify-center bg-blue-600 hover:bg-blue-500 active:scale-95 text-white disabled:opacity-40 disabled:hover:bg-blue-600 disabled:active:scale-100 transition-all shrink-0 shadow"
        >
          {isLoading ? (
            <Loader2 size={16} className="animate-spin" />
          ) : (
            <Send size={16} />
          )}
        </button>
      </div>

      {/* Hướng dẫn phím tắt nhỏ ở dưới */}
      <div className="text-[11px] text-slate-400 mt-1.5 text-right pr-2">
        Nhấn <kbd className="px-1 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300">Enter</kbd> để gửi, <kbd className="px-1 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300">Shift + Enter</kbd> để xuống dòng
      </div>
    </div>
  );
};
