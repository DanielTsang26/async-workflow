import asyncio
import logging

logger = logging.getLogger("Engine.Monitor")

class StatusMonitor:
    def __init__(self,ledger, timeout_seconds: float = 4.0):
        self.ledger = ledger
        self.timeout_seconds = timeout_seconds
    
    async def start_monitoring(self):
        logger.info(f"Liveness Monitor active. Sweeping ledger state entries every 2 seconds.")
        while True:
            await asyncio.sleep(2)
            stuck_jobs = self.ledger.get_stuck_jobs(self.timeout_seconds)

            for job_id in stuck_jobs:
                logger.error(f"Liveness Monitor detected missing signal for Job {job_id}")
                self.ledger.handle_failure(job_id, "Signal timeout exceeded.")


