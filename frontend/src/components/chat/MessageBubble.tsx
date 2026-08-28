import React, { useState } from 'react';
import { LocalMessageRecord } from '../../db/indexedDbManager';
import { MessageActionsMenu } from './MessageActionsMenu';
import { MoreHorizontal, Lock, Check, CheckCheck } from 'lucide-react';

interface Props {
  message: LocalMessageRecord;
  isSender: boolean;
  peerAvatarUrl?: string;
  onUnsend: (messageId: string) => void;
  onDeleteForMe: (messageId: string) => void;
}

export const MessageBubble: React.FC<Props> = ({
  message,
  isSender,
  peerAvatarUrl,
  onUnsend,
  onDeleteForMe,
}) => {
  const [showMenu, setShowMenu] = useState(false);
  const [showImagePreview, setShowImagePreview] = useState(false);

  const formattedTime = new Date(message.sentAt).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div className={`flex w-full my-1.5 group ${isSender ? 'justify-end' : 'justify-start items-end space-x-2'}`}>
      {!isSender && (
        <img
          src={peerAvatarUrl || 'https://lh3.googleusercontent.com/a/default-avatar'}
          alt="Avatar"
          className="w-7 h-7 rounded-full object-cover mb-1 ring-1 ring-white/10"
        />
      )}

      <div className="relative max-w-[70%] sm:max-w-[60%] flex items-center space-x-1.5">
        {/* Action Menu for Sender (Left of bubble) */}
        {isSender && !message.isRevoked && (
          <div className="relative opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={() => setShowMenu(!showMenu)}
              className="p-1 rounded-full text-slate-400 hover:text-white hover:bg-slate-800"
            >
              <MoreHorizontal className="w-4 h-4" />
            </button>
            {showMenu && (
              <MessageActionsMenu
                isSender={true}
                onUnsendEveryone={() => onUnsend(message.id)}
                onDeleteForMe={() => onDeleteForMe(message.id)}
                onClose={() => setShowMenu(false)}
              />
            )}
          </div>
        )}

        {/* Message Body */}
        <div
          className={`px-4 py-2.5 rounded-3xl text-sm leading-relaxed transition-all shadow-sm ${
            message.isRevoked
              ? 'bg-slate-900/60 border border-white/5 text-slate-400 italic text-xs'
              : isSender
              ? 'glass-bubble-sender rounded-br-md text-white'
              : 'glass-bubble-recipient rounded-bl-md text-slate-100'
          }`}
        >
          {message.isRevoked ? (
            <div className="flex items-center space-x-1.5 py-0.5">
              <Lock className="w-3.5 h-3.5 text-slate-500" />
              <span>{message.plaintext}</span>
            </div>
          ) : message.messageType === 'IMAGE' && message.mediaObjectUrl ? (
            <div>
              <img
                src={message.mediaObjectUrl}
                alt="Encrypted attachment"
                onClick={() => setShowImagePreview(true)}
                className="max-h-60 rounded-2xl cursor-pointer hover:opacity-95 transition-opacity object-cover"
              />
              <div className={`text-[10px] mt-1 text-right ${isSender ? 'text-blue-100/75' : 'text-slate-400'}`}>
                {formattedTime}
              </div>
            </div>
          ) : (
            <div>
              <p className="break-words select-text whitespace-pre-wrap">{message.plaintext}</p>
              <div className={`text-[10px] mt-0.5 flex items-center justify-end space-x-1 ${isSender ? 'text-blue-100/75' : 'text-slate-400'}`}>
                <span>{formattedTime}</span>
                {isSender && (
                  <span>
                    {message.status === 'READ' ? (
                      <CheckCheck className="w-3 h-3 text-cyan-200" />
                    ) : (
                      <Check className="w-3 h-3" />
                    )}
                  </span>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Action Menu for Recipient (Right of bubble) */}
        {!isSender && !message.isRevoked && (
          <div className="relative opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={() => setShowMenu(!showMenu)}
              className="p-1 rounded-full text-slate-400 hover:text-white hover:bg-slate-800"
            >
              <MoreHorizontal className="w-4 h-4" />
            </button>
            {showMenu && (
              <MessageActionsMenu
                isSender={false}
                onDeleteForMe={() => onDeleteForMe(message.id)}
                onClose={() => setShowMenu(false)}
              />
            )}
          </div>
        )}
      </div>

      {/* Fullscreen Image Lightbox Modal */}
      {showImagePreview && message.mediaObjectUrl && (
        <div
          onClick={() => setShowImagePreview(false)}
          className="fixed inset-0 z-50 bg-slate-950/90 backdrop-blur-md flex items-center justify-center p-4 cursor-zoom-out"
        >
          <img
            src={message.mediaObjectUrl}
            alt="Decrypted attachment"
            className="max-w-full max-h-[90vh] rounded-2xl shadow-2xl object-contain"
          />
        </div>
      )}
    </div>
  );
};
