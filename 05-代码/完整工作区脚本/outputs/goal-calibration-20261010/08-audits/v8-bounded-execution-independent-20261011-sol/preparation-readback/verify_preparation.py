"""Read-only independent closure/bytes/AST/preparation audit, no classifier call."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import ast, hashlib, json
O=Path(__file__).resolve().parent;G=O.parents[2]
C=G/'06-coding/rule-five-dimension-joint-root/versions/joint-v8-target-product-gap-sol'
P=G/'06-coding/rule-full4481-final-v7-root';RUN=P/'run4481-first';V=G/'06-coding/rule-v8-bounded-delta-root'
D=('S','E','Ec','I','F');MARK='单品种未上市与按需优先机会';I={}
def bind(p):
 p=Path(p).resolve();b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def reg(p,expected=None):
 b=bind(p)
 if expected:assert all(b[k]==expected[k] for k in ('path','bytes','sha256')),b
 I[b['path']]=b;return Path(b['path'])
def load(p):return json.loads(reg(p).read_bytes())
def save(n,x):
 with (O/n).open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def paths(x,p='$'):
 if isinstance(x,str):return [p] if MARK in x else []
 if isinstance(x,dict):return [q for k,v in x.items() for q in paths(v,p+'/'+str(k))]
 if isinstance(x,list):return [q for k,v in enumerate(x) for q in paths(v,p+'/'+str(k))]
 return []
def references(x):
 if isinstance(x,dict):
  if x.get('reference')==MARK:yield x
  for v in x.values():yield from references(v)
 elif isinstance(x,list):
  for v in x:yield from references(v)
def replace(t,a,b):assert t.count(a)==1;return t.replace(a,b)
def main():
 assert not (O/'report.json').exists()
 execution_present_at_audit_start=(V/'run-affected-first').exists()
 reg(__file__);reg(G/'08-audits/prepare-rule-v8-delta-execution-root.py')
 sealed=load(C/'output-seal.json');members={str(Path(b['path']).resolve()):b for b in sealed['files']}
 assert len(members)==len(sealed['files'])==126
 for b in sealed['files']:reg(b['path'],b)
 necessary=[C/(n+'.py') for n in ('source_packet','source_receipts','evidence','relations','dimensions','select_sealed_v7_impact')]+[C/'static-impact-proof.json',C/'candidate-freeze.json']
 for p in necessary:assert str(p.resolve()) in members;reg(p,members[str(p.resolve())])
 pre=load(C/'candidate-freeze.json')
 for b in pre['candidate_modules']:reg(b['path'],b)
 ps=load(RUN/'seal.json');ex=load(RUN/'execution.json')
 assert ps['status']=='sealed_complete_production_provisional_rule_run' and ps['record_N']==4481 and ps['dimension_N']==22405
 assert ex['status']=='completed' and ex['actual_record_N']==4481 and ex['actual_dimension_N']==22405 and ex['technical_failure_dimension_N']==0 and not ex['implementation_errors']
 assert ps['source_packet_unchanged'] and ps['no_reference_read']
 for group in ('implementation_files','material_bindings','control_inputs','output_files'):
  for b in ps[group]:reg(b['path'],b)
 oldmods={b['module']:reg(b['path'],b) for b in load(P/'algorithm-bindings.json')['modules']}
 assert all(oldmods[n].read_bytes()==(C/(n+'.py')).read_bytes() for n in ('source_packet','source_receipts','evidence','relations'))
 old=oldmods['dimensions'].read_text();new=(C/'dimensions.py').read_text()
 branch="    if re.search('境外已上市[^。；;]{0,8}境内未上市', text) and opportunity and (not any((re.search(pattern, text) for pattern in GAPS.values()))):\n"
 following="    if unit.kind == 'named_mechanism' and unit.details.get('relation_subtype') == 'bounded_IF_actual_support'"
 assert old.count(branch)==new.count(branch)==1
 a=old.index(branch)+len(branch);b=old.index(following,a);na=new.index(branch)+len(branch);nb=new.index(following,na)
 assert old[:a]==new[:na] and old[b:]==new[nb:]
 assert ast.dump(ast.parse(new[:na]+old[a:b]+new[nb:]),include_attributes=False)==ast.dump(ast.parse(old),include_attributes=False)
 # The modified body mutates only F accumulator entries; no source/unit mutation.
 body=ast.parse('if True:\n'+new[na:nb]);mutating=[]
 for node in ast.walk(body):
  if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name) and node.func.value.id=='acc':
   assert node.func.attr in ('add','boundary') and isinstance(node.args[0],ast.Constant) and node.args[0].value=='F';mutating.append(node.func.attr)
 assert sorted(mutating)==['add','boundary']
 oldscope=load(P/'frozen-scope.json');rows=[json.loads(x) for x in reg(RUN/'predictions.jsonl').read_bytes().splitlines()]
 assert [r['id'] for r in rows]==oldscope['approved_record_ids'] and len(rows)==4481
 decisionkeys={'value','basis_path','current_anchor','current_proposition','context_evidence','reason','needed_material','rule_conflict','details'}
 affected=[]
 for r in rows:
  assert not r['implementation_errors'] and r['decisions']==r['candidate_decisions_diagnostic_only'] and set(r['decisions'])==set(D) and set(r['labels'])==set(D)
  assert all(set(r['decisions'][d])==decisionkeys and r['labels'][d]==r['decisions'][d]['value'] and (r['labels'][d] is None or type(r['labels'][d]) is int and r['labels'][d] in (0,1)) for d in D)
  f=r['decisions']['F'];hits=list(references(f));pp=paths(r);assert bool(hits)==bool(pp)
  if hits:affected.append({'id':r['id'],'old_F':f['value'],'boundary_reference_N':len(hits),'marker_paths':pp})
 ids=[x['id'] for x in affected];assert len(ids)==7 and Counter(str(x['old_F']) for x in affected)==Counter({'1':2,'None':5})
 selection=load(G/'08-audits/v8-impact-closure-selection-root/actual-selection.json')
 assert selection['selected_N']==7 and selection['reusable_N']==4474 and [x['id'] for x in selection['affected_records']]==ids
 for x,y in zip(affected,selection['affected_records']):assert x['old_F']==y['final_F_value'] and x['marker_paths']==y['marker_paths']
 for k in ('old_prediction_binding','old_seal_binding','old_execution_binding','old_freeze_binding','candidate_freeze_binding','selector_binding'):reg(selection[k]['path'],selection[k])
 closure=load(V/'impact-closure-plan.json');scope=load(V/'frozen-scope.json');alg=load(V/'algorithm-bindings.json');prepared=load(V/'pre-execution-run-seal.json');side=load(V/'ROOT-pre-inference-adoption-sidecar.json');lineage=load(V/'original-input-lineage-sidecar.json')
 assert closure['affected_record_ids']==scope['approved_record_ids']==ids and closure['affected_record_N']==7 and closure['unaffected_inherited_record_N']==4474
 assert scope['expected_record_N']==7 and scope['expected_dimension_N']==35 and scope['bounded_delta_only'] and scope['parent_complete_record_N']==4481
 assert scope['formal_validation_complete'] is False and scope['human_validation_complete'] is False and scope['blind_validation'] is False
 for k in ('parent_seal','parent_execution','parent_predictions','candidate_delivery','static_impact_proof'):reg(closure[k]['path'],closure[k])
 for k in ('scope','closure_plan'):reg(prepared[k]['path'],prepared[k])
 for b in prepared['implementation_files']:reg(b['path'],b)
 for k in ('candidate_total_seal','selection','impact_plan','frozen_scope','pre_execution_seal','original_input_lineage'):reg(side[k]['path'],side[k])
 assert side['new_inference_calls']==0 and side['formal_validation_complete'] is False and {b['path'] for b in side['required_candidate_members_verified']}=={str(p.resolve()) for p in necessary}
 for b in side['required_candidate_members_verified']:assert members[b['path']]==b;reg(b['path'],b)
 for n in ('manual','prompt','protocol','source_reading_protocol_code','source_package_seal','source_manifest'):assert oldscope[n]==scope[n]
 for b in scope['material_bindings']:reg(b['path'],b);assert Path(b['path']).suffix!='.xlsx' and Path(b['path']).name!='reference.jsonl' and '/04-calibration/' not in b['path'] and '/09-delivery/' not in b['path'] and '/07-statistics/' not in b['path']
 for b in alg['modules']:reg(b['path'],b);assert members[b['path']]=={k:b[k] for k in ('path','bytes','sha256')}
 assert [b['module'] for b in alg['modules']]==['source_packet','source_receipts','evidence','relations','dimensions']
 parentraw=reg(oldscope['source_packet']['path'],oldscope['source_packet']).read_bytes();subsetraw=reg(scope['source_packet']['path'],scope['source_packet']).read_bytes();mapping=[];chosen=[];cursor=0;subsetcursor=0
 for index,line in enumerate(parentraw.splitlines(keepends=True),1):
  rid=json.loads(line)['source_record']['id'];assert rid==oldscope['approved_record_ids'][index-1]
  if rid in ids:
   chosen.append(line);mapping.append({'id':rid,'parent_line_1based':index,'parent_start_utf8_byte':cursor,'parent_end_utf8_byte_exclusive':cursor+len(line),'subset_line_1based':len(chosen),'subset_start_utf8_byte':subsetcursor,'subset_end_utf8_byte_exclusive':subsetcursor+len(line),'exact_input_line_sha256':hashlib.sha256(line).hexdigest(),'literal_original_line_reused':True});subsetcursor+=len(line)
  cursor+=len(line)
 assert subsetraw==b''.join(chosen) and [x['id'] for x in mapping]==ids and lineage['records']==mapping
 assert lineage['parent_source']==oldscope['source_packet'] and lineage['subset_source']==scope['source_packet'] and lineage['subset_offsets_not_claimed_as_parent_offsets']
 pplan=load(P/'packet-bindings.json');splan=load(V/'packet-bindings.json');packets=[p for p in pplan['packets'] if p['source_id'] in ids]
 assert splan['packets']==packets and splan['packet_N']==7 and splan['ordered_source_ids']==ids
 for p,line in zip(packets,chosen):
  packet=json.loads(reg(p['path'],p).read_bytes());bundle=json.loads(line)
  assert packet['packet_version']=='native-full-source-3' and packet['source_bundle']==bundle and packet['source_id']==bundle['source_record']['id'] and packet['output_id']==p['output_id']
  assert hashlib.sha256(json.dumps(bundle,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()==packet['source_bundle_sha256']==p['source_bundle_sha256']
 for n in ('interface_common.py','status_bridge.py'):assert reg(P/n).read_bytes()==reg(V/n).read_bytes()
 driver=reg(P/'rule_driver.py').read_text()
 driver=replace(driver,"VERSION='v7-full4481-original-common-driver-1'","VERSION='v8-bounded-original-common-delta-driver-1'")
 driver=replace(driver,"    if scope.get('expected_record_N') != 4481 or scope.get('expected_dimension_N') != 22405:\n        raise ValueError('adapter requires the complete 4481-record, 22405-dimension scope')","    if not scope.get('bounded_delta_only') or scope.get('parent_complete_record_N') != 4481:\n        raise ValueError('explicit bounded delta and complete parent scope required')\n    delta_N = scope.get('expected_record_N')\n    if type(delta_N) is not int or not (0 < delta_N < 4481) or scope.get('expected_dimension_N') != delta_N * 5:\n        raise ValueError('adapter requires the exact pre-frozen affected subset')")
 driver=replace(driver,"packet_plan['packet_N']!=4481","packet_plan['packet_N']!=scope['expected_record_N']")
 changes=[('joint-v7 generic direct-content and bounded-relation repair; original common packets/manual/prompt/protocol unchanged','joint-v8 bounded needed-product access relation repair; original common packets/manual/prompt/protocol unchanged; partial execution with complete parent v7 inheritance'),("'fixed_algorithm_version':'joint-v7-relation-content-sol'","'fixed_algorithm_version':'joint-v8-target-product-gap-sol'"),("'sealed_complete_production_provisional_rule_run'","'sealed_complete_production_provisional_rule_delta_run'"),('Final sealed v5 full4481 original common source-only execution; one first domain pass; persistent per-record outputs.','Sealed v8 bounded delta on original common sources; one pass over all affected records; no full v8 run claim.')]
 for a,b in changes:driver=replace(driver,a,b)
 assert driver==reg(V/'rule_driver.py').read_text();ast.parse(driver)
 # Do not claim byte equality of selected records' future F evidence before inference.
 result={'at_utc':datetime.now(timezone.utc).isoformat(),'status':'actual_frozen_preparation_and_sidecars_independently_read_back_no_blocking_issue','pre_inference_independent_review':False,'execution_directory_exists_at_audit_start':execution_present_at_audit_start,'candidate_delivery_members_verified_N':126,'required_candidate_members_verified_N':8,'parent_record_N':4481,'parent_slot_N':22405,'parent_technical_failure_N':0,'four_modules_byte_unchanged':True,'outside_changed_if_body_byte_unchanged':True,'restored_old_body_AST_identical':True,'changed_body_only_F_accumulator_mutations':True,'old_final_and_candidate_decisions_all_identical':True,'affected_records':affected,'affected_record_N':7,'unaffected_reusable_record_N':4474,'positive_F_records_included_N':2,'all_reference_marker_hits_included':True,'lineage_records':mapping,'original_line_and_packet_bytes_preserved':True,'driver_changes_only_scope_count_and_metadata':True,'old_interface_and_status_bridge_byte_identical':True,'classification_imports_or_calls_N':0,'preparation_sidecar_recorded_inference_calls_N':0,'new_F_values_not_yet_claimed':True,'full4481_ran_v8':False,'formal_validation_complete':False,'remaining_required_work':'Actual one-pass delta execution+seal audit; compare every other dimension/request/evidence path and per-slot merged lineage before adopting results.'}
 save('report.json',result)
 (O/'report.md').write_text('实际v8准备与sidecar已独立核验，未见阻断执行问题。完整v7的4481条旧结果里仅7条命中唯一改变的旧分支，其中2条旧F=1、5条旧F=null，全部纳入。四模块逐字节相同，恢复旧if主体后AST全同；变更主体只写F累加器。原common行字节、原packet、原行号/UTF8span到子集对应全部相符；新驱动仅改子集计数守卫及版本/说明标识。\n\n候选126成员及8个必要成员、完整父22405槽/0技术失败、冻结scope与两个sidecar均实际绑定通过。独立审计开始时局部执行目录已经存在；本报告是冻结准备资料的事后字节核验，不声称早于推理完成审查。本审计不执行分类，也不给新F值或合并结果。后续只执行7条，完整合并必须说明4474条继承v7、7条来自实际delta，不能称4481全都跑过v8；正式验证仍false。\n',encoding='utf8')
 for b in I.values():assert bind(b['path'])==b
 save('input-bindings.json',{'files':list(I.values()),'all_after_readback_unchanged':True})
 save('seal.json',{'files':[bind(p) for p in sorted(O.iterdir()) if p.is_file()],'self_excluded':True})
 print(json.dumps({'status':result['status'],'report':bind(O/'report.json'),'seal':bind(O/'seal.json'),'affected_N':7},ensure_ascii=False))
if __name__=='__main__':main()
