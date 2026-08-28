# Quickstart & Developer Validation Guide

**Feature Branch**: `001-e2ee-chat-messaging`  
**Date**: 2026-08-28  
**Spec Reference**: [`specs/001-e2ee-chat-messaging/spec.md`](spec.md) | [`data-model.md`](data-model.md) | [`contracts/rest-api.yaml`](contracts/rest-api.yaml)

---

## 1. Prerequisites & Environment Setup

### 1.1 Requirements
- **Java**: JDK 17 or JDK 21
- **Node.js**: Node.js 18+ and npm / yarn / pnpm
- **MongoDB**: MongoDB 7.0+ (running locally on port 27017 or via Docker `docker run -d -p 27017:27017 --name chat-mongo mongo:7.0`)
- **Google OAuth Client ID**: Configured in Google Cloud Console with authorized origins `http://localhost:5173`.

### 1.2 Configuration (`application.properties` & `application-local.properties`)
Create `application-local.properties` (ignored by git per Constitution Principle VII):
```properties
spring.data.mongodb.uri=mongodb://localhost:27017/chat_message_e2e
google.oauth2.client-id=YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com
jwt.secret=YOUR_SECURE_DEV_JWT_SECRET_STRING_AT_LEAST_256_BITS
jwt.expiration-ms=86400000
```

---

## 2. Running Locally

### 2.1 Start Backend (Spring Boot)
```bash
mvn clean spring-boot:run
```
Backend starts on `http://localhost:8080`.

### 2.2 Start Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev
```
Frontend starts on `http://localhost:5173`.

---

## 3. Step-by-Step Feature Validation Flows

### Scenario 1: Google Sign-In & Cryptographic Key Initialization
1. Open Browser A (e.g. Chrome) to `http://localhost:5173`.
2. Click **"Sign in with Google"** and complete OAuth flow as `alice@gmail.com`.
3. Open DevTools > Application > IndexedDB > `ChatMessageE2E_ClientDB` > `identity_keys`.
4. **Assert**:
   - User profile loaded with avatar, name, and email.
   - Private key and Public key are generated in IndexedDB.
   - Public key bundle is saved in MongoDB `user_public_keys` collection.

### Scenario 2: Asynchronous 4-Layer Handshake Verification
1. In Browser A (`alice@gmail.com`), type `bob@gmail.com` in the exact Gmail search bar and click **"Start Secure Chat"**.
2. **Layer 1 Check**: System validates `bob@gmail.com` exists.
3. Conversation is created in `PENDING_ACCEPTANCE`.
4. Open Browser B (e.g. Incognito or Firefox) and sign in as `bob@gmail.com`.
5. **Layer 2 Notification**: Bob receives notification in the sidebar: *"Alice wants to connect"*.
6. Bob clicks **"Accept Invitation"**.
7. **Layer 3**: Clients exchange Pre-Keys; both calculate the identical 6-digit visual safety code (e.g. `842910`).
8. **Layer 4**: Bob and Alice are shown the matching 6-digit code. Bob clicks **"Confirm Code Matches"**.
9. **Assert**: Conversation status transitions to `VERIFIED_ACTIVE` and the chat input box turns active.

### Scenario 3: Real-Time E2EE Messaging & Zero-Knowledge Verification
1. In Browser A, type `"Hello Bob, this message is encrypted!"` and press Enter.
2. In Browser B, message arrives instantly (< 500ms) and renders in plain text.
3. Open MongoDB Compass or `mongosh`:
   ```javascript
   db.encrypted_messages.find().pretty()
   ```
4. **Zero-Knowledge Assert**:
   - `ciphertext`: Contains Base64 encrypted string (e.g. `U2FsdGVkX1+...`).
   - The string `"Hello Bob"` **never** appears anywhere in the MongoDB database or Spring Boot log outputs.

### Scenario 4: Encrypted Image Attachment & Unsend
1. In Browser A, click the image icon, attach an image (`photo.png` ≤ 5MB), and send.
2. In Browser B, image decrypts and previews cleanly inside the chat bubble.
3. In Browser A, hover over the message bubble, select **"Unsend for Everyone"**.
4. **Assert**: Both Browser A and Browser B immediately replace the bubble with *"This message was unsent"*.

---

## 4. Automated Testing Commands

```bash
# Run Backend Unit & Integration Tests (including Testcontainers & Crypto vector tests)
mvn clean test

# Run JaCoCo Test Coverage Report (Assert >= 80% overall, >= 90% domain)
mvn test jacoco:report

# Run Frontend Component & E2EE Crypto Tests
cd frontend && npm run test

# Run Playwright E2E User Journey Suite
cd frontend && npx playwright test
```
