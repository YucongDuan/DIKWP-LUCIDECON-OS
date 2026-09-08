import unittest,copy,tempfile,json,random,sys,subprocess
from pathlib import Path
from lucidecon.common import *
from lucidecon.samples import base_case,cases,market,settlement
from lucidecon.engine import assess,public_receipt
from lucidecon.validation import validate_case
from lucidecon.routing import route
from lucidecon.economics import stress
from lucidecon.settlement import settle,apportion
from lucidecon.simulation import simulate,capped_allocate
from lucidecon.journal import append,verify,outcome
from lucidecon.reporting import save_assessment
from lucidecon.trace import semantic_trace

class AssessmentTests(unittest.TestCase):
    def test_reference_statuses(self):
        expected=['ROBUST_WITHIN_DECLARED_SCENARIOS','ROBUST_WITHIN_DECLARED_SCENARIOS','BOUNDED_PILOT_ONLY','NO_CURRENT_PATH_IN_SCOPE','INSUFFICIENT_EVIDENCE','RESOURCE_BLOCKED','BLOCKED_BY_RIGHTS']
        self.assertEqual([assess(x)['results'][0]['status'] for x in cases().values()],expected)
    def test_deterministic(self): self.assertEqual(assess(base_case()),assess(base_case()))
    def test_no_input_mutation(self):
        c=base_case();before=canonical(c);assess(c);self.assertEqual(before,canonical(c))
    def test_synthetic_is_not_empirical(self):
        r=assess(base_case());self.assertFalse(r['empirical_validation']);self.assertEqual(r['data_origin'],'SYNTHETIC')
    def test_no_person_score(self): self.assertIsNone(assess(base_case())['global_person_score'])
    def test_receipt_minimized(self):
        p=public_receipt(assess(base_case()));self.assertNotIn('results',p);self.assertNotIn('owner_alias',p);self.assertNotIn('resources',p)
    def test_actual_numbers(self):
        r=assess(base_case())['results'][0];self.assertEqual(r['summary']['worst_net_cents'],29400);self.assertEqual(r['summary']['prefund_cents'],101400)
    def test_evidence_missing_not_no_path(self):
        c=cases()['no-current-path'];c['evidence']=[]
        self.assertEqual(assess(c)['portfolio_status'],'EVIDENCE_INCOMPLETE_NOT_A_NO_PATH_PROOF')
    def test_evidence_expiry(self):
        c=base_case();c['as_of']='2026-12-02';c['consent']['expires_on']='2027-01-01'
        self.assertEqual(assess(c)['results'][0]['status'],'INSUFFICIENT_EVIDENCE')
    def test_evidence_future(self):
        c=base_case();c['evidence'][0]['observed_on']='2026-10-01'
        self.assertFalse(assess(c)['results'][0]['evidence']['passed'])
    def test_operation_scope(self):
        c=base_case();c['evidence'][1]['operations']=['other.operation'];self.assertFalse(assess(c)['results'][0]['evidence']['passed'])
    def test_duplicates_do_not_raise_capability(self):
        c=base_case();c['evidence'].append(copy.deepcopy(c['evidence'][0]))
        with self.assertRaises(ValidationError): assess(c)
    def test_missing_role_not_averaged(self):
        c=base_case();c['evidence'][-1]['roles']=['D','I','K','W']
        self.assertIn('ROLE_P',assess(c)['results'][0]['evidence']['missing'])
    def test_rights_cannot_be_offset(self):
        c=base_case();c['opportunities'][0]['rights']['lawful']=False;c['opportunities'][0]['economics']['unit_price_cents']=[1000000,1000000]
        self.assertEqual(assess(c)['results'][0]['status'],'BLOCKED_BY_RIGHTS')
    def test_trace_explicit(self):
        c=base_case();t=semantic_trace(c,assess(c));ids={r['id'] for r in t['records']}
        self.assertEqual(len(t['allowed_role_pairs']),25)
        for e in t['edges']: self.assertIn(e['source'],ids);self.assertIn(e['target'],ids);self.assertTrue(e['generated_content'])
    def test_no_all_pairs_claim(self): self.assertFalse(semantic_trace(base_case(),assess(base_case()))['all_25_pairs_executed'])

