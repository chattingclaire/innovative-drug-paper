from pathlib import Path
from collections import Counter,defaultdict
import json,hashlib,subprocess,unicodedata,re
B=Path(__file__).resolve().parent;D=B.parent
W=D.parents[3]
MANUAL=W/'定义溯源核查/测量与计数统一/共用编码手册.md'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def source_path(r):return r['source_position']['unit_source_file'] or r['source_position']['source_file']
def norm(s):return re.sub(r'\s+','',unicodedata.normalize('NFKC',s)).translate(str.maketrans({'，':',','。':'.','；':';','：':':'}))
def read_source(p):
 p=Path(p);ext=p.suffix.lower()
 if ext in {'.txt','.json'}:return p.read_text(),'UTF8_text'
 if ext=='.pdf':return subprocess.run(['pdftotext','-layout','-enc','UTF-8',str(p),'-'],check=True,capture_output=True,text=True).stdout,'pdftotext_layout'
 if ext=='.doc':return subprocess.run(['textutil','-convert','txt','-stdout',str(p)],check=True,capture_output=True,text=True).stdout,'textutil_doc_to_text'
 return None,'unsupported_extension'
counts={};representatives=[];protected={str(MANUAL):sha(MANUAL)};source_cache={}
for dim in ('I','F'):
 path=D/f'{dim}_二元分歧.jsonl';protected[str(path)]=sha(path)
 rows=[json.loads(l) for l in path.read_text().splitlines()]
 assert len({r['id'] for r in rows})==len(rows)
 groups=defaultdict(list)
 for r in rows:groups[(r['group'],r['rule_label'],r['llm_label'])].append(r)
 bydoc=defaultdict(list)
 for r in rows:bydoc[(r['group'],source_path(r))].append(r)
 clusterlist=[]
 for (group,source),rs in sorted(bydoc.items(),key=lambda kv:(-len(kv[1]),kv[0])):
  clusterlist.append({'department':group,'source_component_path':source,'n_disagreements':len(rs),'directions':[{'rule':a,'llm':b,'n':c} for (a,b),c in sorted(Counter((r['rule_label'],r['llm_label']) for r in rs).items())],'ids':[r['id'] for r in sorted(rs,key=lambda r:r['id'])]})
 selected=[];useddocs=set();selection_trace=[]
 for stratum,rs in sorted(groups.items()):
  docs=defaultdict(list)
  for r in rs:docs[source_path(r)].append(r)
  top=sorted(docs.items(),key=lambda kv:(-len(kv[1]),kv[0]))[0]
  pick=min(top[1],key=lambda r:r['id']);selected.append(pick);useddocs.add(source_path(pick));selection_trace.append({'selection':'one per department-direction stratum','stratum':list(stratum),'source_cluster_count':len(top[1]),'id':pick['id']})
 while len(selected)<min(6,len(rows)):
  candidates=[c for c in clusterlist if c['source_component_path'] not in useddocs]
  if candidates:
   c=candidates[0];rs=bydoc[(c['department'],c['source_component_path'])];pick=min((r for r in rs if r['id'] not in {s['id'] for s in selected}),key=lambda r:r['id']);useddocs.add(source_path(pick));count=c['n_disagreements']
  else:
   pick=min((r for r in rows if r['id'] not in {s['id'] for s in selected}),key=lambda r:r['id']);count=None
  selected.append(pick);selection_trace.append({'selection':'largest remaining unrepresented document cluster','id':pick['id'],'source_cluster_count':count})
 counts[dim]={'n':len(rows),'department_direction_counts':[{'department':s[0],'rule':s[1],'llm':s[2],'n':len(rs)} for s,rs in sorted(groups.items())],'source_component_cluster_count':len(bydoc),'all_source_document_counts':clusterlist,'selection_trace':selection_trace,'selected_ids':[r['id'] for r in selected]}
 for r in selected:
  inp=r['rule_source_input_complete']['input'];position=r['source_position'];source=source_path(r);candidate=position['candidate_file'];srcsha=sha(source);csha=sha(candidate)
  protected[source]=srcsha;protected[candidate]=csha
  if source not in source_cache:
   try:source_cache[source]=read_source(source)
   except Exception as e:source_cache[source]=(None,'failed:'+type(e).__name__+':'+str(e))
  raw,method=source_cache[source]
  candidate_doc=json.loads(Path(candidate).read_text());unit=next(x for x in candidate_doc['unit_candidates'] if x['id']==inp['unit_id'])
  rr=r['rule_output_complete']['result'];llm=r['llm_output_complete'];dimension=r['dimension']
  contexts=inp.get('paragraph_context',[])
  actual_source_current_literal=bool(raw is not None and norm(r['text']) in norm(raw))
  if raw is not None and Path(source).suffix.lower()=='.json':
   parsed=json.loads(raw)
   def vals(x):
    if isinstance(x,dict):
     for v in x.values():yield from vals(v)
    elif isinstance(x,list):
     for v in x:yield from vals(v)
    elif isinstance(x,str):yield x
   strings=list(vals(parsed));actual_source_current_literal=any(norm(r['text'])==norm(t) for t in strings)
   if unit.get('cells'):actual_source_current_literal=all(any(norm(cell)==norm(t) for t in strings) for cell in unit['cells'] if cell)
  source_read_details={}
  if not actual_source_current_literal and Path(source).suffix.lower()=='.pdf':
   from pypdf import PdfReader
   pdf=PdfReader(source);physical_pages=unit.get('pages',[]);pieces=[]
   for page_no in physical_pages:
    value=pdf.pages[page_no-1].extract_text() or ''
    value=re.sub(r'(?m)^\s*[—–-]?\s*[0-9]+\s*[—–-]?\s*$','',value)
    pieces.append(value)
   actual_source_current_literal=norm(r['text']) in norm(''.join(pieces))
   source_read_details={'physical_pages':physical_pages,'fallback':'pypdf bounded actual pages; numeric-only folio lines omitted','not_a_new_runtime_certificate':True}
   if actual_source_current_literal:method+=' + pypdf_bounded_pages'
  material={'dimension':dimension,'id':r['id'],'department':r['group'],'direction':{'rule':r['rule_label'],'llm':r['llm_label']},'current_text':r['text'],'source_position':position,'source_actual_sha256':srcsha,'source_sha_matches_recorded':srcsha==position['unit_source_sha256_recorded'],'candidate_actual_sha256':csha,'candidate_sha_matches_recorded':csha==position['candidate_sha256_recorded'],'actual_current_source_read_method':method,'source_read_details':source_read_details,'actual_current_literal_found_in_source_read':actual_source_current_literal,'current_candidate_unit':unit,'source_paragraph_context':contexts,'llm_contexts_actually_supplied':r['llm_source_input_complete'].get('contexts',[]),'rule_dimension_evidence':[x for x in rr.get('evidence',[]) if x.get('dimension')==dimension],'rule_dimension_suppressions':[x for x in rr.get('suppressions',[]) if dimension in x.get('dimensions',[]) or x.get('dimension')==dimension],'rule_label_zero_has_no_positive_reason':r['rule_label']==0,'llm_dimension_reason':llm.get('dimension_reasons',{}).get(dimension),'llm_dimension_evidence':[x for x in llm.get('evidence',[]) if x.get('dimension')==dimension]}
  representatives.append(material)
