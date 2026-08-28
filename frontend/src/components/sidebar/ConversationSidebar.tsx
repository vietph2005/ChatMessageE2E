import React from 'react';
import { LogOut, MessageSquarePlus } from 'lucide-react';
import { ConversationSummaryDto } from '../../services/apiClient';
import { ExactGmailSearchBar } from './ExactGmailSearchBar';
import { ConversationItem } from './ConversationItem';
import { useAuth } from '../../hooks/useAuth';

interface Props {
  conversations: ConversationSummaryDto[];
  activeConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onStartChat: (recipientEmail: string) => Promise<void>;
}

export const ConversationSidebar: React.FC<Props> = ({
  conversations,
  activeConversationId,
  onSelectConversation,
  onStartChat,
}) => {
  const { user, logout } = useAuth();

  return (
    <div className="w-full md:w-80 lg:w-96 h-full flex flex-col glass-panel border-r border-white/10 select-none">
      {/* User App Header */}
      <div className="p-4 flex items-center justify-between border-b border-white/10">
        <div className="flex items-center space-x-3 min-w-0">
          <div className="relative">
            <img
              src={user?.avatarUrl || 'https://lh3.googleusercontent.com/a/default-avatar'}
              alt={user?.displayName}
              className="w-10 h-10 rounded-full object-cover ring-2 ring-blue-500/50"
            />
            <span className="absolute bottom-0 right-0 w-3 h-3 rounded-full bg-emerald-500 ring-2 ring-slate-950" />
          </div>

          <div className="min-w-0">
            <h1 className="text-sm font-bold text-white truncate">{user?.displayName}</h1>
            <p className="text-[11px] text-slate-400 truncate">{user?.email}</p>
          </div>
        </div>

        <button
          onClick={logout}
          className="p-2 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-full transition-colors"
          title="Sign Out"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>

      {/* Exact Gmail Search for privacy */}
      <ExactGmailSearchBar onStartChat={onStartChat} />

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto py-2">
        {conversations.length > 0 ? (
          conversations.map((conv) => (
            <ConversationItem
              key={conv.id}
              conversation={conv}
              isActive={conv.id === activeConversationId}
              onSelect={() => onSelectConversation(conv.id)}
            />
          ))
        ) : (
          <div className="h-64 flex flex-col items-center justify-center p-6 text-center text-slate-500">
            <MessageSquarePlus className="w-10 h-10 mb-2 opacity-50 text-slate-400" />
            <p className="text-sm font-semibold text-slate-300">No conversations yet</p>
            <p className="text-xs text-slate-500 mt-1 max-w-xs">
              Search a contact by their exact Gmail address above to begin a secure 4-layer verified chat.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
