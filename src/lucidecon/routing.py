from .economics import stress

def route(op, resources=None):
    g=op['route_gates']; eligible=[]; rejected=[]; unknown=[]
    for a in op['routes']:
        reasons=[]
        if not a['authorized']: reasons.append('AUTHORIZATION_NOT_DECLARED')
        if g['data_class'] not in a['data_classes']: reasons.append('DATA_CLASS_BLOCKED')
        for k,target in [('quality_bps','min_quality_bps'),('reliability_bps','min_reliability_bps')]:
            if a[k]<g[target]: reasons.append(k.upper()+'_BELOW_FLOOR')
        for k,target in [('cost_cents','max_cost_cents'),('latency_ms','max_latency_ms'),('egress_bytes','max_egress_bytes')]:
            if a[k]>g[target]: reasons.append(k.upper()+'_ABOVE_CEILING')
        e=a.get('energy'); comparable=e is not None and e['boundary']==g['energy_boundary']
        if g['max_energy_j'] is not None:
            if not comparable: reasons.append('ENERGY_BUDGET_CANNOT_BE_VERIFIED')
            elif e['joules'][1]>g['max_energy_j']: reasons.append('ENERGY_ABOVE_BUDGET')
        if reasons: rejected.append({'id':a['id'],'reasons':reasons})
        else:
            eligible.append(a)
            if not comparable: unknown.append(a['id'])
    if not eligible: return {'status':'NO_FEASIBLE_EXECUTION_ROUTE','selected':None,'rejected':rejected,'unknown_energy_ids':unknown}
    economics=[]; economic_filter='NOT_REQUESTED'
    if resources is not None:
        robust=[]; pilots=[]
        for a in eligible:
            rows=[stress(op['economics'],resources,s,a['cost_cents']) for s in op['scenarios']]
            worst=min(x['net_cash_cents'][0] for x in rows); best=max(x['net_cash_cents'][1] for x in rows)
            prefund=max(x['prefund_cents'] for x in rows)
            affordable=prefund<=resources['spendable_cents'] and worst>=-resources['max_loss_cents'] and op['economics']['setup_minutes']<=resources['available_minutes']
            record={'id':a['id'],'worst_net_cents':worst,'best_net_cents':best,'prefund_cents':prefund,'affordable_within_loss_limit':affordable}
            economics.append(record)
            if affordable and worst>=resources['target_surplus_cents']: robust.append(a)
            elif affordable and best>=resources['target_surplus_cents']: pilots.append(a)
        if robust: eligible=robust; economic_filter='ROBUST_ECONOMIC_SUBSET'
        elif pilots: eligible=pilots; economic_filter='BOUNDED_PILOT_ECONOMIC_SUBSET'
        else: economic_filter='NO_ECONOMICALLY_FEASIBLE_ROUTE_DIAGNOSTIC_ONLY'
    comparable=[a for a in eligible if a['id'] not in unknown]
    if comparable:
        pool=comparable; selection='MIN_UPPER_ESTIMATED_OR_MEASURED_JOULES_WITHIN_COMPARABLE_SUBSET'
        key=lambda a:(a['energy']['joules'][1],a['cost_cents'],a['latency_ms'],a['egress_bytes'],a['id'])
    else:
        pool=eligible; selection='COST_FALLBACK_ENERGY_NOT_RANKABLE'
        key=lambda a:(a['cost_cents'],a['latency_ms'],a['egress_bytes'],a['id'])
    selected=sorted(pool,key=key)[0]
    def vec(a):
        v=[a['cost_cents'],a['latency_ms'],a['egress_bytes'],-a['quality_bps'],-a['reliability_bps']]
        return ([a['energy']['joules'][1]]+v) if comparable else v
    frontier=[a['id'] for a in pool if not any(all(x<=y for x,y in zip(vec(b),vec(a))) and any(x<y for x,y in zip(vec(b),vec(a))) for b in pool)]
    return {'status':'ROUTE_PLANNED_NOT_EXECUTED','selected':selected,'selection_rule':selection,
            'pareto_ids':sorted(frontier),'unknown_energy_ids':unknown,'rejected':rejected,
            'economic_route_checks':economics,'economic_filter':economic_filter,
            'energy_is_globally_minimal':False,'metrics_independently_measured_by_runtime':False,
            'boundary':'Per delivered unit. Energy boundaries must match; unknown is never zero. No model, GUI, remote node or paid service was invoked.'}
