from __future__ import annotations
from typing import Any
from .common import clamp, sha256_obj
from .models import DIKWP_ROLES, validate_opportunity, validate_profile
from .capability import capability_passport
from .routing import select_execution_route

def _market_metrics(op: dict[str, Any]) -> dict[str, float]:
    m = op["market"]
    capacity = max(float(m["capacity"]), 1e-9)
    occupancy = max(float(m["occupancy"]), 0.0)
    saturation = clamp(occupancy / capacity)
    first_mover_capture = clamp(
        float(m["network_effect"]) *
        float(m["concentration"]) *
        (0.35 + 0.65 * saturation)
    )
    commoditization = clamp(
        float(m["ai_substitutability"]) *
        float(m["digital_replicability"]) *
        (1.0 - 0.30 * float(m["locality"])) *
        (1.0 - 0.20 * float(m["trust_dependency"]))
    )
    human_complementarity = clamp((
        float(m["locality"]) +
        float(m["trust_dependency"]) +
        float(m["accountability_dependency"]) +
        float(m.get("physical_dependency",0)) +
        float(m.get("ownership_leverage",0))
    ) / 5.0)
    opportunity_slack = clamp(
        0.45 * (1.0 - saturation) +
        0.35 * float(m["demand_growth"]) +
        0.20 * float(m.get("unmet_need",0.5))
    )
    return {
        "saturation": round(saturation,6),
        "first_mover_capture": round(first_mover_capture,6),
        "commoditization_pressure": round(commoditization,6),
        "human_complementarity": round(human_complementarity,6),
        "opportunity_slack": round(opportunity_slack,6),
    }

def _constraints(profile: dict[str, Any], op: dict[str, Any]) -> list[str]:
    b = profile.get("budgets",{})
    c = op.get("constraints",{})
    reasons=[]
    if float(c.get("required_capital",0)) > float(b.get("available_capital",0)):
        reasons.append("capital_requirement_exceeds_budget")
    if float(c.get("hours_to_first_evidence",0)) > float(b.get("available_hours_90d",0)):
        reasons.append("time_to_first_evidence_exceeds_90d_budget")
    if c.get("requires_unlawful_or_deceptive_action",False):
        reasons.append("rights_or_legality_gate_failed")
    if float(c.get("max_tolerable_harm",0)) < float(c.get("estimated_harm",0)):
        reasons.append("harm_ceiling_exceeded")
    if c.get("requires_personal_data_without_consent",False):
        reasons.append("data_consent_gate_failed")
    return reasons

