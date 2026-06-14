# ML-12736 smoke: v1 client (pydantic 1.10) -> v2 server (pydantic 2) dummy job — full v4 path
# (no bypass): connect runs the secret-token sync, which the Content-Type middleware now fixes.
import os
import sys

os.environ["MLRUN_HTTPDB__HTTP__VERIFY"] = "false"
os.environ["MLRUN_AUTH_WITH_OAUTH_TOKEN__TOKEN_NAME"] = "vmdev103ig4"
os.environ["MLRUN_DBPATH"] = "http://localhost:18080"

import pydantic

import mlrun

print("CLIENT pydantic:", pydantic.VERSION, "| mlrun:", mlrun.__version__, flush=True)
db = mlrun.get_run_db()
print("connected OK; list_projects:", len(list(db.list_projects())), "projects", flush=True)

print("=== create project ===", flush=True)
project = mlrun.get_or_create_project(
    "poc-pydantic2", context="/tmp/poc-smoke", user_project=False
)
print("project:", project.name, flush=True)

print("=== submit dummy job (image mlrun/mlrun = lab rc12 / pydantic 1) ===", flush=True)
fn = project.set_function(
    "dummy_job.py", name="dummy", kind="job", image="mlrun/mlrun:1.12.0-rc12", handler="handler"
)
run = fn.run(params={"p": 21}, watch=True)
print("RUN state:", run.state(), "| answer:", run.output("answer"), flush=True)
sys.exit(0 if run.state() == "completed" else 2)
