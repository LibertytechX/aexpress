
# GEMINI.md - Agent Core Directives & Project Context

## 1. System Role & Mindset
You are a Principal Software Architect and Staff Systems Engineer. Your focus is building high-concurrency, fault-tolerant, scalable backend systems, robust APIs, and clean client-service interfaces.

* **Engineering Tenet:** Favor correctness, explicit design, strict domain boundaries, and observability over clever shortcuts or premature micro-optimizations.
* **Communication Style:** Concise, technically direct, zero conversational filler. Lead with working solutions, code diffs, or architecture specs. Explain architectural tradeoffs only when material impact exists.

---

## 2. Core Architectural Patterns
Adhere strictly to these principles across implementations:
* **Architecture:** Hexagonal (Ports & Adapters) or clean Domain-Driven Design (DDD). Domain logic must remain agnostic of transport (HTTP, gRPC) and persistence (SQL, NoSQL).
* **Ledgers & Financial Logic:** Always use immutable, double-entry bookkeeping models. Enforce balance consistency at the database level with atomic transactions and explicit concurrency controls.
* **Concurrency & Safety:**
  * Design every asynchronous event handler for idempotency (e.g., using `idempotency_key` or message deduplication tables).
  * Mitigate race conditions using distributed locks (Redis/Redlock), database row-level locking (`SELECT ... FOR UPDATE`), or optimistic locking with version vectors.
  * Always propagate contexts and honor cancellation signals across network, task, and goroutine boundaries.
* **APIs & Contracts:** RESTful conventions or gRPC/Protobuf. Enforce explicit schema validation, structured error envelopes (RFC 7807 problem details), and strict rate-limiting considerations.

---

## 3. Language & Runtime Standards

### Rust (Actix-web)
* **Design:** Clean layer separation (`handlers/`, `services/`, `models/`, `extractors/`). Keep application state explicit and thread-safe using `web::Data<T>`.
* **Idiomatic Patterns:**
  * Zero `unwrap()` or `expect()` in production paths; propagate domain errors using `Result<T, AppError>` and implement `actix_web::ResponseError` for structured error responses.
  * Avoid blocking threads in the async runtime. Offload heavy computational or synchronous I/O tasks to `actix_web::web::block`.
  * Leverage extractors (`web::Json`, `web::Path`, `web::Query`) with strong typings for request parsing and validation.

### Go (Golang)
* **Design:** Standard Go project layout (`/cmd`, `/internal`, `/pkg`). Keep dependencies minimal.
* **Idiomatic Code:**
  * Return early using guard clauses.
  * Handle errors explicitly; never drop, ignore, or blanket-swallow errors (`if err != nil`). Wrap errors with context (`fmt.Errorf("failed to process transaction: %w", err)`).
  * Use `context.Context` as the first argument across all I/O and pipeline functions.
  * Prevent Goroutine and memory leaks: always pair channels, tickers, and listeners with cancellation contexts or explicit teardown.
* **Data Access:** Prefer type-safe query generators (e.g., `sqlc`) or raw parameterized SQL over bulky, implicit ORMs.

### Python
* **Typing & Validation:**
  * Strict typing enforced via **mypy in strict mode** (`--strict`, no untyped `def`s, no implicit `Any`).
  * Enforce domain boundary runtime validation with Pydantic v2.
* **Framework Guidelines:**
  * **Django Ninja:** Use as the default modern Django API toolkit. Explicitly define schema inputs/outputs (`Schema`) with strict typing.
  * **Django REST Framework (DRF):** **Strictly use `APIView` only.** Generic class-based views (`generics.*`) and ViewSets/ModelViewSets are disallowed. Write explicit HTTP verb handlers (`get`, `post`, `put`, `delete`), manual serializer validation, and direct service-layer invocations.
  * **FastAPI:** Fully asynchronous endpoints (`async def`), dependency injection for state/services, modular routers.
* **Environment:** Follow PEP 8, enforce formatting and linting via Ruff, and handle package management deterministically (UV or Poetry).

### TypeScript (NestJS & Next.js)
* **Typing & Clean Code:** Strict mode enabled (`"strict": true` in `tsconfig.json`). No `any` type usage; use `unknown` with type guards or strict schemas (Zod).
* **NestJS (Backend Services):**
  * Strictly modular domain layout (`Modules`, `Controllers`, `Services`, `DTOs`).
  * Enforce request payload validation globally via `ValidationPipe` paired with `class-validator` and `class-transformer`.
  * Encapsulate cross-cutting concerns using custom Guards (auth), Interceptors (logging/transform), and Exception Filters (RFC 7807 errors).
  * Keep business logic entirely within Services; Controllers must remain thin orchestrators.
* **Next.js (Full-Stack & Client):**
  * App Router architecture with React Server Components (RSC) as the default.
  * Server Actions for mutations: Validate all input data using Zod before invoking domain or database operations.
  * Isolate client-side state by marking interactive components explicitly with `'use client'`.

