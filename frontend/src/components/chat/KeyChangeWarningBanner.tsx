import React from 'react';
import { AlertTriangle, ShieldCheck, X } from 'lucide-react';

interface Props {
  peerName: string;
  onVerifySafetyNumber: () => void;
  onDismiss: () => void;
}

export const KeyChangeWarningBanner: React.FC<Props> = ({
  peerName,
  onVerifySafetyNumber,
  onDismiss,
}) => {
  return (
    <div className="mx-4 my-2 p-3.5 bg-amber-500/10 border border-amber-500/30 rounded-2xl flex items-center justify-between animate-in fade-in slide-in-from-top-2">
      <div className="flex items-center space-x-3">
        <div className="w-8 h-8 rounded-xl bg-amber-500/20 text-amber-400 flex items-center justify-center shrink-0">
          <AlertTriangle className="w-4 h-4" />
        </div>
        <div>
          <p className="text-xs font-bold text-amber-300">Safety Number Changed</p>
          <p className="text-[11px] text-amber-200/80">
            {peerName}'s security keys have changed. Tap to verify the new safety code.
          </p>
        </div>
      </div>

      <div className="flex items-center space-x-2">
        <button
          onClick={onVerifySafetyNumber}
          className="px-3 py-1.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs rounded-xl shadow-sm transition-all flex items-center space-x-1"
        >
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Verify</span>
        </button>
        <button
          onClick={onDismiss}
          className="p-1 text-amber-400 hover:text-amber-200 rounded-full hover:bg-amber-500/20"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
