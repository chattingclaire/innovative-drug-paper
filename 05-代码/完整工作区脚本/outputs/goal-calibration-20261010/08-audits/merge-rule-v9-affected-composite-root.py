"""Merge one completed v9 affected pass into the sealed compatible v8 parent.

Keep original prediction/slot bytes and each inherited actual execution origin.
This operation performs no classification and no reference comparison.
"""
import argparse, collections, datetime, hashlib, json
from pathlib import Path

R = Path(__file__).resolve().parents[1]
BASELINE = R/'06-coding/rule-full4481-v8-delta-merged-root'
DIMS = ('S', 'E', 'Ec', 'I', 'F')

def load(p): return json.loads(Path(p).read_bytes())
def bind(p):
    p=Path(p).resolve(); raw=p.read_bytes()
    return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def exact(b):
    actual=bind(b['path'])
    assert all(actual[k]==b[k] for k in ('path','bytes','sha256')),b['path']
def save(p,x):
    with Path(p).open('x',encoding='utf8') as f:
        json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def verify_seal(p,seen=None):
    seen=set() if seen is None else seen
    p=Path(p).resolve()
    if p in seen:return
    seen.add(p);seal=load(p)
    for key in ('files','members','output_files','implementation_files','material_bindings','control_inputs'):
        for b in seal.get(key,[]):exact(b)
    for b in seal.get('ancestor_seals',[]):
        exact(b);verify_seal(b['path'],seen)
