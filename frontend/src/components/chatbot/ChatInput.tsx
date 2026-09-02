import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2 } from 'lucide-react';

interface ChatInputProps {
  onSendMessage: (question: string) => void;
  isLoading: boolean;
  placeholder?: string;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  isLoading,
  placeholder = 'Nhập câu hỏi về ChatMessage (ví dụ: làm sao tìm bạn bè?)...',
}) => {
  const [text, setText] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto focus input on load
  useEffect(() => {
    if (!isLoading) {
      textareaRef.current?.focus();
    }
  }, [isLoading]);

  // Adjust height dynamically
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [text]);

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed || isLoading) return;
    onSendMessage(trimmed);
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const canSend = text.trim().length > 0 && !isLoading;

  return (
    <div className="w-full bg-slate-900/90 backdrop-blur-sm border-t border-slate-800 p-3 md:p-4">
      <div className="max-w-4xl mx-auto flex items-end gap-2 bg-slate-950 border border-slate-800 rounded-2xl p-1.5 focus-within:border-blue-500/70 focus-within:ring-1 focus-within:ring-blue-500/30 transition-all shadow-lg">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          rows={1}
          placeholder={placeholder}
          maxLength={1000}
          className="w-full resize-none bg-transparent px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none disabled:opacity-60 max-h-[120px]"
        />

        <button
          type="button"
          onClick={handleSend}
          disabled={!canSend}
          aria-label="Gửi câu hỏi"
          className="w-10 h-10 rounded-xl bg-blue-600 hover:bg-blue-500 active:bg-blue-700 disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center text-white shrink-0 transition-colors shadow-sm"
        >
          {isLoading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Send className="w-4 h-4 ml-0.5" />
          )}
        </button>
      </div>
      <div className="max-w-4xl mx-auto flex justify-between items-center mt-1.5 px-2 text-[11px] text-slate-500">
        <span>Nhấn Enter để gửi, Shift + Enter để xuống dòng</span>
        <span>{text.length}/1000</span>
      </div>
    </div>
  );
};
