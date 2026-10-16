"""Source-only full-frame preflight. No classifiers, coder outputs, or labels.

All original CTX nodes and locator structures survive. Literal verification and
candidate identity are separate. Original source-specific reviews are used by
source SHA + old/new text SHA, never by a dimension or an ID exception.
"""
from pathlib import Path
import copy, hashlib, importlib.util, json, os, re, unicodedata, subprocess, zipfile
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from collections import Counter, defaultdict

OUT=Path(__file__).resolve().parent
PARENT=OUT.parent
ROOT=OUT.parents[2]
BASE=ROOT/'00-baseline'
SIDE=ROOT.parent/'编码修订核查-20261008/LLM编码/统一判据编码准备/共用纯来源材料02/provenance_with_scope02.jsonl'
spec=importlib.util.spec_from_file_location('source_projection_primitives',PARENT/'build_projection.py')
pr=importlib.util.module_from_spec(spec);spec.loader.exec_module(pr)
pr.PAIR_KEYS.add('header_index')
def sha(b):return hashlib.sha256(b).hexdigest()
def shafile(p):return sha(Path(p).read_bytes())
def canonical(o):return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def readrows(p):return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]
def write(p,b):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 if isinstance(b,str):b=b.encode()
 if p.exists():assert p.read_bytes()==b,'Existing sealed version differs: '+str(p)
 else:p.write_bytes(b)
def dump(p,o):write(p,json.dumps(o,ensure_ascii=False,indent=2)+'\n')
def jsonl(p,o):write(p,''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in o))
def norm(t):return pr.normalized_text(t)
def famnorm(t):return ''.join(c for c in unicodedata.normalize('NFKC',t) if not c.isspace() and not unicodedata.category(c).startswith('P'))
FORBIDDEN=pr.FORBIDDEN_KEYS|{'evidence_certificate','semantic_certificate','verified_semantics','dimension','dimensions','agreement','I','F','S','E','Ec','A','support_triplet','generalization_certificate','freeze_signature','validation_checks','verification','validated','coding','label','is_innovative','interpretation','semantic_fixes'}

def forbidden(v,p=''):
 if isinstance(v,dict):
  for k,x in v.items():
   if k in FORBIDDEN:yield p+'/'+k
   yield from forbidden(x,p+'/'+k)
 elif isinstance(v,list):
  for i,x in enumerate(v):yield from forbidden(x,p+'/'+str(i))

class SourceTableHTML(HTMLParser):
 def __init__(self):super().__init__();self.tables=[];self.table=None;self.row=None;self.cell=None
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='table':self.table=[];self.tables.append(self.table)
  elif tag=='tr' and self.table is not None:self.row=[];self.table.append(self.row)
  elif tag in {'td','th'} and self.row is not None:self.cell={'text_parts':[],'row_span':int(a.get('rowspan',1)),'column_span':int(a.get('colspan',1))};self.row.append(self.cell)
 def handle_data(self,s):
  if self.cell is not None:self.cell['text_parts'].append(s)
 def handle_endtag(self,t):
  if t in {'td','th'}:self.cell=None
  elif t=='tr':self.row=None
  elif t=='table':self.table=None

