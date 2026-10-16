from pathlib import Path
import json, hashlib, datetime
R=Path(__file__).resolve().parents[2];A=Path(__file__).resolve().parent;D=R/'06-coding/rule-v11-I-v16-affected-v2-root';RUN=D/'run-affected-first';V=R/'06-coding/rule-five-dimension-joint-root/versions/joint-v11-protected-data-role-sol';M=R/'01-review/source-interface-v16-article6-addendum-sol';RID='RECODE25-01402'
def h(raw):return hashlib.sha256(raw).hexdigest()
def cj(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def bind(p):
 p=p.resolve();b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':h(b)}
def save(name,x):
 with (A/name).open('x') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
def target(p):
 for n,line in enumerate(p.open(),1):
  x=json.loads(line)
  if x.get('id',x.get('source_id'))==RID:return x,n
 raise ValueError('target not found')
pred,ordinal=target(RUN/'predictions.jsonl');cons,co=target(RUN/'actual-source-consumption.jsonl');delivery,do=target(RUN/'input-deliveries.jsonl');ledger,lo=target(RUN/'execution-ledger.jsonl')
assert ordinal==co==do==lo==21
packet=M/'packets/RECODE25-01402.json';p=json.loads(packet.read_bytes());b=p['source_bundle'];s=b['source_record']['source_ref']['sha256']
assert bind(packet)['sha256']==delivery['actual_packet_binding']['sha256'];assert h(cj(b).encode())==p['source_bundle_sha256']==delivery['source_bundle_sha256']
assert pred['labels'] is None and pred['decisions'] is None
events=pred['source_view_events'];assert events==cons['source_view_events'];assert len(events)==29
# Independent mechanical projection of precisely this packet's existing
# inventory branch. No classifier/module/protocol prepare/check is executed.
# These assertions make the projection exhaustive for this one target shape.
assert not b['preserved_historical_neutral_source_supplements'] and not b['source_asset_locations']
assert all(x.get('source_locator',{}).get('kind')=='structured_JSON_and_original_HTML' for x in b['source_full_text_resources'])
assert all(not x.get('source_visual_text_resources') and not x.get('source_display_regions') for x in b['explicit_or_primary_source_resources'])
inventory=[]
inventory.append(dict(resource_id='BODY-'+RID,source_sha256=s,available_views={'text':h(b['source_record']['text'].encode())},locator=b['source_record']['source_ref']['locator'],projection_pointer='/source_record'))
for n,c in enumerate(b['source_record']['contexts']):
 fields={k:c[k] for k in ['text','title','caption','headers','row_cells'] if k in c}
 inventory.append(dict(resource_id=c['context_id'],source_sha256=c['source_ref']['sha256'],available_views={'text':h(cj(fields).encode()),'geometry':h(cj(c['structure']).encode())},locator=c['source_ref']['locator'],projection_pointer='/source_record/contexts/'+str(n)))
for n,d in enumerate(b['explicit_or_primary_source_resources']):
 inventory.append(dict(resource_id=d['source_resource_id'],source_sha256=d.get('source_sha256',d.get('snapshot_sha256')),available_views={'document_bundle':h(cj(d).encode())},locator={'document_resource_id':d['source_resource_id']},projection_pointer='/explicit_or_primary_source_resources/'+str(n)))
for n,x in enumerate(b['source_full_text_resources']):
 inventory.append(dict(resource_id=x['source_resource_id'],source_sha256=x['source_sha256'],available_views={'text':x['text_sha256']},locator=x['source_locator'],projection_pointer='/source_full_text_resources/'+str(n)))
assert len(inventory)==14 and not any(x['resource_id'].startswith('FULLSOURCE-') for x in inventory)
resolved=inventory # source_receipts resolves FULLSOURCE-only; none exist here.
lookup={x['resource_id']:x for x in resolved};checks=[];seen=set()
body=dict(resource_id='BODY-'+RID,view='text',source_sha256=s,view_sha256=h(b['source_record']['text'].encode()),event_kind='current_text_matching_view')
for driver_i,e in enumerate([body]+events):
 key=(e['resource_id'],e['view'])
 if key in seen:continue
 seen.add(key);old=lookup.get(e['resource_id'])
 ok=old is not None and e['source_sha256']==old['source_sha256'] and e['view_sha256']==old['available_views'].get(e['view'])
 checks.append(dict(driver_event_index_zero_based=driver_i,view_event_index_zero_based=driver_i-1 if driver_i else None,resource_id=e['resource_id'],view=e['view'],event_source_sha256=e['source_sha256'],event_view_sha256=e['view_sha256'],producer_inventory_entry=old,resolved_inventory_entry=old,guard_would_match=ok,reason='entry absent in both producer/resolved' if old is None else 'all source/view hashes match' if ok else 'hash mismatch'))
missing=[x for x in checks if not x['guard_would_match']];assert len(missing)==5 and missing[0]['driver_event_index_zero_based']==14
src=b['explicit_or_primary_source_resources'][1]['source_texts']
assert [x['resource_id'] for x in missing]==[x['source_resource_id'] for x in src]
necessary=[]
for i,x in enumerate(src):
 assert h(x['text'].encode())==x['text_sha256']==missing[i]['event_view_sha256']
 assert x['source_sha256']==s==x['source_locator']['structured_snapshot']['sha256']
 necessary.append(dict(source_bundle_pointer='/explicit_or_primary_source_resources/1/source_texts/'+str(i),source_resource_id=x['source_resource_id'],source_document_resource_id=x['source_document_resource_id'],source_sha256=x['source_sha256'],text_sha256=x['text_sha256'],role=x['role'],text=x['text'],source_locator=x['source_locator'],source_version_id=x['source_version_id']))
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
save('exact01402-first-failure-evidence.json',dict(at_utc=now,record_id=RID,original_row_line_1based=21,packet_binding=bind(packet),source_bundle_sha256=p['source_bundle_sha256'],actual_error=pred['implementation_errors'],actual_uniform_audit_state=pred['uniform_source_audit_state'],source_log_returned=False,retained_labels=None,retained_decisions=None,candidate_diagnostic_only_present=bool(pred.get('candidate_decisions_diagnostic_only')),first_exact_failure=missing[0],actual_original_source_view_events=events,actual_source_relation_traces=pred['source_relation_traces'],static_expected_inventory_projection=inventory,static_resolved_inventory_projection=resolved,source_identity_resolution_delta_for_target=[],projection_basis='unchanged source_packet inventory AST branches; target exhaustive metadata assertions. Not a returned runtime log and no classifier/module/protocol rerun.',unique_view_checks=checks,all_missing_text_inventory_entries=missing,source_relation_use_ids=[{'resource_id':z['resource_id'],'view':z['view']} for t in pred['source_relation_traces'] for z in t.get('used_source_views',[])],control_execution_order_correction='Actual immutable driver main365 judge/validation produced diagnostic-only decisions before main371 actual_reading_log failed; these are not retained valid predictions.'))
save('necessary-five-literal-inventory-provenance.json',dict(at_utc=now,packet_binding=bind(packet),material_seal=bind(M/'output-seal.json'),source_document_pointer='/explicit_or_primary_source_resources/1',source_document_bundle_sha256=h(cj(b['explicit_or_primary_source_resources'][1]).encode()),original_source_sha256=s,resources=necessary,identity_and_text_hashes_independent_of_actual_event=True,original_source_same_version_binding='already sealed v16 literal original structured snapshot/HTML positions; no new material or semantic inference',new_semantic_source_read=False))
proposal=dict(at_utc=now,status='proposal_only_not_implemented',cause='Unchanged _v12_source_inventory exposes explicit documents as document_bundle, but does not expose their source_texts. _v13/source_inventory literal paragraph registry only traverses source_full_text_resources. Old NP003..012 have mirrors there; new five literal source_texts live only in explicit doc1. _derived_contexts scans them and emits literal text events, so the first NP013 event finds no inventory entry. This is a missing neutral inventory projection, not event/document hash collision or source identity bridging.',first_failure=missing[0],all_missing_N=5,document_bundle_hash_mismatch=False,raw_vs_resolved_source_SHA_mismatch=False,old_fulltext_collision=False,minimal_transport_only_fix=['Add a separate neutral inventory extension in a NEW transport version; keep C five modules, common packet/v16, original producer library inventory and original v12 protocol code byte-identical.','Derive missing literal entries from explicit_or_primary_source_resources[*].source_texts only for the already supported structured_JSON_and_original_HTML representation. Do not use actual events or predicted values to construct expected identity.','Verify literal text SHA from immutable text; same document/version/source SHA; independently bound original structured JSON pointer and original HTML SHA/finite positions. Append schema-equivalent text view entries with existing resource_id/source_document_resource_id/source_sha256/source_locator/text_sha256/role; status remains available/not_recorded.','Retain original producer inventory separately. Preserve every old entry exactly. Duplicate IDs must match immutable original source/view/locator proof or fail; never overwrite or silently conflate conflicting IDs.','Wire the identical extended/resolved inventory function into finite facade.source_inventory, protocol source_identity_resolver and actual log expected inventory. Preserve old FULLSOURCE identity delta separately and record each added neutral literal entry provenance.','Keep actual events, relation use traces, requirements, source/view hash guard and original protocol.check unchanged. Missing/invalid provenance remains technical failure.','Recovery scope only01402 in a fresh separately authorized output. Preserve43 first valid results and both prior prep/runtime failures, including all5 failed slots for14, as distinct actual origins.'],forbidden_actions=['no dropping/scanning-event suppression','no deriving expected hashes from event claims','no guard relaxation','no positive/null hard-fill','no I expectation/value change','no protocol/candidate/manual/prompt/material edit'],proposal_material_binding=bind(A/'necessary-five-literal-inventory-provenance.json'),model_calls=0,classifier_calls=0,transport_reruns=0)
save('minimal-transport-only-proposal.json',proposal)
scope=json.loads((D/'frozen-scope.json').read_bytes())
inputs=[packet,M/'output-seal.json',D/'rule_driver.py',D/'frozen-scope.json',V/'source_packet.py',V/'source_receipts.py',V/'relations.py',Path(scope['source_reading_protocol_code']['path'])]+[RUN/n for n in ['predictions.jsonl','actual-source-consumption.jsonl','input-deliveries.jsonl','execution-ledger.jsonl','seal.json']]
save('input-bindings-and-read-scope.json',dict(at_utc=now,inputs=[bind(x) for x in inputs],selected_record_id=RID,read_mode='Mechanical target-row extraction only from multi-record run files; no other record semantics inspected. Code/metadata/source hashes only.',other_record_semantic_read=False,human200_or_remaining_read=False,classifier_or_model_rerun=False,immutable_files_edited=False))
(A/'report.md').write_text('首个失配：actual events[14]（BODY前置后；view.source_view_events[13]），SOURCETEXT-09d813b3014db413-NP013 / text。原source SHA 09d813b3014db4137d2bceab8bc280c396a5916fafa7bb4c216c5798ae824d06；literal view SHA 70c4d7e260d73b470e7f68023054718381eef7aaaed9538baca4182a512cbca9。producer及resolved inventory都无该ID。\n\n五个新source_texts均缺inventory条目；旧9段在source_full_text_resources有镜像，故旧事件可核。两份document_bundle哈希均匹配，没有raw/resolved SHA桥接变化，也没有源字面值冲突。实际view事件和关系使用日志保留，uniform log未返回；静态inventory投影明确标注非runtime返回日志。\n\n建议仅新增运输层中性literal inventory adapter，从冻结source_texts及独立原源JSON/HTML绑定登记缺失text视图；producer原库存和旧条目原样保留，新增来源证明单列。相同扩展inventory须用于prepare、check、resolver及actual_reading_log；不删事件、不放宽guard、不改协议/C/材料/期待。ROOT另授权仅14技术恢复，43条首轮有效结果和全部失败保留。\n\n实际driver已先judge/validate并留下diagnostic-only，随后actual_reading_log失败；这不构成有效预测，retained labels/decisions仍null。此次0 classifier、0 model、0 rerun，无任何冻结输入修改。\n')
files=[x for x in A.rglob('*') if x.is_file() and x.name!='output-seal.json']
save('output-seal.json',dict(at_utc=now,status='bounded_diagnosis_frozen_stopped_proposal_only',files=[bind(x) for x in sorted(files)],self_excluded=True,model_calls=0,classifier_calls=0,reruns=0))
print(json.dumps({'first_resource':missing[0]['resource_id'],'missing_N':len(missing),'document_hash_mismatch':False,'proposal':str(A/'minimal-transport-only-proposal.json'),'seal':bind(A/'output-seal.json')},ensure_ascii=False,indent=2))