def lines(p,slots=False):
    result={}
    for raw in Path(p).read_bytes().splitlines(keepends=True):
        x=json.loads(raw);key=(x['id'],x['dimension']) if slots else x['id']
        assert key not in result
        result[key]=(x,raw)
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preparation',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args();prep=Path(args.preparation).resolve();out=Path(args.output).resolve()
    assert not out.exists(),'Never overwrite an actual or composite result'
    delta=prep/'run-affected-first';plan=load(prep/'impact-closure-plan.json')
    adoption=load(prep/'ROOT-pre-inference-adoption-sidecar.json')
    for key in ('candidate_total_seal','selection','impact_plan','frozen_scope',
                'pre_execution_seal','original_input_lineage','baseline_compatible_seal'):
        exact(adoption[key])
    for b in adoption['required_candidate_members_verified']:exact(b)
    assert adoption['provisional_delta_adoption_by_ROOT'] is True
    assert adoption['same_independent_selector_set'] is True
    assert adoption['baseline_compatible_seal']==bind(BASELINE/'seal.json')
    for key,name in (('impact_plan','impact-closure-plan.json'),('frozen_scope','frozen-scope.json'),
                     ('pre_execution_seal','pre-execution-run-seal.json'),
                     ('original_input_lineage','original-input-lineage-sidecar.json')):
        assert adoption[key]==bind(prep/name),(key,prep)
    assert adoption['selection']==plan['selection']
    assert plan['candidate_delivery']==adoption['candidate_total_seal']
    verify_seal(BASELINE/'seal.json');verify_seal(delta/'seal.json')
    parent_status=load(BASELINE/'composite-status.json')
    assert parent_status['actual_record_N']==4481 and parent_status['actual_dimension_N']==22405
    assert parent_status['technical_failure_dimension_N']==0
    delta_seal=load(delta/'seal.json');freeze=load(delta/'freeze.json')
    assert delta_seal['status']=='sealed_complete_production_provisional_rule_delta_run'
    assert delta_seal['control_inputs']==[bind(prep/'frozen-scope.json')]
    assert freeze['control_inputs']==delta_seal['control_inputs']
    execution=load(delta/'execution.json');delta_N=plan['affected_record_N']
    assert execution['status']=='completed' and execution['actual_record_N']==delta_N
    assert execution['actual_dimension_N']==delta_N*5 and execution['technical_failure_dimension_N']==0
    assert execution['no_reference_read'] and execution['actual_cohort_inference_runs']==1
    assert datetime.datetime.fromisoformat(adoption['at_utc'])<datetime.datetime.fromisoformat(execution['started_at_utc'])
    old=lines(BASELINE/'predictions.jsonl');new=lines(delta/'predictions.jsonl')
    old_slots=lines(BASELINE/'all-dimension-slots.jsonl',True)
    new_slots=lines(delta/'all-dimension-slots.jsonl',True)
    origins=lines(BASELINE/'execution-origin-lineage.jsonl')
    assert len(old)==len(origins)==4481 and len(old_slots)==22405
    assert list(new)==plan['affected_record_ids'] and len(new)==delta_N
    assert len(new_slots)==delta_N*5 and set(new)<=set(old)
    assert set(old_slots)=={(rid,d) for rid in old for d in DIMS}
    assert set(new_slots)=={(rid,d) for rid in new for d in DIMS}
    assert list(old)==[x[0]['id'] for x in origins.values()]
    scope=load(prep/'frozen-scope.json')
    assert freeze['final_candidate_algorithm']==scope['final_candidate_algorithm']==bind(prep/'algorithm-bindings.json')
    assert freeze['final_candidate_pre_execution_seal']==scope['final_candidate_pre_execution_seal']==plan['candidate_freeze']
    assert freeze['final_candidate_delivery_seal']==scope['final_candidate_delivery_seal']==plan['candidate_delivery']
    assert scope['impact_closure_plan']==adoption['impact_plan']
    assert scope['source_packet']==load(prep/'original-input-lineage-sidecar.json')['subset_source']
    assert scope['algorithm_bindings']==bind(prep/'algorithm-bindings.json')
    parent_scope=load(R/'06-coding/rule-full4481-final-v7-root/frozen-scope.json')
    assert list(old)==parent_scope['approved_record_ids'] and scope['approved_record_ids']==list(new)
    for key in ('manual','protocol','prompt'):assert scope[key]==parent_scope[key]
    assert plan['unaffected_inherited_record_N']==4481-delta_N
    label_changes=[];decision_changes=[];log_changes=[]
    for rid,(x,_) in new.items():
        y=old[rid][0]
        assert not x['implementation_errors'] and not y['implementation_errors']
        assert set(x['labels'])==set(y['labels'])==set(x['decisions'])==set(DIMS)
        for d in DIMS:
            assert x['labels'][d]==x['decisions'][d]['value']
            assert x['labels'][d] is None or type(x['labels'][d]) is int and x['labels'][d] in (0,1)
            if d in ('S','E','Ec'):assert x['decisions'][d]==y['decisions'][d],(rid,d)
            if x['labels'][d]!=y['labels'][d]:
                label_changes.append({'id':rid,'dimension':d,'parent_value':y['labels'][d],
                    'delta_value':x['labels'][d],'parent_decision':y['decisions'][d],
                    'delta_decision':x['decisions'][d]})
            if x['decisions'][d]!=y['decisions'][d]:
                decision_changes.append({'id':rid,'dimension':d,'value_changed':x['labels'][d]!=y['labels'][d]})
        for key in ('source_requests','source_relation_traces','relation_traces'):
            if x.get(key)!=y.get(key):log_changes.append({'id':rid,'field':key})
    out.mkdir(parents=True)
    lineage=[];counts={d:collections.Counter() for d in DIMS};algorithm_counts=collections.Counter()
    with (out/'predictions.jsonl').open('xb') as p,(out/'all-dimension-slots.jsonl').open('xb') as s:
        for ordinal,rid in enumerate(old,1):
            selected=rid in new;x,raw=(new if selected else old)[rid]
            p.write(raw);slot_dict=new_slots if selected else old_slots
            prior=origins[rid][0]
            assert prior['corpus_ordinal_1based']==ordinal
            assert prior['actual_prediction_line_sha256']==hashlib.sha256(old[rid][1]).hexdigest()
            assert prior['prediction_line_bytes']==len(old[rid][1])
            for d in DIMS:
                slot,slot_raw=slot_dict[(rid,d)]
                assert slot['rule_value']==x['labels'][d] and not slot['technical_failure']
                s.write(slot_raw)
                key='positive_N' if x['labels'][d]==1 else 'negative_N' if x['labels'][d]==0 else 'lawful_null_N'
                counts[d][key]+=1
            origin=dict(prior)
            if selected:
                origin.update(actual_inference_algorithm='joint-v9-generic-relationship-sol',
                    actual_run_directory=str(delta),source_consumption_log=str(delta/'actual-source-consumption.jsonl'),
                    source_consumption_record_key=rid)
                origin.pop('v8_compatibility_basis',None)
            origin.update(corpus_ordinal_1based=ordinal,id=rid,
                actual_prediction_line_sha256=hashlib.sha256(raw).hexdigest(),prediction_line_bytes=len(raw),
                unchanged_actual_record_bytes_retained=True,
                v9_compatibility_basis='actual_v9_affected_inference' if selected else 'unchanged_input_and_proved_new_gate_not_reached',
                inherited_parent_origin_binding=None if selected else {'path':str(BASELINE/'execution-origin-lineage.jsonl'),
                    'record_key':rid,'line_sha256':hashlib.sha256(origins[rid][1]).hexdigest()})
            lineage.append(origin);algorithm_counts[origin['actual_inference_algorithm']]+=1
    with (out/'execution-origin-lineage.jsonl').open('x',encoding='utf8') as f:
        for x in lineage:f.write(json.dumps(x,ensure_ascii=False,allow_nan=False)+'\n')
    save(out/'v8-compatible-to-v9-actual-changes.json',{'label_changes':label_changes,
        'complete_decision_changes':decision_changes,'source_or_relation_log_changes':log_changes,
        'S_E_Ec_complete_decisions_all_identical':True})
    status={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'status':'complete_v9_compatible_composite_with_explicit_execution_origins',
        'actual_record_N':4481,'actual_dimension_N':22405,'technical_failure_dimension_N':0,
        'lawful_null_N':sum(c['lawful_null_N'] for c in counts.values()),
        'counts':{d:{k:c[k] for k in ('positive_N','negative_N','lawful_null_N')} for d,c in counts.items()},
        'actual_v9_affected_inference_record_N':delta_N,'inherited_compatible_parent_record_N':4481-delta_N,
        'actual_execution_algorithm_record_N':dict(algorithm_counts),
        'all4481_actually_inferred_under_v9':delta_N==4481,
        'label_change_N_v8_compatible_to_v9':len(label_changes),
        'decision_change_N_v8_compatible_to_v9':len(decision_changes),
        'no_reference_read_by_classifier':True,'reference_comparison_NOT_executed_by_merge':True,
        'formal_validation_complete':False,'human_validation_complete':False,'paper_writing_gate_open':False,
        'parent_seal':bind(BASELINE/'seal.json'),'delta_seal':bind(delta/'seal.json'),
        'impact_closure_plan':bind(prep/'impact-closure-plan.json'),
        'adoption':bind(prep/'ROOT-pre-inference-adoption-sidecar.json'),
        'original_input_lineage':bind(prep/'original-input-lineage-sidecar.json'),'merger':bind(__file__)}
    save(out/'composite-status.json',status)
    save(out/'seal.json',{'status':status['status'],'files':[bind(p) for p in sorted(out.iterdir()) if p.is_file()],
        'self_excluded':True,'ancestor_seals':[status['parent_seal'],status['delta_seal']],
        'no_new_inference_executed_by_merge':True,'all4481_actually_inferred_under_v9':delta_N==4481,
        'formal_validation_complete':False})
    print(json.dumps({k:status[k] for k in ('actual_record_N','actual_dimension_N',
        'actual_v9_affected_inference_record_N','inherited_compatible_parent_record_N','lawful_null_N',
        'label_change_N_v8_compatible_to_v9','decision_change_N_v8_compatible_to_v9')},ensure_ascii=False))

if __name__=='__main__':main()
