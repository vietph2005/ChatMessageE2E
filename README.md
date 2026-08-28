# ChatMessageE2E — 1-1 End-to-End Encrypted Real-Time Chat System

[![Java CI](https://img.shields.io/badge/Java-17%2B-orange.svg)](https://www.oracle.com/java/)
[![Spring Boot](https://img.shields.io/badge/Spring%20Boot-3.3.3-brightgreen.svg)](https://spring.io/projects/spring-boot)
[![Vite + React](https://img.shields.io/badge/React-18.3-blue.svg)](https://reactjs.org/)
[![Web Crypto API](https://img.shields.io/badge/Web%20Crypto-ECDH%20%2F%20AES--256--GCM-blueviolet.svg)](https://developer.mozilla.org/en-US/docs/Web/API/Web_Crypto_API)
[![Security](https://img.shields.io/badge/Zero--Knowledge-Strict-success.svg)](#zero-knowledge-invariants)

ChatMessageE2E is a state-of-the-art, 1-1 real-time messaging web application featuring a **4-Layer Asynchronous Handshake Verification** model and hardware-accelerated **Web Crypto API (SubtleCrypto)** end-to-end encryption. The user experience is heavily inspired by Facebook Messenger, featuring a dark-themed glassmorphism interface, real-time typing indicators, read receipts, message recall ("Unsend for Everyone" / "Delete for Me"), and interactive 6-digit Safety Code & QR verification.

---

## 🔒 4-Layer Handshake Architecture

Before two users can exchange messages, the channel MUST progress through 4 independent security layers:

```
[User A]                                                                       [User B]
   │                                                                              │
   ├────────── Layer 1: Google Account Verification (OAuth2 / OpenID) ────────────┤
   │           • Authenticates identity via Google ID Token                       │
   │           • Searchable ONLY via exact Gmail address (privacy protection)     │
   │                                                                              │
   ├────────── Layer 2: Mutual Connection Consent (Asynchronous) ─────────────────┤
   │           • User A sends chat invitation (User B can be offline)             │
   │           • User B reviews & accepts/declines invitation upon next login     │
   │                                                                              │
   ├────────── Layer 3: Cryptographic Pre-Key Exchange ──────────────────────────┤
   │           • SubtleCrypto ECDH (P-256) Identity & Pre-Keys exchanged          │
   │           • HKDF (SHA-256) derives 256-bit symmetric AES-GCM session key     │
   │                                                                              │
   └────────── Layer 4: Visual Safety Code & QR Confirmation ─────────────────────┘
               • Deterministic 6-digit visual decimal code & SHA-256 fingerprint
               • Confirm code match on both screens / scan QR to unlock chat
```

---

## 🛡️ Zero-Knowledge Invariants

1. **Private Key Isolation**: Private keys are generated locally inside the browser's hardware-accelerated `window.crypto.subtle` engine and persisted **strictly inside client IndexedDB**. Private keys NEVER leave the device and are never sent to the backend.
2. **Ciphertext-Only Persistence**: The MongoDB database stores **only Base64 ciphertexts** and random 96-bit Initialization Vectors (IVs). Plaintext message contents and decrypted media are never stored or logged on the server.
3. **MDC Correlation Logging**: Server logs use structured MDC trace IDs (`traceId`, `requestId`) and strictly sanitize payload contents to prevent sensitive data leakage.

---

## 🚀 Quick Start Guide

### Prerequisites
- **JDK 17+**
- **Maven 3.8+**
- **Node.js 18+ & npm**
- **MongoDB 6.0+** (running on `localhost:27017` or configured via `MONGODB_URI`)

### 1. Start the Spring Boot Backend

```bash
# Clone the repository and navigate to root
mvn clean test
mvn spring-boot:run
```
Backend starts on `http://localhost:8080` (REST API and WebSocket `/ws`).

### 2. Start the Vite Frontend

```bash
cd frontend
npm install
npm run dev
```
Frontend development server starts on `http://localhost:5173`.

### 3. Demo / Development Testing Flow

1. Open `http://localhost:5173` in Browser Window 1 -> Click **"Sign in as Alice (alice@gmail.com)"**.
2. Open `http://localhost:5173` in Browser Window 2 (Incognito) -> Click **"Sign in as Bob (bob@gmail.com)"**.
3. In Alice's window, type `bob@gmail.com` in the exact Gmail search bar and click **"Connect"**.
4. In Bob's window, view the incoming connection request -> click **"Verify Now"** -> **"Accept"** (Layer 2 & 3).
5. In both windows, verify the matching **6-digit Safety Code** (e.g. `842 910`) and click **"Confirm Match"** (Layer 4).
6. Send encrypted text messages, emojis, and encrypted images (≤ 5MB).
7. Test **Unsend for Everyone** by hovering over any sent bubble -> three dots -> **"Unsend for Everyone"**.

---

## 🧪 Testing & Verification

### Run Backend Unit & Integration Tests (JaCoCo Coverage ≥ 80%)
```bash
mvn test
```

### Run Frontend Web Crypto & Component Tests
```bash
cd frontend
npm run test
```

### Build Frontend Production Bundle
```bash
cd frontend
npm run build
```

---

## 📂 Project Structure

```
ChatMessageE2E/
├── pom.xml                               # Spring Boot 3.x configuration & JaCoCo plugin
├── src/main/java/org/example/chat/
│   ├── presentation/                     # Presentation Layer (Controllers, STOMP, Exception Handlers)
│   │   ├── controller/                   # AuthController, ConversationController, UserKeyController, MediaController
│   │   ├── websocket/                    # ChatStompController, HandshakeNotificationHandler
│   │   ├── dto/                          # Machine-readable DTO records
│   │   └── exception/                    # GlobalExceptionHandler & ApiError
│   ├── application/service/              # Application Layer (UserService, HandshakeService, MessageService, SafetyCodeService)
│   ├── domain/                           # Domain Layer (Enterprise business models & repository ports)
│   │   ├── model/                        # UserProfile, UserPublicKeyBundle, Conversation, HandshakeVerification, EncryptedMessage
│   │   └── repository/                   # Domain repository interfaces
│   └── infrastructure/                   # Infrastructure Layer (MongoDB Adapters, Security, WebSocket broker)
│       ├── persistence/mongodb/          # MongoConfig, documents & repository implementations
│       ├── security/                     # SecurityConfig, JwtTokenProvider, GoogleTokenVerifier
│       ├── websocket/                    # WebSocketConfig STOMP configuration
│       └── logging/                      # MdcLoggingFilter
└── frontend/                             # React 18 + Vite + TypeScript Frontend
    ├── src/
    │   ├── crypto/                       # Web Crypto API engine (ECDH, HKDF, AES-GCM, Fingerprints)
    │   ├── db/                           # IndexedDB client database manager
    │   ├── services/                     # Typed REST API client & WebSocket STOMP client
    │   ├── hooks/                        # useAuth, useChat
    │   └── components/                   # UI components (auth, sidebar, chat, handshake, security)
```
