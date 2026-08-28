import React from 'react';
import { ShieldCheck, Check } from 'lucide-react';

interface Props {
  safetyCode: string;
  peerName: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export const SafetyCodeConfirmDialog: React.FC<Props> = ({
  safetyCode,
  peerName,
  onConfirm,
  onCancel,
}) => {
  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-sm p-6 glass-panel rounded-3xl border border-white/10 text-center shadow-2xl animate-in zoom-in-95">
        <div className="w-14 h-14 mx-auto rounded-2xl bg-cyan-500/20 text-cyan-400 flex items-center justify-center mb-4">
          <ShieldCheck className="w-8 h-8" />
        </div>

        <h3 className="text-base font-bold text-white">Confirm Security Safety Code</h3>
        <p className="text-xs text-slate-400 mt-1">
          Verify that this 6-digit code matches the code displayed on <span className="text-slate-200 font-semibold">{peerName}</span>'s device.
        </p>

        <div className="my-6 py-3 px-4 bg-slate-900/90 rounded-2xl border border-cyan-500/30">
          <span className="text-3xl font-mono font-extrabold tracking-widest text-cyan-300">
            {safetyCode.slice(0, 3)} {safetyCode.slice(3)}
          </span>
        </div>

        <div className="flex space-x-2.5">
          <button
            onClick={onCancel}
            className="flex-1 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 py-2.5 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white rounded-xl text-xs font-bold shadow-md shadow-blue-500/20 flex items-center justify-center space-x-1.5"
          >
            <Check className="w-4 h-4" />
            <span>Confirm Match</span>
          </button>
        </div>
      </div>
    </div>
  );
};
