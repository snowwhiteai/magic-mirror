# Project Planning

Initial Planning checklist for beginning phase.

NOTE: This is done in help with Gemini. Somethings may need to change.
---

### **Phase 0: Prerequisite - Pipecat Cloud API Investigation**

**Goal:** Confirm necessary API capabilities for dynamic agent management and updates.

**Actions:**

* [x] Thoroughly read the latest Pipecat Cloud API documentation.
* [x] Identify specific endpoints and request/response formats for:
    * Agent Provisioning (Create/Delete): How is initial configuration passed? Confirm `FrameContext` update mechanism if that's the intended path.
    * Agent Identification: How to get a stable `instance_id` or equivalent upon creation? Validate the plan to store this mapping in our database.
    * Dynamic Updates: Pinpoint the *exact* endpoint and payload format for context updates without agent restarts. Verify if full configuration updates without restart are possible.
    * Agent Status Querying: Confirm if an endpoint exists to check if a specific agent instance is running/ready/error state.
* [x] Understand Authentication: Confirm preferred method (API Keys, OAuth2, etc.). Plan integration with Auth0 or similar identity provider, considering billing links later.
* [x] Contact Pipecat Support: Clarify any ambiguities regarding multi-tenancy support, dynamic update mechanisms, status querying, and rate limits, especially if documentation is insufficient.

**Outcome:** YES. For our current use cases, it seems to be the right choice with minimal infra overheads and low latency for the bots.

---

### **Phase 1: Foundational Setup**

**Goal:** Establish the project structure, core dependencies using optimized libraries, and basic configurations.

**Actions:**

* [ ] Install core, high-performance dependencies:
    * Web Framework: `fastapi`
    * ASGI Server: `uvicorn[standard]` (includes performance boosts like `uvloop`, `httptools`), `gunicorn` (as a production process manager for Uvicorn).
    * Database ORM/Toolkit: `sqlmodel` (combines Pydantic and SQLAlchemy, great with FastAPI).
    * Async DB Driver: `asyncpg` (for PostgreSQL - highly recommended for performance).
    * Redis Client: `redis[hiredis]` (for async Pub/Sub and potential caching, hiredis provides C-based speedups).
    * HTTP Client: `httpx` (modern, async/sync, HTTP/2 support).
    * Configuration: `pydantic-settings` (replaces `python-dotenv` for robust settings management integrated with Pydantic/FastAPI).
    * Schema/Validation: `pydantic` (comes with FastAPI/SQLModel).
    * Retries: `tenacity`.
    * Logging: `structlog` (for structured, production-ready logging).
    * YAML Parsing: `PyYAML` (if config involves YAML).
* [ ] Set up project structure (e.g., `config_sync_service/app/`, `app/main.py`, `app/core/`, `app/db/`, `app/mq/`, `app/pipecat_client/`, `app/processing/`, `app/schemas/`, `app/api/` for health endpoints, `tests/`).
* [ ] Configure `structlog` for JSON-formatted logs suitable for log aggregation systems.
* [ ] Define configuration loading using `pydantic-settings` (loading from `.env` files and environment variables) for DB URL, Redis URL, Pipecat API Key/Endpoint, Pub/Sub channel names, etc. Define a `Settings` model in `app/core/config.py`.

---

### **Phase 2: Database Interaction Module (`app/db/`)**

**Goal:** Implement async functions for robust database interactions using PostgreSQL via asyncpg and SQLModel/SQLAlchemy.

**Actions:**

* [ ] Define `SQLModel` models (or SQLAlchemy Core/ORM models) in `app/db/models.py` for `Agent` and `AgentConfiguration` tables (including fields like `pipecat_cloud_instance_id`, `sync_status`, `last_error_message`, relationships).
* [ ] Define Pydantic schemas in `app/schemas/` for data validation and API responses, potentially reusing or inheriting from SQLModel models.
* [ ] Implement `init_db_pool` (or equivalent setup, possibly managed within FastAPI lifespan) to create and manage the `asyncpg` connection pool.
* [ ] Create async database CRUD functions (e.g., in `app/db/crud.py` or repositories):
    * [ ] `get_agent_details(db_session, agent_id: UUID) -> Optional[Agent]`
    * [ ] `get_active_configuration(db_session, agent_id: UUID) -> Optional[AgentConfiguration]`
    * [ ] `get_llm_context_data(db_session, agent_id: UUID) -> Optional[dict]` (extract specific JSONB field part)
    * [ ] `update_agent_sync_status(db_session, agent_id: UUID, status: str, error_message: Optional[str] = None)`
    * [ ] `create_agent(...)`, `update_agent(...)`, etc. as needed.
* [ ] Ensure database sessions are managed correctly (e.g., using FastAPI dependencies or context managers).

