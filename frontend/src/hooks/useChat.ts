import { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from './useAuth';
import { apiClient, ConversationDetailDto, ConversationSummaryDto } from '../services/apiClient';
import { stompChatService, StompChatMessage, HandshakeNotificationEvent } from '../services/stompClient';
import {
  importPeerPublicKey,
  deriveSessionKey,
  encryptText,
  decryptText,
  encryptMedia,
  decryptMedia,
} from '../crypto/webCryptoEngine';
import {
  loadIdentityKeyPair,
  saveLocalMessage,
  getMessagesByConversation,
  revokeLocalMessage,
  LocalMessageRecord,
} from '../db/indexedDbManager';

export function useChat() {
  const { user, token } = useAuth();

  const [conversations, setConversations] = useState<ConversationSummaryDto[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [activeConversationDetail, setActiveConversationDetail] = useState<ConversationDetailDto | null>(null);
  const [messages, setMessages] = useState<LocalMessageRecord[]>([]);
  const [isTyping, setIsTyping] = useState<boolean>(false);
  const [activeSessionKey, setActiveSessionKey] = useState<CryptoKey | null>(null);
  const [pendingHandshakeNotification, setPendingHandshakeNotification] = useState<HandshakeNotificationEvent | null>(null);
  const [showHandshakeModal, setShowHandshakeModal] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Refresh conversation list
  const loadConversations = useCallback(async () => {
    if (!token) return;
    try {
      const list = await apiClient.listConversations();
      setConversations(list);
    } catch (e) {
      console.error('Failed to load conversations', e);
    }
  }, [token]);

  // Connect STOMP WebSocket on login
  useEffect(() => {
    if (token) {
      stompChatService.connect(token, () => {
        loadConversations();
      });

      // Subscribe to personal notification queue for async 4-layer handshakes
      const unsubscribeNotifications = stompChatService.subscribeToUserNotifications((event) => {
        console.log('[Notification Received]', event);
        setPendingHandshakeNotification(event);
        loadConversations();
      });

      return () => {
        unsubscribeNotifications();
        stompChatService.disconnect();
      };
    }
  }, [token, loadConversations]);

  // Load details and derive E2EE session key when active conversation changes
  useEffect(() => {
    async function setupConversationSession() {
      if (!activeConversationId || !token || !user) return;

      setIsLoading(true);
      try {
        const detail = await apiClient.getConversationDetail(activeConversationId);
        setActiveConversationDetail(detail);

        // Load local message cache
        const localCached = await getMessagesByConversation(activeConversationId);
        setMessages(localCached);

        // If conversation is VERIFIED_ACTIVE, derive session key
        if (detail.status === 'VERIFIED_ACTIVE' || detail.status === 'HANDSHAKE_IN_PROGRESS') {
          const peerId = detail.participantAId === user.id ? detail.participantBId : detail.participantAId;
          const peerBundle = await apiClient.getPeerPublicKeyBundle(peerId);

          const myKeys = await loadIdentityKeyPair();
          if (myKeys && peerBundle.identityPublicKey) {
            const peerPublicKey = await importPeerPublicKey(peerBundle.identityPublicKey);
            const derivedKey = await deriveSessionKey(myKeys.keyPair.privateKey, peerPublicKey, activeConversationId);
            setActiveSessionKey(derivedKey);
          }
        } else {
          setActiveSessionKey(null);
          if (detail.status === 'PENDING_ACCEPTANCE') {
            setShowHandshakeModal(true);
          }
        }
      } catch (e) {
        console.error('Failed to setup conversation session', e);
      } finally {
        setIsLoading(false);
      }
    }

    setupConversationSession();
  }, [activeConversationId, token, user]);

  // Subscribe to real-time messages in active conversation
  useEffect(() => {
    if (!activeConversationId || !activeSessionKey || !user) return;

    const unsubscribe = stompChatService.subscribeToConversation(
      activeConversationId,
      async (stompMsg: StompChatMessage) => {
        try {
          let plaintext = '';
          let mediaBlobUrl: string | undefined = undefined;

          if (stompMsg.messageType === 'TEXT') {
            plaintext = await decryptText(stompMsg.ciphertext, stompMsg.initializationVector, activeSessionKey);
          } else if (stompMsg.messageType === 'IMAGE' && stompMsg.mediaUrl) {
            const res = await fetch(stompMsg.mediaUrl, {
              headers: { Authorization: `Bearer ${token}` }
            });
            const encryptedBytes = await res.arrayBuffer();
            const blob = await decryptMedia(encryptedBytes, stompMsg.initializationVector, activeSessionKey, 'image/png');
            mediaBlobUrl = URL.createObjectURL(blob);
            plaintext = '[Image]';
          }

          const localRecord: LocalMessageRecord = {
            id: stompMsg.messageId,
            conversationId: stompMsg.conversationId,
            senderId: stompMsg.senderId,
            recipientId: stompMsg.recipientId,
            messageType: stompMsg.messageType,
            plaintext,
            mediaObjectUrl: mediaBlobUrl,
            sentAt: stompMsg.sentAt,
            isRevoked: stompMsg.isRevoked,
            status: 'DELIVERED',
          };

          await saveLocalMessage(localRecord);
          setMessages((prev) => {
            if (prev.some((m) => m.id === localRecord.id)) return prev;
            return [...prev, localRecord];
          });
        } catch (e) {
          console.error('Decryption failed for incoming message', e);
        }
      },
      (typingEvent) => {
        if (typingEvent.userId !== user.id) {
          setIsTyping(typingEvent.isTyping);
          if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
          if (typingEvent.isTyping) {
            typingTimeoutRef.current = setTimeout(() => setIsTyping(false), 3000);
          }
        }
      },
      async (unsendEvent) => {
        await revokeLocalMessage(unsendEvent.messageId);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === unsendEvent.messageId
              ? { ...m, isRevoked: true, plaintext: 'This message was unsent', mediaObjectUrl: undefined }
              : m
          )
        );
      }
    );

    return () => unsubscribe();
  }, [activeConversationId, activeSessionKey, user, token]);

  // Send Text Message
  const sendTextMessage = async (text: string) => {
    if (!activeConversationId || !activeSessionKey || !user || !activeConversationDetail) return;

    const peerId = activeConversationDetail.participantAId === user.id
      ? activeConversationDetail.participantBId
      : activeConversationDetail.participantAId;

    const { ciphertext, iv } = await encryptText(text, activeSessionKey);
    stompChatService.sendMessage(activeConversationId, user.id, peerId, 'TEXT', ciphertext, iv);
  };

  // Send Encrypted Image
  const sendImageAttachment = async (file: File) => {
    if (!activeConversationId || !activeSessionKey || !user || !activeConversationDetail) return;

    const peerId = activeConversationDetail.participantAId === user.id
      ? activeConversationDetail.participantBId
      : activeConversationDetail.participantAId;

    const arrayBuffer = await file.arrayBuffer();
    const { encryptedBlob, iv } = await encryptMedia(arrayBuffer, activeSessionKey);

    const uploadRes = await apiClient.uploadEncryptedMedia(activeConversationId, encryptedBlob);
    stompChatService.sendMessage(activeConversationId, user.id, peerId, 'IMAGE', '', iv, uploadRes.mediaUrl);
  };

  // Unsend Message
  const unsendChatMessage = (messageId: string) => {
    if (!activeConversationId) return;
    stompChatService.sendUnsend(activeConversationId, messageId);
  };

  // Delete for me
  const deleteForMe = async (messageId: string) => {
    await revokeLocalMessage(messageId);
    setMessages((prev) => prev.filter((m) => m.id !== messageId));
  };

  // Start new 1-1 Chat (initiates 4-layer handshake)
  const startNewChat = async (recipientEmail: string) => {
    const myKeys = await loadIdentityKeyPair();
    if (!myKeys) throw new Error('Identity keys not initialized');

    const conv = await apiClient.initiateConversation(recipientEmail, myKeys.publicKeyBase64);
    await loadConversations();
    setActiveConversationId(conv.id);
    setShowHandshakeModal(true);
  };

  // Accept Handshake (Layer 2 & 3)
  const acceptHandshake = async () => {
    if (!activeConversationId) return;
    const myKeys = await loadIdentityKeyPair();
    if (!myKeys) return;

    const updated = await apiClient.acceptHandshake(activeConversationId, myKeys.publicKeyBase64);
    setActiveConversationDetail(updated);
    await loadConversations();
  };

  // Confirm Safety Code (Layer 4)
  const confirmSafetyCode = async (code: string) => {
    if (!activeConversationId) return;
    const updated = await apiClient.confirmSafetyCode(activeConversationId, code);
    setActiveConversationDetail(updated);
    setShowHandshakeModal(false);
    await loadConversations();
  };

  return {
    conversations,
    activeConversationId,
    activeConversationDetail,
    messages,
    isTyping,
    isLoading,
    showHandshakeModal,
    pendingHandshakeNotification,
    setActiveConversationId,
    setShowHandshakeModal,
    setPendingHandshakeNotification,
    sendTextMessage,
    sendImageAttachment,
    unsendChatMessage,
    deleteForMe,
    startNewChat,
    acceptHandshake,
    confirmSafetyCode,
    loadConversations,
  };
}
