"""Merge one sealed affected pass into an explicitly supplied complete compatible parent.

Keep original prediction/slot bytes and each inherited actual execution origin.
This operation performs no classification and no reference comparison.
"""
import argparse, ast, collections, datetime, hashlib, json
from pathlib import Path

if not __debug__:
    raise RuntimeError("Run without Python optimisation; binding assertions must remain active")

R = Path(__file__).resolve().parents[2]
DIMS = ('S', 'E', 'Ec', 'I', 'F')

def load(p): return json.loads(Path(p).read_bytes())
def bind(p):
    p=Path(p).resolve(); raw=p.read_bytes()
    return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def exact(b):
    actual=bind(b['path'])
    assert all(actual[k]==b[k] for k in ('path','bytes','sha256')),b['path']
def exact_bytes(b):
    exact(b);return Path(b['path']).read_bytes()

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

def object_member_raw(raw,key):
    """Return the literal UTF8 value of one unique JSON object member."""
    text=raw.decode('utf8');decoder=json.JSONDecoder();index=0
    def whitespace(i):
        while i<len(text) and text[i] in ' \t\r\n':i+=1
        return i
    index=whitespace(index);assert text[index]=='{';index+=1;values={}
    while True:
        index=whitespace(index)
        if text[index]=='}':index+=1;break
        name,index=decoder.raw_decode(text,index)
        assert isinstance(name,str) and name not in values
        index=whitespace(index);assert text[index]==':';index=whitespace(index+1)
        start=index;_,index=decoder.raw_decode(text,index);values[name]=text[start:index].encode('utf8')
        index=whitespace(index)
        if text[index]=='}':index+=1;break
        assert text[index]==',';index+=1
    assert whitespace(index)==len(text) and key in values
    return values[key]

