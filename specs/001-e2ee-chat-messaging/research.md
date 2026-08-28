# Technical Research: 1-1 End-to-End Encrypted Chat with 4-Layer Handshake Verification

**Feature Branch**: `001-e2ee-chat-messaging`  
**Date**: 2026-08-28  
**Status**: Completed  
**Spec Reference**: [`specs/001-e2ee-chat-messaging/spec.md`](spec.md)

---

## 1. Cryptographic Suite & E2EE Handshake Protocol

### Decision: Web Crypto API (SubtleCrypto) with ECDH (P-256) + HKDF + AES-GCM-256 + SHA-256 Fingerprint
- **Key Exchange**: ECDH using NIST curve P-256 (or X25519 where supported) via standard browser `window.crypto.subtle`.
- **Key Derivation (KDF)**: HKDF (RFC 5869) with SHA-256 to derive symmetrical message encryption keys and authentication tags from the shared secret.
- **Message & Media Encryption**: AES-GCM with 256-bit keys and unique 96-bit (12-byte) initialization vectors (IVs) generated per message/media payload.
- **Visual Safety Code (Layer 4)**: SHA-256 hash computed over sorted lexicographical concatenation of both users' public identity keys + conversation ID, truncated to 6 digits (`000000` - `999999`) for simple visual confirmation on-screen, with complete 60-character hex fingerprint available in the Security panel.
- **Client Storage**: Private keys and ratchet keys stored strictly in browser IndexedDB (never exported or transmitted to the network).

### Rationale:
- Native browser `crypto.subtle` offers hardware-accelerated, timing-attack-resistant cryptographic operations without bulky external JavaScript crypto libraries.
- AES-GCM provides authenticated encryption with associated data (AEAD), guaranteeing both confidentiality and integrity/tamper detection.
- Aligns strictly with Constitution Principle III (Privacy & E2EE by Default) and Zero-Knowledge Invariant.

### Alternatives Considered:
- *Pure JavaScript RSA (forge / js-crypto)*: Rejected due to high CPU overhead, lack of forward secrecy, and vulnerability to side-channel attacks in JS runtimes.
- *OpenPGP.js*: Rejected because of massive bundle size, complex keyring management, and mismatch with lightweight real-time chat bubbles.

---

## 2. Google Identity & OAuth2 Authentication Architecture

### Decision: Spring Security OAuth2 Resource Server + Google ID Token Verification + Stateless JWT
- **Client Flow**: Google Identity Services (`@react-oauth/google` or Google Sign-In button) obtains verified Google ID Token (JWT).
- **Backend Flow**: Frontend exchanges Google ID Token with backend `/api/v1/auth/google`. Backend verifies signature and claims against Google's public JWKS endpoints (`https://www.googleapis.com/oauth2/v3/certs`).
- **Session Issuance**: Backend creates/updates the `UserProfile` document in MongoDB and issues a signed application JWT (Access Token + Refresh Token in HttpOnly cookie or secure header).
- **Identity Key Registration**: Upon first login, client generates its ECDH public key bundle and registers it with backend `/api/v1/users/keys`.

### Rationale:
- Separation of concerns: Google manages password/2FA identity validation; backend manages application session tokens and public key directory.
- Exact Gmail search query: `db.users.findOne({ email: queryEmail.toLowerCase() })` without leaking directory listings.

### Alternatives Considered:
- *Traditional Session Cookies (JSESSIONID)*: Rejected due to WebSocket distributed scaling limitations and stateful server memory overhead.
- *Server-side OAuth2 redirect flow*: Rejected because a single-page React app with direct Google SDK provides a much smoother, pop-up based UX without full-page reloads.

---

## 3. Real-Time Transport & WebSocket Architecture

### Decision: Spring WebSocket with STOMP over SockJS
- **Protocol**: STOMP (Simple Text Oriented Messaging Protocol) with SockJS fallback for network resilience.
- **Broker**: Spring built-in Simple Broker for development/single-instance, with easy migration path to RabbitMQ / Redis PubSub if clustered.
- **Channels / Destinations**:
  - `/topic/conversation/{conversationId}`: Broadcasts real-time encrypted message payloads, delivery receipts, and unsend events to active participants.
  - `/user/queue/notifications`: Delivers asynchronous 4-layer handshake invitations, consent requests, and security alerts.
  - `/topic/conversation/{conversationId}/typing`: Broadcasts transient typing indicator events.
- **Heartbeat & Reconnect**: Client configures 10-second STOMP heartbeat and exponential backoff reconnection logic (1s -> 2s -> 4s -> max 10s).

### Rationale:
- STOMP provides standardized frame headers (`receipt`, `destination`, `subscription-id`) and native Spring Security integration via `ChannelInterceptor`.
- Fulfills Constitution Principle V (Real-Time First Communication).

---

## 4. Backend Persistence & Zero-Knowledge Architecture

### Decision: Spring Boot (Java 17/21) + Spring Data MongoDB + GridFS / S3 Pointer for Media
- **Database**: MongoDB 7.0+ for flexible JSON document storage (User profiles, Public Key Bundles, Conversations, Handshake States, and Encrypted Messages).
- **Zero-Knowledge Enforcement**:
  - The `EncryptedMessage` document stores ONLY `ciphertext` (Base64 string), `iv` (Base64), `senderId`, `recipientId`, `messageType`, and timestamps.
  - Encrypted image attachments (≤ 5MB) are uploaded as encrypted binary blobs to `/api/v1/media/upload`, storing only encrypted ciphertext on disk/database; decryption key is part of the E2EE message payload shared only between the 2 clients.
  - Server stack trace and logs are strictly scrubbed with MDC trace correlation (Constitution Principle IV & VII).

---

## 5. Frontend Architecture & Design System

### Decision: React 18/19 + Vite + Tailwind CSS + Lucide React
- **Design Inspiration**: Facebook Messenger (modern clean layout, rich vibrant accent palette `#0084FF` / `#00C6FF`, glassmorphism translucent panels, smooth spring micro-animations, dark/light theme).
- **State Management**: Zustand or lightweight React Context with custom hooks (`useAuth`, `useCrypto`, `useChat`, `useWebSocket`).
- **IndexedDB Wrapper**: `idb` (lightweight promise-based IndexedDB wrapper) for storing local private keys and offline message store.
- **Testing**: Vitest + React Testing Library + MSW (Mock Service Worker) for unit/interaction testing; Playwright for E2E user journeys.

---

## 6. 4-Layer Handshake State Machine Workflow

```text
[State: INITIATING]
       │
       ▼ (Layer 1: Google Accounts Validated)
[State: PENDING_ACCEPTANCE (Layer 2)]
       │
       ├─► [Rejected by Recipient] ──► [State: DISMISSED]
       │
       ▼ (Layer 2 Accepted)
[State: HANDSHAKE_KEY_EXCHANGE (Layer 3)]
       │
       ▼ (Pre-Keys Exchanged, Shared Secret & 6-Digit Code Computed)
[State: PENDING_CONFIRMATION (Layer 4)]
       │
       ▼ (Recipient & Initiator Confirm Visual 6-Digit Code Matches)
[State: VERIFIED_ACTIVE] ──► [Messaging Enabled]
```
