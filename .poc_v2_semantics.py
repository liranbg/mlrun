# Verify exact pydantic-2 semantics for the conversion ruleset.
import warnings
import typing

import pydantic

print("pydantic", pydantic.VERSION)


def check(label, fn):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            fn()
        print(f"[OK   ] {label}")
    except Warning as w:
        print(f"[WARN ] {label}: {type(w).__name__}: {str(w)[:90]}")
    except Exception as e:
        print(f"[ERR  ] {label}: {type(e).__name__}: {str(e)[:110]}")


# 1. Extra still importable?
def _extra():
    from pydantic import Extra  # noqa
check("from pydantic import Extra", _extra)


# 2. class Config with v2 key names
def _cfg_v2():
    class M(pydantic.BaseModel):
        x: int = 1
        class Config:
            extra = "allow"
            from_attributes = True
            populate_by_name = True
check("class Config{extra='allow', from_attributes, populate_by_name}", _cfg_v2)


# 3. class Config with v1 orm_mode (does v2 accept/map it?)
def _cfg_orm():
    class M(pydantic.BaseModel):
        x: int = 1
        class Config:
            orm_mode = True
check("class Config{orm_mode=True}", _cfg_orm)


# 4. implicit optional: does `T | None` WITHOUT default become required in v2?
def _impl_opt():
    class M(pydantic.BaseModel):
        a: str | None
    M()  # if a is required, this raises
print("--- implicit optional behavior ---")
try:
    class M(pydantic.BaseModel):
        a: str | None
    inst = M()
    print(f"[INFO ] `a: str|None` no default -> M() OK, a={inst.a!r} (treated optional)")
except Exception as e:
    print(f"[INFO ] `a: str|None` no default -> M() FAILS: {type(e).__name__} (field is REQUIRED in v2)")


# 5. Literal with StrEnum member (const= replacement)
import enum
class Kind(str, enum.Enum):
    project = "project"

def _lit():
    class M(pydantic.BaseModel):
        kind: typing.Literal[Kind.project] = Kind.project
    assert M().kind == Kind.project
check("Literal[StrEnum.member] (const replacement)", _lit)
