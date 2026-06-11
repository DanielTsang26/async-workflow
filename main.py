import asyncio
import logging
from src.ledger import JobLedger
from src.worker import BackgroundWorker
from src.monitor import StatusMonitor
from src.cli import interactive_cli

logging.basicConfig(
    level = logging.INFO,
    format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)

async def main():
    ledger = JobLedger()
    worker = BackgroundWorker(worker_id="Compute-Node-01", ledger=ledger)
    monitor = StatusMonitor(ledger=ledger, timeout_seconds=4.0)
    
    await asyncio.gather(
        monitor.start_monitoring(),
        worker.start_worker_loop(),
        interactive_cli(ledger,worker)
    )

if __name__ =="__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nEngine safely shutdown.")