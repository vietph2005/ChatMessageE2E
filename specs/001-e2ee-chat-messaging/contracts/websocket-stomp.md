# WebSocket STOMP Messaging Contracts

**Feature Branch**: `001-e2ee-chat-messaging`  
**Date**: 2026-08-28  
**Protocol**: STOMP over SockJS / WebSocket  
**Base Endpoint**: `/ws/chat` (Handshake URL with JWT token authentication via query parameter `?token=...` or `STOMP CONNECT` header `Authorization: Bearer <token>`)

---

## 1. Connection & Session Lifecycle

### STOMP Connect Frame
```text
CONNECT
accept-version:1.2
host:/
Authorization:Bearer <JWT_ACCESS_TOKEN>
heart-beat:10000,10000

^@
```

### STOMP Connected Frame (Server Response)
```text
CONNECTED
version:1.2
heart-beat:10000,10000
user-name:<USER_ID>

^@
```

---

## 2. Real-Time Destinations & Frame Specifications

### 2.1 Send Encrypted Message
- **Client Destination**: `/app/chat.send`
- **Security Check**: Backend rejects frame if conversation status is NOT `VERIFIED_ACTIVE`.
- **Payload Schema**:
```json
{
  "conversationId": "conv_64f1a2b3c4d5",
  "recipientId": "user_recipient_id",
  "messageType": "TEXT", // "TEXT" | "IMAGE"
  "ciphertext": "U2FsdGVkX1+vupppZks...", // Base64 AES-256-GCM
  "initializationVector": "x8/D1k3e9...", // Base64 12-byte IV
  "mediaUrl": null, // Optional encrypted blob URL
  "clientSentAt": "2026-08-28T14:40:00.000Z"
}
```

### 2.2 Receive Encrypted Message in Active Conversation
- **Topic Subscription**: `/topic/conversation/{conversationId}`
- **Server Broadcast Payload**:
```json
{
  "messageId": "msg_987654321",
  "conversationId": "conv_64f1a2b3c4d5",
  "senderId": "user_sender_id",
  "recipientId": "user_recipient_id",
  "messageType": "TEXT",
  "ciphertext": "U2FsdGVkX1+vupppZks...",
  "initializationVector": "x8/D1k3e9...",
  "mediaUrl": null,
  "sequenceNumber": 42,
  "sentAt": "2026-08-28T14:40:00.120Z",
  "isRevoked": false
}
```

### 2.3 Typing Indicator Event
- **Send Destination**: `/app/chat.typing`
- **Topic Subscription**: `/topic/conversation/{conversationId}/typing`
- **Payload**:
```json
{
  "conversationId": "conv_64f1a2b3c4d5",
  "isTyping": true,
  "userId": "user_sender_id"
}
```

### 2.4 Message Read Receipt Event
- **Send Destination**: `/app/chat.read`
- **Topic Subscription**: `/topic/conversation/{conversationId}/receipts`
- **Payload**:
```json
{
  "conversationId": "conv_64f1a2b3c4d5",
  "messageId": "msg_987654321",
  "readerId": "user_recipient_id",
  "readAt": "2026-08-28T14:40:05.500Z"
}
```

### 2.5 Message Revocation ("Unsend for Everyone")
- **Send Destination**: `/app/chat.unsend`
- **Topic Subscription**: `/topic/conversation/{conversationId}/revocations`
- **Payload**:
```json
{
  "conversationId": "conv_64f1a2b3c4d5",
  "messageId": "msg_987654321",
  "revokedBy": "user_sender_id",
  "revokedAt": "2026-08-28T14:40:30.000Z"
}
```

### 2.6 User Notifications & Handshake Async Events
- **User Queue Subscription**: `/user/queue/notifications`
- **Server Push Payload for Asynchronous Handshake & Invitations**:
```json
{
  "eventType": "HANDSHAKE_INVITATION_RECEIVED", // "HANDSHAKE_ACCEPTED" | "SAFETY_CODE_CONFIRMED" | "KEY_CHANGED"
  "conversationId": "conv_64f1a2b3c4d5",
  "initiator": {
    "id": "user_initiator_id",
    "displayName": "Alice Google",
    "email": "alice@gmail.com",
    "avatarUrl": "https://lh3.googleusercontent.com/..."
  },
  "safetyCode": "842910",
  "timestamp": "2026-08-28T14:38:00.000Z"
}
```
