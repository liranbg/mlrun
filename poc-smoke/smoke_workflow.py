# ML-12736 smoke: remote KFP workflow. The workflow runner pod uses the lab's mlrun-kfp image
# (pydantic 1, KFP 1.8); the v2 api orchestrates + monitors it via kfp_server_api 1.8.
import os
import sys

os.environ["MLRUN_HTTPDB__HTTP__VERIFY"] = "false"
os.environ["MLRUN_AUTH_WITH_OAUTH_TOKEN__TOKEN_NAME"] = "vmdev103ig4"
os.environ["MLRUN_DBPATH"] = "http://localhost:18080"

import mlrun

project = mlrun.get_or_create_project(
    "poc-pydantic2", context="/tmp/poc-smoke", user_project=False
)
project.set_function(
    "dummy_job.py", name="dummy", kind="job", image="mlrun/mlrun:1.12.0-rc12", handler="handler"
)
# pin the runner image to the lab's existing rc12 kfp image (pydantic 1); otherwise the
# unstable-versioned api resolves mlrun/mlrun-kfp:unstable, which isn't in the registry.
project.set_workflow(
    "main", "workflow.py", image="mlrun/mlrun-kfp:1.12.0-rc12", embed=True
)
project.save()

print("=== run remote KFP workflow ===", flush=True)
run = project.run("main", engine="remote", watch=True)
state = getattr(run, "state", run)
print("WORKFLOW run_id:", getattr(run, "run_id", "?"), "| state:", state, flush=True)
ok = str(state).lower() in ("succeeded", "completed")
sys.exit(0 if ok else 2)
