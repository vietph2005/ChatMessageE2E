import React from 'react';
import { Bot, User, AlertCircle, Sparkles } from 'lucide-react';
import { SourceBadge } from './SourceBadge';
import { FaqSource } from '../../services/chatbotService';

export interface ChatMessageItem {
  id: string;
  role: 'user' | 'bot';
  content: string;
  sources?: FaqSource[];
  hasContext?: boolean;
  timestamp: Date;
  status: 'sending' | 'done' | 'error';
}

interface MessageBubbleProps {
  message: ChatMessageItem;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user';
  const formattedTime = new Intl.DateTimeFormat('vi-VN', {
    hour: '2-digit',
    minute: '2-digit',
  }).format(message.timestamp);

  if (isUser) {
    return (
      <div className="flex justify-end mb-4 animate-in fade-in duration-200">
        <div className="flex items-end gap-2 max-w-[85%] md:max-w-[70%]">
          <div className="flex flex-col items-end">
            <div className="px-4 py-2.5 rounded-2xl rounded-tr-sm bg-blue-600 text-white shadow-md text-sm leading-relaxed whitespace-pre-wrap">
              {message.content}
            </div>
            <span className="text-[10px] text-slate-400 mt-1 px-1">
              {formattedTime}
            </span>
          </div>
          <div className="w-8 h-8 rounded-full bg-blue-500/20 border border-blue-400/40 flex items-center justify-center text-blue-300 shrink-0">
            <User className="w-4 h-4" />
          </div>
        </div>
      </div>
    );
  }

  // Bot message
  const hasSources = message.sources && message.sources.length > 0;
  const isOutOfScope = message.hasContext === false;

  return (
    <div className="flex justify-start mb-4 animate-in fade-in duration-200">
      <div className="flex items-start gap-2.5 max-w-[90%] md:max-w-[75%]">
        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-600 to-blue-500 flex items-center justify-center text-white shadow-md shrink-0 mt-0.5">
          <Bot className="w-4 h-4" />
        </div>

        <div className="flex flex-col items-start w-full">
          <div className="w-full px-4 py-3 rounded-2xl rounded-tl-sm bg-slate-900 border border-slate-800 text-slate-100 shadow-md text-sm leading-relaxed">
            {/* Header with bot badge */}
            <div className="flex items-center gap-1.5 text-xs text-indigo-400 font-medium mb-1.5">
              <Sparkles className="w-3 h-3" />
              <span>Trợ lý ChatMessage</span>
            </div>

            {/* Content */}
            <div className="whitespace-pre-wrap text-slate-200 font-normal">
              {message.content}
            </div>

            {/* Out-of-scope notice if applicable */}
            {isOutOfScope && (
              <div className="mt-3 p-2 rounded-lg bg-amber-950/30 border border-amber-800/40 flex items-center gap-2 text-xs text-amber-300">
                <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                <span>Câu hỏi nằm ngoài kiến thức hệ thống. Vui lòng hỏi các chủ đề về ChatMessage.</span>
              </div>
            )}

            {/* Sources list */}
            {hasSources && (
              <div className="mt-3 pt-2.5 border-t border-slate-800/80">
                <p className="text-[11px] font-semibold text-slate-400 mb-1.5 flex items-center gap-1">
                  <span>Tài liệu FAQ tham khảo:</span>
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {message.sources!.map((src) => (
                    <SourceBadge key={src.id} source={src} />
                  ))}
                </div>
              </div>
            )}
          </div>

          <span className="text-[10px] text-slate-400 mt-1 px-1">
            {formattedTime}
          </span>
        </div>
      </div>
    </div>
  );
};
