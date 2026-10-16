"""Independent post-completion audit; never imports or calls a rule classifier."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter,defaultdict
from fractions import Fraction
import json,hashlib,csv,sys,zipfile,re,posixpath,xml.etree.ElementTree as ET
OUT=Path(__file__).resolve().parent;G=OUT.parents[1]
V7=G/'06-coding/rule-full4481-final-v7-root';RUN=V7/'run4481-first';OLD=G/'06-coding/rule-full4481-final-v5-receipt-recovery-root'
DIMS=('S','E','Ec','I','F');NAMES={'S':'安全性','E':'有效性','Ec':'经济性','I':'创新性','F':'公平性'};inputs={}
def cj(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def bind(p):
 p=Path(p).resolve();h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return {'path':str(p),'bytes':p.stat().st_size,'sha256':h.hexdigest()}
def register(p,expected=None):
 b=bind(p)
 if expected:assert b['bytes']==expected['bytes'] and b['sha256']==expected['sha256'],b
 if b['path'] in inputs:assert inputs[b['path']]==b
 inputs[b['path']]=b;return Path(b['path'])
def read(p):return json.loads(register(p).read_bytes())
def jl(p):
 with register(p).open(encoding='utf8') as f:
  for line in f:yield json.loads(line)
def save(name,x):
 with (OUT/name).open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def binary(v):return type(v) is int and v in (0,1)
def divide(a,b):return None if b==0 else float(Fraction(a,b))
def metric(pairs,scope):
 assert all(binary(a) and binary(b) for a,b in pairs)
 c=Counter(pairs);tp,fp,fn,tn=(c[1,1],c[0,1],c[1,0],c[0,0]);n=sum(c.values());rp,pp,rn,pn=tp+fn,tp+fp,tn+fp,tn+fn;kden=pp*rn+rp*pn
 return {'reference_scope_N':scope,'comparable_N':n,'excluded_N':scope-n,'coverage':divide(n,scope),'TP':tp,'FP':fp,'FN':fn,'TN':tn,'reference_positive_N':rp,'reference_negative_N':rn,'prediction_positive_N':pp,'prediction_negative_N':pn,'kappa':divide(2*(tp*tn-fp*fn),kden),'P':divide(tp,pp),'R':divide(tp,rp),'F1':divide(2*tp,2*tp+fp+fn),'Po':divide(tp+tn,n),'Pe':divide(rp*pp+rn*pn,n*n),'specificity':divide(tn,rn),'NPV':divide(tn,pn),'positive_agreement':divide(2*tp,2*tp+fp+fn),'negative_agreement':divide(2*tn,2*tn+fp+fn),'metric_denominators':{'kappa':kden,'P':pp,'R':rp,'F1':2*tp+fp+fn,'Po':n,'specificity':rn,'NPV':pn,'positive_agreement':2*tp+fp+fn,'negative_agreement':2*tn+fp+fn}}
def xlsx(p):
 ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'};rns='http://schemas.openxmlformats.org/officeDocument/2006/relationships';rows={};loc={}
 with zipfile.ZipFile(register(p)) as z:
  ss=[]
  if 'xl/sharedStrings.xml' in z.namelist():ss=[''.join(e.itertext()) for e in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si',ns)]
  wb=ET.fromstring(z.read('xl/workbook.xml'));sid=next(s.attrib['{'+rns+'}id'] for s in wb.findall('s:sheets/s:sheet',ns) if s.attrib['name']=='编码表');rels=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'));target=next(x.attrib['Target'] for x in rels if x.attrib['Id']==sid);target=target.lstrip('/') if target.startswith('/') else posixpath.normpath(posixpath.join('xl',target));grid={};formulas=[]
  for row in ET.fromstring(z.read(target)).findall('s:sheetData/s:row',ns):
   cells={}
   for c in row.findall('s:c',ns):
    addr=c.attrib['r'];col=re.match('[A-Z]+',addr).group();typ=c.attrib.get('t','n');v=c.find('s:v',ns);raw=v.text if v is not None else None
    if typ=='inlineStr':val=''.join(c.find('s:is',ns).itertext())
    elif typ=='s':val=ss[int(raw)]
    elif typ=='n' and raw is not None:val=int(raw) if re.fullmatch('-?\\d+',raw) else float(raw)
    else:val=raw
    cells[col]=val
    if c.find('s:f',ns) is not None:formulas.append(addr)
   grid[int(row.attrib['r'])]=cells
  ix={value:col for col,value in grid[6].items()}
  for rn,cells in sorted(grid.items()):
   if rn<7 or not any(v is not None and str(v).strip() for v in cells.values()):continue
   raw=cells[ix['条款编号']];rid=f'RECODE25-{raw:05d}' if type(raw) is int else str(raw).strip();rid=rid if rid.startswith('RECODE25-') else 'RECODE25-'+rid.zfill(5);d=str(cells[ix['维度']]).split()[0];v=cells[ix['编码值']];assert d in DIMS and binary(v);key=rid,d;assert key not in rows;rows[key]=v;loc[key]={'row':rn,'value_cell':ix['编码值']+str(rn)};assert loc[key]['value_cell'] not in formulas
 assert len(rows)==385 and len({k[0] for k in rows})==77
 return rows,loc

def main():
 if not (RUN/'execution.json').exists() or not (RUN/'seal.json').exists():
  print(cj({'status':'waiting_for_complete_execution_and_seal','final_audit_written':False}));return
 assert not (OUT/'report.json').exists(),'never overwrite a final audit'
 auditpre=read(OUT/'pre-execution-audit-freeze.json')
 for b in auditpre['files']:register(b['path'],b)
 ex=read(RUN/'execution.json');seal=read(RUN/'seal.json');freeze=read(RUN/'freeze.json');scope=read(V7/'frozen-scope.json');oldex=read(OLD/'execution.json');oldseal=read(OLD/'seal.json');algorithm=read(V7/'algorithm-bindings.json');pre=read(V7/'pre-execution-run-seal.json')
 checks=[]
 for group in ('output_files','implementation_files','material_bindings','control_inputs'):
  for b in seal[group]:register(b['path'],b)
  checks.append({'scope':group,'bindings_checked_N':len(seal[group])})
 for b in oldseal.get('files',oldseal.get('output_files',[])):register(b['path'],b)
 delivery=read(algorithm['final_candidate_delivery_seal']['path']);register(algorithm['final_candidate_delivery_seal']['path'],algorithm['final_candidate_delivery_seal'])
 for b in delivery['files']:register(b['path'],b)
 for b in pre['files']:register(b['path'],b)
 assert ex['status']=='completed' and seal['status']=='sealed_complete_production_provisional_rule_run'
 assert ex['actual_record_N']==4481 and ex['actual_dimension_N']==22405 and ex['actual_cohort_inference_runs']==1
 assert ex['technical_failure_dimension_N']==0 and not ex['implementation_errors']
 assert freeze['reference_input'] is None and freeze['fixed_algorithm_version']=='joint-v7-relation-content-sol'
 assert ex['formal_validation_complete'] is False and freeze['blind_validation'] is False
 oldscope=read(G/'06-coding/rule-full4481-final-v5-sol/frozen-scope.json');versions={k:{'v5':oldscope[k],'v7':scope[k],'unchanged':oldscope[k]==scope[k]} for k in ('source_packet','source_package_seal','source_manifest','manual','prompt','protocol','source_reading_protocol_code')};assert all(v['unchanged'] for v in versions.values())
 assert freeze['source_scope']==scope
 allowed={str(Path(b['path']).resolve()) for b in freeze['implementation_files']+freeze['material_bindings']+freeze['control_inputs']};bad_reads=[];outside=[]
 for path in ex['read_paths']:
  s=str(Path(path).resolve())
  if Path(s).suffix=='.xlsx' or Path(s).name=='reference.jsonl' or '/04-calibration/' in s or '/07-statistics/' in s or '/09-delivery/' in s:bad_reads.append(s)
  if s not in allowed and str(RUN) not in s and '/lib/python' not in s:outside.append(s)
 assert not bad_reads and not outside;assert ex['no_reference_read'] and seal['no_reference_read']
 # Fixed records and exact original packet version, order, canonical source identity.
 ids=scope['approved_record_ids'];assert len(ids)==4481 and len(set(ids))==4481
 ds=list(jl(RUN/'input-deliveries.jsonl'));assert len(ds)==4481
 assert [x.get('record_id',x.get('id',x.get('source_id'))) for x in ds]==ids
 assert all(x['actual_input_kind']=='original_frozen_native_packet' and x['same_common_JSONL_identity_verified'] for x in ds)
 text={};bundlehash={};bids=[]
 for bundle in jl(RUN/'delivered-complete-source-bundles.jsonl'):
  rid=bundle['source_record']['id'];bids.append(rid);text[rid]=bundle['source_record']['text'];bundlehash[rid]=hashlib.sha256(cj(bundle).encode()).hexdigest()
 assert bids==ids
 packetplan=read(V7/'packet-bindings.json');assert packetplan['ordered_source_ids']==ids and packetplan['packet_N']==4481
 cursor=0;original_packet_versions=Counter()
 with Path(scope['source_packet']['path']).open('rb') as stream:
  for index,line in enumerate(stream):
   v=json.loads(line);bundle=v['source_bundle'] if 'source_bundle' in v else v;rid=ids[index];canonical=cj(bundle).encode();assert bundle['source_record']['id']==rid and hashlib.sha256(canonical).hexdigest()==bundlehash[rid]
   metadata=ds[index];assert metadata['source_id']==rid and metadata['source_bundle_sha256']==bundlehash[rid] and metadata['source_bundle_utf8_bytes']==len(canonical) and metadata['input_line_1based']==index+1 and metadata['input_line_sha256']==hashlib.sha256(line).hexdigest() and metadata['input_start_utf8_byte']==cursor and metadata['input_end_utf8_byte_exclusive']==cursor+len(line)
   pb=packetplan['packets'][index];assert metadata['actual_packet_binding']==pb;packet=json.loads(Path(pb['path']).read_bytes());assert packet['source_bundle']==bundle and packet['source_id']==rid and packet['source_bundle_sha256']==bundlehash[rid] and packet['packet_version']=='native-full-source-3';original_packet_versions[packet['packet_version']]+=1;cursor+=len(line)
 assert index+1==4481 and cursor==scope['source_packet']['bytes']
 old={} 
 for x in jl(OLD/'all-dimension-slots.jsonl'):
  k=x['id'],x['dimension'];assert k not in old;old[k]=x;assert not x['technical_failure'];assert x['rule_value'] is None or binary(x['rule_value'])
 assert len(old)==22405
 pred={};pids=[]
 for x in jl(RUN/'predictions.jsonl'):
  rid=x['id'];pids.append(rid);assert rid not in pred;assert not x['implementation_errors'] and isinstance(x['labels'],dict);assert set(x['labels'])==set(DIMS)
  assert all(x['labels'][d]==x['decisions'][d]['value'] and (x['labels'][d] is None or binary(x['labels'][d])) for d in DIMS);pred[rid]=x
 assert pids==ids
 new={};slot_ids=[];bydim={d:Counter() for d in DIMS};changes=[];transitions=Counter();basis_changes=Counter()
 with (OUT/'full4481-changes.jsonl').open('x',encoding='utf8') as detail,(OUT/'full4481-changes.csv').open('x',encoding='utf8',newline='') as cf:
  fields=['source_id','dimension','old_value','new_value','old_status','new_status','old_basis_path','new_basis_path','current_original_text','old_reason','new_reason','new_context_quotes']
  writer=csv.DictWriter(cf,fieldnames=fields);writer.writeheader()
  for x in jl(RUN/'all-dimension-slots.jsonl'):
   k=x['id'],x['dimension'];rid,d=k;assert k not in new and k in old;new[k]={'value':x['rule_value'],'status':x['status'],'decision':x['retained_rule_decision']};slot_ids.append(k)
   assert x['source_bundle_sha256']==bundlehash[rid] and not x['technical_failure']
   assert x['rule_value']==pred[rid]['labels'][d] and x['retained_rule_decision']==pred[rid]['decisions'][d]
   assert x['rules_null']==(x['rule_value'] is None);assert x['status']==('source_dependency_unresolved' if x['rule_value'] is None else 'retained_rule_decision')
   bydim[d][str(x['rule_value'])]+=1;o=old[k];transitions[(d,str(o['rule_value']),str(x['rule_value']))]+=1
   if o['rule_value']!=x['rule_value'] or o['status']!=x['status']:
    olddec=o['retained_rule_decision'];newdec=x['retained_rule_decision'];change={'source_id':rid,'dimension':d,'old_value':o['rule_value'],'new_value':x['rule_value'],'old_status':o['status'],'new_status':x['status'],'current_original_text':text[rid],'old_decision':olddec,'new_decision':newdec,'explanation_basis':'actual recorded basis_path/reason and original quoted content only; no new gold label or correctness judgment'}
    detail.write(json.dumps(change,ensure_ascii=False,allow_nan=False)+'\n');changes.append({k:v for k,v in change.items() if k not in ('old_decision','new_decision')});basis_changes[(d,olddec['basis_path'],newdec['basis_path'])]+=1
    writer.writerow({'source_id':rid,'dimension':d,'old_value':o['rule_value'],'new_value':x['rule_value'],'old_status':o['status'],'new_status':x['status'],'old_basis_path':olddec['basis_path'],'new_basis_path':newdec['basis_path'],'current_original_text':text[rid],'old_reason':olddec['reason'],'new_reason':newdec['reason'],'new_context_quotes':json.dumps([q.get('text') for q in newdec['context_evidence']],ensure_ascii=False)})
 assert slot_ids==[(rid,d) for rid in ids for d in DIMS]
 assert sum(x['value'] is None for x in new.values())==ex['lawful_null_N']
 ledgers=list(jl(RUN/'execution-ledger.jsonl'));assert len(ledgers)==4481 and [x['id'] for x in ledgers]==ids
 for index,x in enumerate(ledgers,1):assert x['index_1based']==index and not x['technical_failure'] and x['one_adapter_view_judge_attempt_only'] and x['no_null_filled_zero'] and x['labels']==pred[x['id']]['labels'] and x['source_bundle_sha256']==bundlehash[x['id']]
 # Independently reconstruct each status alias; do not import the bridge.
 request_N=0;added_N=0;source_log_ids=[];statuscounts=Counter();log_errors=[];modalitycounts=Counter();read_N=use_N=0
 for rec in jl(RUN/'actual-source-consumption.jsonl'):
  rid=rec['id'];source_log_ids.append(rid);log=rec['uniform_source_reading_log'];chk=rec['uniform_source_protocol_check'];assert not chk['errors'];assert rec['image_read_N']==0;assert log['actual_full_source_bundle_sha256']==bundlehash[rid]
  a=log['original_source_requests'];b=log['source_requests'];provenance=log['source_request_status_alias_provenance'];assert len(a)==len(b)==len(provenance)
  assert a==pred[rid]['source_requests']==rec['source_requests']
  for source,target,pr in zip(a,b,provenance):
   fields=[k for k in ('status','dependency_status') if k in source];assert fields
   assert all(type(source[k]) is str and source[k] in ('resolved','stopped','unresolved') for k in fields);assert len({source[k] for k in fields})==1
   expected=dict(source,status=source[fields[0]]);assert expected==target and pr['original_request']==source and pr['original_request_canonical_sha256']==hashlib.sha256(cj(source).encode()).hexdigest() and pr['canonical_request_sha256']==hashlib.sha256(cj(target).encode()).hexdigest()
   assert pr['source_fields_present']==fields and pr['source_field_values']=={f:source[f] for f in fields} and pr['canonical_status_source']==('both_exactly_equal' if len(fields)==2 else fields[0]) and pr['added_status_alias']==('status' not in source)
   assert pr['canonical_status']==target['status'] and pr['nonstatus_fields_preserved'] and not pr['resolution_evidence_or_consumption_certified'];request_N+=1;added_N+=int('status' not in source);statuscounts[target['status']]+=1
  receipt_keys={(x['resource_id'],x['view']) for x in log['read_receipts']};receipt_ids={x['receipt_id'] for x in log['read_receipts']};read_N+=len(log['read_receipts']);use_N+=len(log['use_receipts'])
  inventory={x['resource_id']:x for x in log['source_inventory']}
  for q in log['read_receipts']:
   assert q['record_id']==rid and q['resource_id'] in inventory and q['source_sha256']==inventory[q['resource_id']]['source_sha256'] and q['view_sha256']==inventory[q['resource_id']]['available_views'][q['view']];assert q['delivery_status']=='complete' and q['read_attestation']=='recorded' and not q['pixel_interpretation'];modalitycounts[q['view']]+=1
  for q in log['use_receipts']:assert (q['resource_id'],q['view']) in receipt_keys and q['read_receipt_id'] in receipt_ids
  assert not any(s in chk['dependency_stop_reasons'] for s in ('required_view_not_read','scope_boundary_unknown','read_delivery_incomplete'))
 assert source_log_ids==ids
 refs={};locs={};review=G/'09-delivery/agent-review-20261010/真人4项复核后-v2'
 for r in ('A','B'):refs[r],locs[r]=xlsx(review/('编码复核表-'+r+'.xlsx'))
 assert set(refs['A'])==set(refs['B']);disagree=[{'id':k[0],'dimension':k[1],'A':refs['A'][k],'B':refs['B'][k]} for k in refs['A'] if refs['A'][k]!=refs['B'][k]]
 metrics={};unknown=[];paired=[];numeric_mismatches=[]
 for r in ('A','B'):
  dd={d:metric([(val,new[k]['value']) for k,val in refs[r].items() if k[1]==d and binary(new[k]['value'])],77) for d in DIMS}
  for d in DIMS:
   dd[d].update(scope_reference_positive_N=sum(val==1 for k,val in refs[r].items() if k[1]==d),scope_reference_negative_N=sum(val==0 for k,val in refs[r].items() if k[1]==d),excluded_reference_positive_N=sum(val==1 and not binary(new[k]['value']) for k,val in refs[r].items() if k[1]==d),excluded_reference_negative_N=sum(val==0 and not binary(new[k]['value']) for k,val in refs[r].items() if k[1]==d))
  pool=metric([(val,new[k]['value']) for k,val in refs[r].items() if binary(new[k]['value'])],385);pool.update(scope_reference_positive_N=sum(refs[r].values()),scope_reference_negative_N=385-sum(refs[r].values()),excluded_reference_positive_N=sum(val==1 and not binary(new[k]['value']) for k,val in refs[r].items()),excluded_reference_negative_N=sum(val==0 and not binary(new[k]['value']) for k,val in refs[r].items()));complete=sum(all(binary(new[(rid,d)]['value']) for d in DIMS) for rid in {k[0] for k in refs[r]});metrics[r]={'per_dimension':dd,'pooled_label_slots':pool,'complete_five_dimension_records':complete,'complete_row_scope':77}
 for k in sorted(refs['A']):
  rid,d=k;x=new[k];p={'source_id':rid,'dimension':d,'reference_A':refs['A'][k],'reference_B':refs['B'][k],'v7_value':x['value'],'v7_status':x['status'],'basis_path':x['decision']['basis_path'],'reference_A_locator':locs['A'][k],'reference_B_locator':locs['B'][k]};paired.append(p)
  if x['value'] is None:unknown.append({**p,'current_original_text':text[rid],'recorded_decision':x['decision']})
  elif refs['A'][k]!=x['value'] or refs['B'][k]!=x['value']:numeric_mismatches.append(p)
 with (OUT/'reference77-paired-ledger.csv').open('x',encoding='utf8',newline='') as f:
  wr=csv.DictWriter(f,fieldnames=['source_id','dimension','reference_A','reference_B','v7_value','v7_status','basis_path']);wr.writeheader();wr.writerows({k:v for k,v in p.items() if k not in ('reference_A_locator','reference_B_locator')} for p in paired)
 save('reference77-metrics.json',{'identity':'exposed77 development diagnostics only','dimension_names':NAMES,'A_B_disagreements':disagree,'reference_A':metrics['A'],'reference_B':metrics['B'],'unknown_slots':unknown,'numeric_mismatches':numeric_mismatches,'null_never_converted_to_zero_or_one':True,'zero_denominator_returns_null_not_one':True,'F1_direct_count_formula':True,'formal_validation_complete':False})
 counts={d:{'old_positive':sum(x['rule_value']==1 for k,x in old.items() if k[1]==d),'new_positive':bydim[d]['1'],'old_negative':sum(x['rule_value']==0 for k,x in old.items() if k[1]==d),'new_negative':bydim[d]['0'],'old_null':sum(x['rule_value'] is None for k,x in old.items() if k[1]==d),'new_null':bydim[d]['None'],'changed_slots':sum(x['dimension']==d for x in changes)} for d in DIMS}
 compare={'record_N':4481,'slot_N':22405,'changed_slots':len(changes),'changed_records':len({x['source_id'] for x in changes}),'unchanged_slots':22405-len(changes),'per_dimension':counts,'value_transitions':[{'dimension':d,'old':a,'new':b,'N':n} for (d,a,b),n in sorted(transitions.items())],'actual_basis_path_transitions':[{'dimension':d,'old_basis_path':a,'new_basis_path':b,'N':n} for (d,a,b),n in sorted(basis_changes.items())],'change_explanations_only_recorded_rule_basis_and_source':True,'new_subjective_gold_labels_N':0}
 save('full4481-v5-v7-comparison.json',compare)
 protocol={'execution':{'path':str(RUN/'execution.json'),'status':ex['status'],'record_N':4481,'slot_N':22405,'technical_failure_dimension_N':0,'lawful_null_N':ex['lawful_null_N'],'one_adapter_attempt_per_record_ledger_N':4481},'independent_audit_code_prefrozen':True,'checked_binding_groups':checks,'v7_delivery_members_verified_N':len(delivery['files']),'input_versions':versions,'original_input_packet_versions':dict(original_packet_versions),'original_packet_to_common_JSONL_to_delivered_identity_verified_N':4481,'reference_reading_check':{'read_paths_N':len(ex['read_paths']),'reference_or_review_or_statistics_reads':bad_reads,'unapproved_reads':outside,'guard_actual_read_paths_checked':True,'classifier_reference_values_absent':True,'disclosed_development_preparation_not_blind':True,'audit_hook_starts_after_material_preflight':True,'preflight_static_material_allowlist_contains_no_reference':True,'constant_no_reference_read_flag_not_alone_proof':True,'interfaces_imported_before_driver_freeze_current_presealed_bytes_verified':True},'status_alias_independent_readback':{'request_N':request_N,'added_alias_N':added_N,'canonical_status_counts':dict(statuscounts),'original_order_fields_evidence_preserved':True,'substantive_resolution_not_inferred':True,'producer_resolved_evidence_sufficiency_not_independently_certified':True,'same_value_alias_can_remove_prior_missing_field_default_stop':True},'source_reading_receipts':{'source_log_record_N':4481,'read_receipt_N':read_N,'use_receipt_N':use_N,'views':dict(modalitycounts),'protocol_errors':log_errors,'image_reads_claimed_N':0,'all_used_views_have_read_receipts':True,'recorded_runtime_receipts_hashes_verified_not_semantic_correctness_or_human_read_certification':True},'formal_validation_complete':False,'human_validation_complete':False,'native_recovery35_process_compliance_claimed':False,'static_independent_review':register(OUT/'static-execution-check.md').name}
 save('execution-integrity-audit.json',protocol)
 report={'at_utc':datetime.now(timezone.utc).isoformat(),'identity':'independent post-completion integrity/count/arithmetic audit of a disclosed development-derived rule run','execution_integrity':protocol,'reference77_metrics':metrics,'reference77_unknown_slots':[{k:v for k,v in x.items() if k!='recorded_decision'} for x in unknown],'A_B_disagreements':disagree,'reference77_numeric_mismatches':numeric_mismatches,'full4481_comparison':compare,'formal_validation_complete':False,'population_confidence_interval_claimed':False,'native_recovery35_process_compliance_claimed':False}
 save('report.json',report)
 lines=['完整 v7 原包执行已完成，独立核验4481条、22405个维度槽位与封印。技术失败0；合法待定'+str(ex['lawful_null_N'])+'。输入 v15 原包、冻结手册、prompt、protocol 与旧v5逐字节版本相同；v7五源码与交付封印一致。','', '运行期实际阅读路径未出现真人A/B、统计或参照文件。读取hook不覆盖此前材料预检；静态预检清单没有参照路径，no_reference_read标志不能单独证明全过程。开发阶段曾公开的77条仍属开发诊断，不能据此称独立盲验证。','',f"status别名逐请求复核{request_N}项，其中补status字段{added_N}项；原字段、顺序、证据均不变，只复制已有合法status/dependency_status值，不推断解决状态。所有记录的来源日志、使用引文的阅读回执与原包身份均已核验。",'', 'A/B77的指标分别计算：','', '|维度|可比/77|κ|P|R|F1|Po|特异度|NPV|正类一致率|负类一致率|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
 for d in DIMS:
  m=metrics['A']['per_dimension'][d];lines.append('|'+NAMES[d]+'|'+str(m['comparable_N'])+'/77|'+'|'.join('NA' if m[k] is None else f'{m[k]:.6f}' for k in ('kappa','P','R','F1','Po','specificity','NPV','positive_agreement','negative_agreement'))+'|')
 lines+=['',f"A/B有{len(disagree)}个参照差异；各有{metrics['A']['pooled_label_slots']['comparable_N']}/385可比值。待定及其原文、实际理由见reference77-metrics.json；null未填0或1，零分母指标未写1。",'',f"相对旧v5 receipt recovery，全部4481条有{len(changes)}个维度槽位变化，涉及{compare['changed_records']}条。变化按实际basis_path、理由和原文引文列出，没有新增主观金标签或宣称每项变化正确。",'', '|维度|旧阳性|新阳性|旧待定|新待定|变化槽位|','|---|---:|---:|---:|---:|---:|']
 for d in DIMS:
  c=counts[d];lines.append(f"|{NAMES[d]}|{c['old_positive']}|{c['new_positive']}|{c['old_null']}|{c['new_null']}|{c['changed_slots']}|")
 lines+=['','完整变化清单见full4481-changes.csv及jsonl，详细分母/计数/转移见full4481-v5-v7-comparison.json。','', '本审计仅核完整执行身份、来源消费约束、计数及条件算术，不建立总体区间或正式验证结论，也不能保证补跑35的流程合规。旧源码、预测、统计和progress未改。']
 (OUT/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
 for b in inputs.values():assert bind(b['path'])==b
 save('input-bindings.json',{'at_utc':datetime.now(timezone.utc).isoformat(),'members':list(inputs.values()),'all_after_readback_unchanged':True})
 save('seal.json',{'at_utc':datetime.now(timezone.utc).isoformat(),'files':[bind(p) for p in sorted(OUT.iterdir()) if p.is_file()],'self_excluded':True})
 print(cj({'status':'audit_complete','report':bind(OUT/'report.json'),'seal':bind(OUT/'seal.json'),'comparison':compare,'reference77_comparable':metrics['A']['pooled_label_slots']['comparable_N']}))
if __name__=='__main__':main()
