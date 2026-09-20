import React from 'react';
import teamLogo from '../assets/team.png';
import { useJoinCreateChat } from '../hooks/useJoinCreateChat';

export const JoinCreateChat: React.FC = () => {
  const {
    detail,
    errorMessage,
    successMessage,
    loading,
    handleInputChange,
    handleJoinChat,
    handleCreateRoom,
  } = useJoinCreateChat();

  return (
    <div className="min-h-screen w-full bg-[#0d131f] flex items-center justify-center p-4 selection:bg-blue-500/30 selection:text-blue-200">
      {/* Container Card */}
      <div className="w-full max-w-[460px] bg-[#141c2e] border border-slate-800/80 rounded-3xl p-8 sm:p-10 shadow-2xl flex flex-col items-center">
        {/* Logo with warm yellow circle matching reference */}
        <div className="w-28 h-28 rounded-full bg-[#f6c343] flex items-center justify-center p-4 shadow-lg shadow-amber-500/20 mb-6 hover:scale-105 transition-transform duration-300">
          <img
            src={teamLogo}
            alt="Chat Logo"
            className="w-20 h-20 object-contain drop-shadow"
          />
        </div>

        {/* Title */}
        <h1 className="text-2xl sm:text-[26px] font-bold text-white text-center mb-8 tracking-wide">
          Join Room / Create Room ..
        </h1>

        {/* Form */}
        <form onSubmit={(e) => e.preventDefault()} className="w-full space-y-6">
          {/* Field: Your name */}
          <div className="space-y-2">
            <label
              htmlFor="userName"
              className="block text-white text-base font-medium pl-1"
            >
              Your name
            </label>
            <input
              type="text"
              id="userName"
              name="userName"
              value={detail.userName}
              onChange={handleInputChange}
              autoComplete="off"
              className="w-full h-12 px-6 rounded-full bg-[#2c374d] text-white text-base outline-none border border-transparent focus:border-blue-500/60 focus:bg-[#323e57] focus:ring-2 focus:ring-blue-500/30 transition-all shadow-inner"
            />
          </div>

          {/* Field: Room ID / New Room ID */}
          <div className="space-y-2">
            <label
              htmlFor="roomId"
              className="block text-white text-base font-medium pl-1"
            >
              Room ID / New Room ID
            </label>
            <input
              type="text"
              id="roomId"
              name="roomId"
              value={detail.roomId}
              onChange={handleInputChange}
              autoComplete="off"
              className="w-full h-12 px-6 rounded-full bg-[#2c374d] text-white text-base outline-none border border-transparent focus:border-blue-500/60 focus:bg-[#323e57] focus:ring-2 focus:ring-blue-500/30 transition-all shadow-inner"
            />
          </div>

          {/* Alert messages */}
          {errorMessage && (
            <div className="text-sm text-red-400 text-center font-medium bg-red-500/10 border border-red-500/20 rounded-xl py-2 px-3">
              {errorMessage}
            </div>
          )}
          {successMessage && (
            <div className="text-sm text-emerald-400 text-center font-medium bg-emerald-500/10 border border-emerald-500/20 rounded-xl py-2 px-3">
              {successMessage}
            </div>
          )}

          {/* Buttons */}
          <div className="flex items-center justify-center gap-4 pt-4">
            <button
              type="button"
              onClick={handleJoinChat}
              disabled={loading}
              className="px-7 py-3 rounded-full bg-[#2563EB] hover:bg-[#1d4ed8] active:scale-95 text-white font-medium text-base shadow-md shadow-blue-500/25 transition-all cursor-pointer disabled:opacity-60"
            >
              {loading ? 'Đang vào...' : 'Join Room'}
            </button>

            <button
              type="button"
              onClick={handleCreateRoom}
              disabled={loading}
              className="px-7 py-3 rounded-full bg-[#f97316] hover:bg-[#ea580c] active:scale-95 text-white font-medium text-base shadow-md shadow-orange-500/25 transition-all cursor-pointer disabled:opacity-60"
            >
              {loading ? 'Đang tạo...' : 'Create Room'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default JoinCreateChat;
