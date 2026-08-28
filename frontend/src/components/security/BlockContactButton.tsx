import React, { useState } from 'react';
import { Ban, Loader2 } from 'lucide-react';
import { apiClient } from '../../services/apiClient';

interface Props {
  peerUserId: string;
  peerDisplayName: string;
  onBlocked: () => void;
}

export const BlockContactButton: React.FC<Props> = ({
  peerUserId,
  peerDisplayName,
  onBlocked,
}) => {
  const [isBlocking, setIsBlocking] = useState(false);

  const handleBlock = async () => {
    if (!window.confirm(`Are you sure you want to block ${peerDisplayName}? You will no longer receive messages from them.`)) {
      return;
    }

    setIsBlocking(true);
    try {
      await apiClient.blockUser(peerUserId);
      onBlocked();
    } catch (e: any) {
      alert(e.message || 'Failed to block user');
    } finally {
      setIsBlocking(false);
    }
  };

  return (
    <button
      onClick={handleBlock}
      disabled={isBlocking}
      className="p-2 rounded-full text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors"
      title={`Block ${peerDisplayName}`}
    >
      {isBlocking ? <Loader2 className="w-4 h-4 animate-spin" /> : <Ban className="w-4 h-4" />}
    </button>
  );
};
