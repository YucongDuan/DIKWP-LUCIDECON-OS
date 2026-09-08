from __future__ import annotations
from typing import Any
from .common import clamp, sha256_obj

def settle_value_flow(case: dict[str, Any]) -> dict[str, Any]:
    gross=float(case["gross_value"])
    harm=max(0.0,float(case.get("verified_harm",0)))
    unacceptable=bool(case.get("unacceptable_harm",False))
    policy=case.get("policy",{})
    repair_multiplier=max(1.0,float(policy.get("harm_repair_multiplier",1.25)))
    commons_rate=clamp(policy.get("commons_rate_on_positional_rent",0.10),0,0.5)
    newcomer_rate=clamp(policy.get("newcomer_opportunity_rate",0.08),0,0.4)
    positional_rent=clamp(case.get("positional_rent_fraction",0.0))
    repair_reserve=min(gross,harm*repair_multiplier)
    if unacceptable:
        return {
            "status":"PAYOUT_BLOCKED_UNTIL_UNACCEPTABLE_HARM_IS_RESOLVED",
            "gross_value":gross,
            "repair_reserve":repair_reserve,
            "distributable":0.0,
            "receipts":[],
            "note":"Positive output cannot compensate for a non-compensable harm floor violation.",
        }
    commons=gross*positional_rent*commons_rate
    newcomer=gross*newcomer_rate
    distributable=max(0.0,gross-repair_reserve-commons-newcomer)
    contributions=case.get("contributions",[])
    weights=[]
    for c in contributions:
        verified=clamp(c.get("verification_confidence",0))
        marginal=max(0.0,float(c.get("marginal_outcome",0)))
        continuity=clamp(c.get("maintenance_and_followthrough",0.5))
        rights=1.0 if c.get("rights_and_consent_clear",False) else 0.0
        weights.append(marginal*(0.55+0.25*verified+0.20*continuity)*rights)
    total=sum(weights)
    receipts=[]
    for c,w in zip(contributions,weights):
        share=(w/total) if total>0 else 0
        amount=round(distributable*share,2)
        receipts.append({
            "contribution_id":c["contribution_id"],
            "claimant":c["claimant"],
            "dikwp_role":c.get("dikwp_role"),
            "bounded_contribution_share":round(share,6),
            "payout":amount,
            "verification_confidence":clamp(c.get("verification_confidence",0)),
            "marginal_outcome":c.get("marginal_outcome",0),
            "scope":"this value-creation event only",
        })
    out={
        "status":"DRY_RUN_SETTLEMENT_GENERATED",
        "gross_value":gross,
        "repair_reserve":round(repair_reserve,2),
        "commons_value":round(commons,2),
        "newcomer_opportunity_fund":round(newcomer,2),
        "distributable":round(distributable,2),
        "receipts":receipts,
        "real_funds_moved":False,
        "non_interpretation":[
            "not a global personal value score",
            "not a legal liability determination",
            "not proof of causality beyond the declared marginal tests",
        ],
    }
    out["settlement_hash"]=sha256_obj(out)
    return out
