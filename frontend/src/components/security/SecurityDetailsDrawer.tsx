import React from 'react';
import { ShieldCheck, UserCheck, Lock, KeyRound, X } from 'lucide-react';
import { ConversationDetailDto } from '../../services/apiClient';
import { SafetyNumberQrCode } from './SafetyNumberQrCode';
import { BlockContactButton } from './BlockContactButton';

interface Props {
  conversation: ConversationDetailDto;
  peerDisplayName: string;
  peerAvatarUrl?: string;
  peerUserId: string;
  onClose: () => void;
  onBlocked: () => void;
}

export const SecurityDetailsDrawer: React.FC<Props> = ({
  conversation,
  peerDisplayName,
  peerAvatarUrl,
  peerUserId,
  onClose,
  onBlocked,
}) => {
  const { handshake } = conversation;

  return (
    <div className="fixed inset-y-0 right-0 z-40 w-full sm:w-96 glass-panel border-l border-white/10 p-6 flex flex-col justify-between shadow-2xl overflow-y-auto animate-in slide-in-from-right duration-200">
      <div>
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-white/10">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-5 h-5 text-cyan-400" />
            <h3 className="text-sm font-bold text-white">Conversation Security</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-full text-slate-400 hover:text-white hover:bg-slate-800"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Contact Overview */}
        <div className="text-center py-5">
          <img
            src={peerAvatarUrl || 'https://lh3.googleusercontent.com/a/default-avatar'}
            alt={peerDisplayName}
            className="w-16 h-16 rounded-full mx-auto object-cover ring-2 ring-blue-500/50 mb-2"
          />
          <h4 className="text-base font-bold text-white">{peerDisplayName}</h4>
          <span className="inline-block mt-1 px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 text-xs font-semibold">
            {conversation.status === 'VERIFIED_ACTIVE' ? '4-Layer E2EE Verified' : 'Handshake Pending'}
          </span>
        </div>

        {/* 4-Layer Verification Audit Trail */}
        <div className="space-y-2 mb-6">
          <p className="text-xs uppercase font-semibold text-slate-400">Security Verification Status</p>

          <div className="p-3 bg-slate-900/80 rounded-xl border border-white/5 flex items-center justify-between text-xs">
            <div className="flex items-center space-x-2 text-slate-300">
              <UserCheck className="w-4 h-4 text-emerald-400" />
              <span>Layer 1: Google Identity</span>
            </div>
            <span className="text-emerald-400 font-semibold">{handshake?.layer1Status || 'VERIFIED'}</span>
          </div>

          <div className="p-3 bg-slate-900/80 rounded-xl border border-white/5 flex items-center justify-between text-xs">
            <div className="flex items-center space-x-2 text-slate-300">
              <Lock className="w-4 h-4 text-emerald-400" />
              <span>Layer 2: Mutual Consent</span>
            </div>
            <span className="text-emerald-400 font-semibold">{handshake?.layer2Status || 'ACCEPTED'}</span>
          </div>

          <div className="p-3 bg-slate-900/80 rounded-xl border border-white/5 flex items-center justify-between text-xs">
            <div className="flex items-center space-x-2 text-slate-300">
              <KeyRound className="w-4 h-4 text-emerald-400" />
              <span>Layer 3: Pre-Key Exchange</span>
            </div>
            <span className="text-emerald-400 font-semibold">{handshake?.layer3Status || 'EXCHANGED'}</span>
          </div>

          <div className="p-3 bg-slate-900/80 rounded-xl border border-white/5 flex items-center justify-between text-xs">
            <div className="flex items-center space-x-2 text-slate-300">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>Layer 4: Safety Code</span>
            </div>
            <span className="text-emerald-400 font-semibold">{handshake?.layer4Status || 'CONFIRMED'}</span>
          </div>
        </div>

        {/* Safety QR & Fingerprint */}
        {handshake?.safetyCode && (
          <div className="mb-6 text-center">
            <p className="text-xs uppercase font-semibold text-slate-400 mb-2">Safety Number QR</p>
            <SafetyNumberQrCode
              conversationId={conversation.id}
              safetyCode={handshake.safetyCode}
              fullFingerprintHex={handshake.fullFingerprintHex || ''}
            />
            <div className="mt-3 text-lg font-mono font-bold tracking-widest text-cyan-300">
              {handshake.safetyCode.slice(0, 3)} {handshake.safetyCode.slice(3)}
            </div>
            <p className="text-[10px] font-mono text-slate-500 break-all mt-1">
              {handshake.fullFingerprintHex}
            </p>
          </div>
        )}
      </div>

      {/* Footer / Actions */}
      <div className="pt-4 border-t border-white/10 flex items-center justify-between">
        <span className="text-xs text-slate-400">Danger Zone</span>
        <BlockContactButton
          peerUserId={peerUserId}
          peerDisplayName={peerDisplayName}
          onBlocked={onBlocked}
        />
      </div>
    </div>
  );
};
