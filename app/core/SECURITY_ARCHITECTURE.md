# Security Layer — Architecture & Onboarding Guide

This document explains the authentication and authorization pipeline in `security.py`. It is written for onboarding: you should be able to read it, understand each piece, and explain it to others.

---

## The Big Picture

The security layer solves two requirements that seem to conflict:

1. **Verify the user's password** without ever storing a readable copy in the database.
2. **Remember the user** across many API requests without querying the database every time.

```
  Registration/Login                    Every Protected Request
  ═══════════════════                   ═══════════════════════

  Password → hash → store               Token in header → decode → get user
  Password → verify → mint JWT          No password re-check needed
```

---

## Real-World Flow Scenarios

Use these walkthroughs to visualize the flow. When asked in an interview, picture one of these scenarios and walk through it step by step.

---

### Scenario 1: Fresh User — First-Time Login (Just Registered)

**Character:** Sarah just signed up. She's at the Host Stand to get her wristband.

```
  Sarah (Client)                         Server (Sushi Queue API)
  ─────────────────                     ────────────────────────

  1. POST /api/auth/register
     {"email": "sarah@email.com", "password": "dragonroll123"}
         │
         │─────────────────────────────►  hash_password("dragonroll123")
         │                                 → "$2b$12$abc..." (stored in DB)
         │                                 Save new User to PostgreSQL
         │◄─────────────────────────────  Return {"id": 1, "email": "sarah@email.com"}
         │                                 (No token yet — she must log in)

  2. POST /api/auth/token
     {"email": "sarah@email.com", "password": "dragonroll123"}
         │
         │─────────────────────────────►  Search DB by email → find User id=1
         │                                 verify_password("dragonroll123", "$2b$12$abc...")
         │                                    → True ✅
         │                                 create_access_token({"sub": "1"})
         │                                    → "eyJhbGciOiJIUzI1NiIs..."
         │◄─────────────────────────────  Return {"access_token": "eyJ...", "token_type": "bearer"}

  3. Sarah stores the token (e.g. in localStorage or memory).
     She can now call protected endpoints.
```

**Interview tip:** "A fresh user does two HTTP calls: register (hash + store), then login (verify + mint JWT). The token is only issued after password verification."

---

### Scenario 2: Existing User — Returning Login (Token Expired or New Session)

**Character:** John used the app yesterday. He closed the browser. Today he opens it again — no token in memory. He must log in again.

```
  John (Client)                          Server (Sushi Queue API)
  ──────────────                         ────────────────────────

  POST /api/auth/token
  {"email": "john@email.com", "password": "salmonnigiri"}
      │
      │────────────────────────────────►  Search DB by email → find User id=42
      │                                    verify_password("salmonnigiri", user.hashed_password)
      │                                       → True ✅
      │                                    create_access_token({"sub": "42"})
      │                                       → New JWT (fresh 60-min expiry)
      │◄────────────────────────────────  Return {"access_token": "eyJ...", "token_type": "bearer"}

  John stores the new token. He's back in.
```

**Interview tip:** "An existing user with no token (new device, cleared storage, or expired token) goes through the same login flow. We always verify the password before issuing a new JWT. No password = no token."

---

### Scenario 3: Returning User — Already Has a Valid Token

**Character:** Maria logged in 10 minutes ago. She's still browsing. Her token is valid. She clicks "My Orders."

```
  Maria (Client)                         Server (Sushi Queue API)
  ───────────────                       ────────────────────────

  GET /api/orders/me
  Header: Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
      │
      │────────────────────────────────►  oauth2_scheme extracts token from header
      │                                    get_current_user(token, db)
      │                                       → decode_access_token(token) → payload ✅
      │                                       → payload["sub"] = "7"
      │                                       → SELECT * FROM users WHERE id = 7 → Maria
      │                                    Route runs: return Maria's orders
      │◄────────────────────────────────  Return [order1, order2, ...]
```

**Interview tip:** "When the user already has a valid token, we never touch the password. We decode the JWT (signature + expiry check), read the user ID, do one DB lookup to get the full User object, and run the route. Stateless and fast."

---

### Scenario 4: Rejected — Wrong Password, Expired Token, or No Token

```
  WRONG PASSWORD (Login)
  ──────────────────────
  POST /api/auth/token {"email": "x@x.com", "password": "wrong"}
      → verify_password("wrong", stored_hash) → False
      → 401 Unauthorized (never mint a token)


  EXPIRED OR INVALID TOKEN (Protected Request)
  ───────────────────────────────────────────
  GET /api/orders/me  Header: Authorization: Bearer <expired-or-fake-token>
      → decode_access_token(token) → None (JWTError)
      → get_current_user raises 401 "Invalid or expired token"
      → Route never runs


  NO TOKEN (Protected Request)
  ───────────────────────────
  GET /api/orders/me  (no Authorization header)
      → OAuth2PasswordBearer sees missing token
      → 403 Forbidden (before get_current_user even runs)
      → FastAPI may redirect to tokenUrl="/api/auth/token"
```

