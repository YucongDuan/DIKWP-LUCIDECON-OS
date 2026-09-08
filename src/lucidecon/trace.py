from .common import digest

def semantic_trace(case,result):
    records=[{'id':'D.input','role':'D','content':{'input_hash':digest(case),'source':'private_input.json'}},
             {'id':'I.gaps','role':'I','content':[{'id':r['opportunity_id'],'evidence_gaps':r['evidence']['missing'],'resource_blockers':r['resource_blockers']} for r in result['results']]},
             {'id':'W.policy','role':'W','content':{'consent':case['consent'],'resources':case['resources'],'rights':{o['id']:o['rights'] for o in case['opportunities']}}},
             {'id':'P.assess','role':'P','content':{'operation':'lucidecon.engine.assess','input':'D.input','output':'K.result'}},
             {'id':'K.result','role':'K','content':{'assessment_hash':result['assessment_hash'],'scope':result['purpose']}},
             {'id':'P.replay','role':'P','content':{'operation':'recompute from private_input.json and compare assessment hash','source':'K.result'}},
             {'id':'D.replay','role':'D','content':{'boundary':'Claimed only when the replay command returns equality; no external market verification.'}}]
    edges=[('D.input','P.assess','Normalized declared input'),('W.policy','P.assess','Hard consent, rights, budget and loss gates'),
           ('P.assess','K.result','Calculated scoped outcome'),('K.result','I.gaps','Preserve missing evidence and blockers'),
           ('K.result','P.replay','Request deterministic regeneration'),('P.replay','D.replay','Target equality criterion, not a pre-executed proof')]
    return {'records':records,'edges':[{'source':a,'target':b,'generated_content':c} for a,b,c in edges],
            'allowed_role_pairs':[a+'->'+b for a in 'DIKWP' for b in 'DIKWP'],
            'all_25_pairs_executed':False,'reverse_replay_performed':False,'scope':'Engineering interpretation, not certification of an ontology.'}
