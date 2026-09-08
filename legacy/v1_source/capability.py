from __future__ import annotations
from collections import defaultdict
from typing import Any
from .common import clamp
from .models import DIKWP_ROLES, validate_profile

def capability_passport(profile: dict[str, Any]) -> dict[str, Any]:
    validate_profile(profile)
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for e in profile["capability_evidence"]:
        buckets[e["dikwp_role"]].append(e)

    role_results: dict[str, Any] = {}
    for role in DIKWP_ROLES:
        evidence = buckets.get(role, [])
        if not evidence:
            role_results[role] = {
                "bounded_capability": 0.0,
                "evidence_count": 0,
                "status": "NO_SUBMITTED_EVIDENCE",
                "evidence_ids": [],
            }
            continue
        vals = []
        for e in evidence:
            outcome_factor = 1.0 if e.get("outcome_verified") else 0.65
            recency = clamp(e.get("recency", 0.7))
            provenance = clamp(e.get("provenance_quality", 0.7))
            v = (
                0.35 * clamp(e["strength"]) +
                0.25 * clamp(e["transferability"]) +
                0.20 * outcome_factor +
                0.10 * recency +
                0.10 * provenance
            )
            vals.append(v)
        # Diminishing returns: multiple independent evidence items strengthen the bounded estimate.
        vals.sort(reverse=True)
        score = vals[0]
        for v in vals[1:]:
            score = 1 - (1-score) * (1-0.35*v)
        score = clamp(score)
        status = (
            "ROBUST_WITHIN_SUBMITTED_SCOPE" if score >= 0.78 else
            "FUNCTIONAL_WITHIN_SUBMITTED_SCOPE" if score >= 0.62 else
            "DEVELOPING" if score >= 0.42 else
            "FRAGILE"
        )
        role_results[role] = {
            "bounded_capability": round(score, 6),
            "evidence_count": len(evidence),
            "status": status,
            "evidence_ids": [e["evidence_id"] for e in evidence],
        }

    return {
        "profile_id": profile["profile_id"],
        "owner": profile["owner"],
        "scope": profile.get("scope", "submitted tasks and evidence only"),
        "dikwp_roles": role_results,
        "prohibited_interpretations": [
            "not a global intelligence score",
            "not a ranking of human worth",
            "not a mental-health or personality diagnosis",
            "not valid outside the declared evidence scope",
        ],
        "profile_hash_basis": {
            "evidence_count": len(profile["capability_evidence"]),
            "owner_controlled": True,
            "revocable": bool(profile.get("consent", {}).get("revocable", True)),
        },
    }
