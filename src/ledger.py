import time
import logging
from typing import Dict, Any

logger = logging.getLogger("Engine.Ledger")


class JobLedger:
    DEFAULT_MAX_RETRIES: int = 2
    
    def __init__(self):
        self._jobs: Dict[str, Dict[str, Any]] = {}

    def register_job(self, job_id: str, workflow_id: str, tenant_id: str, artifact_path:str ):
        self._jobs[job_id] = {
            "job_id": job_id,
            "workflow_id": workflow_id,
            "tenant_id": tenant_id,
            "artifact_path": artifact_path,
            "status":"PENDING",
            "last_heartbeat":time.time(),
            "retries":0,
            "max_retries":self.DEFAULT_MAX_RETRIES
        }
        logger.info(f"Job {job_id} registered in ledger [PENDING]")

    def claim_job(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if job and job["status"] in ["PENDING", "STUCK"]:
            job["status"] = "PROCESSING"
            job["last_signal"] = time.time()
            logger.info(f"Job {job_id} Claimed by worker node [PROCESSING]")
            return True
        return False
    
    def update_signal(self, job_id: str):
        if job_id in self._jobs:
            self._jobs[job_id]["last_signal"] = time.time()

    def mark_completed(self, job_id: str):
        if job_id in self._jobs:
            self._jobs[job_id]["status"] = "COMPLETED"
            logger.info(f"Job{job_id} successfully processed and audited [COMPLETED]")

    def handle_failure(self, job_id: str, reason: str):
        job = self._jobs.get(job_id)
        if not job:
            logger.error(f"Transaction Rejected: Attempted to fail non-existent Job ID {job_id}")
            return
        
        job["retries"] = job.get("retries", 0)
        max_retries = job.get("max_retries", self.DEFAULT_MAX_RETRIES)

        job["failure_log"] =  job.get("failure_log", [])
        job["failure_log"].append({"timestamp": time.time(), "error":reason})

        if job["retries"] < max_retries:
            self.execute_soft_recovery(job, job_id, reason, max_retries)
        else:
            self.execute_dlq_eviction(job, job_id, reason)
            

    def execute_soft_recovery(self, job: dict, job_id: str, reason: str, max_retries: int):
        job["retries"] +=1
        job["status"] = "PENDING"

        print(f"\n{'-'*60}\n"
              f"\033[93m[SYSTEM RECOVERY] Automated Remediation Triggered for {job_id}\033[0m\n"
              f"Reason: \033[91m{reason}\033[0m\n"
              f"Action: State reset to [PENDING] | Attempt {job['retries']}/{max_retries}\n"
              f"{'-'*60}\n")
        
        logger.warning(f"Job{job_id} recycled back to processing job pool.")
    
    def execute_dlq_eviction(self, job: dict, job_id: str, reason: str):
        job["status"] = "FAILED"

        print(f"\n{''*60}\n"
              f"\033[41m\033[97m CRITICAL SYSTEM FAILURE: {job_id} Breached Threshold Limits \033[0m\n"
              f"Terminal Error: {reason}\033[0m\n"
              f"Action: Quarantined to Dead Letter Queue (DLQ) for manual forensics.\n"
              f"{''*60}\n")
              
        logger.error(f"DLQ Eviction: Job {job_id} permanently quarantined.")


        



    def get_stuck_jobs(self, timeout_seconds: float) -> list:
        now = time.time()
        stuck = []
        for job_id, meta in self._jobs.items():
            if meta["status"] == "PROCESSING" and (now - meta["last_signal"]) > timeout_seconds:
                stuck.append(job_id)
        return stuck
    
    def get_all_statuses(self) -> dict:
        return {jid: data["status"] for jid, data in self._jobs.items()}
