# Security & E2EE Protocol Quality Checklist: Re-Handshake & Unblock Contact

**Purpose**: Validate the completeness, clarity, cryptographic rigor, and error-handling quality of requirements for Re-Handshake and Unblock Contact.
**Created**: 2026-08-30
**Feature**: [spec.md](../spec.md) | [plan.md](../plan.md)

**Review Ownership**: This checklist is a reviewer-owned requirements-quality review artifact. Mark an item `[x]` only when the reviewer determines the requirements-quality criterion is satisfied.
**Marker Semantics**: `[x]` means the criterion has been reviewed and satisfied for requirements quality. It does not mean implementation work is complete.

## 1. Cryptographic Protocol & Key Lifecycle

- [ ] CHK001 Are the conditions that constitute a key mismatch unambiguously specified with concrete identity key parameters? [Clarity, Spec §FR-001]
- [ ] CHK002 Are the exact state transitions for `HandshakeVerification` during a re-handshake explicitly defined? [Completeness, Spec §FR-003, Plan §2.1]
- [ ] CHK003 Is the derivation formula for the new AES-GCM session key (`HKDF(ECDH(KeyA, KeyB))`) consistent with the primary E2EE protocol specification? [Consistency, Plan §Technical Context]
- [ ] CHK004 Is the zero-knowledge invariant (server never receives or stores private keys or decrypted plaintext) explicitly preserved during re-handshake? [Security, Spec §SC-004]
- [ ] CHK005 Is the versioning / incrementing mechanism for `HandshakeVerification` defined to invalidate stale sessions? [Coverage, Data-Model §1.2]

## 2. Real-Time Transport & WebSocket Notifications

- [ ] CHK006 Are the STOMP payload schemas and event types (`KEY_CHANGED`, `HANDSHAKE_ACCEPTED`, `SAFETY_CODE_CONFIRMED`) completely defined with field types? [Completeness, Contracts §websocket-stomp.md]
- [ ] CHK007 Are the delivery semantics and fallback behaviors specified when the peer user is offline during re-handshake initiation? [Edge Cases, Spec §Edge Cases]
- [ ] CHK008 Are message transmission suppression rules while re-handshake is in progress explicitly testable? [Measurability, Spec §FR-006]

## 3. User Experience & Visual Verification

- [ ] CHK009 Are visual banner requirements and copy for the "Security Key Changed" alert clearly documented? [Clarity, Spec §FR-002, Clarifications]
- [ ] CHK010 Is the 6-digit visual Safety Code calculation and display format specified for cross-party manual verification? [Completeness, Spec §FR-005]
- [ ] CHK011 Are the requirements for historical message separation (timeline divider on new session) testable and unambiguous? [Coverage, Spec §FR-010]
- [ ] CHK012 Are input disabling/enabling trigger conditions consistently documented across all conversation states? [Consistency, Spec §FR-006, Spec §FR-008]

## 4. Unblock Functionality & Relationship Lifecycle

- [ ] CHK013 Is the unilateral vs. bilateral unblock state resolution behavior clearly specified? [Completeness, Spec §Edge Cases, Clarifications]
- [ ] CHK014 Are the REST API request and response schemas for `/api/v1/users/unblock` defined in OpenAPI format? [Traceability, Contracts §rest-api.yaml]
- [ ] CHK015 Are the conversation restoration criteria (resuming `VERIFIED_ACTIVE` vs. triggering re-handshake) testable and unambiguous? [Clarity, Spec §FR-008]
- [ ] CHK016 Are persistence and audit timestamp requirements for block/unblock actions documented in domain entities? [Completeness, Spec §FR-009, Data-Model §1.3]

## 5. Edge Cases & Concurrency

- [ ] CHK017 Is the tie-breaking mechanism for concurrent re-handshake initiations by both participants specified? [Edge Cases, Spec §Edge Cases]
- [ ] CHK018 Are error handling and domain exception responses defined for unauthorized or mismatched handshake actions? [Error Handling, Contracts §rest-api.yaml]
- [ ] CHK019 Are latency and response time thresholds measurable and verifiable? [Measurability, Spec §SC-001, Spec §SC-003]

## Notes

- Mark items `[x]` only after review confirms the requirement-quality criterion is satisfied
- Leave items unchecked when they still require clarification, correction, or reviewer evaluation
- `/speckit-implement` reads checklist checkbox state as a gate and must not modify markers
- Items are numbered sequentially (CHK001 - CHK019) for unambiguous review tracking
