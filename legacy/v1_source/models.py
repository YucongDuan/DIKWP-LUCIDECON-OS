from __future__ import annotations
from typing import Any
from .common import ValidationError, require_fields, clamp

DIKWP_ROLES = ("D","I","K","W","P")
PATH_STATUSES = (
    "PATH_VERIFIED_IN_CURRENT_SCOPE",
    "PATH_VIABLE_AFTER_SPECIFIED_GAPS",
    "FRONTIER_WINDOW_OPEN",
    "CROWDED_COMMODITY_ROUTE",
    "NO_CURRENT_VERIFIED_PATH",
    "PATH_BLOCKED_BY_RIGHTS_OR_SAFETY",
    "INSUFFICIENT_EVIDENCE_TO_ASSESS",
)

def validate_profile(profile: dict[str, Any]) -> None:
    require_fields(profile, ("profile_id","owner","consent","budgets","capability_evidence"), "profile")
    if not profile.get("consent", {}).get("self_assessment_authorized", False):
        raise ValidationError("profile lacks explicit self-assessment authorization")
    for item in profile["capability_evidence"]:
        require_fields(item, ("evidence_id","dikwp_role","operation","strength","transferability","outcome_verified"), "capability_evidence")
        if item["dikwp_role"] not in DIKWP_ROLES:
            raise ValidationError(f"unknown DIKWP role: {item['dikwp_role']}")
        for f in ("strength","transferability"):
            if not 0 <= float(item[f]) <= 1:
                raise ValidationError(f"{f} must be in [0,1]")

def validate_opportunity(op: dict[str, Any]) -> None:
    require_fields(op, ("opportunity_id","title","required_dikwp","market","constraints","execution_routes"), "opportunity")
    for r in DIKWP_ROLES:
        if r not in op["required_dikwp"]:
            raise ValidationError(f"opportunity missing required_dikwp.{r}")
    m = op["market"]
    require_fields(m, ("capacity","occupancy","demand_growth","network_effect","concentration","digital_replicability","ai_substitutability","locality","trust_dependency","accountability_dependency"), "market")
    if float(m["capacity"]) <= 0:
        raise ValidationError("market.capacity must be positive")
    if float(m["occupancy"]) < 0:
        raise ValidationError("market.occupancy must be non-negative")

def bounded_num(d: dict[str, Any], key: str, default: float = 0.0) -> float:
    return clamp(float(d.get(key, default)))
