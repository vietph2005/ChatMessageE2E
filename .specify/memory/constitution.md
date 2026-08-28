<!--
Sync Impact Report:
- Version change: Initial Template -> 1.0.0
- List of modified principles:
  - Added Principle I: Layered Architecture & Separation of Concerns (NON-NEGOTIABLE)
  - Added Principle II: Clean Code & World-Class Standards (NON-NEGOTIABLE)
  - Added Principle III: Privacy & End-to-End Encryption by Default (NON-NEGOTIABLE)
  - Added Principle IV: Honest APIs, Structured Error Handling & Clear Debug Logging
  - Added Principle V: Real-Time First Communication
  - Added Principle VI: Comprehensive Automated Testing & Quality Gates (NON-NEGOTIABLE)
  - Added Principle VII: Security & Configuration Integrity (NON-NEGOTIABLE)
  - Added Principle VIII: Simplicity Over Complexity
- Added sections: Governance
- Removed sections: N/A
- Follow-up TODOs: None
-->

# ChatMessageE2E Constitution

## Core Principles

### I. Layered Architecture & Separation of Concerns (NON-NEGOTIABLE)
The system MUST strictly enforce a Layered Architecture to guarantee maintainability and separation of concerns:

- **Backend (Java Spring Framework)**:
  - **Presentation Layer**: REST Controllers, WebSocket/STOMP handlers, and DTOs.
  - **Application Layer**: Use cases, service orchestration, transaction boundaries.
  - **Domain Layer**: Business logic, core entities, domain events, value objects.
  - **Infrastructure Layer**: Database persistence (Spring Data MongoDB), external integrations, crypto/encryption providers.
  - **Dependency Rule**: Dependencies MUST strictly flow inward (Presentation → Application → Domain ← Infrastructure). Domain logic MUST NOT depend on presentation or infrastructure frameworks.
- **Frontend (React + Tailwind CSS)**:
  - Strict separation into API communication, state management, feature UI components, and shared Tailwind-styled design system elements.

### II. Clean Code & World-Class Standards (NON-NEGOTIABLE)
- Code is written for human clarity first. All code MUST adhere to clean code standards and SOLID principles.
- Naming MUST be intention-revealing. Methods/functions MUST have a Single Responsibility (SRP).
- Complexity MUST be justified: if a simpler design satisfies the requirements, it MUST be chosen.

### III. Privacy & End-to-End Encryption by Default (NON-NEGOTIABLE)
- User message content is strictly private and MUST be protected via end-to-end encryption.
- The backend server MUST NEVER have access to plaintext message content.
- Encryption is a foundational requirement from day one, not a deferred feature.

### IV. Honest APIs, Structured Error Handling & Clear Debug Logging
- **API Predictability**: Every exposed endpoint (REST API and WebSocket) MUST behave predictably and adhere to standard REST/STOMP conventions.
- **Structured Error Handling**: Error handling MUST be structured and actionable across all boundaries. Every error response MUST provide a standard machine-readable format containing an HTTP status, domain error code, descriptive message, and trace identifier. Server stack traces MUST NEVER be leaked to clients.
- **Clear Logging for Debuggability**: The system MUST implement clear, structured, and contextual logging across all architectural layers:
  - Logs MUST use appropriate levels (`TRACE`, `DEBUG`, `INFO`, `WARN`, `ERROR`).
  - Detailed `DEBUG` and `TRACE` logs MUST capture critical lifecycle events, message transport transitions, handshake flows, and state changes to enable rapid troubleshooting and diagnostics.
  - Every request and WebSocket session MUST be tagged with a unique Correlation/Trace ID (`traceId` / `requestId`) propagated through MDC (Mapped Diagnostic Context) to trace operations end-to-end.
  - Logs MUST contain rich diagnostic context (e.g., operation name, user ID/session identifier, error causes, execution duration) while strictly adhering to Principle III (NEVER log decrypted/plaintext message content, private keys, or credentials).

### V. Real-Time First Communication
- As a real-time messaging platform, low latency, message ordering guarantees, and reliable delivery/acknowledgment are first-class architectural concerns.
- Reconnections MUST handle network disruptions gracefully with back-off mechanisms.

### VI. Comprehensive Automated Testing & Quality Gates (NON-NEGOTIABLE)
No code is considered complete or mergeable without automated verification. Tests MUST be organized by level, and within each level by feature area, following the rules below.

1. **Unit Testing**:
   - Every unit of domain logic and application service MUST have unit tests.
   - **Frontend scope**: Unit tests MUST cover logic-bearing units — custom hooks, state managers, encryption/decryption helpers, form validation logic, and non-trivial utility functions. Pure presentational components (layout wrappers, icon wrappers, typography primitives with no conditional rendering) are excluded from this requirement; prefer Interaction Testing (React Testing Library) for component-level verification.
   - All external dependencies (database, network, broker) MUST be mocked or stubbed — no real infrastructure is permitted at this level.
   - Business rules, invariants, and edge cases MUST be the primary focus.

