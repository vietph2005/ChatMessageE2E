import React, { useRef, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { useChat } from '../../hooks/useChat';
import { ConversationSidebar } from '../sidebar/ConversationSidebar';
import { ChatHeader } from '../chat/ChatHeader';
import { MessageBubble } from '../chat/MessageBubble';
import { ChatInputBar } from '../chat/ChatInputBar';
import { TypingIndicator } from '../chat/TypingIndicator';
import { HandshakeModal } from '../handshake/HandshakeModal';
import { SafetyNumberAlertBanner } from '../chat/SafetyNumberAlertBanner';
import { ShieldCheck, MessageCircle, Lock, Ban } from 'lucide-react';

export const AppShell: React.FC = () => {
  const { user } = useAuth();
  const {
    conversations,
    activeConversationId,
    activeConversationDetail,
    messages,
    isTyping,
    isLoading,
    isKeyMismatched,
    showHandshakeModal,
    setActiveConversationId,
    setShowHandshakeModal,
    setIsKeyMismatched,
    sendTextMessage,
    sendImageAttachment,
    unsendChatMessage,
    deleteForMe,
    startNewChat,
    acceptHandshake,
    confirmSafetyCode,
    reInitiateHandshake,
    unblockContact,
    loadConversations,
  } = useChat();

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const activeConversationSummary = conversations.find((c) => c.id === activeConversationId);
  const peerUser = activeConversationSummary?.peerUser;
  const isVerified = activeConversationDetail?.status === 'VERIFIED_ACTIVE' && !isKeyMismatched;
  const isBlocked = activeConversationDetail?.status === 'BLOCKED';
  const isRecipient = activeConversationDetail?.participantBId === user?.id;

  return (
    <div className="flex h-screen w-screen bg-slate-950 text-slate-100 overflow-hidden relative">
      {/* Background Ambient Glow */}
      <div className="absolute top-0 right-1/4 w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-0 left-1/4 w-[400px] h-[400px] bg-cyan-500/10 rounded-full blur-[120px] pointer-events-none" />

      {/* Sidebar (Full screen on mobile if no active conversation) */}
      <div className={`h-full ${activeConversationId ? 'hidden md:flex' : 'flex w-full'}`}>
        <ConversationSidebar
          conversations={conversations}
          activeConversationId={activeConversationId}
          onSelectConversation={(id) => setActiveConversationId(id)}
          onStartChat={startNewChat}
        />
      </div>

      {/* Main Chat Area */}
      <div className={`flex-1 h-full flex flex-col relative ${!activeConversationId ? 'hidden md:flex' : 'flex'}`}>
        {activeConversationId && peerUser ? (
          <>
            {/* Chat Top Header */}
            <ChatHeader
              peerUser={peerUser}
              conversationDetail={activeConversationDetail}
              onBackMobile={() => setActiveConversationId(null)}
              onBlocked={() => {
                setActiveConversationId(null);
                loadConversations();
              }}
              onUnblocked={() => unblockContact(peerUser.id)}
            />

            {/* Key Mismatch Warning Banner */}
            {isKeyMismatched && (
              <SafetyNumberAlertBanner
                peerDisplayName={peerUser.displayName}
                onVerify={reInitiateHandshake}
                onDismiss={() => setIsKeyMismatched(false)}
              />
            )}

            {/* Blocked Notice Banner */}
            {isBlocked && (
              <div className="p-3 bg-rose-500/10 border-b border-rose-500/20 flex items-center justify-between px-4">
                <div className="flex items-center space-x-2 text-xs text-rose-300">
                  <Ban className="w-4 h-4 text-rose-400" />
                  <span>This contact is currently blocked. You cannot send or receive messages.</span>
                </div>
                <button
                  onClick={() => unblockContact(peerUser.id)}
                  className="px-3 py-1 bg-rose-600 hover:bg-rose-500 text-white rounded-xl text-xs font-semibold shadow-sm transition-all"
                >
                  Unblock Contact
                </button>
              </div>
            )}

            {/* Handshake Prompt Banner if not verified */}
            {!isVerified && !isKeyMismatched && !isBlocked && activeConversationDetail && (
              <div className="p-3 bg-blue-600/15 border-b border-blue-500/30 flex items-center justify-between px-4">
                <div className="flex items-center space-x-2 text-xs text-blue-200">
                  <ShieldCheck className="w-4 h-4 text-cyan-400" />
                  <span>4-Layer Handshake Verification required before chatting.</span>
                </div>
                <button
                  onClick={() => setShowHandshakeModal(true)}
                  className="px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-semibold shadow-sm transition-all"
                >
                  Verify Now
                </button>
              </div>
            )}

            {/* Messages Feed */}
            <div className="flex-1 overflow-y-auto p-4 space-y-1">
              {/* E2EE Session Divider */}
              <div className="flex items-center justify-center my-2">
                <div className="px-3 py-1 rounded-full bg-slate-900/80 border border-white/5 text-[11px] text-slate-400 flex items-center gap-1.5 shadow-sm">
                  <Lock className="w-3 h-3 text-cyan-400" />
                  <span>Messages in this conversation are end-to-end encrypted.</span>
                </div>
              </div>

              {messages.map((msg) => (
                <MessageBubble
                  key={msg.id}
                  message={msg}
                  isSender={msg.senderId === user?.id}
                  peerAvatarUrl={peerUser.avatarUrl}
                  onUnsend={unsendChatMessage}
                  onDeleteForMe={deleteForMe}
                />
              ))}

              {isTyping && (
                <TypingIndicator
                  peerAvatarUrl={peerUser.avatarUrl}
                />
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Chat Input Bar */}
            <ChatInputBar
              conversationId={activeConversationId}
              onSendMessage={sendTextMessage}
              onSendImage={sendImageAttachment}
              disabled={!isVerified || isBlocked}
            />

            {/* 4-Layer Handshake Modal */}
            {showHandshakeModal && activeConversationDetail && (
              <HandshakeModal
                conversation={activeConversationDetail}
                isRecipient={isRecipient}
                peerDisplayName={peerUser.displayName}
                onAccept={acceptHandshake}
                onConfirmSafetyCode={confirmSafetyCode}
                onClose={() => setShowHandshakeModal(false)}
                isLoading={isLoading}
              />
            )}
          </>
        ) : (
          /* Empty Active State */
          <div className="flex-1 flex flex-col items-center justify-center p-6 text-center text-slate-500">
            <div className="w-16 h-16 rounded-3xl bg-slate-900 border border-white/5 flex items-center justify-center mb-4 text-blue-500 shadow-xl shadow-blue-500/5">
              <MessageCircle className="w-8 h-8" />
            </div>
            <h2 className="text-lg font-bold text-slate-200">Select a Conversation</h2>
            <p className="text-xs text-slate-400 max-w-sm mt-1">
              Choose a verified contact from the sidebar or find a friend by exact Gmail to start a secure end-to-end encrypted session.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