def word_source(path):
 p=Path(path)
 if zipfile.is_zipfile(p):
  with zipfile.ZipFile(p) as z:
   if 'word/document.xml' not in z.namelist():return None,None,None
   b=z.read('word/document.xml');root=ET.fromstring(b);ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
   texts=[''.join(n.itertext()) for n in root.findall('.//w:t',ns)]
   return '\n'.join(texts),'Word2007_ZIP_XML_signature_not_extension',None
 if p.read_bytes()[:8]==bytes.fromhex('D0CF11E0A1B11AE1'):
  txt=subprocess.run(['textutil','-convert','txt','-stdout',str(p)],capture_output=True,text=True,timeout=30)
  ht=subprocess.run(['textutil','-convert','html','-stdout',str(p)],capture_output=True,text=True,timeout=30)
  if txt.returncode or ht.returncode:return None,'Word_legacy_converter_failure',None
  parser=SourceTableHTML();parser.feed(ht.stdout);tables=[]
  for ti,rows in enumerate(parser.tables):
   carried={};grid=[];merges=[]
   for ri,row in enumerate(rows):
    cells={c:v[0] for c,v in carried.items() if v[1]>=ri};col=0
    for node in row:
     while col in cells:col+=1
     text=''.join(node['text_parts']).strip();cs=node['column_span'];rs=node['row_span']
     for c in range(col,col+cs):cells[c]=text;carried[c]=(text,ri+rs-1)
     if cs>1 or rs>1:merges.append({'text':text,'column_index':col,'physical_grid_row_start_zero_based':ri,'physical_grid_row_span':rs,'physical_grid_column_span':cs})
     col+=cs
    grid.append([cells.get(c,'') for c in range(max(cells)+1)] if cells else [])
   tables.append({'table_index_zero_based':ti,'grid_rows':grid,'physical_merged_cells':merges,'conversion_method':'macOS_textutil_HTML_rowspan_colspan','source_sha256':shafile(p)})
  return txt.stdout,'Word_legacy_textutil_signature',tables
 return None,None,None

def remove_pdf_printed_footer(t):
 """Audit only: remove bottom standalone printed-page marker, preserve policy strings."""
 pages=t.split('\f');new=[];removed=[]
 for i,page in enumerate(pages,1):
  lines=page.splitlines();last=next((j for j in range(len(lines)-1,-1,-1) if lines[j].strip()),None)
  if last is not None and re.fullmatch(r'\s*[—－\-]?\s*\d{1,3}\s*[—－\-]?\s*',lines[last]):
   removed.append({'physical_page':i,'printed_page_marker':lines[last].strip(),'extracted_line_index_zero_based':last});lines.pop(last)
  new.append('\n'.join(lines))
 return '\f'.join(new),removed

