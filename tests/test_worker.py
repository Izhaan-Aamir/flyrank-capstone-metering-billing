from worker.jobs import BillingJob
from worker.worker import BillingWorker


def test_worker_processes_finalize_usage_job():
    worker = BillingWorker()

    worker.submit(
        BillingJob(
            job_id="job-001",
            tenant_id="tenant-001",
            job_type="finalize_usage",
            payload={},
        )
    )

    result = worker.run_once()

    assert result == "Finalized usage for tenant tenant-001"


def test_worker_rejects_unknown_job_type():
    worker = BillingWorker()

    worker.submit(
        BillingJob(
            job_id="job-002",
            tenant_id="tenant-001",
            job_type="unknown_job",
            payload={},
        )
    )

    try:
        worker.run_once()
        assert False, "Expected ValueError for unknown job type"
    except ValueError as exc:
        assert str(exc) == "Unknown job type: unknown_job"