class ValidationTests(unittest.TestCase):
    def assert_bad(self,fn):
        c=base_case();fn(c)
        with self.assertRaises(ValidationError): validate_case(c)
    def test_expired_consent(self): self.assert_bad(lambda c:c['consent'].update(expires_on='2026-09-06'))
    def test_revoked_consent(self): self.assert_bad(lambda c:c['consent'].update(revoked=True))
    def test_not_granted(self): self.assert_bad(lambda c:c['consent'].update(granted=False))
    def test_purpose_binding(self): self.assert_bad(lambda c:c.update(purpose='other'))
    def test_owner_binding(self): self.assert_bad(lambda c:c.update(owner_alias='other'))
    def test_boolean_string(self): self.assert_bad(lambda c:c['consent'].update(granted='true'))
    def test_bool_not_money(self): self.assert_bad(lambda c:c['resources'].update(spendable_cents=True))
    def test_negative_budget(self): self.assert_bad(lambda c:c['resources'].update(spendable_cents=-1))
    def test_nan_money(self): self.assert_bad(lambda c:c['resources'].update(spendable_cents=float('nan')))
    def test_fractional_cent(self): self.assert_bad(lambda c:c['resources'].update(spendable_cents=100.5))
    def test_currency(self): self.assert_bad(lambda c:c['opportunities'][0]['economics'].update(currency='EUR'))
    def test_inverted_interval(self): self.assert_bad(lambda c:c['opportunities'][0]['economics'].update(demand_units=[10,1]))
    def test_zero_delivery_duration(self): self.assert_bad(lambda c:c['opportunities'][0]['economics'].update(delivery_minutes_per_unit=0))
    def test_renamed_same_scenarios(self):
        def edit(c): c['opportunities'][0]['scenarios'][1].update(price_bps=10000,demand_bps=10000,cost_bps=10000)
        self.assert_bad(edit)
    def test_one_scenario(self): self.assert_bad(lambda c:c['opportunities'][0].update(scenarios=c['opportunities'][0]['scenarios'][:1]))
    def test_missing_opportunities(self): self.assert_bad(lambda c:c.update(opportunities=[]))
    def test_duplicate_json_keys(self):
        with self.assertRaises(ValidationError): parse('{"a":1,"a":2}')
    def test_json_nan_rejected(self):
        with self.assertRaises(ValidationError): parse('{"a":NaN}')
    def test_json_infinity_rejected(self):
        with self.assertRaises(ValidationError): parse('{"a":Infinity}')
    def test_input_limit(self):
        with self.assertRaises(ValidationError): parse(' '*2_000_001)
    def test_identifier_path(self): self.assert_bad(lambda c:c.update(case_id='../bad'))
    def test_v1_rejected(self): self.assert_bad(lambda c:c.update(schema_version='1.0'))

class RoutingTests(unittest.TestCase):
    def op(self):return base_case()['opportunities'][0]
    def test_egress_gate(self):
        r=route(self.op());self.assertEqual(r['selected']['id'],'local-reviewed-code');self.assertIn('EGRESS_BYTES_ABOVE_CEILING',r['rejected'][0]['reasons'])
    def test_unknown_energy_not_zero(self):
        o=self.op();o['routes'][0]['energy']=None;r=route(o)
        self.assertEqual(r['selection_rule'],'COST_FALLBACK_ENERGY_NOT_RANKABLE');self.assertFalse(r['energy_is_globally_minimal'])
    def test_unknown_with_budget_blocked(self):
        o=self.op();o['routes'][0]['energy']=None;o['route_gates']['max_energy_j']=10000
        self.assertIsNone(route(o)['selected'])
    def test_mismatched_boundary(self):
        o=self.op();o['routes'][0]['energy']['boundary']='GPU-only'
        self.assertIn('local-reviewed-code',route(o)['unknown_energy_ids'])
    def test_upper_energy_budget(self):
        o=self.op();o['route_gates']['max_energy_j']=80;self.assertIsNone(route(o)['selected'])
    def test_authorization(self):
        o=self.op();o['routes'][0]['authorized']=False;self.assertIsNone(route(o)['selected'])
    def test_quality_gate(self):
        o=self.op();o['routes'][0]['quality_bps']=8999;self.assertIsNone(route(o)['selected'])
    def test_reliability_gate(self):
        o=self.op();o['routes'][0]['reliability_bps']=8999;self.assertIsNone(route(o)['selected'])
    def test_no_routes(self):
        o=self.op();o['routes']=[];self.assertEqual(route(o)['status'],'NO_FEASIBLE_EXECUTION_ROUTE')
    def test_pareto_member(self):
        r=route(self.op());self.assertIn(r['selected']['id'],r['pareto_ids'])

