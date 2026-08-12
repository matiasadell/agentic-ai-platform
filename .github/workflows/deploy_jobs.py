import json
from pathlib import Path

from databricks.sdk import WorkspaceClient

JOBS_DIR = Path(__file__).resolve().parents[2] / "jobs"


def deploy_job(client: WorkspaceClient, job_path: Path) -> None:
    job_name = job_path.stem
    spec = json.loads(job_path.read_text())

    for existing in client.jobs.list(name=job_name):
        client.jobs.delete(job_id=existing.job_id)
        print(f"deleted existing '{job_name}' (job_id={existing.job_id})")

    created = client.jobs.create(**spec)
    print(f"created '{job_name}' (job_id={created.job_id}) from {job_path.relative_to(JOBS_DIR)}")


client = WorkspaceClient()
for job_path in sorted(JOBS_DIR.rglob("*.json")):
    deploy_job(client, job_path)
