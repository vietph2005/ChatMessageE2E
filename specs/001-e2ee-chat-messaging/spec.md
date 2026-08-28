# Feature Specification: 1-1 End-to-End Encrypted Chat with 4-Layer Handshake Verification

**Feature Branch**: `001-e2ee-chat-messaging`

**Created**: 2026-08-28

**Status**: Draft

**Input**: User description: "Hỗ trợ chat 1-1. Dùng xác thực 4 lớp để xác thực khi lần đầu khởi tạo cuộc trò chuyện. Các tin nhắn giữa nhau phải được mã hóa. Sử dụng đăng nhập google và gmail. Giao diện dựa trên mesage"

## Clarifications

### Session 2026-08-28
- Q: Trong quy trình xác thực 4 lớp khi khởi tạo chat 1-1 lần đầu, người dùng sẽ thực hiện xác nhận Lớp 4 (Mã An Toàn / Safety Code) theo hình thức nào? → A: Option A - Hệ thống tự động tính toán mã an toàn trực quan (chuỗi 6 chữ số / QR) từ khóa công khai của hai bên; người dùng chỉ cần đối soát và bấm "Xác nhận khớp mã" để hoàn tất Lớp 4 và mở khóa kênh chat.
- Q: Khi người dùng đăng nhập bằng tài khoản Google trên một trình duyệt hoặc thiết bị mới (hoặc sau khi xóa dữ liệu trình duyệt), hệ thống sẽ xử lý khóa bảo mật riêng tư (Private Key) và lịch sử tin nhắn như thế nào? → A: Option A - Khóa riêng tư lưu trữ cục bộ độc lập (Local-Only Identity). Mỗi trình duyệt/thiết bị mới tự sinh một cặp khóa độc lập và cập nhật Public Key Bundle lên máy chủ; không bao giờ lưu Private Key lên máy chủ; hệ thống tự động phát hiện và gửi thông báo cập nhật Safety Code tới các bạn chat khi khóa thay đổi.
- Q: Trong phạm vi phiên bản hiện tại (v1), hệ thống chat 1-1 sẽ hỗ trợ những loại nội dung tin nhắn nào giữa hai người dùng? → A: Option A - Hỗ trợ tin nhắn văn bản, biểu tượng cảm xúc (emoji) và hình ảnh mã hóa đầu-cuối (JPG, PNG, GIF dung lượng tối đa 5MB) được mã hóa cục bộ tại client trước khi truyền tải qua máy chủ.
- Q: Người dùng sẽ tìm kiếm và khám phá các liên hệ khác để bắt đầu cuộc trò chuyện 1-1 bằng phương thức tìm kiếm nào? → A: Option A - Tìm kiếm chính xác theo địa chỉ Gmail (Exact Gmail Search). Người dùng chỉ có thể tìm thấy và gửi lời mời khi nhập chính xác địa chỉ Gmail; không hiển thị danh sách gợi ý người dùng công khai nhằm bảo vệ quyền riêng tư.
- Q: Hệ thống chat 1-1 sẽ hỗ trợ cơ chế xóa hoặc thu hồi tin nhắn (Unsend / Delete) như thế nào giữa hai người dùng? → A: Option A - Hỗ trợ cả hai tùy chọn: "Thu hồi cho mọi người" (Unsend for Everyone) và "Xóa ở phía tôi" (Delete for Me) với thông báo trạng thái thu hồi hiển thị đồng bộ trên cả hai client.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Google Authentication & Identity Onboarding (Priority: P1)

Users access the application and securely sign in using their Google/Gmail account. Upon initial sign-in, the system establishes their authenticated session, imports their Google profile details (name, email, avatar), and initializes their local cryptographic identity for secure messaging in local browser storage (Local-Only Identity).

**Why this priority**: Authentication is the foundational prerequisite for establishing verified user identities, searchability via exact Gmail, and binding cryptographic keys to legitimate accounts.

