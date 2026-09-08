from __future__ import annotations
import os, json
from pathlib import Path
from .common import canonical,digest,parse,ValidationError,identifier,text
ZERO='0'*64

def verify(path, expected_head=None):
    p=Path(path); errors=[]; prev=ZERO; n=0
    if not p.exists(): return {'valid':False,'count':0,'errors':['MISSING_LEDGER'],'head':ZERO}
    try:
        with p.open(encoding='utf-8') as f:
            for line in f:
                n+=1
                if len(line)>2_000_000: raise ValidationError('oversize event')
                e=parse(line)
                if not isinstance(e,dict) or set(e)!={'seq','kind','actor','payload','previous','hash'}: raise ValidationError('event keys invalid')
                if type(e['seq']) is not int or e['seq']!=n: errors.append(f'SEQUENCE:{n}')
                if e['previous']!=prev: errors.append(f'LINK:{n}')
                core={k:v for k,v in e.items() if k!='hash'}
                if digest(core)!=e['hash']: errors.append(f'HASH:{n}')
                prev=e['hash']
    except (ValueError,TypeError,KeyError) as exc: errors.append(f'FORMAT:{n}:{exc}')
    if n==0: errors.append('EMPTY_LEDGER')
    if expected_head is not None and prev!=expected_head: errors.append('CHECKPOINT_MISMATCH')
    return {'valid':not errors,'count':n,'errors':errors,'head':prev,'externally_anchored':expected_head is not None}

def append(path,kind,payload,actor):
    text(kind,'kind',100);text(actor,'actor',100)
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); lock=Path(str(p)+'.lock')
    try: fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    except FileExistsError as exc: raise ValidationError('ledger locked; review a stale lock manually') from exc
    os.close(fd)
    try:
        v=verify(p) if p.exists() else {'valid':True,'count':0,'head':ZERO}
        if not v['valid']: raise ValidationError('refusing to append to invalid existing ledger')
        core={'seq':v['count']+1,'kind':kind,'actor':actor,'payload':payload,'previous':v['head']}
        event={**core,'hash':digest(core)}
        with p.open('a',encoding='utf-8') as f:
            f.write(canonical(event)+'\n');f.flush();os.fsync(f.fileno())
        return event
    finally: lock.unlink(missing_ok=True)

def outcome(assessment,entry):
    from .common import integer,flag,signed
    identifier(entry.get('id'),'outcome.id'); text(entry.get('actor'),'outcome.actor')
    if entry.get('assessment_hash')!=assessment['assessment_hash']: raise ValidationError('outcome is not bound to the assessment')
    op=entry.get('opportunity_id')
    if op not in {x['opportunity_id'] for x in assessment['results']}: raise ValidationError('unknown outcome opportunity')
    if entry.get('result') not in ('IMPROVED','NO_CHANGE','WORSENED','NOT_MEASURED'): raise ValidationError('invalid outcome result')
    if entry.get('result')!='NOT_MEASURED': text(entry.get('evidence_ref'),'outcome.evidence_ref')
    decision={'IMPROVED':'PROVISIONAL_SUPPORT_IN_THIS_CONTEXT','NO_CHANGE':'REVISE_BEFORE_SCALING',
              'WORSENED':'PAUSE_AND_REVIEW_HARM','NOT_MEASURED':'OUTCOME_DEBT_OPEN'}[entry['result']]
    return signed({'parent_assessment_hash':assessment['assessment_hash'],'outcome':entry,
                   'decision':decision,'original_assessment_overwritten':False,'causal_proof':False},'successor_hash')
