// ============================================================
//  MESSAGE BUBBLE — Component hiển thị từng bong bóng tin nhắn
// ============================================================

import React, { useState } from 'react';
import { Bot, User, BookOpen, AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react';
import { ChatMessage, FaqSource } from '../../types/chatbot.types';

interface MessageBubbleProps {
  message: ChatMessage; // Dữ liệu của một tin nhắn (từ useChatbot)
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user';
  const isError = message.status === 'error';

  // State ẩn/hiện danh sách nguồn tài liệu tham khảo
  const [showSources, setShowSources] = useState<boolean>(false);

  // Format thời gian gửi (ví dụ: 14:35)
  const formattedTime = new Intl.DateTimeFormat('vi-VN', {
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(message.timestamp));

  return (
    <div
      className={`flex items-start gap-3 my-3 transition-all ${
        isUser ? 'flex-row-reverse' : 'flex-row'
      }`}
    >
      {/* ── 1. Avatar biểu tượng (Người dùng hoặc Bot) ── */}
      <div
        className={`w-9 h-9 rounded-full flex items-center justify-center shrink-0 shadow-md ${
          isUser
            ? 'bg-blue-600 text-white'
            : isError
            ? 'bg-red-500/20 text-red-400 border border-red-500/30'
            : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
        }`}
      >
        {isUser ? <User size={18} /> : <Bot size={18} />}
      </div>

      {/* ── 2. Nội dung bong bóng chat ── */}
      <div
        className={`max-w-[85%] md:max-w-[70%] rounded-2xl px-4 py-3 text-sm shadow-sm ${
          isUser
            ? 'bg-blue-600 text-white rounded-tr-none'
            : isError
            ? 'bg-red-950/40 text-red-200 border border-red-800/40 rounded-tl-none'
            : 'bg-slate-800/90 text-slate-100 border border-slate-700/60 rounded-tl-none'
        }`}
      >
        {/* Nội dung tin nhắn (giữ định dạng xuống dòng với whitespace-pre-wrap) */}
        <div className="whitespace-pre-wrap leading-relaxed">{message.content}</div>

        {/* ── 3. Cảnh báo khi câu hỏi ngoài phạm vi tri thức (hasContext === false) ── */}
        {!isUser && message.hasContext === false && (
          <div className="mt-2.5 flex items-center gap-1.5 text-xs text-amber-300 bg-amber-950/40 border border-amber-800/40 px-2.5 py-1.5 rounded-lg">
            <AlertTriangle size={14} className="shrink-0" />
            <span>Câu hỏi ngoài phạm vi tài liệu FAQ. Câu trả lời có thể mang tính chất tham khảo chung.</span>
          </div>
        )}

        {/* ── 4. Khu vực nguồn trích dẫn RAG (nếu Bot có trả về sources) ── */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-3 pt-2.5 border-t border-slate-700/50">
            {/* Nút bấm toggle mở rộng / thu gọn danh sách nguồn */}
            <button
              onClick={() => setShowSources((prev) => !prev)}
              className="flex items-center justify-between w-full text-xs text-slate-400 hover:text-slate-200 transition-colors py-1"
            >
              <span className="flex items-center gap-1.5 font-medium">
                <BookOpen size={13} className="text-emerald-400" />
                Nguồn tham khảo ({message.sources.length} tài liệu)
              </span>
              {showSources ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            </button>

            {/* Chi tiết từng tài liệu FAQ được trích xuất */}
            {showSources && (
              <div className="mt-2 space-y-2">
                {message.sources.map((source: FaqSource) => {
                  const percent = Math.round(source.similarity * 100);
                  return (
                    <div
                      key={source.id}
                      className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-700/40 text-xs text-slate-300"
                    >
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <span className="px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300 text-[10px] font-medium uppercase tracking-wider">
                          {source.category}
                        </span>
                        <span className="text-[11px] text-emerald-400 font-medium">
                          {percent}% liên quan
                        </span>
                      </div>
                      <p className="font-medium text-slate-200">{source.question}</p>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* ── 5. Thời gian gửi tin nhắn ── */}
        <div
          className={`text-[10px] mt-1.5 text-right ${
            isUser ? 'text-blue-200' : 'text-slate-400'
          }`}
        >
          {formattedTime}
        </div>
      </div>
    </div>
  );
};