class EconomicsTests(unittest.TestCase):
    def test_negative_margin_bounds(self):
        c=cases()['no-current-path'];s=assess(c)['results'][0]['scenarios'][0]
        self.assertLessEqual(s['net_cash_cents'][0],s['net_cash_cents'][1]);self.assertEqual(s['net_cash_cents'][0],-23600)
    def test_zero_capacity(self):
        c=base_case();c['resources']['available_minutes']=0;s=assess(c)['results'][0]['scenarios'][0]
        self.assertEqual(s['deliverable_units'],[0,0]);self.assertEqual(s['net_cash_cents'],[-15000,-15000])
    def test_interval_contains_enumerated_corners(self):
        c=base_case();e=c['opportunities'][0]['economics'];r=c['resources'];s=c['opportunities'][0]['scenarios'][0]
        z=stress(e,r,s,200)
        for q in range(8,13):
            for price in (20000,26000):
                for cost in (4000,7000):
                    v=q*(price-cost-200)-15000
                    self.assertLessEqual(z['net_cash_cents'][0],v);self.assertGreaterEqual(z['net_cash_cents'][1],v)
    def test_setup_cost_included(self):
        c=base_case();a=assess(c)['results'][0]['summary'];c['opportunities'][0]['economics']['upfront_cents']+=100
        b=assess(c)['results'][0]['summary'];self.assertEqual(a['worst_net_cents']-100,b['worst_net_cents'])
    def test_goal_reopen(self):
        r=assess(cases()['no-current-path'])['results'][0];self.assertTrue(any('shortfall_cents' in str(x) for x in r['reopen_conditions']))

class SettlementTests(unittest.TestCase):
    def test_exact_example(self):
        s=settle(settlement());self.assertEqual(s['held_cents'],14401);self.assertEqual(s['paid_cents'],57602)
    def test_disputed_not_reallocated(self):
        c=settlement();a=settle(c);c['contributions'][2]['status']='ACCEPTED';b=settle(c)
        self.assertEqual([x['amount_cents'] for x in a['allocations']],[x['amount_cents'] for x in b['allocations']])
    def test_repair_exceeds_gross(self):
        c=settlement();c['repair_claim_cents']=150000;r=settle(c)
        self.assertEqual(r['repair_reserve_cents'],100003);self.assertEqual(r['repair_shortfall_cents'],49997);self.assertEqual(r['paid_cents'],0)
    def test_no_claimants_holds_remainder(self):
        c=settlement();c['contributions']=[];r=settle(c);self.assertEqual(r['held_cents'],72003)
    def test_zero_weights_hold(self):
        c=settlement()
        for x in c['contributions']:x['units']=0
        self.assertEqual(settle(c)['held_cents'],72003)
    def test_rights_hold_all(self):
        c=settlement();c['policy']['rights_clear']=False;r=settle(c);self.assertEqual(r['held_cents'],c['gross_cents']);self.assertEqual(r['paid_cents'],0)
    def test_policy_total_invalid(self):
        c=settlement();c['policy'].update(commons_bps=9000,newcomer_bps=9000)
        with self.assertRaises(ValidationError):settle(c)
    def test_duplicate_contribution(self):
        c=settlement();c['contributions'].append(copy.deepcopy(c['contributions'][0]))
        with self.assertRaises(ValidationError):settle(c)
    def test_zero_gross(self):
        c=settlement();c['gross_cents']=0;self.assertTrue(settle(c)['conservation_ok'])
    def test_cent_rounding(self):self.assertEqual(apportion(1,[('b',1),('a',1)]),{'a':1,'b':0})
    def test_random_conservation(self):
        rng=random.Random(402)
        for _ in range(250):
            c=settlement();c['gross_cents']=rng.randrange(0,1000000);c['repair_claim_cents']=rng.randrange(0,2000000)
            c['policy']['commons_bps']=rng.randrange(0,10001);c['policy']['newcomer_bps']=rng.randrange(0,10001-c['policy']['commons_bps'])
            for x in c['contributions']:x['units']=rng.randrange(0,100)
            r=settle(c);self.assertEqual(c['gross_cents'],sum(r[k] for k in ['repair_reserve_cents','commons_cents','newcomer_cents','paid_cents','held_cents']))

