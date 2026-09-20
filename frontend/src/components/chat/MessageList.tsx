import React from 'react';
import { Message } from '../../hooks/useChat';

interface MessageListProps {
  messages: Message[];
  currentUserName: string;
  messagesEndRef: React.RefObject<HTMLDivElement>;
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  messagesEndRef,
}) => {
  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {/* Khi phòng chưa có tin nhắn nào */}
      {messages.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-full text-center text-[#b0b3b8] py-12">
          <div className="w-16 h-16 rounded-full bg-[#3a3b3c] flex items-center justify-center text-2xl font-bold mb-3 text-slate-300">
            💬
          </div>
          <p className="text-base font-semibold text-white">Chưa có tin nhắn nào</p>
          <p className="text-xs text-[#b0b3b8] mt-1">Hãy gửi tin nhắn đầu tiên để bắt đầu cuộc trò chuyện!</p>
        </div>
      ) : (
        /* Danh sách tin nhắn */
        messages.map((msg) => {
          const isMe = msg.isMe;

          return (
            <div
              key={msg.id}
              className={`flex flex-col ${isMe ? 'items-end' : 'items-start'} max-w-full`}
            >
              {/* Tên người gửi nếu không phải chính mình */}
              {!isMe && (
                <span className="text-[11px] text-[#b0b3b8] mb-1 pl-2 font-medium">
                  {msg.senderName}
                </span>
              )}

              {/* Bong bóng tin nhắn */}
              <div
                className={`max-w-[75%] sm:max-w-[65%] px-4 py-2.5 rounded-2xl break-words text-sm shadow-sm ${
                  isMe
                    ? 'bg-[#0084ff] text-white rounded-br-sm'
                    : 'bg-[#3a3b3c] text-[#e4e6eb] rounded-bl-sm'
                }`}
              >
                {msg.content}
              </div>

              {/* Thời gian gửi */}
              <span className="text-[10px] text-[#b0b3b8] mt-1 px-1">
                {msg.timestamp}
              </span>
            </div>
          );
        })
      )}

      {/* Điểm neo để tự động cuộn xuống cuối */}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default MessageList;
