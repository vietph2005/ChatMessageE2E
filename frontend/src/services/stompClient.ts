import { Client, IMessage, StompSubscription } from '@stomp/stompjs';
import SockJS from 'sockjs-client';

export interface StompChatMessage {
  messageId: string;
  conversationId: string;
  senderId: string;
  recipientId: string;
  messageType: 'TEXT' | 'IMAGE';
  ciphertext: string;
  initializationVector: string;
  mediaUrl?: string;
  sequenceNumber: number;
  sentAt: string;
  isRevoked: boolean;
}

export interface TypingEvent {
  conversationId: string;
  userId: string;
  isTyping: boolean;
}

export interface HandshakeNotificationEvent {
  eventType: 'HANDSHAKE_INVITATION_RECEIVED' | 'HANDSHAKE_ACCEPTED' | 'SAFETY_CODE_CONFIRMED' | 'KEY_CHANGED';
  conversationId: string;
  initiator: {
    id: string;
    displayName: string;
    email: string;
    avatarUrl: string;
  };
  safetyCode?: string;
  timestamp: string;
}

class StompChatService {
  private client: Client | null = null;
  private isConnected: boolean = false;
  private subscriptions: Map<string, StompSubscription> = new Map();

  connect(token: string, onConnected?: () => void, onError?: (err: unknown) => void): void {
    if (this.client && this.isConnected) return;

    this.client = new Client({
      webSocketFactory: () => new SockJS('/ws'),
      connectHeaders: {
        Authorization: `Bearer ${token}`,
      },
      heartbeatIncoming: 10000,
      heartbeatOutgoing: 10000,
      reconnectDelay: 3000,
      debug: (msg) => {
        if (import.meta.env.DEV) {
          console.debug('[STOMP]', msg);
        }
      },
      onConnect: () => {
        this.isConnected = true;
        console.log('[STOMP] Connected to WebSocket broker');
        if (onConnected) onConnected();
      },
      onStompError: (frame) => {
        console.error('[STOMP Error]', frame.headers['message'], frame.body);
        if (onError) onError(frame);
      },
      onWebSocketClose: () => {
        this.isConnected = false;
        console.log('[STOMP] WebSocket connection closed');
      },
    });

    this.client.activate();
  }

  disconnect(): void {
    if (this.client) {
      this.subscriptions.forEach((sub) => sub.unsubscribe());
      this.subscriptions.clear();
      this.client.deactivate();
      this.client = null;
      this.isConnected = false;
    }
  }

  subscribeToConversation(
    conversationId: string,
    onMessage: (msg: StompChatMessage) => void,
    onTyping?: (typing: TypingEvent) => void,
    onUnsend?: (revocation: { messageId: string; revokedAt: string }) => void
  ): () => void {
    if (!this.client || !this.isConnected) return () => {};

    const msgTopic = `/topic/conversation/${conversationId}`;
    const subMsg = this.client.subscribe(msgTopic, (message: IMessage) => {
      try {
        const payload: StompChatMessage = JSON.parse(message.body);
        onMessage(payload);
      } catch (e) {
        console.error('Failed to parse STOMP message', e);
      }
    });

    const typingTopic = `/topic/conversation/${conversationId}/typing`;
    const subTyping = this.client.subscribe(typingTopic, (message: IMessage) => {
      try {
        const payload: TypingEvent = JSON.parse(message.body);
        if (onTyping) onTyping(payload);
      } catch (e) {
        console.error('Failed to parse typing payload', e);
      }
    });

    const revocationTopic = `/topic/conversation/${conversationId}/revocations`;
    const subUnsend = this.client.subscribe(revocationTopic, (message: IMessage) => {
      try {
        const payload = JSON.parse(message.body);
        if (onUnsend) onUnsend(payload);
      } catch (e) {
        console.error('Failed to parse unsend payload', e);
      }
    });

    return () => {
      subMsg.unsubscribe();
      subTyping.unsubscribe();
      subUnsend.unsubscribe();
    };
  }

  subscribeToUserNotifications(
    onNotification: (event: HandshakeNotificationEvent) => void
  ): () => void {
    if (!this.client || !this.isConnected) return () => {};

    const sub = this.client.subscribe('/user/queue/notifications', (message: IMessage) => {
      try {
        const event: HandshakeNotificationEvent = JSON.parse(message.body);
        onNotification(event);
      } catch (e) {
        console.error('Failed to parse notification payload', e);
      }
    });

    return () => sub.unsubscribe();
  }

  sendMessage(
    conversationId: string,
    senderId: string,
    recipientId: string,
    messageType: 'TEXT' | 'IMAGE',
    ciphertext: string,
    initializationVector: string,
    mediaUrl?: string
  ): void {
    if (!this.client || !this.isConnected) {
      throw new Error('STOMP client not connected');
    }

    this.client.publish({
      destination: '/app/chat.send',
      body: JSON.stringify({
        conversationId,
        senderId,
        recipientId,
        messageType,
        ciphertext,
        initializationVector,
        mediaUrl,
        clientSentAt: new Date().toISOString(),
      }),
    });
  }

  sendTyping(conversationId: string, isTyping: boolean): void {
    if (!this.client || !this.isConnected) return;
    this.client.publish({
      destination: '/app/chat.typing',
      body: JSON.stringify({ conversationId, isTyping }),
    });
  }

  sendUnsend(conversationId: string, messageId: string): void {
    if (!this.client || !this.isConnected) return;
    this.client.publish({
      destination: '/app/chat.unsend',
      body: JSON.stringify({ conversationId, messageId }),
    });
  }
}

export const stompChatService = new StompChatService();