**Independent Test**: Can be fully tested by navigating to the application, authenticating via Google OAuth2, verifying that the user profile displays accurate Google information, and confirming local cryptographic identity keys are generated.

**Acceptance Scenarios**:

1. **Given** an unauthenticated user on the login screen, **When** the user clicks "Sign in with Google" and completes the Google OAuth2 consent flow, **Then** the user is redirected to the main Messenger-style chat interface with their profile loaded.
2. **Given** a user logging in for the first time on a browser, **When** authentication succeeds, **Then** the client automatically initializes local cryptographic identity keys in browser storage and registers public key material with the identity directory.
3. **Given** an expired or invalid session token, **When** the user attempts to perform any action, **Then** the user is prompted to re-authenticate with Google.

---

### User Story 2 - 4-Layer Asynchronous Handshake Verification for Initiating 1-1 Conversation (Priority: P1)

When a user initiates a 1-1 conversation with another user for the first time, the system enforces a mandatory 4-layer verification process before allowing message exchange. **Crucially, this process is fully asynchronous (offline-friendly)**: the initiator can send the invitation and cryptographic challenge even if the recipient is offline; the recipient can review, accept, and confirm the safety code whenever they next open the application.

- **Layer 1 (Identity & Google Account Validation)**: Both sender and recipient are validated as active Google/Gmail accounts by the system.
- **Layer 2 (Mutual Request & Explicit Consent)**: The sender issues a conversation request, queued on the server until the recipient reviews and explicitly accepts the connection.
- **Layer 3 (Asynchronous End-to-End Cryptographic Key Handshake)**: Clients perform a cryptographic key exchange using pre-published public key bundles, enabling the initiator to establish the session without waiting for the recipient to be online simultaneously.
- **Layer 4 (Channel Safety Code Challenge Confirmation)**: A mutual visual safety code (matching 6-digit visual security code or safety number verification) is confirmed by the recipient (and initiator) with a single-click "Confirm Code Matches", sealing the secure channel.

**Why this priority**: Prevents unsolicited spam, guarantees non-repudiation, allows natural asynchronous communication without requiring simultaneous presence, and ensures that end-to-end encrypted sessions are mutually authenticated against Man-in-the-Middle (MITM) attacks before any communication occurs.

**Independent Test**: Can be tested by having User A initiate a chat while User B is offline, verifying the pending challenge is stored, having User B log in later to accept and confirm the safety code, and confirming the chat unlocks for both parties.

**Acceptance Scenarios**:

1. **Given** User A searches for User B by exact Gmail address, **When** User A initiates a new conversation, **Then** the system checks Layer 1 (Google identity verified) and queues the conversation invitation in "Pending Acceptance" (Layer 2).
2. **Given** User B is offline when User A sends the request, **When** User B later logs in, **Then** User B sees a pending conversation request notification with User A's profile.
3. **Given** User B reviews the request, **When** User B accepts the request, **Then** Layer 2 completes and the client processes Layer 3 (cryptographic pre-key exchange) and displays the Layer 4 visual 6-digit safety code challenge.
4. **Given** User B confirms the Layer 4 safety code, **Then** the conversation status transitions to "Secure & Verified" for User B immediately; when User A next accesses the chat, User A sees the verified confirmation and the message input box is enabled for both users.
5. **Given** User B rejects the conversation request at Layer 2, **Then** the conversation request is dismissed and no communication channel is opened.

---

### User Story 3 - Real-Time End-to-End Encrypted 1-1 Messaging & Media (Priority: P1)

Once a 1-1 conversation is verified, users can send and receive real-time text messages (with emoji) and encrypted images (≤ 5MB), as well as manage message retractions. Every message or media attachment is encrypted on the sender's client using the verified session keys, transmitted across the server as opaque ciphertext, and decrypted solely on the recipient's client.

**Why this priority**: Delivering confidential, low-latency communication with modern rich media and message control is the primary purpose of the application.

