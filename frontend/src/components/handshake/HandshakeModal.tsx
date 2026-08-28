import React from 'react';
import { ShieldCheck, UserCheck, KeyRound, Lock, CheckCircle2, ArrowRight, Loader2 } from 'lucide-react';
import { ConversationDetailDto } from '../../services/apiClient';

interface Props {
  conversation: ConversationDetailDto;
  isRecipient: boolean;
  peerDisplayName: string;
  onAccept: () => Promise<void>;
  onConfirmSafetyCode: (code: string) => Promise<void>;
  onClose: () => void;
  isLoading?: boolean;
}

export const HandshakeModal: React.FC<Props> = ({
  conversation,
  isRecipient,
  peerDisplayName,
  onAccept,
  onConfirmSafetyCode,
  onClose,
  isLoading = false,
}) => {
  const { handshake } = conversation;

  const isLayer1Done = handshake?.layer1Status === 'VERIFIED';
  const isLayer2Done = handshake?.layer2Status === 'ACCEPTED';
  const isLayer3Done = handshake?.layer3Status === 'EXCHANGED';
  const isLayer4Done = handshake?.layer4Status === 'CONFIRMED';

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4">
      <div className="w-full max-w-lg p-6 glass-panel rounded-3xl border border-white/10 shadow-2xl animate-in fade-in zoom-in-95">
        {/* Header */}
        <div className="flex items-center space-x-3 mb-6">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-blue-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <ShieldCheck className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">4-Layer Handshake Verification</h2>
            <p className="text-xs text-slate-400">Secure E2EE Channel with {peerDisplayName}</p>
          </div>
        </div>

        {/* 4 Layers Step Progress */}
        <div className="space-y-3 mb-6">
          {/* Layer 1 */}
          <div className={`p-3.5 rounded-2xl border flex items-center justify-between transition-all ${
            isLayer1Done ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-slate-900 border-white/5'
          }`}>
            <div className="flex items-center space-x-3">
              <div className={`w-8 h-8 rounded-xl flex items-center justify-center ${isLayer1Done ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-800 text-slate-400'}`}>
                <UserCheck className="w-4 h-4" />
              </div>
              <div>
                <p className="text-xs font-bold text-white">Layer 1: Google Identity Verified</p>
                <p className="text-[11px] text-slate-400">Both accounts authenticated via Google OAuth2</p>
              </div>
            </div>
            {isLayer1Done && <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />}
          </div>

          {/* Layer 2 */}
          <div className={`p-3.5 rounded-2xl border flex items-center justify-between transition-all ${
            isLayer2Done ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-slate-900 border-white/5'
          }`}>
            <div className="flex items-center space-x-3">
              <div className={`w-8 h-8 rounded-xl flex items-center justify-center ${isLayer2Done ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-800 text-slate-400'}`}>
                <Lock className="w-4 h-4" />
              </div>
              <div>
                <p className="text-xs font-bold text-white">Layer 2: Mutual Connection Consent</p>
                <p className="text-[11px] text-slate-400">
                  {isLayer2Done ? 'Invitation accepted by recipient' : isRecipient ? 'Please review & accept this chat request' : 'Waiting for recipient to accept invitation'}
                </p>
              </div>
            </div>
            {isLayer2Done ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            ) : isRecipient ? (
              <button
                onClick={onAccept}
                disabled={isLoading}
                className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-semibold shadow-sm transition-all"
              >
                {isLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : 'Accept'}
              </button>
            ) : (
              <span className="text-[10px] text-amber-400 font-semibold px-2 py-0.5 rounded-md bg-amber-400/10">Pending</span>
            )}
          </div>

          {/* Layer 3 */}
          <div className={`p-3.5 rounded-2xl border flex items-center justify-between transition-all ${
            isLayer3Done ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-slate-900 border-white/5'
          }`}>
            <div className="flex items-center space-x-3">
              <div className={`w-8 h-8 rounded-xl flex items-center justify-center ${isLayer3Done ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-800 text-slate-400'}`}>
                <KeyRound className="w-4 h-4" />
              </div>
              <div>
                <p className="text-xs font-bold text-white">Layer 3: Cryptographic Pre-Key Exchange</p>
                <p className="text-[11px] text-slate-400">
                  {isLayer3Done ? 'ECDH P-256 session key derived' : 'Exchanging public keys & computing shared secret'}
                </p>
              </div>
            </div>
            {isLayer3Done && <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />}
          </div>

          {/* Layer 4 */}
          <div className={`p-3.5 rounded-2xl border flex flex-col space-y-3 transition-all ${
            isLayer4Done ? 'bg-emerald-500/10 border-emerald-500/30' : isLayer3Done ? 'bg-blue-500/10 border-blue-500/30' : 'bg-slate-900 border-white/5'
          }`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className={`w-8 h-8 rounded-xl flex items-center justify-center ${isLayer4Done ? 'bg-emerald-500/20 text-emerald-400' : 'bg-blue-500/20 text-blue-400'}`}>
                  <ShieldCheck className="w-4 h-4" />
                </div>
                <div>
                  <p className="text-xs font-bold text-white">Layer 4: Visual Safety Code Match</p>
                  <p className="text-[11px] text-slate-400">Confirm 6-digit code matches on both screens</p>
                </div>
              </div>
              {isLayer4Done && <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />}
            </div>

            {isLayer3Done && !isLayer4Done && handshake?.safetyCode && (
              <div className="pt-2 border-t border-white/10 flex items-center justify-between">
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-semibold">Your Safety Code:</span>
                  <div className="text-2xl font-mono font-extrabold tracking-widest text-cyan-400">
                    {handshake.safetyCode.slice(0, 3)} {handshake.safetyCode.slice(3)}
                  </div>
                </div>
                <button
                  onClick={() => onConfirmSafetyCode(handshake.safetyCode)}
                  disabled={isLoading}
                  className="px-4 py-2 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white rounded-xl text-xs font-bold shadow-md shadow-blue-500/20 transition-all flex items-center space-x-1.5"
                >
                  <span>Confirm Match</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
