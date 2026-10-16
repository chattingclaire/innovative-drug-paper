"""Prepare a source-identical v9 pass after an independently audited static selection.

Preparation does not import a classifier or read the human references. An actual
run is a separate operation. Both old positives and pending values are selected.
"""
import argparse, ast, copy, datetime, hashlib, json
from pathlib import Path

R = Path(__file__).resolve().parents[1]
PARENT = R/'06-coding/rule-full4481-final-v7-root'
BASELINE = R/'06-coding/rule-full4481-v8-delta-merged-root'
CANDIDATE = R/'06-coding/rule-five-dimension-joint-root/versions/joint-v9-generic-relationship-sol'
VERSION = 'v9-original-common-affected-driver-1'
MODULES = ('source_packet', 'source_receipts', 'evidence', 'relations', 'dimensions')

def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def load(p): return json.loads(Path(p).read_bytes())
def bind(p):
    p=Path(p).resolve();raw=p.read_bytes()
    return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def exact(spec):
    actual=bind(spec['path'])
    assert all(actual[k]==spec[k] for k in ('path','bytes','sha256')),spec['path']
    return Path(spec['path']).read_bytes()
def save(p,value):
    with Path(p).open('x',encoding='utf8') as f:
        json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def replace_once(text,old,new):
    assert text.count(old)==1,old
    return text.replace(old,new)