**Independent Test**: Can be tested by sending text and encrypted images between two verified active users, confirming immediate delivery in the UI, testing message recall ("Unsend for Everyone"), and verifying that the backend server store only holds encrypted ciphertext with zero plaintext visibility.

**Acceptance Scenarios**:

1. **Given** two users with an active verified conversation, **When** User A types a text message or attaches an image (≤ 5MB) and clicks send, **Then** the payload is encrypted on User A's client, transmitted in real-time, and delivered to User B.
2. **Given** User B receives an encrypted incoming message or image payload, **When** the message reaches User B's client, **Then** it is decrypted locally and rendered in the conversation timeline in chronological order.
3. **Given** User B is temporarily offline, **When** User A sends an encrypted message, **Then** the server stores the encrypted payload and delivers it immediately when User B reconnects.
4. **Given** a message is sent and delivered, **When** state changes occur, **Then** real-time delivery and read status indicators (sent, delivered, read) update for the sender.
5. **Given** User A selects "Unsend for Everyone" on a sent message, **When** confirmed, **Then** the message ciphertext is replaced with a revocation tombstone and both clients display "This message was unsent".
6. **Given** User A selects "Delete for Me", **When** confirmed, **Then** the message is deleted only from User A's local client storage without altering User B's view.

---

### User Story 4 - Messenger-Inspired Modern User Interface (Priority: P2)

Users interact with an interface inspired by modern Messenger: a left conversation sidebar showing contacts, recent chats, unread badges, and active status; a center chat area with styled message bubbles, timestamps, typing indicators, image previews, and message action menus; and a right-hand conversation details panel displaying security status and safety numbers.

**Why this priority**: A responsive, intuitive, and polished user interface provides high usability and clarity for real-time interactions and security statuses.

**Independent Test**: Can be tested across desktop and mobile screen resolutions to verify responsive sidebar toggling, chat bubble alignments, active status indicators, and typing status animations.

**Acceptance Scenarios**:

1. **Given** a user logged into the application, **When** viewing the main screen, **Then** the left sidebar displays their active conversations sorted by most recent message with unread count badges and exact Gmail search input.
2. **Given** an open conversation, **When** the other participant starts typing, **Then** a real-time typing indicator appears in the chat window.
3. **Given** messages displayed in the active chat, **When** viewing the message stream, **Then** the user's own messages appear right-aligned (accent color) and incoming messages appear left-aligned (neutral color) with timestamps, read receipts, and action menus (Unsend / Delete).
4. **Given** a mobile viewport, **When** selecting a conversation from the sidebar, **Then** the view transitions smoothly into full-screen chat mode with a back navigation button to return to the sidebar.

---

### User Story 5 - Conversation Security Details & Safety Number Verification (Priority: P3)

Users can open a conversation information panel to inspect the security attributes of their 1-1 chat, view and compare the cryptographic safety number/fingerprint, review verification history for all 4 layers, or block/unfriend the contact.

**Why this priority**: Empowers users with transparency and cryptographic verification tools, building high trust in the platform.

**Independent Test**: Can be tested by opening the conversation settings drawer and comparing safety number strings between two browser sessions.

**Acceptance Scenarios**:

1. **Given** an established conversation, **When** a user clicks the "Security Details" button, **Then** the panel displays the status of all 4 verification layers and the 60-digit formatted safety number (or QR code).
2. **Given** a contact whose device/key changed, **When** the user is notified of the safety number change, **Then** the user can re-verify the new safety code to confirm authenticity.
3. **Given** a user chooses to block a contact, **When** confirmed, **Then** the blocked contact cannot send further messages or initiate new handshakes.

---

### Edge Cases

