import asyncio
import time
import logging


logger = logging.getLogger("Engine.CLI")

async def interactive_cli(ledger, worker):
    print("\n" + "="*50)
    print("     STUCK JOB DETECTOR WITH SELF-HEALING SIMULATION COMMANDS")
    print("  'submit' - Run a new clinical workflow pipeline")
    print("  'crash'  - Inject fatal OOM exception/freeze worker")
    print("  'status' - Print live, atomic ledger state dashboard")
    print("  'exit'   - Stop the runtime engine")
    print("="*50 + "\n")

    job_counter = 1
    while True:
        command = await asyncio.to_thread(input, "yesod-admin> ")
        command = command.strip().lower()

        if command == "submit":
            job_id = f"job_00{job_counter}"
            ledger.register_job(job_id, "statistical_derivation_v2", "pharma_corp", f"uploads/{job_id}.sas7bdat")
            asyncio.create_task(worker.run_workflow(job_id))
            job_counter += 1

        elif command == "crash":
            worker.is_healthy = False
            logger.warning(" INJECTING CRASH: Worker node health state set to UNHEALTHY.")

        elif command == "status":
            print(f"\n--- ATOMIC LEDGER STATUS CHECK ({time.strftime('%H:%M:%S')}) ---")
            statuses = ledger.get_all_statuses()
            if not statuses:
                print("No jobs currently running or queued.")
            for jid, status in statuses.items():
                print(f" * {jid}: [{status}]")
            print("-" * 45 + "\n")

        elif command == "exit":
            print("Stopping core engine execution. Goodbye.")
            break