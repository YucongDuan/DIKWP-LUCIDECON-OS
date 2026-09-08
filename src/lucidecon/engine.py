from .common import signed
from .validation import validate_case
from .evidence import evidence_gate
from .routing import route
from .economics import stress

STATUS_ORDER=['ROBUST_WITHIN_DECLARED_SCENARIOS','BOUNDED_PILOT_ONLY','INSUFFICIENT_EVIDENCE',
              'RESOURCE_BLOCKED','NO_CURRENT_PATH_IN_SCOPE','NO_FEASIBLE_EXECUTION_ROUTE','BLOCKED_BY_RIGHTS']

def assess(c):
    validate_case(c); results=[]
    for o in c['opportunities']:
        eg=evidence_gate(c,o); rt=route(o,c['resources']); rights=[k for k,v in o['rights'].items() if not v]
        scenario_rows=[stress(o['economics'],c['resources'],s,rt['selected']['cost_cents'] if rt['selected'] else 0) for s in o['scenarios']]
        r=c['resources']; blockers=[]; reopen=[]
        worst=min(s['net_cash_cents'][0] for s in scenario_rows)
        best=max(s['net_cash_cents'][1] for s in scenario_rows)
        prefund=max(s['prefund_cents'] for s in scenario_rows)
        if prefund>r['spendable_cents']: blockers.append('PRE_FUNDING_BUDGET')
        if worst < -r['max_loss_cents']: blockers.append('LOSS_BUDGET')
        if o['economics']['setup_minutes']>r['available_minutes']: blockers.append('SETUP_TIME_BUDGET')
        if rights: status='BLOCKED_BY_RIGHTS'
        elif not rt['selected']: status='NO_FEASIBLE_EXECUTION_ROUTE'
        elif not eg['passed']: status='INSUFFICIENT_EVIDENCE'
        elif max(x['best_net_cents'] for x in rt['economic_route_checks'])<r['target_surplus_cents']: status='NO_CURRENT_PATH_IN_SCOPE'
        elif blockers or rt['economic_filter']=='NO_ECONOMICALLY_FEASIBLE_ROUTE_DIAGNOSTIC_ONLY': status='RESOURCE_BLOCKED'
        elif all(s['cash_goal_met_at_lower_bound'] for s in scenario_rows): status='ROBUST_WITHIN_DECLARED_SCENARIOS'
        else: status='BOUNDED_PILOT_ONLY'
        if rights: reopen.append({'change':'obtain_valid_rights_and_review','fields':rights})
        if prefund>r['spendable_cents']: reopen.append({'change':'reduce_pre_funding_or_scope','gap_cents':prefund-r['spendable_cents'],'not_a_recommendation_to_borrow':True})
        if worst < -r['max_loss_cents']: reopen.append({'change':'reduce_downside_before_any_pilot','excess_loss_cents':-worst-r['max_loss_cents']})
        if eg['missing']: reopen.append({'change':'collect_task_scoped_evidence','missing':eg['missing']})
        if best<r['target_surplus_cents']: reopen.append({'change':'test_new_price_demand_cost_or_target_assumptions','best_case_shortfall_cents':r['target_surplus_cents']-best})
        if not rt['selected']: reopen.append({'change':'add_a_route_passing_existing_constraints','do_not_silently_lower_gates':True})
        results.append({'opportunity_id':o['id'],'title':o['title'],'status':status,'rights_missing':rights,
            'resource_blockers':blockers,'evidence':eg,'execution':rt,'scenarios':scenario_rows,
            'summary':{'worst_net_cents':worst,'best_net_cents':best,'prefund_cents':prefund,
                       'target_surplus_cents':r['target_surplus_cents']},'reopen_conditions':reopen})
    results.sort(key=lambda a:(STATUS_ORDER.index(a['status']),a['opportunity_id']))
    statuses={x['status'] for x in results}
    if 'ROBUST_WITHIN_DECLARED_SCENARIOS' in statuses: portfolio='SCENARIO_ROBUST_CANDIDATE_PRESENT'
    elif 'BOUNDED_PILOT_ONLY' in statuses: portfolio='PILOT_CANDIDATE_PRESENT'
    elif 'INSUFFICIENT_EVIDENCE' in statuses: portfolio='EVIDENCE_INCOMPLETE_NOT_A_NO_PATH_PROOF'
    else: portfolio='NO_CURRENT_FEASIBLE_PATH_IN_SUBMITTED_SET'
    out={'system':'DIKWP-LUCIDECON-OS','version':'2.0.0','case_id':c['case_id'],'as_of':c['as_of'],
         'purpose':c['purpose'],'horizon_days':c['horizon_days'],'data_origin':c['data_origin'],'currency':r['currency'],
         'portfolio_status':portfolio,'results':results,
         'empirical_validation':False,'automated_external_action':False,'global_person_score':None,
         'privacy':'Local analysis contains potentially sensitive business inputs. Share only the minimized receipt deliberately.',
         'limits':['Inputs, reviews and permissions are declarations, not authenticated facts.',
                   'Each opportunity uses the full stated budget separately; results are not an executable combined portfolio.',
                   'Net cash excludes tax, debt service and personal living costs unless included explicitly; it is not net welfare.',
                   'All units are assumed pre-funded; receivable timing and credit facilities are not modeled.',
                   'Scenario intervals are bounded what-if assumptions, not confidence intervals or probabilities.',
                   'A no-path decision covers only this candidate set, horizon, target and input assumptions.']}
    return signed(out,'assessment_hash')

def public_receipt(result):
    return {k:result[k] for k in ('system','version','case_id','as_of','data_origin','portfolio_status','assessment_hash','empirical_validation')} | {'personal_details_included':False,'warning':'Case aliases and hashes may still be linkable. No automatic publication.'}
