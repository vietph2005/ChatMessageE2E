import React from 'react';
import { useChatbot } from '../hooks/useChatbot';
import { ChatWindow } from '../components/chatbot/ChatWindow';
import { ArrowLeft } from 'lucide-react';

interface ChatbotPageProps {
  onBack?: () => void;
}

export const ChatbotPage: React.FC<ChatbotPageProps> = ({ onBack }) => {
  const { messages, isLoading, errorMessage, sendMessage, clearChat } = useChatbot();

  return (
    <div className="h-screen w-screen flex flex-col bg-slate-950 text-slate-100">
      {onBack && (
        <div className="bg-slate-900/90 backdrop-blur-sm border-b border-slate-800 px-4 py-2 flex items-center">
          <button
            type="button"
            onClick={onBack}
            className="flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-blue-400 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Quay lại ứng dụng tin nhắn</span>
          </button>
        </div>
      )}
      <div className="flex-1 overflow-hidden">
        <ChatWindow
          messages={messages}
          isLoading={isLoading}
          errorMessage={errorMessage}
          onSendMessage={sendMessage}
          onClearChat={clearChat}
        />
      </div>
    </div>
  );
};
