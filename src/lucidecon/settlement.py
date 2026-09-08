"""Exact minor-unit, negotiated-policy allocation. Not a payment processor."""
from fractions import Fraction
from .common import *

def apportion(total, weighted_ids):
    integer(total,'total',0,10**12)
    ids=[x[0] for x in weighted_ids]
    if len(ids)!=len(set(ids)): raise ValidationError('duplicate recipient ID')
    weights=[Fraction(x[1]) for x in weighted_ids]
    if any(x<0 for x in weights): raise ValidationError('negative allocation weight')
    if not weighted_ids or sum(weights)==0: return {k:0 for k in ids}
    ideal=[total*w/sum(weights) for w in weights]
    allocations=[v.numerator//v.denominator for v in ideal]
    left=total-sum(allocations)
    for i in sorted(range(len(ids)),key=lambda i:(-(ideal[i]-allocations[i]),ids[i]))[:left]: allocations[i]+=1
    return dict(zip(ids,allocations))

def settle(c):
    identifier(c.get('event_id'),'event_id'); identifier(c.get('currency'),'currency')
    gross=integer(c.get('gross_cents'),'gross_cents',0,10**12)
    repair=integer(c.get('repair_claim_cents'),'repair_claim_cents',0,10**12)
    policy=c['policy']; text(policy.get('id'),'policy.id')
    for k in ('agreed','rights_clear'): flag(policy.get(k),'policy.'+k)
    cb=integer(policy.get('commons_bps'),'commons_bps',0,10000)
    nb=integer(policy.get('newcomer_bps'),'newcomer_bps',0,10000)
    if cb+nb>10000: raise ValidationError('pool basis points exceed 10000')
    participants=array(c.get('contributions'),'contributions',300); unique(participants,'id','contribution.id')
    for x in participants:
        integer(x.get('units'),'contribution.units',0,10**9)
        if x.get('status') not in ('ACCEPTED','DISPUTED','UNVERIFIED'): raise ValidationError('invalid contribution status')
        if any(r not in ('D','I','K','W','P') for r in array(x.get('roles'),'roles',5)): raise ValidationError('invalid DIKWP roles')
        text(x.get('receipt_ref'),'receipt_ref')
    allowed=policy['agreed'] and policy['rights_clear']
    if not allowed:
        return signed({'event_id':c['event_id'],'currency':c['currency'],'status':'ALL_FUNDS_HELD_POLICY_OR_RIGHTS_OPEN',
                       'gross_cents':gross,'repair_reserve_cents':0,'commons_cents':0,'newcomer_cents':0,'paid_cents':0,
                       'held_cents':gross,'repair_shortfall_cents':max(0,repair-gross),'allocations':[],
                       'conservation_ok':True,'real_funds_moved':False},'settlement_hash')
    reserve=min(gross,repair); after=gross-reserve
    commons=after*cb//10000; newcomer=after*nb//10000; pool=after-commons-newcomer
    amounts=apportion(pool,[(x['id'],x['units']) for x in participants])
    allocated=sum(amounts.values()); held=pool-allocated; paid=0; entries=[]
    for x in sorted(participants,key=lambda x:x['id']):
        a=amounts[x['id']]; ok=x['status']=='ACCEPTED'
        paid+=a if ok else 0; held+=0 if ok else a
        entries.append({'id':x['id'],'roles':x['roles'],'amount_cents':a,
                        'state':'PLANNED_PAYOUT' if ok else 'HELD_PENDING_REVIEW','receipt_ref':x['receipt_ref']})
    assert gross==reserve+commons+newcomer+paid+held
    return signed({'event_id':c['event_id'],'currency':c['currency'],'status':'DRY_RUN_CONSERVED_ALLOCATION',
                   'gross_cents':gross,'repair_reserve_cents':reserve,'commons_cents':commons,'newcomer_cents':newcomer,
                   'paid_cents':paid,'held_cents':held,'repair_shortfall_cents':max(0,repair-gross),
                   'allocations':entries,'conservation_ok':True,'real_funds_moved':False,
                   'policy_id':policy['id'],'boundary':'Weights and pool rules are agreed normative inputs, not objective causal value, tax or legal liability. Disputed shares are held, not redistributed to accepted claims.'},'settlement_hash')