class MarketTests(unittest.TestCase):
    def test_fixed_pool(self):
        r=simulate(market())
        for run in ('baseline','policy'):
            for x in r[run]:self.assertEqual(x['total_cents'],100000)
    def test_policy_cap(self):
        for x in simulate(market())['policy']: self.assertLessEqual(max(x['allocations_cents'].values()),20000)
    def test_reserve_floor(self):
        for x in simulate(market())['policy']:self.assertGreaterEqual(x['newcomer_share'],.2)
    def test_infeasible_cap(self):
        c=market();c['policy']['max_share_bps']=500
        with self.assertRaises(ValidationError): simulate(c)
    def test_no_eligible_newcomer(self):
        c=market()
        for x in c['entrants']: x['newcomer']=False
        with self.assertRaises(ValidationError): simulate(c)
    def test_reinforcement_not_universal(self):
        a=market();b=market();b['reinforcement_power']=1
        self.assertGreater(simulate(a)['baseline'][-1]['max_share'],simulate(b)['baseline'][-1]['max_share'])
    def test_policy_can_increase_concentration(self):
        c=market();c['reinforcement_power']=1;r=simulate(c)
        self.assertGreater(r['policy'][-1]['hhi'],r['baseline'][-1]['hhi'])
    def test_deterministic(self):self.assertEqual(simulate(market()),simulate(market()))

class LedgerTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name)/'ledger.jsonl'
    def tearDown(self):self.tmp.cleanup()
    def seed(self):
        append(self.p,'INPUT',{'x':1},'tester');append(self.p,'OUTPUT',{'x':2},'tester')
    def test_valid(self):self.seed();self.assertTrue(verify(self.p)['valid'])
    def test_missing(self):self.assertFalse(verify(self.p)['valid'])
    def test_empty(self):self.p.write_text('');self.assertFalse(verify(self.p)['valid'])
    def test_changed_payload(self):
        self.seed();s=self.p.read_text().replace('"x":1','"x":9');self.p.write_text(s);self.assertFalse(verify(self.p)['valid'])
    def test_invalid_keys_no_crash(self):self.p.write_text('{}\n');self.assertFalse(verify(self.p)['valid'])
    def test_reorder(self):
        self.seed();self.p.write_text('\n'.join(self.p.read_text().splitlines()[::-1])+'\n');self.assertFalse(verify(self.p)['valid'])
    def test_sequence_checked_even_after_rehash(self):
        self.seed();items=[parse(x) for x in self.p.read_text().splitlines()];items[1]['seq']=20;items[1]['hash']=digest({k:v for k,v in items[1].items() if k!='hash'})
        self.p.write_text('\n'.join(canonical(x) for x in items)+'\n');self.assertFalse(verify(self.p)['valid'])
    def test_tail_truncation_needs_checkpoint(self):
        self.seed();head=verify(self.p)['head'];self.p.write_text(self.p.read_text().splitlines()[0]+'\n')
        self.assertTrue(verify(self.p)['valid']);self.assertFalse(verify(self.p,head)['valid'])
    def test_no_append_to_invalid_chain(self):
        self.p.write_text('{}\n')
        with self.assertRaises(ValidationError): append(self.p,'X',{},'a')
    def test_lock(self):
        Path(str(self.p)+'.lock').write_text('')
        with self.assertRaises(ValidationError):append(self.p,'X',{},'a')
    def test_output_no_overwrite(self):
        c=base_case();a=assess(c);d=Path(self.tmp.name)/'run';save_assessment(c,a,d)
        with self.assertRaises(ValueError):save_assessment(c,a,d)
    def test_outcome_bound(self):
        a=assess(base_case());e={'id':'o1','actor':'a','assessment_hash':'bad','opportunity_id':'local-maintenance','result':'WORSENED','evidence_ref':'ref'}
        with self.assertRaises(ValidationError):outcome(a,e)
    def test_outcome_harm(self):
        a=assess(base_case());e={'id':'o1','actor':'a','assessment_hash':a['assessment_hash'],'opportunity_id':'local-maintenance','result':'WORSENED','evidence_ref':'ref'}
        self.assertEqual(outcome(a,e)['decision'],'PAUSE_AND_REVIEW_HARM')
    def test_not_measured_stays_open(self):
        a=assess(base_case());e={'id':'o1','actor':'a','assessment_hash':a['assessment_hash'],'opportunity_id':'local-maintenance','result':'NOT_MEASURED'}
        self.assertEqual(outcome(a,e)['decision'],'OUTCOME_DEBT_OPEN')

if __name__=='__main__':unittest.main()

class JointRouteTests(unittest.TestCase):
    def test_economics_before_energy(self):
        c=base_case();o=c['opportunities'][0];bad=copy.deepcopy(o['routes'][0]);bad['id']='low-energy-expensive';bad['energy']['joules']=[1,2];bad['cost_cents']=1500;o['routes'].append(bad)
        c['resources']['spendable_cents']=105000
        r=assess(c)['results'][0]
        self.assertEqual(r['execution']['selected']['id'],'local-reviewed-code')
        self.assertEqual(len(r['execution']['economic_route_checks']),2)
    def test_malformed_case_validation(self):
        with self.assertRaises(ValidationError): assess({'schema_version':'2.0'})