def verify_seal(path,visited=None,members=None):
    visited=set() if visited is None else visited
    members={} if members is None else members
    path=Path(path).resolve()
    if path in visited:return members
    visited.add(path);data=load(path)
    for key in ('files','members','output_files','implementation_files','material_bindings','control_inputs'):
        for item in data.get(key,[]):
            p=Path(item.get('path',item.get('relative_path','')))
            if not p.is_absolute():p=path.parent/p
            actual=bind(p)
            assert actual['bytes']==item['bytes'] and actual['sha256']==item['sha256'],p
            assert str(p.resolve()) not in members or members[str(p.resolve())]==actual
            members[str(p.resolve())]=actual
    for ancestor in data.get('ancestor_seals',[]):
        exact(ancestor);verify_seal(ancestor['path'],visited,members)
    return members

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selection',required=True)
    parser.add_argument('--candidate-delivery',required=True,help='Final total candidate delivery seal')
    parser.add_argument('--candidate-freeze',required=True,help='Final pre-production candidate freeze')
    parser.add_argument('--required-candidate-members',required=True,
        help='Explicit independently read-back final candidate members, including controls and proofs')
    parser.add_argument('--output',required=True)
    args=parser.parse_args();out=Path(args.output).resolve()
    assert not out.exists(),'Never overwrite prepared or actual results'
    selection_path=Path(args.selection).resolve();selected=load(selection_path)
    assert selected['status']=='static_selection_only_no_classifier_execution'
    assert selected['record_N']==4481
    contract=load(Path(selected['contract_binding']['path']))
    for key in ('contract_binding','manifest_binding','baseline_prediction_binding','selector_binding'):
        exact(selected[key])
    assert contract['manual_static_audit']['approved'] is True
    for item in contract['manual_static_audit']['proof_artifact_bindings']:exact(item)
    if selected['full_fallback_reasons']:
        assert selected['selected_N']==4481
    else:
        for key in ('record_local_only','new_relation_not_consumed_by_old_units',
                    'only_IF_decision_or_explicit_IF_request_mutations',
                    'same_packets_adapter_evidence_wrapper','mixed_baseline_equivalence_verified'):
            assert contract['manual_static_audit'][key] is True,key
    delivery=Path(args.candidate_delivery).resolve();freeze=Path(args.candidate_freeze).resolve()
    assert delivery.exists() and freeze.exists()
    assert Path(load(delivery)['candidate_directory']).resolve()==CANDIDATE.resolve()
    sealed_members=verify_seal(delivery)
    candidate_modules={Path(item['path']).stem:item for item in contract['candidate_modules']}
    assert set(candidate_modules)==set(MODULES)
    for name,item in candidate_modules.items():
        exact(item);assert Path(item['path']).resolve()==(CANDIDATE/(name+'.py')).resolve()
    required_path=Path(args.required_candidate_members).resolve()
    required=load(required_path)
    assert required['candidate_delivery']==bind(delivery)
    assert required['independent_readback_complete'] is True
    extra=required['required_candidate_members']
    assert extra and required['includes_static_proofs_and_all_finite_controls_and_readback'] is True
    for item in list(candidate_modules.values())+[bind(freeze),selected['selector_binding']]+extra:
        exact(item)
        assert sealed_members.get(str(Path(item['path']).resolve()))==bind(item['path']),item['path']
    verify_seal(BASELINE/'seal.json')
    status=load(BASELINE/'composite-status.json')
    assert status['actual_record_N']==4481 and status['actual_dimension_N']==22405
    assert status['technical_failure_dimension_N']==0
    assert selected['baseline_prediction_binding']==bind(BASELINE/'predictions.jsonl')
    parent_run=PARENT/'run4481-first';verify_seal(parent_run/'seal.json')
    scope=load(PARENT/'frozen-scope.json');packet_plan=load(PARENT/'packet-bindings.json')
    ids=scope['approved_record_ids'];assert len(ids)==len(set(ids))==4481
    affected=[item['id'] for item in selected['affected_records']]
    assert len(affected)==len(set(affected))==selected['selected_N']
    chosen=set(affected);assert affected==[rid for rid in ids if rid in chosen]
    assert 0<len(affected)<=4481 and selected['reusable_N']==4481-len(affected)
    assert packet_plan['ordered_source_ids']==ids and packet_plan['packet_N']==4481
    original=exact(scope['source_packet']);lines=original.splitlines(keepends=True)
    assert len(lines)==4481
    subset=[];lineage=[];cursor=0;subset_cursor=0
    for ordinal,(rid,line) in enumerate(zip(ids,lines),1):
        assert json.loads(line)['source_record']['id']==rid
        if rid in chosen:
            subset.append(line)
            lineage.append({'id':rid,'parent_ordinal_1based':ordinal,
                            'parent_utf8_start':cursor,'parent_utf8_end':cursor+len(line),
                            'subset_ordinal_1based':len(subset),'subset_utf8_start':subset_cursor,
                            'subset_utf8_end':subset_cursor+len(line),
                            'line_sha256':hashlib.sha256(line).hexdigest()})
            subset_cursor+=len(line)
        cursor+=len(line)
    out.mkdir(parents=True)
    source_path=out/'affected-original-common-lines.jsonl';source_path.write_bytes(b''.join(subset))
    plan={'at_utc':now(),'selection':bind(selection_path),'contract':selected['contract_binding'],
          'independent_required_candidate_members':bind(required_path),
          'candidate_delivery':bind(delivery),'candidate_freeze':bind(freeze),
          'parent_compatible_seal':bind(BASELINE/'seal.json'),'parent_predictions':bind(BASELINE/'predictions.jsonl'),
          'affected_record_ids':affected,'affected_record_N':len(affected),
          'unaffected_inherited_record_N':4481-len(affected),
          'all_entry_records_included_without_old_label_filter':True,
          'full_fallback_reasons':selected['full_fallback_reasons'],
          'source_manual_prompt_protocol_unchanged':True,'no_reference_read':True,
          'classification_executed_in_preparation':False}
    save(out/'impact-closure-plan.json',plan)
    save(out/'original-input-lineage-sidecar.json',{'original_source':scope['source_packet'],
         'subset_source':bind(source_path),'rows':lineage,'source_lines_byte_identical':True})
    packet_plan.update(packet_N=len(affected),ordered_source_ids=affected,
                       packets=[p for p in packet_plan['packets'] if p['source_id'] in chosen],
                       parent_complete_packet_manifest=bind(PARENT/'packet-bindings.json'),bounded_delta_only=True)
    assert [p['source_id'] for p in packet_plan['packets']]==affected
    save(out/'packet-bindings.json',packet_plan)
    for name in ('interface_common.py','status_bridge.py'):
        (out/name).write_bytes((PARENT/name).read_bytes())
    driver=(PARENT/'rule_driver.py').read_text()
    driver=replace_once(driver,"VERSION='v7-full4481-original-common-driver-1'","VERSION='"+VERSION+"'")
    driver=replace_once(driver,
        "    if scope.get('expected_record_N') != 4481 or scope.get('expected_dimension_N') != 22405:\n        raise ValueError('adapter requires the complete 4481-record, 22405-dimension scope')",
        "    if not scope.get('bounded_delta_only') or scope.get('parent_complete_record_N') != 4481:\n        raise ValueError('complete compatible parent and explicit affected scope required')\n    delta_N=scope.get('expected_record_N')\n    if type(delta_N) is not int or not (0 < delta_N <= 4481) or scope.get('expected_dimension_N') != delta_N*5:\n        raise ValueError('exact affected scope or explicit full fallback required')")
    driver=replace_once(driver,"packet_plan['packet_N']!=4481","packet_plan['packet_N']!=scope['expected_record_N']")
    driver=driver.replace('joint-v7 generic direct-content and bounded-relation repair; original common packets/manual/prompt/protocol unchanged',
                          'joint-v9 relation repair on all statically selected original records; inherited records retain actual prior origins')
    driver=driver.replace("'fixed_algorithm_version':'joint-v7-relation-content-sol'","'fixed_algorithm_version':'joint-v9-generic-relationship-sol'")
    driver=driver.replace("'sealed_complete_production_provisional_rule_run'","'sealed_complete_production_provisional_rule_delta_run'")
    driver=driver.replace('Final sealed v5 full4481 original common source-only execution; one first domain pass; persistent per-record outputs.',
                          'v9 original-common affected execution; persistent first results; full fallback allowed only as explicit complete scope.')
    ast.parse(driver);(out/'rule_driver.py').write_text(driver)
    algorithm={'algorithm_version':'joint-v9-generic-relationship-sol',
               'modules':[dict(bind(CANDIDATE/(n+'.py')),module=n) for n in MODULES],
               'final_candidate_delivery_seal':bind(delivery),'final_candidate_pre_execution_seal':bind(freeze),
               'source_and_manual_unchanged':True,'reference_not_classifier_input':True,
               'bounded_delta_execution':True,'impact_closure_plan':bind(out/'impact-closure-plan.json')}
    save(out/'algorithm-bindings.json',algorithm)
    run=out/'run-affected-first';auth='ROOT-v9-all-affected-original-once-20261012'
    release=load(PARENT/'rule-production-release.json')
    release.update(authorization_id=auth,output_directory=str(run),source_input=bind(source_path),
                   algorithm=bind(out/'algorithm-bindings.json'),algorithm_version=algorithm['algorithm_version'],
                   final_algorithm=bind(out/'algorithm-bindings.json'),bounded_delta_only=True,
                   parent_complete_seal=bind(BASELINE/'seal.json'),
                   description='One actual v9 pass over every selected original record; no old-value selection',
                   parent_explicit_authorization='User authorized partial correction first, full fallback if required.')
    release.pop('first_final_v5_full_domain_run',None);save(out/'rule-production-release.json',release)
    scope=copy.deepcopy(scope);old_release=scope['release']['path']
    save(out/'approved-affected-record-ids.json',{'approved_record_ids':affected,'parent_scope':bind(PARENT/'frozen-scope.json')})
    scope.update(authorization_id=auth,output_directory=str(run),source_packet=bind(source_path),
                 release=bind(out/'rule-production-release.json'),algorithm_bindings=bind(out/'algorithm-bindings.json'),
                 driver_version=VERSION,algorithm_origin='v9 frozen generic repair with complete v8 compatible parent',
                 final_candidate_algorithm=bind(out/'algorithm-bindings.json'),final_candidate_pre_execution_seal=bind(freeze),
                 final_candidate_delivery_seal=bind(delivery),approved_record_ids=affected,
                 expected_record_N=len(affected),expected_dimension_N=len(affected)*5,
                 packet_bindings=bind(out/'packet-bindings.json'),bounded_delta_only=True,parent_complete_record_N=4481,
                 parent_complete_seal=bind(BASELINE/'seal.json'),impact_closure_plan=bind(out/'impact-closure-plan.json'),
                 original_ordered_record_ids_binding=scope['ordered_record_ids_binding'],
                 ordered_record_ids_binding=bind(out/'approved-affected-record-ids.json'))
    scope['material_bindings']=[b for b in scope['material_bindings'] if b['path']!=old_release]+[scope['source_packet'],scope['release']]
    save(out/'frozen-scope.json',scope)
    save(out/'pre-execution-run-seal.json',{'at_utc':now(),'scope':bind(out/'frozen-scope.json'),
         'implementation_files':[bind(out/n) for n in ('rule_driver.py','interface_common.py','status_bridge.py','packet-bindings.json','algorithm-bindings.json','rule-production-release.json')],
         'impact_plan':bind(out/'impact-closure-plan.json'),'lineage':bind(out/'original-input-lineage-sidecar.json'),
         'affected_record_N':len(affected),'unaffected_record_N':4481-len(affected),
         'max_actual_cohort_passes':1,'actual_inference_runs':0,'formal_validation_complete':False})
    print(json.dumps({'scope':str(out/'frozen-scope.json'),'affected_record_N':len(affected),
                      'reused_record_N':4481-len(affected),'actual_inference_runs':0},ensure_ascii=False))

if __name__=='__main__':main()
