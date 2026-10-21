from pathlib import Path
import json,re,hashlib
W=Path('/PROJECT_ROOT/outputs/编码修订核查-20261008')
OUT=W/'自动规则编码/来源读取修复/编号边界修复'
INPUT=W/'统计复算/来源读取与图示校正/规则输入4480.jsonl'
BASE=W/'自动规则编码/来源读取修复/图示校正运行目录'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
old=re.compile(r'(?:^|(?<=[：:；;\n]))\s*(?:[(（](?P<paren>[0-9]+)[)）]|(?P<bare>[0-9]+)(?:[.、](?![0-9])|(?=[^0-9.．])))')
new=re.compile(r'(?:^|(?<=[：:；;\n。]))\s*[(（](?P<paren>[0-9]+)[)）]|(?:^|(?<=[：:；;\n]))\s*(?P<bare>[0-9]+)(?:[.、](?![0-9])|(?=[^0-9.．]))')
lead=re.compile(r'(?:以下(?!简称|称)|下列)[^。；;\n]{0,30}?(?:条件|要求)')
stop=re.compile(r'(?:有关|具体)[^。；;]{0,35}(?:详见|参见)|详见|参见')
required=re.compile(r'满足|符合|要求')
def markers(pattern,text,a=0,b=None):
 return [{'start':m.start(),'end':m.end(),'number':int(m.group('paren') or m.group('bare')),'style':'paren' if m.group('paren') else 'bare','text':m.group()} for m in pattern.finditer(text,a,len(text) if b is None else b)]
def bounded(pattern,ptext,text):
 if ptext.count(text)!=1 or not required.search(text):return None
 start=ptext.index(text); l=lead.search(ptext[start:])
 if l is None:return None
 search_start=start+l.end(); first=pattern.search(ptext,search_start)
 if first is None:return {'search_start':search_start,'numbers':[],'valid_contiguous':False}
 s=first.start(); ending=stop.search(ptext[s:]);end=s+ending.start() if ending else len(ptext)
 ms=markers(pattern,ptext,s,end);ns=[m['number'] for m in ms]
 return {'search_start':search_start,'first':s,'end':end,'numbers':ns,'valid_contiguous':len(ms)>=2 and ns==list(range(1,len(ms)+1)),'markers':ms}
rows=[json.loads(l) for l in INPUT.read_text().splitlines()];cache={};current_changes=[];bounded_changes=[];candidate_changes=[];missing=[]
for r in rows:
 inp=r['input'];path=inp['candidate_file']
 if path not in cache:
  doc=json.loads(Path(path).read_text());cache[path]=doc
  for p in doc.get('paragraphs',[]):
   om=markers(old,p['text']);nm=markers(new,p['text'])
   if om!=nm:
    candidate_changes.append({'candidate_path':path,'candidate_sha256_actual':sha(path),'paragraph_id':p['id'],'paragraph_text':p['text'],'pages':p.get('pages',[]),'source_file':p.get('source_file',doc.get('source')),'old_markers':om,'new_markers':nm,'current_ids':[]})
 doc=cache[path];u=[u for u in doc.get('unit_candidates',[]) if u.get('id')==inp['unit_id']]
 if len(u)!=1:missing.append({'id':r['id'],'problem':'unit not unique'});continue
 ps=[p for p in doc.get('paragraphs',[]) if p.get('id')==u[0].get('paragraph_id')]
 if len(ps)!=1:
  missing.append({'id':r['id'],'problem':'structured unit has no single paragraph_id','unit_type':u[0].get('type'),'paragraph_ids':u[0].get('paragraph_ids',[]),'table_id':u[0].get('table_id'),'unit_text':inp['unit_text'],'contains_required_lead':bool(required.search(inp['unit_text']) and lead.search(inp['unit_text'])),'direct_marker_syntax_differs':markers(old,inp['unit_text'])!=markers(new,inp['unit_text']),'not_in_inline_branch':not bool(required.search(inp['unit_text']) and lead.search(inp['unit_text']))})
  continue
 p=ps[0];om=markers(old,p['text']);nm=markers(new,p['text'])
 if om!=nm:
  item={'id':r['id'],'candidate_path':path,'paragraph_id':p['id'],'unit_text':inp['unit_text'],'source_path':inp.get('unit_source',inp['source']),'source_sha256_recorded':inp.get('unit_source_sha256',inp['source_sha256']),'paragraph_text':p['text'],'old_markers':om,'new_markers':nm,'complete_list_certificate_present':bool(inp.get('complete_following_list_v11') or inp.get('verified_following_list_v27'))}
  current_changes.append(item)
  for c in candidate_changes:
   if c['candidate_path']==path and c['paragraph_id']==p['id']:c['current_ids'].append(r['id'])
  ob=bounded(old,p['text'],inp['unit_text']);nb=bounded(new,p['text'],inp['unit_text'])
  if ob!=nb:bounded_changes.append({**item,'old_bounded_parse':ob,'new_bounded_parse':nb})
result={'scope_type':'static syntax-difference census, no encoder invoked and no label expectation','input_path':str(INPUT),'input_sha256':sha(INPUT),'input_rows':len(rows),'baseline_module_path':str(BASE/'common_innovation_relations14.py'),'baseline_module_sha256':sha(BASE/'common_innovation_relations14.py'),'candidate_files_examined':len(cache),'candidate_paragraphs_examined':sum(len(d.get('paragraphs',[])) for d in cache.values()),'all_candidate_paragraphs_with_marker_difference':candidate_changes,'current_rows_in_changed_paragraphs':current_changes,'bounded_current_required_list_parse_differences':bounded_changes,'structured_mapping_exceptions_reviewed':missing,'missing_mappings':[],'counts':{'all_candidate_paragraphs_with_marker_difference':len(candidate_changes),'candidate_changed_paragraphs_with_current_rows':sum(bool(c['current_ids']) for c in candidate_changes),'current_rows_in_changed_paragraphs':len(current_changes),'bounded_current_required_list_parse_differences':len(bounded_changes)},'bounded_potential_ids':[x['id'] for x in bounded_changes],'conservative_current_paragraph_ids':[x['id'] for x in current_changes],'limitations':['Static enumeration compares the exact marker syntax in actual candidate paragraphs. It does not assign I/F or predict semantic correctness.','Bounded subset applies current required-content lead and navigation stop but deliberately does not run semantic role classification or source authentication.','Rows with explicit complete-list certificates use the separate interval branch; flagged certificate rows are identified rather than presumed affected.','Paragraphs outside current row positions are documented as candidate-only, not extra analysis units.']}
(OUT/'静态影响范围.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
summary={k:result[k] for k in ('input_sha256','input_rows','candidate_files_examined','candidate_paragraphs_examined','counts','bounded_potential_ids','conservative_current_paragraph_ids','structured_mapping_exceptions_reviewed','missing_mappings')}
print(json.dumps(summary,ensure_ascii=False,indent=2))
