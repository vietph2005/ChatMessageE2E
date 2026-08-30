# Implementation Plan: Re-Handshake & Unblock Contact

**Branch**: `002-rehandshake-and-unblock` | **Date**: 2026-08-30 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/002-rehandshake-and-unblock/spec.md`

## Summary

This feature adds end-to-end support for **Re-Handshake (Key Mismatch Detection & Session Re-Keying)** and **Unblock Contact**.
- **Re-Handshake**: Automatically detects when a client's local ECDH identity key pair differs from the public key registered in the conversation's active handshake record (e.g. following an incognito session restart, app reset, or device migration). Displays a warning banner, initiates a fresh 4-layer cryptographic handshake via `POST /api/v1/conversations/{id}/handshake/re-initiate`, broadcasts real-time `KEY_CHANGED` STOMP notifications, computes a new 6-digit visual Safety Code, and derives a new synchronized AES-GCM-256 session key.
- **Unblock Contact**: Allows users to unblock previously blocked contacts via `POST /api/v1/users/unblock`, restoring conversation state (`VERIFIED_ACTIVE`) and re-enabling messaging workflows in real time.

---

## Technical Context

**Language/Version**: Java 21 (Backend), TypeScript 5.x / React 18 (Frontend)

**Primary Dependencies**: Spring Boot 3.2.x (Web, Security, WebSocket/STOMP, Data MongoDB), SubtleCrypto (Web Crypto API), `@stomp/stompjs` + `sockjs-client`, `idb` (IndexedDB client storage), Tailwind CSS, Lucide React

**Storage**: MongoDB (Collections: `users`, `conversations`, `handshake_verifications`), Client-Side IndexedDB (`identity_keys`, `conversation_sessions`, `local_messages`)

**Testing**: JUnit 5, Mockito, Spring Boot Test, Vitest / React Testing Library, Playwright (E2E)

**Target Platform**: Modern Evergreen Browsers (Chrome, Edge, Firefox, Safari with Web Crypto API), Linux/Windows Containerized Backend

**Project Type**: Web Application (Spring Boot REST + WebSocket Backend + Vite React Frontend)

**Performance Goals**: Re-handshake initiation < 200ms, STOMP event dispatch < 50ms, Unblock operation < 100ms

**Constraints**: Strict Zero-Knowledge Privacy — private keys NEVER leave the client; server NEVER has access to plaintext message content.

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment | Status |
| :--- | :--- | :--- |
| **I. Layered Architecture** | Strictly respects Presentation (Controllers/WebSocket) → Application (Services) → Domain (Models/Repo) ← Infrastructure (MongoDB/Security). | ✅ PASSED |
| **II. Clean Code & Standards** | Clear naming, Single Responsibility methods, typed DTOs and contracts. | ✅ PASSED |
| **III. Privacy & E2EE by Default** | Private keys generated and kept strictly in browser memory/IndexedDB. Re-Handshake ensures no silent decryption failures or plaintexts on backend. | ✅ PASSED |
| **IV. Honest APIs & Structured Errors** | Clear REST endpoints (`/handshake/re-initiate`, `/users/unblock`) and structured domain exceptions. MDC traceId logging. | ✅ PASSED |
| **V. Real-Time First Communication** | STOMP event `KEY_CHANGED` pushed over `/user/queue/notifications` with auto-reconnection handling. | ✅ PASSED |
| **VI. Comprehensive Automated Testing** | Unit tests for services and cryptographic hooks, integration tests for REST/WebSocket pipelines, target ≥ 80% coverage. | ✅ PASSED |
| **VII. Security & Integrity** | JWT token validation on WebSocket CONNECT, authenticated endpoints, no secrets in repo. | ✅ PASSED |
| **VIII. Simplicity Over Complexity** | Reuses existing 4-Layer Handshake infrastructure rather than creating parallel handshake systems. | ✅ PASSED |

---

## Project Structure

### Documentation (this feature)

```text
specs/002-rehandshake-and-unblock/
├── plan.md              # This file
├── research.md          # Architecture & technical decisions
├── data-model.md        # Entities & state transitions
├── contracts/
│   ├── rest-api.yaml    # OpenAPI 3.0 specification for Re-Handshake & Unblock
│   └── websocket-stomp.md # STOMP event payload contracts
├── quickstart.md        # End-to-end validation scenarios
├── checklists/
│   └── requirements.md  # Specification quality checklist
└── spec.md              # Feature specification
```

### Source Code Impact

```text
backend (src/main/java/org/example/chat/):
├── application/service/
│   ├── HandshakeService.java        # Add reInitiateHandshake method
│   └── UserService.java             # Add unblockUser method
├── presentation/controller/
│   ├── ConversationController.java  # Expose /handshake/re-initiate endpoint
│   └── UserController.java          # Expose /users/unblock endpoint
└── presentation/websocket/
    └── HandshakeNotificationHandler.java # Add notifyKeyChanged method

frontend (frontend/src/):
├── services/
│   ├── apiClient.ts                 # Add reInitiateHandshake, unblockUser APIs
│   └── stompClient.ts               # Support KEY_CHANGED event handling
├── hooks/
│   └── useChat.ts                   # Key mismatch detection, re-handshake trigger, unblock action
└── components/
    ├── chat/
    │   ├── ChatHeader.tsx           # Add Unblock and Re-verify actions
    │   └── SafetyNumberAlertBanner.tsx # Integrate key change warning banner
    └── handshake/
        └── HandshakeModal.tsx       # Support re-handshake flow
```

---

## Complexity Tracking

*No constitutional violations identified. Standard layered architecture and existing cryptographic engine reused.*
