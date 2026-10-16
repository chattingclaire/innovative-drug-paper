"""Independent actual delta and exact byte-line composite audit; no recoding."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import hashlib,json,runpy
O=Path(__file__).resolve().parent;G=O.parents[2];A=O.parent/'preparation-readback'
P=G/'06-coding/rule-full4481-final-v7-root/run4481-first';PREP=G/'06-coding/rule-v8-bounded-delta-root';DELTA=PREP/'run-affected-first';MERGE=G/'06-coding/rule-full4481-v8-delta-merged-root';D=('S','E','Ec','I','F');I={}
def cj(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def bind(p):
 p=Path(p).resolve();h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return {'path':str(p),'bytes':p.stat().st_size,'sha256':h.hexdigest()}
def reg(p,b=None):
 actual=bind(p)
 if b:assert all(actual[k]==b[k] for k in ('path','bytes','sha256')),actual
 I[actual['path']]=actual;return Path(actual['path'])
def load(p):return json.loads(reg(p).read_bytes())
def save(n,x):
 with (O/n).open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def lines(p,slot=False):
 result={}
 for raw in reg(p).read_bytes().splitlines(keepends=True):
  assert raw.endswith(b'\n');x=json.loads(raw);k=(x['id'],x['dimension']) if slot else x['id'];assert k not in result;result[k]=(x,raw)
 return result
def sealed_run(run,N,tag):
 s=load(run/'seal.json');e=load(run/'execution.json');f=load(run/'freeze.json')
 assert s['status']==tag and s['record_N']==N and s['dimension_N']==5*N
 for group in ('output_files','implementation_files','material_bindings','control_inputs'):
  for b in s[group]:reg(b['path'],b)
 assert e['status']=='completed' and e['actual_record_N']==N and e['actual_dimension_N']==5*N and e['actual_cohort_inference_runs']==1 and e['technical_failure_dimension_N']==0 and not e['implementation_errors']
 assert s['source_packet_unchanged'] and s['no_reference_read'] and e['no_reference_read'] and f['reference_input'] is None
 assert e['formal_validation_complete'] is False and e['human_validation_complete'] is False and f['blind_validation'] is False
 allowed={str(Path(b['path']).resolve()) for b in f['implementation_files']+f['material_bindings']+f['control_inputs']}
 bad=[]
 for p in e['read_paths']:
  p=str(Path(p).resolve())
  assert Path(p).suffix!='.xlsx' and Path(p).name!='reference.jsonl' and '/04-calibration/' not in p and '/07-statistics/' not in p and '/09-delivery/' not in p
  if p not in allowed and str(run) not in p and '/lib/python' not in p:bad.append(p)
 assert not bad
 return s,e,f
def main():
 assert not (O/'report.json').exists();reg(__file__)
 prepseal=load(A/'seal.json')
 for b in prepseal['files']:reg(b['path'],b)
 prepared=load(A/'report.json');assert prepared['affected_record_N']==7 and prepared['status']=='actual_frozen_preparation_and_sidecars_independently_read_back_no_blocking_issue'
 ps,pe,pf=sealed_run(P,4481,'sealed_complete_production_provisional_rule_run');ds,de,df=sealed_run(DELTA,7,'sealed_complete_production_provisional_rule_delta_run')
 ms=load(MERGE/'seal.json')
 assert ms['status']=='complete_v8_compatible_composite_with_explicit_execution_origins' and ms['all4481_actually_inferred_under_v8'] is False and ms['no_new_inference_executed_by_merge']
 for b in ms['files']+ms['ancestor_seals']:reg(b['path'],b)
 status=load(MERGE/'composite-status.json');closure=load(PREP/'impact-closure-plan.json');lineage=load(PREP/'original-input-lineage-sidecar.json')
 ids=closure['affected_record_ids'];assert ids==[x['id'] for x in prepared['affected_records']] and len(ids)==7
 assert df['source_scope']['approved_record_ids']==ids and df['fixed_algorithm_version']=='joint-v8-target-product-gap-sol'
 before=lines(P/'predictions.jsonl');after=lines(DELTA/'predictions.jsonl');merged=lines(MERGE/'predictions.jsonl');bs=lines(P/'all-dimension-slots.jsonl',True);ns=lines(DELTA/'all-dimension-slots.jsonl',True);mergedslots=lines(MERGE/'all-dimension-slots.jsonl',True)
 assert list(after)==ids and list(merged)==list(before)==pf['source_scope']['approved_record_ids'] and len(before)==len(merged)==4481
 assert list(ns)==[(sid,d) for sid in ids for d in D] and list(mergedslots)==list(bs)==[(sid,d) for sid in before for d in D]
 labelchanges=[];decisionchanges=[];requestfields=('source_requests','relation_traces','source_relation_traces','material_requests','source_protocol_requirements_recorded','source_dependency_stop_reasons')
 for sid in ids:
  old=before[sid][0];new=after[sid][0]
  assert not old['implementation_errors'] and not new['implementation_errors'] and new['decisions']==new['candidate_decisions_diagnostic_only'] and set(new['labels'])==set(D)
  for d in D:
   val=new['labels'][d];assert val is None or type(val) is int and val in (0,1);assert val==new['decisions'][d]['value']
   if d!='F':assert new['decisions'][d]==old['decisions'][d]
   if val!=old['labels'][d]:labelchanges.append({'id':sid,'dimension':d,'old':old['labels'][d],'new':val,'old_decision':old['decisions'][d],'new_decision':new['decisions'][d]})
   if new['decisions'][d]!=old['decisions'][d]:decisionchanges.append({'id':sid,'dimension':d,'value_changed':val!=old['labels'][d]})
  assert all(old.get(k)==new.get(k) for k in requestfields),sid
 # Input exact bytes and actual delivered packet identity, including actual subset offsets.
 source=reg(df['source_scope']['source_packet']['path'],df['source_scope']['source_packet']).read_bytes().splitlines(keepends=True)
 deliveries=[json.loads(x) for x in reg(DELTA/'input-deliveries.jsonl').read_bytes().splitlines()];bundles=[json.loads(x) for x in reg(DELTA/'delivered-complete-source-bundles.jsonl').read_bytes().splitlines()];packetplan=load(PREP/'packet-bindings.json')
 assert len(source)==len(deliveries)==len(bundles)==7;hashes={}
 for i,(raw,m,b,p,l) in enumerate(zip(source,deliveries,bundles,packetplan['packets'],lineage['records']),1):
  sid=ids[i-1];canonical=cj(b).encode();sha=hashlib.sha256(canonical).hexdigest();hashes[sid]=sha
  assert b==json.loads(raw) and b['source_record']['id']==sid and m['source_id']==sid and m['source_bundle_sha256']==sha and m['source_bundle_utf8_bytes']==len(canonical)
  assert m['input_line_1based']==l['subset_line_1based']==i and m['input_line_sha256']==l['exact_input_line_sha256']==hashlib.sha256(raw).hexdigest()
  assert m['input_start_utf8_byte']==l['subset_start_utf8_byte'] and m['input_end_utf8_byte_exclusive']==l['subset_end_utf8_byte_exclusive']
  assert m['actual_input_kind']=='original_frozen_native_packet' and m['same_common_JSONL_identity_verified'] and m['actual_packet_binding']==p
  packet=json.loads(reg(p['path'],p).read_bytes());assert packet['source_bundle']==b and packet['packet_version']=='native-full-source-3' and packet['source_bundle_sha256']==sha
 consumption=[json.loads(x) for x in reg(DELTA/'actual-source-consumption.jsonl').read_bytes().splitlines()];assert [x['id'] for x in consumption]==ids
 reads=uses=requests=aliases=0;views=Counter();statuses=Counter()
 for r in consumption:
  sid=r['id'];log=r['uniform_source_reading_log'];check=r['uniform_source_protocol_check'];assert not check['errors'] and r['image_read_N']==0 and log['actual_full_source_bundle_sha256']==hashes[sid]
  original=log['original_source_requests'];canonical=log['source_requests'];prov=log['source_request_status_alias_provenance'];assert len(original)==len(canonical)==len(prov) and original==after[sid][0]['source_requests']==r['source_requests']
  for a,b,p in zip(original,canonical,prov):
   fields=[k for k in ('status','dependency_status') if k in a];assert fields and len({a[k] for k in fields})==1 and all(type(a[k]) is str and a[k] in ('resolved','stopped','unresolved') for k in fields)
   assert b==dict(a,status=a[fields[0]]) and p['original_request']==a and p['original_request_canonical_sha256']==hashlib.sha256(cj(a).encode()).hexdigest() and p['canonical_request_sha256']==hashlib.sha256(cj(b).encode()).hexdigest()
   assert p['source_fields_present']==fields and p['source_field_values']=={f:a[f] for f in fields} and p['canonical_status_source']==('both_exactly_equal' if len(fields)==2 else fields[0]) and p['added_status_alias']==('status' not in a) and p['canonical_status']==b['status'] and p['nonstatus_fields_preserved'] and not p['resolution_evidence_or_consumption_certified']
   requests+=1;aliases+=int('status' not in a);statuses[b['status']]+=1
  inventory={x['resource_id']:x for x in log['source_inventory']};rr={(x['resource_id'],x['view']):x for x in log['read_receipts']};ridset={x['receipt_id'] for x in log['read_receipts']}
  for q in log['read_receipts']:
   assert q['record_id']==sid and q['source_sha256']==inventory[q['resource_id']]['source_sha256'] and q['view_sha256']==inventory[q['resource_id']]['available_views'][q['view']] and q['delivery_status']=='complete' and q['read_attestation']=='recorded' and not q['pixel_interpretation'];views[q['view']]+=1;reads+=1
  for q in log['use_receipts']:assert (q['resource_id'],q['view']) in rr and q['read_receipt_id'] in ridset;uses+=1
  assert not any(s in check['dependency_stop_reasons'] for s in ('required_view_not_read','scope_boundary_unknown','read_delivery_incomplete'))
 for k,(slot,raw) in ns.items():
  sid,d=k;assert slot['rule_value']==after[sid][0]['labels'][d] and slot['retained_rule_decision']==after[sid][0]['decisions'][d] and slot['source_bundle_sha256']==hashes[sid] and not slot['technical_failure'] and slot['rules_null']==(slot['rule_value'] is None)
 ledgers=[json.loads(x) for x in reg(DELTA/'execution-ledger.jsonl').read_bytes().splitlines()];assert [x['id'] for x in ledgers]==ids
 for i,r in enumerate(ledgers,1):assert r['index_1based']==i and r['one_adapter_view_judge_attempt_only'] and not r['technical_failure'] and r['no_null_filled_zero'] and r['labels']==after[r['id']][0]['labels'] and r['source_bundle_sha256']==hashes[r['id']]
 # Exact original line bytes, rather than reserialization equality, for every merged output.
 origin=[json.loads(x) for x in reg(MERGE/'execution-origin-lineage.jsonl').read_bytes().splitlines()];assert [x['id'] for x in origin]==list(before)
 counts={d:Counter() for d in D};inherit=actual=0
 for i,(sid,(value,raw)) in enumerate(merged.items(),1):
  selected=sid in after;expected=(after if selected else before)[sid];run=DELTA if selected else P;assert (value,raw)==expected
  p=origin[i-1];assert p['corpus_ordinal_1based']==i and p['actual_run_directory']==str(run.resolve()) and p['actual_prediction_line_sha256']==hashlib.sha256(raw).hexdigest() and p['prediction_line_bytes']==len(raw) and p['unchanged_actual_record_bytes_retained']
  assert p['actual_inference_algorithm']==('joint-v8-target-product-gap-sol' if selected else 'joint-v7-relation-content-sol') and p['v8_compatibility_basis']==('actual_v8_delta_inference' if selected else 'unchanged_input_and_proved_changed_branch_not_reached') and p['source_consumption_log']==str((run/'actual-source-consumption.jsonl').resolve()) and p['source_consumption_record_key']==sid
  actual+=int(selected);inherit+=int(not selected)
  for d in D:
   k=sid,d;assert mergedslots[k]==(ns if selected else bs)[k];s=mergedslots[k][0];assert s['rule_value']==value['labels'][d] and not s['technical_failure'];counts[d]['positive_N' if s['rule_value']==1 else 'negative_N' if s['rule_value']==0 else 'lawful_null_N']+=1
 assert actual==7 and inherit==4474
 counted={d:{k:counts[d][k] for k in ('positive_N','negative_N','lawful_null_N')} for d in D};assert status['counts']==counted and status['lawful_null_N']==sum(x['lawful_null_N'] for x in counted.values())==238
 assert status['actual_record_N']==4481 and status['actual_dimension_N']==22405 and status['actual_v8_delta_inference_record_N']==7 and status['inherited_v7_record_N']==4474 and status['all4481_actually_inferred_under_v8'] is False
 assert status['formal_validation_complete'] is False and status['human_validation_complete'] is False and status['paper_writing_gate_open'] is False
 changes=load(MERGE/'v7-to-v8-actual-changes.json');assert changes['complete_decision_changes']==decisionchanges and not changes['source_or_relation_log_changes'] and changes['other_four_dimensions_all_identical']
 assert [(x['id'],x['dimension'],x['parent_value'],x['delta_value']) for x in changes['label_changes']]==[(x['id'],x['dimension'],x['old'],x['new']) for x in labelchanges]
 for x,y in zip(labelchanges,changes['label_changes']):assert x['old_decision']==y['parent_decision'] and x['new_decision']==y['delta_decision']
 assert len(labelchanges)==len(decisionchanges)==status['label_change_N_v7_to_v8']==status['decision_change_N_v7_to_v8']==2
 oldv5=lines(G/'06-coding/rule-full4481-final-v5-receipt-recovery-root/recovered-predictions.jsonl');v5changes=[{'id':sid,'dimension':d,'old':oldv5[sid][0]['labels'][d],'new':row[0]['labels'][d]} for sid,row in merged.items() for d in D if oldv5[sid][0]['labels'][d]!=row[0]['labels'][d]];assert len(v5changes)==116
 save('v7-to-v8-independent-actual-changes.json',{'label_changes':labelchanges,'decision_changes':decisionchanges,'source_request_and_relation_fields_all_same':True})
 nsapi=runpy.run_path(str(reg(G/'08-audits/v7-complete-rule-independent-20261011-sol/audit_complete.py')));refmetrics={}
 for side in ('A','B'):
  p=G/f'09-delivery/agent-review-20261010/真人4项复核后-v2/编码复核表-{side}.xlsx';reg(p);ref,_=nsapi['xlsx'](p)
  refmetrics[side]={d:nsapi['metric']([(v,merged[sid][0]['labels'][d]) for (sid,dim),v in ref.items() if dim==d and type(merged[sid][0]['labels'][d]) is int],77) for d in D}
 report={'at_utc':datetime.now(timezone.utc).isoformat(),'status':'actual_delta_and_all_composite_source_bytes_independently_verified','actual_v8_delta_record_N':7,'actual_v8_delta_slot_N':35,'delta_technical_failure_N':0,'delta_null_N':3,'inherited_v7_record_N':4474,'inherited_v7_slots_byte_identical_N':22370,'actual_delta_slots_byte_identical_N':35,'merged_record_N':4481,'merged_slot_N':22405,'merged_counts':counted,'merged_null_N':238,'label_change_N_v7_to_v8':2,'complete_decision_change_N_v7_to_v8':2,'other_four_full_decisions_unchanged_N':28,'source_requests_and_relation_fields_all_unchanged':True,'v5_to_composite_changed_slots_N':116,'delta_receipts':{'read_N':reads,'use_N':uses,'views':dict(views),'request_N':requests,'status_alias_N':aliases,'statuses':dict(statuses)},'A_B_separately_computed_development77':refmetrics,'source_reading_hook_starts_after_material_preflight':True,'status_alias_not_evidence_sufficiency_certificate':True,'initial_audit_temporal_condition_failure_preserved_not_machine_failure':True,'classifier_imports_or_calls_N':0,'all4481_actually_inferred_under_v8':False,'formal_validation_complete':False,'paper_writing_gate_open':False}
 save('report.json',report)
 (O/'report.md').write_text('实际局部v8执行与合并字节已独立核验：7条/35槽、0技术失败、3待定。4474条/22370槽逐字节来自完整v7，7条/35槽逐字节来自真实delta；全部4481条/22405槽的原序与执行来源逐条对应。\n\n仅00110、00118公平性null→1改变完整decision和值；其他四维28个完整decision以及全部来源请求/关系字段不变，两条旧F阳性保留。合并待定238、F阳性50；相对旧v5变化116槽。A/B77分别复算，各385值均可比，逐维核心与辅助指标为1，仍仅开发诊断。\n\n本报告不声称4481全部实际跑v8，不声称正式验证或全文写作门槛已开放。先前审计“必须早于推理”的时间前置断言失败已保留，与机器运行0技术失败分开。\n',encoding='utf8')
 for b in I.values():assert bind(b['path'])==b
 save('input-bindings.json',{'files':list(I.values()),'all_after_readback_unchanged':True});save('seal.json',{'files':[bind(p) for p in sorted(O.iterdir()) if p.is_file()],'self_excluded':True})
 print(json.dumps({'status':report['status'],'report':bind(O/'report.json'),'seal':bind(O/'seal.json')},ensure_ascii=False))
if __name__=='__main__':main()
