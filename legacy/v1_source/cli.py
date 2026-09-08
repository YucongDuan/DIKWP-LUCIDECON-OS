from __future__ import annotations
import argparse, json, shutil
from pathlib import Path
from .capability import capability_passport
from .common import write_json
from .ledger import append_event, verify_ledger
from .market import simulate_first_mover
from .pathfinder import assess_portfolio
from .reporting import write_path_report
from .valueflow import settle_value_flow
from .embedded import PROFILE, OPPORTUNITIES, MARKET, POLICY, VALUEFLOW

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def cmd_inspect(args):
    print(json.dumps({
        "system":"DIKWP-LUCIDECON-OS",
        "version":"1.0.0",
        "purpose":"bounded personal pathfinding and transparent contribution/value-flow governance",
        "automatic_external_action_authority":0,
        "global_person_score":None,
        "no_path_meaning":"no current verified path within declared evidence, market, horizon and constraints",
    },indent=2))

def cmd_assess(args):
    profile=load(args.profile)
    opportunities=load(args.opportunities)
    if isinstance(opportunities,dict):
        opportunities=opportunities.get("opportunities",[])
    passport=capability_passport(profile)
    portfolio=assess_portfolio(profile,opportunities)
    out=Path(args.output); out.mkdir(parents=True,exist_ok=True)
    ledger=out/"evidence_ledger.jsonl"
    append_event(ledger,"PROFILE_ACCEPTED",{"profile_id":profile["profile_id"],"owner":profile["owner"]})
    append_event(ledger,"CAPABILITY_PASSPORT_CREATED",passport)
    for r in portfolio["results"]:
        append_event(ledger,"PATH_ASSESSED",{"opportunity_id":r["opportunity_id"],"status":r["status"],"assessment_hash":r["assessment_hash"]})
    append_event(ledger,"PORTFOLIO_SETTLED",{"status":portfolio["portfolio_status"],"portfolio_hash":portfolio["portfolio_hash"]})
    write_path_report(out,portfolio,passport)
    print(json.dumps({"status":portfolio["portfolio_status"],"output":str(out),"ledger":verify_ledger(ledger)},indent=2))

def cmd_simulate(args):
    result=simulate_first_mover(load(args.market),load(args.policy) if args.policy else None)
    write_json(args.output,result)
    print(json.dumps(result,indent=2))

def cmd_settle(args):
    result=settle_value_flow(load(args.input))
    write_json(args.output,result)
    print(json.dumps(result,indent=2))

def cmd_verify(args):
    print(json.dumps(verify_ledger(args.ledger),indent=2))

def cmd_demo(args):
    root=Path(__file__).resolve().parents[2]
    # zipapp path fallback: examples copied under current working directory
    ex=Path(args.root)
    profile_path=ex/"examples/profiles/ordinary_knowledge_worker.json"
    opportunity_path=ex/"examples/opportunities/opportunity_portfolio.json"
    profile=load(profile_path) if profile_path.exists() else PROFILE
    opportunities=load(opportunity_path)["opportunities"] if opportunity_path.exists() else OPPORTUNITIES
    out=Path(args.output); out.mkdir(parents=True,exist_ok=True)
    passport=capability_passport(profile)
    portfolio=assess_portfolio(profile,opportunities)
    ledger=out/"evidence_ledger.jsonl"
    if ledger.exists(): ledger.unlink()
    append_event(ledger,"PROFILE_ACCEPTED",{"profile_id":profile["profile_id"]})
    append_event(ledger,"CAPABILITY_PASSPORT_CREATED",passport)
    for r in portfolio["results"]:
        append_event(ledger,"PATH_ASSESSED",{"opportunity_id":r["opportunity_id"],"status":r["status"],"assessment_hash":r["assessment_hash"]})
    append_event(ledger,"PORTFOLIO_SETTLED",{"status":portfolio["portfolio_status"],"portfolio_hash":portfolio["portfolio_hash"]})
    write_path_report(out,portfolio,passport)
    market_path=ex/"examples/markets/winner_take_most.json"
    policy_path=ex/"examples/markets/transparent_policy.json"
    valueflow_path=ex/"examples/valueflows/cooperative_service.json"
    sim=simulate_first_mover(load(market_path) if market_path.exists() else MARKET, load(policy_path) if policy_path.exists() else POLICY)
    write_json(out/"first_mover_simulation.json",sim)
    settlement=settle_value_flow(load(valueflow_path) if valueflow_path.exists() else VALUEFLOW)
    write_json(out/"valueflow_settlement.json",settlement)
    print(json.dumps({"portfolio_status":portfolio["portfolio_status"],"output":str(out),"ledger":verify_ledger(ledger)},indent=2))

def build_parser():
    p=argparse.ArgumentParser(prog="dikwp-lucidecon")
    sub=p.add_subparsers(dest="cmd",required=True)
    a=sub.add_parser("inspect"); a.set_defaults(func=cmd_inspect)
    a=sub.add_parser("assess"); a.add_argument("profile"); a.add_argument("opportunities"); a.add_argument("--output",required=True); a.set_defaults(func=cmd_assess)
    a=sub.add_parser("simulate"); a.add_argument("market"); a.add_argument("--policy"); a.add_argument("--output",required=True); a.set_defaults(func=cmd_simulate)
    a=sub.add_parser("settle"); a.add_argument("input"); a.add_argument("--output",required=True); a.set_defaults(func=cmd_settle)
    a=sub.add_parser("verify"); a.add_argument("ledger"); a.set_defaults(func=cmd_verify)
    a=sub.add_parser("demo"); a.add_argument("--root",default="."); a.add_argument("--output",default="outputs/demo"); a.set_defaults(func=cmd_demo)
    return p

def main():
    args=build_parser().parse_args()
    args.func(args)

if __name__=="__main__":
    main()
