import React from 'react';
import { ShieldAlert, ShieldCheck, X } from 'lucide-react';

interface Props {
  peerDisplayName: string;
  onVerify: () => void;
  onDismiss: () => void;
}

export const SafetyNumberAlertBanner: React.FC<Props> = ({
  peerDisplayName,
  onVerify,
  onDismiss,
}) => {
  return (
    <div className="mx-4 my-2 p-3 bg-amber-500/10 border border-amber-500/30 rounded-2xl flex items-center justify-between animate-in fade-in">
      <div className="flex items-center space-x-2.5">
        <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0" />
        <span className="text-xs text-amber-200">
          Your safety number with <strong className="text-white">{peerDisplayName}</strong> has changed.
        </span>
      </div>

      <div className="flex items-center space-x-2">
        <button
          onClick={onVerify}
          className="px-2.5 py-1 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs rounded-xl flex items-center space-x-1"
        >
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Verify</span>
        </button>
        <button
          onClick={onDismiss}
          className="p-1 text-amber-400 hover:text-white rounded-full"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
