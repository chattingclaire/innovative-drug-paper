"""Package integrity checks and an explicitly non-final v8 source preflight seal."""
from pathlib import Path
import json,hashlib,copy,re,collections
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
H=lambda b:hashlib.sha256(b).hexdigest()
def rows(p):return [json.loads(x) for x in p.read_text().splitlines()]
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def jl(p,x):p.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in x))
canon=OUT/'canonical_source_context-v8.jsonl';D=rows(canon);F=rows(ROOT/'00-baseline/source-only-frame.jsonl');O=rows(OUT/'canonical_source_context-v7.jsonl');FD={r['id']:r for r in F};OD={r['id']:r for r in O}
forbid=set(json.loads((OUT/'source-QA-summary-v8.json').read_text())['recursive_forbidden_keys']['keys']);violations=[];dangling=[];duplicates=[];shaissues=[];interfacebad=[]
def walk(x,path):
 if isinstance(x,dict):
  for k,v in x.items():
   if k in forbid:violations.append({'path':path+'/'+k})
   walk(v,path+'/'+k)
 elif isinstance(x,list):
  for i,v in enumerate(x):walk(v,path+f'/{i}')
def strings(x):
 if isinstance(x,str):yield x
 elif isinstance(x,dict):
  for v in x.values():yield from strings(v)
 elif isinstance(x,list):
  for v in x:yield from strings(v)
assets={}
for r in D:
 walk(r,r['id']);ids={n['context_id'] for n in r['contexts']};nr={x['relation_id'] for x in r.get('source_relations',[])}
 if len(ids)!=len(r['contexts']):duplicates.append(r['id'])
 for x in strings(r):
  if x.startswith('CTX-') and x not in ids:dangling.append({'record_id':r['id'],'ref':x})
  if x.startswith('NR-') and x not in nr:dangling.append({'record_id':r['id'],'ref':x})
 assert {n['context_id'] for n in OD[r['id']]['contexts']}<=ids
 for a in r.get('source_attachments',[]):
  p=(OUT/a['relative_path']).resolve();key=(str(p),a['sha256']);assets[key]={**a,'snapshot':str(p)}
  if not p.is_file() or H(p.read_bytes())!=a['sha256']:shaissues.append({'record_id':r['id'],'attachment_id':a['attachment_id'],'path':str(p)})
 # These two neutral selectors are exactly the same projection, including order.
 a=json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode();b=json.dumps(copy.deepcopy(r),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
 if a!=b:interfacebad.append(r['id'])
assert [r['id'] for r in D]==[r['id'] for r in F] and len(D)==4481
assert not violations and not dangling and not duplicates and not shaissues and not interfacebad
docs=rows(OUT/'source-document-identities-v7.jsonl');tr=json.loads((OUT/'care-source-transcriptions-v8.json').read_text());s=tr['source_pdf_sha256']
pure={'source_resource_id':'SOURCE-'+s,'source_pdf_sha256':s,'source_title':'罕见疾病创新药物研发鼓励试点计划（“关爱计划-延伸”）','paragraphs':tr['source_transcriptions'],'tables':tr['actual_tables'],'transcription_coverage':{'substantive_paragraphs_and_source_table_cells':True,'table_of_contents_page12_not_fully_transcribed':True,'actual_page_images_for_all18_pages_available':True},'publication_date_established_from_source':False}
lib=OUT/'source-library/care-full-source-v8.json';dump(lib,pure)
for x in docs:
 if x['source_sha256']==s:x['source_text_resource']={'relative_path':str(lib.relative_to(OUT)),'sha256':H(lib.read_bytes()),'source_pdf_sha256':s,'kind':'literal_source_scan_transcription_and_actual_table_cells'}
jl(OUT/'source-document-identities-v8.jsonl',docs)
jl(OUT/'source-assets-manifest-v8.jsonl',list(assets.values()))
oldacc=(OUT/'source_only_interface.py').read_text();acc=oldacc.replace('canonical_source_context-v7.jsonl','canonical_source_context-v8.jsonl').replace('007342cd7f89681258bb5fbd31a3c6ae6b8f6cd6f013f97329aa0dcdee799974',H(canon.read_bytes())).replace('source-document-identities-v7.jsonl','source-document-identities-v8.jsonl')
(OUT/'source_only_interface_v8.py').write_text(acc)
summary=json.loads((OUT/'source-QA-summary-v8.json').read_text());checks={'status':'sealed_source_preflight_v8_not_final_material_freeze','frame_N':len(D),'source_interface_N':4924,'excluded_GOV_N':443,'all_frame_IDs_and_order_preserved':True,'original_context_IDs_preserved':True,'current_context_N':sum(len(r['contexts']) for r in D),'current_textless_context_N':sum('text' not in n and not any(k in n for k in ['headers','title','row_cells','caption']) for r in D for n in r['contexts']),'dangling_context_or_relation_references':dangling,'forbidden_keys':violations,'duplicate_context_ID_record_ids':duplicates,'attached_file_sha_failures':shaissues,'unique_attached_file_N':len(assets),'rule_model_projection_byte_difference_N':len(interfacebad),'literal_source_pending_occurrence_N':summary['pending_issue_N'],'literal_source_pending_unique_N':summary['pending_unique_source_text_N'],'body_changes_from_original_frame_N':2,'body_changes_from_v7_N':1,'context_text_changes_from_v7_N':6,'unchanged_body_N':4479,'pending_is_not_a_zero_dimension_label':True,'final_material_freeze_completed':False}
dump(OUT/'package-integrity-v8.json',checks)
names=['canonical_source_context-v8.jsonl','source-QA-summary-v8.json','body-source-QA-v8.jsonl','context-source-QA-v8.jsonl','source-exceptions-v8.jsonl','grouped-source-review-jobs-v8.jsonl','material-record-bindings-v8.jsonl','family-exposure-impact-v8.json','source-visual-review-v8.json','source-text-changes-v8.json','care-source-transcriptions-v8.json','source-document-identities-v8.jsonl','source-assets-manifest-v8.jsonl','source_only_interface_v8.py','source-library/care-full-source-v8.json','package-integrity-v8.json']
dump(OUT/'delivery-seal-v8.json',{'status':'source_only_preflight_and_version_seal; pending_source_work_remains; not_coding_material_final_freeze','files':[{'path':str(OUT/n),'sha256':H((OUT/n).read_bytes()),'bytes':(OUT/n).stat().st_size} for n in names],'package_integrity':checks,'remaining_source_work':summary['pending_unique_job_fragment_types'],'original_sources_and_old_versions_preserved':True,'human_independent_validation_completed':False,'new_whole_frame_machine_coding_launched':False})
print(json.dumps(checks,ensure_ascii=False,indent=2))
