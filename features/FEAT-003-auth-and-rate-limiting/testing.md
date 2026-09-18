# Feature Testing & Verification: FEAT-003 - JWT Authentication & Redis Rate Limiting

> **Feature ID:** `FEAT-003`  
> **Status:** `PENDING_EXECUTION`  
> **Spec Reference:** [Feature Spec](./spec.md) | [Design & ADRs](./design.md)

---

## 1. Verification Strategy
1. **Authentication Tests:** Verify register, login, invalid credentials, token expiration, and tampered signatures.
2. **Rate Limiting Tests:** Send concurrent bursts exceeding limits; verify HTTP 429 status and `Retry-After` header.

---

## 2. Test Case Matrix

| Test ID | Test Scenario | Target Component | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| `TC-01` | Register new user with valid email and password | `AuthController` | Returns 201 Created with user ID | `PENDING` |
| `TC-02` | Login with correct credentials | `AuthController` | Returns 200 OK with Bearer access token | `PENDING` |
| `TC-03` | Login with wrong password | `AuthController` | Returns 401 Unauthorized | `PENDING` |
| `TC-04` | Access protected endpoint without Bearer token | `SecurityFilterChain` | Returns 401 Unauthorized | `PENDING` |
| `TC-05` | Send 11 rapid requests to `/auth/login` | `RedisRateLimitingFilter` | 11th request returns 429 Too Many Requests with `Retry-After` header | `PENDING` |

---

## 3. Manual Verification Steps (cURL)

```bash
# 1. Register User
curl -i -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@company.com", "password":"Password123!", "fullName":"Test User"}'

# 2. Login
curl -i -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@company.com", "password":"Password123!"}'

# 3. Burst rate limit test
for i in {1..12}; do
  curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:8080/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@company.com", "password":"Wrong"}'
done
# Expected: 200/401 for first 10, then 429 Too Many Requests
```
