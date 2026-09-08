from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from . import __version__
from .common import load,write,digest,ValidationError
from .engine import assess
from .settlement import settle
from .simulation import simulate
from .journal import verify,append,outcome
from .reporting import save_assessment
from .trace import semantic_trace
from .samples import cases,market,settlement

def execute(args):
    if args.cmd=='inspect':
        return {'system':'DIKWP-LUCIDECON-OS','version':__version__,'runtime_dependencies':[],
                'global_person_score':None,'automatic_external_actions':False,'real_funds_moved':False,
                'file_storage_encrypted_by_runtime':False,'field_validation_performed':False}
    if args.cmd=='init':
        out=Path(args.output)
        if out.exists(): raise ValidationError('will not overwrite an existing case')
        write(out,cases()['ordinary-pilot']);return {'template':str(out),'must_replace_synthetic_evidence':True}
    if args.cmd=='assess':
        c=load(args.case);r=assess(c);v=save_assessment(c,r,args.output)
        write(Path(args.output)/'semantic_trace.json',semantic_trace(c,r))
        return {'status':r['portfolio_status'],'assessment_hash':r['assessment_hash'],'ledger':v}
    if args.cmd=='demo':
        out=Path(args.output)
        if out.exists() and any(out.iterdir()): raise ValidationError('use a fresh empty output directory')
        out.mkdir(parents=True,exist_ok=True); statuses={}
        for name,c in cases().items():
            a=assess(c);save_assessment(c,a,out/name);write(out/name/'semantic_trace.json',semantic_trace(c,a));statuses[name]=a['portfolio_status']
        write(out/'market.json',simulate(market()));write(out/'settlement.json',settle(settlement()))
        write(out/'demo_summary.json',statuses);return statuses
    if args.cmd in ('settle','simulate-market'):
        if Path(args.output).exists(): raise ValidationError('will not overwrite previous output')
        r=(settle if args.cmd=='settle' else simulate)(load(args.input));write(args.output,r);return r
    if args.cmd=='verify':
        return verify(args.ledger,args.expected_head)
    if args.cmd=='replay':
        d=Path(args.directory);original=load(d/'assessment.json');fresh=assess(load(d/'private_input.json'))
        untouched=digest({k:v for k,v in original.items() if k!='assessment_hash'})==original.get('assessment_hash')
        equal=untouched and fresh['assessment_hash']==original['assessment_hash']
        return {'replay_equal':equal,'stored_hash_valid':untouched,'computed_hash':fresh['assessment_hash'],
                'meaning':'Same declared inputs and policy regenerate the same result; not proof of real market feasibility.'}
    if args.cmd=='record-outcome':
        d=Path(args.directory);a=load(d/'assessment.json');entry=load(args.input)
        if digest({k:v for k,v in a.items() if k!='assessment_hash'})!=a.get('assessment_hash'): raise ValidationError('stored assessment hash invalid')
        s=outcome(a,entry)
        p=d/('outcome_'+entry['id']+'.json')
        if p.exists(): raise ValidationError('outcome ID already exists; use a new ID to preserve history')
        ev=append(d/'ledger.jsonl','OUTCOME_RECORDED',s,entry['actor']);write(p,s)
        write(d/('checkpoint_'+entry['id']+'.json'),verify(d/'ledger.jsonl'))
        return {'successor':s,'event_hash':ev['hash']}
    if args.cmd=='audit-v1':
        c=load(args.input)
        return {'migration_status':'MANUAL_EVIDENCE_AND_ECONOMICS_REQUIRED',
                'detected_keys':sorted(c.keys()),'warnings':['v1 strength/transferability ratings are not v2 task evidence.',
                  'Provide dated demand, access and delivery records; do not relabel old scores as reviewed evidence.',
                  'Provide integer-minor-unit cash intervals and explicit scenarios; no automatic value inference.']}
    raise ValidationError('unknown command')

def parser():
    p=argparse.ArgumentParser(description='Local evidence-scoped opportunity and contribution tools, version '+__version__)
    sp=p.add_subparsers(dest='cmd',required=True)
    sp.add_parser('inspect')
    a=sp.add_parser('init');a.add_argument('--output',default='my_case.json')
    a=sp.add_parser('demo');a.add_argument('--output',default='outputs/demo')
    a=sp.add_parser('assess');a.add_argument('case');a.add_argument('--output',required=True)
    for cmd in ('settle','simulate-market'):
        a=sp.add_parser(cmd);a.add_argument('input');a.add_argument('--output',required=True)
    a=sp.add_parser('verify');a.add_argument('ledger');a.add_argument('--expected-head')
    a=sp.add_parser('replay');a.add_argument('directory')
    a=sp.add_parser('record-outcome');a.add_argument('directory');a.add_argument('input')
    a=sp.add_parser('audit-v1');a.add_argument('input')
    return p

def main():
    args=parser().parse_args()
    try:
        r=execute(args);print(json.dumps(r,ensure_ascii=False,indent=2,allow_nan=False))
        return 1 if (r.get('valid') is False or r.get('replay_equal') is False) else 0
    except (ValidationError,KeyError,TypeError,ValueError,OSError) as e:
        print(json.dumps({'error':type(e).__name__,'message':str(e)},ensure_ascii=False),file=sys.stderr);return 2

if __name__=='__main__': raise SystemExit(main())