def assess_path(profile: dict[str, Any], op: dict[str, Any]) -> dict[str, Any]:
    validate_profile(profile)
    validate_opportunity(op)
    passport = capability_passport(profile)
    market = _market_metrics(op)
    gaps={}
    matches={}
    for r in DIKWP_ROLES:
        have = float(passport["dikwp_roles"][r]["bounded_capability"])
        need = float(op["required_dikwp"][r])
        gaps[r] = round(max(0.0, need-have),6)
        matches[r] = round(min(1.0, have/max(need,1e-9)) if need>0 else 1.0,6)
    max_gap=max(gaps.values())
    mean_match=sum(matches.values())/5
    blockers=_constraints(profile,op)
    route=select_execution_route(op,profile)
    if route["status"]=="NO_FEASIBLE_EXECUTION_ROUTE":
        blockers.append("no_execution_route_passes_hard_gates")

    m=op["market"]
    differentiation=clamp(
        float(m.get("differentiation_space",0.5)) +
        0.20*float(m.get("ownership_leverage",0)) +
        0.20*market["human_complementarity"] -
        0.25*market["commoditization_pressure"]
    )
    evidence_count=sum(v["evidence_count"] for v in passport["dikwp_roles"].values())

    if blockers:
        status="PATH_BLOCKED_BY_RIGHTS_OR_SAFETY" if any("rights" in x or "consent" in x or "harm" in x for x in blockers) else "NO_CURRENT_VERIFIED_PATH"
    elif evidence_count == 0:
        status="INSUFFICIENT_EVIDENCE_TO_ASSESS"
    elif market["saturation"] >= 0.82 and market["commoditization_pressure"] >= 0.68 and differentiation < 0.48:
        status="CROWDED_COMMODITY_ROUTE"
    elif max_gap <= 0.08 and market["opportunity_slack"] >= 0.42 and route["selected"]:
        status="PATH_VERIFIED_IN_CURRENT_SCOPE"
    elif market["opportunity_slack"] >= 0.62 and max_gap <= 0.24:
        status="FRONTIER_WINDOW_OPEN"
    elif max_gap <= 0.25 and differentiation >= 0.48:
        status="PATH_VIABLE_AFTER_SPECIFIED_GAPS"
    else:
        status="NO_CURRENT_VERIFIED_PATH"

    recommendations=[]
    if status=="CROWDED_COMMODITY_ROUTE":
        recommendations=[
            "Do not compete on generic output volume or prompt syntax.",
            "Move toward a bounded domain with owned problem access, trusted users, real deployment and accountable outcomes.",
            "Build a verifiable asset: dataset with consent, workflow, distribution channel, maintenance contract or community trust.",
            "Set a 30-day evidence deadline; exit the route if no real user, payment, adoption or outcome evidence appears."
        ]
    elif status in ("PATH_VIABLE_AFTER_SPECIFIED_GAPS","FRONTIER_WINDOW_OPEN"):
        recommendations=[
            "Close the largest DIKWP gaps with one real-world task and an external acceptance test.",
            "Create a transferable artifact owned by the contributor rather than a platform-only reputation signal.",
            "Run a low-capital pilot before education debt or irreversible career commitment.",
            "Preserve one non-digital or trust-based backup route."
        ]
    elif status=="PATH_VERIFIED_IN_CURRENT_SCOPE":
        recommendations=[
            "Start with a small written purpose contract and outcome metric.",
            "Capture contribution receipts, costs, energy and externalities.",
            "Reassess market saturation and model substitution every 30 days.",
            "Avoid exclusive dependence on one platform, customer or model provider."
        ]
    elif status=="PATH_BLOCKED_BY_RIGHTS_OR_SAFETY":
        recommendations=[
            "Do not proceed until the rights, consent, legality or harm gate is resolved.",
            "Seek an authorized alternative that preserves the same legitimate purpose.",
        ]
    else:
        recommendations=[
            "Record the result as no current verified path in the submitted market, not as a judgment of personal worth.",
            "Reopen only when a specific capability, demand, access, ownership or constraint changes.",
            "Search adjacent needs with higher locality, trust, accountability, maintenance or physical-world dependence.",
            "Protect health, cash runway and relationships while avoiding sunk-cost escalation."
        ]

    reopen=[]
    for role,g in sorted(gaps.items(), key=lambda kv:-kv[1]):
        if g>0.05:
            reopen.append({"condition":f"verified_{role}_capability_increases","required_delta":g})
    if market["saturation"]>0.75:
        reopen.append({"condition":"market_saturation_falls_or_new_segment_created","current":market["saturation"]})
    if market["commoditization_pressure"]>0.65:
        reopen.append({"condition":"route_gains_non_commoditized_asset_or_accountability","current":market["commoditization_pressure"]})
    if blockers:
        reopen.extend({"condition":x+"_resolved"} for x in blockers)

    result={
        "profile_id":profile["profile_id"],
        "opportunity_id":op["opportunity_id"],
        "opportunity_title":op["title"],
        "status":status,
        "scope":"submitted profile, evidence, market model and constraints",
        "dikwp_match":matches,
        "dikwp_gaps":gaps,
        "mean_match":round(mean_match,6),
        "market":market,
        "differentiation_space":round(differentiation,6),
        "hard_blockers":sorted(set(blockers)),
        "execution_route":route,
        "recommendations":recommendations,
        "reopen_conditions":reopen,
        "non_interpretation":[
            "not a global forecast",
            "not a ranking of human worth",
            "not proof that a person has no future",
            "not permission to make an irreversible career or financial decision without human review",
        ],
    }
    result["assessment_hash"]=sha256_obj(result)
    return result

def assess_portfolio(profile: dict[str, Any], opportunities: list[dict[str, Any]]) -> dict[str, Any]:
    results=[assess_path(profile,o) for o in opportunities]
    priority={
        "PATH_VERIFIED_IN_CURRENT_SCOPE":0,
        "FRONTIER_WINDOW_OPEN":1,
        "PATH_VIABLE_AFTER_SPECIFIED_GAPS":2,
        "CROWDED_COMMODITY_ROUTE":3,
        "NO_CURRENT_VERIFIED_PATH":4,
        "PATH_BLOCKED_BY_RIGHTS_OR_SAFETY":5,
        "INSUFFICIENT_EVIDENCE_TO_ASSESS":6,
    }
    results.sort(key=lambda x:(priority[x["status"]], -x["market"]["opportunity_slack"], x["opportunity_id"]))
    viable=[x for x in results if x["status"] in {"PATH_VERIFIED_IN_CURRENT_SCOPE","FRONTIER_WINDOW_OPEN","PATH_VIABLE_AFTER_SPECIFIED_GAPS"}]
    portfolio_status="AT_LEAST_ONE_BOUNDED_PATH_FOUND" if viable else "NO_CURRENT_VERIFIED_PATH_IN_SUBMITTED_MARKET"
    out={
        "profile_id":profile["profile_id"],
        "portfolio_status":portfolio_status,
        "results":results,
        "best_current_candidate":viable[0] if viable else None,
        "required_response":(
            "pilot_and_measure" if viable else
            "protect_runway_search_adjacent_needs_and_reopen_on_evidence"
        ),
    }
    out["portfolio_hash"]=sha256_obj(out)
    return out
