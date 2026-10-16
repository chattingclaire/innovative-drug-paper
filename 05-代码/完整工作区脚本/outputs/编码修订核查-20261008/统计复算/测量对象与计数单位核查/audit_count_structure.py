"""Structural census only. No coding modules, labels, models or classifiers."""
from pathlib import Path
from collections import Counter,defaultdict
from itertools import combinations
import json,hashlib,unicodedata,sys
sys.dont_write_bytecode=True
b=Path(__file__).resolve().parent;w=b.parents[1]
paths={'frame':w/'人工参照复核/全量目标框验证准备01/source_only_frame_all4481.jsonl','source_material':w/'LLM编码/统一判据编码准备/共用纯来源材料04/source_only_with_scope04.jsonl','rule_input':w/'LLM编码/统一判据编码准备/共用纯来源材料04/rule_inputs_material04.jsonl'}
def sha_bytes(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def canon(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def layout(s):return ''.join(c for c in unicodedata.normalize('NFKC',s) if not c.isspace())
input_sha={k:sha_bytes(p) for k,p in paths.items()};data={k:[json.loads(l) for l in p.read_text().splitlines()] for k,p in paths.items()}
frame=data['frame'];rules={r['id']:r for r in data['rule_input']};material={r['id']:r for r in data['source_material']};F={r['id']:r for r in frame}
file_hash={};documents={};paragraphs={};candidate_units={};bindings={};binding_issues=[]
def hash_actual(path,expected):
 if not path:return None
 if path not in file_hash:
  try:file_hash[path]={'actual_sha256':sha_bytes(path),'readable':True}
  except Exception as e:file_hash[path]={'actual_sha256':None,'readable':False,'error':str(e)}
 return file_hash[path]['actual_sha256']==expected
for r in frame:
 sp=r['source_position'];inp=rules.get(r['id'],{}).get('input');src=material.get(r['id']);problems=[]
 if inp is None or src is None:problems.append('missing rule/source-material id')
 elif not (r['unit_text']==inp['unit_text']==src['text']):problems.append('frame rule material current-text mismatch')
 cp=sp['candidate_file'];expected=sp['candidate_sha256_recorded']
 if not hash_actual(cp,expected):problems.append('candidate bytes SHA mismatch/unavailable')
 if cp not in documents:
  try:
   documents[cp]=json.loads(Path(cp).read_text());paragraphs[cp]={p['id']:p for p in documents[cp].get('paragraphs',[])};candidate_units[cp]={u['id']:u for u in documents[cp].get('unit_candidates',[])}
  except Exception as e:documents[cp]={};paragraphs[cp]={};candidate_units[cp]={};problems.append('candidate JSON unreadable')
 u=candidate_units[cp].get(sp['unit_id']);p=paragraphs[cp].get((u or {}).get('paragraph_id'))
 if not u:problems.append('candidate unit id absent')
 elif u.get('text')!=r['unit_text']:problems.append('candidate unit text differs')
 structured=bool(u and (u.get('type') in ['example_table_row','blank_example_table'] or u.get('table_id') or u.get('cells')))
 if not p and not structured:problems.append('candidate unit paragraph absent')
 actual_source=sp.get('unit_source_file') or sp['source_file'];source_sha=sp.get('unit_source_sha256_recorded') or sp['source_sha256_recorded']
 if not hash_actual(actual_source,source_sha):problems.append('current source bytes SHA mismatch/unavailable')
 interval=None
 if p and p['text'].count(r['unit_text'])==1:
  start=p['text'].index(r['unit_text']);interval=[start,start+len(r['unit_text'])]
 elif p and not structured:problems.append('current unit exact source-paragraph occurrence not unique')
 bindings[r['id']]={'candidate_file':cp,'candidate_sha256':expected,'paragraph_id':(u or {}).get('paragraph_id'),'unit_id':sp['unit_id'],'source_path':actual_source,'source_sha256':source_sha,'unique_raw_paragraph_interval':interval,'unit_type':(u or {}).get('type','sentence_or_text'),'structured_table_unit':structured,'paragraph_ids':(u or {}).get('paragraph_ids') or ([(u or {}).get('paragraph_id')] if (u or {}).get('paragraph_id') else []),'span_census_applicable':not structured,'issues':problems}
 if problems:binding_issues.append({'id':r['id'],'issues':problems})
# Enumerate only named existing list certificates, not colon/keyword guesses.
fields=['complete_following_list_v11','verified_following_list_v27','source_local_list_family_v14','source_local_list_family_v13']
raw_certificates=[]
def collect_named_certificates(value,path,owner,inp):
 if isinstance(value,dict):
  for key,child in value.items():
   if key in fields and isinstance(child,dict):raw_certificates.append((owner,path+'.'+key,child,inp))
   collect_named_certificates(child,path+'.'+key,owner,inp)
 elif isinstance(value,list):
  for index,child in enumerate(value):collect_named_certificates(child,path+'['+str(index)+']',owner,inp)
for row in data['rule_input']:collect_named_certificates(row['input'],'input',row['id'],row['input'])
# Deduplicate the same interval across fields/owners. Keep all owner roles.
families={}
for owner,field,cert,inp in raw_certificates:
 contexts=cert.get('contexts') or [];cp=cert.get('candidate_path') or (contexts[0].get('candidate_path') if contexts else None) or inp['candidate_file'];boundary=cert.get('structure_boundary') or {}
 source_sha=cert.get('source_sha256') or inp.get('unit_source_sha256') or inp.get('source_sha256');nextb=boundary.get('next_boundary') or boundary.get('next_structure') or {};nxt_id=boundary.get('next_paragraph_id') or nextb.get('paragraph_id') or nextb.get('id');nxt_text=boundary.get('next_paragraph_text') or nextb.get('text')
 signature=canon({'candidate_file':cp,'source_sha256':source_sha,'contexts':[(c.get('paragraph_id'),digest(c.get('text',''))) for c in contexts],'first':boundary.get('first_paragraph'),'last':boundary.get('last_paragraph'),'next':nxt_id,'next_text':nxt_text})
 key='LIST-'+digest(signature)[:20]
 if key not in families:families[key]={'family_id':key,'candidate_file':cp,'source_sha256':source_sha,'contexts':contexts,'structure_boundary':boundary,'owners':[],'fields':[],'validation_checks':[]}
 fam=families[key];fam['owners'].append({'id':owner,'in_target_frame':owner in F,'certificate_field':field,'owner_unit_text':inp['unit_text'],'owner_paragraph_id':bindings.get(owner,{}).get('paragraph_id'),'declared_actual_parent_predicate':cert.get('actual_parent_predicate')});fam['fields'].append(field.split('.')[-1])
 cp_doc=documents.get(cp)
 if cp_doc is None:
  try:cp_doc=json.loads(Path(cp).read_text());documents[cp]=cp_doc;paragraphs[cp]={p['id']:p for p in cp_doc.get('paragraphs',[])}
  except Exception:cp_doc={};paragraphs[cp]={}
 actual=cp_doc.get('paragraphs',[]);idx={p['id']:i for i,p in enumerate(actual)};pids=[c.get('paragraph_id') for c in contexts]
 context_equal=bool(contexts) and all(c.get('paragraph_id') in idx and actual[idx[c['paragraph_id']]]['text']==c.get('text') for c in contexts)
 positions=[idx[p] for p in pids if p in idx];contiguous=context_equal and positions==list(range(positions[0],positions[0]+len(positions)))
 next_equal=nxt_id in idx and actual[idx[nxt_id]]['text']==nxt_text and bool(positions) and idx[nxt_id]==positions[-1]+1
 source_context_checks=[bool(hash_actual(c.get('source_path') or cert.get('source_path') or inp.get('unit_source') or inp.get('source'),c.get('source_sha256') or source_sha)) for c in contexts]
 candidate_context_checks=[bool(hash_actual(c.get('candidate_path') or cp,c.get('candidate_sha256') or cert.get('candidate_sha256') or inp['candidate_sha256'])) for c in contexts]
 context_hash=cert.get('contexts_sha256');hash_equal=(digest(json.dumps(contexts,ensure_ascii=False,sort_keys=True))==context_hash) if context_hash else None
 declared_verified=(cert.get('source_files_hash_verified') is True or (cert.get('verification') or {}).get('verified') is True or (cert.get('actual_parent_predicate',{}).get('verification') or {}).get('verified') is True)
 current_sha=cert.get('original_unit_sha256') or cert.get('current_unit_sha256');current_sha_equal=(current_sha==digest(inp['unit_text'])) if current_sha else None
 fam['validation_checks'].append({'owner_id':owner,'field':field,'complete_interval_declared':boundary.get('all_paragraphs_in_interval_included') is True,'existing_source_certification_declared':declared_verified,'contexts_match_candidate_paragraphs':context_equal,'paragraph_interval_contiguous':contiguous,'next_boundary_matches_actual_candidate':next_equal,'actual_source_bytes_sha_matches_all_contexts':all(source_context_checks),'candidate_bytes_sha_matches_all_contexts':all(candidate_context_checks),'contexts_serialization_sha_matches':hash_equal,'current_unit_sha_matches':current_sha_equal})
# Join family paragraphs to independently counted target-frame rows.
by_candidate_paragraph=defaultdict(list)
for r in frame:
 bind=bindings[r['id']]
 for pid in bind['paragraph_ids']:by_candidate_paragraph[(bind['candidate_file'],pid)].append(r)
for fam in families.values():
 fam['fields']=sorted(set(fam['fields']));fam['owner_ids_in_target_frame']=sorted({o['id'] for o in fam['owners'] if o['in_target_frame']});fam['owner_ids_all_source04']=sorted({o['id'] for o in fam['owners']});fam['owner_metadata_occurrences']=len(fam['owners'])
 parent_ids={o['declared_actual_parent_predicate'].get('paragraph_id') for o in fam['owners'] if isinstance(o['declared_actual_parent_predicate'],dict)}
 if not parent_ids and fam['contexts']:parent_ids={fam['contexts'][0].get('paragraph_id')}
 fam['parent_paragraph_ids_from_metadata']=sorted(p for p in parent_ids if p)
 for owner in fam['owners']:
  pid=owner['owner_paragraph_id']
  owner['owner_structural_role']='parent_paragraph_unit' if pid in parent_ids else 'member_paragraph_unit' if pid in {c.get('paragraph_id') for c in fam['contexts']} else 'outside_interval_or_not_in_target'
 fam['parent_paragraph_owner_ids_in_target_frame']=sorted({o['id'] for o in fam['owners'] if o['in_target_frame'] and o['owner_structural_role']=='parent_paragraph_unit'})
 fam['member_paragraph_owner_ids_in_target_frame']=sorted({o['id'] for o in fam['owners'] if o['in_target_frame'] and o['owner_structural_role']=='member_paragraph_unit'})

 fam['paragraph_to_independent_rows']=[];allrows=[];memberrows=[]
 for c in fam['contexts']:
  rows=by_candidate_paragraph.get((fam['candidate_file'],c.get('paragraph_id')),[])
  entries=[{'id':r['id'],'unit_id':r['source_position']['unit_id'],'unit_text':r['unit_text'],'text_equals_complete_context_paragraph':r['unit_text']==c.get('text'),'unique_raw_paragraph_interval':bindings[r['id']]['unique_raw_paragraph_interval']} for r in rows]
  fam['paragraph_to_independent_rows'].append({'paragraph_id':c.get('paragraph_id'),'source_context_text':c.get('text'),'pages':c.get('pages',[]),'source_lines':c.get('source_lines',[]),'metadata_parent_paragraph':c.get('paragraph_id') in parent_ids,'independent_target_rows':entries})
  allrows.extend(r['id'] for r in rows)
  if c.get('paragraph_id') not in parent_ids:memberrows.extend(r['id'] for r in rows)
 fam['independent_interval_row_ids']=sorted(set(allrows));fam['independent_member_row_ids']=sorted(set(memberrows))
 fam['independent_parent_paragraph_row_ids']=sorted({r['id'] for pid in parent_ids for r in by_candidate_paragraph.get((fam['candidate_file'],pid),[])})
 whole=layout(''.join(c.get('text','') for c in fam['contexts']));fam['standalone_whole_interval_row_ids']=[r['id'] for r in frame if bindings[r['id']]['candidate_file']==fam['candidate_file'] and layout(r['unit_text'])==whole]
 fam['structure_check_passed']=any(all(c.get(k) is True for k in ['complete_interval_declared','existing_source_certification_declared','contexts_match_candidate_paragraphs','paragraph_interval_contiguous','next_boundary_matches_actual_candidate','actual_source_bytes_sha_matches_all_contexts','candidate_bytes_sha_matches_all_contexts']) and c.get('contexts_serialization_sha_matches') is not False and c.get('current_unit_sha_matches') is not False for c in fam['validation_checks'])
# Exact repeated text within the same candidate document (not semantic repeats).
exact=defaultdict(list);existing_normalized=defaultdict(list)
for r in frame:
 cp=bindings[r['id']]['candidate_file'];exact[(cp,r['unit_text'])].append(r['id']);existing_normalized[(cp,r['normalized_text_family']['normalized_text_sha256'])].append(r['id'])
exact_groups=[{'candidate_file':cp,'text':text,'ids':ids,'paragraph_ids':[bindings[i]['paragraph_id'] for i in ids]} for (cp,text),ids in exact.items() if len(ids)>1]
normalized_groups=[{'candidate_file':cp,'existing_normalized_text_sha256':s,'ids':ids} for (cp,s),ids in existing_normalized.items() if len(ids)>1]
# Same-paragraph literal interval overlap/containment, separately from context reuse.
overlaps=[]
for (cp,pid),rows in by_candidate_paragraph.items():
 for a,c in combinations(rows,2):
  ia=bindings[a['id']]['unique_raw_paragraph_interval'];ic=bindings[c['id']]['unique_raw_paragraph_interval']
  if not ia or not ic or not bindings[a['id']]['span_census_applicable'] or not bindings[c['id']]['span_census_applicable']:continue
  if max(ia[0],ic[0])<min(ia[1],ic[1]):
   relation='equal_span' if ia==ic else 'proper_containment' if ((ia[0]<=ic[0] and ia[1]>=ic[1]) or (ic[0]<=ia[0] and ic[1]>=ia[1])) else 'partial_overlap'
   overlaps.append({'candidate_file':cp,'paragraph_id':pid,'id_a':a['id'],'id_b':c['id'],'span_a':ia,'span_b':ic,'relation':relation,'text_a':a['unit_text'],'text_b':c['unit_text']})
focus={}
for id in ['RECODE25-03424','RECODE25-00087']:
 families_focus=[f for f in families.values() if id in f['owner_ids_all_source04']]
 contexts=material[id]['contexts'];repeated=defaultdict(list)
 for c in contexts:
  pid=c.get('structure',{}).get('paragraph_id')
  if pid:repeated[(c.get('source_document'),pid,c.get('text',''))].append({'context_id':c.get('context_id'),'kind':c.get('kind'),'structure':c.get('structure')})
 focus[id]={'frame_row':F[id],'binding':bindings[id],'families':families_focus,'source_material_context_count':len(contexts),'same_source_paragraph_context_repetitions':[{'source_document':s,'paragraph_id':pid,'text':txt,'count':len(v),'contexts':v} for (s,pid,txt),v in repeated.items() if len(v)>1]}
complete=[f for f in families.values() if any(k in f['fields'] for k in ['complete_following_list_v11','verified_following_list_v27'])];target_complete=[f for f in complete if f['owner_ids_in_target_frame']];target_families=[f for f in families.values() if f['owner_ids_in_target_frame']]
validated_complete=[f for f in target_complete if f['structure_check_passed']]
physical_source_repeats=defaultdict(list)
for r in frame:
 bind=bindings[r['id']];physical_source_repeats[(bind['source_path'],bind['source_sha256'],r['unit_text'])].append(r['id'])
physical_source_repeat_groups=[{'source_path':path,'source_sha256':s,'text':text,'ids':ids} for (path,s,text),ids in physical_source_repeats.items() if len(ids)>1]
summary={'input_sha256':input_sha,'input_rows':{k:len(v) for k,v in data.items()},'target_department_rows':dict(Counter(r['analysis_group'] for r in frame)),'all_frame_ids_unique':len(F)==len(frame),'frame_binding_issues_count':len(binding_issues),'ordinary_single_paragraph_span_units':sum(v['span_census_applicable'] and v['unique_raw_paragraph_interval'] is not None for v in bindings.values()),'structured_units_excluded_from_literal_span_overlap_census':sum(v['structured_table_unit'] for v in bindings.values()),'candidate_document_count':len({r['source_position']['candidate_file'] for r in frame}),'existing_list_certificate_fields_inspected':fields,'raw_certificate_occurrences_source04_including_shared_duplicates':len(raw_certificates),'deduplicated_existing_list_intervals_all_source04':len(families),'deduplicated_existing_list_intervals_with_target_owner':len(target_families),'complete_following_intervals_with_target_owner':len(target_complete),'complete_following_target_owners_unique':len({id for f in target_complete for id in f['owner_ids_in_target_frame']}),'complete_following_target_intervals_structure_check_passed':sum(f['structure_check_passed'] for f in target_complete),'validated_complete_parent_paragraph_owner_ids_unique':len({id for f in validated_complete for id in f['parent_paragraph_owner_ids_in_target_frame']}),'validated_complete_member_paragraph_owner_ids_unique':len({id for f in validated_complete for id in f['member_paragraph_owner_ids_in_target_frame']}),'validated_complete_member_rows_union':len({id for f in validated_complete for id in f['independent_member_row_ids']}),'validated_complete_intervals_with_independent_parent_and_member_rows':sum(bool(f['independent_parent_paragraph_row_ids']) and bool(f['independent_member_row_ids']) for f in validated_complete),'independent_parent_paragraph_rows_union':len({id for f in validated_complete for id in f['independent_parent_paragraph_row_ids']}),'validated_complete_intervals_with_parent_owner_and_independent_members':sum(bool(f['parent_paragraph_owner_ids_in_target_frame']) and bool(f['independent_member_row_ids']) for f in validated_complete),'complete_following_target_intervals_with_independent_members':sum(bool(f['independent_member_row_ids']) for f in target_complete),'complete_following_target_member_rows_union':len({id for f in target_complete for id in f['independent_member_row_ids']}),'standalone_whole_list_intervals_in_target_frame':sum(bool(f['standalone_whole_interval_row_ids']) for f in target_complete),'exact_text_repeat_families_within_physical_source':len(physical_source_repeat_groups),'exact_text_repeat_additional_rows_within_physical_source':sum(len(g['ids'])-1 for g in physical_source_repeat_groups),'unit_types':dict(Counter(v['unit_type'] for v in bindings.values())),'exact_text_repeat_families_within_candidate_document':len(exact_groups),'exact_text_repeat_rows_within_candidate_document':sum(len(g['ids']) for g in exact_groups),'exact_text_repeat_additional_rows_beyond_one_per_family':sum(len(g['ids'])-1 for g in exact_groups),'existing_normalized_repeat_families_within_candidate_document':len(normalized_groups),'same_paragraph_literal_overlap_pair_count':len(overlaps),'same_paragraph_literal_overlap_pair_types':dict(Counter(o['relation'] for o in overlaps)),'labels_or_semantic_encoder_used':False,'new_source_pdf_page_or_visual_authentication_performed':False,'limits':['enumeration is limited to four existing certificate fields; lists lacking these fields are not inferred','source and candidate byte hashes plus candidate paragraph/boundary structure are verified; prior literal/visual page review is not independently repeated','role labels parent/member are taken from certificate metadata, not assigned by an attention-dimension classifier','same attention counted twice remains a research decision; structural reuse alone is not a proven label double-count','whole interval matching uses NFKC and whitespace removal only; exact repeats use unnormalized current text; normalized repeat families reuse frame metadata','paragraph containment census only includes unique literal occurrences in ordinary text; structured table units are separately recorded and not forced into single-paragraph spans']}
assert input_sha=={k:sha_bytes(p) for k,p in paths.items()},'input files changed during read-only audit'
(b/'structure_census_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
(b/'authenticated_list_interval_mappings.json').write_text(json.dumps({'families':list(families.values()),'raw_certificate_occurrences':len(raw_certificates)},ensure_ascii=False,indent=2))
(b/'focus_actual_structure.json').write_text(json.dumps(focus,ensure_ascii=False,indent=2))
(b/'literal_duplicate_and_overlap_mappings.json').write_text(json.dumps({'exact_same_document_text_families':exact_groups,'exact_same_physical_source_text_families':physical_source_repeat_groups,'existing_normalized_same_document_text_families':normalized_groups,'same_paragraph_literal_overlaps':overlaps,'binding_issues':binding_issues,'bindings':bindings,'actual_file_sha_records':file_hash},ensure_ascii=False,indent=2))
print(json.dumps(summary,ensure_ascii=False,indent=2))
for id,f in focus.items():
 for fam in f['families']:print('FOCUS',id,fam['family_id'],fam['fields'],'independent_interval_rows',len(fam['independent_interval_row_ids']),'independent_members',len(fam['independent_member_row_ids']),'structure_pass',fam['structure_check_passed'],'whole_interval_rows',fam['standalone_whole_interval_row_ids'])
print('FOCUS_CONTEXT_REPETITIONS',[(id,[(r['paragraph_id'],r['count']) for r in v['same_source_paragraph_context_repetitions']]) for id,v in focus.items()])
