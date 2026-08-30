# Feature Specification: Re-Handshake & Unblock Contact

**Feature Branch**: `002-rehandshake-and-unblock`

**Created**: 2026-08-30

**Status**: Draft

**Input**: User description: "re handshake cũng như thêm chức năng gỡ block"

## Clarifications

### Session 2026-08-30
- Q: How should the system trigger and guide users through the re-handshake process when a key mismatch is detected upon opening an existing conversation? → A: Option A (Auto-detect key mismatch upon opening chat, display warning banner with 'Re-verify' button, and disable chat input until 4-layer re-handshake is verified)
- Q: When a user unblocks a contact, what state should the conversation resume to if both participants' public keys remain unchanged? → A: Option A (Restore conversation to its pre-blocked status; if keys are unchanged, resume VERIFIED_ACTIVE directly, otherwise show re-handshake banner)
- Q: How should the chat interface handle historical messages sent prior to a re-handshake when a user is on a new device or session without local message cache? → A: Option A (Display a security timeline divider notifying that a new E2EE session was established and display only decryptable messages from that point forward on the new device)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automatic Key Mismatch Detection & Re-Handshake (Priority: P1)

As a chat user who opened a new browser session, changed devices, or cleared local keys, I want the system to detect when my cryptographic identity key does not match the active conversation's established handshake, and allow me to initiate a re-handshake so that my peer and I can securely re-establish a synchronized E2EE session and resume messaging.

**Why this priority**: Without re-handshake capability, whenever a user loses their local key (such as closing an incognito window or logging in on a new device), existing conversations become permanently unreadable and cannot send or receive messages due to cryptographic session key divergence.

**Independent Test**: Can be independently tested by clearing client identity keys on User A's browser, opening an existing verified conversation with User B, clicking "Re-verify / Re-handshake", completing the 4-layer verification with User B, and verifying that new plaintext messages are successfully encrypted, transmitted, and decrypted by both parties.

**Acceptance Scenarios**:

1. **Given** User A and User B have an existing verified conversation (`VERIFIED_ACTIVE`), **When** User A logs in with a new identity key pair (e.g. from a new session) and opens the conversation, **Then** the application detects the public key mismatch, displays a "Security Key Changed" warning banner, and disables message input until re-verification occurs.
2. **Given** a detected key mismatch, **When** User A clicks "Re-verify", **Then** the conversation transitions to `HANDSHAKE_IN_PROGRESS` with the updated public key, and User B receives an immediate real-time notification (`KEY_CHANGED`) alerting them to re-verify.
3. **Given** both users are in the re-handshake flow, **When** both users accept the new exchange and verify the new 6-digit visual Safety Code (Layer 4), **Then** the conversation status returns to `VERIFIED_ACTIVE`, a new shared AES-GCM session key is derived on both clients, and both users can send/receive encrypted messages seamlessly.
4. **Given** a re-handshake is completed on a new session/device without prior local IndexedDB cache, **When** the chat feed renders, **Then** a security timeline divider is displayed indicating a new E2EE session was established, and only messages encrypted under the new session key are rendered.

---

### User Story 2 - Unblock Contact Functionality (Priority: P2)

As a user who previously blocked a contact, I want to be able to unblock them directly from the chat header or a blocked contacts view, so that we can communicate again when desired.

**Why this priority**: Users need full control over their relationship privacy, including the ability to reverse a block action without contacting support or manually manipulating the database.

**Independent Test**: Can be independently tested by blocking User B from User A's interface, verifying that communication is halted and the UI shows "Blocked", then clicking "Unblock", and confirming that the block is lifted on both backend and frontend.

**Acceptance Scenarios**:

1. **Given** User A has blocked User B, **When** User A views the conversation or contact profile with User B, **Then** the UI clearly indicates that the contact is currently blocked and provides an "Unblock Contact" action button.
2. **Given** User A clicks "Unblock Contact", **When** the unblock request is confirmed, **Then** the system removes User B from User A's block list, restores the conversation to its previous status (e.g. `VERIFIED_ACTIVE` if keys are unchanged), and notifies User A of the successful unblock.
3. **Given** an unblocked contact whose keys have not changed, **When** either user navigates to the conversation, **Then** communication is immediately restored to `VERIFIED_ACTIVE` without requiring a redundant handshake. If keys changed during the block period, the system displays the Re-Handshake banner.

