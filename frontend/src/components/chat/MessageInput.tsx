import React from 'react';
import { Send } from 'lucide-react';

interface MessageInputProps {
  inputText: string;
  setInputText: (value: string) => void;
  onSendMessage: (e?: React.FormEvent) => void;
}

export const MessageInput: React.FC<MessageInputProps> = ({
  inputText,
  setInputText,
  onSendMessage,
}) => {
  return (
    <div className="p-3 bg-[#242526] border-t border-[#393a3b]">
      <form onSubmit={onSendMessage} className="flex items-center gap-2 max-w-5xl mx-auto">
        {/* Ô nhập tin nhắn */}
        <input
          type="text"
          placeholder="Nhập tin nhắn..."
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          className="flex-1 bg-[#3a3b3c] text-white placeholder-[#b0b3b8] text-sm px-4 py-2.5 rounded-full outline-none focus:ring-2 focus:ring-[#0084ff]/50 transition-all"
        />

        {/* Nút gửi tin nhắn */}
        <button
          type="submit"
          disabled={!inputText.trim()}
          title="Gửi tin nhắn"
          className="p-2.5 rounded-full bg-[#0084ff] hover:bg-[#0073e6] active:scale-95 text-white transition-all disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer shadow-md shadow-blue-500/20"
        >
          <Send className="w-5 h-5" />
        </button>
      </form>
    </div>
  );
};

export default MessageInput;
