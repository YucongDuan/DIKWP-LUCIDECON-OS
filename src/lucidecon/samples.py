from copy import deepcopy

def base_case():
    op='local.workflow.maintenance'
    evidence=[]
    for kind in ('DEMAND','DELIVERY','ACCESS','CAPABILITY'):
        evidence.append({'id':'ev-'+kind.lower(),'kind':kind,'basis':'REVIEWED','outcome':'PASS',
                         'source_ref':'synthetic-fixture:'+kind.lower(),'reviewer':'fictional-independent-reviewer',
                         'sample_n':4,'operations':[op],'roles':['D','I','K','W','P'] if kind=='CAPABILITY' else [],
                         'observed_on':'2026-09-01','valid_until':'2026-12-01'})
    return {'schema_version':'2.0','case_id':'ordinary-pilot','as_of':'2026-09-07','horizon_days':90,'data_origin':'SYNTHETIC',
            'purpose':'Test one bounded 90-day service path without risking protected living reserves.',
            'owner_alias':'participant-demo','consent':{'granted':True,'revoked':False,'owner_alias':'participant-demo',
            'purpose':'Test one bounded 90-day service path without risking protected living reserves.','expires_on':'2026-12-01'},
            'resources':{'currency':'USD','spendable_cents':150000,'available_minutes':7200,'max_loss_cents':30000,'target_surplus_cents':25000},
            'evidence':evidence,'opportunities':[{'id':'local-maintenance','title':'Local small-business workflow maintenance / 本地小企业流程维护',
            'operation':op,'required_roles':['D','I','K','W','P'],
            'rights':{'lawful':True,'data_consent':True,'reversible':True,'human_review':True},
            'economics':{'currency':'USD','upfront_cents':10000,'fixed_period_cents':5000,
                         'unit_price_cents':[20000,26000],'unit_cost_cents':[3000,5000],
                         'acquisition_cents':[1000,2000],'demand_units':[8,12],
                         'setup_minutes':600,'delivery_minutes_per_unit':240},
            'scenarios':[{'id':'baseline','price_bps':10000,'demand_bps':10000,'cost_bps':10000},
                         {'id':'price-and-demand-shock','price_bps':8000,'demand_bps':7500,'cost_bps':12000}],
            'route_gates':{'data_class':'INTERNAL','min_quality_bps':9000,'min_reliability_bps':9000,
                           'max_cost_cents':2000,'max_latency_ms':600000,'max_egress_bytes':0,
                           'max_energy_j':None,'energy_boundary':'compute-and-network-per-delivered-unit'},
            'routes':[{'id':'local-reviewed-code','mode':'GENERATED_CODE','authorized':True,'data_classes':['PUBLIC','INTERNAL'],
                       'quality_bps':9500,'reliability_bps':9500,'cost_cents':200,'latency_ms':60000,'egress_bytes':0,
                       'energy':{'joules':[60,110],'basis':'ESTIMATED','boundary':'compute-and-network-per-delivered-unit'}},
                      {'id':'remote-cheap','mode':'REMOTE_API','authorized':True,'data_classes':['PUBLIC','INTERNAL'],
                       'quality_bps':9800,'reliability_bps':9900,'cost_cents':100,'latency_ms':20000,'egress_bytes':500000,
                       'energy':{'joules':[40,80],'basis':'ESTIMATED','boundary':'compute-and-network-per-delivered-unit'}}]}]}

def cases():
    a=base_case(); b=deepcopy(a);b['case_id']='late-entrant'
    b['opportunities'][0]['title']='Late entrant: accountable local maintenance / 后进入者的本地责任服务'
    p=deepcopy(a);p['case_id']='conditional-pilot';p['resources']['target_surplus_cents']=60000
    n=deepcopy(a);n['case_id']='no-current-path';o=n['opportunities'][0]
    o['title']='Generic summary resale / 同质化摘要转售'
    o['operation']='generic.summary.resale'
    for e in n['evidence']: e['operations']=['generic.summary.resale']; e['source_ref']='synthetic-summary:'+e['kind'].lower()
    o['economics'].update(upfront_cents=15000,fixed_period_cents=5000,unit_price_cents=[300,500],unit_cost_cents=[150,250],acquisition_cents=[100,300],demand_units=[2,8],setup_minutes=300,delivery_minutes_per_unit=30)
    u=deepcopy(a);u['case_id']='insufficient-evidence'
    for e in u['evidence']: e['basis']='SELF_REPORT'
    r=deepcopy(a);r['case_id']='limited-budget';r['resources']['spendable_cents']=10000
    h=deepcopy(a);h['case_id']='consent-boundary';h['opportunities'][0]['rights']['data_consent']=False
    return {c['case_id']:c for c in (a,b,p,n,u,r,h)}

def market():
    return {'market_id':'fixed-pool-first-mover','pool_cents':100000,'rounds':12,'network_bps':16000,'reinforcement_power':2,
            'entrants':[{'id':f'e{i:02d}','quality_units':100,'initial_exposure_units':1000 if i==0 else 10,'newcomer':i>=6} for i in range(10)],
            'policy':{'max_share_bps':2000,'newcomer_reserve_bps':2000}}

def settlement():
    return {'event_id':'contribution-demo','currency':'USD','gross_cents':100003,'repair_claim_cents':10000,
            'policy':{'id':'negotiated-demo-not-universal','agreed':True,'rights_clear':True,'commons_bps':1000,'newcomer_bps':1000},
            'contributions':[{'id':'a','roles':['D','I'],'units':3,'status':'ACCEPTED','receipt_ref':'synthetic:need-discovery'},
                             {'id':'b','roles':['K'],'units':5,'status':'ACCEPTED','receipt_ref':'synthetic:delivery'},
                             {'id':'c','roles':['W','P'],'units':2,'status':'DISPUTED','receipt_ref':'synthetic:disputed-review'}]}
