import React from 'react';
import { Undo2, Trash2 } from 'lucide-react';

interface Props {
  isSender: boolean;
  onUnsendEveryone?: () => void;
  onDeleteForMe: () => void;
  onClose: () => void;
}

export const MessageActionsMenu: React.FC<Props> = ({
  isSender,
  onUnsendEveryone,
  onDeleteForMe,
  onClose,
}) => {
  return (
    <div className="absolute right-0 bottom-full mb-1 z-30 min-w-[150px] p-1 glass-panel rounded-2xl border border-white/10 shadow-2xl animate-in fade-in zoom-in-95">
      {isSender && onUnsendEveryone && (
        <button
          onClick={() => {
            onUnsendEveryone();
            onClose();
          }}
          className="w-full px-3 py-2 text-left text-xs font-semibold text-rose-300 hover:bg-rose-500/20 rounded-xl flex items-center space-x-2 transition-all"
        >
          <Undo2 className="w-3.5 h-3.5" />
          <span>Unsend for Everyone</span>
        </button>
      )}

      <button
        onClick={() => {
          onDeleteForMe();
          onClose();
        }}
        className="w-full px-3 py-2 text-left text-xs font-semibold text-slate-300 hover:bg-slate-800 rounded-xl flex items-center space-x-2 transition-all"
      >
        <Trash2 className="w-3.5 h-3.5 text-slate-400" />
        <span>Delete for Me</span>
      </button>
    </div>
  );
};
