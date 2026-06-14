# ML-12736 POC — test candidate fixes for the FastAPI/pydantic.v1 incompatibility.
# Goal: find the cheapest source change that makes FastAPI (v2) accept the model.
import warnings

import fastapi
import pydantic

print("pydantic:", pydantic.VERSION, "| fastapi:", fastapi.__version__)
print("=" * 70)


def try_register(label, model_cls):
    app = fastapi.FastAPI()
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)  # surface v1-compat deprecations

            @app.post("/x")
            def _ep(body: model_cls):  # noqa
                return body

        print(f"[OK ] {label}: FastAPI accepted the model")
    except Exception as e:
        print(f"[ERR] {label}: {type(e).__name__}: {str(e)[:160]}")


# --- Candidate F: native pydantic (v2 here) but written in v1-compat style ---
from pydantic import BaseModel, Field  # native (==v2 in this env)

try:
    from pydantic import validator  # v1-style validator, deprecated-but-present in v2
except Exception:
    validator = None


class NativeV1StyleConfig(BaseModel):
    name: str

    class Config:
        extra = "allow"


try_register("F1 native + class Config(extra='allow')", NativeV1StyleConfig)


if validator:

    class NativeV1StyleValidator(BaseModel):
        name: str

        @validator("name")
        def _v(cls, v):  # noqa
            return v

    try_register("F2 native + @validator", NativeV1StyleValidator)


# const= is the known hard-removal in v2 — confirm it breaks
try:

    class NativeConst(BaseModel):
        kind: str = Field("project", const=True)

    try_register("F3 native + Field(const=True)", NativeConst)
except Exception as e:
    print(f"[ERR] F3 native + Field(const=True) at CLASS DEF: {type(e).__name__}: {str(e)[:160]}")


# Literal works as the v2-idiomatic replacement for const=
import typing


class NativeLiteral(BaseModel):
    kind: typing.Literal["project"] = "project"


try_register("F4 native + Literal (const replacement)", NativeLiteral)
