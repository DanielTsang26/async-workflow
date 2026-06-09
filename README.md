# Async Workflow 

##Fault Taxonomies: Mitigating Long-Running Pipeline Failures (The core problems)

To ensure enterprise-grade reliability and user trust, the architecture must defensively handle three primary failure modes common in asynchronous data pipelines:

* **Process Volatility (OOM Failures & Uncaught Exceptions)**
    * *The Problem:* Intensive data transformations (e.g., parsing massive clinical `.sas7bdat` or `.csv` files) can trigger Operating System Out-Of-Memory (OOM) kills or unhandled fatal exceptions. The background worker process terminates abruptly (`SIGKILL`) without an execution cleanup block, leaving the persistent database layer stranded in a perpetual `PROCESSING` state.
* **Execution Deadlocks (The Zombie Worker Pattern)**
    * *The Problem:* A background worker enters an infinite computational loop due to logical edge cases, or stalls indefinitely awaiting a response from an un-timeouted external storage API. The process remains technically alive and consuming resources, but it is entirely blocked from making progress. Because it is unresponsive, its active heartbeat trail ceases.
* **Transient Poison Payloads (Cyclic Queue Destabilization)**
    * *The Problem:* A user uploads a structurally malformed or corrupted clinical dataset. When a background worker dequeues the job, the malformed payload triggers an immediate crash. If the queue lacks a safety valve, the message is instantly re-queued and picked up by the next available worker, systematically crashing every instance in the worker pool in a destructive loop.
