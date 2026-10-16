"""Independent completed v9 delta/merge byte, receipt and arithmetic readback.

No coder/selector executes; source-only adapter resolves original supplied handles.
All bodies, decisions and quotes are checked mechanically, not adjudicated.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,collections,sys,importlib.util
sys.dont_write_bytecode=True
G=Path(__file__).resolve().parents[3];O=Path(__file__).resolve().parent
PREP=G/'06-coding/rule-v9-affected-original-common-root';DELTA=PREP/'run-affected-first';BASE=G/'06-coding/rule-full4481-v8-delta-merged-root';DIMS=('S','E','Ec','I','F');inputs={}
def cj(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def bind(p):
 p=Path(p).resolve();h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return dict(path=str(p),bytes=p.stat().st_size,sha256=h.hexdigest())
def reg(p,s=None):
 a=bind(p)
 if s:assert all(a[k]==s[k]for k in ('path','bytes','sha256')),p
 inputs[a['path']]=a;return Path(a['path'])
def load(p):return json.loads(reg(p).read_bytes())
def save(n,v):
 with (O/n).open('x',encoding='utf8')as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def line_map(p,slots=False):
 rows={}
 for raw in reg(p).read_bytes().splitlines(keepends=True):
  assert raw.endswith(b'\n');x=json.loads(raw);k=(x['id'],x['dimension'])if slots else x['id'];assert k not in rows;rows[k]=(x,raw)
 return rows
def verify_seal(p):
 s=load(p)
 for k in ('files','output_files','implementation_files','material_bindings','control_inputs','ancestor_seals'):
  for b in s.get(k,[]):reg(b['path'],b)
 return s
parser=argparse.ArgumentParser();parser.add_argument('--merge',required=True);args=parser.parse_args();MERGE=Path(args.merge).resolve()
assert (DELTA/'seal.json').exists()and(MERGE/'seal.json').exists(),'Do not audit unfinished outputs as final'
assert not(O/'report.json').exists()
prepared=load(O.parent/'prepared-scope-readback/report.json');scope=load(PREP/'frozen-scope.json');plan=load(PREP/'impact-closure-plan.json');lineage=load(PREP/'original-input-lineage-sidecar.json');packets=load(PREP/'packet-bindings.json')
reg(prepared['prepared_scope_binding']['path'],prepared['prepared_scope_binding']);reg(prepared['actual_driver_binding']['path'],prepared['actual_driver_binding'])
adoption=load(PREP/'ROOT-pre-inference-adoption-sidecar.json');seal=verify_seal(DELTA/'seal.json');execution=load(DELTA/'execution.json');freeze=load(DELTA/'freeze.json');merged_seal=verify_seal(MERGE/'seal.json');status=load(MERGE/'composite-status.json');verify_seal(BASE/'seal.json')
ids=scope['approved_record_ids'];assert len(ids)==3904 and seal['record_N']==3904 and seal['dimension_N']==19520 and seal['status']=='sealed_complete_production_provisional_rule_delta_run'
assert execution['status']=='completed'and execution['actual_record_N']==3904 and execution['actual_dimension_N']==19520 and execution['actual_cohort_inference_runs']==1 and execution['technical_failure_dimension_N']==0 and not execution['implementation_errors']
assert execution['no_reference_read']and seal['no_reference_read']and seal['source_packet_unchanged']and freeze['reference_input']is None
assert execution['formal_validation_complete']is execution['human_validation_complete']is freeze['blind_validation']is False
assert seal['control_inputs']==freeze['control_inputs']==[bind(PREP/'frozen-scope.json')]
for k in ('final_candidate_algorithm','final_candidate_pre_execution_seal','final_candidate_delivery_seal'):assert freeze[k]==scope[k];reg(scope[k]['path'],scope[k])
for k,n in [('impact_plan','impact-closure-plan.json'),('frozen_scope','frozen-scope.json'),('pre_execution_seal','pre-execution-run-seal.json'),('original_input_lineage','original-input-lineage-sidecar.json')]:assert adoption[k]==bind(PREP/n)
assert adoption['candidate_total_seal']==plan['candidate_delivery']and adoption['selection']==plan['selection']
for key in ('candidate_total_seal','candidate_freeze','selection','impact_plan','frozen_scope','pre_execution_seal','original_input_lineage','baseline_compatible_seal','independent_static_audit_seal','independent_prepared_scope_audit_seal','approved_static_contract'):reg(adoption[key]['path'],adoption[key])
assert adoption['independent_prepared_scope_audit_seal']==bind(O.parent/'prepared-scope-readback/output-seal.json')
for s in adoption['required_candidate_members_verified']:reg(s['path'],s)
assert len(adoption['required_candidate_members_verified'])==117 and adoption['actual_selected_N']==3904 and adoption['inherited_parent_N']==577 and adoption['actual_cohort_passes_authorized']==1
assert adoption['semantic_acceptance_complete']is adoption['formal_validation_complete']is adoption['paper_writing_gate_open']is False
assert datetime.datetime.fromisoformat(adoption['at_utc'])<datetime.datetime.fromisoformat(execution['started_at_utc'])
assert adoption['provisional_delta_adoption_by_ROOT']and adoption['same_independent_selector_set']
allowed={str(Path(s['path']).resolve())for s in freeze['implementation_files']+freeze['material_bindings']+freeze['control_inputs']}
for p in execution['read_paths']:
 p=str(Path(p).resolve());assert not any(t in p for t in ['/04-calibration/','/07-statistics/','/09-delivery/','.xlsx','reference.jsonl'])
 assert p in allowed or str(DELTA)in p or '/lib/python'in p,p
old=line_map(BASE/'predictions.jsonl');new=line_map(DELTA/'predictions.jsonl');merged=line_map(MERGE/'predictions.jsonl');oldslots=line_map(BASE/'all-dimension-slots.jsonl',True);newslots=line_map(DELTA/'all-dimension-slots.jsonl',True);mergedslots=line_map(MERGE/'all-dimension-slots.jsonl',True);prior_origins=line_map(BASE/'execution-origin-lineage.jsonl');origins=line_map(MERGE/'execution-origin-lineage.jsonl')
assert list(new)==ids and list(old)==list(merged)==list(prior_origins)==list(origins)and len(merged)==4481
assert list(newslots)==[(rid,d)for rid in ids for d in DIMS]and list(mergedslots)==list(oldslots)==[(rid,d)for rid in old for d in DIMS]
labelchanges=[];decisionchanges=[];logs=[];counts={d:collections.Counter()for d in DIMS};actual_origins=collections.Counter()
for i,(rid,(row,raw))in enumerate(merged.items(),1):
 selected=rid in new;source=(new if selected else old)[rid];assert (row,raw)==source
 origin=origins[rid][0];prior=prior_origins[rid][0]
 assert origin['corpus_ordinal_1based']==i and origin['actual_prediction_line_sha256']==hashlib.sha256(raw).hexdigest()and origin['prediction_line_bytes']==len(raw)
 assert origin['source_consumption_record_key']==rid and origin['unchanged_actual_record_bytes_retained']
 if selected:
  assert origin['actual_run_directory']==str(DELTA)and origin['actual_inference_algorithm']=='joint-v9-generic-relationship-sol'and origin['source_consumption_log']==str(DELTA/'actual-source-consumption.jsonl')
  assert origin['v9_compatibility_basis']=='actual_v9_affected_inference'
 else:
  for k in ('actual_run_directory','actual_inference_algorithm','source_consumption_log','source_consumption_record_key'):assert origin[k]==prior[k]
  assert origin['v9_compatibility_basis']=='unchanged_input_and_proved_new_gate_not_reached'and origin['inherited_parent_origin_binding']['line_sha256']==hashlib.sha256(prior_origins[rid][1]).hexdigest()
 actual_origins[origin['actual_inference_algorithm']]+=1
 assert row['candidate_decisions_diagnostic_only']==row['decisions']and not row['implementation_errors']
 for d in DIMS:
  val=row['labels'][d];assert val is None or type(val)is int and val in (0,1);assert val==row['decisions'][d]['value']
  expectedslots=(newslots if selected else oldslots)[(rid,d)];assert mergedslots[(rid,d)]==expectedslots
  slot=expectedslots[0];assert slot['rule_value']==val and slot['retained_rule_decision']==row['decisions'][d]and not slot['technical_failure']and slot['rules_null']==(val is None)
  counts[d]['positive_N'if val==1 else'negative_N'if val==0 else'lawful_null_N']+=1
  if selected:
   previous=old[rid][0]
   if d in ('S','E','Ec'):assert row['decisions'][d]==previous['decisions'][d],(rid,d)
   if val!=previous['labels'][d]:labelchanges.append({'id':rid,'dimension':d,'old':previous['labels'][d],'new':val,'old_decision':previous['decisions'][d],'new_decision':row['decisions'][d]})
   if row['decisions'][d]!=previous['decisions'][d]:decisionchanges.append({'id':rid,'dimension':d,'value_changed':val!=previous['labels'][d]})
 if selected:
  for k in ('source_requests','source_relation_traces','relation_traces'):
   if row.get(k)!=old[rid][0].get(k):logs.append({'id':rid,'field':k})
counted={d:{k:c[k]for k in ('positive_N','negative_N','lawful_null_N')}for d,c in counts.items()};assert status['counts']==counted and status['lawful_null_N']==sum(c['lawful_null_N']for c in counted.values())
assert status['actual_record_N']==4481 and status['actual_dimension_N']==22405 and status['technical_failure_dimension_N']==0 and status['formal_validation_complete']is False
changes=load(MERGE/'v8-compatible-to-v9-actual-changes.json');assert changes['complete_decision_changes']==decisionchanges and changes['source_or_relation_log_changes']==logs and changes['S_E_Ec_complete_decisions_all_identical']
assert [(x['id'],x['dimension'],x['parent_value'],x['delta_value'])for x in changes['label_changes']]==[(x['id'],x['dimension'],x['old'],x['new'])for x in labelchanges]
for x,y in zip(changes['label_changes'],labelchanges):assert x['parent_decision']==y['old_decision']and x['delta_decision']==y['new_decision']
# Source-only exact-handle reconstruction, never RelationView/dimensions/judge.
adapter_path=Path(next(x['path']for x in load(PREP/'algorithm-bindings.json')['modules']if x['module']=='source_packet'));reg(adapter_path)
spec=importlib.util.spec_from_file_location('independent_v9_source_handle_adapter',adapter_path);adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
source=reg(scope['source_packet']['path'],scope['source_packet']).read_bytes().splitlines(keepends=True)
deliveries=[json.loads(x)for x in reg(DELTA/'input-deliveries.jsonl').read_bytes().splitlines()];bundles=[json.loads(x)for x in reg(DELTA/'delivered-complete-source-bundles.jsonl').read_bytes().splitlines()];units=[json.loads(x)for x in reg(DELTA/'effective-semantic-units.jsonl').read_bytes().splitlines()];consumption=[json.loads(x)for x in reg(DELTA/'actual-source-consumption.jsonl').read_bytes().splitlines()];ledgers=[json.loads(x)for x in reg(DELTA/'execution-ledger.jsonl').read_bytes().splitlines()]
assert len(source)==len(deliveries)==len(bundles)==len(units)==len(consumption)==len(ledgers)==3904
reads=uses=requests=aliases=quotes_N=0;views=collections.Counter();requeststatuses=collections.Counter()
for i,(raw,m,b,u,r,ledger,p,l)in enumerate(zip(source,deliveries,bundles,units,consumption,ledgers,packets['packets'],lineage['rows']),1):
 rid=ids[i-1];canon=cj(b).encode();sha=hashlib.sha256(canon).hexdigest()
 assert b==json.loads(raw)and b['source_record']['id']==rid and m['source_id']==u['id']==r['id']==ledger['id']==rid
 assert m['source_bundle_sha256']==sha and m['source_bundle_utf8_bytes']==len(canon)and m['input_line_sha256']==l['line_sha256']==hashlib.sha256(raw).hexdigest()
 assert m['input_line_1based']==l['subset_ordinal_1based']==i and m['input_start_utf8_byte']==l['subset_utf8_start']and m['input_end_utf8_byte_exclusive']==l['subset_utf8_end']
 assert m['actual_packet_binding']==p and m['same_common_JSONL_identity_verified']and m['actual_input_kind']=='original_frozen_native_packet'
 assert p['source_bundle_sha256']==sha and p['output_id']==m['original_packet_output_id']
 semantic=adapter.semantic_unit(b);assert semantic==u['semantic_unit'];by_id={c['context_id']:c for c in semantic['contexts']}
 def quote(q):
  global quotes_N
  if not isinstance(q,dict):return
  if {'context_id','start','end','text','source_ref'}<=set(q):
   c=by_id[q['context_id']];a=q['start'];z=q['end'];assert type(a)is int and type(z)is int and 0<=a<z<=len(c['text'])and q['text']==c['text'][a:z]and q['source_ref']==c['source_ref'];quotes_N+=1
 def nested(q):
  if isinstance(q,dict):
   quote(q)
   for v in q.values():nested(v)
  elif isinstance(q,list):
   for v in q:nested(v)
 for decision in new[rid][0]['decisions'].values():
  for key in ('current_anchor','current_proposition'):
   q=decision[key]
   if q is not None:
    a,z=q['start'],q['end'];assert type(a)is int and type(z)is int and 0<=a<z<=len(semantic['text'])and q['text']==semantic['text'][a:z]
  nested(decision['context_evidence']);nested(decision['details'])
 for relation in new[rid][0]['relation_traces']:nested(relation)
 log=r['uniform_source_reading_log'];check=r['uniform_source_protocol_check'];assert not check['errors']and r['image_read_N']==0 and log['actual_full_source_bundle_sha256']==sha
 original=log['original_source_requests'];canonical=log['source_requests'];provenance=log['source_request_status_alias_provenance'];assert len(original)==len(canonical)==len(provenance)and original==r['source_requests']==new[rid][0]['source_requests']
 for a,c,proof in zip(original,canonical,provenance):
  fields=[k for k in ('status','dependency_status')if k in a];assert fields and len({a[k]for k in fields})==1 and all(type(a[k])is str and a[k]in ('resolved','stopped','unresolved')for k in fields)
  assert c==dict(a,status=a[fields[0]])and proof['original_request']==a and proof['original_request_canonical_sha256']==hashlib.sha256(cj(a).encode()).hexdigest()and proof['canonical_request_sha256']==hashlib.sha256(cj(c).encode()).hexdigest()
  assert proof['canonical_status_source']==('both_exactly_equal'if len(fields)==2 else fields[0])and proof['added_status_alias']==('status'not in a)
  assert proof['source_fields_present']==fields and proof['source_field_values']=={k:a[k]for k in fields}and proof['nonstatus_fields_preserved']and not proof['resolution_evidence_or_consumption_certified']and proof['canonical_status']==c['status']
  requests+=1;aliases+=int('status'not in a);requeststatuses[c['status']]+=1
 inventory={q['resource_id']:q for q in log['source_inventory']};receiptids={q['receipt_id']for q in log['read_receipts']};readkeys={(q['resource_id'],q['view']):q for q in log['read_receipts']}
 for q in log['read_receipts']:
  assert q['record_id']==rid and q['source_sha256']==inventory[q['resource_id']]['source_sha256']and q['view_sha256']==inventory[q['resource_id']]['available_views'][q['view']]and q['delivery_status']=='complete'and q['read_attestation']=='recorded'and not q['pixel_interpretation'];reads+=1;views[q['view']]+=1
 for q in log['use_receipts']:assert (q['resource_id'],q['view'])in readkeys and q['read_receipt_id']==readkeys[(q['resource_id'],q['view'])]['receipt_id'];uses+=1
 assert not any(s in check['dependency_stop_reasons']for s in ('required_view_not_read','scope_boundary_unknown','read_delivery_incomplete'))
 assert ledger['index_1based']==i and ledger['one_adapter_view_judge_attempt_only']and not ledger['technical_failure']and ledger['no_null_filled_zero']and ledger['labels']==new[rid][0]['labels']and ledger['source_bundle_sha256']==sha
 for d in DIMS:assert newslots[(rid,d)][0]['source_bundle_sha256']==sha
report={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'completed_delta_and_complete_composite_mechanically_verified','actual_delta_record_N':3904,'actual_delta_slots_N':19520,'inherited_record_N':577,'merged_record_N':4481,'merged_slots_N':22405,'delta_technical_failure_N':0,'merged_counts':counted,'merged_null_N':status['lawful_null_N'],'actual_execution_origin_counts':dict(actual_origins),'S_E_Ec_complete_decisions_identical_N':3904*3,'value_change_N':len(labelchanges),'complete_decision_change_N':len(decisionchanges),'source_or_relation_log_change_N':len(logs),'all_merged_prediction_and_slot_lines_exact_actual_origin_bytes':True,'original_input_delivery_ordinal_byte_source_binding_N':3904,'source_only_effective_units_identical_N':3904,'read_receipt_N':reads,'used_receipt_N':uses,'read_views':dict(views),'request_N':requests,'mechanical_status_alias_N':aliases,'request_status_counts':dict(requeststatuses),'exact_quote_ranges_checked_N':quotes_N,'pre_inference_adoption_time_verified':True,'runtime_read_path_binding_verified':True,'read_hook_begins_after_preflight_not_whole_process_proof':True,'status_alias_not_semantic_evidence_certificate':True,'candidate_classifier_or_selector_executed_by_this_audit':False,'new_or_human200_semantic_adjudication':False,'formal_validation_complete':False,'paper_final_ready':False}
save('actual-changes.json',{'label_changes':labelchanges,'complete_decision_changes':decisionchanges,'log_changes':logs});save('report.json',report)
with (O/'report.md').open('x',encoding='utf8')as f:f.write(f'真实delta与完整合并通过机械核验：3904条/19520槽，0技术失败；577条继承原父行字节。4481条/22405槽及真执行来源逐条一致。S/E/Ec的11712个完整decision保持。原输入与实际delivery、单次ledger、来源receipt及状态别名均逐条绑定。\n\n值变化{len(labelchanges)}槽、完整decision变化{len(decisionchanges)}槽、合并待定{status["lawful_null_N"]}槽。具体变化保存于actual-changes.json；本报告只核机械来源与算术，不为未曝光或human200正文作语义裁决，不执行分类器，也不证明机器语义正确或正式验证成立。\n')
for s in inputs.values():assert bind(s['path'])==s
save('input-bindings.json',{'inputs':list(inputs.values()),'exact_before_after':True})
files=[bind(p)for p in sorted(O.iterdir())if p.is_file()and p.name!='output-seal.json'];save('output-seal.json',{'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':files,'input_bindings':list(inputs.values()),'classification_runs':0,'formal_validation_complete':False,'self_excluded':True})
print(json.dumps({'report':bind(O/'report.json'),'seal':bind(O/'output-seal.json'),'counts':counted,'value_change_N':len(labelchanges)},ensure_ascii=False))
