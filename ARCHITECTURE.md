# Sushi Queue — Project Architecture

This document explains the overall architecture of the Sushi Queue project: why folders are organized the way they are, what each layer does, and the design decisions behind the structure. It is written for engineers joining the project or reviewing the codebase.

We use a **restaurant metaphor** throughout: the Open Restaurant (app/), the Maintenance Crew (root folders), the Waiters (routes), the Door Guards (schemas), the Managers (services), the Filing Cabinet (models), the Whiteboard (core), and the Kitchen Staff (tasks). This analogy makes the architecture easier to visualize and remember.

---

## Table of Contents

1. [Project Structure Overview](#project-structure-overview)
2. [The Restaurant Metaphor (Analogy Key)](#the-restaurant-metaphor-analogy-key)
3. [Root-Level Folders: Why They Exist](#root-level-folders-why-they-exist)
4. [The `app/` Folder: Application vs. Operational Code](#the-app-folder-application-vs-operational-code)
5. [Operational Tools: What They Are and Why at Root](#operational-tools-what-they-are-and-why-at-root)
6. [Inside `app/`: Layer-by-Layer Breakdown](#inside-app-layer-by-layer-breakdown)
7. [Data Flow: How a Request Moves Through the System](#data-flow-how-a-request-moves-through-the-system)
8. [Design Decisions and Trade-offs](#design-decisions-and-trade-offs)
9. [Related Documentation](#related-documentation)

---

## Project Structure Overview

```
sushi-queue/
├── app/                    # 🏢 The Open Restaurant (runtime)
│   ├── api/                # 🤵 The Waiters
│   │   └── routes/         # HTTP entry points
│   ├── core/               # 🪧 The Whiteboard (config, Redis, auth)
│   ├── models/             # 🗄️ The Filing Cabinet (ORM)
│   ├── schemas/            # 🚪 The Door Guards (validation & filtering)
│   ├── services/           # 👔 The Managers (business logic)
│   ├── tasks/              # 🧑‍🍳 The Kitchen Staff (Celery workers)
│   ├── websocket/          # Live updates (future)
│   └── frontend/           # NiceGUI UI (future)
├── migrations/             # 🧰 Maintenance Crew: DB schema changes
├── scripts/               # 🧰 Maintenance Crew: seed, admin scripts
├── tests/                 # 🧰 Maintenance Crew: verification
├── .github/                # CI/CD workflows
├── pyproject.toml         # Project metadata and dependencies
├── docker-compose.yml     # Local development stack
├── .env.example           # Environment template
└── README.md
```

---

## 🍣 The Restaurant Metaphor (Analogy Key)

To make this architecture easier to visualize, we map our technical layers to a working restaurant:

- **🏢 The Open Restaurant (app/)**: The main building and package where we actively serve customers.

- **🧰 The Maintenance Crew (Root Folders)**: Tools that run on demand outside the main request cycle (e.g., scripts/, migrations/).

- **🤵 The Waiters (app/api/routes/)**: The HTTP entry points that receive requests and return responses.

- **🚪 The Door Guards (app/schemas/)**: Pydantic models that validate incoming data and filter outgoing data.

- **👔 The Managers (app/services/)**: Encapsulate the business logic and prepare instructions for the database.

- **🗄️ The Filing Cabinet (app/models/)**: SQLAlchemy classes that define exactly how data is stored permanently.

- **🪧 The Whiteboard (app/core/)**: The underlying infrastructure, like our lightning-fast Redis cache.

- **🧑‍🍳 The Kitchen Staff (app/tasks/)**: Celery workers handling heavy background jobs so the Waiters don't freeze.

---

## Root-Level Folders: Why They Exist

### The Principle: Separation by Lifecycle and Purpose

Root-level folders are divided by **when** and **how** they run. Think of the **🏢 Open Restaurant** as the main building where customers are served, and the **🧰 Maintenance Crew** as the team that works *outside* the dining room — before opening, after closing, or on demand:

| Folder | Lifecycle | Restaurant Analogy |
|--------|-----------|-------------------|
| `app/` | Runs with the server (uvicorn) | 🏢 The Open Restaurant — open for business |
| `migrations/` | Runs on deploy or schema change | 🧰 Maintenance Crew — rearranging the Filing Cabinet |
| `scripts/` | Runs on demand (CLI, cron, manual) | 🧰 Maintenance Crew — stocking the menu, seeding data |
| `tests/` | Runs in CI or locally | 🧰 Maintenance Crew — health checks, quality checks |
| `.github/` | Runs on push/PR | Automation |

**Decision:** Each folder has a distinct execution context. Mixing them (e.g., putting scripts inside the Open Restaurant) would blur responsibilities — you wouldn't want the Maintenance Crew doing their work in the middle of the dining room during service.

---

## The `app/` Folder: Application vs. Operational Code

### Why Use an `app/` Folder? (🏢 The Open Restaurant)

1. **Package boundary.** `app` is the main Python package — the entire restaurant building. Imports like `from app.models import User` make it clear where code lives. The package name is the project's namespace.

2. **Deployment unit.** When we build a Docker image or deploy to Railway, we copy the Open Restaurant (`app/`) and supporting files. The application entry point is `app.main:app`. Everything the server needs at runtime lives under `app/`.

3. **Convention.** FastAPI, Django, Flask, and most Python web frameworks use a top-level application package. New engineers expect it — like expecting a restaurant to have a kitchen and dining area.

4. **Exclusion clarity.** What is *not* in `app/` is not part of the running restaurant. The Maintenance Crew (tests, scripts, migrations) works outside the building. This prevents accidental imports of test fixtures or seed data in production code.

### What Belongs in the Open Restaurant (`app/`)?

- Code that runs when the API serves requests (the Waiters)
- Code that runs when Celery workers process tasks (the Kitchen Staff)
- Code that runs when WebSocket connections are active
- Shared infrastructure (the Whiteboard: config, database, Redis, security)

### What Does *Not* Belong in the Open Restaurant?

- Seed scripts (🧰 Maintenance Crew — run once before opening)
- Migration files (🧰 Maintenance Crew — run by Alembic)
- Test code (🧰 Maintenance Crew — run by pytest)
- CI config (run by GitHub Actions, not by the app)

---

## Operational Tools: What They Are and Why at Root

### What Are Operational Tools? (🧰 The Maintenance Crew)

**Operational tools** are the **Maintenance Crew** — they support the restaurant but don't serve customers during the request-response cycle. They work:

- **On demand** — e.g., `uv run python scripts/seed_db.py` (stocking the menu before opening)
- **On schedule** — e.g., Celery Beat (the Kitchen Staff's scheduler runs separately)
- **During deployment** — e.g., `alembic upgrade head` (rearranging the Filing Cabinet)
- **During development** — e.g., `pytest tests/` (quality checks)

Examples in this project:

| Tool | Location | Restaurant Analogy |
|------|----------|-------------------|
| Seed script | `scripts/seed_db.py` | 🧰 Maintenance Crew — stocking the menu, creating bot users |
| Alembic | `migrations/` | 🧰 Maintenance Crew — rearranging the Filing Cabinet (DB schema) |
| Pytest | `tests/` | 🧰 Maintenance Crew — health checks, quality checks |
| Celery worker | `app/tasks/` | 🧑‍🍳 Kitchen Staff — inside the restaurant, but a separate process |
| Celery Beat | `app/tasks/` | 🧑‍🍳 Kitchen Staff — the scheduler |

### Why Is the Maintenance Crew at the Root?

1. **Different entry points.** The Open Restaurant runs via `uvicorn app.main:app`. The seed script runs via `python scripts/seed_db.py`. Each has its own entry point. The Maintenance Crew doesn't enter through the front door — they have their own entrance.

2. **Not importable as app code.** We don't want `from app.scripts.seed_db import seed` in production. Scripts are executed directly. Keeping them outside the Open Restaurant prevents them from being treated as part of the dining room.

3. **Tool-specific dependencies.** The Maintenance Crew might need different tools or env vars (e.g., sync vs async). Root-level placement makes it obvious they're separate from the main restaurant.

4. **Industry convention.** Most Python projects use `scripts/` or `tools/` at the root for admin and maintenance tasks — like Django's `manage.py`.

### Important Note

> **The Maintenance Crew are first-class citizens.** They are not "less important" than the Waiters or Kitchen Staff. They simply work in a *different lifecycle* — before opening, after closing, or on demand. Document them, test them when possible, and keep them maintainable.

---

## Inside `app/`: Layer-by-Layer Breakdown

### High-Level Flow (The Restaurant in Action)

```
  Customer (HTTP Request)
       │
       ▼
  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
  │ 🤵 Waiters  │ ──► │ 👔 Managers │ ──► │ 🗄️ Filing  │
  │ (routes)    │     │ (services)  │     │   Cabinet   │
  │             │     │             │     │ (models)    │
  └─────────────┘     └─────────────┘     └─────────────┘
       │                     │                     │
       │                     │                     │
       ▼                     ▼                     ▼
  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
  │ 🚪 Door     │     │ 🪧 Whiteboard│     │  PostgreSQL │
  │   Guards    │     │ (core)       │     │  (storage)  │
  │ (schemas)   │     │ Redis, auth  │     │             │
  └─────────────┘     └─────────────┘     └─────────────┘
```

### 🤵 The Waiters (`app/api/routes/`)

**Purpose:** HTTP entry points — the front-of-house staff. Thin layer that receives requests, validates input (via the Door Guards), calls the Managers, and returns responses.

**Why separate from the Managers?** Waiters handle HTTP concerns (status codes, headers, dependency injection). Managers handle business logic. Keeping them separate allows:
- Reusing Managers from the Kitchen Staff (Celery) or WebSocket handlers
- Testing business logic without HTTP
- Clear single responsibility: Waiters serve; Managers decide.

### 👔 The Managers (`app/services/`)

**Purpose:** Business logic. Create user, create order, get menu items, authenticate. The Managers prepare instructions for the Filing Cabinet and hand work to the Kitchen Staff. No HTTP, no low-level database details.

**Why a Managers layer?** Waiters should stay thin — they just take orders and deliver. Managers encapsulate "what the system does" — e.g., "create an order" involves validating items, computing total, creating Order + OrderItems in the Filing Cabinet, and handing the ticket to the Kitchen Staff. That logic belongs in a Manager, not in a Waiter.

### 🗄️ The Filing Cabinet (`app/models/`)

**Purpose:** SQLAlchemy ORM models. The permanent storage — how data is filed and retrieved. Map Python classes to database tables. Define relationships.

**Why a Filing Cabinet?** The database schema is the source of truth for persistence. Models are the Python representation of those files. They are used by Managers, migrations (Maintenance Crew), and the Kitchen Staff. Keeping them in one place ensures consistency — everyone reads from the same filing system.

### 🚪 The Door Guards (`app/schemas/`)

**Purpose:** Pydantic models for request validation and response shaping. The Door Guards validate incoming orders and filter what leaves the building. Define what goes in and out of the API.

**Why separate from the Filing Cabinet?** The Filing Cabinet has internal files (e.g., `hashed_password`) that must never leave the building. The Door Guards define the API contract — they ensure we never expose `hashed_password`. Schemas act as a filter and validator at the boundary. See `app/schemas/ARCHITECTURE.md` for details.

### 🪧 The Whiteboard (`app/core/`)

**Purpose:** Cross-cutting infrastructure. Config, database connection, Redis cache, security (hashing, JWT). The shared tools everyone uses — like a whiteboard in the back office with the day's specials, connection info, and security procedures.

**Why "Whiteboard"?** These modules are used by Waiters, Managers, and the Kitchen Staff. They are not business logic — they are the plumbing. Naming them `core` signals that they are foundational — the shared reference everyone consults.

### 🧑‍🍳 The Kitchen Staff (`app/tasks/`)

**Purpose:** Celery tasks. Heavy background jobs — `process_order`, `cancel_stale_orders`. The Kitchen Staff handles work so the Waiters don't freeze. When a customer orders, the Waiter hands the ticket to the Kitchen; the Kitchen prepares it and signals when it's ready.

**Why inside the Open Restaurant?** The Kitchen Staff use the same Filing Cabinet, Whiteboard, and business concepts. They are part of the restaurant — they just work in a separate area (separate process). Keeping them in `app/` allows `from app.models import Order` and shared config.

### `app/websocket/` (future)

**Purpose:** WebSocket connection management and Redis Pub/Sub listener for live updates. Like a runner who announces "Order #42 is ready!" to everyone watching the board.

**Why inside app/?** WebSockets are another way the restaurant communicates with customers. They share the Whiteboard (Redis), config, and the same event model. They belong in the Open Restaurant.

---

## Data Flow: How a Request Moves Through the System

### Example: POST /api/orders (A Customer Places an Order)

```
  1. Customer (client) sends JSON order
        │
        ▼
  2. 🤵 Waiter (FastAPI) receives the request at the door
        │
        ▼
  3. 🚪 Door Guards (OrderCreate schema) validate the order
        │  Invalid? → 422 (order rejected at the door)
        ▼
  4. 🚪 Door Guards (get_current_user) check the customer's wristband (JWT)
        │  No/invalid token? → 401 (no entry)
        ▼
  5. 🤵 Waiter hands order to 👔 Manager: order_service.create_order(...)
        │
        ▼
  6. 👔 Manager: validates menu items, computes total, files Order + OrderItems in 🗄️ Filing Cabinet
        │
        ▼
  7. 👔 Manager: hands ticket to 🧑‍🍳 Kitchen Staff: process_order.delay(order.id)
        │
        ▼
  8. 🤵 Waiter returns OrderPublic (202 Accepted) — "We've got your order!"
        │
        ▼
  9. 🧑‍🍳 Kitchen Staff picks up the ticket (separate process)
        │
        ▼
 10. 🧑‍🍳 Kitchen Staff: PREPARING → sleep → READY, publishes to 🪧 Whiteboard (Redis)
        │
        ▼
 11. WebSocket listener reads from Whiteboard, broadcasts "Order #42 is ready!" to connected clients
```

Each layer has a clear responsibility. **Waiters** don't touch the Filing Cabinet directly; **Managers** don't know about HTTP status codes; the **Filing Cabinet** doesn't know about JSON.

---

## Design Decisions and Trade-offs

### 1. Async Everywhere (API)

**Decision:** Use `async def` for routes and `AsyncSession` for database access.

**Why:** Non-blocking I/O improves throughput — the Waiters can handle more customers without blocking. FastAPI and SQLAlchemy support async natively.

**Trade-off:** The Kitchen Staff (Celery workers) run sync code. We use `app/core/db_sync.py` for workers. Two database access patterns — acceptable because the Kitchen is a separate process with a different concurrency model.

### 2. Managers Layer (Services)

**Decision:** Waiters call Managers; Managers contain business logic.

**Why:** Testability, reusability (from Kitchen Staff, WebSockets), and clear separation — Waiters serve; Managers decide.

**Trade-off:** Extra indirection. For very simple CRUD, it can feel like overkill. For orders (validation, pricing, handing tickets to the Kitchen), it pays off.

### 3. Door Guards Separate from Filing Cabinet

**Decision:** Pydantic schemas for API; SQLAlchemy models for persistence.

**Why:** Security (the Door Guards never let `hashed_password` leave the building), flexibility (the API contract can evolve independently of the Filing Cabinet), and validation at the boundary.

**Trade-off:** Some duplication (e.g., both have `email`, `id`). The benefit of explicit API contracts outweighs this.

### 4. Maintenance Crew at Root

**Decision:** `scripts/` at project root, not inside the Open Restaurant.

**Why:** The Maintenance Crew are operational tools — they work outside the request-handling cycle. Different lifecycle, different entry point. They don't serve customers.

**Trade-off:** Scripts must add project root to `sys.path` (or run with `uv run` from root). Minor inconvenience for clearer structure.

### 5. Whiteboard as Shared Infrastructure

**Decision:** Config, database, Redis, security in `app/core/` (the Whiteboard).

**Why:** Single place for cross-cutting concerns. Everyone — Waiters, Managers, Kitchen Staff — consults the same Whiteboard. Easy to find and update.

**Trade-off:** The Whiteboard can grow large. If it does, consider splitting into `core/config`, `core/db`, `core/auth`, etc.

---

## Related Documentation

| Document | Purpose |
|----------|---------|
| `app/core/SECURITY_ARCHITECTURE.md` | Auth, JWT, password hashing, `get_current_user` |
| `app/schemas/ARCHITECTURE.md` | Pydantic schemas, validation, output filtering |
| `app/models/ARCHITECTURE.md` | ORM models, relationships, migrations |
| `BUILD_GUIDE.md` | Step-by-step build from scratch (in parent repo) |

---

## Summary

| Concept | Restaurant Analogy | Explanation |
|---------|-------------------|-------------|
| **app/** | 🏢 The Open Restaurant | The main building. Everything that runs with the server or workers. |
| **scripts/** | 🧰 Maintenance Crew | Run on demand, not part of request handling. Stock the menu, seed data. |
| **migrations/** | 🧰 Maintenance Crew | Rearrange the Filing Cabinet. Run by Alembic. |
| **tests/** | 🧰 Maintenance Crew | Quality checks. Run by pytest. |
| **app/api/routes/** | 🤵 The Waiters | HTTP entry points. Receive requests, return responses. |
| **app/schemas/** | 🚪 The Door Guards | Validate incoming data, filter outgoing data. |
| **app/services/** | 👔 The Managers | Business logic. Prepare instructions for the Filing Cabinet. |
| **app/models/** | 🗄️ The Filing Cabinet | How data is stored permanently. SQLAlchemy ORM. |
| **app/core/** | 🪧 The Whiteboard | Config, Redis, auth. Shared infrastructure. |
| **app/tasks/** | 🧑‍🍳 The Kitchen Staff | Celery workers. Heavy background jobs. |
| **Layer flow** | Customer → Door → Waiter → Manager → Filing Cabinet → Kitchen | Each role has a clear responsibility. |

The folder structure reflects **separation by lifecycle and responsibility**. When you add a new feature, ask: *Does it run with the server (Open Restaurant), on demand (Maintenance Crew), or in CI?* That answer determines where it lives.
