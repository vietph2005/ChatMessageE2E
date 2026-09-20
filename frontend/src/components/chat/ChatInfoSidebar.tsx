import React from 'react';
import { ShieldCheck, Users, Bell, Search } from 'lucide-react';

interface ChatInfoSidebarProps {
  currentRoomId: string;
  showRightSidebar: boolean;
}

export const ChatInfoSidebar: React.FC<ChatInfoSidebarProps> = ({
  currentRoomId,
  showRightSidebar,
}) => {
  if (!showRightSidebar) return null;

  return (
    <aside className="hidden lg:flex w-80 bg-[#242526] border-l border-[#393a3b] flex-col overflow-y-auto">
      {/* Header Profile Info */}
      <div className="p-6 flex flex-col items-center text-center border-b border-[#393a3b]">
        <div className="relative mb-3">
          <div className="w-20 h-20 rounded-full bg-gradient-to-tr from-[#0084ff] to-cyan-400 flex items-center justify-center font-bold text-2xl text-white shadow-lg">
            {currentRoomId.charAt(0).toUpperCase() || 'R'}
          </div>
          <span className="absolute bottom-1 right-1 w-4 h-4 rounded-full bg-[#31a24c] ring-2 ring-[#242526]" />
        </div>
        <h3 className="text-base font-bold text-white">Phòng: {currentRoomId}</h3>
        <p className="text-xs text-[#31a24c] font-medium mt-0.5">Đang hoạt động</p>

        {/* Quick Actions */}
        <div className="flex items-center justify-center gap-6 mt-4">
          <div className="flex flex-col items-center">
            <button className="w-9 h-9 rounded-full bg-[#3a3b3c] hover:bg-[#4e4f50] flex items-center justify-center text-white transition-colors cursor-pointer">
              <Users className="w-4 h-4" />
            </button>
            <span className="text-[11px] text-[#b0b3b8] mt-1">Thành viên</span>
          </div>
          <div className="flex flex-col items-center">
            <button className="w-9 h-9 rounded-full bg-[#3a3b3c] hover:bg-[#4e4f50] flex items-center justify-center text-white transition-colors cursor-pointer">
              <Bell className="w-4 h-4" />
            </button>
            <span className="text-[11px] text-[#b0b3b8] mt-1">Thông báo</span>
          </div>
          <div className="flex flex-col items-center">
            <button className="w-9 h-9 rounded-full bg-[#3a3b3c] hover:bg-[#4e4f50] flex items-center justify-center text-white transition-colors cursor-pointer">
              <Search className="w-4 h-4" />
            </button>
            <span className="text-[11px] text-[#b0b3b8] mt-1">Tìm kiếm</span>
          </div>
        </div>
      </div>

      {/* Thông tin mã hóa E2EE */}
      <div className="p-4 space-y-2 text-sm text-[#e4e6eb]">
        <div className="p-3 rounded-xl bg-[#3a3b3c]/40 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <span className="font-semibold text-xs">Mã hóa đầu cuối E2EE</span>
          </div>
          <span className="text-[10px] text-emerald-400 font-bold bg-emerald-500/10 px-2 py-0.5 rounded-full">
            Bật
          </span>
        </div>
      </div>
    </aside>
  );
};

export default ChatInfoSidebar;