summary={'scope':'read-only diagnostic of first actual rule versus LLM differences; not independent human validation','manual_path':str(MANUAL),'manual_sha256':sha(MANUAL),'comparison_input_sha256':{d:sha(D/f'{d}_二元分歧.jsonl') for d in ('I','F')},'counting_unit':'one difference row per dimension; document is actual unit source component, not master container source','fixed_selection_rule':['For each existing (department,rule label,LLM label) stratum, choose its largest source-component document cluster; tie by absolute source path, then choose smallest ID.','Fill to at most six per dimension from largest as-yet unrepresented document clusters; tie by absolute source path, then smallest unused ID.','Selection uses counts and identifiers only, before semantic diagnosis; no resampling after judgments.'],'counts':counts,'protected_files_before':protected,'protected_files_unchanged_at_end':all(sha(p)==s for p,s in protected.items()),'old_AB_labels_or_metrics_read':False,'coding_or_model_called':False,'runtime_changed':False}
(B/'全体计数与代表选择.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
(B/'固定12条来源与双方证据.json').write_text(json.dumps(representatives,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'counts':{d:{k:counts[d][k] for k in ('n','department_direction_counts','source_component_cluster_count','selected_ids')} for d in ('I','F')},'source_checks':[{'id':r['id'],'dimension':r['dimension'],'source_sha':r['source_sha_matches_recorded'],'candidate_sha':r['candidate_sha_matches_recorded'],'literal_found':r['actual_current_literal_found_in_source_read'],'method':r['actual_current_source_read_method']} for r in representatives]},ensure_ascii=False,indent=2))
