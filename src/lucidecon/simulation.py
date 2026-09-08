"""Fixed-pool concentration experiment, not a market or income forecast."""
from fractions import Fraction as F
from .common import *
from .settlement import apportion

def capped_allocate(total,weights,cap,base=None):
    ids=[x[0] for x in weights]; weight=dict(weights); amounts={i:(base or {}).get(i,0) for i in ids}
    if any(v>cap for v in amounts.values()) or total>len(ids)*cap or sum(amounts.values())>total:
        raise ValidationError('policy infeasible: floors/cap cannot conserve the fixed pool')
    remaining=total-sum(amounts.values())
    while remaining:
        active=[i for i in ids if amounts[i]<cap]
        alloc=apportion(remaining,[(i,weight[i]) for i in active])
        if sum(alloc.values())==0: alloc=apportion(remaining,[(i,1) for i in active])
        delivered=0
        for i in active:
            v=min(cap-amounts[i],alloc[i]); amounts[i]+=v; delivered+=v
        if not delivered: raise ValidationError('allocation stalled')
        remaining-=delivered
    return amounts

def simulate(c):
    integer(c.get('pool_cents'),'pool_cents',1,10**12)
    integer(c.get('rounds'),'rounds',1,200)
    integer(c.get('network_bps'),'network_bps',0,100000)
    integer(c.get('reinforcement_power'),'reinforcement_power',1,3)
    entrants=array(c.get('entrants'),'entrants',200)
    if len(entrants)<2: raise ValidationError('at least two entrants required')
    unique(entrants,'id','entrant.id')
    for e in entrants:
        integer(e.get('quality_units'),'quality_units',1,10000)
        integer(e.get('initial_exposure_units'),'initial_exposure_units',1,10000)
        flag(e.get('newcomer'),'newcomer')
    p=c['policy']; capbps=integer(p.get('max_share_bps'),'max_share_bps',1,10000)
    reservebps=integer(p.get('newcomer_reserve_bps'),'newcomer_reserve_bps',0,10000)
    pool=c['pool_cents']; cap=pool*capbps//10000
    if cap*len(entrants)<pool: raise ValidationError('cap infeasible for this population and pool')
    news=[e['id'] for e in entrants if e['newcomer']]
    if reservebps and not news: raise ValidationError('newcomer reserve has no eligible recipient')
    reserve=pool*reservebps//10000; base=apportion(reserve,[(i,1) for i in news])
    if any(v>cap for v in base.values()): raise ValidationError('newcomer floor exceeds cap')
    def run(governed):
        previous=apportion(pool,[(e['id'],e['initial_exposure_units']) for e in entrants]); history=[]
        for t in range(c['rounds']):
            weights=[(e['id'],e['quality_units']*(F(1)+F(c['network_bps'],10000)*F(previous[e['id']],pool)*len(entrants))**c['reinforcement_power']) for e in entrants]
            current=capped_allocate(pool,weights,cap,base) if governed else apportion(pool,weights)
            history.append({'round':t+1,'allocations_cents':current,'total_cents':sum(current.values()),
                            'hhi':float(sum(F(v,pool)**2 for v in current.values())),
                            'max_share':max(current.values())/pool,
                            'newcomer_share':sum(current[i] for i in news)/pool})
            previous=current
        return history
    return signed({'market_id':identifier(c.get('market_id'),'market_id'),'data_origin':'SYNTHETIC_POLICY_EXPERIMENT',
                   'pool_cents_per_round':pool,'baseline':run(False),'policy':run(True),
                   'assumptions':'Fixed pool, fixed entrant qualities, no price response, entry cost, production or demand creation. Reallocating exposure/value does not create new income.',
                   'real_funds_moved':False},'simulation_hash')
