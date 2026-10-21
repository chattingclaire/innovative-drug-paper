"""Read-only DOCX integration preflight. Writes JSON/text preview only, never DOCX.
No automatic discovery or reading of any candidate03 run, labels or statistics.
"""
from pathlib import Path,PurePosixPath
from zipfile import ZipFile
from collections import Counter
import argparse,hashlib,json,re,sys,datetime
from lxml import etree as E

ROOT=Path('/PROJECT_ROOT')
R3=ROOT/'outputs/coding-revision-20261007-r3'
D=R3/'manuscript-update-20261008'
BASE=ROOT/'outputs/final-three-department-20261007/论文修订稿-三部门版.docx'
EXPECTED_REPLACEMENT_N=52
BASE_SHA='4ca9e0b4340f045a4f8dd6c2bbb83bd4c8ff88bf1f01426be2f7e397d4923fae'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships','wp':'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing','v':'urn:schemas-microsoft-com:vml'}
W=lambda n:'{'+NS['w']+'}'+n
FIELD=re.compile(r'\{\{([A-Za-z][A-Za-z0-9_]*)\}\}')
CITE=re.compile(r'\[(?P<old>\d+(?:\s*[,，;；–—-]\s*\d+)*)\]|〔(?P<keys>[A-Za-z][A-Za-z0-9_]*(?:\s*[;；,，]\s*[A-Za-z][A-Za-z0-9_]*)*)〕')
sha=lambda data:hashlib.sha256(data).hexdigest()
def bind(p):return {'path':str(p),'sha256':sha(p.read_bytes())}
def read(p):return json.loads(p.read_text())
def plain(x):return ''.join(x.xpath('.//w:t/text()',namespaces=NS))
def xmlbytes(x):return E.tostring(x,encoding='UTF-8',with_tail=False)
def xmlbind(x):return {'xml_sha256':sha(xmlbytes(x)),'canonical_xml_sha256':sha(E.tostring(x,method='c14n'))}
def write(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def numbers(token):
 out=[]
 for item in re.split('[,，;；]',token):
  ends=re.split('[–—-]',item.strip())
  assert len(ends)<=2
  a=int(ends[0]);b=int(ends[-1]);assert a<=b
  out.extend(range(a,b+1))
 return out

def citation_identity(match,keys,refs):
 if match.group('old') is not None:
  result=['old:'+str(n) for n in numbers(match.group('old'))]
  assert all(int(x[4:]) in refs for x in result),match.group()
 else:
  result=[]
  for key in re.split('[;；,，]',match.group('keys')):
   key=key.strip();assert key in keys,'unresolved citation source key '+key
   old=keys[key].get('existing_number')
   assert old is None or old in refs
   result.append('old:'+str(old) if old is not None else 'new:'+key)
 return list(dict.fromkeys(result))

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=Path(__file__).parent/'snapshot-20261008-v4');ap.add_argument('--require-manuscript-ready',action='store_true');args=ap.parse_args()
 assert not args.out.exists(),'Preserve prior preflight; choose a new output directory'
 rep_path=D/'完整论文局部替换稿-v4.json';ref_path=D/'新引用接入清单.json';inputs=[BASE,rep_path,ref_path,Path(__file__)];initial={str(p):sha(p.read_bytes()) for p in inputs}
 assert initial[str(BASE)]==BASE_SHA
 staged=read(rep_path);keylist=read(ref_path);keys=keylist['source_keys']
 assert staged['baseline']['sha256']==BASE_SHA and Path(staged['baseline']['path'])==BASE
 assert len(staged['replacements'])==EXPECTED_REPLACEMENT_N
 with ZipFile(BASE) as z:parts={x.filename:z.read(x.filename) for x in z.infolist()}
 document=E.fromstring(parts['word/document.xml']);body=document.find('w:body',NS);ps=body.findall('w:p',NS);tables=body.findall('w:tbl',NS)
 assert len(ps)==173 and len(tables)==4
 replacements={x['zero_based_body_p_index']:x for x in staged['replacements']};assert len(replacements)==EXPECTED_REPLACEMENT_N
 checked=[]
 for index,item in replacements.items():
  actual=plain(ps[index]);assert sha(actual.encode())==item['old_text_sha256'] and actual==item['old_text'],index
  checked.append({'zero_based_body_p_index':index,'old_text_sha256':sha(actual.encode()),'replacement_text_sha256':sha(item['replacement_text'].encode()),'unchanged_after_review':item['unchanged_after_review']})
 boundary=next(i for i,p in enumerate(ps) if plain(p).strip()=='参考文献');assert boundary==110
 oldrefs={};ref_positions={}
 for i in range(boundary+1,len(ps)):
  text=plain(ps[i]);match=re.fullmatch(r'\[(\d+)\]\s*(.*)',text)
  assert match,text
  n=int(match[1]);assert n not in oldrefs;oldrefs[n]=match[2];ref_positions[n]=i
 assert set(oldrefs)==set(range(1,63))
 aliases={}
 for key,item in keys.items():
  if item.get('existing_number') is not None:
   n=item['existing_number'];assert n in oldrefs;aliases.setdefault('old:'+str(n),[]).append(key)
 # Document-order stream includes all preserved table cells and their paragraphs.
 # Table2/3 legacy numbers are never inserted into the staged preview.
 blocks=[];pindex=0;tindex=0
 for child_index,node in enumerate(body):
  if node.tag==W('p'):
   if pindex<boundary:
    text=replacements[pindex]['replacement_text'] if pindex in replacements else plain(node)
    blocks.append({'kind':'paragraph','body_child_index':child_index,'body_p_index':pindex,'text':text,'baseline_xml':xmlbind(node),'replacement':pindex in replacements})
   pindex+=1
  elif node.tag==W('tbl'):
   tindex+=1
   if tindex in (1,4):
    cells=[]
    for ri,row in enumerate(node.findall('w:tr',NS)):
     for ci,cell in enumerate(row.findall('w:tc',NS)):
      for pi,p in enumerate(cell.findall('w:p',NS)):cells.append({'row':ri,'column':ci,'paragraph':pi,'text':plain(p)})
    blocks.append({'kind':'preserved_table','body_child_index':child_index,'table_number':tindex,'cells':cells,'baseline_xml':xmlbind(node)})
   else:blocks.append({'kind':'statistical_table_pending','body_child_index':child_index,'table_number':tindex,'legacy_values_omitted':True,'contract':staged['table_contracts']['table_'+str(tindex)]})
 # Record each first appearance once, deduplicating alias keys that refer to oldrefs.
 ordering=[];first={};occurrences=[];all_fields=set();field_occurrences={}
 for block in blocks:
  pieces=[{'text':block['text'],'location':{'body_p_index':block['body_p_index']}}] if block['kind']=='paragraph' else [{'text':x['text'],'location':{'table_number':block['table_number'],'row':x['row'],'column':x['column'],'cell_paragraph':x['paragraph']}} for x in block.get('cells',[])]
  for piece in pieces:
   for f in FIELD.finditer(piece['text']):
    all_fields.add(f[1]);field_occurrences.setdefault(f[1],[]).append(piece['location'])
   for match in CITE.finditer(piece['text']):
    identities=citation_identity(match,keys,oldrefs)
    event={'body_child_index':block['body_child_index'],**piece['location'],'offset':match.start(),'token':match.group(),'identities':identities}
    occurrences.append(event)
    for identity in identities:
     if identity not in first:first[identity]=event;ordering.append(identity)
 assert all_fields==set(staged['measurement_fields']) and len(all_fields)==39
 numbers_by_identity={identity:i+1 for i,identity in enumerate(ordering)}
 def renumber(text):
  def repl(match):
   ids=citation_identity(match,keys,oldrefs)
   return '['+','.join(map(str,sorted(set(numbers_by_identity[x] for x in ids))))+']'
  return CITE.sub(repl,text)
 # Source registry supplies corrected entries only for explicit aliases; unchanged
 # baseline entries retain baseline bibliographic text, not newly invented metadata.
 bibliography=[]
 for identity in ordering:
  if identity.startswith('old:'):
   old=int(identity[4:]);matching=aliases.get(identity,[])
   entries={keys[k]['entry'] for k in matching};assert len(entries)<=1
   entry=next(iter(entries)) if entries else oldrefs[old];source='explicit alias entry' if entries else 'baseline bibliography'
  else:
   old=None;matching=[identity[4:]];entry=keys[matching[0]]['entry'];source='new resolved source key'
  bibliography.append({'new_number':numbers_by_identity[identity],'identity':identity,'old_number':old,'source_keys':matching,'entry':entry,'entry_source':source,'first_appearance':first[identity]})
 removed=[{'old_number':n,'baseline_body_p_index':ref_positions[n],'entry':oldrefs[n]} for n in oldrefs if 'old:'+str(n) not in numbers_by_identity]
 unusedkeys=[key for key,item in keys.items() if ('old:'+str(item['existing_number']) if item.get('existing_number') is not None else 'new:'+key) not in numbers_by_identity]
 # Structural inventory for a future OOXML-preserving builder.
 relroot=E.fromstring(parts['word/_rels/document.xml.rels']);rels={r.get('Id'):dict(r.attrib) for r in relroot}
 drawings=[]
 for i,p in enumerate(ps):
  if not p.xpath('.//w:drawing|.//w:pict',namespaces=NS):continue
  images=[]
  for rid in p.xpath('.//a:blip/@r:embed|.//v:imagedata/@r:id',namespaces=NS):
   rel=rels[rid];target='word/'+rel['Target'];assert target in parts
   images.append({'relationship_id':rid,'relationship':rel,'part':target,'part_sha256':sha(parts[target]),'byte_n':len(parts[target])})
  drawings.append({'body_p_index':i,'paragraph_xml':xmlbind(p),'images':images,'drawing_ids':p.xpath('.//wp:docPr/@id',namespaces=NS),'drawing_names':p.xpath('.//wp:docPr/@name',namespaces=NS),'extent_emu':[dict(x.attrib) for x in p.xpath('.//wp:extent',namespaces=NS)],'adjacent_caption_indices':[i+1,i+2]})
 assert [x['body_p_index'] for x in drawings]==[33,64]
 section=[]
 for x in document.findall('.//w:sectPr',NS):
  section.append({**xmlbind(x),'xml':xmlbytes(x).decode(),'page_size_twips':{E.QName(k).localname:v for k,v in x.find('w:pgSz',NS).attrib.items()},'page_margins_twips':{E.QName(k).localname:v for k,v in x.find('w:pgMar',NS).attrib.items()},'columns':[dict(q.attrib) for q in x.findall('w:cols',NS)]})
 preserve_tables=[]
 for num in [1,4]:
  node=tables[num-1];preserve_tables.append({'table_number':num,**xmlbind(node),'rows':[[plain(c) for c in r.findall('w:tc',NS)] for r in node.findall('w:tr',NS)],'table_properties_xml':xmlbytes(node.find('w:tblPr',NS)).decode(),'table_grid_xml':xmlbytes(node.find('w:tblGrid',NS)).decode(),'exact_preservation_expected':True,'citation_marker_update_only_if_citations_present':True,'citation_n':sum(len(CITE.findall(plain(c))) for c in node.findall('.//w:tc',NS))})
 # Defined but still-unbound final payload contracts; this preflight performs no
 # measurement filling and does not read candidate run directories.
 metrics=['kappa','precision','recall','f1'];dims=['S','E','Ec','I','F'];groups=['NMPA','NHSA','NHC']
 table2={'status':'pending_adopted_complete_statistics','row_n_excluding_header':10,'columns':['维度','方法','κ（A/C）','P（A/C）','R（A/C）','F1（A/C）'],'selector':{'component':'probability_canonical','group':'ALL','weighting':'eligible_design_weighted','references':['A','C'],'dimensions':dims,'methods':'exact adopted rules and LLM method keys'},'cell_contracts':[{'dimension':d,'method_role':m,'metric':metric,'references':['A','C'],'format':'A/C original decimal units;null→NA; never multiply P/R by100','statistical_paths':{ref:'comparisons[component=probability_canonical,group=ALL,weighting=eligible_design_weighted,method=ADOPTED_'+m.upper()+',reference='+ref+',dimension='+d+'].metrics.'+metric+'.estimate' for ref in ['A','C']}} for d in dims for m in ['rules','LLM'] for metric in metrics],
 'metric_object_keys':['estimate','ci95_primary','ci95_source_file_conditional_sensitivity'],'primary_CI_keys':['low','high','defined_repetitions','undefined_repetitions'],'CI_selection_rule':'Use sibling ci95_primary on the same metric object; never source-file conditional sensitivity as primary. Each probability metric requires defined_repetitions+undefined_repetitions=5000 and explicit point NA reason when estimate is null.','required_metric_points':80,'required_bound_CI_pairs':80,'CI_binding':'Every point and its ci95_primary must come from the same adopted bundle;5000 department_unit_rescaled_SRSWOR;candidate/department/challenge separately retained in supplement. Do not take candidate02 intervals for03.','raw_cells_required':True,'paired_n_expected':180,'design_N_by_department':{'NMPA':947,'NHSA':760,'NHC':60},'all240_development_exposure':True,'legacy_main1057_or_percent_PR_allowed':False}
 table3={'status':'pending_adopted_complete_full_corpus_statistics','row_n_excluding_header':6,'dimensions':dims,'row_keys':[{'department':g,'method_role':m} for g in groups for m in ['rules','LLM']],'unit_n_by_department':{'NMPA':1848,'NHSA':2100,'NHC':533},'scope_n':4481,'exclude_GOV_n':443,'machine_full_output_n_required':4924,'q_definition':'q_d=coding_count_d/sum_five_dimension_coding_counts;percentage=100q; no sample design weighting','required_q_n':30,'required_denominator_n':6,'rounding':'table2 decimal metrics3places; table3 q percent2places; figure2percent1place. Five exact shares sum1; displayed rounding may not sum100.','must_not_include':'A/C/candidate probability estimates or1057legacy rows','full_numerators_denominators_and_input_output_sha_required':True}
 adoption={'status':'PENDING_COMPLETE_METHOD_ADOPTION','root_adopted_methods_confirmed':False,'material_version':None,'shared_material_binding':None,'reference_binding':None,'sampling_design_binding':None,'methods':{'rules':{'method_id':None,'full4924_output_binding':None,'execution_QA_binding':None,'code_freeze_binding':None},'LLM':{'method_id':None,'full4924_output_binding':None,'full_execution_QA_binding':None,'actual_request_prompt_runtime_lineage_binding':None,'first_valid_attempt_policy_verified':False,'all_failures_preserved':False,'stability_scope_or_explicit_not_assessed':None}},'statistics':{'complete_unit_classification_bundle':None,'same180_attention_bundle':None,'full4481_attention_bundle':None,'all10_pair_cooccurrence_bundle':None,'definition6_bundle':None,'file_composition56_bundle':None,'independent_point_QA':None,'CI_mathematical_QA':None,'same_adopted_output_sha_everywhere':False},'semantic_validation_status':'development_only_all240_exposed; true-human validation pending','render_and_full_reference_QA':None,'figure2_new_data_and_render_binding':None}
 fields={name:{'status':'UNFILLED','value':None,'occurrences':field_occurrences[name],'required_binding':'exact adopted method/statistical bundle and JSON pointer; prose direction summaries require full-scenario check','may_substitute_legacy_value':False} for name in sorted(all_fields)}
 blockers=[{'code':'UNFILLED_39_PROSE_FIELDS','count':39,'fields':sorted(all_fields)},{'code':'ADOPTED_RULES_AND_LLM_COMPLETE_BINDINGS_NOT_CONFIRMED'},{'code':'TABLE_2_NEW_PROBABILITY180_CONTRACT_UNFILLED'},{'code':'TABLE_3_NEW_FULL4481_CONTRACT_UNFILLED'},{'code':'FIGURE_2_REQUIRES_ADOPTED_BOTH_METHODS_REDRAW'},{'code':'FINAL_DOCX_RENDER_AND_REFERENCE_QA_NOT_PERFORMED'}]
 part_inventory={name:{'sha256':sha(value),'bytes':len(value),'preservation_rule':('future controlled document edits only' if name=='word/document.xml' else 'figure2 media replacement only after new render binding' if name=='word/media/image4.png' else 'preserve byte-for-byte unless explicit rendering need with audited diff')} for name,value in parts.items()}
 preservation={'baseline':bind(BASE),'part_inventory':part_inventory,'body_paragraph_n':173,'direct_body_table_n':4,'body_order':[{'body_child_index':i,'tag':E.QName(x).localname} for i,x in enumerate(body)],'preserved_table_1_4':preserve_tables,'section_settings':section,'document_relationships':rels,'drawings':drawings,'figure_contracts':staged['figure_contracts'],
 'orphan_or_other_media_relationships':[{'id':rid,**rel} for rid,rel in rels.items() if rel['Type'].endswith('/image') and rid not in {i['relationship_id'] for d in drawings for i in d['images']}],
 'paragraph_structure_preservation':[{'index':i,'pPr_xml':xmlbytes(p.find('w:pPr',NS)).decode() if p.find('w:pPr',NS) is not None else None,'drawing_n':len(p.xpath('.//w:drawing|.//w:pict',namespaces=NS)),'bookmark_start_ids':p.xpath('.//w:bookmarkStart/@w:id',namespaces=NS)} for i,p in enumerate(ps)],
 'future_preservation_notes':['Preserve pPr and relevant run formatting, drawing anchors, relationship IDs, table1/4 grids/borders and section settings. New bibliography can change reference paragraph count.','No XML serialization or ZIP write is performed now. Figures are relationship inventory only; figure1 semantic/visual consistency still requires final render check.','image1.png/image2.png relationships exist but are not referenced by the two current body drawings; preserve them, do not silently delete package parts.']}
 # Preview is one document-order text reconstruction, retains all39 fields and
 # substitutes contract markers for the two old statistical tables and old figure2.
 preview=['# 全文接入文本预览：未成稿、全部39字段仍待填','','此文件仅将52段局部替换与未改正文按OOXML实际顺序拼接，并模拟引用重排。表2/3不带入旧值；图2旧图不作为新证据。不能用于投稿或替代最终DOCX。','']
 for block in blocks:
  if block['kind']=='paragraph':
   i=block['body_p_index'];text=renumber(block['text'])
   if i==33:preview+=['[图1位置：保留rId3 → word/media/image3.png；待最终图文核验]','']
   elif i==64:preview+=['[图2位置：原rId4 → word/media/image4.png，待按最终采用两方法新数据重绘；旧图未嵌入此预览]','']
   if text:preview += [text,'']
  elif block['kind']=='preserved_table':
   num=block['table_number'];table=tables[num-1];matrix=[[renumber(plain(c)) for c in tr.findall('w:tc',NS)] for tr in table.findall('w:tr',NS)]
   preview+=['|'+ '|'.join(x.replace('|','\\|') for x in matrix[0])+'|','|'+'|'.join('---' for _ in matrix[0])+'|']
   preview+=['|'+ '|'.join(x.replace('|','\\|') for x in row)+'|' for row in matrix[1:]];preview.append('')
  else:preview+=['[表'+str(block['table_number'])+'待填：'+block['contract']+'；禁止沿用基稿旧统计表]','']
 preview+=['参考文献（仅为本次文本预览按首次出现模拟排序；真实DOCX尚未改号）','']
 for row in bibliography:preview.append('['+str(row['new_number'])+'] '+row['entry'])
 preview_text='\n'.join(preview)+'\n';assert set(FIELD.findall(preview_text))==all_fields
 assert not re.search(r'1057|97\.22|5000次文件聚类bootstrap|按来源文件聚类的bootstrap',preview_text),'legacy substantive values remain in staged preview'
 report={'status':'PREVIEW_PREFLIGHT_PASS_MANUSCRIPT_GENERATION_BLOCKED','created_at':datetime.datetime.now().astimezone().isoformat(),'inputs':{str(p):{'path':str(p),'sha256':initial[str(p)]} for p in inputs},'read_only_DOCX':True,'no_DOCX_generated_or_modified':True,'no_partial_LLM03_read':True,'this_script_reads_no_predictions_labels_or_statistics':True,'measurement_values_filled':0,'baseline_sha_pass':True,'body_paragraph_n':173,'table_n':4,'replacements_n':len(replacements),'all_old_text_hash_checks_pass':True,'replacement_checks':checked,'unfilled_unique_prose_field_n':39,'reference_old_entry_n':62,'newly_numbered_used_reference_n':len(bibliography),'unused_old_reference_n':len(removed),'unused_old_reference_numbers':[r['old_number'] for r in removed],'unresolved_citation_source_keys':[],'unused_source_keys':unusedkeys,'preserved_table_cell_citation_n':sum(t['citation_n'] for t in preserve_tables),'bibliography_first_appearance_policy':'actual body order, including table1/4 cell paragraphs and their surrounding source notes; exclude old bibliography; table2/3 replaced by new contracts','manuscript_generation_allowed':False,'blocking_reasons':blockers,'statistical_contracts':{'table2':table2,'table3':table3},'warning':'Citation number mapping is a preflight plan only. No final manuscript is produced until all39 fields, actual adopted method QA, new tables/figure2 and render checks are complete. Recompute first-appearance numbering after any change in prose, citations, table notes or field text; the preview numbering is not a permanent assignment.'}
 for path,h in initial.items():assert sha(Path(path).read_bytes())==h,'Input changed during preflight: '+path
 args.out.mkdir(parents=True,exist_ok=False)
 outputs={'接入预检结果.json':report,'引用重排与未用文献清单.json':{'used_bibliography':bibliography,'old_number_to_new':{str(n):numbers_by_identity.get('old:'+str(n)) for n in oldrefs},'source_key_to_new':{key:numbers_by_identity.get('old:'+str(x['existing_number']) if x.get('existing_number') is not None else 'new:'+key) for key,x in keys.items()},'citation_occurrences':occurrences,'unused_old_entries':removed,'unused_source_keys':unusedkeys},'OOXML保留清单.json':preservation,'统计表接入契约.json':{'table2':table2,'table3':table3,'sample_attention':staged['table_contracts']['sample_attention_supplement']},'39字段待填契约.json':fields,'最终采用方法绑定_PENDING模板.json':adoption}
 for name,obj in outputs.items():write(args.out/name,obj)
 (args.out/'全文接入预览_未成稿.md').write_text(preview_text)
 write(args.out/'output_freeze.json',{'files':{p.name:sha(p.read_bytes()) for p in args.out.iterdir() if p.is_file()},'script':bind(Path(__file__))})
 print(json.dumps({k:report[k] for k in ['status','all_old_text_hash_checks_pass','unfilled_unique_prose_field_n','newly_numbered_used_reference_n','unused_old_reference_numbers','manuscript_generation_allowed']},ensure_ascii=False))
 if args.require_manuscript_ready:raise SystemExit(2)

if __name__=='__main__':main()
