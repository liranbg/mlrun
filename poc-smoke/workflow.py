# ML-12736 POC remote KFP workflow — single step running the dummy function.
from kfp import dsl

import mlrun


@dsl.pipeline(name="poc-pydantic2-pipeline")
def pipeline(p: int = 21):
    project = mlrun.get_current_project()
    project.run_function("dummy", params={"p": p}, outputs=["answer"])
