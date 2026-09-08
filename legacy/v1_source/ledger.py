from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .common import canonical_json, sha256_obj

GENESIS = "0" * 64

def append_event(path: str | Path, event_type: str, payload: dict[str, Any], actor: str = "runtime") -> dict[str, Any]:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    prev_hash = GENESIS
    seq = 1
    if p.exists() and p.stat().st_size:
        lines = [x for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
        if lines:
            last = json.loads(lines[-1])
            prev_hash = last["event_hash"]
            seq = int(last["seq"]) + 1
    core = {
        "seq": seq,
        "event_type": event_type,
        "actor": actor,
        "payload": payload,
        "prev_hash": prev_hash,
    }
    event_hash = sha256_obj(core)
    event = {**core, "event_hash": event_hash}
    with p.open("a", encoding="utf-8") as f:
        f.write(canonical_json(event) + "\n")
    return event

def verify_ledger(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {"valid": False, "event_count": 0, "errors": ["ledger_missing"]}
    prev = GENESIS
    errors: list[str] = []
    count = 0
    for line_no, line in enumerate(p.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        count += 1
        try:
            e = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line_{line_no}_invalid_json:{exc}")
            continue
        if e.get("prev_hash") != prev:
            errors.append(f"line_{line_no}_prev_hash_mismatch")
        core = {k: e[k] for k in ("seq","event_type","actor","payload","prev_hash")}
        calc = sha256_obj(core)
        if calc != e.get("event_hash"):
            errors.append(f"line_{line_no}_event_hash_mismatch")
        prev = e.get("event_hash", prev)
    return {"valid": not errors, "event_count": count, "errors": errors, "head_hash": prev}