---

### **Phase 3: Message Queue Listener (`app/mq/`)**

**Goal:** Implement an async listener for Redis Pub/Sub to receive update notifications.

**Actions:**

* [ ] Implement `redis_listener` async function or class using `redis-py`'s async `pubsub` interface.
* [ ] Configure Redis connection pool for efficient connection reuse.
* [ ] Implement subscription logic to the designated channel (e.g., `agent_config_updates`).
* [ ] Implement robust JSON message parsing and validation (using Pydantic schemas defined in `app/schemas/`). Expected format: `{"agent_id": "...", "version": ..., "change_type": "CONTEXT_UPDATE" | "FULL_SYNC" | "PROVISION" | "DEPROVISION"}`.
* [ ] Implement error handling for Redis connection loss/errors (with retries using `tenacity`).
* [ ] Decide how the listener runs: Likely as a background task initiated during the FastAPI application startup (`lifespan` context manager in `app/main.py`).
* [ ] Pass validated messages to the core processing module (Phase 5).

---

### **Phase 4: Pipecat Cloud API Client (`app/pipecat_client/`)**

**Goal:** Develop a robust, async, and reusable client for the Pipecat Cloud API using `httpx`.

**Actions:**

* [ ] Create a class `PipecatCloudClient`.
* [ ] Initialize `httpx.AsyncClient` within the class, potentially configured with base URL, default headers, and timeouts. Consider managing the client lifecycle (e.g., created on app startup, closed on shutdown).
* [ ] Implement authentication handling (e.g., injecting API key into headers).
* [ ] Implement async methods based on Phase 0 findings:
    * [ ] `provision_agent(config: dict) -> Optional[str]`
    * [ ] `deprovision_agent(instance_id: str) -> bool`
    * [ ] `send_context_update(instance_id: str, context_payload: dict) -> bool`
    * [ ] `get_agent_status(instance_id: str) -> Optional[str]`
    * [ ] `update_full_config(instance_id: str, config: dict) -> bool` (if supported)
* [ ] Implement comprehensive error handling: Check status codes, parse potential error responses from Pipecat, raise custom exceptions (e.g., `PipecatApiError`, `PipecatRateLimitError`).
* [ ] Integrate `tenacity` for automatic retries on transient network errors or specific Pipecat API error codes (e.g., 5xx).

---

### **Phase 5: Core Processing Logic (`app/processing/`)**

**Goal:** Orchestrate the synchronization process triggered by messages from the queue.

**Actions:**

* [ ] Implement the main async processing function `process_update_message(message: dict, db: AsyncSession, pc_client: PipecatCloudClient)`. Note: `db` session and `pc_client` instance should ideally be passed in (dependency injection).
* [ ] Extract `agent_id` and `change_type` from the validated message.
* [ ] Fetch `agent_details` (including `pipecat_cloud_instance_id`) from the DB using `get_agent_details`. Handle `AgentNotFound` errors gracefully (log, potentially update status if possible, or send to DLQ).
* [ ] Implement the core decision logic based on `change_type`:
    * [ ] **CONTEXT_UPDATE:** Fetch context -> Format -> Call `pc_client.send_context_update` -> Update DB status.
    * [ ] **FULL_SYNC / PROVISION:** Fetch full config -> Format -> Call `pc_client.provision_agent` or `pc_client.update_full_config` -> Update DB with `instance_id` (if new) and status.
    * [ ] **DEPROVISION:** Call `pc_client.deprovision_agent` -> Update DB status (e.g., `DELETED`, `PENDING_DELETE`).
* [ ] Wrap all external calls (DB, Pipecat API) in `try...except` blocks.
* [ ] Use `tenacity` within this layer *strategically* if retrying the entire process makes sense, otherwise rely on retries within the DB/API client layers.
* [ ] Log detailed errors at each step.
* [ ] Update the agent's sync status (`SYNCED`, `ERROR_SYNC`, `ERROR_DEPROVISIONING`, etc.) and `last_error_message` in the database upon success or failure.

---

### **Phase 6: Error Handling & Reliability**

**Goal:** Ensure the service is resilient to failures and operates reliably.

**Actions:**