- **Offline Handshake Interruption**: If either party loses network connection during Layer 2, 3, or 4 of the handshake, the conversation remains in its current pending stage and resumes gracefully upon reconnection without corrupting key states.
- **Out-of-Order Key Handshake Packets**: Handshake packets arriving out of order are queued and processed sequentially based on sequence identifiers.
- **Multiple Device / New Browser Login**: When a user logs in from a new browser/device, a new local key pair is generated; previous history remains on the original device (Local-Only Identity), and contacts receive a "Safety number changed" notice.
- **Invalid / Tampered Message Payloads**: If a received message cannot be decrypted with the session key (e.g., tampered payload or corrupted sequence), the client displays a "Message could not be decrypted" warning and requests a session key resynchronization without crashing.
- **Simultaneous Cross-Initiation**: If User A and User B initiate a 1-1 chat request to each other at the exact same moment, the system detects the duplicate request pair and merges them into a single 4-layer handshake negotiation.
- **Revoked Google Permissions**: If a user revokes OAuth access or their Google account is deactivated, all active WebSocket connections are terminated and the session is invalidated.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST authenticate users exclusively via Google OAuth2 (Gmail identity).
- **FR-002**: System MUST retrieve and maintain basic user profile information (display name, Gmail address, avatar URL) from Google identity providers.
- **FR-003**: System MUST generate and securely store client-side cryptographic key pairs (Identity Key, Pre-keys) in client-side secure browser storage (Local-Only Identity).
- **FR-004**: System MUST allow users to search and discover other users exclusively using their exact Gmail address (preventing public user enumeration).
- **FR-005**: System MUST enforce a 4-layer verification process for any initial 1-1 conversation before allowing message exchange:
  - **FR-005.1 (Layer 1)**: System MUST verify that both initiating and receiving users possess valid, active Google accounts.
  - **FR-005.2 (Layer 2)**: System MUST require the recipient to explicitly accept or decline an incoming conversation invitation.
  - **FR-005.3 (Layer 3)**: System MUST perform an asynchronous end-to-end cryptographic key exchange handshake between clients once the invitation is accepted.
  - **FR-005.4 (Layer 4)**: System MUST require confirmation of a visual 6-digit safety code / QR match generated from exchanged public keys to finalize channel establishment.
- **FR-006**: System MUST prevent any message sending or transmission in a conversation until all 4 verification layers have reached the "Completed" status.
- **FR-007**: System MUST encrypt all message contents (text, emoji, and images ≤ 5MB) on the sending client prior to transmission using modern authenticated encryption algorithms (AES-GCM).
- **FR-008**: System MUST ensure that the backend server only stores and transports encrypted ciphertexts, metadata (timestamps, sender/receiver IDs, message IDs), and public key bundles, with zero access to plaintext message bodies or private keys (Zero-Knowledge Invariant).
- **FR-009**: System MUST deliver messages in real time via bi-directional WebSocket communication with delivery receipts (Sent, Delivered, Read).
- **FR-010**: System MUST support offline message queueing such that encrypted messages sent to an offline user are delivered as soon as the recipient reconnects.
- **FR-011**: System MUST provide real-time typing indicator events and online/offline presence statuses for 1-1 chat participants.
- **FR-012**: System MUST render a modern Messenger-style user interface comprising:
  - Collapsible/responsive conversation list sidebar with recent snippets, timestamps, and unread count badges.
  - Header showing contact name, avatar, online status, and conversation security badge.
  - Chronological message history stream with sender-differentiated chat bubbles.
  - Rich message input bar with send action, image attachment button, and typing detection.
  - Slide-out conversation security info panel displaying safety codes and verification details.
- **FR-013**: System MUST alert users whenever the safety number of a conversation participant changes (e.g., due to key rotation or new device login).
- **FR-014**: System MUST allow users to block/unblock contacts and terminate active chat sessions.
- **FR-015**: System MUST provide clear, user-friendly error messages when network disruptions or cryptographic verification failures occur.
- **FR-016**: System MUST support message retraction ("Unsend for Everyone") replacing ciphertext with a revocation tombstone, as well as local message deletion ("Delete for Me").
- **FR-017**: System MUST support client-side encrypted image attachments (JPG, PNG, GIF up to 5MB) rendered securely within message bubbles.

### Key Entities *(include if feature involves data)*

