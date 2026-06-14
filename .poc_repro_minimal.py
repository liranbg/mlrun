# ML-12736 POC — minimal reproduction of FastAPI rejecting pydantic.v1 schema models.
import fastapi
import pydantic

import mlrun.common.schemas

print("pydantic:", pydantic.VERSION, "| fastapi:", fastapi.__version__)
print("Project base classes:", [c.__module__ for c in type(mlrun.common.schemas.Project).__mro__][:3])

app = fastapi.FastAPI()


@app.post("/projects")
def create_project(project: mlrun.common.schemas.Project):
    return project


print("Route registered OK (unexpected)")
