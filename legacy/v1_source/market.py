from __future__ import annotations
import math
from typing import Any
from .common import clamp, gini, sha256_obj

def simulate_first_mover(market: dict[str, Any], policy: dict[str, Any] | None = None) -> dict[str, Any]:
    policy = policy or {}
    entrants = int(market.get("entrants",20))
    value_pool = float(market.get("value_pool",100000.0))
    network_effect = clamp(market.get("network_effect",0.7))
    incumbency_decay = max(0.0,float(market.get("incumbency_decay",0.10)))
    quality = market.get("entrant_quality",[1.0]*entrants)
    if len(quality)<entrants:
        quality=list(quality)+[1.0]*(entrants-len(quality))
    raw=[]
    for i in range(entrants):
        early_bonus = 1.0 + network_effect * math.exp(-incumbency_decay*i) * (entrants-i)/entrants
        raw.append(max(0.0,float(quality[i]))*early_bonus)
    total=sum(raw) or 1.0
    shares=[x/total for x in raw]

    max_share=clamp(policy.get("max_individual_share",1.0),0.01,1.0)
    newcomer_reserve=clamp(policy.get("newcomer_reserve",0.0),0.0,0.5)
    commons_levy=clamp(policy.get("positional_rent_commons_levy",0.0),0.0,0.5)
    newcomer_count=max(1,int(policy.get("newcomer_count",max(1,entrants//5))))
    newcomer_idx=list(range(max(0,entrants-newcomer_count),entrants))

    # Apply cap iteratively and move excess to an opportunity-renewal pool.
    capped=shares[:]
    renewal_pool=0.0
    for _ in range(entrants+2):
        excess=0.0
        uncapped=[]
        for i,s in enumerate(capped):
            if s>max_share:
                excess += s-max_share
                capped[i]=max_share
            else:
                uncapped.append(i)
        if excess<=1e-12 or not uncapped:
            renewal_pool += excess
            break
        add=excess/len(uncapped)
        capped=[s+(add if i in uncapped else 0) for i,s in enumerate(capped)]

    distributable=max(0.0,1.0-commons_levy-newcomer_reserve)
    capped_sum=sum(capped) or 1.0
    final=[s/capped_sum*distributable for s in capped]
    for i in newcomer_idx:
        final[i]+=newcomer_reserve/len(newcomer_idx)
    commons_value=value_pool*(commons_levy+renewal_pool)
    payouts=[round(value_pool*s,2) for s in final]
    result={
        "entrants":entrants,
        "value_pool":value_pool,
        "policy":policy,
        "unregulated":{
            "shares":shares,
            "payouts":[round(value_pool*s,2) for s in shares],
            "gini":round(gini(shares),6),
            "top_10_percent_share":round(sum(sorted(shares,reverse=True)[:max(1,entrants//10)]),6),
            "last_20_percent_share":round(sum(shares[-max(1,entrants//5):]),6),
        },
        "transparent_policy":{
            "shares":final,
            "payouts":payouts,
            "gini":round(gini(final),6),
            "top_10_percent_share":round(sum(sorted(final,reverse=True)[:max(1,entrants//10)]),6),
            "last_20_percent_share":round(sum(final[-max(1,entrants//5):]),6),
            "commons_and_opportunity_renewal_value":round(commons_value,2),
        },
        "interpretation":"The simulation tests positional capture under declared assumptions. It is not a forecast of a real market.",
    }
    result["simulation_hash"]=sha256_obj(result)
    return result
