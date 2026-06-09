# Async Workflow 

## Fault Taxonomies: Mitigating Long-Running Pipeline Failures (The core problems)

To ensure enterprise-grade reliability and user trust, the architecture must defensively handle three primary failure modes common in asynchronous data pipelines:

* **Process Volatility (OOM Failures & Uncaught Exceptions)**
    * *The Problem:* Intensive data transformations (e.g., parsing massive clinical `.sas7bdat` or `.csv` files) can trigger Operating System Out-Of-Memory (OOM) kills or unhandled fatal exceptions. The background worker process terminates abruptly (`SIGKILL`) without an execution cleanup block, leaving the persistent database layer stranded in a perpetual `PROCESSING` state.
* **Execution Deadlocks (The Zombie Worker Pattern)**
    * *The Problem:* A background worker enters an infinite computational loop due to logical edge cases, or stalls indefinitely awaiting a response from an un-timeouted external storage API. The process remains technically alive and consuming resources, but it is entirely blocked from making progress. Because it is unresponsive, its active heartbeat trail ceases.
* **Transient Poison Payloads (Cyclic Queue Destabilization)**
    * *The Problem:* A user uploads a structurally malformed or corrupted clinical dataset. When a background worker dequeues the job, the malformed payload triggers an immediate crash. If the queue lacks a safety valve, the message is instantly re-queued and picked up by the next available worker, systematically crashing every instance in the worker pool in a destructive loop.

## Architectural Draft Markdown

Core concept MVP vs. Production Ready

<img width="867" height="546" alt="image" src="https://github.com/user-attachments/assets/94311d6d-4322-4941-bb68-b04b4b2ea00f" />

## Technical Blueprint: Prototype Architecture & Strategic Tradeoffs

### Production Architecture Design

In a scaled enterprise environment, the heartbeat-and-lease pattern designed to prevent black-box workflow failures is distributed across an decoupled infrastructure stack:

* **API Web Gateway (FastAPI):** Ingests incoming clinical metadata asynchronously, enforces tenant-level rate limits, and immediately returns an HTTP `202 Accepted` response with a unique tracking token.
* **Persistent Ledger (PostgreSQL):** Enforces rigid data integrity, strict database schemas, and immutable auditing records necessary for regulatory clinical environments.
* **Message Broker & Cache (Redis):** Orchestrates background task distribution via Redis Lists/Streams, while simultaneously managing worker heartbeat timestamps utilizing native Key Expiration (TTL) policies.
* **Decoupled Payload Storage (AWS S3):** Hosts large clinical data files (`.sas7bdat`, `.csv`, `.xlsx`). The message broker never carries raw data payloads—only lightweight URI pointers—preventing memory saturation.

---

### The MVP Execution Strategy

While the distributed system outlined above represents the production design, a key requirement of early-stage infrastructure engineering is maximizing execution velocity without compromising logical correctness. 

For the 3-day challenge prototype, I made a conscious engineering decision to bypass the operational overhead of configuring separate database containers, network brokers, or third-party message queues on `localhost`. Instead, I engineered a fully self-contained, in-memory simulation script that isolates and demonstrates the exact math, logic, and state-machine behavior of the production recovery engine.

#### Minimalist Prototype Tech Stack
* **Language:** Python 3.10+ (Native ecosystem fit for clinical data science pipelines).
* **Concurrency Engine:** Standard Library `asyncio` (Simulates high-concurrency background message lines and decoupled, independent workers).
* **Volatile State Tracker:** Standard Python `dict` (Acts as the high-speed, in-memory state ledger to simulate the primary database).
* **Interface Layer:** Python Native CLI (Provides high-transparency, color-coded live logs mapping system events in real time).