---

### Quick Reference: Which Path Am I On?

| Situation | Endpoint | What Happens |
|-----------|----------|--------------|
| Just registered, first login | `POST /api/auth/token` | verify_password → create_access_token → return JWT |
| Came back after closing app | `POST /api/auth/token` | Same as above (password required) |
| Already logged in, token valid | `GET /api/...` with Bearer token | decode_access_token → get user from DB → run route |
| Token expired or missing | Any protected route | 401 or 403, no route execution |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CLIENT (Browser / App)                                                      │
│  Sends: email + password (login)  OR  Authorization: Bearer <token> (API)  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  security.py — THE GATEWAY                                                   │
│  ├── hash_password      → One-way scramble for storage                       │
│  ├── verify_password    → Check login attempt                                │
│  ├── create_access_token → Mint JWT after successful login                   │
│  ├── decode_access_token → Validate JWT on each request                      │
│  └── get_current_user  → Dependency that ties it all together                │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PostgreSQL                                                                  │
│  Stores: hashed_password (never plaintext)                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Part 1: Password Hashing (`hash_password`)

**Purpose:** Turn a plaintext password into an irreversible string we can safely store.

### Step-by-Step

```
  Input: "ilovesushi" (plaintext)
      │
      │  1. Encode to UTF-8 bytes
      │     plain.encode('utf-8')
      │     → bcrypt works on raw bytes, not Python strings
      ▼
  pwd_bytes = b'ilovesushi'
      │
      │  2. Generate a random salt
      │     bcrypt.gensalt()
      │     → Salt = random data added before hashing
      │     → Prevents rainbow table attacks (precomputed hash lists)
      │     → Every hash is unique even for the same password
      ▼
  salt = bcrypt.gensalt()
      │
      │  3. Hash password + salt
      │     bcrypt.hashpw(pwd_bytes, salt)
      │     → bcrypt is intentionally slow (deters brute force)
      │     → Output is irreversible: you cannot get "ilovesushi" back
      ▼
  hashed_bytes = bcrypt.hashpw(pwd_bytes, salt)
      │
      │  4. Decode back to string for database storage
      ▼
  return hashed_bytes.decode('utf-8')
  → "$2b$12$KIX..." (safe to store in PostgreSQL)
```

### Why Each Step Matters

| Step | Reason |
|------|--------|
| UTF-8 encode | Cryptographic functions work on bytes, not strings |
| Salt | Same password → different hashes; rainbow tables useless |
| bcrypt | Slow by design; brute force becomes impractical |
| Irreversible | Even with DB access, attacker cannot recover the password |

---

## Part 2: Password Verification (`verify_password`)

**Purpose:** Check if a login attempt matches the stored hash.

### Step-by-Step

```
  Input: plain="ilovesushi", hashed="$2b$12$KIX..."
      │
      │  1. Encode both to bytes
      ▼
  pwd_bytes = plain.encode('utf-8')
  hashed_bytes = hashed.encode('utf-8')
      │
      │  2. bcrypt.checkpw runs the same algorithm on the plain password
      │     and compares the result to the stored hash.
      │     → One bit wrong = False
      ▼
  return bcrypt.checkpw(pwd_bytes, hashed_bytes)
  → True (match) or False (no match)
```

**Important:** We never "decrypt" the hash. We re-hash the attempt and compare. The server never sees or stores the real password.

---

## Part 3: JWT Creation (`create_access_token`)

**Purpose:** After a successful login, create a token the client can send on future requests so we don't have to verify the password again.

### Step-by-Step

```
  Input: data = {"sub": "42"}  (sub = subject = user ID)
      │
      │  1. Copy the payload and add expiration
      │     expire = datetime.now(timezone.utc) + timedelta(minutes=60)
      │     → UTC ensures consistency across servers/timezones
      ▼
  to_encode = {"sub": "42", "exp": 1734567890}
      │
      │  2. Sign with the server's secret key
      │     jwt.encode(to_encode, settings.secret_key, algorithm="HS256")
      │     → Creates a 3-part string: header.payload.signature
      │     → Signature = cryptographic proof the token wasn't tampered with
      │     → Client can hold the token but cannot alter it (signature would break)
      ▼
  return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0MiIsImV4cCI6MTczNDU2Nzg5MH0.xxx"
```

### JWT Structure

```
  header.payload.signature
  ───────────────────────
  header   → Algorithm (HS256), type (JWT)
  payload  → {"sub": "42", "exp": 1734567890}  (base64-encoded)
  signature → HMAC-SHA256(header + payload, secret_key)
```

---

## Part 4: JWT Decoding (`decode_access_token`)

**Purpose:** Validate a token and extract the payload. Returns `None` if invalid or expired.

### Step-by-Step

