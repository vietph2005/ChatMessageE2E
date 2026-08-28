import React, { useState } from 'react';
import { Search, UserPlus, ShieldAlert, CheckCircle2, Loader2 } from 'lucide-react';
import { apiClient, UserProfileDto } from '../../services/apiClient';
import { useAuth } from '../../hooks/useAuth';

interface Props {
  onStartChat: (recipientEmail: string) => Promise<void>;
}

export const ExactGmailSearchBar: React.FC<Props> = ({ onStartChat }) => {
  const { user } = useAuth();
  const [emailQuery, setEmailQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [foundUser, setFoundUser] = useState<UserProfileDto | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!emailQuery.trim()) return;

    if (emailQuery.toLowerCase().trim() === user?.email.toLowerCase().trim()) {
      setError('You cannot initiate a 1-1 chat with yourself.');
      setFoundUser(null);
      return;
    }

    setIsSearching(true);
    setError(null);
    setFoundUser(null);

    try {
      const result = await apiClient.searchUserByGmail(emailQuery.trim());
      setFoundUser(result);
    } catch (err: any) {
      setError(err.message || 'No user registered with this exact Gmail address.');
    } finally {
      setIsSearching(false);
    }
  };

  const handleInitiate = async () => {
    if (!foundUser) return;
    try {
      await onStartChat(foundUser.email);
      setEmailQuery('');
      setFoundUser(null);
    } catch (e: any) {
      setError(e.message || 'Failed to start chat');
    }
  };

  return (
    <div className="w-full px-3 py-2">
      <form onSubmit={handleSearch} className="relative">
        <input
          type="email"
          value={emailQuery}
          onChange={(e) => {
            setEmailQuery(e.target.value);
            if (error) setError(null);
          }}
          placeholder="Search by exact Gmail address..."
          className="w-full bg-slate-900/90 text-xs text-white placeholder:text-slate-500 pl-8 pr-16 py-2.5 rounded-2xl border border-white/10 focus:outline-none focus:border-blue-500 transition-all"
        />
        <Search className="w-4 h-4 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />

        <button
          type="submit"
          disabled={isSearching || !emailQuery.trim()}
          className="absolute right-1.5 top-1/2 -translate-y-1/2 px-2.5 py-1 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white text-[11px] font-semibold rounded-xl transition-all"
        >
          {isSearching ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : 'Find'}
        </button>
      </form>

      {/* Search Result Dropdown Card */}
      {foundUser && (
        <div className="mt-2 p-3 rounded-2xl bg-slate-900 border border-blue-500/30 shadow-lg shadow-blue-500/10 flex items-center justify-between animate-in fade-in slide-in-from-top-2">
          <div className="flex items-center space-x-2.5 min-w-0">
            <img
              src={foundUser.avatarUrl || 'https://lh3.googleusercontent.com/a/default-avatar'}
              alt={foundUser.displayName}
              className="w-8 h-8 rounded-full ring-2 ring-blue-500/50 object-cover"
            />
            <div className="min-w-0">
              <p className="text-xs font-bold text-white truncate flex items-center gap-1">
                {foundUser.displayName}
                <CheckCircle2 className="w-3.5 h-3.5 text-blue-400 inline shrink-0" />
              </p>
              <p className="text-[10px] text-slate-400 truncate">{foundUser.email}</p>
            </div>
          </div>

          <button
            onClick={handleInitiate}
            className="px-3 py-1.5 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white text-xs font-semibold rounded-xl shadow-sm flex items-center space-x-1 shrink-0 ml-2"
          >
            <UserPlus className="w-3.5 h-3.5" />
            <span>Connect</span>
          </button>
        </div>
      )}

      {error && (
        <div className="mt-2 p-2 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-[11px] flex items-center space-x-1.5">
          <ShieldAlert className="w-3.5 h-3.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
};