---

### Edge Cases

- **Concurrent Re-Handshake Requests**: If both User A and User B attempt to initiate a re-handshake simultaneously, the system MUST resolve the conflict deterministically using the latest timestamp and maintain cryptographic consistency.
- **Messaging During Re-Handshake**: If either user attempts to send a message while a re-handshake is in progress (`HANDSHAKE_IN_PROGRESS` or `PENDING_ACCEPTANCE`), message sending MUST remain disabled to prevent transmission of undecryptable ciphertexts.
- **Unblocking When Peer Has Also Blocked**: If User A unblocks User B, but User B still has User A blocked, User A sees that they unblocked User B, but messaging remains restricted until User B also unblocks User A.
- **Offline Peer During Re-Handshake**: If User B is offline when User A requests a re-handshake, User B MUST see the pending re-handshake prompt upon their next login or reconnection.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a mechanism to detect when a participant's registered identity public key differs from the public key stored in the conversation's active handshake verification record.
- **FR-002**: System MUST allow either conversation participant to initiate a re-handshake workflow (`re-initiate handshake`) for an existing conversation via a visible 'Re-verify' action banner.
- **FR-003**: Upon re-handshake initiation, System MUST update the conversation handshake record with the initiator's new public key and reset layer verification statuses to allow fresh consensus.
- **FR-004**: System MUST push real-time WebSocket notifications (`KEY_CHANGED` / `HANDSHAKE_INVITATION_RECEIVED`) to the peer when a re-handshake is initiated.
- **FR-005**: System MUST compute and present a new 6-digit deterministic Safety Code derived from the updated public key pair for mutual visual verification.
- **FR-006**: System MUST prevent message transmission in a conversation while a re-handshake is pending or unverified.
- **FR-007**: System MUST provide a dedicated Unblock Contact API endpoint and UI action to remove a user from the active user's blocked list.
- **FR-008**: System MUST update the conversation state and UI immediately when a contact is unblocked, restoring `VERIFIED_ACTIVE` if identity keys remain consistent or prompting for Re-Handshake if keys diverge.
- **FR-009**: System MUST persist blocked and unblocked user relationships in the user profile/domain layer with clear audit timestamps.
- **FR-010**: System MUST render a distinct security session divider in the chat feed when a new E2EE session key is established on a device without prior message cache.

### Key Entities

- **HandshakeVerification**: Represents the multi-layer cryptographic consensus between two participants for a conversation. Key attributes: `conversationId`, `initiatorPublicKey`, `recipientPublicKey`, `safetyCode`, `layer1Status` through `layer4Status`, `updatedAt`.
- **UserBlockRecord**: Represents a directional block relationship between an actor user and a target blocked user. Key attributes: `userId`, `blockedUserId`, `blockedAt`.
- **Conversation**: Represents a 1-to-1 secure communication channel with statuses: `PENDING_ACCEPTANCE`, `HANDSHAKE_IN_PROGRESS`, `VERIFIED_ACTIVE`, `BLOCKED`.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users who lose local session keys or log in from a new browser session can re-establish an active E2EE session within 30 seconds via the re-handshake flow.
- **SC-002**: 100% of messages sent after a successful re-handshake are decryptable by both participants with zero "Decryption Failed" errors.
- **SC-003**: Unblocking a contact takes effect immediately (< 500ms response time) and enables standard conversation workflows without requiring page reload.
- **SC-004**: Zero cryptographic key leaks — private keys remain strictly client-side and unexportable throughout all re-handshake operations.

---

## Assumptions

- Both users have access to standard Web Crypto API support in their client environment.
- The existing 4-Layer Handshake protocol foundation (ECDH P-256 + HKDF SHA-256 + 6-digit visual Safety Code) is reused for re-handshake verification.
- Blocked relationships are directional (User A blocking User B prevents User B from initiating chats or sending messages to User A).