2. **Integration Testing**:
   - Every integration point between application layers and real infrastructure MUST be covered by integration tests.
   - Tests MUST use containerized environments (e.g., Testcontainers) — no shared or persistent test databases are permitted.
   - Each feature's persistence, security filter chain, and messaging pipeline MUST be verified as a whole at this level.

3. **API / Contract Testing**:
   - Every externally exposed REST endpoint and WebSocket/STOMP message contract MUST have a corresponding contract test.
   - Tests MUST verify request/response schemas, HTTP status codes, and error response formats.
   - Business logic MUST NOT be re-tested at this level — only the contract boundary matters.

4. **E2EE & Cryptographic Testing**:
   Because end-to-end encryption is a Non-Negotiable principle (Principle III), its correctness MUST be independently verified:
   - **Crypto correctness**: Client-side encryption/decryption logic MUST be tested against known test vectors — given a fixed plaintext and key, the output MUST match the expected ciphertext exactly.
   - **Key exchange & ratchet**: The full key exchange handshake and any forward-secrecy ratchet steps MUST have dedicated unit tests covering both happy path and out-of-order message delivery.
   - **Key loss / compromise scenarios**: Tests MUST cover session recovery, stale-key rejection, and re-keying flows to prevent silent data corruption.
   - **Zero-knowledge invariant**: Integration tests MUST assert that no test database snapshot, server log, or API response ever contains a decryptable plaintext message.

5. **End-to-End (E2E) Testing**:
   - E2E tests MUST cover only critical user journeys — feature-level happy paths and the most impactful failure modes.
   - Tests MUST run against the fully deployed system stack.
   - Coverage at this level MUST NOT duplicate what is already verified at unit or integration level.

**Async & Real-Time Testing Standards**:
- **Backend**: All async assertions (e.g., waiting for a domain event, message delivery acknowledgment) MUST use Awaitility with an explicit timeout and polling interval. Raw `Thread.sleep()` is prohibited.
- **Frontend**: WebSocket transport MUST be replaced with a deterministic in-memory stub/mock when testing components or hooks that consume real-time messages. No test may depend on a live WebSocket connection.
- A test that exhibits non-deterministic (flaky) behavior due to timing MUST be fixed before merge — masking it with increased timeouts is not acceptable.

**Quality Gates (All Levels)**:
- **Coverage Threshold**: Automated test suites MUST achieve a minimum of 80% overall line and branch coverage (Domain logic MUST achieve at least 90% coverage).
- **Coverage Exclusions**: The following categories are explicitly excluded from coverage measurement and MUST be configured as such in JaCoCo / Vitest coverage settings:
  - Backend: DTOs, MongoDB `@Document` entities (getter/setter only), `@Configuration` classes, Spring Security config beans, constants, and auto-generated code.
  - Frontend: TypeScript type definition files (`.d.ts`), Tailwind config, static asset imports, and pure presentational components (as defined in §1).
- **100% Pass Rate**: 100% of test suites across all active levels MUST pass with zero failures and zero flaky tests before merge approval.
- **CI Pipeline Stages**:
  - **PR Fast Gate (target: < 7 minutes)**: Runs Unit Tests + Integration Tests + Contract Tests. A Pull Request MUST NOT be merged if this gate fails or if coverage drops below 80%.
  - **Deployment Gate (nightly or pre-release)**: Runs the full E2E suite (Playwright) and Cryptographic integration tests against the fully deployed stack. Failures MUST block the release and be triaged before the next deployment.

### VII. Security & Configuration Integrity (NON-NEGOTIABLE)
- Authentication, role-based authorization (RBAC), and strict input validation (backend and frontend) are mandatory foundations.
- No secrets, tokens, or private keys may ever be hardcoded or committed to version control.
- **Configuration & Secrets Separation**:
  - Backend configuration MUST use the `.properties` format (`application.properties`, `application-local.properties`).
  - Main configuration files committed to version control (`application.properties`) MUST ONLY reference environment variables (`${VAR_NAME}`) or safe fallback defaults; they MUST NEVER contain real secrets, API keys, or credentials.
  - Local development overrides and live local keys MUST reside in local configuration files (`application-local.properties`), which MUST be strictly excluded from version control via `.gitignore`.
- Security dependencies and vulnerabilities MUST be actively monitored and resolved promptly.

### VIII. Simplicity Over Complexity
- Every added library, layer, or architectural abstraction MUST have a clear, justified purpose.
- Avoid over-engineering; build for current requirements with clean extension points.

## Governance
- **Supremacy**: This Constitution supersedes all informal team conventions and temporary development shortcuts.
- **Enforcement**: All Pull Requests, architectural reviews, and AI code generation MUST verify compliance with these principles.
- **Amendments**: Amendments require formal proposal, team consensus, updated documentation in this file, and an accompanying migration plan if breaking existing standards.
- **Versioning Policy**: Semantic versioning (MAJOR for breaking principle removals/redefinitions, MINOR for new principles/expanded rules, PATCH for clarifications).

**Version**: 1.0.0 | **Ratified**: 2026-08-28 | **Last Amended**: 2026-08-28
