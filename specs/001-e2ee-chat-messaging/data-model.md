# Data Model Specification: 1-1 End-to-End Encrypted Chat with 4-Layer Handshake Verification

**Feature Branch**: `001-e2ee-chat-messaging`  
**Date**: 2026-08-28  
**Status**: Completed  
**Spec Reference**: [`specs/001-e2ee-chat-messaging/spec.md`](spec.md) | [`research.md`](research.md)

---

## 1. Conceptual & Database Entity Model (MongoDB)

```mermaid
erDiagram
    UserProfile ||--o{ UserPublicKeyBundle : owns
    UserProfile ||--o{ Conversation : participates_in
    Conversation ||--|| HandshakeVerification : governed_by
    Conversation ||--o{ EncryptedMessage : contains

    UserProfile {
        string id PK
        string googleSubjectId UK
        string email UK "Exact Gmail address"
        string displayName
        string avatarUrl
        datetime createdAt
        datetime lastSeenAt
        boolean isOnline
    }

    UserPublicKeyBundle {
        string id PK
        string userId FK
        string identityPublicKey "Base64 encoded ECDH P-256 public key"
        string signedPreKey "Base64 encoded signed pre-key"
        string preKeySignature "Signature validating pre-key authenticity"
        int keyVersion
        datetime updatedAt
    }

    Conversation {
        string id PK
        string participantAId FK "Initiator"
        string participantBId FK "Recipient"
        string status "INITIATING, PENDING_ACCEPTANCE, HANDSHAKE_IN_PROGRESS, VERIFIED_ACTIVE, BLOCKED"
        string lastMessageId FK "Optional"
        datetime lastMessageAt
        datetime createdAt
        datetime updatedAt
    }

    HandshakeVerification {
        string id PK
        string conversationId FK UK
        string layer1Status "VERIFIED, FAILED"
        string layer2Status "PENDING, ACCEPTED, REJECTED"
        string layer3Status "PENDING, EXCHANGED, FAILED"
        string layer4Status "PENDING, CONFIRMED, FAILED"
        string safetyCode "6-digit visual code e.g. 842910"
        string fullFingerprintHex "60-char SHA-256 hex string"
        datetime layer1VerifiedAt
        datetime layer2AcceptedAt
        datetime layer3ExchangedAt
        datetime layer4ConfirmedAt
        datetime completedAt
    }

    EncryptedMessage {
        string id PK
        string conversationId FK
        string senderId FK
        string recipientId FK
        string messageType "TEXT, IMAGE"
        string ciphertext "Base64 encoded AES-256-GCM ciphertext"
        string initializationVector "Base64 encoded 12-byte IV"
        string mediaUrl "URL to encrypted blob if IMAGE"
        boolean isRevoked "True if unsent for everyone"
        datetime revokedAt
        int sequenceNumber
        datetime sentAt
        datetime deliveredAt
        datetime readAt
    }
```

---

## 2. Detailed Collection Schemas

### 2.1 Collection: `users`
Represents an authenticated Google/Gmail user.

| Field Name | Type | Constraints | Description |
|---|---|---|---|
| `_id` | `ObjectId / String` | Primary Key | Unique user identifier. |
| `googleSubjectId` | `String` | Unique, Indexed, Not Null | Google Sub identifier from Google OAuth2 ID Token. |
| `email` | `String` | Unique, Indexed, Lowercase, Not Null | Verified Gmail address used for exact search. |
| `displayName` | `String` | Not Null, Max 100 chars | Name synced from Google profile or customized. |
| `avatarUrl` | `String` | Nullable, URL format | Profile photo URL from Google. |
| `createdAt` | `Date` | Not Null | Account creation timestamp. |
| `lastSeenAt` | `Date` | Not Null | Timestamp of last user presence/activity. |
| `isOnline` | `Boolean` | Default: `false` | Real-time presence flag maintained by WebSocket sessions. |

---

### 2.2 Collection: `user_public_keys`
Represents public cryptographic key bundles published by a user. **Zero private keys are stored here.**

| Field Name | Type | Constraints | Description |
|---|---|---|---|
| `_id` | `ObjectId / String` | Primary Key | Unique key bundle record ID. |
| `userId` | `String` | Unique, Indexed, Not Null | Foreign key reference to `users._id`. |
| `identityPublicKey` | `String` | Not Null, Base64 | Public ECDH (P-256) Identity Key (SPKI format). |
| `signedPreKey` | `String` | Not Null, Base64 | Current active Signed Pre-Key. |
| `preKeySignature` | `String` | Not Null, Base64 | Digital signature validating the pre-key. |
| `keyVersion` | `Integer` | Default: `1` | Incremented upon key rotation. |
| `updatedAt` | `Date` | Not Null | Timestamp of last key update. |

---

### 2.3 Collection: `conversations`
Represents a 1-1 chat channel between two participants.

| Field Name | Type | Constraints | Description |
|---|---|---|---|
| `_id` | `ObjectId / String` | Primary Key | Unique conversation identifier. |
| `participantAId` | `String` | Indexed, Not Null | User ID of the initiator. |
| `participantBId` | `String` | Indexed, Not Null | User ID of the recipient. |
| `status` | `String` | Enum, Not Null | Status: `INITIATING`, `PENDING_ACCEPTANCE`, `HANDSHAKE_IN_PROGRESS`, `VERIFIED_ACTIVE`, `BLOCKED`. |
| `lastMessageId` | `String` | Nullable | ID of the most recent message for snippet preview. |
| `lastMessageAt` | `Date` | Nullable, Indexed | Timestamp of last message (for sorting sidebar). |
| `createdAt` | `Date` | Not Null | Conversation creation timestamp. |
| `updatedAt` | `Date` | Not Null | Last update timestamp. |

