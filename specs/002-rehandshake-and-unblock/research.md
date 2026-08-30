# Technical Research & Architecture Decisions: Re-Handshake & Unblock Contact

**Feature**: `002-rehandshake-and-unblock`
**Date**: 2026-08-30

## Research Findings & Technical Decisions

### 1. Key Mismatch Detection Mechanism

#### Decision:
Compare the local `primary_identity` public key loaded from `IndexedDB` with the user's corresponding public key stored in the conversation's active `HandshakeVerification` record (retrieved via `apiClient.getConversationDetail(id)`).

#### Rationale:
- If a user opens a new browser/incognito session or logs in on a new device, a new `CryptoKeyPair` is generated and saved in `IndexedDB`.
- When the user opens an existing conversation:
  - If `user.id == participantAId`, check if `myPublicKey != initiatorPublicKey`.
  - If `user.id == participantBId`, check if `myPublicKey != recipientPublicKey`.
- If a mismatch is detected, the frontend immediately flags `isKeyMismatched = true`, displays the `SafetyNumberAlertBanner`, and sets `activeSessionKey = null` to prevent sending unencryptable/corrupted messages.

#### Alternatives Considered:
- *Re-registering keys without warning*: Insecure; peer would be unable to decrypt messages without warning, leading to silent message loss.
- *Forcing conversation deletion*: Destructive; loses conversation history on peer devices.

---

### 2. Re-Handshake Initiation & State Machine

#### Decision:
Expose a REST endpoint `POST /api/v1/conversations/{conversationId}/handshake/re-initiate` taking `{ initiatorPublicKey: string }`.

#### Workflow:
1. When User A clicks "Re-verify", frontend calls `/api/v1/conversations/{conversationId}/handshake/re-initiate`.
2. Backend:
   - Sets `conversation.status = HANDSHAKE_IN_PROGRESS`.
   - If User A is Participant A: updates `handshake.initiatorPublicKey`, sets `layer1Status = VERIFIED`, resets `layer2Status = PENDING`, `layer3Status = PENDING`, `layer4Status = PENDING`.
   - If User A is Participant B: updates `handshake.recipientPublicKey`, resets layers appropriately.
   - Saves `HandshakeVerification` and `Conversation`.
   - Pushes real-time notification to User B via `messagingTemplate.convertAndSendToUser(peerId, "/queue/notifications", payload)` with `eventType = "KEY_CHANGED"`.
3. Both clients re-run Layer 2/3 exchange and Layer 4 Safety Code confirmation:
   - A new deterministic 6-digit visual Safety Code is computed from the new public key pair.
   - Once both confirm Layer 4, status transitions back to `VERIFIED_ACTIVE`, and both derive the new `activeSessionKey` (AES-GCM-256).

---

### 3. Unblock Contact Mechanism & State Restoration

#### Decision:
Expose a REST endpoint `POST /api/v1/users/unblock` taking `{ userId: string }`.

#### Workflow:
1. Backend removes `targetUserId` from `currentUser.blockedUserIds`.
2. Updates any existing conversation between User A and User B:
   - If User B has NOT blocked User A:
     - Check if existing `HandshakeVerification` has valid keys and `layer4Status == CONFIRMED`:
       - If valid, restore `conversation.status = VERIFIED_ACTIVE`.
       - If keys diverged, set `conversation.status = HANDSHAKE_IN_PROGRESS` or `PENDING_ACCEPTANCE`.
   - If User B STILL has User A blocked:
     - Leave `conversation.status = BLOCKED` (or unilateral block state) until User B also unblocks User A.
3. Frontend updates `useChat` state (`loadConversations()`) and restores the chat view.

---

### 4. Historical Message Display on New Device

#### Decision:
In the chat feed (`MessageBubble` / `AppShell`), when a new E2EE session key is established on a device without prior IndexedDB cache, render a visual divider:
`🔒 End-to-End Encryption session re-established. Earlier messages sent from other devices are not decryptable on this device.`

#### Rationale:
- In strict Zero-Knowledge E2EE, historical ciphertexts cannot be decrypted without the original ephemeral private key.
- A clear timeline divider provides transparency and prevents user confusion when older messages do not render on a fresh device.
