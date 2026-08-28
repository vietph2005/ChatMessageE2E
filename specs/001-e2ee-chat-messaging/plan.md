# Implementation Plan: 1-1 End-to-End Encrypted Chat with 4-Layer Handshake Verification

**Branch**: `001-e2ee-chat-messaging` | **Date**: 2026-08-28 | **Spec**: [`specs/001-e2ee-chat-messaging/spec.md`](spec.md)

**Input**: Feature specification from `specs/001-e2ee-chat-messaging/spec.md`

---

## Summary

This plan outlines the technical design and phased implementation for building a 1-1 End-to-End Encrypted (E2EE) real-time chat application with a mandatory 4-layer asynchronous handshake verification process, Google OAuth2 (Gmail) authentication, and a modern Messenger-inspired user interface.

- **Backend**: Spring Boot (Java 17/21) following strict 4-tier Layered Architecture, Spring Data MongoDB for zero-knowledge ciphertext persistence, Spring Security with Google OAuth2/JWT verification, and Spring WebSocket STOMP for sub-500ms real-time event broadcasting.
- **Frontend**: React (TypeScript + Vite) styled with Tailwind CSS, utilizing the native Web Crypto API (`window.crypto.subtle`) for client-side ECDH P-256 key exchange, AES-256-GCM encryption for text and images (≤ 5MB), and IndexedDB for local-only key isolation.

---

## Technical Context

- **Language/Version**: Java 17/21 (Backend) & TypeScript 5+ with React 18/19 (Frontend)
- **Primary Dependencies**:
  - *Backend*: `spring-boot-starter-web`, `spring-boot-starter-websocket`, `spring-boot-starter-data-mongodb`, `spring-boot-starter-security`, `spring-boot-starter-oauth2-resource-server`, `jjwt`, `awaitility`, `testcontainers`.
  - *Frontend*: `react`, `react-dom`, `@react-oauth/google`, `@stomp/stompjs`, `sockjs-client`, `idb`, `lucide-react`, `tailwindcss`, `clsx`, `tailwind-merge`.
- **Storage**: MongoDB 7.0+ (Backend persistence of users, public keys, conversation states, ciphertexts) & Browser IndexedDB (Client private keys, session ratchets, local decrypted store).
- **Testing**: JUnit 5, Mockito, Testcontainers, Awaitility, JaCoCo (Backend); Vitest, React Testing Library, Playwright (Frontend).
- **Target Platform**: Modern evergreen web browsers (Desktop & Mobile) & Linux/Containerized JVM server runtime.
- **Project Type**: Full-stack Web Application (Java Spring Backend + React Single-Page Application).
- **Performance Goals**: Google OAuth login < 3s, real-time message delivery < 500ms, 4-layer handshake < 15s (synchronous) or instant resume (asynchronous).
- **Constraints**: 100% Zero-Knowledge invariant (zero plaintext or private keys accessible by server), Local-Only Identity (no private key backups on server), image payload ≤ 5MB.
- **Scale/Scope**: 1-1 real-time messaging, asynchronous handshake state machine, 5 major user journeys.

---

## Constitution Check

