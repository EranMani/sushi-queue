# Pydantic Schemas — Architecture & Security

This document explains the role of Pydantic schemas in the Sushi Queue API: validation, security, and how they bridge SQLAlchemy models to the web.

---

## The Two Worlds

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         INTERNET (JSON)                                       │
│  Browsers, mobile apps, curl, Postman — they speak JSON over HTTP            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │  Pydantic Schemas
                                    │  (the translator & gatekeeper)
                                    │
┌─────────────────────────────────────────────────────────────────────────────┐
│                         POSTGRESQL (SQL)                                     │
│  Tables, rows, columns — SQLAlchemy models speak this language               │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Pydantic** and **SQLAlchemy** are separate systems. They don't depend on each other. When they need to talk, `model_config = {"from_attributes": True}` is the translator.

---

## Schema Roles

### 1. Door Guard (Input Validation)

**Incoming data** from the client is validated before it reaches the database.

```
  Client sends JSON                    Pydantic validates                 Database
  ─────────────────                   ─────────────────                  ─────────
  {"email": "x",                      UserCreate schema                  ❌ Rejected
   "password": "secret"}    ──────►    catches invalid email   ──────►    (never reached)

  {"email": "user@mail.com",          UserCreate schema                  ✅ Accepted
   "password": "secret"}    ──────►    passes validation      ──────►    (service creates user)
```

**Example:** `OrderCreate` expects `items: list[OrderItemCreate]` with `menu_item_id: int` and `quantity: int`. If the client sends `"quantity": "three"`, Pydantic rejects it. The database never sees bad data.

---

### 2. Filter (Output Control)

**Outgoing data** is filtered so only allowed fields are exposed.

```
  Database row                         Pydantic filters                   Response JSON
  ─────────────                        ───────────────                   ─────────────
  User(id=1,                           UserPublic schema                 {"id": 1,
   email="x@x.com",         ──────►    keeps: id, email, is_bot  ──────►   "email": "x@x.com",
   hashed_password="...",               drops: hashed_password             "is_bot": false}
   is_bot=False)
```

**Security:** `hashed_password` never leaves the server. The schema defines exactly what the client can see.

---

## Data Flow Diagram

```
                    INBOUND (Request)                          OUTBOUND (Response)
                    ═════════════════                          ════════════════════

  Client                    FastAPI Route                     Client
    │                             │                              ▲
    │  POST /auth/register        │                              │
    │  {"email": "...",            │                              │
    │   "password": "..."}         │                              │
    │         │                   │                              │
    │         ▼                   │                              │
    │  ┌──────────────┐           │                              │
    │  │ UserCreate   │  Validate │                              │
    │  │ (Pydantic)   │ ────────► │  Service creates User       │
    │  └──────────────┘           │  in database                 │
    │         │                  │         │                    │
    │         │  Invalid?         │         │  SQLAlchemy User    │
    │         │  ──► 422 Error   │         │  object            │
    │         │                  │         ▼                    │
    │         │                  │  ┌──────────────┐            │
    │         │                  │  │ UserPublic   │  Filter     │
    │         │                  │  │ (Pydantic)   │ ──────────►  │  JSON response
    │         │                  │  └──────────────┘            │
    │         │                  │         │                     │
    │         │                  │  from_attributes=True         │
    │         │                  │  reads User.id, .email, .is_bot │
    │         │                  │  ignores .hashed_password       │
    │         │                  │                               │
```

---

## Input vs Output Schemas

| Schema | Direction | Purpose |
|--------|-----------|---------|
| `UserCreate` | IN | Validate registration (email, password) |
| `UserPublic` | OUT | Expose id, email, is_bot only |
| `OrderCreate` | IN | Validate order payload (items list) |
| `OrderItemCreate` | IN | Validate each line item |
| `OrderPublic` | OUT | Expose order + items (no internal fields) |
| `OrderItemPublic` | OUT | Expose line item fields |
| `MenuItemPublic` | OUT | Expose menu item (including ingredients) |
| `Token` | OUT | Return JWT to client |

---

## The Translator: `from_attributes=True`

SQLAlchemy returns **objects** with attributes. Pydantic expects **dicts** or keyword args. `from_attributes=True` tells Pydantic to read object attributes.

```
  SQLAlchemy User object              Pydantic UserPublic
  ─────────────────────              ────────────────────

  user.id          ──────────────────►  id: 1
  user.email       ──────────────────►  email: "x@x.com"
  user.is_bot      ──────────────────►  is_bot: False
  user.hashed_password  ──►  (not in schema, dropped)
  user.created_at       ──►  (not in schema, dropped)
```

**Code:**
```python
user = await db.get(User, 1)           # SQLAlchemy object
return UserPublic.model_validate(user) # Pydantic reads user.id, user.email, user.is_bot
```

Without `from_attributes=True`, you'd need:
```python
UserPublic(id=user.id, email=user.email, is_bot=user.is_bot)  # manual mapping
```

---

