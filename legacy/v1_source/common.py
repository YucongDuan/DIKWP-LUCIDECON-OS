from __future__ import annotations
import hashlib, json, math, time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(x)))

def canonical_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def sha256_obj(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()

def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def now_epoch() -> int:
    return int(time.time())

def gini(values: Iterable[float]) -> float:
    vals = sorted(max(0.0, float(v)) for v in values)
    if not vals or sum(vals) == 0:
        return 0.0
    n = len(vals)
    weighted = sum((i + 1) * v for i, v in enumerate(vals))
    return (2 * weighted) / (n * sum(vals)) - (n + 1) / n

def merkle_root(items: list[str]) -> str:
    if not items:
        return hashlib.sha256(b"").hexdigest()
    layer = [hashlib.sha256(x.encode("utf-8")).hexdigest() for x in items]
    while len(layer) > 1:
        if len(layer) % 2:
            layer.append(layer[-1])
        layer = [
            hashlib.sha256((layer[i] + layer[i+1]).encode("ascii")).hexdigest()
            for i in range(0, len(layer), 2)
        ]
    return layer[0]

class ValidationError(ValueError):
    pass

def require_fields(obj: dict[str, Any], fields: Iterable[str], label: str) -> None:
    missing = [f for f in fields if f not in obj]
    if missing:
        raise ValidationError(f"{label} missing required fields: {', '.join(missing)}")

def write_json(path: str | Path, obj: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
