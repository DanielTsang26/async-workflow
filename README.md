# Async Workflow 

## Fault Taxonomies: Mitigating Long-Running Pipeline Failures (The core problems)

To ensure enterprise-grade reliability and user trust, the architecture must defensively handle three primary failure modes common in asynchronous data pipelines:

* **Process Volatility (OOM Failures & Uncaught Exceptions)**
    * *The Problem:* Intensive data transformations (e.g., parsing massive clinical `.sas7bdat` or `.csv` files) can trigger Operating System Out-Of-Memory (OOM) kills or unhandled fatal exceptions. The background worker process terminates abruptly (`SIGKILL`) without an execution cleanup block, leaving the persistent database layer stranded in a perpetual `PROCESSING` state.
* **Execution Deadlocks (The Zombie Worker Pattern)**
    * *The Problem:* A background worker enters an infinite computational loop due to logical edge cases, or stalls indefinitely awaiting a response from an un-timeouted external storage API. The process remains technically alive and consuming resources, but it is entirely blocked from making progress. Because it is unresponsive, its active heartbeat trail ceases.
* **Transient Uncertain Payloads (Cyclic Queue Destabilization)**
    * *The Problem:* A user uploads a structurally malformed or corrupted clinical dataset. When a background worker dequeues the job, the malformed payload triggers an immediate crash. If the queue lacks a safety valve, the message is instantly re-queued and picked up by the next available worker, systematically crashing every instance in the worker pool in a destructive loop.

## Architectural Draft Markdown

Core concept MVP vs. Production Ready

<img width="867" height="546" alt="image" src="https://github.com/user-attachments/assets/94311d6d-4322-4941-bb68-b04b4b2ea00f" />

---
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

---

### Architectural Mapping (Concept) and Indepth Overview of Prototype:

| Component in Prototype Code | Enterprise Cloud Equivalent | Architectural Role & Technical Defense |
| :--- | :--- | :--- |
| `self._jobs` (Dictionary) | **PostgreSQL Database** / **Redis Cache** | **Central Transaction Ledger & State Machine:** Serves as the immutable single source of truth for all multi-tenant workflow states, preventing race conditions. |
| `self.DEFAULT_MAX_RETRIES` | **AWS Systems Manager Parameter Store** / **HashiCorp Vault** | **Policy Threshold Bounds:** Centralizes runtime configuration boundaries to eliminate "magic numbers" and govern system-wide resilience constraints. |
| `start_worker_loop()` | **Containerized Daemon** (Docker on AWS ECS / Kubernetes Pod) | **Distributed Compute Consumer Node:** Runs continuously as an isolated background process, independently polling the state ledger to consume and process data workloads. |
| `start_monitoring()` | **Sidecar Proxy** / **Scheduled AWS CloudWatch Event** | **Autonomous Infrastructure Janitor:** Functions as a decoupled liveness sweeper that detects missed worker heartbeat windows and triggers automated circuit-breaker remediation. |
| `failure_log` array | **Elasticsearch Stack (ELK)** / **Datadog Logs** | **Immutable Compliance Audit Trail:** Chronologically captures and stores contextual error signatures within the job data structure to satisfy **FDA 21 CFR Part 11** forensic auditing requirements. |

### What Makes a Job "Stuck"?
In a production system, a job gets stuck when a background worker picks up a file to process, but then crashes completely (like running out of memory or losing power). Because the worker is dead, it can't update the system to say "I broke." The job just sits there marked as PROCESSING forever, and the user is left staring at an infinite loading wheel.

### How the script Detects and Fixes It (Step-by-Step)

1. The Notebook (src/ledger.py):
This is just a central database ledger that keeps track of every job's status. When a job starts, it's marked as PENDING. When a worker grabs it, the status changes to PROCESSING.

2. The Worker (src/worker.py):
The worker picks up PENDING jobs and starts processing them in 5 incremental stages. Every single time it completes a stage, it writes the current time into the ledger. This is the heartbeat. It's the worker constantly saying, "I'm still alive, and I'm still working."

3. The Monitor (src/monitor.py):
This is the actual stuck job detector. It runs on an independent loop every 2 seconds and checks the ledger. It looks at the current time and subtracts the last heartbeat time recorded by the worker.

   If that time difference is greater than 4 seconds, the monitor knows the worker has stopped checking in.

   It sounds the alarm: "Job is stuck!"

4. The Self-Healing Fix
The moment the monitor detects a stuck job, it automatically intervenes. It changes the job's status back to PENDING and adds 1 to its retry counter. Because a healthy worker loop is always polling the ledger, a working node will instantly see the reset job, grab it, and successfully finish it.

If a job gets stuck too many times (breaching max_retries), the script realizes the file itself might be corrupted and moves it to a FAILED state so it doesn't loop forever.

---

### Tool Disclosure:

Tools that were used was Claude AI, Github Copilot, Python, Python Libraries such as Asyncio, Logging, and Time.
---
### Future Iterations:

Database Persistence Layer
Dedicated Distributed Message Broker (Decoupling Core Tasks)
Advanced Anomaly Detection (Predictive Monitoring)

PHASE 1 (Current) ---->      PHASE 2 (Short-Term) ---->   PHASE 3 (Production)
 In-Memory Prototype        SQL Database Storage         Decoupled Redis Broker
 Local Asyncio Loops        Docker Containerization      Horizontal Microservice

