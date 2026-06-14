# ML-12736 — local runtime smoke: drive the pydantic-2 api with FastAPI TestClient against
# a throwaway sqlite DB, to surface handler-body runtime bugs the route-registration boot misses.
import os
import warnings

warnings.simplefilter("ignore")
os.environ.setdefault("MLRUN_HTTPDB__DSN", "sqlite:////tmp/poc_tc_mlrun.db?check_same_thread=false")
os.environ["MLRUN_HTTPDB__AUTHENTICATION__MODE"] = "none"
os.environ["MLRUN_LOG_LEVEL"] = "ERROR"
os.environ["MLRUN_IS_API_SERVER"] = "true"

from fastapi.testclient import TestClient

import services.api.daemon as d

app = d.app()

# Unauthenticated, no-DB-data GET endpoints exercised on SDK connect / health.
GETS = [
    "/api/v1/healthz",
    "/api/v1/client-spec",
    "/api/v1/frontend-spec",
    "/api/v1/clusterization-spec",   # the one that 500'd on the lab
    "/api/v1/projects",
]

with TestClient(app, raise_server_exceptions=False) as client:
    for path in GETS:
        try:
            r = client.get(path)
            flag = "OK " if r.status_code < 500 else "ERR"
            body = "" if r.status_code < 500 else f" :: {str(r.text)[:160]}"
            print(f"[{flag}] GET {path} -> {r.status_code}{body}")
        except Exception as e:
            print(f"[EXC] GET {path} -> {type(e).__name__}: {str(e)[:160]}")
