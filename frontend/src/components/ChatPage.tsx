import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useChat } from '../hooks/useChat';
import { ChatSidebar } from './chat/ChatSidebar';
import { ChatHeader } from './chat/ChatHeader';
import { MessageList } from './chat/MessageList';
import { MessageInput } from './chat/MessageInput';
import { ChatInfoSidebar } from './chat/ChatInfoSidebar';

export const ChatPage: React.FC = () => {
  const navigate = useNavigate();

  const {
    currentUserName,
    currentRoomId,
    messages,
    inputText,
    setInputText,
    conversations,
    showRightSidebar,
    setShowRightSidebar,
    showMobileSidebar,
    setShowMobileSidebar,
    messagesEndRef,
    handleSendMessage,
  } = useChat();

  return (
    <div className="flex h-screen w-full bg-[#18191a] text-[#e4e6eb] font-sans antialiased overflow-hidden selection:bg-[#0084ff]/30 selection:text-white">
      {/* 1. Cột danh sách phòng bên trái */}
      <ChatSidebar
        currentUserName={currentUserName}
        currentRoomId={currentRoomId}
        conversations={conversations}
        showMobileSidebar={showMobileSidebar}
        onCloseMobileSidebar={() => setShowMobileSidebar(false)}
        onNavigateJoin={() => navigate('/join')}
      />

      {/* 2. Khung chat trung tâm */}
      <div className="flex-1 flex flex-col h-full bg-[#18191a] relative overflow-hidden">
        <ChatHeader
          currentRoomId={currentRoomId}
          showRightSidebar={showRightSidebar}
          onOpenMobileSidebar={() => setShowMobileSidebar(true)}
          onToggleRightSidebar={() => setShowRightSidebar((prev) => !prev)}
        />

        <MessageList
          messages={messages}
          currentUserName={currentUserName}
          messagesEndRef={messagesEndRef}
        />

        <MessageInput
          inputText={inputText}
          setInputText={setInputText}
          onSendMessage={handleSendMessage}
        />
      </div>

      {/* 3. Cột thông tin chi tiết phòng bên phải */}
      <ChatInfoSidebar
        currentRoomId={currentRoomId}
        showRightSidebar={showRightSidebar}
      />
    </div>
  );
};

export default ChatPage;