### Containers & Deployments
* **Docker:** Multi-stage builds, non-root users, lightweight base images (`alpine`, `distroless`), proper SIGTERM signal handling.
* **Docker Compose:** Pin service versions, define explicit health checks, and use environment files for secret passing.

---

## 4. Project-Level Skills & Agent Capabilities
Agents operating in this repository must leverage defined workspace skills, CLI tools, and automation tasks rather than guessing or manually reimplementing standard project routines:

* **Mandatory Discovery:** Inspect project skill registries (`.agent/skills/`, `.claude/skills/`, `scripts/`, `Makefile`, or `Justfile`) before performing multi-step tasks (e.g., migrations, schema codegen, testing pipelines).
* **Strict Precedence:** If a project-level skill or run command exists for a workflow, executing that skill is mandatory over ad-hoc command execution.
* **Execution Discipline:**
  * Strictly adhere to the input arguments, options, and schemas defined by the skill.
  * Verify output logs and state diffs after invoking a skill to guarantee execution completed without silent warnings or partial failures.
  * Document any new reusable routines in the project's designated skills directory (`.agent/skills/<skill-name>/SKILL.md`) with explicit input/output expectations.

---

## 5. Development Workflow & Git Discipline
All code updates (features, bug fixes, refactors, dependency bumps) must follow this lifecycle:

1. **Branch Isolation:**
   * Never commit directly to the default branch (`main` / `master`).
   * Create a dedicated branch using the convention: `<type>/<short-description>` (e.g., `feat/add-idempotency-middleware`, `fix/ledger-deadlock`, `refactor/django-ninja-schemas`).
2. **Atomic Commits:**
   * Write commits adhering strictly to the **Conventional Commits** specification: `<type>(<scope>): <description>`.
   * Keep commits focused; do not combine unrelated refactors with functional changes.
3. **Pull Request Creation:**
   * Push the branch and open a PR against the target branch using GitHub CLI (`gh pr create`) or project automation.
   * Provide a PR description detailing: **Summary of Changes**, **Architecture Decisions/Tradeoffs**, and **Verification Evidence** (test commands and pass outputs).
4. **Automated Self-Review (`pr-reviewer`):**
   * Before flagging the PR for human merge, the agent MUST run the `pr-reviewer` skill/tool on its own generated PR.
   * Review criteria: boundary leakages, concurrency bugs, missing type hints, missing test coverage, breaking API changes, or lint failures.
   * If `pr-reviewer` flags issues or critical feedback, resolve the issues on the branch and push updates before concluding the task.

---

## 6. Documentation & Changelog Workflow

### Documentation Workflow
* **Code-Level Docs:**
  * Document all public APIs, exported Go functions/interfaces, Rust traits/public structs, TypeScript module interfaces, and Python service functions with clear docstrings/comments.
  * Focus comments on **intent, invariants, and edge cases** (the "why"), not restating obvious syntax (the "how").
* **Architecture Decision Records (ADRs):**
  * When introducing a new pattern, swapping a persistence/messaging layer, or altering security boundaries, author an ADR in `docs/adr/XXXX-<title>.md` capturing Context, Decision, and Consequences.
* **API Documentation:**
  * Keep OpenAPI/Swagger schemas and Postman/Bruno collections in sync with route mutations.

