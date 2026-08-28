import React, { useState } from 'react';
import { ShieldCheck, ShieldAlert, QrCode, ArrowLeft, Info } from 'lucide-react';
import { UserProfileDto, ConversationDetailDto } from '../../services/apiClient';
import { SafetyQrCodeModal } from '../handshake/SafetyQrCodeModal';
import { SecurityDetailsDrawer } from '../security/SecurityDetailsDrawer';
import { BlockContactButton } from '../security/BlockContactButton';

interface Props {
  peerUser: UserProfileDto;
  conversationDetail: ConversationDetailDto | null;
  onBackMobile?: () => void;
  onBlocked: () => void;
}

export const ChatHeader: React.FC<Props> = ({
  peerUser,
  conversationDetail,
  onBackMobile,
  onBlocked,
}) => {
  const [showQrModal, setShowQrModal] = useState(false);
  const [showSecurityDrawer, setShowSecurityDrawer] = useState(false);

  const isVerified = conversationDetail?.status === 'VERIFIED_ACTIVE';
  const handshake = conversationDetail?.handshake;

  return (
    <>
      <div className="h-16 px-4 glass-panel border-b border-white/10 flex items-center justify-between z-20">
        <div className="flex items-center space-x-3 min-w-0">
          {onBackMobile && (
            <button
              onClick={onBackMobile}
              className="p-1.5 md:hidden text-slate-400 hover:text-white rounded-full hover:bg-slate-800"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
          )}

          {/* Avatar with Online Badge */}
          <div className="relative shrink-0">
            <img
              src={peerUser.avatarUrl || 'https://lh3.googleusercontent.com/a/default-avatar'}
              alt={peerUser.displayName}
              className="w-10 h-10 rounded-full object-cover ring-2 ring-white/10"
            />
            {peerUser.isOnline && (
              <span className="absolute bottom-0 right-0 w-3 h-3 rounded-full bg-emerald-500 ring-2 ring-slate-950 shadow-sm shadow-emerald-500/50" />
            )}
          </div>

          {/* Contact Details & Security Badge */}
          <div className="min-w-0">
            <div className="flex items-center space-x-1.5">
              <h2 className="text-sm font-bold text-white truncate">{peerUser.displayName}</h2>
              {isVerified ? (
                <button
                  onClick={() => setShowSecurityDrawer(true)}
                  title="View 4-Layer Security Audit"
                  className="px-1.5 py-0.5 rounded-full bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 text-[10px] font-bold flex items-center gap-1 shrink-0 transition-colors"
                >
                  <ShieldCheck className="w-3 h-3" />
                  <span className="hidden sm:inline">E2EE Verified</span>
                </button>
              ) : (
                <button
                  onClick={() => setShowSecurityDrawer(true)}
                  title="Handshake verification in progress"
                  className="px-1.5 py-0.5 rounded-full bg-amber-500/20 hover:bg-amber-500/30 text-amber-400 text-[10px] font-bold flex items-center gap-1 shrink-0 transition-colors"
                >
                  <ShieldAlert className="w-3 h-3" />
                  <span className="hidden sm:inline">Handshake</span>
                </button>
              )}
            </div>
            <p className="text-[11px] text-slate-400 truncate">{peerUser.email}</p>
          </div>
        </div>

        {/* Action Toolbar */}
        <div className="flex items-center space-x-1">
          {handshake?.safetyCode && (
            <button
              onClick={() => setShowQrModal(true)}
              className="p-2 rounded-full text-slate-400 hover:text-cyan-400 hover:bg-slate-800 transition-colors"
              title="Show Safety Number & QR Code"
            >
              <QrCode className="w-4 h-4" />
            </button>
          )}

          <button
            onClick={() => setShowSecurityDrawer(true)}
            className="p-2 rounded-full text-slate-400 hover:text-blue-400 hover:bg-slate-800 transition-colors"
            title="Conversation Security Details"
          >
            <Info className="w-4 h-4" />
          </button>

          <BlockContactButton
            peerUserId={peerUser.id}
            peerDisplayName={peerUser.displayName}
            onBlocked={onBlocked}
          />
        </div>
      </div>

      {showQrModal && handshake?.safetyCode && (
        <SafetyQrCodeModal
          conversationId={conversationDetail?.id || ''}
          safetyCode={handshake.safetyCode}
          fullFingerprintHex={handshake.fullFingerprintHex || ''}
          peerName={peerUser.displayName}
          onClose={() => setShowQrModal(false)}
        />
      )}

      {showSecurityDrawer && conversationDetail && (
        <SecurityDetailsDrawer
          conversation={conversationDetail}
          peerDisplayName={peerUser.displayName}
          peerAvatarUrl={peerUser.avatarUrl}
          peerUserId={peerUser.id}
          onClose={() => setShowSecurityDrawer(false)}
          onBlocked={onBlocked}
        />
      )}
    </>
  );
};