* [ ] **Retries:** Confirm `tenacity` is used effectively in the Pipecat client (Phase 4) and DB interactions (implicitly via connection pool handling, explicitly if needed for specific operations) for transient errors. Configure exponential backoff and jitter.
* [ ] **Dead Letter Queue (DLQ):** Implement logic in the Redis listener (Phase 3) or processing logic (Phase 5) to move messages that repeatedly fail (after retries) to a designated Redis list (e.g., `agent_config_updates_dlq`). This prevents blocking the main queue.
* [ ] **Specific Exception Handling:** Define and use custom exceptions for different failure modes (e.g., `DbError`, `PipecatApiError`, `InvalidMessageFormatError`, `ConfigurationError`). Catch these specifically in the processing logic for appropriate handling and status updates.
* [ ] **Graceful Shutdown:** Implement signal handlers (SIGINT, SIGTERM) within the FastAPI application (or the process manager like Gunicorn) to:
    * Stop the Redis listener from accepting new messages.
    * Allow currently processing tasks to complete (with a timeout).
    * Close the Pipecat `httpx.AsyncClient`.
    * Close the database connection pool.
    * Close the Redis connection pool.
* [ ] **Structured Logging:** Ensure `structlog` provides detailed context (agent_id, change_type, error details) in logs for easier debugging.

---

### **Phase 7: Health & Monitoring (`app/api/`)**

**Goal:** Provide HTTP endpoints for observability, health checks, and Kubernetes probes using FastAPI.

**Actions:**

* [ ] Create a FastAPI router (e.g., `app/api/monitoring.py`) for health endpoints.
* [ ] Implement `GET /healthz`: Basic liveness check. Returns `200 OK` with `{"status": "ok"}` if the FastAPI app is running.
* [ ] Implement `GET /readyz`: Readiness check.
    * [ ] Check database connectivity (e.g., execute a simple `SELECT 1`).
    * [ ] Check Redis connectivity (e.g., `PING` command).
    * [ ] (Optional) Check basic connectivity/authentication to Pipecat Cloud API (maybe cache a successful auth check periodically).
    * [ ] Return `200 OK` `{"status": "ready"}` only if all checks pass, otherwise `503 Service Unavailable`.
* [ ] (Optional) Implement `GET /status`: Provide more detailed internal metrics (e.g., messages processed, DLQ size, last error timestamp) for internal monitoring. Protect this endpoint if it exposes sensitive data.
* [ ] Integrate the monitoring router into the main FastAPI application (`app/main.py`).

---

### **Phase 8: Deployment**

**Goal:** Package the service into a container and configure deployment.

**Actions:**

* [ ] Create a multi-stage `Dockerfile`:
    * Stage 1: Build dependencies using Poetry.
    * Stage 2: Copy application code and built dependencies into a slim Python base image (e.g., `python:3.11-slim`).
    * Configure non-root user.
    * Set `CMD` or `ENTRYPOINT` to run the application using `gunicorn` managing `uvicorn` workers (e.g., `gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000`). Adjust worker count based on resources/needs.
* [ ] Build and push the Docker image to a container registry (e.g., Docker Hub, GCR, ECR, ACR).
* [ ] Create Kubernetes Deployment and Service YAML manifests (or Terraform/Pulumi/etc.).
* [ ] Configure environment variables (DB URL, Redis URL, Pipecat secrets, etc.) using Kubernetes Secrets and pass them to the Deployment.
* [ ] Configure liveness (`/healthz`) and readiness (`/readyz`) probes in the Deployment manifest, pointing to the endpoints created in Phase 7. Set appropriate initial delays, periods, and timeouts.
* [ ] Set up Horizontal Pod Autoscaler (HPA) if needed, based on CPU/memory usage or custom metrics.
* [ ] [Optional] Set up CI/CD pipeline (e.g., GitHub Actions, GitLab CI) to automate testing, building, and deployment.

---

### **Phase 9: Testing**

**Goal:** Implement comprehensive tests to ensure correctness, robustness, and reliability.

**Actions:**

* [ ] **Unit Tests:** Use `pytest`. Mock dependencies (`db` functions, `redis` client, `httpx` client using `unittest.mock` or `pytest-mock`) to test individual functions and classes in isolation (e.g., testing processing logic branches, utility functions, schema validation).
* [ ] **Integration Tests:**
    * Use `pytest`.
    * Test interactions between components (e.g., does the listener correctly call the processor? Does the processor interact with DB mocks correctly?).
    * Use FastAPI's `TestClient` (with `httpx` backend) to test the health/monitoring API endpoints (`/healthz`, `/readyz`).
    * Use libraries like `pytest-httpx` to mock external Pipecat API calls.
    * Potentially use test containers (`testcontainers-python`) to spin up real PostgreSQL and Redis instances for more realistic integration testing of DB and MQ modules.
* [ ] **End-to-End Tests (Optional/Complex):** If feasible and a staging Pipecat environment is available, simulate the full flow: publish a message to Redis -> verify the service processes it -> check the (mocked or real staging) Pipecat agent state -> verify the DB status update.
* [ ] **Stress Tests (Optional):** Simulate high load (many messages) to check performance and resource usage.
* [ ] Ensure tests cover edge cases identified in the original plan (API down, DB down, invalid messages, rate limits, etc.).

---
