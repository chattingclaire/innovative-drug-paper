"""Prepare one source-identical affected pass from explicitly bound parameters.

Preparation does not import a classifier or read the human references. An actual
run is a separate operation. Both old positives and pending values are selected.
"""
import argparse, ast, copy, datetime, hashlib, json, re
from pathlib import Path

if not __debug__:
    raise RuntimeError("Run without Python optimisation; binding assertions must remain active")

R = Path(__file__).resolve().parents[2]
MODULES = ('source_packet', 'source_receipts', 'evidence', 'relations', 'dimensions')
MODULES_TO_DIMS=('S','E','Ec','I','F')

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

def build_driver(path, runtime_version, candidate_version):
    original=Path(path).read_text();tree=ast.parse(original)
    def metadata_pair(variable,key,new_value):
        dictionaries=[n.value for n in ast.walk(tree) if isinstance(n,ast.Assign)
                      and any(isinstance(t,ast.Name) and t.id==variable for t in n.targets)
                      and isinstance(n.value,ast.Dict)]
        assert len(dictionaries)==1,variable
        entries=[(k,v) for k,v in zip(dictionaries[0].keys,dictionaries[0].values)
                 if isinstance(k,ast.Constant) and k.value==key]
        assert len(entries)==1
        k,v=entries[0];assert isinstance(v,ast.Constant) and isinstance(v.value,str)
        pattern=re.escape(ast.get_source_segment(original,k))+r'\s*:\s*'+re.escape(ast.get_source_segment(original,v))
        matches=list(re.finditer(pattern,original));assert len(matches)==1
        old=matches[0].group();new=repr(key)+':'+repr(new_value)
        return old,new
    version=[n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='VERSION' for t in n.targets)]
    assert len(version)==1 and isinstance(version[0].value,ast.Constant)
    changes=[(ast.get_source_segment(original,tree.body[0]),repr('Generic original-common affected execution; true inherited origins retained.')),
             (ast.get_source_segment(original,version[0]),'VERSION='+repr(runtime_version)),
             ("    if scope.get('expected_record_N') != 4481 or scope.get('expected_dimension_N') != 22405:\n        raise ValueError('adapter requires the complete 4481-record, 22405-dimension scope')",
              "    if not scope.get('bounded_delta_only') or scope.get('parent_complete_record_N') != 4481:\n        raise ValueError('complete compatible parent and explicit affected scope required')\n    delta_N=scope.get('expected_record_N')\n    if type(delta_N) is not int or not (0 < delta_N <= 4481) or scope.get('expected_dimension_N') != delta_N*5:\n        raise ValueError('exact affected scope or explicit full fallback required')"),
             ("packet_plan['packet_N']!=4481","packet_plan['packet_N']!=scope['expected_record_N']"),
             metadata_pair('freeze','semantic_change',candidate_version+': original common affected execution; inherited records retain actual prior origins'),
             metadata_pair('freeze','fixed_algorithm_version',candidate_version),
             ("'sealed_complete_production_provisional_rule_run'","'sealed_complete_production_provisional_rule_delta_run'")]
    driver=original
    for old,new in changes:driver=replace_once(driver,old,new)
    restored=driver
    for old,new in reversed(changes):restored=replace_once(restored,new,old)
    assert restored==original
    assert ast.dump(ast.parse(restored),include_attributes=False)==ast.dump(tree,include_attributes=False)
    ast.parse(driver)
    return driver,{'original_driver':bind(path),'replacement_N':len(changes),
                   'authorized_replacements':[{'old':old,'new':new} for old,new in changes],
                   'core_AST_equal_after_reverting_only_authorized_transport_changes':True,
                   'original_AST_sha256':hashlib.sha256(ast.dump(tree,include_attributes=False).encode()).hexdigest(),
                   'candidate_driver_bytes':len(driver.encode()),'candidate_driver_sha256':hashlib.sha256(driver.encode()).hexdigest(),
                   'classification_executed':False}

