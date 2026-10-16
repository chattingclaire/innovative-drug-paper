"""Source-only same-version projection. No reference labels or classification."""
from pathlib import Path
import copy,hashlib,json,re,sys,html
import fitz
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];PREV=HERE.parent/'规则修复第五轮-20261015'
sys.path.insert(0,str(PREV/'code'))
import source_packet,evidence

def sha(x):return hashlib.sha256(x).hexdigest()
def cj(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def save(name,x):(HERE/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def bind(p):
 p=Path(p);b=p.read_bytes();return {'path':str(p.resolve()),'bytes':len(b),'sha256':sha(b)}
def norm(t):return re.sub(r'\s+','',t)
def declared(u):
 ds=[d for d in u['source_bundle']['source_documents'] if d['source_sha256']==u['source_ref']['sha256']];assert len(ds)==1
 d=ds[0];p=Path(d['snapshot']);raw=p.read_bytes();assert sha(raw)==d['source_sha256'] and len(raw)==d['bytes'];return p,raw,d

def textleaf(p,raw):
 t=raw.decode();d=sha(raw);loc={'kind':'verbatim_UTF8_snapshot_text','snapshot_absolute_path':str(p),'snapshot_sha256':d,
 'coordinate_basis':'exact original UTF8 bytes decoded without newline normalization','physical_line_interval_inclusive_1based':[1,len(t.splitlines(keepends=True))],
 'unicode_code_point_interval_half_open':[0,len(t)],'utf8_byte_interval_half_open':[0,len(raw)],'physical_pages':None}
 return {'kind':'verbatim_UTF8_snapshot_text','source_resource_id':'SOURCE-TEXT-'+d+'-COMPLETE','source_sha256':d,'source_version_id':'SOURCEVERSION-'+d,'text':t,'text_utf8_sha256':d,'text_utf8_bytes':len(raw),'text_unicode_code_points':len(t),'locator':loc}

def utf8_articles(p,raw):
 t=raw.decode();d=sha(raw);ls=t.splitlines(keepends=True);offs=[0]
 for l in ls:offs.append(offs[-1]+len(l))
 docid='SOURCE-ORDERED-UTF8-'+d;ms=[]
 def loc(i,j):
  a,b=offs[i],offs[j];return {'kind':'verbatim_UTF8_snapshot_text','snapshot_absolute_path':str(p),'snapshot_sha256':d,'physical_line_interval_inclusive_1based':[i+1,j],'unicode_code_point_interval_half_open':[a,b],'utf8_byte_interval_half_open':[len(t[:a].encode()),len(t[:b].encode())]}
 for i,l in enumerate(ls):
  ms.append({'source_resource_id':f'{docid}-L{i+1:04d}','source_document_resource_id':'SOURCE-'+d,'source_sha256':d,'text':l,'text_sha256':sha(l.encode()),'representation':'literal original UTF8 physical line','source_locator':loc(i,i+1)})
 groups=[];heads=[]
 for i,l in enumerate(ls):
  m=re.match(r'^(第[一二三四五六七八九十百零〇两]+[条章节])',l.strip())
  if m:heads.append((i,m.group(1)))
 for n,(i,h) in enumerate(heads):
  if not h.endswith('条'):continue
  j=heads[n+1][0] if n+1<len(heads) else len(ls)
  # This source prints article headings and first proposition on one line.
  selected=ms[i:j]
  for k,m in enumerate(selected,1):m.update(article=h,clause_index_one_based=k)
  groups.append({'article':h,'source_sha256':d,'ordered_source_resource_ids':[m['source_resource_id'] for m in selected],
   'next_boundary_source_resource_id':ms[j]['source_resource_id'] if j<len(ms) else None,'article_with_heading_locator':loc(i,j),
   'closure_basis':'all physical lines from literal article heading through immediately before next original article/chapter/section heading'})
 return {'source_resource_id':docid,'source_sha256':d,'source_texts':ms,'ordered_article_groups':groups,'representation':'exact UTF8 physical lines grouped by original heading boundaries'},textleaf(p,raw)

oldpath=ROOT/'06-coding/rule-full4481-v2-root/run4481-first/effective-semantic-units.jsonl'
targets={'RECODE25-01383','RECODE25-03423','RECODE25-04067','RECODE25-03919'}
olds={r['id']:r['semantic_unit'] for r in map(json.loads,oldpath.open()) if r['id'] in targets}
prevpath=PREV/'semantic-overrides.json';outputs=json.loads(prevpath.read_text());previous=copy.deepcopy(outputs)
bindings=[];source_checks=[]

def finish(sid,bundle,notes):
 old=olds[sid];assert source_packet.semantic_unit(old['source_bundle'])==old
 new=source_packet.semantic_unit(bundle)
 # Preserve original semantic ordering/provenance while appending only new IDs.
 byid={c['context_id']:c for c in new['contexts']};oldids={c['context_id'] for c in old['contexts']}
 assert all(byid[c['context_id']]==c for c in old['contexts'])
 new['contexts']=copy.deepcopy(old['contexts'])+[c for c in new['contexts'] if c['context_id'] not in oldids]
 new['derived_context_origins'].update(copy.deepcopy(old['derived_context_origins']))
 assert new['text']==old['text'] and new['source_ref']==old['source_ref']
 assert new['contexts'][:len(old['contexts'])]==old['contexts']
 assert {k:new['derived_context_origins'][k] for k in old['derived_context_origins']}==old['derived_context_origins']
 assert bundle['source_record']==old['source_bundle']['source_record']
 for k in old:
  if k not in ['contexts','source_bundle','derived_context_origins']:assert new[k]==old[k]
 assert len({c['context_id'] for c in new['contexts']})==len(new['contexts'])
 for c in new['contexts'][len(old['contexts']):]:
  v=new['source_bundle'];ptr=new['derived_context_origins'][c['context_id']]['source_bundle_pointer']
  for k in ptr.strip('/').split('/'):v=v[int(k)] if isinstance(v,list) else v[k]
  assert c['text']==v['text']
  assert evidence.context_anchor(new,c['context_id'],0,len(c['text']),'source_only_projection_check')['text']==c['text']
 inv=copy.deepcopy(bundle);inv['source_record']['id']=sid;source_packet.source_inventory(inv)
 outputs[sid]=new
 bindings.append({'id':sid,'old_semantic_sha256':sha(cj(old)),'new_semantic_sha256':sha(cj(new)),
 'current_and_raw_source_record_unchanged':True,'old_contexts_exact_prefix':True,'old_origins_unchanged':True,
 'added_context_N':len(new['contexts'])-len(old['contexts']),'adapter_baseline_exact':True,'no_classification_run':True,'notes':notes})

# Text original: all original articles, not only a selected branch.
sid='RECODE25-04067';old=olds[sid];p,raw,spec=declared(old);doc,leaf=utf8_articles(p,raw)
assert len([g for g in doc['ordered_article_groups'] if g['article']=='第四十二条'])==1
b=copy.deepcopy(old['source_bundle']);b['source_full_text_resources'].append(leaf);b['explicit_or_primary_source_resources'].append(doc)
finish(sid,b,{'article_N':len(doc['ordered_article_groups']),'article42':next(g for g in doc['ordered_article_groups'] if g['article']=='第四十二条'),'article43':next(g for g in doc['ordered_article_groups'] if g['article']=='第四十三条')})
source_checks.append(bind(p))

# JSON+actual HTML: preserve all existing paragraph objects and IDs verbatim.
sid='RECODE25-01383';old=olds[sid];p,raw,spec=declared(old);j=json.loads(raw);d=sha(raw)
hp=Path(j['source_html']);hr=hp.read_bytes();assert sha(hr)==j['source_sha256'];ht=hr.decode()
ps=[]
for k,m in enumerate(re.finditer(r'<p\b[^>]*>.*?</p>',ht,re.S|re.I)):
 visible=html.unescape(re.sub(r'<[^>]*>','',m.group()))
 ps.append({'i':k,'a':m.start(),'b':m.end(),'text':visible,'outer_sha256':sha(m.group().encode())})
existing={m['source_resource_id']:m for doc in old['source_bundle']['explicit_or_primary_source_resources'] for m in doc.get('source_texts',[])}
newms=[];groups=[];annids=[];normids=[];article=None;clause=0;html_cursor=0
for category,prefix in [('announcement_paragraphs','AP'),('normative_paragraphs','NP')]:
 for i,t in enumerate(j[category]):
  hits=[x for x in ps if norm(x['text'])==norm(t) and x['a']>=html_cursor];assert hits,(category,i);hit=min(hits,key=lambda x:x['a']);html_cursor=hit['b']
  rid=f'SOURCETEXT-{d[:16]}-{prefix}{i:03d}'
  if category=='normative_paragraphs':
   am=re.match(r'(第[一二三四五六七八九十百]+条)',t)
   if am:article=am.group(1);clause=0;groups.append({'article':article,'source_sha256':d,'ordered_source_resource_ids':[]})
   clause+=1;groups[-1]['ordered_source_resource_ids'].append(rid);normids.append(rid)
  else:annids.append(rid)
  loc={'kind':'structured_JSON_and_original_HTML','structured_snapshot':{'absolute_path':str(p),'sha256':d,'json_pointer':f'/{category}/{i}'},
   'raw_html':{'absolute_path':str(hp),'sha256':sha(hr),'text_view':'strict UTF8 original raw bytes; CR/LF preserved','locator':{'tag':'p','p_element_index_zero_based_document_wide':hit['i'],'unicode_character_start_zero_based':hit['a'],'unicode_character_end_exclusive':hit['b'],'outer_html_sha256_utf8':hit['outer_sha256']}}}
  row={'source_resource_id':rid,'source_document_resource_id':'SOURCE-'+d,'source_sha256':d,'text':t,'text_sha256':sha(t.encode()),'source_locator':loc,'role':'original_normative_paragraph' if category=='normative_paragraphs' else 'original_announcement_paragraph','representation':f'literal_structured_JSON_{category}; original_HTML_visible_text'}
  if category=='normative_paragraphs':row.update(article=article,clause_index_one_based=clause)
  if rid in existing:assert existing[rid]['text']==t;row=copy.deepcopy(existing[rid])
  newms.append(row)
# Retain the actual attachment label and attachment title, not an invented component ID.
links=[]
for label in ['附件：药品试验数据保护实施办法','药品试验数据保护实施办法']:
 hits=[x for x in ps if norm(x['text'])==norm(label)];assert len(hits)==1;hit=hits[0];rid=f'HTML-BINDING-{d[:16]}-P{hit["i"]:03d}'
 row={'source_resource_id':rid,'source_document_resource_id':'SOURCE-'+d,'source_sha256':d,'text':hit['text'],'text_sha256':sha(hit['text'].encode()),'representation':'literal original HTML visible paragraph; not a JSON normative paragraph','source_locator':{'kind':'original_HTML_visible_text','structured_snapshot':{'absolute_path':str(p),'sha256':d,'json_pointer':'/excluded_metadata/'+str(j['excluded_metadata'].index(label))},'raw_html_path':str(hp),'raw_html_sha256':sha(hr),'unicode_character_interval_half_open':[hit['a'],hit['b']],'outer_html_sha256_utf8':hit['outer_sha256']}}
 newms.append(row);links.append(rid)
# Entire original tables stay in payload, with every cell delivered as exact JSON text.
table_rows=[]
for ti,table in enumerate(j['tables']):
 ip=Path(table['source_image']);assert sha(ip.read_bytes())==table['source_sha256'];source_checks.append(bind(ip))
 table_rows.append(copy.deepcopy(table))
 for ri,row in enumerate(table['rows']):
  for ci,t in enumerate(row):
   if t=='':continue  # Empty cells remain literal empty in complete table payload; no nonempty evidence anchor.
   rid=f'JSONCELL-{d[:16]}-T{ti}-R{ri}-C{ci}'
   newms.append({'source_resource_id':rid,'source_document_resource_id':'SOURCE-'+d,'source_sha256':d,'text':t,'text_sha256':sha(t.encode()),'representation':'literal structured JSON table cell; source image binding retained','source_locator':{'kind':'structured_JSON_and_original_image','structured_snapshot':{'absolute_path':str(p),'sha256':d,'json_pointer':f'/tables/{ti}/rows/{ri}/{ci}'},'source_image':str(ip),'source_image_sha256':table['source_sha256']}})
complete={'source_resource_id':'SOURCE-COMPLETE-JSONHTML-'+d,'source_document_resource_id':'SOURCE-'+d,'source_sha256':d,'snapshot':str(p),'snapshot_sha256':d,'source_texts':newms,'ordered_article_groups':groups,'ordered_announcement_resource_ids':annids,'ordered_normative_resource_ids':normids,'attachment_connection_resource_ids':links,'original_tables':table_rows,'original_excluded_metadata':copy.deepcopy(j['excluded_metadata']),'representation':'complete declaration, normative paragraphs and original tables from bound JSON with HTML paragraph anchors; no inferred component ID'}
b=copy.deepcopy(old['source_bundle']);b['explicit_or_primary_source_resources'].append(complete);b['source_full_text_resources'].extend([textleaf(p,raw),textleaf(hp,hr)])
finish(sid,b,{'announcement_paragraph_N':len(annids),'normative_paragraph_N':len(normids),'article_N':len(groups),'table_N':len(table_rows),'attachment_connection_resource_ids':links,'old_3rd_5th_article_members_reused_exactly':True})
source_checks.extend([bind(p),bind(hp)])

# PDF pages 5-7: literal page extraction and exact member spans, visually checked.
sid='RECODE25-03423';old=olds[sid];p,raw,spec=declared(old);d=sha(raw);pdf=fitz.open(p);pages=[]
for physical in [5,6,7]:
 page=pdf[physical-1];t=page.get_text('text');rid=f'PDFPAGE-{d[:16]}-P{physical:03d}'
 pages.append({'source_resource_id':rid,'source_paragraph_id':rid,'source_sha256':d,'physical_pages':[physical],'text':t,'text_sha256':sha(t.encode()),'source_locator':{'kind':'original_PDF_page_text','snapshot_absolute_path':str(p),'source_pdf_sha256':d,'physical_page_1based':physical,'page_width_points':page.rect.width,'page_height_points':page.rect.height,'extraction':'PyMuPDF page.get_text(text), full page including printed page number; no whitespace normalization','extraction_library_version':fitz.VersionBind}})
labels=['认知功能的变化：','感官功能的变化：','运动功能的变化：','其他生理和病理生理学变化：','多病共存和多重用药：','心理和社会因素：']
member_spans=[]
for k,label in enumerate(labels):
 matches=[(idx,pg,pg['text'].index(label)) for idx,pg in enumerate(pages) if label in pg['text']];assert len(matches)==1;idx,pg,start=matches[0]
 end=pg['text'].find(labels[k+1],start+len(label)) if k+1<len(labels) else -1
 if end<0:end=len(pg['text'])
 member_spans.append({'member_sequence_index_1based':k+1,'literal_heading':label,'source_resource_id':pg['source_resource_id'],'physical_page_1based':idx+5,'unicode_code_point_interval_half_open':[start,end],'text':pg['text'][start:end],'text_sha256':sha(pg['text'][start:end].encode())})
# The next page's complete conclusion and next subsection are retained, not read as members.
assert '因此，以老年患者的需求为中心' in pages[2]['text'] and '（二）将老年患者反馈机制纳入药物研发全过程' in pages[2]['text']
full={'source_resource_id':'SOURCE-PDF-PAGES-'+d+'-P005-P007','source_sha256':d,'source_pdf_sha256':d,'source_snapshot':str(p),'paragraphs':pages,
 'representation':'complete physical PDF pages 5-7; visual source checked; no invented numbered list or component ID',
 'bounded_unordered_list':{'lead_in_page_resource_id':pages[0]['source_resource_id'],'literal_lead_in':'这些特征包括但不限于以下几个方面：','ordered_member_ranges':member_spans,'closure_page_resource_id':pages[2]['source_resource_id'],'literal_conclusion_start':'因此，以老年患者的需求为中心','literal_next_subsection':'（二）将老年患者反馈机制纳入药物研发全过程','membership_basis':'six original paragraph headings, original page/text order; not synthetic numbered items'}}
b=copy.deepcopy(old['source_bundle']);b['source_full_text_resources'].append(full)
finish(sid,b,{'physical_pages':[5,6,7],'complete_feature_member_N':6,'visual_review_images':['source-review/03423-page-5.png','source-review/03423-page-6.png','source-review/03423-page-7.png'],'PDF_SHA_is_distinct_from_extracted_text_SHA':True})
source_checks.append(bind(p))
# Same-PDF FAQ source: full announcement page and the entire two-page annex.
sid='RECODE25-03919';old=olds[sid];p,raw,spec=declared(old);d=sha(raw);pdf=fitz.open(p);faqpages=[]
for physical in [1,12,13]:
 page=pdf[physical-1];t=page.get_text('text');rid=f'PDFPAGE-{d[:16]}-P{physical:03d}'
 faqpages.append({'source_resource_id':rid,'source_paragraph_id':rid,'source_sha256':d,'physical_pages':[physical],'text':t,'text_sha256':sha(t.encode()),'source_locator':{'kind':'original_PDF_page_text','snapshot_absolute_path':str(p),'source_pdf_sha256':d,'physical_page_1based':physical,'page_width_points':page.rect.width,'page_height_points':page.rect.height,'extraction':'PyMuPDF page.get_text(text), full page including printed page number; no whitespace normalization','extraction_library_version':fitz.VersionBind}})
assert pdf.page_count==13
ann=faqpages[0]['text'];front=faqpages[1]['text'];end=faqpages[2]['text']
assert '2.《药物临床试验质量管理规范（2026 年修订）》问答文件' in ann
assert '附件2' in front and '《药物临床试验质量管理规范（2026 年修订）》' in front and '问答文件' in front
headings=[]
for pg in faqpages[1:]:
 for m in re.finditer(r'(?m)^[一二三四五六]、[^\n]+',pg['text']):
  headings.append({'literal_heading':m.group(),'source_resource_id':pg['source_resource_id'],'physical_page_1based':pg['physical_pages'][0],'unicode_code_point_interval_half_open':[m.start(),m.end()]})
assert len(headings)==6
full={'source_resource_id':'SOURCE-PDF-PAGES-'+d+'-P001-P012-P013','source_sha256':d,'source_pdf_sha256':d,'source_snapshot':str(p),'paragraphs':faqpages,
 'representation':'complete physical PDF announcement page 1 and complete FAQ annex pages 12-13; no cross-SHA object inference',
 'annex_literal_index':{'announcement_page_resource_id':faqpages[0]['source_resource_id'],'literal_annex_reference':'2.《药物临床试验质量管理规范（2026 年修订）》问答文件','annex_title_page_resource_id':faqpages[1]['source_resource_id'],'literal_annex_marker':'附件2','literal_title':'《药物临床试验质量管理规范（2026 年修订）》','literal_document_kind':'问答文件','ordered_question_headings':headings,'complete_annex_pages':[12,13],'annex_ends_at_document_physical_page':13}}
b=copy.deepcopy(old['source_bundle']);b['source_full_text_resources'].append(full)
finish(sid,b,{'physical_pages':[1,12,13],'complete_question_N':6,'same_primary_PDF_only':True,'other_SHA_old_contexts_preserved_but_not_used_to_supply_new_material':True,'visual_review_images':['source-review/03919-page-1.png','source-review/03919-page-12.png','source-review/03919-page-13.png']})
source_checks.append(bind(p))

assert all(outputs[k]==v for k,v in previous.items())
save('semantic-overrides.json',outputs)
save('source-projection-bindings.json',{'old_effective_inputs':bind(oldpath),'previous_round_overrides':bind(prevpath),'previous_two_units_unchanged':True,'output':bind(HERE/'semantic-overrides.json'),'adapter':bind(PREV/'code/source_packet.py'),'records':bindings,'verified_originals':source_checks,'new_record_N':4,'total_override_N':len(outputs),'human_answers_read':False,'classification_run':False,'component_ids_invented':False})
print(json.dumps({'total_overrides':len(outputs),'new_records':4,'source_checks':len(source_checks),'bindings':[(x['id'],x['added_context_N']) for x in bindings]},ensure_ascii=False))