def arguments(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('preparation','parent-composite','original-preparation','candidate-version','output'):
        parser.add_argument('--'+name,required=True)
    parser.add_argument('--mutable-dimensions',required=True,nargs='+',choices=DIMS,
                        help='Exact explicit unique subset bound to the approved contract')
    parser.add_argument('--validate-only',action='store_true',help='Read-only: no merge output is created')
    return parser.parse_args(argv)

def run(args):
    prep=Path(args.preparation).resolve();out=Path(args.output).resolve()
    BASELINE=Path(args.parent_composite).resolve()
    ORIGINAL=Path(args.original_preparation).resolve()
    candidate_version=args.candidate_version
    assert args.mutable_dimensions and len(args.mutable_dimensions)==len(set(args.mutable_dimensions))
    assert set(args.mutable_dimensions)<=set(DIMS)
    mutable=[d for d in DIMS if d in args.mutable_dimensions]
    immutable=[d for d in DIMS if d not in mutable]
    assert candidate_version and len(candidate_version)<129
    assert args.validate_only or not out.exists(),'Never overwrite an actual or composite result'
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
    assert plan['candidate_freeze']==adoption['candidate_freeze']
    assert plan['parent_compatible_seal']==bind(BASELINE/'seal.json')
    assert plan['parent_predictions']==bind(BASELINE/'predictions.jsonl')
    if not args.validate_only:
        assert plan['candidate_version']==candidate_version
        assert plan['original_complete_scope']==bind(ORIGINAL/'frozen-scope.json')
        assert plan['original_complete_packet_manifest']==bind(ORIGINAL/'packet-bindings.json')
    verify_seal(adoption['candidate_total_seal']['path'])
    required=load(plan['independent_required_candidate_members']['path'])
    exact(plan['independent_required_candidate_members'])
    assert required['candidate_delivery']==adoption['candidate_total_seal']
    assert required.get('required_member_readback_complete',required.get('independent_readback_complete')) is True
    assert adoption['required_candidate_members_verified']==required['required_candidate_members']
    contract=load(plan['contract']['path']);exact(plan['contract'])
    assert contract['manual_static_audit']['approved'] is True
    legacy_IF_contract=args.validate_only and 'allowed_mutable_dimensions' not in contract
    if legacy_IF_contract:
        assert candidate_version=='joint-v9-generic-relationship-sol','Legacy normalization is restricted to the completed v9 read-only case'
        assert mutable==['I','F'] and contract['manual_static_audit']['only_IF_decision_or_explicit_IF_request_mutations'] is True
    else:
        assert contract['allowed_mutable_dimensions']==mutable
        assert contract['manual_static_audit']['approval_actor']=='ROOT'
        assert contract['manual_static_audit']['only_allowed_dimension_decision_or_explicit_request_mutations'] is True
        assert plan['allowed_mutable_dimensions']==mutable and plan['immutable_dimensions']==immutable
        assert adoption['allowed_mutable_dimensions']==mutable
    for b in contract['manual_static_audit']['proof_artifact_bindings']:exact(b)
    verify_seal(BASELINE/'seal.json');verify_seal(delta/'seal.json')
    parent_status=load(BASELINE/'composite-status.json')
    assert parent_status['actual_record_N']==4481 and parent_status['actual_dimension_N']==22405
    assert parent_status['technical_failure_dimension_N']==0
    delta_seal=load(delta/'seal.json');freeze=load(delta/'freeze.json')
    assert delta_seal['status']=='sealed_complete_production_provisional_rule_delta_run'
    assert delta_seal['control_inputs']==[bind(prep/'frozen-scope.json')]
    assert freeze['control_inputs']==delta_seal['control_inputs']
    execution=load(delta/'execution.json');delta_N=plan['affected_record_N']
    assert type(delta_N) is int and 0<delta_N<=4481
    assert execution['status']=='completed' and execution['actual_record_N']==delta_N
    assert execution['actual_dimension_N']==delta_N*5 and execution['technical_failure_dimension_N']==0
    assert execution['no_reference_read'] and execution['actual_cohort_inference_runs']==1
    assert not execution['implementation_errors']
    assert freeze['reference_input'] is None
    assert execution['formal_validation_complete'] is execution['human_validation_complete'] is freeze['blind_validation'] is False
    assert freeze['fixed_algorithm_version']==candidate_version
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
    if not legacy_IF_contract:
        assert scope['allowed_mutable_dimensions']==mutable and scope['immutable_dimensions']==immutable
    assert freeze['final_candidate_algorithm']==scope['final_candidate_algorithm']==bind(prep/'algorithm-bindings.json')
    assert freeze['final_candidate_pre_execution_seal']==scope['final_candidate_pre_execution_seal']==plan['candidate_freeze']
    assert freeze['final_candidate_delivery_seal']==scope['final_candidate_delivery_seal']==plan['candidate_delivery']
    assert scope['impact_closure_plan']==adoption['impact_plan']
    assert scope['source_packet']==load(prep/'original-input-lineage-sidecar.json')['subset_source']
    assert scope['algorithm_bindings']==bind(prep/'algorithm-bindings.json')
    parent_scope=load(ORIGINAL/'frozen-scope.json')
    assert list(old)==parent_scope['approved_record_ids'] and scope['approved_record_ids']==list(new)
    for key in ('manual','protocol','prompt','source_reading_protocol_code','source_package_seal','source_manifest'):
        assert scope[key]==parent_scope[key];exact(scope[key])
    assert scope['bounded_delta_only'] and scope['parent_complete_record_N']==4481 and scope['expected_record_N']==delta_N and scope['expected_dimension_N']==delta_N*5
    assert scope['formal_validation_complete'] is scope['human_validation_complete'] is scope['blind_validation'] is False
    assert scope['max_actual_cohort_inference_runs']==1
    algorithm=load(prep/'algorithm-bindings.json')
    assert algorithm['algorithm_version']==candidate_version
    if not legacy_IF_contract:assert algorithm['allowed_mutable_dimensions']==mutable
    assert algorithm['final_candidate_delivery_seal']==plan['candidate_delivery'] and algorithm['final_candidate_pre_execution_seal']==plan['candidate_freeze']
    assert algorithm['impact_closure_plan']==bind(prep/'impact-closure-plan.json')
    assert {Path(b['path']).stem:{k:b[k] for k in ('path','bytes','sha256')} for b in algorithm['modules']}=={Path(b['path']).stem:b for b in contract['candidate_modules']}
    for b in algorithm['modules']:exact(b)
    selection=load(plan['selection']['path']);exact(plan['selection'])
    assert selection['contract_binding']==plan['contract'] and selection['baseline_prediction_binding']==bind(BASELINE/'predictions.jsonl')
    assert [r['id'] for r in selection['affected_records']]==list(new) and selection['selected_N']==delta_N and selection['reusable_N']==4481-delta_N
    assert not selection['full_fallback_reasons'] or delta_N==4481
    assert plan['unaffected_inherited_record_N']==4481-delta_N
    label_changes=[];decision_changes=[];log_changes=[]
    for rid,(x,new_raw) in new.items():
        y,old_raw=old[rid]
        new_decision_bytes=object_member_raw(new_raw,'decisions')
        old_decision_bytes=object_member_raw(old_raw,'decisions')
        assert not x['implementation_errors'] and not y['implementation_errors']
        assert set(x['labels'])==set(y['labels'])==set(x['decisions'])==set(DIMS)
        for d in DIMS:
            assert x['labels'][d]==x['decisions'][d]['value']
            assert x['labels'][d] is None or type(x['labels'][d]) is int and x['labels'][d] in (0,1)
            if d in immutable:
                assert x['decisions'][d]==y['decisions'][d],(rid,d)
                assert object_member_raw(new_decision_bytes,d)==object_member_raw(old_decision_bytes,d),(rid,d,'complete decision byte mismatch')
            if x['labels'][d]!=y['labels'][d]:
                label_changes.append({'id':rid,'dimension':d,'parent_value':y['labels'][d],
                    'delta_value':x['labels'][d],'parent_decision':y['decisions'][d],
                    'delta_decision':x['decisions'][d]})
            if x['decisions'][d]!=y['decisions'][d]:
                decision_changes.append({'id':rid,'dimension':d,'value_changed':x['labels'][d]!=y['labels'][d]})
        for key in ('source_requests','source_relation_traces','relation_traces'):
            if x.get(key)!=y.get(key):log_changes.append({'id':rid,'field':key})
    # Complete every source, slot and origin assertion before creating output.
    original=exact_bytes(parent_scope['source_packet']);source=exact_bytes(scope['source_packet'])
    original_lines=original.splitlines(keepends=True);subset_lines=source.splitlines(keepends=True)
    assert len(original_lines)==4481 and len(subset_lines)==delta_N
    selected_set=set(new);expected=[];mapping=[];pos=0;subset_pos=0
    for ordinal,(rid,raw) in enumerate(zip(parent_scope['approved_record_ids'],original_lines),1):
        assert json.loads(raw)['source_record']['id']==rid
        if rid in selected_set:
            expected.append(raw);mapping.append({'id':rid,'parent_ordinal_1based':ordinal,
                'parent_utf8_start':pos,'parent_utf8_end':pos+len(raw),
                'subset_ordinal_1based':len(expected),'subset_utf8_start':subset_pos,
                'subset_utf8_end':subset_pos+len(raw),'line_sha256':hashlib.sha256(raw).hexdigest()})
            subset_pos+=len(raw)
        pos+=len(raw)
    lineage_input=load(prep/'original-input-lineage-sidecar.json')
    assert source==b''.join(expected) and lineage_input['rows']==mapping
    assert lineage_input['original_source']==parent_scope['source_packet'] and lineage_input['subset_source']==scope['source_packet']
    assert list(new)==[rid for rid in old if rid in selected_set]
    assert scope['source_packet']==lineage_input['subset_source']
    prepared_seal=load(prep/'pre-execution-run-seal.json')
    for b in prepared_seal['implementation_files']:exact(b)
    assert prepared_seal['scope']==bind(prep/'frozen-scope.json')
    if not args.validate_only:
        proof=load(prep/'driver-transport-proof.json')
        assert proof['core_AST_equal_after_reverting_only_authorized_transport_changes']
        driver=bind(prep/'rule_driver.py')
        assert driver['bytes']==proof['candidate_driver_bytes'] and driver['sha256']==proof['candidate_driver_sha256']
        assert proof['original_driver']==bind(ORIGINAL/'rule_driver.py')
        assert proof['replacement_N']==len(proof['authorized_replacements'])==7
        restored=(prep/'rule_driver.py').read_text()
        for replacement in reversed(proof['authorized_replacements']):
            assert restored.count(replacement['new'])==1
            restored=restored.replace(replacement['new'],replacement['old'])
        original_driver=(ORIGINAL/'rule_driver.py').read_text()
        assert restored==original_driver
        assert ast.dump(ast.parse(restored),include_attributes=False)==ast.dump(ast.parse(original_driver),include_attributes=False)
    for name in ('interface_common.py','status_bridge.py'):
        assert (prep/name).read_bytes()==(ORIGINAL/name).read_bytes()
    prediction_bytes=[];slot_bytes=[];checked_counts={d:collections.Counter() for d in DIMS}
    checked_algorithms=collections.Counter()
    for ordinal,rid in enumerate(old,1):
        selected=rid in new;record,raw=(new if selected else old)[rid]
        prior=origins[rid][0]
        assert prior['corpus_ordinal_1based']==ordinal
        assert prior['actual_prediction_line_sha256']==hashlib.sha256(old[rid][1]).hexdigest()
        assert prior['prediction_line_bytes']==len(old[rid][1])
        assert prior['source_consumption_record_key']==rid
        assert record['candidate_decisions_diagnostic_only']==record['decisions']
        assert not record['implementation_errors'] and set(record['labels'])==set(record['decisions'])==set(DIMS)
        prediction_bytes.append(raw)
        checked_algorithms[candidate_version if selected else prior['actual_inference_algorithm']]+=1
        for d in DIMS:
            val=record['labels'][d];assert val is None or type(val) is int and val in (0,1)
            assert val==record['decisions'][d]['value']
            slot,slot_raw=(new_slots if selected else old_slots)[(rid,d)]
            assert slot['rule_value']==val and slot['retained_rule_decision']==record['decisions'][d]
            assert not slot['technical_failure'] and slot['rules_null']==(val is None)
            assert not slot['record_implementation_errors'] and not slot['global_implementation_errors']
            slot_bytes.append(slot_raw)
            checked_counts[d]['positive_N' if val==1 else 'negative_N' if val==0 else 'lawful_null_N']+=1
    if args.validate_only:
        return {'status':'read_only_completed_delta_merge_compatibility_check',
                'actual_record_N':4481,'actual_dimension_N':22405,'affected_record_N':delta_N,
                'inherited_record_N':4481-delta_N,'label_change_N':len(label_changes),
                'decision_change_N':len(decision_changes),'prediction_bytes':b''.join(prediction_bytes),
                'slot_bytes':b''.join(slot_bytes),'counts':{d:dict(c) for d,c in checked_counts.items()},
                'actual_algorithm_counts':dict(checked_algorithms),'all_checks_before_output_creation':True,
                'allowed_mutable_dimensions':mutable,'immutable_dimensions':immutable,
                'legacy_IF_contract_normalized_readonly':legacy_IF_contract,
                'immutable_complete_decision_bytes_equal':True,
                'classification_runs':0,'outputs_created':False}
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
                origin.update(actual_inference_algorithm=candidate_version,
                    actual_run_directory=str(delta),source_consumption_log=str(delta/'actual-source-consumption.jsonl'),
                    source_consumption_record_key=rid)
                prior_bases={k:origin.pop(k) for k in list(origin) if k.endswith('_compatibility_basis')}
                origin['superseded_parent_compatibility_basis_fields']=prior_bases
            origin.update(corpus_ordinal_1based=ordinal,id=rid,
                actual_prediction_line_sha256=hashlib.sha256(raw).hexdigest(),prediction_line_bytes=len(raw),
                unchanged_actual_record_bytes_retained=True,
                candidate_compatibility_basis='actual_affected_inference' if selected else 'unchanged_input_and_proved_new_gate_not_reached',
                inherited_parent_origin_binding=None if selected else {'path':str(BASELINE/'execution-origin-lineage.jsonl'),
                    'record_key':rid,'line_sha256':hashlib.sha256(origins[rid][1]).hexdigest()})
            lineage.append(origin);algorithm_counts[origin['actual_inference_algorithm']]+=1
    with (out/'execution-origin-lineage.jsonl').open('x',encoding='utf8') as f:
        for x in lineage:f.write(json.dumps(x,ensure_ascii=False,allow_nan=False)+'\n')
    save(out/'parent-compatible-to-candidate-actual-changes.json',{'label_changes':label_changes,
        'complete_decision_changes':decision_changes,'source_or_relation_log_changes':log_changes,
        'allowed_mutable_dimensions':mutable,'immutable_dimensions':immutable,
        'immutable_complete_decision_bytes_all_identical':True})
    status={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'status':'complete_compatible_rule_composite_with_explicit_execution_origins',
        'candidate_algorithm_version':candidate_version,'allowed_mutable_dimensions':mutable,
        'immutable_dimensions':immutable,'immutable_complete_decision_bytes_all_identical':True,
        'actual_record_N':4481,'actual_dimension_N':22405,'technical_failure_dimension_N':0,
        'lawful_null_N':sum(c['lawful_null_N'] for c in counts.values()),
        'counts':{d:{k:c[k] for k in ('positive_N','negative_N','lawful_null_N')} for d,c in counts.items()},
        'actual_affected_inference_record_N':delta_N,'inherited_compatible_parent_record_N':4481-delta_N,
        'actual_execution_algorithm_record_N':dict(algorithm_counts),
        'all4481_actually_inferred_under_candidate':delta_N==4481,
        'label_change_N_parent_to_candidate':len(label_changes),
        'decision_change_N_parent_to_candidate':len(decision_changes),
        'no_reference_read_by_classifier':True,'reference_comparison_NOT_executed_by_merge':True,
        'formal_validation_complete':False,'human_validation_complete':False,'paper_writing_gate_open':False,
        'parent_seal':bind(BASELINE/'seal.json'),'delta_seal':bind(delta/'seal.json'),
        'impact_closure_plan':bind(prep/'impact-closure-plan.json'),
        'adoption':bind(prep/'ROOT-pre-inference-adoption-sidecar.json'),
        'original_input_lineage':bind(prep/'original-input-lineage-sidecar.json'),'merger':bind(__file__)}
    save(out/'composite-status.json',status)
    save(out/'seal.json',{'status':status['status'],'files':[bind(p) for p in sorted(out.iterdir()) if p.is_file()],
        'self_excluded':True,'ancestor_seals':[status['parent_seal'],status['delta_seal']],
        'no_new_inference_executed_by_merge':True,'all4481_actually_inferred_under_candidate':delta_N==4481,
        'formal_validation_complete':False})
    return {k:status[k] for k in ('actual_record_N','actual_dimension_N',
        'actual_affected_inference_record_N','inherited_compatible_parent_record_N','lawful_null_N',
        'label_change_N_parent_to_candidate','decision_change_N_parent_to_candidate')}

if __name__=='__main__':
    result=run(arguments())
    result={k:v for k,v in result.items() if k not in ('prediction_bytes','slot_bytes')}
    print(json.dumps(result,ensure_ascii=False))
