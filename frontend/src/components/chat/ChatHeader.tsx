import React from 'react';
import { ChevronLeft, Info } from 'lucide-react';

interface ChatHeaderProps {
  currentRoomId: string;
  onOpenMobileSidebar: () => void;
  onToggleRightSidebar: () => void;
  showRightSidebar: boolean;
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({
  currentRoomId,
  onOpenMobileSidebar,
  onToggleRightSidebar,
  showRightSidebar,
}) => {
  return (
    <header className="h-16 px-4 py-2 bg-[#242526] border-b border-[#393a3b] flex items-center justify-between z-10">
      {/* Thông tin phòng bên trái */}
      <div className="flex items-center space-x-3">
        {/* Nút mở menu trên thiết bị di động */}
        <button
          onClick={onOpenMobileSidebar}
          className="md:hidden p-2 rounded-full hover:bg-[#3a3b3c] text-[#b0b3b8] hover:text-white transition-colors"
          title="Mở danh sách phòng"
        >
          <ChevronLeft className="w-5 h-5" />
        </button>

        {/* Avatar biểu tượng phòng */}
        <div className="relative">
          <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center font-bold text-white shadow-md text-sm">
            {currentRoomId.charAt(0).toUpperCase() || 'R'}
          </div>
          <span className="absolute bottom-0 right-0 w-3 h-3 rounded-full bg-[#31a24c] ring-2 ring-[#242526]" />
        </div>

        {/* Tiêu đề phòng và trạng thái */}
        <div>
          <h3 className="font-semibold text-white leading-tight text-base truncate max-w-[200px] sm:max-w-xs">
            Phòng: {currentRoomId}
          </h3>
          <p className="text-xs text-[#31a24c] flex items-center space-x-1 font-medium">
            <span>● Đang hoạt động</span>
          </p>
        </div>
      </div>

      {/* Nút đóng/mở thông tin phòng bên phải */}
      <div className="flex items-center space-x-1">
        <button
          onClick={onToggleRightSidebar}
          title="Thông tin chi tiết phòng"
          className={`p-2.5 rounded-full transition-colors ${
            showRightSidebar
              ? 'text-[#0084ff] bg-[#0084ff]/10'
              : 'text-[#b0b3b8] hover:bg-[#3a3b3c] hover:text-white'
          }`}
        >
          <Info className="w-5 h-5" />
        </button>
      </div>
    </header>
  );
};

export default ChatHeader;