*Compound Index*: `{ participantAId: 1, participantBId: 1 }` (unique) to guarantee only one conversation exists per pair.

---

### 2.4 Collection: `handshake_verifications`
Governs the 4-layer verification state for initiating a conversation.

| Field Name | Type | Constraints | Description |
|---|---|---|---|
| `_id` | `ObjectId / String` | Primary Key | Unique verification ID. |
| `conversationId` | `String` | Unique, Indexed, Not Null | Foreign key reference to `conversations._id`. |
| `layer1Status` | `String` | Enum: `VERIFIED`, `FAILED` | Layer 1: Google account validation. |
| `layer2Status` | `String` | Enum: `PENDING`, `ACCEPTED`, `REJECTED` | Layer 2: Recipient consent. |
| `layer3Status` | `String` | Enum: `PENDING`, `EXCHANGED`, `FAILED` | Layer 3: Cryptographic pre-key exchange. |
| `layer4Status` | `String` | Enum: `PENDING`, `CONFIRMED`, `FAILED` | Layer 4: Visual safety code confirmation. |
| `safetyCode` | `String` | 6 Digits (`\d{6}`) | Visual 6-digit verification code (e.g. `482910`). |
| `fullFingerprintHex`| `String` | 60-char Hex string | Full cryptographic SHA-256 fingerprint. |
| `layer1VerifiedAt` | `Date` | Nullable | Timestamp Layer 1 passed. |
| `layer2AcceptedAt` | `Date` | Nullable | Timestamp Layer 2 accepted. |
| `layer3ExchangedAt`| `Date` | Nullable | Timestamp Layer 3 key exchange completed. |
| `layer4ConfirmedAt`| `Date` | Nullable | Timestamp Layer 4 safety code confirmed. |
| `completedAt` | `Date` | Nullable | Timestamp when conversation reached `VERIFIED_ACTIVE`. |

---

### 2.5 Collection: `encrypted_messages`
Stores encrypted message payloads in Zero-Knowledge compliance.

| Field Name | Type | Constraints | Description |
|---|---|---|---|
| `_id` | `ObjectId / String` | Primary Key | Unique message identifier. |
| `conversationId` | `String` | Indexed, Not Null | Foreign key reference to `conversations._id`. |
| `senderId` | `String` | Indexed, Not Null | User ID of message sender. |
| `recipientId` | `String` | Indexed, Not Null | User ID of message recipient. |
| `messageType` | `String` | Enum: `TEXT`, `IMAGE` | Type of payload. |
| `ciphertext` | `String` | Not Null, Base64 | AES-256-GCM encrypted payload. |
| `initializationVector`| `String` | Not Null, Base64 | 12-byte initialization vector (IV). |
| `mediaUrl` | `String` | Nullable, URL | URL to encrypted image blob (if `messageType == IMAGE`). |
| `isRevoked` | `Boolean` | Default: `false` | True if unsent for everyone. |
| `revokedAt` | `Date` | Nullable | Timestamp of retraction. |
| `sequenceNumber` | `Integer` | Not Null | Incremental sequence counter for ordering. |
| `sentAt` | `Date` | Not Null, Indexed | Client sent timestamp. |
| `deliveredAt` | `Date` | Nullable | Recipient delivery timestamp. |
| `readAt` | `Date` | Nullable | Recipient read receipt timestamp. |

---

## 3. Client-Side Secure Storage Schema (IndexedDB)

Database: `ChatMessageE2E_ClientDB` (version 1)

### 3.1 Object Store: `identity_keys` (KeyPath: `keyId`)
- `keyId`: `"primary_identity"`
- `privateKey`: `CryptoKey` (Non-extractable ECDH P-256 private key).
- `publicKey`: `CryptoKey` (ECDH P-256 public key).
- `rawPublicKeySpki`: `ArrayBuffer` (Exported public key for sharing).
- `createdAt`: `Timestamp`.

### 3.2 Object Store: `conversation_sessions` (KeyPath: `conversationId`)
- `conversationId`: String (e.g. `"conv_123"`).
- `peerUserId`: String.
- `sharedSecretKey`: `CryptoKey` (Derived AES-GCM 256-bit session key).
- `safetyCode`: String (6 digits).
- `fullFingerprintHex`: String.
- `ratchetSendCounter`: Number.
- `ratchetReceiveCounter`: Number.
- `updatedAt`: `Timestamp`.

### 3.3 Object Store: `local_decrypted_messages` (KeyPath: `messageId`)
- `messageId`: String.
- `conversationId`: String (Indexed).
- `senderId`: String.
- `messageType`: `"TEXT" | "IMAGE"`.
- `plaintext`: String (Plaintext message content for rendering).
- `decryptedMediaBlobUrl`: String (Object URL of decrypted image).
- `isRevoked`: Boolean.
- `sentAt`: Timestamp.
- `status`: `"SENDING" | "SENT" | "DELIVERED" | "READ"`.
