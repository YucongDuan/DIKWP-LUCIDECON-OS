from __future__ import annotations
from typing import Any
from .common import clamp
from .models import validate_opportunity

def select_execution_route(opportunity: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    validate_opportunity(opportunity)
    budgets = profile.get("budgets", {})
    allowed_modes = set(profile.get("allowed_execution_modes", [
        "MODEL_NATIVE","GENERATED_CODE","LOCAL_API","REMOTE_API","BROWSER","GUI","FEDERATED_NODE","HUMAN","PHYSICAL"
    ]))
    data_class = opportunity.get("data_class", "PUBLIC")
    allowed_data = set(profile.get("allowed_data_classes", ["PUBLIC","INTERNAL"]))
    candidates = []
    rejected = []
    for r in opportunity["execution_routes"]:
        reasons = []
        if r.get("mode") not in allowed_modes:
            reasons.append("mode_not_authorized")
        if data_class not in allowed_data:
            reasons.append("data_class_not_authorized")
        if not r.get("authorized", False):
            reasons.append("route_not_authorized")
        if float(r.get("quality",0)) < float(opportunity["constraints"].get("min_quality",0)):
            reasons.append("quality_below_floor")
        if float(r.get("reliability",0)) < float(opportunity["constraints"].get("min_reliability",0)):
            reasons.append("reliability_below_floor")
        if float(r.get("privacy_risk",1)) > float(opportunity["constraints"].get("max_privacy_risk",1)):
            reasons.append("privacy_risk_above_ceiling")
        if float(r.get("irreversibility",1)) > float(opportunity["constraints"].get("max_irreversibility",1)):
            reasons.append("irreversibility_above_ceiling")
        if float(r.get("energy_j",0)) > float(budgets.get("max_energy_j", float("inf"))):
            reasons.append("energy_budget_exceeded")
        if float(r.get("money_cost",0)) > float(budgets.get("max_money", float("inf"))):
            reasons.append("money_budget_exceeded")
        if float(r.get("latency_s",0)) > float(budgets.get("max_latency_s", float("inf"))):
            reasons.append("latency_budget_exceeded")
        if reasons:
            rejected.append({"route_id": r.get("route_id"), "reasons": reasons})
        else:
            candidates.append(r)
    if not candidates:
        return {"status":"NO_FEASIBLE_EXECUTION_ROUTE","selected":None,"rejected":rejected}
    candidates.sort(key=lambda r: (
        float(r.get("energy_j", float("inf"))),
        float(r.get("money_cost", float("inf"))),
        float(r.get("latency_s", float("inf"))),
        float(r.get("human_minutes", float("inf"))),
        float(r.get("data_egress_mb", float("inf"))),
        -float(r.get("quality",0)),
    ))
    selected = candidates[0]
    return {
        "status":"ROUTE_SELECTED_WITHIN_DECLARED_CONSTRAINTS",
        "selected":selected,
        "alternatives":[r for r in candidates[1:]],
        "rejected":rejected,
        "selection_order":["energy_j","money_cost","latency_s","human_minutes","data_egress_mb","quality_desc"],
        "warning":"Energy minimization is applied only after authorization, quality, reliability, privacy and reversibility gates.",
    }
