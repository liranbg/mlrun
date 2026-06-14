# ML-12736 — full-package gate:
#  (1) import the server v2 schemas hub,
#  (2) v1<->v2 field-equivalence for every converted submodule,
#  (3) FastAPI must accept every top-level v2 model (no PydanticV1NotSupportedError).
import importlib
import os
import sys
import warnings

warnings.simplefilter("ignore")  # silence pydantic v2 deprecation noise for the gate

import fastapi
import pydantic.v1 as v1
import pydantic as v2

WT = os.path.dirname(os.path.abspath(__file__))
SCHEMAS_DIR = os.path.join(WT, "server", "py", "schemas")
PYDANTIC_UNDEFINED = object()


def discover_submodules():
    subs = []
    for root, _dirs, files in os.walk(SCHEMAS_DIR):
        if "proto" in root or "__pycache__" in root:
            continue
        for fn in files:
            if not fn.endswith(".py") or fn == "__init__.py":
                continue
            rel = os.path.relpath(os.path.join(root, fn), SCHEMAS_DIR)[:-3]
            subs.append(rel.replace(os.sep, "."))
    return sorted(subs)


def v1_contract(mf):
    # effective default state: factory > required > concrete default
    if getattr(mf, "default_factory", None) is not None:
        return ("factory",)
    required = bool(mf.required) if mf.required is not None else False
    return ("required",) if required else ("default", repr(mf.default))


def v2_contract(fi):
    if getattr(fi, "default_factory", None) is not None:
        return ("factory",)
    return ("required",) if fi.is_required() else ("default", repr(fi.default))


def models(module, base):
    return {
        n: getattr(module, n)
        for n in dir(module)
        if isinstance(getattr(module, n), type)
        and issubclass(getattr(module, n), base)
        and getattr(module, n).__module__ == module.__name__
    }


def verify_contract(sub):
    problems = []
    try:
        m1 = importlib.import_module(f"mlrun.common.schemas.{sub}")
        m2 = importlib.import_module(f"schemas.{sub}")
    except Exception as e:
        return [f"IMPORT FAILED: {type(e).__name__}: {e}"]
    mv1, mv2 = models(m1, v1.BaseModel), models(m2, v2.BaseModel)
    for missing in sorted(set(mv1) - set(mv2)):
        problems.append(f"model missing in v2: {missing}")
    for name, c1 in mv1.items():
        c2 = mv2.get(name)
        if c2 is None:
            continue
        f1 = {n: v1_contract(f) for n, f in c1.__fields__.items()}
        f2 = {n: v2_contract(f) for n, f in c2.model_fields.items()}
        if set(f1) != set(f2):
            problems.append(
                f"{name}: fields v1-only={sorted(set(f1) - set(f2))} v2-only={sorted(set(f2) - set(f1))}"
            )
        for fn in set(f1) & set(f2):
            if f1[fn] != f2[fn]:
                problems.append(f"{name}.{fn}: contract v1={f1[fn]} v2={f2[fn]}")
    return problems


def main():
    print("== import server v2 schemas hub ==")
    try:
        hub = importlib.import_module("schemas")
        print("  OK: import schemas")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"  HUB IMPORT FAILED: {type(e).__name__}: {e}")
        sys.exit(2)

    print("\n== v1<->v2 contract per submodule ==")
    total = 0
    for sub in discover_submodules():
        probs = verify_contract(sub)
        if probs:
            total += len(probs)
            print(f"[FAIL] {sub}")
            for p in probs:
                print(f"    - {p}")
        else:
            print(f"[ OK ] {sub}")

    print("\n== FastAPI acceptance of every top-level v2 model ==")
    app = fastapi.FastAPI()
    rejected = 0
    checked = 0
    for name in dir(hub):
        obj = getattr(hub, name)
        if isinstance(obj, type) and issubclass(obj, v2.BaseModel):
            checked += 1
            try:
                app.add_api_route(f"/_t/{name}", (lambda: None), response_model=obj, methods=["GET"])
            except Exception as e:
                rejected += 1
                print(f"  [REJECT] {name}: {type(e).__name__}: {str(e)[:80]}")
    print(f"  models checked={checked} rejected={rejected}")

    print(f"\n{'ALL GOOD' if total == 0 and rejected == 0 else 'PROBLEMS: contract=' + str(total) + ' rejected=' + str(rejected)}")
    sys.exit(0 if total == 0 and rejected == 0 else 1)


if __name__ == "__main__":
    main()
