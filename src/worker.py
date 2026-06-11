import asyncio
import logging

logger = logging.getLogger("Engine.Worker")

class BackgroundWorker:

    def __init__(self,worker_id:str, ledger):
        self.worker_id = worker_id
        self.ledger = ledger
        self.is_healthy = True

    async def start_worker_loop(self):
        logger.info(f"Worker [{self.worker_id}] initialized and polling for jobs...")
        while True:
            await asyncio.sleep(1)

            for job_id, meta in list(self.ledger._jobs.items()):
                if meta["status"] in ["PENDING", "STUCK"] and self.is_healthy:
                    asyncio.create_task(self.run_workflow(job_id))

    async def run_workflow(self, job_id: str):
        if not self.ledger.claim_job(job_id):
            return

        try:
            for chunk in range(1, 6):
                if not self.is_healthy:
                    logger.error(f"Worker[{self.worker_id}] experienced fatal crash mid job.")

                    while True:
                        await asyncio.sleep(1)

                await asyncio.sleep(1)
                self.ledger.update_signal(job_id)
                logger.info(f"Worker[{self.worker_id}] processing chunk {chunk}/5 for Job {job_id}...")

            self.ledger.mark_completed(job_id)
        except Exception as e:
            self.ledger.handle_failure(job_id, str(e))



