from .common import day
from .validation import ROLES

def evidence_gate(case, opportunity):
    now=day(case['as_of'],'as_of'); op=opportunity['operation']
    eligible=[]; excluded=[]
    for e in case['evidence']:
        reasons=[]
        if op not in e['operations']: reasons.append('OUT_OF_SCOPE')
        if not day(e['observed_on'],'observed_on')<=now<=day(e['valid_until'],'valid_until'): reasons.append('NOT_CURRENT')
        if e['basis']!='REVIEWED': reasons.append('NOT_REVIEWED_IN_RECORD')
        if e['outcome']!='PASS': reasons.append('OUTCOME_NOT_PASS')
        if e['sample_n']<1: reasons.append('EMPTY_SAMPLE')
        (excluded if reasons else eligible).append({'id':e['id'],'reasons':reasons} if reasons else e)
    kinds={x['kind'] for x in eligible}
    roles={role:[x['id'] for x in eligible if x['kind']=='CAPABILITY' and role in x.get('roles',[])] for role in ROLES}
    missing=['EVIDENCE_'+k for k in ('DEMAND','DELIVERY','ACCESS') if k not in kinds]
    missing+=['ROLE_'+r for r in opportunity['required_roles'] if not roles[r]]
    return {'passed':not missing,'missing':missing,'eligible_ids':[e['id'] for e in eligible],
            'excluded':excluded,'role_evidence':roles,
            'reviewer_identity_authenticated':False,
            'boundary':'Reviews and source references are submitted declarations; files are not independently authenticated by this offline runtime.'}