- **UserProfile**: Represents a registered user. Attributes: `id`, `googleSubjectId`, `email` (Gmail), `displayName`, `avatarUrl`, `createdAt`, `lastSeenAt`.
- **UserPublicKeyBundle**: Represents public cryptographic keys published by a user. Attributes: `userId`, `identityPublicKey`, `signedPreKey`, `preKeySignature`, `oneTimePreKeys`, `updatedAt`.
- **Conversation**: Represents a 1-1 chat channel between two users. Attributes: `id`, `participantAId`, `participantBId`, `status` (`INITIATING`, `PENDING_ACCEPTANCE`, `HANDSHAKE_IN_PROGRESS`, `VERIFIED_ACTIVE`, `BLOCKED`), `createdAt`, `lastActivityAt`.
- **HandshakeVerification**: Represents the 4-layer verification state of a conversation. Attributes:
  - `conversationId`
  - `layer1Status` (`VERIFIED`, `FAILED`) - Google Identity Verification
  - `layer2Status` (`PENDING`, `ACCEPTED`, `REJECTED`) - Invitation Consent
  - `layer3Status` (`PENDING`, `EXCHANGED`, `FAILED`) - Crypto Key Handshake
  - `layer4Status` (`PENDING`, `CONFIRMED`, `FAILED`) - Safety Challenge Confirmation (6-digit safety code)
  - `safetyNumber` (computed fingerprint / 6-digit code)
  - `completedAt`
- **EncryptedMessage**: Represents a message transferred and stored across the system. Attributes: `id`, `conversationId`, `senderId`, `recipientId`, `messageType` (`TEXT`, `IMAGE`), `ciphertext`, `initializationVector` (IV), `mediaUrl` (encrypted blob reference if image), `isRevoked`, `revokedAt`, `senderKeyId`, `sequenceNumber`, `sentAt`, `deliveredAt`, `readAt`.
- **SessionRatchetState**: Client-side persisted state for managing session keys, ratchet chains, and message decryption counters for a specific conversation.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: **Authentication Speed**: Users complete Google OAuth sign-in and land on the chat interface in under 3 seconds under normal network conditions.
- **SC-002**: **4-Layer Handshake Completion & Reliability**: When both users are actively online, the complete 4-layer verification handshake completes in under 15 seconds. In asynchronous scenarios (where recipient is offline), 100% of pending invitations, pre-key bundles, and safety challenges are reliably persisted on the server and delivered without data loss when the recipient reconnects.
- **SC-003**: **Real-Time Delivery Latency**: 99% of messages sent between online participants are delivered and decrypted in under 500 milliseconds.
- **SC-004**: **Zero-Knowledge Data Integrity**: 100% of persisted message bodies on the server database are encrypted; zero instances of plaintext message content or private keys exist in server logs or database stores.
- **SC-005**: **Unverified Message Block Rate**: 100% of attempts to transmit message payloads before completing all 4 verification layers are strictly rejected.
- **SC-006**: **Responsive Usability**: UI renders and functions seamlessly without horizontal scroll or clipping across standard screen widths ranging from 360px (mobile) to 2560px (4K desktop).

---

## Assumptions

- **Target Platforms**: Modern evergreen web browsers (Chrome, Firefox, Edge, Safari) supporting modern HTML5, WebSockets, and standard Web Cryptography APIs.
- **Google Identity**: Google OAuth 2.0 / OpenID Connect service is available and provides verified Gmail email addresses and basic public profile information.
- **Scope Boundary for Initial Feature**: The initial implementation focuses on 1-1 text messaging, emojis, and encrypted images (≤ 5MB), with group chat, voice/video calling, and large files reserved for future features.
- **Client-Side Key Management (Local-Only)**: User private keys are generated and stored exclusively within the user's browser local secure storage (IndexedDB) and are never transmitted to any server.
- **Network Resilience**: WebSocket connections automatically attempt reconnect with exponential backoff if temporary network interruptions occur.
