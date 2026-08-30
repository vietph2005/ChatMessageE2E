# WebSocket STOMP Contracts: Re-Handshake Notifications

## 1. User Notification Queue

**Destination**: `/user/queue/notifications`

### 1.1. Key Changed Notification Event (`KEY_CHANGED`)

Sent to the conversation peer when a user initiates a re-handshake with an updated public key.

```json
{
  "eventType": "KEY_CHANGED",
  "conversationId": "66d1a2b3c4d5e6f7a8b9c0d1",
  "initiator": {
    "id": "user_alice_123",
    "displayName": "Alice Smith",
    "email": "alice@gmail.com",
    "avatarUrl": "https://lh3.googleusercontent.com/..."
  },
  "timestamp": "2026-08-30T10:30:00Z"
}
```

### 1.2. Re-Handshake Accepted Notification Event (`HANDSHAKE_ACCEPTED`)

Sent to both participants once Layer 2 & 3 are re-exchanged, providing the new 6-digit visual Safety Code.

```json
{
  "eventType": "HANDSHAKE_ACCEPTED",
  "conversationId": "66d1a2b3c4d5e6f7a8b9c0d1",
  "safetyCode": "583921",
  "timestamp": "2026-08-30T10:31:00Z"
}
```

### 1.3. Re-Handshake Confirmed Notification Event (`SAFETY_CODE_CONFIRMED`)

Sent to both participants once Layer 4 Safety Code is verified by both parties.

```json
{
  "eventType": "SAFETY_CODE_CONFIRMED",
  "conversationId": "66d1a2b3c4d5e6f7a8b9c0d1",
  "timestamp": "2026-08-30T10:32:00Z"
}
```
