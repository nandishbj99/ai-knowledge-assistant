# Feature Specification: FEAT-003 - JWT Authentication & Redis Rate Limiting

> **Feature ID:** `FEAT-003`  
> **Status:** `DESIGN_READY`  
> **Parent Spec:** [Master Project Spec](../../specs/main-spec.md)  
> **Design & ADRs:** [Design & ADRs](./design.md) | **Tasks:** [Tasks](./tasks.md) | **Testing:** [Testing](./testing.md)

---

## 1. Overview & Objective
Implements secure user identity verification via JWT access tokens and distributed rate limiting backed by Redis to protect LLM endpoints, document uploads, and database resources from abusive traffic and denial-of-service.

---

## 2. User Stories
- **US-01:** As a user, I want to register and log in with email and password to receive a secure JWT token.
- **US-02:** As a system administrator, I want unauthenticated requests to protected endpoints to be rejected with HTTP 401 Unauthorized.
- **US-03:** As an operator, I want bursts of document uploads or chat requests to be throttled with HTTP 429 Too Many Requests and a `Retry-After` header.

---

## 3. Scope & Requirements

### Functional Requirements (FR)
- **FR-01 (User Registration):** `POST /api/v1/auth/register` with email, password (min 8 chars), and name. Stores password hashed with BCrypt.
- **FR-02 (User Login):** `POST /api/v1/auth/login` validating credentials and returning a signed JWT bearer token (24h TTL).
- **FR-03 (Stateless JWT Filter):** Validates Bearer token on incoming requests, sets authenticated user principal in `SecurityContext`.
- **FR-04 (Redis Distributed Rate Limiting):**
  - Document uploads: 10 requests / hour per user.
  - Chat queries: 30 requests / minute per user.
  - Auth endpoints: 10 requests / minute per client IP.
- **FR-05 (Rate Limit Headers):** Return `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `Retry-After` on HTTP 429 responses.