def main():
 OUT.mkdir(exist_ok=True)
 manifest_path=BASE/'source_files_manifest.json';manifest=json.loads(manifest_path.read_text())
 bs={r['sha256']:r for r in manifest['files']};bp={r['original']:r for r in manifest['files']}
 bd={'D-'+s[:16]:r for s,r in bs.items()};bd.update({pr.opaque('D2-',r['original'],r['sha256']):r for r in manifest['files']})
 framepath=BASE/'source-only-frame.jsonl';F={r['id']:r for r in readrows(framepath)}
 me=next(r for r in manifest['files'] if 'model_source_file' in r['roles']);re_=next(r for r in manifest['files'] if 'rule_input_file' in r['roles'])
 allM=readrows(me['snapshot']);allR=readrows(re_['snapshot']);M={r['id']:r for r in allM if r['id'] in F};R={r['id']:r for r in allR if r['id'] in F};side={r['id']:r for r in readrows(SIDE) if r['id'] in F}
 assert len(F)==len(M)==len(R)==len(side)==4481
 assert len(allM)==len(allR)==4924
 assert all(F[i]['unit_text']==M[i]['text']==R[i]['input']['unit_text'] for i in F)
 assert all(sha(F[i]['unit_text'].encode())==F[i]['unit_text_sha256'] for i in F)
 assert all(sha(famnorm(F[i]['unit_text']).encode())==F[i]['normalized_text_family']['normalized_text_sha256'] for i in F)
 snapshots=[];extracted={};normalized={};objects={};paragraphs={};footer_text={};footer_info={};source_tables={}
 for s,e in bs.items():
  actual=shafile(e['snapshot']);assert actual==s
  snapshots.append({'source_sha256':s,'snapshot':e['snapshot'],'bytes':Path(e['snapshot']).stat().st_size,'byte_identity_verified':True,'roles':e['roles']})
  if any(k in e['roles'] for k in ['source_file','unit_source_file']):
   t,method=pr.extract_snapshot_text(e['snapshot'])
   wt,wm,table=word_source(e['snapshot'])
   if wt is not None:t,method=wt,wm
   if table:source_tables[s]=table
   extracted[s]=(t,method);normalized[s]=norm(t) if t is not None else None
   if Path(e['snapshot']).suffix=='.pdf' and t is not None:
    clean,info=remove_pdf_printed_footer(t);footer_text[s]=norm(clean);footer_info[s]=info
   if Path(e['snapshot']).suffix.lower()=='.json':objects[s]=json.loads(Path(e['snapshot']).read_text())
  if 'candidate_file' in e['roles']:
   v=json.loads(Path(e['snapshot']).read_text());objects[s]=v;paragraphs[s]={p.get('id',p.get('paragraph_id')):p for p in v.get('paragraphs',[]) if isinstance(p,dict) and isinstance(p.get('text'),str)}
 def literal(text,s):
  if not text:return 'empty_source_cell_or_field'
  if s not in extracted:return 'no_primary_text_extractor'
  t,_=extracted[s]
  if t is None:return 'no_extractable_primary_text'
  if text in t:return 'exact_primary_extracted_text'
  if norm(text) in normalized[s]:return 'primary_NFKC_whitespace_only'
  if s in footer_text and norm(text) in footer_text[s]:return 'primary_literal_join_across_bottom_printed_page_markers'
  for table in source_tables.get(s,[]):
   if any(norm(text)==norm(' | '.join(row)) for row in table['grid_rows']):return 'primary_Word_table_cells_and_merged_rows_serialization'
  # Parsed JSON string identity is different from its escaped serialization.
  if s in objects:
   strings=[]
   def collect(v):
    if isinstance(v,str):strings.append(v)
    elif isinstance(v,list):
     for x in v:collect(x)
    elif isinstance(v,dict):
     for k,x in v.items():
      if k in {'text','raw_text','announcement_paragraphs','normative_paragraphs','rows','headers','title','caption','group_context','content','note','period','classification','分类','内容','数据保护期','备注'}:collect(x)
   collect(objects[s])
   if any(text==v or norm(text) in norm(v) for v in strings):return 'parsed_primary_JSON_source_string'
   for t in objects[s].get('tables',[]):
    for cells in t.get('rows',[]):
     if isinstance(cells,list) and text==' | '.join(str(x) for x in cells):return 'parsed_primary_table_row_serialization'
  return 'not_located_automatically'
 # Load source-reviewed corrections and visual evidence by source/text identity.
 # These are source review outputs; no coder submissions are read.
 repair_map={};visual_map={};proof_inputs=[]
 a41=json.loads((PARENT/'literal-review-v2.json').read_text())
 old41={r['id']:r for r in readrows(PARENT/'canonical_source_context.jsonl')};new41={r['id']:r for r in readrows(PARENT/'canonical_source_context-v2.jsonl')}
 for rid,o in old41.items():
  n=new41[rid]
  if o['text']!=n['text']:
   s=o['contexts'][0]['source_ref']['sha256'];repair_map[(s,sha(o['text'].encode()))]={'replacement':n['text'],'proof':'../source-context-changes-v2.json','operation':'source_diagram_number_transcription_correction'}
 def put_visual(s,oldsha,newsha,attachments,proof):
  value={'attachments':attachments,'proof':proof};visual_map[(s,oldsha)]=value;visual_map[(s,newsha)]=value
 # Reviewed nodes across both development projections can establish literal source
 # correspondence for identical source bytes + identical text, regardless of owner.
 for folder,oldname,newname,auditname in [(PARENT,'canonical_source_context.jsonl','canonical_source_context-v2.jsonl','projection-audit-v2.json'),(PARENT/'coverage01','canonical_source_context.jsonl','canonical_source_context-v2.jsonl','projection-audit-v2.json')]:
  op=folder/oldname;np=folder/newname;ap=folder/auditname;proof_inputs.extend([{'path':str(x),'sha256':shafile(x)} for x in [op,np,ap]])
  old={r['id']:r for r in readrows(op)};new={r['id']:r for r in readrows(np)};audit=json.loads(ap.read_text())
  checked=set()
  for rec in audit['context_provenance']:
   for ft in rec['text_fields']:
    if 'visual_source_check' in ft or 'source_specific_review_v2' in rec or ft.get('literal_check','').startswith('source_table') or ft.get('literal_check','').startswith('serialized_two_source'):
     checked.add((rec['record_id'],rec['context_id'],ft['field']))
  if folder==PARENT:
   for rv in a41['reviewed_context_occurrences']:checked.add((rv['record_id'],rv['context_id'],rv['field']))
  for rid,row in new.items():
   oldnodes={n['context_id']:n for n in old[rid]['contexts']}
   for node in row['contexts']:
    for field,text in pr.text_values(node):
     if (rid,node['context_id'],field) in checked:
      s=node['source_ref']['sha256'];before=dict(pr.text_values(oldnodes.get(node['context_id'],node))).get(field,text)
      ats=[]
      for at in row.get('source_page_attachments',[])+row.get('source_image_attachments',[]):
       if at.get('source_pdf_sha256',s)==s:
        at=copy.deepcopy(at);at['relative_path']=os.path.relpath(folder/at['relative_path'],OUT);assert shafile(OUT/at['relative_path'])==at['sha256'];ats.append(at)
      put_visual(s,sha(before.encode()),sha(text.encode()),ats,str(ap))
 output=[];bodyqa=[];contextqa=[];issues=[];changes=[];recordmap=[];tot=Counter();dangling=[];side_mismatch=[]
 for rid,fr in F.items():
  row=M[rid];sid=side[rid];leaf=defaultdict(list)
  for x in sid.get('policy_leaves',[]):leaf[x.get('context_id')].append(x)
  def candidates_for(cid):
   out=set()
   if fr['source_position']['candidate_file'] in bp:out.add(bp[fr['source_position']['candidate_file']]['sha256'])
   for l in leaf.get(cid,[]):
    b=l.get('source_binding',{});p=b.get('candidate_path')
    if p in bp and bp[p]['sha256']==b.get('candidate_sha256'):out.add(bp[p]['sha256'])
   for a in sid.get('added_component_fragments',[]):
    if a['context_id']==cid and a['candidate']['path'] in bp:out.add(bp[a['candidate']['path']]['sha256'])
   return out
  nodes=[];sources={};methods={};candidate_locs={}
  for original in row['contexts']:
   assert not (set(original)-pr.MODEL_KEYS),(rid,set(original)-pr.MODEL_KEYS)
   node={k:pr.scalar_tree(v) for k,v in original.items() if k in {'context_id','kind','source_document'}};node['structure']=pr.project_structure(original['structure'])
   for k in pr.POLICY_KEYS:
    if k in original:node[k]=pr.scalar_tree(original[k])
   cid=node['context_id'];src=bd.get(node.get('source_document'));method=[]
   if src:method.append('exported_document_identity')
   for l in leaf.get(cid,[]):
    txt=dict(pr.text_values(node)).get(l['output_field'])
    if txt is not None and sha(txt.encode())!=l['text_sha256']:side_mismatch.append({'record_id':rid,'context_id':cid,'field':l['output_field']})
   if not src:
    ss={l.get('source_binding',{}).get('source_sha256') for l in leaf.get(cid,[])}-{None}
    if len(ss)==1 and next(iter(ss)) in bs:src=bs[next(iter(ss))];method.append('source_only_sidecar_complete_source_pair')
   locs=[];declared=node['structure'].get('paragraph_id',node['structure'].get('candidate_paragraph_id'))
   for cs in candidates_for(cid):
    if declared in paragraphs.get(cs,{}):
     p=paragraphs[cs][declared];text=node.get('text');match=isinstance(text,str) and norm(text) in norm(p['text'])
     sourcepath=p.get('source_file',objects[cs].get('source'));actual=bp.get(sourcepath)
     loc={'candidate_sha256':cs,'paragraph_id':declared,'candidate_text_correspondence':match,'primary_source_sha256':actual['sha256'] if actual else None,'physical_pages':p.get('pages',[]),'line_ids':p.get('line_ids',[])};locs.append(loc)
   # Correct a wrong inherited boundary identity only with declared source address,
   # exact candidate text and actual byte-verified primary literal correspondence.
   if node.get('text') and src and literal(node['text'],src['sha256']) in {'not_located_automatically','no_extractable_primary_text','no_primary_text_extractor'} and node['text']!='EOF':
    # No paragraph ID on preceding paragraphs/headings: search only this record's
    # byte-verified candidate documents for a uniquely identical complete source
    # paragraph. Its source_file/rootsource must then match real primary bytes.
    if not any(l['candidate_text_correspondence'] for l in locs):
     for cs in candidates_for(cid):
      for pid,p in paragraphs.get(cs,{}).items():
       if norm(node['text'])!=norm(p['text']):continue
       actual=bp.get(p.get('source_file',objects[cs].get('source')))
       if actual:locs.append({'candidate_sha256':cs,'paragraph_id':pid,'candidate_text_correspondence':True,'primary_source_sha256':actual['sha256'],'physical_pages':p.get('pages',[]),'line_ids':p.get('line_ids',[]),'match_kind':'unique_complete_paragraph_text_in_record_candidate'})
    opts={l['primary_source_sha256']:l for l in locs if l['candidate_text_correspondence'] and l['primary_source_sha256'] in bs and literal(node['text'],l['primary_source_sha256']) in {'exact_primary_extracted_text','primary_NFKC_whitespace_only','parsed_primary_JSON_source_string'}}
    current=src['sha256'] if src else None
    if len(opts)==1 and current not in opts:
     target=next(iter(opts));before=current;src=bs[target];node['source_document']='D-'+target[:16];method.append('declared_candidate_paragraph_and_actual_primary_literal_repair')
     changes.append({'record_id':rid,'context_id':cid,'operation':'repair_declared_or_unique_literal_paragraph_primary_source_identity','before_source_sha256':before,'after_source_sha256':target,'candidate_locator':opts[target],'policy_text_unchanged':True})
   if src:sources[cid]=src
   methods[cid]=method;candidate_locs[cid]=locs;nodes.append(node)
  bycid={n['context_id']:n for n in nodes};assert len(bycid)==len(nodes)
  # Boundary containers are tied to their explicitly declared text children,
  # never guessed from a surrounding heading or unrelated parent group.
  for node in nodes:
   if node['kind']=='boundary_container':
    children=node['structure'].get('text_child_context_ids',[]);sset={sources[c]['sha256'] for c in children if c in sources}
    if len(sset)==1:
     target=next(iter(sset));current=sources.get(node['context_id'],{}).get('sha256')
     if current!=target:
      changes.append({'record_id':rid,'context_id':node['context_id'],'operation':'repair_boundary_container_from_explicit_child_source','before_source_sha256':current,'after_source_sha256':target,'child_context_ids':children,'policy_text_unchanged':True});sources[node['context_id']]=bs[target];node['source_document']='D-'+target[:16];methods[node['context_id']].append('explicit_boundary_child_primary_identity')
  for _ in range(len(nodes)):
   done=False
   for node in nodes:
    cid=node['context_id']
    if cid in sources or list(pr.text_values(node)):continue
    refs=[r for _,r in pr.context_references(node['structure'])]+[n['context_id'] for n in nodes if n['structure'].get('parent_context_id')==cid]
    opts={sources[x]['sha256'] for x in refs if x in sources}
    if len(opts)==1:sources[cid]=bs[next(iter(opts))];methods[cid].append('textless_unique_connected_source_identity');done=True
   if not done:break
  def checked_text(text,s,rid,cid,field):
   oldsha=sha(text.encode());repair=repair_map.get((s,oldsha));newtext=repair['replacement'] if repair else text
   if repair:changes.append({'record_id':rid,'context_id':cid,'field':field,'operation':repair['operation'],'before_text_sha256':oldsha,'after_text_sha256':sha(newtext.encode()),'source_sha256':s,'source_review_evidence':repair['proof']})
   status=literal(newtext,s);visual=visual_map.get((s,sha(newtext.encode())))
   if status in {'not_located_automatically','no_extractable_primary_text','no_primary_text_extractor'} and visual:status='previous_source_specific_visual_review_same_source_and_text_SHA'
   return newtext,oldsha,status,visual
  ats={}
  for node in nodes:
   cid=node['context_id'];src=sources.get(cid);s=src['sha256'] if src else None
   loc=copy.deepcopy(node['structure']);node['source_ref']={'sha256':s,'locator':loc}
   ca={'record_id':rid,'context_id':cid,'kind':node['kind'],'original_source_document':bycid[cid].get('source_document'),'primary_source_sha256':s,'source_identity_methods':methods[cid],'candidate_locators':candidate_locs[cid],'policy_text_fields':[],'textless_structure':not bool(list(pr.text_values(node)))}
   if not src:issues.append({'record_id':rid,'context_id':cid,'issue_type':'source_identity_unresolved','kind':node['kind']})
   for field,text in list(pr.text_values(node)):
    nt,oldsha,status,visual=checked_text(text,s,rid,cid,field)
    if text=='EOF' and node['kind']=='boundary' and node['structure'].get('position')=='next_component_boundary_text':status='structural_EOF_marker_not_policy_literal'
    if nt!=text:
     key,*index=field.split('/')
     if index:node[key][int(index[0])]=nt
     else:node[key]=nt
    item={'field':field,'original_text_sha256':oldsha,'projected_text_sha256':sha(nt.encode()),'literal_status':status}
    if visual:
     item['source_visual_review_evidence']=visual['proof']
     for at in visual['attachments']:ats[at['attachment_id']]=at
    ca['policy_text_fields'].append(item);tot['context_literal_'+status]+=1
    if status in {'not_located_automatically','no_extractable_primary_text','no_primary_text_extractor'}:
     typ='image_diagram_or_scanned_page_requires_visual' if src and Path(src['snapshot']).suffix=='.pdf' and (not normalized.get(s) or len(nt)>500 and any(c in nt for c in ['→','├','└','图'])) else 'literal_not_located_in_primary_extraction'
     issues.append({'record_id':rid,'context_id':cid,'field':field,'issue_type':typ,'source_sha256':s,'kind':node['kind'],'text_sha256':sha(nt.encode()),'character_N':len(nt),'locator':loc,'candidate_locators':candidate_locs[cid]})
   contextqa.append(ca);tot['contexts']+=1;tot['textless_contexts']+=ca['textless_structure'];tot['source_identity_resolved_contexts']+=bool(src)
  # Body source is the unit source, not the generic policy bundle source.
  bsrc=bp.get(fr['source_position']['unit_source_file']);s=bsrc['sha256'] if bsrc else None
  body,boldsha,status,visual=checked_text(row['text'],s,rid,None,'text')
  bqa={'record_id':rid,'primary_source_sha256':s,'frame_body_sha256':fr['unit_text_sha256'],'projected_body_sha256':sha(body.encode()),'literal_status':status,'pages':row['pages'],'source_position':fr['source_position']}
  if visual:
   bqa['source_visual_review_evidence']=visual['proof']
   for at in visual['attachments']:ats[at['attachment_id']]=at
  bodyqa.append(bqa);tot['body_literal_'+status]+=1
  if status in {'not_located_automatically','no_extractable_primary_text','no_primary_text_extractor'}:issues.append({'record_id':rid,'context_id':None,'field':'text','issue_type':'body_literal_not_located_in_primary_extraction','source_sha256':s,'text_sha256':sha(body.encode()),'character_N':len(body),'pages':row['pages']})
  newrow={'id':rid,'text':body,'pages':copy.deepcopy(row['pages']),'source_ref':{'sha256':s,'locator':{'physical_pages':copy.deepcopy(row['pages']),'paragraph_ids':fr['source_position']['paragraph_ids'],'source_unit_id':fr['source_position']['unit_id']}},'contexts':nodes}
  # Source Word table geometry is serialized separately from candidate semantic
  # metadata. It is based on converted original binary rowspan/colspan only.
  for table in source_tables.get(s,[]):
   matches=[(i,cells) for i,cells in enumerate(table['grid_rows']) if norm(body)==norm(' | '.join(cells))]
   if len(matches)==1:
    ri,cells=matches[0];tablecid='CTX-SRCFULL-'+sha((s+'/table/'+str(table['table_index_zero_based'])+'/row/'+str(ri)).encode())[:20]
    tnode={'context_id':tablecid,'kind':'table_row','source_document':'D-'+s[:16],'structure':{'physical_grid_row_index_zero_based':ri,'table_index_zero_based':table['table_index_zero_based'],'grid_row_index_convention':'0 denotes original header row','physical_merged_cells':copy.deepcopy(table['physical_merged_cells']),'column_indices':list(range(len(cells)))},'headers':table['grid_rows'][0],'row_cells':cells,'source_ref':{'sha256':s,'locator':{'original_binary_table_index_zero_based':table['table_index_zero_based'],'physical_grid_row_index_zero_based':ri,'conversion_method':table['conversion_method']}}}
    nodes.append(tnode);bycid[tablecid]=tnode;tot['new_source_Word_geometry_nodes']+=1
    changes.append({'record_id':rid,'context_id':tablecid,'operation':'add_original_binary_Word_table_row_header_and_merge_geometry','source_sha256':s,'physical_grid_row_index_zero_based':ri,'source_conversion_method':table['conversion_method'],'original_nodes_and_body_retained':True})
  if ats:newrow['source_attachments']=list(ats.values())
  for node in nodes:
   for ptr,value in pr.context_references(node):
    if value not in bycid:dangling.append({'record_id':rid,'context_id':node['context_id'],'pointer':ptr,'target':value})
  output.append(newrow);recordmap.append({'id':rid,'department':fr['analysis_group'],'original_frame_body_sha256':fr['unit_text_sha256'],'projected_body_sha256':sha(body.encode()),'body_changed':body!=fr['unit_text'],'original_family_id':fr['normalized_text_family']['family_id'],'projected_family_id':'TEXTFAM-'+sha(famnorm(body).encode()),'primary_source_sha256':s,'original_context_sha256':fr['shared_context_identity']['model_contexts_sha256'],'projected_context_sha256':sha(canonical(nodes).encode()),'projected_record_sha256':sha(canonical(newrow).encode())})
 assert not dangling,dangling
 assert not side_mismatch,side_mismatch
 bad=list(forbidden(output));assert not bad,bad
 outpath=OUT/'canonical_source_context-v2.jsonl';jsonl(outpath,output)
 jsonl(OUT/'body-source-QA-v2.jsonl',bodyqa);jsonl(OUT/'context-source-QA-v2.jsonl',contextqa);jsonl(OUT/'material-record-bindings-v2.jsonl',recordmap);jsonl(OUT/'source-exceptions-v2.jsonl',issues);dump(OUT/'source-changes-v2.json',{'changes':changes,'source_specific_review_inputs':proof_inputs})
 exposure=json.loads((ROOT/'01-review/exposure-ids.json').read_text());direct=set(exposure['direct_exposure_ids']);oldex=set(exposure['excluded_ids']);oldeligible=set(exposure['eligible_ids']) if 'eligible_ids' in exposure else set(F)-oldex
 groups=defaultdict(list)
 for r in recordmap:groups[r['projected_family_id']].append(r['id'])
 expfamilies={r['projected_family_id'] for r in recordmap if r['id'] in direct};newex={r['id'] for r in recordmap if r['projected_family_id'] in expfamilies};eligible=set(F)-newex
 family={'normalization':'NFKC; remove Unicode whitespace and P* punctuation; keep remaining symbols and case; same baseline algorithm verified for all4481 original bodies','original_family_N':len({r['original_family_id'] for r in recordmap}),'projected_family_N':len(groups),'changed_body_N':sum(r['body_changed'] for r in recordmap),'changed_body_records':[r for r in recordmap if r['body_changed']],'changed_family_assignment_N':sum(r['original_family_id']!=r['projected_family_id'] for r in recordmap),'old_direct_exposure_N':len(direct),'same_historical_direct_evidence_preserved':True,'old_closed_excluded_N':len(oldex),'recomputed_closed_excluded_N':len(newex),'old_remaining_pool_N':len(oldeligible),'recomputed_remaining_pool_N':len(eligible),'newly_closed_excluded_ids':sorted(newex-oldex),'no_longer_family_closed_ids':sorted(oldex-newex),'remaining_pool_membership_unchanged':eligible==oldeligible,'remaining_by_department':dict(Counter(F[i]['analysis_group'] for i in eligible)),'remaining_pool_not_final_sample':True,'no_new_case_coding_or_manual_use':True,'source_review_only_not_added_to_direct_exposure':True,'freeze_instruction':'Repeat family/exposure closure after all future source body repairs and finalized development exposure registry; 1444 and proposed600 are pre-freeze candidate designs.'}
 dump(OUT/'family-exposure-impact-v2.json',family);dump(OUT/'normalized-text-families-v2.json',{'normalization':family['normalization'],'families':[{'family_id':k,'ids':sorted(v)} for k,v in sorted(groups.items())]})
 dump(OUT/'original-Word-table-geometry-v2.json',{'tables':[{'source_sha256':s,'tables':t} for s,t in source_tables.items()],'render_or_conversion_identity':'derived source layout, not official-origin binary authentication'})
 dump(OUT/'printed-page-marker-extraction-v2.json',{'sources':[{'source_sha256':s,'removed_bottom_markers':x} for s,x in footer_info.items()],'scope':'Audit-only layout extraction join. No policy text normalization/correction is performed.'})
 qa={'status':'full_frame_source_only_automatic_preflight_complete; pending_source_specific_visual_and_locator_reviews_retained','frame_N':4481,'source_interface_input_N':4924,'excluded_GOV_interface_N':443,'department_N':dict(Counter(r['analysis_group'] for r in F.values())),'counts':dict(tot),'source_snapshot_byte_check_N':len(snapshots),'source_snapshot_byte_failures_N':0,'all_original_context_nodes_and_CTX_IDs_retained':True,'original_context_N':sum(len(r['contexts']) for r in M.values()),'all_original_textless_structure_nodes_retained':True,'body_changes_N':sum(r['body_changed'] for r in recordmap),'source_change_operations':dict(Counter(r['operation'] for r in changes)),'dangling_recursive_CTX_references':dangling,'source_sidecar_policy_field_SHA_mismatches':side_mismatch,'recursive_forbidden_keys':{'keys':sorted(FORBIDDEN),'violations':bad},'pending_issue_N':len(issues),'pending_issue_types':dict(Counter(r['issue_type'] for r in issues)),'pending_unique_source_text_N':len({(r.get('source_sha256'),r.get('text_sha256')) for r in issues if r.get('text_sha256')}),'input_files':[{'path':str(p),'sha256':shafile(p)} for p in [framepath,manifest_path,Path(me['snapshot']),Path(re_['snapshot']),SIDE]],'source_specific_review_inputs':proof_inputs,'builder_sha256':shafile(__file__),'output':{'path':str(outpath),'sha256':shafile(outpath)},'outputs':[{'path':str(p),'sha256':shafile(p)} for p in sorted(OUT.glob('*-v2.json*'))],'source_snapshot_byte_checks':snapshots,'scope':{'dimension_judgment_performed':False,'new_classifier_run':False,'coder_outputs_read':False,'final_sample_drawn':False,'rows_dropped_due_to_labels_or_scores':0,'full_frame_projection_is_not_statement_of_semantic_context_sufficiency':True},'limits':['Automatic nonmatch is a pending source locator/extraction problem, not proof of erroneous policy text.','Candidate JSON source content does not substitute for authentication against the original binary; source and candidate checks are separate.','Source locator and original geometry are permitted; semantic/manual certificates are excluded.','Source-QA may expose source text but does not constitute case-coding development. This preserves the stated exposure definition; it is not a certificate that coders have never seen the text.','This version retains actual full source structure and existing CTXIDs. Tables/graphs that cannot be certified mechanically remain pending and must not be declared fully authenticated.','Two supplemental sources are a separate neutral library with literal reference candidates, not an automatic per-row semantic evidence extension.']}
 dump(OUT/'source-QA-summary-v2.json',qa)
 print(json.dumps({'counts':dict(tot),'issues':qa['pending_issue_types'],'pending_N':len(issues),'changes':qa['source_change_operations'],'body_changes_N':qa['body_changes_N'],'output_sha256':shafile(outpath),'family_impact':{k:family[k] for k in ['changed_family_assignment_N','recomputed_closed_excluded_N','recomputed_remaining_pool_N','remaining_pool_membership_unchanged']}},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
