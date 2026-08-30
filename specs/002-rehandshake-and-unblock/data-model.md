# Data Model & State Transitions: Re-Handshake & Unblock Contact

**Feature**: `002-rehandshake-and-unblock`
**Date**: 2026-08-30

## 1. Domain Entities & Database Documents

### 1.1. Conversation Entity & ConversationDocument
Collection: `conversations`

```json
{
  "_id": "66d1a2b3c4d5e6f7a8b9c0d1",
  "participantAId": "user_alice_123",
  "participantBId": "user_bob_456",
  "status": "VERIFIED_ACTIVE", // Enum: INITIATING, PENDING_ACCEPTANCE, HANDSHAKE_IN_PROGRESS, VERIFIED_ACTIVE, BLOCKED
  "blockedByUserId": null, // Optional: captures who initiated the block when status == BLOCKED
  "createdAt": "2026-08-30T10:00:00Z",
  "updatedAt": "2026-08-30T10:30:00Z"
}
```

### 1.2. HandshakeVerification Entity & HandshakeVerificationDocument
Collection: `handshake_verifications`

```json
{
  "_id": "66d1a2b3c4d5e6f7a8b9c0d2",
  "conversationId": "66d1a2b3c4d5e6f7a8b9c0d1",
  "initiatorId": "user_alice_123",
  "recipientId": "user_bob_456",
  "initiatorPublicKey": "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE...", // SPKI Base64 ECDH P-256
  "recipientPublicKey": "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE...", // SPKI Base64 ECDH P-256
  "layer1Status": "VERIFIED",
  "layer1VerifiedAt": "2026-08-30T10:00:00Z",
  "layer2Status": "ACCEPTED",
  "layer2AcceptedAt": "2026-08-30T10:01:00Z",
  "layer3Status": "EXCHANGED",
  "layer3ExchangedAt": "2026-08-30T10:01:00Z",
  "layer4Status": "CONFIRMED",
  "layer4ConfirmedAt": "2026-08-30T10:02:00Z",
  "safetyCode": "583921", // Deterministic 6-digit visual code
  "fullFingerprintHex": "a1b2c3d4e5f6...", // SHA-256 64-character hex string
  "version": 2, // Incremented on each Re-Handshake
  "completedAt": "2026-08-30T10:02:00Z"
}
```

### 1.3. UserProfile Entity & UserProfileDocument
Collection: `users`

```json
{
  "_id": "user_alice_123",
  "googleSubjectId": "google_sub_112233",
  "email": "alice@gmail.com",
  "displayName": "Alice Smith",
  "avatarUrl": "https://lh3.googleusercontent.com/...",
  "blockedUserIds": ["user_charlie_789"], // Set of blocked user IDs
  "createdAt": "2026-08-30T09:00:00Z",
  "lastSeenAt": "2026-08-30T10:30:00Z",
  "isOnline": true
}
```

---

## 2. State Transition Diagrams

### 2.1. Re-Handshake State Transition

```mermaid
stateDiagram-v2
    [*] --> VERIFIED_ACTIVE: Existing conversation with Key_A1 & Key_B
    VERIFIED_ACTIVE --> KEY_MISMATCH_DETECTED: User A logs in on new device (Key_A2)
    KEY_MISMATCH_DETECTED --> HANDSHAKE_IN_PROGRESS: User A clicks "Re-verify" (POST /handshake/re-initiate)
    
    state HANDSHAKE_IN_PROGRESS {
        [*] --> Layer1_Updated: Initiator key replaced with Key_A2
        Layer1_Updated --> Layer2_3_Exchanged: Peer accepts & provides Key_B
        Layer2_3_Exchanged --> Layer4_SafetyCode: Safety Code recomputed with (Key_A2, Key_B)
        Layer4_SafetyCode --> [*]: Both confirm Safety Code
    }

    HANDSHAKE_IN_PROGRESS --> VERIFIED_ACTIVE: Re-handshake complete (New Session Key derived)
```

### 2.2. Block & Unblock State Transition

```mermaid
stateDiagram-v2
    VERIFIED_ACTIVE --> BLOCKED: User A clicks "Block" (POST /api/v1/users/block)
    BLOCKED --> UNBLOCKING: User A clicks "Unblock" (POST /api/v1/users/unblock)
    
    state UNBLOCKING {
        CheckPeerBlock: Is User A blocked by User B?
        CheckKeys: Are public keys still consistent with Handshake?
    }

    UNBLOCKING --> BLOCKED: Peer still has active block on User A
    UNBLOCKING --> VERIFIED_ACTIVE: Keys valid and no mutual block
    UNBLOCKING --> HANDSHAKE_IN_PROGRESS: Keys changed during block period
```