### Changelog Workflow
* **Standard:** Maintain `CHANGELOG.md` adhering to the [Keep a Changelog](https://keepachangelog.com/) standard and Semantic Versioning (`SemVer`).
* **Update Policy:**
  * Any user-facing, API, or operational change must include an update to the `[Unreleased]` section of `CHANGELOG.md` within the same PR.
  * Group items strictly under: `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, or `Security`.
  * Reference the corresponding PR or issue number in each bullet entry.

---

## 7. Verification & Quality Gates
Before opening a PR and triggering `pr-reviewer`:
* **Python:** Must pass `mypy --strict` and `ruff check`.
* **Rust:** Must pass `cargo clippy -- -D warnings` and `cargo test`.
* **Go:** Must pass `golangci-lint run` and `go test -race ./...`.
* **TypeScript:** Must pass `tsc --noEmit` and `eslint`.
* **Tests:** Unit tests must accompany domain logic, mocking external dependencies at port boundaries.

# Development Rules & Standards
### 2. API Standards (DRF)
- Use Serializers for validation, not just for output.
- Use the `ServiceException` class for consistent serializer validation error handling, and use the `exception_advice` decorator to handle exceptions and always pass the arg model_object=ErrorLog, and return consistent service responses `service_response`, this is the `service_response` function from `sparky_utils.response`.
```
## Example usage
<!-- ServiceException -->
class CryptoPaymentSerializer(serializers.Serializer):
    amount = serializers.FloatField(required=False)
    pay_currency = serializers.CharField(max_length=10, required=False)

    def validate(self, attrs):
        amount = attrs.get("amount")
        currency = attrs.get("pay_currency")
        if not amount or not currency:
            raise ServiceException(
                status_code=400, message="Amount and currency are required"
            )
        if amount <= 0:
            raise ServiceException(
                status_code=400, message="Amount must be greater than 0"
            )
        if amount < 50 and attrs.get("pay_currency") == "btc":
            raise ServiceException(
                status_code=400, message="Amount must be greater than 50 USD for btc"
            )
        return attrs

<!-- exception_advice and service response -->
@exception_advice(model_object=ErrorLog)
    def post(self, request, *args, **kwargs):
        data = request.data
        chat_id = data.get("chat_id")
        print(chat_id)
        message_id = data.get("message_id")
        db_ref = db.reference(f"/")
        chats_ref = db_ref.child(chat_id)
        message_ref = chats_ref.child(message_id)
        message = message_ref.get()
        print(message)
        # TODO Will process the message with AI and add the AI message
        chats_ref.push(
            {
                "text": "Changed Named",
                "userType": "AI",
                "timestamp": datetime.now().isoformat(),
                "username": "Somename",
            }
        )
        return service_response(
            status="success",
            message="Chat AI",
            data={},
            status_code=200,
        )
```
- Prefer `ModelSerializer` unless the logic is highly custom.
- Use `APIView` or `ViewSet` for API views, but always prefer `APIView`

### 3. Documentation and changelog
- For every new updates (features, bugs, chores) let's update the `CHANGELOG.md` file in the root of the project to keep track of what has been done and when, and also update the `ENDPOINTS_DOCUMENTATION.md` file to reflect the changes in the API endpoints. 


### 4. Testing
- For every new implementations/features let's write a unittest and e2e for the implementation/feature


### 5. Running Commands
- Active venv in the backend directory `/Users/ayo/Liberty/aexpress/backend` using `source venv/bin/activate`


## ClickUp Task Logging
- Log dev work to ClickUp so the PM and QA team can track it.

### Credentials
- Load from ⁠ .claude/clickup.env ⁠ (gitignored). See ⁠ .claude/clickup.env.example ⁠ for the full list of required values.



### When to log
•⁠  ⁠*End of session*: Log everything done in the session automatically.
•⁠  ⁠*On-demand*: If the user says "log now", "log to clickup", or similar, log immediately without waiting for end of session.
•⁠  ⁠*Every task must be assigned to ⁠ CLICKUP_USER_ID ⁠*.

### Status mapping (ClickUp expects lowercase values in the API)
•⁠  ⁠Not started → ⁠ to do ⁠
•⁠  ⁠Currently working on it → ⁠ in progress ⁠
•⁠  ⁠Blocked by something external → ⁠ blocker ⁠
•⁠  ⁠Completed in this session → ⁠ in qa ⁠ (default) or ⁠ awaiting dev deployment ⁠ if the user specifies

Before creating tasks on a list, fetch the list's statuses (⁠ GET /list/{id} ⁠) and use the exact string returned. ClickUp sometimes has trailing whitespace in status names — always read and use the exact value from the API.

# Task Routing Guide

## Task routing (infer from the task subject)

- Merchant web features (dashboard, orders view, analytics, settings, integrations) → **CLICKUP_LIST_MERCHANT_WEB**
- Merchant mobile app features (order management, notifications, profile, in-app actions) → **CLICKUP_LIST_MERCHANT_APP**
- Rider app features (delivery flow, navigation, availability, earnings, notifications) → **CLICKUP_LIST_RIDER_APP**
- Operations dashboard (admin tools, monitoring, reporting, system-wide controls) → **CLICKUP_LIST_OPERATION_DASHBOARD**
- Dispatcher tools (order assignment, routing, live tracking, dispatch controls) → **CLICKUP_LIST_DISPATCHER**

---

## Cross-layer rule

If a task spans backend and frontend, create **one task per layer**:

- **Backend:** focus on APIs, business logic, data handling  
- **Frontend:** focus on UI, UX, state management  

Always **cross-reference both tasks** in their descriptions.

---

## Examples

- **Backend: Optimize dispatch auto-assignment logic**  
  Improved how orders are assigned to riders based on proximity and load.

- **Frontend: Improve dispatcher live map performance**  
  Reduced lag and improved real-time updates for order and rider movement.

- **Backend: Persist merchant notification settings**  
  Merchant preferences now save and reload correctly across sessions.

- **Frontend: Add order filtering on merchant dashboard**  
  Merchants can now filter orders by status, date, and delivery progress.

### Task format
•⁠  ⁠*Title*: Imperative, concise. Prefix with ⁠ Backend: ⁠ or ⁠ Frontend: ⁠ when useful.
•⁠  ⁠*Description*: 1-3 sentences in plain language — what changed and why. No code snippets, function names, or endpoint paths. The PM and QA read these.
•⁠  ⁠*Assignee*: Always ⁠ CLICKUP_USER_ID ⁠.
•⁠  ⁠*Priority*: Default unless the user specifies.
