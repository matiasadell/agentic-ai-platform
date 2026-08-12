import json
from pathlib import Path

from databricks.sdk import WorkspaceClient

JOBS_DIR = Path(__file__).resolve().parents[2] / "jobs"


def correct_path(p):
    pc = "/Workspace/Shared/agentic-ai-platform/" + p.split("agentic-ai-platform/")[1]
    return pc



def deploy_job(client: WorkspaceClient, job_path: Path) -> None:
    job_name = job_path.stem
    spec = json.loads(job_path.read_text())

    for task in spec.get("tasks", []):
        notebook_task = task.get("notebook_task")
        if notebook_task and "notebook_path" in notebook_task:
            notebook_task["notebook_path"] = correct_path(notebook_task["notebook_path"])

        python_task = task.get("spark_python_task")
        if python_task and "python_file" in python_task:
            python_task["python_file"] = correct_path(python_task["python_file"])

    for existing in client.jobs.list(name=job_name):
        client.jobs.delete(job_id=existing.job_id)
        print(f"deleted existing '{job_name}' (job_id={existing.job_id})")

    created = client.jobs.create(**spec)
    print(f"created '{job_name}' (job_id={created.job_id}) from {job_path.relative_to(JOBS_DIR)}")


SHARED_REPO_PATH = "/Workspace/Shared/agentic-ai-platform"


def sync_shared_repo(client: WorkspaceClient, branch: str = "main") -> None:
    repo = next(client.repos.list(path_prefix=SHARED_REPO_PATH))
    client.repos.update(repo_id=repo.id, branch=branch)
    print(f"pulled '{branch}' into {SHARED_REPO_PATH}")


client = WorkspaceClient()
for job_path in sorted(JOBS_DIR.rglob("*.json")):
    deploy_job(client, job_path)

sync_shared_repo(client)