def arguments(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('selection','candidate-directory','candidate-version','driver-version',
                 'candidate-delivery','candidate-freeze','required-candidate-members',
                 'parent-composite','original-preparation','authorization-id','output'):
        parser.add_argument('--'+name,required=True)
    parser.add_argument('--mutable-dimensions',required=True,nargs='+',choices=MODULES_TO_DIMS,
                        help='Explicit unique subset; no default dimensions are authorized')
    parser.add_argument('--validate-only',action='store_true',help='Read-only; create no files or adoption')
    return parser.parse_args(argv)

def run(args):
    PARENT=Path(args.original_preparation).resolve()
    BASELINE=Path(args.parent_composite).resolve()
    CANDIDATE=Path(args.candidate_directory).resolve()
    VERSION=args.driver_version
    candidate_version=args.candidate_version
    assert args.mutable_dimensions and len(args.mutable_dimensions)==len(set(args.mutable_dimensions))
    assert set(args.mutable_dimensions)<=set(MODULES_TO_DIMS)
    mutable=[d for d in MODULES_TO_DIMS if d in args.mutable_dimensions]
    immutable=[d for d in MODULES_TO_DIMS if d not in mutable]
    for value in (VERSION,candidate_version):
        assert re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}',value),'Version must be a transport identifier'
    assert CANDIDATE.name==candidate_version,'Candidate version must match its exact directory identity'
    assert args.authorization_id and len(args.authorization_id)<256
    out=Path(args.output).resolve()
    assert args.validate_only or not out.exists(),'Never overwrite prepared or actual results'
    selection_path=Path(args.selection).resolve();selected=load(selection_path)
    assert selected['status']=='static_selection_only_no_classifier_execution'
    assert selected['record_N']==4481
    contract=load(Path(selected['contract_binding']['path']))
    for key in ('contract_binding','manifest_binding','baseline_prediction_binding','selector_binding'):
        exact(selected[key])
    assert contract['manual_static_audit']['approved'] is True
    legacy_IF_contract=args.validate_only and 'allowed_mutable_dimensions' not in contract
    if legacy_IF_contract:
        assert candidate_version=='joint-v9-generic-relationship-sol','Legacy normalization is restricted to the completed v9 read-only case'
        assert mutable==['I','F'] and contract['manual_static_audit']['only_IF_decision_or_explicit_IF_request_mutations'] is True
    else:
        assert contract['allowed_mutable_dimensions']==mutable
        assert contract['manual_static_audit']['approval_actor']=='ROOT'
        assert contract['manual_static_audit']['only_allowed_dimension_decision_or_explicit_request_mutations'] is True
    for item in contract['manual_static_audit']['proof_artifact_bindings']:exact(item)
    if selected['full_fallback_reasons']:
        assert selected['selected_N']==4481
    else:
        for key in ('record_local_only','new_relation_not_consumed_by_old_units',
                    'same_packets_adapter_evidence_wrapper','mixed_baseline_equivalence_verified'):
            assert contract['manual_static_audit'][key] is True,key
    delivery=Path(args.candidate_delivery).resolve();freeze=Path(args.candidate_freeze).resolve()
    assert delivery.exists() and freeze.exists()
    assert Path(load(delivery)['candidate_directory']).resolve()==CANDIDATE.resolve()
    sealed_members=verify_seal(delivery)
    final_delivery=load(delivery);final_freeze=load(freeze)
    assert Path(final_freeze['candidate_directory']).resolve()==CANDIDATE
    assert selected['selector_binding']==contract['selector_binding']==final_freeze['selector_binding']
    assert final_freeze['candidate_modules']==contract['candidate_modules']
    assert contract['baseline_prediction_binding']==selected['baseline_prediction_binding']
    candidate_modules={Path(item['path']).stem:item for item in contract['candidate_modules']}
    assert set(candidate_modules)==set(MODULES)
    for name,item in candidate_modules.items():
        exact(item);assert Path(item['path']).resolve()==(CANDIDATE/(name+'.py')).resolve()
    required_path=Path(args.required_candidate_members).resolve()
    required=load(required_path)
    assert required['candidate_delivery']==bind(delivery)
    assert required.get('required_member_readback_complete',required.get('independent_readback_complete')) is True
    extra=required['required_candidate_members']
    assert extra and required['includes_static_proofs_and_all_finite_controls_and_readback'] is True
    for item in list(candidate_modules.values())+[bind(freeze),selected['selector_binding']]+extra:
        exact(item)
        assert sealed_members.get(str(Path(item['path']).resolve()))==bind(item['path']),item['path']
    assert {b['path'] for b in final_delivery['required_member_bindings']} <= {b['path'] for b in extra}
    for item in final_delivery.get('input_bindings',[]):exact(item)
    verify_seal(BASELINE/'seal.json')
    status=load(BASELINE/'composite-status.json')
    assert status['actual_record_N']==4481 and status['actual_dimension_N']==22405
    assert status['technical_failure_dimension_N']==0
    assert selected['baseline_prediction_binding']==bind(BASELINE/'predictions.jsonl')
    scope=load(PARENT/'frozen-scope.json');packet_plan=load(PARENT/'packet-bindings.json')
    parent_run=Path(scope['output_directory']).resolve();verify_seal(parent_run/'seal.json')
    ids=scope['approved_record_ids'];assert len(ids)==len(set(ids))==4481
    assert scope['expected_record_N']==4481 and scope['expected_dimension_N']==22405
    assert scope['formal_validation_complete'] is scope['human_validation_complete'] is scope['blind_validation'] is False
    assert scope['max_actual_cohort_inference_runs']==1
    exact(selected['manifest_binding']);manifest=load(selected['manifest_binding']['path'])
    assert manifest['approved_record_ids']==[r['id'] for r in manifest['records']]==ids
    assert [r['packet_binding'] for r in manifest['records']]==[{k:p[k] for k in ('path','bytes','sha256')} for p in packet_plan['packets']]
    parent_predictions=[json.loads(line) for line in (BASELINE/'predictions.jsonl').read_bytes().splitlines()]
    assert [p['id'] for p in parent_predictions]==ids
    assert all(not p['implementation_errors'] and set(p['decisions'])==set(MODULES_TO_DIMS) and p['decisions']==p['candidate_decisions_diagnostic_only'] for p in parent_predictions)
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
    chosen_packets=[p for p in packet_plan['packets'] if p['source_id'] in chosen]
    assert [p['source_id'] for p in chosen_packets]==affected
    exact(scope['release']);release=load(scope['release']['path'])
    assert release['max_actual_cohort_inference_runs']==1 and release['formal_validation_complete'] is release['human_validation_complete'] is False
    driver,driver_proof=build_driver(PARENT/'rule_driver.py',VERSION,candidate_version)
    if args.validate_only:
        return {'status':'read_only_preparation_compatibility_check',
                'affected_record_N':len(affected),'reused_record_N':4481-len(affected),
                'source_subset_bytes':b''.join(subset),'lineage_rows':lineage,
                'driver':driver,'driver_proof':driver_proof,'algorithm_modules':list(candidate_modules.values()),
                'source_original_binding':scope['source_packet'],'selection_binding':bind(selection_path),
                'contract_binding':selected['contract_binding'],'allowed_mutable_dimensions':mutable,
                'immutable_dimensions':immutable,'legacy_IF_contract_normalized_readonly':legacy_IF_contract,
                'classifier_runs':0,'outputs_created':False}
    out.mkdir(parents=True)
    source_path=out/'affected-original-common-lines.jsonl';source_path.write_bytes(b''.join(subset))
    plan={'at_utc':now(),'selection':bind(selection_path),'contract':selected['contract_binding'],
          'independent_required_candidate_members':bind(required_path),
          'candidate_delivery':bind(delivery),'candidate_freeze':bind(freeze),
          'parent_compatible_seal':bind(BASELINE/'seal.json'),'parent_predictions':bind(BASELINE/'predictions.jsonl'),
          'candidate_version':candidate_version,'allowed_mutable_dimensions':mutable,
          'immutable_dimensions':immutable,'original_complete_scope':bind(PARENT/'frozen-scope.json'),
          'original_complete_packet_manifest':bind(PARENT/'packet-bindings.json'),
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
                       packets=chosen_packets,
                       parent_complete_packet_manifest=bind(PARENT/'packet-bindings.json'),bounded_delta_only=True)
    assert [p['source_id'] for p in packet_plan['packets']]==affected
    save(out/'packet-bindings.json',packet_plan)
    for name in ('interface_common.py','status_bridge.py'):
        (out/name).write_bytes((PARENT/name).read_bytes())
    (out/'rule_driver.py').write_text(driver)
    save(out/'driver-transport-proof.json',driver_proof)
    algorithm={'algorithm_version':candidate_version,'allowed_mutable_dimensions':mutable,
               'modules':[dict(bind(CANDIDATE/(n+'.py')),module=n) for n in MODULES],
               'final_candidate_delivery_seal':bind(delivery),'final_candidate_pre_execution_seal':bind(freeze),
               'source_and_manual_unchanged':True,'reference_not_classifier_input':True,
               'bounded_delta_execution':True,'impact_closure_plan':bind(out/'impact-closure-plan.json')}
    save(out/'algorithm-bindings.json',algorithm)
    run=out/'run-affected-first';auth=args.authorization_id
    release.update(authorization_id=auth,allowed_mutable_dimensions=mutable,output_directory=str(run),source_input=bind(source_path),
                   algorithm=bind(out/'algorithm-bindings.json'),algorithm_version=algorithm['algorithm_version'],
                   final_algorithm=bind(out/'algorithm-bindings.json'),bounded_delta_only=True,
                   parent_complete_seal=bind(BASELINE/'seal.json'),
                   description='One actual '+candidate_version+' pass over every selected original record; no old-value selection',
                   parent_explicit_authorization='Caller authorization_id is required; ROOT adoption is recorded separately before actual inference.')
    release.pop('first_final_v5_full_domain_run',None);save(out/'rule-production-release.json',release)
    scope=copy.deepcopy(scope);old_release=scope['release']['path']
    save(out/'approved-affected-record-ids.json',{'approved_record_ids':affected,'parent_scope':bind(PARENT/'frozen-scope.json')})
    scope.update(authorization_id=auth,allowed_mutable_dimensions=mutable,immutable_dimensions=immutable,
                 output_directory=str(run),source_packet=bind(source_path),
                 release=bind(out/'rule-production-release.json'),algorithm_bindings=bind(out/'algorithm-bindings.json'),
                 driver_version=VERSION,algorithm_origin=candidate_version+' frozen repair with exact complete compatible parent',
                 final_candidate_algorithm=bind(out/'algorithm-bindings.json'),final_candidate_pre_execution_seal=bind(freeze),
                 final_candidate_delivery_seal=bind(delivery),approved_record_ids=affected,
                 expected_record_N=len(affected),expected_dimension_N=len(affected)*5,
                 packet_bindings=bind(out/'packet-bindings.json'),bounded_delta_only=True,parent_complete_record_N=4481,
                 parent_complete_seal=bind(BASELINE/'seal.json'),impact_closure_plan=bind(out/'impact-closure-plan.json'),
                 original_ordered_record_ids_binding=scope['ordered_record_ids_binding'],
                 ordered_record_ids_binding=bind(out/'approved-affected-record-ids.json'))
    scope['material_bindings']=[b for b in scope['material_bindings'] if b['path']!=old_release]+[scope['source_packet'],scope['release']]
    save(out/'frozen-scope.json',scope)
    save(out/'pre-execution-run-seal.json',{'at_utc':now(),'candidate_version':candidate_version,'allowed_mutable_dimensions':mutable,'scope':bind(out/'frozen-scope.json'),
         'implementation_files':[bind(out/n) for n in ('rule_driver.py','interface_common.py','status_bridge.py','packet-bindings.json','algorithm-bindings.json','rule-production-release.json','driver-transport-proof.json')],
         'impact_plan':bind(out/'impact-closure-plan.json'),'lineage':bind(out/'original-input-lineage-sidecar.json'),
         'affected_record_N':len(affected),'unaffected_record_N':4481-len(affected),
         'max_actual_cohort_passes':1,'actual_inference_runs':0,'formal_validation_complete':False})
    return {'scope':str(out/'frozen-scope.json'),'affected_record_N':len(affected),
            'reused_record_N':4481-len(affected),'allowed_mutable_dimensions':mutable,'actual_inference_runs':0,'ROOT_adoption_not_created':True}

if __name__=='__main__':
    result=run(arguments())
    result={k:v for k,v in result.items() if k not in ('source_subset_bytes','lineage_rows','driver')}
    print(json.dumps(result,ensure_ascii=False))
