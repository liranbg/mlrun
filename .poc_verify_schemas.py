# ML-12736 — verify a server-side native-v2 schema module preserves the runtime
# contract of its pydantic.v1 origin (field set, required-ness, defaults, extra policy).
#
# Both packages are importable in the same pydantic-2 process:
#   mlrun.common.schemas.<mod>  -> pydantic.v1 models (.__fields__)
#   schemas.<mod>               -> native pydantic 2 models (.model_fields)
#
# Usage: python .poc_verify_schemas.py [submodule ...]   (default: all in schemas/__init__ hub)
import importlib
import sys

import pydantic.v1 as v1
import pydantic as v2

PYDANTIC_UNDEFINED = object()


def _v1_field_contract(mfield):
    required = bool(mfield.required) if mfield.required is not None else False
    default = PYDANTIC_UNDEFINED if required else mfield.default
    return required, default, mfield.alias


def _v2_field_contract(finfo):
    required = finfo.is_required()
    default = PYDANTIC_UNDEFINED if required else finfo.default
    return required, default, (finfo.alias or finfo.title and None)


def _models(module, base):
    out = {}
    for name in dir(module):
        obj = getattr(module, name)
        if isinstance(obj, type) and issubclass(obj, base) and obj.__module__ == module.__name__:
            out[name] = obj
    return out


def verify_submodule(sub):
    problems = []
    try:
        m_v1 = importlib.import_module(f"mlrun.common.schemas.{sub}")
        m_v2 = importlib.import_module(f"schemas.{sub}")
    except Exception as e:
        return [f"IMPORT FAILED ({sub}): {type(e).__name__}: {e}"]

    models_v1 = _models(m_v1, v1.BaseModel)
    models_v2 = _models(m_v2, v2.BaseModel)

    missing = set(models_v1) - set(models_v2)
    if missing:
        problems.append(f"  models missing in v2: {sorted(missing)}")

    for name, cls_v1 in models_v1.items():
        cls_v2 = models_v2.get(name)
        if cls_v2 is None:
            continue
        f1 = {n: _v1_field_contract(f) for n, f in cls_v1.__fields__.items()}
        f2 = {n: _v2_field_contract(f) for n, f in cls_v2.model_fields.items()}
        if set(f1) != set(f2):
            problems.append(
                f"  {name}: field-set mismatch "
                f"(v1-only={sorted(set(f1) - set(f2))}, v2-only={sorted(set(f2) - set(f1))})"
            )
        for fname in set(f1) & set(f2):
            r1, d1, _ = f1[fname]
            r2, d2, _ = f2[fname]
            if r1 != r2:
                problems.append(
                    f"  {name}.{fname}: REQUIRED mismatch (v1 required={r1}, v2 required={r2})"
                )
            elif not r1 and not r2 and d1 != d2 and not (d1 is None and d2 is None):
                # both optional but different defaults (ignore callable/mutable noise)
                if repr(d1) != repr(d2):
                    problems.append(
                        f"  {name}.{fname}: default mismatch (v1={d1!r}, v2={d2!r})"
                    )
        # extra policy
        e1 = getattr(cls_v1.__config__, "extra", None)
        e1 = getattr(e1, "value", e1)
        e2 = cls_v2.model_config.get("extra", None)
        if e1 and e2 and str(e1) != str(e2):
            problems.append(f"  {name}: extra policy mismatch (v1={e1}, v2={e2})")

    return problems


def main():
    subs = sys.argv[1:]
    if not subs:
        hub = importlib.import_module("schemas")
        subs = [sub for sub in dir(hub)]  # not used; pass explicit submodules instead
    total = 0
    for sub in subs:
        probs = verify_submodule(sub)
        if probs:
            total += len(probs)
            print(f"[FAIL] {sub}:")
            for p in probs:
                print(p)
        else:
            print(f"[ OK ] {sub}: v1/v2 contract matches")
    print(f"\n{'PASS' if total == 0 else 'PROBLEMS: ' + str(total)}")
    sys.exit(0 if total == 0 else 1)


if __name__ == "__main__":
    main()
