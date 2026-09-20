import React from 'react';
import { LogOut, X } from 'lucide-react';
import teamLogo from '../../assets/team.png';
import { ChatConversation } from '../../hooks/useChat';

interface ChatSidebarProps {
  currentUserName: string;
  currentRoomId: string;
  conversations: ChatConversation[];
  showMobileSidebar: boolean;
  onCloseMobileSidebar: () => void;
  onNavigateJoin: () => void;
}

export const ChatSidebar: React.FC<ChatSidebarProps> = ({
  currentUserName,
  currentRoomId,
  conversations,
  showMobileSidebar,
  onCloseMobileSidebar,
  onNavigateJoin,
}) => {
  return (
    <aside
      className={`fixed inset-y-0 left-0 z-30 w-80 lg:w-96 bg-[#242526] border-r border-[#393a3b] flex flex-col transition-transform duration-300 ease-in-out md:static md:translate-x-0 ${
        showMobileSidebar ? 'translate-x-0' : '-translate-x-full'
      }`}
    >
      {/* Sidebar Header */}
      <div className="p-4 flex items-center justify-between border-b border-[#393a3b]/50">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-full bg-[#f6c343] flex items-center justify-center p-2 ring-2 ring-blue-500/30">
            <img src={teamLogo} alt="App Logo" className="w-6 h-6 object-contain" />
          </div>
          <div>
            <h2 className="text-xl font-bold tracking-tight text-white">Đoạn chat</h2>
            <p className="text-xs text-[#b0b3b8]">@{currentUserName}</p>
          </div>
        </div>
        <div className="flex items-center space-x-1">
          <button
            onClick={onNavigateJoin}
            title="Rời phòng / Đổi phòng"
            className="p-2 rounded-full hover:bg-[#3a3b3c] text-[#b0b3b8] hover:text-white transition-colors cursor-pointer"
          >
            <LogOut className="w-5 h-5" />
          </button>
          <button
            onClick={onCloseMobileSidebar}
            className="md:hidden p-2 rounded-full hover:bg-[#3a3b3c] text-[#b0b3b8] cursor-pointer"
            title="Đóng sidebar"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Danh sách phòng chat */}
      <div className="flex-1 overflow-y-auto px-2 py-3 space-y-1">
        {conversations.map((chat) => {
          const isCurrent = chat.id === currentRoomId;

          return (
            <div
              key={chat.id}
              className={`flex items-center px-3 py-3 rounded-xl cursor-pointer transition-colors ${
                isCurrent ? 'bg-[#3a3b3c]' : 'hover:bg-[#3a3b3c]/50'
              }`}
            >
              <div className="relative flex-shrink-0 mr-3">
                <div className="w-12 h-12 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center font-bold text-white shadow-md">
                  {chat.name.charAt(0).toUpperCase()}
                </div>
                {chat.isOnline && (
                  <span className="absolute bottom-0 right-0 w-3.5 h-3.5 rounded-full bg-[#31a24c] ring-2 ring-[#242526]" />
                )}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex justify-between items-baseline mb-0.5">
                  <h4 className="text-sm font-semibold text-white truncate">{chat.name}</h4>
                  <span className="text-[11px] text-[#b0b3b8] ml-2 flex-shrink-0">{chat.time}</span>
                </div>
                <p className="text-xs text-[#b0b3b8] truncate">{chat.lastMessage}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Thanh thông tin người dùng ở góc dưới */}
      <div className="p-3 bg-[#1e1f20] border-t border-[#393a3b] flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="relative">
            <div className="w-9 h-9 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold text-sm">
              {currentUserName.charAt(0).toUpperCase()}
            </div>
            <span className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-[#31a24c] ring-2 ring-[#1e1f20]" />
          </div>
          <div>
            <p className="text-xs font-semibold text-white leading-tight">{currentUserName}</p>
            <p className="text-[10px] text-[#31a24c] font-medium">Đang hoạt động</p>
          </div>
        </div>
        <button
          onClick={onNavigateJoin}
          className="text-xs text-[#0084ff] hover:underline font-medium cursor-pointer"
        >
          Đổi phòng
        </button>
      </div>
    </aside>
  );
};

export default ChatSidebar;