*GATE: All principles from [Constitution](file:///c:/Users/phamh/IdeaProjects/TestSpec/ChatMessage/ChatMessageE2E/.specify/memory/constitution.md) verified.*

| Principle | Compliance Assessment | Gate Status |
|---|---|:---:|
| **I. Layered Architecture & Separation of Concerns** | Dependencies strictly flow inward: Presentation (`controllers`, `stomp`) → Application (`services`, `usecases`) → Domain (`entities`, `events`) ← Infrastructure (`mongodb`, `security`, `crypto`). Frontend separates API, state, crypto, and UI components. | **PASS** |
| **II. Clean Code & World-Class Standards** | Single Responsibility Principle enforced across services; intention-revealing naming; zero magic numbers. | **PASS** |
| **III. Privacy & End-to-End Encryption by Default** | Web Crypto API performs all encryption/decryption at the client edge. Zero plaintext reaches server memory or database. | **PASS** |
| **IV. Honest APIs, Structured Errors & Clear Logging** | Machine-readable error schema (`ApiError`), structured MDC logging with `traceId`/`correlationId`. Plaintext/keys strictly excluded from logs. | **PASS** |
| **V. Real-Time First Communication** | STOMP over SockJS with heartbeats, delivery receipts, and exponential back-off reconnection. | **PASS** |
| **VI. Comprehensive Automated Testing & Quality Gates** | Test pyramid: Unit tests (mocked dependencies), Integration tests (Testcontainers MongoDB), Cryptographic known-vector tests, and E2E Playwright tests. Minimum 80% coverage threshold (90% domain). | **PASS** |
| **VII. Security & Configuration Integrity** | Spring Security OAuth2 validation, JWT authentication, configuration via `application.properties` referencing `${VAR_NAME}` and `.gitignore`d `application-local.properties`. | **PASS** |
| **VIII. Simplicity Over Complexity** | Lightweight native Web Crypto API chosen over heavyweight third-party crypto bundles; Spring STOMP SimpleBroker chosen for clean maintainability. | **PASS** |

---

## Project Structure

### Documentation (this feature)

```text
specs/001-e2ee-chat-messaging/
├── spec.md              # Feature specification
├── plan.md              # This implementation plan
├── research.md          # Technical research & decisions (Phase 0)
├── data-model.md        # Database schema & client IndexedDB model (Phase 1)
├── quickstart.md        # Developer setup & validation guide (Phase 1)
├── contracts/           # API and WebSocket contracts (Phase 1)
│   ├── rest-api.yaml    # OpenAPI 3.0 REST schema
│   └── websocket-stomp.md # WebSocket STOMP messaging protocol
└── checklists/
    └── requirements.md  # Requirements quality checklist
```

### Source Code Architecture

```text
c:/Users/phamh/IdeaProjects/TestSpec/ChatMessage/ChatMessageE2E/
├── pom.xml                               # Maven root configuration
├── src/
│   ├── main/
│   │   ├── java/org/example/chat/
│   │   │   ├── presentation/             # Presentation Layer
│   │   │   │   ├── controller/           # REST Controllers (Auth, Users, Handshake, Media)
│   │   │   │   ├── websocket/            # STOMP WebSocket Message Controllers
│   │   │   │   ├── dto/                  # Request/Response DTOs
│   │   │   │   └── exception/            # Global Exception Handler & ApiError
│   │   │   ├── application/              # Application Layer
│   │   │   │   ├── service/              # User, Handshake, Message, Media Services
│   │   │   │   └── usecase/              # Specific Orchestrated Workflows
│   │   │   ├── domain/                   # Domain Layer
│   │   │   │   ├── model/                # User, Conversation, HandshakeVerification, Message
│   │   │   │   ├── repository/           # Domain Repository Interfaces (Ports)
│   │   │   │   └── event/                # Domain Events (HandshakeCompletedEvent, etc.)
│   │   │   └── infrastructure/           # Infrastructure Layer
│   │   │       ├── persistence/mongodb/  # Spring Data Mongo Repositories & Documents
│   │   │       ├── security/             # Spring Security, Google Token Verifier, JWT Filter
│   │   │       └── websocket/            # WebSocket & STOMP Broker Configuration
│   │   └── resources/
│   │       ├── application.properties    # Base config referencing environment variables
│   │       └── application-local.properties.example # Local development template
│   └── test/
│       └── java/org/example/chat/
│           ├── unit/                     # Domain & Service Unit Tests
│           ├── integration/              # Testcontainers MongoDB & Security Filter Tests
│           └── contract/                 # REST & STOMP Contract Verification Tests
└── frontend/                             # React + Vite + Tailwind SPA
    ├── package.json
    ├── vite.config.ts
    ├── tailwind.config.js
    ├── index.html
    └── src/
        ├── crypto/                       # Web Crypto Engine (ECDH, AES-GCM, HKDF, Fingerprint)
        ├── db/                           # IndexedDB Local Storage Manager
        ├── services/                     # REST API Client & STOMP WebSocket Client
        ├── hooks/                        # Custom React Hooks (useAuth, useChat, useCrypto)
        ├── components/                   # Messenger UI Components
        │   ├── layout/                   # Header, App Shell, Navigation
        │   ├── sidebar/                  # Conversation List, Exact Gmail Search, Badges
        │   ├── chat/                     # Message Stream, Bubbles, Input Bar, Typing Indicator
        │   ├── handshake/                # 4-Layer Handshake Modal & 6-Digit Code Dialog
        │   └── security/                 # Safety Number Details Drawer & QR Code
        └── App.tsx
```

---

## Complexity Tracking

*No unjustified complexity or architectural violations detected.*

| Decision | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Native Web Crypto API (`SubtleCrypto`) | Hardware-accelerated, side-channel safe client-side encryption. | External pure JS crypto libraries add large bundle footprint and risk timing attacks. |
| Asynchronous Pre-Key Handshake | Enables initiating secure chats even when the recipient is offline. | Synchronous-only handshake fails whenever users are in different timezones or not simultaneously online. |
