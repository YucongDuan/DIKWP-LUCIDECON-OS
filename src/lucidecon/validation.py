from .common import *
ROLES=('D','I','K','W','P')
MODES=('MODEL_NATIVE','GENERATED_CODE','LOCAL_API','REMOTE_API','BROWSER','GUI','FEDERATED_NODE','HUMAN','PHYSICAL')

def _validate_case(c: dict) -> None:
    if not isinstance(c,dict): raise ValidationError('case must be an object')
    if c.get('schema_version')!='2.0': raise ValidationError('schema_version must be 2.0; v1 needs explicit migration')
    identifier(c.get('case_id'),'case_id'); text(c.get('purpose'),'purpose'); text(c.get('owner_alias'),'owner_alias')
    now=day(c.get('as_of'),'as_of')
    integer(c.get('horizon_days'),'horizon_days',1,365)
    if c.get('data_origin') not in ('SYNTHETIC','USER_SUBMITTED'): raise ValidationError('data_origin required')
    auth=c['consent']
    flag(auth.get('granted'),'consent.granted'); flag(auth.get('revoked'),'consent.revoked')
    text(auth.get('purpose'),'consent.purpose'); text(auth.get('owner_alias'),'consent.owner_alias')
    expires=day(auth.get('expires_on'),'consent.expires_on')
    if not auth['granted'] or auth['revoked'] or expires<now or auth['purpose']!=c['purpose'] or auth['owner_alias']!=c['owner_alias']:
        raise ValidationError('consent missing, revoked, expired or not bound to owner and purpose')
    r=c['resources']; identifier(r.get('currency'),'currency')
    for k in ('spendable_cents','max_loss_cents','target_surplus_cents'):
        integer(r.get(k),k,0,10**9)
    integer(r.get('available_minutes'),'available_minutes',0,1_000_000)
    ev=array(c.get('evidence'),'evidence',300); unique(ev,'id','evidence.id')
    for e in ev:
        if e.get('kind') not in ('DEMAND','DELIVERY','ACCESS','CAPABILITY'): raise ValidationError('unknown evidence kind')
        if e.get('basis') not in ('REVIEWED','OBSERVED','SELF_REPORT'): raise ValidationError('unknown evidence basis')
        if e.get('outcome') not in ('PASS','FAIL','UNCLEAR'): raise ValidationError('unknown evidence outcome')
        text(e.get('source_ref'),'source_ref'); integer(e.get('sample_n'),'sample_n',0,1_000_000)
        scopes=array(e.get('operations'),'evidence.operations',50)
        if not scopes: raise ValidationError('evidence requires an operation scope')
        for x in scopes: identifier(x,'operation')
        for x in array(e.get('roles',[]),'roles',5):
            if x not in ROLES: raise ValidationError('unknown DIKWP role')
        a,b=day(e.get('observed_on'),'observed_on'),day(e.get('valid_until'),'valid_until')
        if b<a: raise ValidationError('evidence expires before observation')
        if e['basis']=='REVIEWED': text(e.get('reviewer'),'reviewer')
    ops=array(c.get('opportunities'),'opportunities',30)
    if not ops: raise ValidationError('at least one explicit opportunity is required')
    unique(ops,'id','opportunity.id')
    for o in ops:
        text(o.get('title'),'title'); identifier(o.get('operation'),'operation')
        roles=array(o.get('required_roles'),'required_roles',5)
        if not roles or len(roles)!=len(set(roles)) or any(x not in ROLES for x in roles): raise ValidationError('invalid required_roles')
        for k in ('lawful','data_consent','reversible','human_review'):
            flag(o['rights'].get(k),'rights.'+k)
        e=o['economics']
        if e.get('currency')!=r['currency']: raise ValidationError('currency mismatch; no automatic exchange rate')
        for k in ('upfront_cents','fixed_period_cents'): integer(e.get(k),k,0,10**9)
        for k in ('unit_price_cents','unit_cost_cents','acquisition_cents'): interval(e.get(k),k,0,10**8)
        interval(e.get('demand_units'),'demand_units',0,10_000)
        integer(e.get('setup_minutes'),'setup_minutes',0,1_000_000)
        integer(e.get('delivery_minutes_per_unit'),'delivery_minutes_per_unit',1,1_000_000)
        scenarios=array(o.get('scenarios'),'scenarios',20)
        if len(scenarios)<2: raise ValidationError('at least two explicit scenarios required')
        unique(scenarios,'id','scenario.id')
        for s in scenarios:
            for k in ('price_bps','demand_bps','cost_bps'): integer(s.get(k),k,0,30_000)
        if len({(s['price_bps'],s['demand_bps'],s['cost_bps']) for s in scenarios})<2:
            raise ValidationError('scenario names alone do not establish different scenarios')
        g=o['route_gates']
        if g.get('data_class') not in ('PUBLIC','INTERNAL','SENSITIVE'): raise ValidationError('invalid data_class')
        for k in ('min_quality_bps','min_reliability_bps'): integer(g.get(k),k,0,10000)
        for k in ('max_cost_cents','max_latency_ms','max_egress_bytes'): integer(g.get(k),k,0,10**9)
        if g.get('max_energy_j') is not None: integer(g['max_energy_j'],'max_energy_j',0,10**9)
        text(g.get('energy_boundary'),'energy_boundary')
        routes=array(o.get('routes'),'routes',40); unique(routes,'id','route.id')
        for a in routes:
            if a.get('mode') not in MODES: raise ValidationError('unknown route mode')
            flag(a.get('authorized'),'route.authorized')
            for k in ('cost_cents','latency_ms','egress_bytes'): integer(a.get(k),k,0,10**9)
            for k in ('quality_bps','reliability_bps'): integer(a.get(k),k,0,10000)
            if any(x not in ('PUBLIC','INTERNAL','SENSITIVE') for x in array(a.get('data_classes'),'route.data_classes',3)): raise ValidationError('unknown data class')
            energy=a.get('energy')
            if energy is not None:
                interval(energy.get('joules'),'energy.joules',0,10**9)
                if energy.get('basis') not in ('MEASURED','ESTIMATED'): raise ValidationError('energy basis required')
                text(energy.get('boundary'),'energy.boundary')
                if energy['basis']=='MEASURED': text(energy.get('measurement_ref'),'energy.measurement_ref')


def validate_case(c: dict) -> None:
    try:
        _validate_case(c)
    except (KeyError,TypeError,AttributeError) as exc:
        raise ValidationError('Missing or malformed required declaration: '+str(exc)) from exc
