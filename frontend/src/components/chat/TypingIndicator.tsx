import React from 'react';

interface Props {
  peerAvatarUrl?: string;
}

export const TypingIndicator: React.FC<Props> = ({ peerAvatarUrl }) => {
  return (
    <div className="flex items-end space-x-2 my-2 animate-in fade-in slide-in-from-bottom-1">
      <img
        src={peerAvatarUrl || 'https://lh3.googleusercontent.com/a/default-avatar'}
        alt="Avatar"
        className="w-6 h-6 rounded-full object-cover ring-1 ring-white/10"
      />
      <div className="px-3.5 py-2.5 rounded-2xl rounded-bl-sm glass-bubble-recipient flex items-center space-x-1">
        <span className="w-1.5 h-1.5 rounded-full bg-slate-300 animate-bounce [animation-delay:-0.3s]"></span>
        <span className="w-1.5 h-1.5 rounded-full bg-slate-300 animate-bounce [animation-delay:-0.15s]"></span>
        <span className="w-1.5 h-1.5 rounded-full bg-slate-300 animate-bounce"></span>
      </div>
    </div>
  );
};
