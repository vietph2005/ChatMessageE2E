# Quickstart Validation Guide: Re-Handshake & Unblock Contact

**Feature**: `002-rehandshake-and-unblock`
**Date**: 2026-08-30

## 1. Prerequisites

- Backend Spring Boot server running on port `8080` (or proxy via Vite on `5173`).
- MongoDB instance running with test or live dataset.
- Frontend React application running (`npm run dev`).
- Two test Google accounts (or test tokens) for User A and User B.

---

## 2. Verification Scenario 1: Re-Handshake Flow

### Steps:
1. **Initial Verified State**:
   - Log in User A (Chrome) and User B (Edge/Incognito).
   - Establish and complete a 4-layer handshake. Verify that User A and User B can send/receive encrypted messages.
2. **Simulate Key Loss / New Session**:
   - Close User B's incognito window.
   - Open a fresh incognito window and log in as User B (a new `IndexedDB` key pair is generated).
3. **Open Existing Conversation**:
   - User B clicks the conversation with User A.
   - **Expected**: Banner *"Your safety number with Alice has changed"* appears with a prominent *"Re-verify"* button. Chat input is disabled.
4. **Trigger Re-Handshake**:
   - User B clicks *"Re-verify"*.
   - **Expected**:
     - User B enters the Handshake Modal.
     - User A receives an instant real-time notification (`KEY_CHANGED`) and prompt to re-verify.
5. **Complete 4-Layer Re-Handshake**:
   - User A and User B both view and confirm the new 6-digit visual Safety Code.
   - **Expected**:
     - Status updates to `VERIFIED_ACTIVE`.
     - Input bar unlocks on both clients.
     - User B sends "Hello Alice from new device" -> User A decrypts and displays it successfully.

---

## 3. Verification Scenario 2: Unblock Contact Flow

### Steps:
1. **Block Contact**:
   - User A opens conversation with User B and clicks *"Block Contact"* in the header or security drawer.
   - **Expected**: Conversation status changes to `BLOCKED`. Input is disabled, showing "You have blocked this contact".
2. **Unblock Contact**:
   - User A clicks *"Unblock Contact"* button.
   - **Expected**:
     - Endpoint `POST /api/v1/users/unblock` is called.
     - Block is removed from User A's profile.
     - Conversation immediately restores to `VERIFIED_ACTIVE` without page reload.
     - Input bar is re-enabled, allowing messaging to resume.