## Security: What Gets Filtered

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  DATABASE (full row)                    │  CLIENT (schema-defined only)    │
├─────────────────────────────────────────┼──────────────────────────────────┤
│  User.hashed_password        ──────────►│  ❌ Never sent                    │
│  User.created_at             ──────────►│  ❌ Omitted unless in schema       │
│  Internal IDs, timestamps    ──────────►│  ❌ Omitted unless in schema       │
│  User.id, email, is_bot      ──────────►│  ✅ UserPublic includes these      │
└─────────────────────────────────────────┴──────────────────────────────────┘
```

**Principle:** The schema is the contract. If it's not in the schema, it doesn't leave the server.

---

## Schema Independence

Pydantic schemas are **not** tied to the database. They validate and shape data.

```
  Use case                    Schema                    Database?
  ─────────                   ──────                    ──────────
  Contact form                ContactFormCreate         No (sends email)
  Search query                SearchParams               No (builds query)
  User registration          UserCreate                 Yes
  Order creation              OrderCreate                Yes
```

When the data **does** come from the database, `from_attributes=True` lets Pydantic read the ORM object. When it doesn't, Pydantic works with plain dicts or JSON.

---

## Schema Design: What to Include or Exclude

### Step 1: List All Model Fields

Before defining a schema, list every field on the SQLAlchemy model:

```
  User model fields:
  ├── id
  ├── email
  ├── hashed_password
  ├── is_bot
  └── created_at
```

### Step 2: Classify Each Field

| Category | Include in Public? | Examples |
|----------|-------------------|----------|
| **Secrets** | Never | `hashed_password`, `api_key`, `refresh_token` |
| **Internal IDs** | Only when needed for reference | `id` (for linking), `user_id` (for ownership) |
| **PII (sensitive)** | Only if required for UX, consider masking | `email` (user profile), `phone` (maybe mask) |
| **Business data** | Usually yes | `name`, `price`, `status`, `quantity` |
| **Audit metadata** | Often no for public; yes for admin | `created_at`, `updated_at`, `deleted_at` |
| **Relationships** | Only if client needs to display/navigate | `items` in OrderPublic |

### Step 3: Ask the Right Questions

```
  For each field, ask:

  1. Can an attacker use this to compromise the system?
     ──► Yes: EXCLUDE (e.g. hashed_password, internal tokens)

  2. Does the client need this to function?
     ──► No: Consider EXCLUDE (e.g. created_at for a simple list view)

  3. Does it expose another user's data?
     ──► Yes: EXCLUDE or restrict by auth (e.g. never show other users' emails in bulk)

  4. Is it useful for the intended use case?
     ──► Yes: INCLUDE (e.g. order status for order tracking)
```

---

## Security: Deciding What to Display Publicly

### The Default Rule

```
  ┌─────────────────────────────────────────────────────────────────┐
  │  DEFAULT: EXCLUDE                                                │
  │  Only add a field to a public schema if you have a clear reason │
  │  to include it. When in doubt, leave it out.                     │
  └─────────────────────────────────────────────────────────────────┘
```

### Security Checklist for Output Schemas

| Question | If Yes | Action |
|----------|--------|--------|
| Is it a secret or credential? | ✓ | Never include |
| Is it a hash, token, or key? | ✓ | Never include |
| Could it help enumerate users or resources? | ✓ | Exclude or rate-limit |
| Is it PII the client doesn't need? | ✓ | Exclude or mask |
| Does the endpoint require auth? | ✓ | Still filter; auth ≠ full access |
| Would it leak another user's data? | ✓ | Exclude; enforce ownership in the route |

### Common Pitfalls

```
  ❌ BAD: Returning the full User model "because the route is protected"
       → Auth protects who can call the route; the schema protects what they see.
       → A logged-in user should not receive their own hashed_password.

  ❌ BAD: Including created_at "because it's harmless"
       → Can leak timing info, help with enumeration, or bloat responses.
       → Include only when the client needs it (e.g. "Ordered 2 hours ago").

  ✅ GOOD: Separate schemas per use case
       → UserPublic for profile display (id, email, is_bot)
       → UserAdmin for admin panel (add created_at, last_login)
       → Different endpoints, different schemas, different exposure.
```

### Schema-by-Role Pattern

When the same entity is exposed to different audiences, use different schemas:

```
  Order
  ├── OrderPublic      → Customer: id, status, total_price, items
  ├── OrderKitchen     → Kitchen: id, items (with prep_time), special_notes
  └── OrderAdmin       → Admin: all above + created_at, updated_at, user_id
```

---

## Summary

| Concept | Explanation |
|---------|-------------|
| **Door Guard** | Input schemas validate incoming JSON before it reaches services or the DB |
| **Filter** | Output schemas control what fields are sent to the client |
| **Translator** | `from_attributes=True` lets Pydantic build from SQLAlchemy objects |
| **Security** | Sensitive fields (e.g. `hashed_password`) are omitted by not including them in output schemas |
| **Independence** | Schemas can validate data that never touches the database |
