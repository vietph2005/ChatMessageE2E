import React from 'react';
import { ShieldCheck, ShieldAlert, Lock } from 'lucide-react';
import { ConversationSummaryDto } from '../../services/apiClient';

interface Props {
  conversation: ConversationSummaryDto;
  isActive: boolean;
  onSelect: () => void;
}

export const ConversationItem: React.FC<Props> = ({
  conversation,
  isActive,
  onSelect,
}) => {
  const { peerUser, status, lastMessageSnippet, lastMessageAt, unreadCount } = conversation;

  const isVerified = status === 'VERIFIED_ACTIVE';

  const formattedTime = lastMessageAt
    ? new Date(lastMessageAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : '';

  return (
    <div
      onClick={onSelect}
      className={`p-3 mx-2 my-1 rounded-2xl cursor-pointer flex items-center space-x-3 transition-all duration-200 ${
        isActive
          ? 'bg-blue-600/20 border border-blue-500/30 text-white shadow-sm'
          : 'hover:bg-slate-900/80 text-slate-300 border border-transparent'
      }`}
    >
      {/* Avatar */}
      <div className="relative shrink-0">
        <img
          src={peerUser.avatarUrl || 'https://lh3.googleusercontent.com/a/default-avatar'}
          alt={peerUser.displayName}
          className="w-12 h-12 rounded-full object-cover ring-2 ring-white/10"
        />
        {peerUser.isOnline && (
          <span className="absolute bottom-0 right-0 w-3.5 h-3.5 rounded-full bg-emerald-500 ring-2 ring-slate-950 shadow-sm shadow-emerald-500/50" />
        )}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-white truncate flex items-center space-x-1">
            <span>{peerUser.displayName}</span>
            {isVerified ? (
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 inline shrink-0" />
            ) : (
              <ShieldAlert className="w-3.5 h-3.5 text-amber-400 inline shrink-0" />
            )}
          </h3>
          <span className="text-[10px] text-slate-500 shrink-0 ml-1">{formattedTime}</span>
        </div>

        <div className="flex items-center justify-between mt-1">
          <p className="text-xs text-slate-400 truncate flex items-center space-x-1">
            <Lock className="w-3 h-3 inline text-slate-500 shrink-0 mr-1" />
            <span>{lastMessageSnippet || (isVerified ? 'No messages yet' : 'Handshake in progress...')}</span>
          </p>

          {unreadCount > 0 && (
            <span className="w-4 h-4 rounded-full bg-messenger-blue text-white text-[10px] font-bold flex items-center justify-center shrink-0 ml-2">
              {unreadCount}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
