import html
from .common import write,digest
from .journal import append,verify
from .engine import public_receipt
from pathlib import Path

def report_md(a):
    lines=[f"# LUCIDECON 2.0 — {a['case_id']}",f"\nData: **{a['data_origin']}**. All input claims remain unverified by this offline engine.",
           f"\nDecision: **{a['portfolio_status']}**",'\nMoney is in minor currency units (cents); not a forecast or personal-worth score.']
    for x in a['results']:
        lines += [f"\n## {x['title']}",f"\n**{x['status']}**",'\n| Scenario | Net cash interval (cents) | Pre-funding (cents) |', '|---|---:|---:|']
        lines += [f"| {s['scenario_id']} | {s['net_cash_cents']} | {s['prefund_cents']} |" for s in x['scenarios']]
        lines += [f"\nEvidence gaps: {', '.join(x['evidence']['missing']) or 'none in declarations'}",f"\nReopen conditions: `{x['reopen_conditions']}`"]
    lines+=['\n## Boundaries']+['\n'+s for s in a['limits']]
    return '\n'.join(lines)+'\n'

def save_assessment(c,a,destination):
    out=Path(destination)
    if out.exists() and any(out.iterdir()): raise ValueError('output directory is not empty; use a new directory to preserve prior runs')
    out.mkdir(parents=True,exist_ok=True)
    write(out/'private_input.json',c);write(out/'assessment.json',a);write(out/'public_receipt.json',public_receipt(a))
    j=out/'ledger.jsonl'
    append(j,'CONSENT_SCOPED_INPUT',{'input_hash':digest(c),'case_id':c['case_id']},c['owner_alias'])
    for x in a['results']: append(j,'OPPORTUNITY_ASSESSED',{'id':x['opportunity_id'],'result_hash':digest(x),'status':x['status']},'local-runtime')
    append(j,'ASSESSMENT_FINISHED',{'assessment_hash':a['assessment_hash']},'local-runtime')
    (out/'report.md').write_text(report_md(a),encoding='utf-8')
    v=verify(j);write(out/'checkpoint.json',v)
    return v
