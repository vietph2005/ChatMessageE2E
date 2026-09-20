export interface ChatMessage {
  id?: string;
  senderId: string;
  recipientId?: string;
  content: string;
  timestamp?: string;
  roomId?: string;
  senderName?: string;
  avatar?: string;
  reactions?: string[];
  type?: 'text' | 'image' | 'like' | 'system';
}

export interface SendMessagePayload {
  senderId: string;
  recipientId: string;
  content: string;
  roomId?: string;
}

export type StompStatus = 'CONNECTING' | 'CONNECTED' | 'DISCONNECTED' | 'ERROR';

export interface Room {
  id?: string;
  roomId: string;
  roomName?: string;
  messages?: ChatMessage[];
}

export interface JoinChatForm {
  userName: string;
  roomId: string;
}

export interface ChatUserSession {
  userName: string;
  roomId: string;
  room?: Room;
}
