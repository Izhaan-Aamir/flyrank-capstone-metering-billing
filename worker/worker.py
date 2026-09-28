from queue import Queue

from worker.jobs import BillingJob


class BillingWorker:
    def __init__(self) -> None:
        self.queue: Queue[BillingJob] = Queue()

    def submit(self, job: BillingJob) -> None:
        self.queue.put(job)

    def get_next_job(self) -> BillingJob:
        return self.queue.get()

    def process_next_job(self) -> str:
        job = self.get_next_job()

        if job.job_type == "finalize_usage":
            return f"Finalized usage for tenant {job.tenant_id}"

        raise ValueError(f"Unknown job type: {job.job_type}")

    def run_once(self) -> str:
        return self.process_next_job()