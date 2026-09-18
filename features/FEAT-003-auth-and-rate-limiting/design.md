# Feature Design & ADRs: FEAT-003 - JWT Authentication & Redis Rate Limiting

> **Feature ID:** `FEAT-003`  
> **Status:** `DESIGN_READY`  
> **Parent Spec:** [FEAT-003 Spec](./spec.md) | [Tasks](./tasks.md) | [Testing](./testing.md)

---

## 1. High-Level Design (HLD)

### Request Filtering, Token Lifecycle & Rate Limiting Pipeline
```mermaid
flowchart TD
    Req["Incoming HTTP Request"] --> SecurityFilter["JwtAuthenticationFilter"]
    
    SecurityFilter -->|Public /api/v1/auth/*| AllowAuth["Forward to Auth Controller"]
    SecurityFilter -->|Protected Endpoints| CheckBlacklist{"Token in Redis Blacklist?\n(bl:token:jti)"}
    
    CheckBlacklist -->|Yes (Revoked)| Err401Revoked["Return 401 Unauthorized (Token Revoked)"]
    CheckBlacklist -->|No| ValidateToken{"Valid Signature & Expiry?"}
    
    ValidateToken -->|No / Expired| Err401["Return 401 Unauthorized"]
    ValidateToken -->|Yes| SetPrincipal["Set SecurityContext\n(user_id, tenant_id, roles)"]
    
    SetPrincipal --> RateLimiterFilter["RedisRateLimiterFilter"]
    RateLimiterFilter --> EvalLua{"Evaluate Redis Lua Token Bucket\nCapacity & Refill Rate"}
    
    EvalLua -->|Tokens Available| Decrement["Decrement Token & Add X-RateLimit-* Headers"] --> Controller["Execute REST Controller\n(Scoped to tenant_id & user_id)"]
    EvalLua -->|Exceeded Limit| Err429["Return 429 Too Many Requests\n(Retry-After Header)"]
```

---

## 2. Architecture Decision Records (ADRs)

### ADR-01: JWT Access Token Lifecycle, Refresh Rotation & Revocation Policy
- **Status:** `ACCEPTED` (Revised)
- **Deciders:** Engineering Team
- **Date:** 2026-09-17

#### Context & Problem Statement
Stateless JWTs cannot be revoked if a user logs out or if credentials are leaked. Long-lived access tokens (e.g. 24h) pose a security risk.

#### Decision Outcome & Justification
**Chosen:** Short-Lived Access Tokens + Refresh Token Rotation + Redis Revocation Blacklist:
1. **Access Token Lifespan:** **15 minutes**.
   - Claims: `sub` (user UUID), `tenant_id` (UUID), `role` (`ROLE_USER`/`ROLE_ADMIN`), `jti` (unique token ID), `exp`, `iat`.
2. **Refresh Token Lifespan:** **7 days**.
   - Stored hashed in the database. When used, the refresh token is rotated (the old refresh token is invalidated and replaced with a new pair).
3. **Revocation on Logout:**
   - Calling `/auth/logout` writes `bl:token:<jti>` to Redis with TTL equal to the token's remaining lifespan. The security filter rejects blacklisted tokens immediately.
4. **Secret Key Rotation Policy:**
   - Tokens support key ID (`kid`) in the header, allowing zero-downtime rotation of signing keys.

---

### ADR-02: Distributed Redis Token Bucket with Defined Capacity, Refill & Expiry
- **Status:** `ACCEPTED`
- **Deciders:** Engineering Team
- **Date:** 2026-09-17

#### Context & Problem Statement
Rate limits must protect expensive LLM operations, prevent upload starvation, and prevent abuse across multiple backend gateway instances.

#### Decision Outcome & Justification
**Chosen:** Redis Lua Script Token Bucket with Explicit Parameter Profiles:

| Scope | Key Pattern | Bucket Capacity | Refill Rate | Redis Key Expiry |
| :--- | :--- | :--- | :--- | :--- |
| **Auth Endpoints** | `rl:auth:<client_ip>` | 10 tokens | 0.16 tokens/sec (10/min) | 2 minutes |
| **Document Uploads**| `rl:upload:<tenant_id>:<user_id>` | 5 tokens | 0.008 tokens/sec (5/hr) | 4 hours |
| **Chat Queries** | `rl:chat:<tenant_id>:<user_id>` | 30 tokens | 0.5 tokens/sec (30/min) | 3 minutes |
| **Read/Status APIs** | `rl:read:<tenant_id>:<user_id>` | 120 tokens | 2 tokens/sec (120/min) | 2 minutes |

- The atomic Redis Lua script ensures zero race conditions across distributed gateway nodes.
- When tokens reach 0, HTTP 429 Too Many Requests is returned with `Retry-After: <seconds>`.

---

### ADR-03: Explicit Per-User and Tenant Authorization Framework
- **Status:** `ACCEPTED`
- **Deciders:** Engineering Team
- **Date:** 2026-09-17

#### Context & Problem Statement
Authentication proves identity; authorization must ensure tenant data boundaries are strictly isolated across all entities.

#### Decision Outcome & Justification
**Chosen:** Framework-Enforced Tenant Context:
1. `JwtAuthenticationFilter` binds an authenticated principal containing `(userId, tenantId)` to the `SecurityContext`.
2. Repositories enforce tenant-scoped queries:
   `Optional<Document> findByIdAndTenantIdAndUserId(UUID id, UUID tenantId, UUID userId)`
3. Any attempt by User B to query, update, or delete User A's document returns `404 Not Found` (preventing ID enumeration attacks) or `403 Forbidden`.
