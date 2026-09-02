import React, { useRef, useEffect, useState } from 'react';
import {
  Trash2,
  Bot,
  Sparkles,
  AlertTriangle,
  RefreshCw,
  HelpCircle,
  ShieldCheck,
  Search,
  KeyRound,
} from 'lucide-react';
import { MessageBubble, ChatMessageItem } from './MessageBubble';
import { ChatInput } from './ChatInput';

interface ChatWindowProps {
  messages: ChatMessageItem[];
  isLoading: boolean;
  errorMessage: string | null;
  onSendMessage: (question: string) => void;
  onClearChat: () => void;
}

const QUICK_PROMPTS = [
  {
    icon: Search,
    title: 'Tìm bạn bè',
    prompt: 'Làm thế nào để tìm kiếm người dùng khác trong ứng dụng?',
  },
  {
    icon: ShieldCheck,
    title: 'Bảo mật E2EE',
    prompt: 'Mã hóa đầu cuối E2EE hoạt động như thế nào và máy chủ có đọc được tin nhắn không?',
  },
  {
    icon: KeyRound,
    title: 'Safety Code',
    prompt: 'Safety code là gì và tại sao tôi cần phải xác minh nó?',
  },
  {
    icon: HelpCircle,
    title: 'Lỗi tin nhắn',
    prompt: 'Tin nhắn bị lỗi không gửi được thì tôi phải xử lý ra sao?',
  },
];

export const ChatWindow: React.FC<ChatWindowProps> = ({
  messages,
  isLoading,
  errorMessage,
  onSendMessage,
  onClearChat,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);
  const [showClearConfirm, setShowClearConfirm] = useState(false);

  // Auto-scroll when messages change or while loading
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleConfirmClear = () => {
    onClearChat();
    setShowClearConfirm(false);
  };

  return (
    <div className="flex flex-col h-full w-full bg-slate-950 text-slate-100 overflow-hidden relative">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-3 bg-slate-900/80 backdrop-blur-md border-b border-slate-800 z-10 shrink-0">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-md">
              <Bot className="w-5 h-5" />
            </div>
            <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-500 border-2 border-slate-900 rounded-full" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <h1 className="font-semibold text-sm text-slate-100">
                Trợ lý Hỗ trợ ChatMessage
              </h1>
              <span className="px-1.5 py-0.5 text-[10px] font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded">
                AI FAQ
              </span>
            </div>
            <p className="text-[11px] text-slate-400 flex items-center gap-1">
              <span>Được hỗ trợ bởi Gemini 2.0 Flash & RAG</span>
            </p>
          </div>
        </div>

        {messages.length > 0 && (
          <button
            type="button"
            onClick={() => setShowClearConfirm(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-slate-400 hover:text-red-400 hover:bg-red-500/10 border border-slate-800 transition-colors"
            title="Xóa toàn bộ hội thoại"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Xóa hội thoại</span>
          </button>
        )}
      </header>

      {/* Confirmation Modal */}
      {showClearConfirm && (
        <div className="absolute inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 max-w-sm w-full shadow-2xl animate-in zoom-in-95 duration-150">
            <h3 className="text-base font-semibold text-slate-100 mb-2">
              Xóa lịch sử hội thoại?
            </h3>
            <p className="text-xs text-slate-400 mb-5 leading-relaxed">
              Toàn bộ tin nhắn hỏi đáp trong phiên này sẽ bị xóa và không thể khôi phục lại.
            </p>
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowClearConfirm(false)}
                className="px-3.5 py-1.5 rounded-xl text-xs font-medium text-slate-300 hover:bg-slate-800 transition-colors"
              >
                Hủy bỏ
              </button>
              <button
                type="button"
                onClick={handleConfirmClear}
                className="px-3.5 py-1.5 rounded-xl text-xs font-medium bg-red-600 hover:bg-red-500 text-white transition-colors"
              >
                Đồng ý xóa
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Message List Area */}
      <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-2">
        {messages.length === 0 ? (
          /* Empty State / Welcome Screen */
          <div className="h-full flex flex-col items-center justify-center text-center max-w-xl mx-auto py-8 px-4 animate-in fade-in duration-300">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-xl shadow-blue-500/10 mb-4">
              <Sparkles className="w-8 h-8" />
            </div>
            <h2 className="text-lg md:text-xl font-bold text-slate-100 mb-2">
              Xin chào! Tôi có thể giúp gì cho bạn?
            </h2>
            <p className="text-xs md:text-sm text-slate-400 mb-8 max-w-md leading-relaxed">
              Tôi là trợ lý AI được trang bị kiến thức chuẩn về ứng dụng ChatMessage, cơ chế mã hóa đầu cuối và các tính năng kết nối bạn bè.
            </p>

            {/* Quick Prompt Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full text-left">
              {QUICK_PROMPTS.map((item, idx) => {
                const Icon = item.icon;
                return (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => onSendMessage(item.prompt)}
                    className="p-3 rounded-xl bg-slate-900/60 hover:bg-slate-900 border border-slate-800/80 hover:border-blue-500/50 text-slate-300 transition-all flex items-start gap-2.5 group"
                  >
                    <div className="p-1.5 rounded-lg bg-blue-500/10 text-blue-400 group-hover:bg-blue-600 group-hover:text-white transition-colors shrink-0 mt-0.5">
                      <Icon className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="font-medium text-xs text-slate-200 group-hover:text-blue-400 transition-colors">
                        {item.title}
                      </div>
                      <div className="text-[11px] text-slate-500 line-clamp-2 mt-0.5">
                        {item.prompt}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        ) : (
          /* Active Messages */
          <div className="max-w-4xl mx-auto w-full">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}

            {/* Thinking / Loading indicator */}
            {isLoading && (
              <div className="flex justify-start mb-4 animate-in fade-in duration-150">
                <div className="flex items-start gap-2.5">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-600 to-blue-500 flex items-center justify-center text-white shadow-md shrink-0">
                    <Bot className="w-4 h-4" />
                  </div>
                  <div className="px-4 py-3 rounded-2xl rounded-tl-sm bg-slate-900 border border-slate-800 text-slate-400 text-xs flex items-center gap-2 shadow-md">
                    <RefreshCw className="w-3.5 h-3.5 animate-spin text-blue-400" />
                    <span>Đang tìm kiếm tài liệu FAQ và trả lời...</span>
                  </div>
                </div>
              </div>
            )}

            {/* Error Notice */}
            {errorMessage && (
              <div className="p-3.5 my-3 rounded-xl bg-red-950/40 border border-red-800/50 text-red-200 text-xs flex items-start gap-2.5 animate-in fade-in">
                <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="font-semibold text-red-300">Không thể lấy câu trả lời</p>
                  <p className="text-red-300/80 mt-0.5">{errorMessage}</p>
                </div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* Input Form */}
      <ChatInput onSendMessage={onSendMessage} isLoading={isLoading} />
    </div>
  );
};