```
  Input: token = "eyJhbGciOiJIUzI1NiIs..."
      │
      │  1. Recompute the signature using our secret key
      │  2. Compare to the signature in the token
      │  3. Check expiration (exp) against current time
      ▼
  jwt.decode(token, settings.secret_key, algorithms=["HS256"])
      │
      ├── Success → return {"sub": "42", "exp": 1734567890}
      └── Failure (bad signature, expired, malformed) → JWTError → return None
```

---

## Part 5: `get_current_user` — The Master Gate

**Purpose:** A FastAPI dependency that runs before any protected route. It extracts the token, validates it, loads the user from the database, and returns the `User` object. If anything fails, the request is rejected with 401.

### How Dependency Injection Works

```
  Client requests: GET /api/orders/me
  Header: Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
      │
      │  FastAPI sees: user: User = Depends(get_current_user)
      │  → "Before running the route, I must call get_current_user and pass the result."
      │  → get_current_user needs: token (from oauth2_scheme), db (from get_db)
      │  → oauth2_scheme automatically extracts the Bearer token from the header
      ▼
  get_current_user(token="eyJ...", db=<session>)
      │
      │  If it returns a User → route runs with that user
      │  If it raises HTTPException → route never runs, client gets 401
      ▼
  Route handler receives: user (the verified User object)
```

### Step-by-Step: What Happens Inside `get_current_user`

```
  Step 1: Get the token
  ─────────────────────
  token: Annotated[str, Depends(oauth2_scheme)]
  → OAuth2PasswordBearer reads the "Authorization: Bearer <token>" header
  → If missing → FastAPI returns 403 before get_current_user even runs
  → If present → token = "eyJhbGciOiJIUzI1NiIs..."


  Step 2: Decode the token
  ───────────────────────
  payload = decode_access_token(token)
  → Valid token → payload = {"sub": "42", "exp": 1734567890}
  → Invalid/expired → payload = None


  Step 3: Reject if invalid
  ─────────────────────────
  if payload is None:
      raise HTTPException(401, "Invalid or expired token")
  → Request stops here. Route never runs.


  Step 4: Extract user ID
  ──────────────────────
  sub = payload.get("sub")
  → "sub" (subject) is the standard JWT claim for "who is this?"
  → We store the user ID as a string in the token
  if sub is None:
      raise HTTPException(401, "Invalid token")


  Step 5: Load user from database
  ───────────────────────────────
  result = await db.execute(select(User).where(User.id == int(sub)))
  user = result.scalar_one_or_none()
  → One database query to fetch the User row
  → We need this to return the full User object (email, is_bot, etc.)


  Step 6: Reject if user no longer exists
  ──────────────────────────────────────
  if user is None:
      raise HTTPException(401, "User not found")
  → User might have been deleted after the token was issued


  Step 7: Return the user
  ───────────────────────
  return user
  → FastAPI injects this into the route: async def get_orders(user: User = Depends(get_current_user))
```

---

## The Full Lifecycle

```
  REGISTRATION
  ────────────
  Client: POST /api/auth/register {"email": "x@x.com", "password": "secret"}
      → hash_password("secret") → store in DB
      → Return UserPublic (no password)


  LOGIN
  ─────
  Client: POST /api/auth/token {"email": "x@x.com", "password": "secret"}
      → Load user from DB by email
      → verify_password("secret", user.hashed_password) → True
      → create_access_token({"sub": str(user.id)})
      → Return {"access_token": "eyJ...", "token_type": "bearer"}


  PROTECTED REQUEST
  ─────────────────
  Client: GET /api/orders/me  Header: Authorization: Bearer eyJ...
      → oauth2_scheme extracts token
      → get_current_user(token, db)
          → decode_access_token(token) → payload
          → select User where id = payload["sub"]
          → return user
      → Route runs with user
      → Return user's orders
```

---

## Security Checklist

| Component | What it protects against |
|-----------|---------------------------|
| `hash_password` | Plaintext passwords in DB; rainbow tables |
| `verify_password` | Wrong passwords at login |
| Salt (inside bcrypt) | Same-password same-hash; precomputed attacks |
| JWT signature | Token tampering (e.g. changing user ID) |
| JWT expiration | Stolen tokens used forever |
| `get_current_user` | Unauthenticated access to protected routes |
| DB lookup in get_current_user | Deleted users with old tokens |

---

## Summary for Explaining to Others

1. **Passwords:** We hash them with bcrypt (salt + slow hash). We never store or transmit plaintext.
2. **Login:** We verify with `bcrypt.checkpw`. On success, we mint a JWT containing the user ID.
3. **JWT:** A signed, expiring credential. The client sends it on every request. We verify the signature and expiration without touching the password again.
4. **get_current_user:** A FastAPI dependency that runs before protected routes. It extracts the token, decodes it, loads the user from the DB, and returns the User. Any failure → 401.
5. **Dependency injection:** FastAPI calls `get_current_user` automatically when a route declares `Depends(get_current_user)`. The route only runs if the dependency succeeds.
