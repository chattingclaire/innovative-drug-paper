"""Versioned source assets/indexes; no labels, semantic certificates, or models."""
from pathlib import Path
import copy,hashlib,json,re,os,unicodedata,importlib.util
from collections import Counter,defaultdict
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2];PARENT=OUT.parent
sp=importlib.util.spec_from_file_location('preflight',OUT/'build_full_frame_preflight_v2.py');pr=importlib.util.module_from_spec(sp);sp.loader.exec_module(pr)
sha=pr.sha;sf=pr.shafile;write=pr.write;dump=pr.dump;jl=pr.jsonl;norm=pr.norm;famnorm=pr.famnorm
F={r['id']:r for r in pr.readrows(ROOT/'00-baseline/source-only-frame.jsonl')};mf=json.loads((ROOT/'00-baseline/source_files_manifest.json').read_text());BS={r['sha256']:r for r in mf['files']};BP={r['original']:r for r in mf['files']};side={r['id']:r for r in pr.readrows(pr.SIDE) if r['id'] in F}
oldpath=OUT/'canonical_source_context-v2.jsonl';oldhash=sf(oldpath);data=pr.readrows(oldpath);changes=[];images={};rels=[];newnodes=[]
def asset(path,s,kind,source_sha=None,page=None,url=None):
 p=Path(path);assert sf(p)==s;dest=OUT/'source-assets'/('SOURCEIMAGE-'+s+p.suffix.lower());write(dest,p.read_bytes());images[s]={'sha256':s,'snapshot':str(dest),'original_path':str(p),'kind':kind,'primary_source_sha256':source_sha,'physical_page':page,'source_url':url,'primary_page_correspondence_visual_verified':False};a={'attachment_id':'SOURCEIMAGE-'+s[:20],'sha256':s,'relative_path':str(dest.relative_to(OUT)),'kind':kind}
 if source_sha:a['source_pdf_sha256']=source_sha
 if page:a['physical_page']=page
 if url:a['source_url']=url
 return a
# Source images below were actually opened by this agent. Complete visual source
# text is typed independently from pixels and compared only by source/text SHA.
image_texts={
'1d2fcb36c01edb23':'专项行动之一：手术质量安全提升行动\n通过专项行动，降低手术并发症、麻醉并发症、围手术期死亡等负性事件发生率，及时发现和消除手术质量安全隐患。到2025年末，日间手术占择期手术的比例进一步提升，全国三级医院手术患者住院死亡率明显下降、非计划重返手术室再手术率不高于1.8‰，住院患者手术后获得性指标发生率不高于7.5‰，全面落实四级手术术前多学科讨论制度。',
'db12af92db9aa44f':'专项行动之二：“破壁”行动\n聚焦心、脑血管疾病，恶性肿瘤等发病率高、严重危害人民群众健康的重大疾病，结合本地居民疾病谱和异地就医流向情况，在保障医疗安全的基础上优化要素配置和运行机制。到2025年末，在冠心病、脑卒中、乳腺癌、肺癌、结直肠癌等专病的诊疗模式和组织形式有创新性突破。全国急性ST段抬高型心肌梗死再灌注治疗率提升至80%；全国急性脑梗死再灌注治疗率提升至45%。',
'1b0fc72c47f1c2e7':'专项行动之三：病历内涵质量提升行动\n以教育培训、质控抽查、优秀病案评比和宣传交流为主要方式，引导医疗机构落实国家病历书写、管理和应用的相关规定，强化病历内涵意识，提升病历客观、真实、准确、及时、完整、规范水平，更好体现临床诊疗思维和过程。到2025年末，病案首页主要诊断编码正确率不低于90%，病历记录完整性和及时性进一步提高，评选全国百佳病案并开展巡讲。',
'ca5554fcd5b3f7e9':'专项行动之四：患者安全专项行动\n医疗机构开展全员参与覆盖诊疗服务、基础设施、应急处置全过程的安全隐患排查行动，优化应急预案并加强演练。强化非惩罚性报告机制，提高识别能力，优化报告途径，鼓励医务人员报告不良事件，塑造良好的质量安全氛围。到2025年末，每百出院人次主动报告不良事件年均大于2.5例次。',
'7c74dc852434f34c':'专项行动之五：“织网”行动\n到2025年末，设置完成不少于60个专业的国家级质控中心，不少于10个中医专业国家级质控中心；不少于1800个省级质控中心，不少于300个省级中医质控中心；不少于1.8万个地市级质控中心（组织），不少于1800个地市级中医质控中心。质控工作逐步覆盖住院、日间、门（急）诊等全诊疗人群。其中，心血管疾病、神经系统疾病、肿瘤、麻醉、重症、药事、院感、护理等专业质控中心（组织）实现地市级全覆盖，并延伸至50%以上县域。全国纳入单病种管理的病种（技术）数量不少于100个，发布年度省级医疗服务与质量安全报告的省份不少于20个，各专业国家级质控中心按年度发布本专业医疗服务与质量安全报告。'}
visual_checked=[];table_source=next(s for s in BS if s.startswith('09d813b3'));tables=json.loads(Path(BS[table_source]['snapshot']).read_text())['tables']
table_images={t['source_sha256']:asset(t['source_image'],t['source_sha256'],'original_source_table_image',url=t['source_url']) for t in tables}
table_geometry={
0:{'physical_merged_cells':[{'text':'5.1','column_index':0,'physical_grid_row_start_zero_based':6,'physical_grid_row_span':2,'physical_grid_column_span':1},{'text':'境外上市的药品申请在境内上市','column_index':1,'physical_grid_row_start_zero_based':5,'physical_grid_row_span':1,'physical_grid_column_span':2}], 'group_row':{'physical_grid_row_index_zero_based':5,'row_cells':['5类','境外上市的药品申请在境内上市','','']}},
1:{'physical_merged_cells':[{'text':'3类','column_index':0,'physical_grid_row_start_zero_based':3,'physical_grid_row_span':3,'physical_grid_column_span':1}]},
2:{'physical_merged_cells':[{'text':'3类','column_index':0,'physical_grid_row_start_zero_based':3,'physical_grid_row_span':4,'physical_grid_column_span':1}]}}
for row in data:
 rid=row['id'];nodes=row['contexts'];bycid={n['context_id']:n for n in nodes};ats={a['attachment_id']:a for a in row.get('source_attachments',[])};neutral=[]
 # NR is an opaque locator/reference. Preserve the associated pure source
 # metadata too, deleting all legacy raw_pointer certificate paths.
 for original in side[rid].get('neutral_relations',[]):
  r={k:copy.deepcopy(original[k]) for k in ['relation_id','kind','related_context_ids','unit_id','candidate_sha256','paragraph_ids','related_unit_ids'] if k in original}
  if original['kind']=='image_source_metadata':
   r['image_sources']=[]
   relatedsources={bycid[c]['source_ref']['sha256'] for c in r.get('related_context_ids',[]) if c in bycid};ss=next(iter(relatedsources)) if len(relatedsources)==1 else None
   for img in original['image_sources']:
    at=asset(img['path'],img['sha256'],'historical_source_page_image',ss);ats[at['attachment_id']]=at;r['image_sources'].append({'sha256':img['sha256'],'attachment_id':at['attachment_id'],'primary_source_sha256':ss})
  neutral.append(r);rels.append({'record_id':rid,**r})
 if neutral:row['source_relations']=neutral
 # Every table retains the selected row, actual merged parent class, headings,
 # original full image and existing column/header references. No label hint.
 for node in list(nodes):
  if node['kind']!='table_row' or node['source_ref']['sha256']!=table_source:continue
  matches=[(ti,t,ri) for ti,t in enumerate(tables) for ri,cells in enumerate(t['rows']) if node.get('row_cells')==cells and node.get('title')==t['title']]
  if len(matches)!=1:continue
  ti,t,ri=matches[0];geo=copy.deepcopy(table_geometry[ti]);physical=ri+1+(1 if ti==0 and ri>=4 else 0)
  additions={'physical_grid_row_index_zero_based':physical,'grid_row_index_convention':'0 denotes original header row; merged cells preserved','table_index_zero_based':ti,'physical_merged_cells':geo['physical_merged_cells'],'source_image_sha256':t['source_sha256']}
  if ti in {1,2} and ri>=2:
   additions['original_selected_row_cells']=['3类',t['rows'][ri][0].split('/')[-1]+' '+t['rows'][ri][1],t['rows'][ri][2],t['rows'][ri][3]]
   additions['flattened_class_cell_convention']='Existing class/child form serializes merged column0 parent class and the child numeral printed at the start of original column1.'
  if ti==0 and ri>=4:
   g=geo['group_row'];cid='CTX-SRCFULL-'+sha((t['source_sha256']+'/group_row5').encode())[:20];gn={'context_id':cid,'kind':'table_group_row','source_document':'D-'+table_source[:16],'structure':{'parent_context_id':node['context_id'],'physical_grid_row_index_zero_based':5,'column_indices':[0,1,2,3]},'row_cells':g['row_cells'],'text':'5类 | 境外上市的药品申请在境内上市','source_ref':{'sha256':table_source,'locator':{'json_pointer':'/tables/0/group_context/5类','source_image_sha256':t['source_sha256'],'physical_grid_row_index_zero_based':5}}};nodes.append(gn);bycid[cid]=gn;newnodes.append({'record_id':rid,**gn});additions['source_group_context_id']=cid
  node['structure'].update(additions);node['source_ref']['locator'].update(copy.deepcopy(additions));ats[table_images[t['source_sha256']]['attachment_id']]=table_images[t['source_sha256']]
  changes.append({'record_id':rid,'context_id':node['context_id'],'operation':'add_actual_source_table_row_and_merge_geometry','source_image_sha256':t['source_sha256'],'source_JSON_sha256':table_source,'table_index_zero_based':ti,'old_row_cells_retained':True,'additions':additions})
 # Full checked NHC source images; retain original body/context transcription.
 used={row['source_ref']['sha256']}|{n['source_ref']['sha256'] for n in nodes}
 for s in used:
  if s and s[:16] in image_texts:
   at=asset(BS[s]['snapshot'],s,'original_source_policy_image',s);ats[at['attachment_id']]=at
   if norm(row['text']) in norm(image_texts[s[:16]]) and row['source_ref']['sha256']==s:visual_checked.append({'record_id':rid,'context_id':None,'field':'text','source_sha256':s,'text_sha256':sha(row['text'].encode())})
   for n in nodes:
    if n['source_ref']['sha256']!=s:continue
    for f,text in pr.pr.text_values(n):
     if norm(text) in norm(image_texts[s[:16]]):visual_checked.append({'record_id':rid,'context_id':n['context_id'],'field':f,'source_sha256':s,'text_sha256':sha(text.encode())})
 if ats:row['source_attachments']=list(ats.values())
 # Neutral uniform source resource IDs resolve to snapshot registry below.
 for ref in [row['source_ref']]+[n['source_ref'] for n in nodes]:ref['source_resource_id']='SOURCE-'+ref['sha256'] if ref['sha256'] else None
 rids={r['relation_id'] for r in neutral};cids=set(bycid)
 for node in nodes:
  for _,cid in pr.pr.context_references(node):assert cid in cids,(rid,cid)
  for k in ['relation_id','image_evidence_ref']:
   v=node['structure'].get(k)
   if isinstance(v,str) and v.startswith('NR-'):assert v in rids,(rid,k,v)
 for r in neutral:assert set(r.get('related_context_ids',[]))<=cids
assert not list(pr.forbidden(data))
path=OUT/'canonical_source_context-v3.jsonl';jl(path,data);assert sf(oldpath)==oldhash
dump(OUT/'source-assets-manifest-v3.json',{'files':list(images.values()),'original_NMPA_three_table_images_visual_reviewed':True,'raw_NHC_five_images_visual_reviewed':True,'historical_source_images_byte_verified':True,'historical_images_not_claimed_new_primary_binary_authentication':True})
dump(OUT/'source-visual-review-v3.json',{'reviewer_kind':'AI source authenticity reviewer; not human coder','source_image_transcriptions':[{'source_sha256':next(s for s in BS if s.startswith(pre)),'text':t,'text_sha256':sha(t.encode()),'image_snapshot':BS[next(s for s in BS if s.startswith(pre))]['snapshot']} for pre,t in image_texts.items()],'checked_source_field_occurrences':visual_checked,'data_protection_table_geometry':table_geometry,'no_dimension_or_label_judgment':True,'FAQ2026_physical_pages_opened':[9,10,12],'FAQ2026_graph2_full_transcription_authentication_completed':False})
checked={(v['record_id'],v['context_id'],v['field'],v['source_sha256'],v['text_sha256']) for v in visual_checked}
oldissues=pr.readrows(OUT/'source-exceptions-v2.jsonl');pending=[v for v in oldissues if (v['record_id'],v['context_id'],v['field'],v['source_sha256'],v['text_sha256']) not in checked];jl(OUT/'source-exceptions-v3.jsonl',pending)
bodyqa=pr.readrows(OUT/'body-source-QA-v2.jsonl');contextqa=pr.readrows(OUT/'context-source-QA-v2.jsonl')
for q in bodyqa:
 if (q['record_id'],None,'text',q['primary_source_sha256'],q['projected_body_sha256']) in checked:q['literal_status']='AI_visual_original_image_and_independent_transcription_correspondence';q['source_visual_review']='source-visual-review-v3.json'
for q in contextqa:
 for f in q['policy_text_fields']:
  if (q['record_id'],q['context_id'],f['field'],q['primary_source_sha256'],f['projected_text_sha256']) in checked:f['literal_status']='AI_visual_original_image_and_independent_transcription_correspondence';f['source_visual_review']='source-visual-review-v3.json'
jl(OUT/'body-source-QA-v3.jsonl',bodyqa);jl(OUT/'context-source-QA-v3.jsonl',contextqa)
# Byte-bound primary document identity; verbatim title-line candidates are kept
# distinct from frame stems and path year literals. No guessed source year/title.
usedshas={r['source_ref']['sha256'] for r in data}|{n['source_ref']['sha256'] for r in data for n in r['contexts']};identities=[];yeard={}
for s in sorted(usedshas):
 if not s:continue
 e=BS[s];txt,method=pr.pr.extract_snapshot_text(e['snapshot']);wt,wm,_=pr.word_source(e['snapshot'])
 if wt is not None:txt,method=wt,wm
 years=sorted({int(y) for y in re.findall(r'(?<!\d)((?:19|20)\d{2})(?!\d)',e['original'])});yeard[s]=years
 titles=[l.strip() for l in (txt or '').split('\f')[0].splitlines() if l.strip()][:18]
 identities.append({'source_resource_id':'SOURCE-'+s,'source_sha256':s,'snapshot':e['snapshot'],'original_path':e['original'],'snapshot_relative_to_projection':os.path.relpath(e['snapshot'],OUT),'bytes':e['bytes'],'byte_SHA_verified':True,'source_title_lines_verbatim_extraction_candidates':titles,'source_title_lines_extraction_method':method,'document_year_literals_in_recorded_original_path':years,'document_year_established':years[0] if len(years)==1 else None,'recorded_frame_document_stems':sorted({F[r['id']]['source_document_stem'] for r in data if r['source_ref']['sha256']==s}),'source_version_id':'SOURCEVERSION-'+s,'no_title_or_department_used_as_label':True})
jl(OUT/'source-document-identities-v3.jsonl',identities)
refs=[]
for r in data:
 bycid={n['context_id']:n for n in r['contexts']}
 for n in r['contexts']:
  if n['kind']!='cited_reference':continue
  members=[bycid[c] for g in n['structure'].get('child_groups',[]) if g['position']=='contexts' for c in g['ordered_context_ids'] if c in bycid];ss=sorted({z['source_ref']['sha256'] for z in members});cur=r['source_ref']['sha256'];cy=yeard.get(cur,[]);tys=[yeard.get(s,[]) for s in ss]
  refs.append({'record_id':r['id'],'reference_context_id':n['context_id'],'reference_address_locator':n['structure'].get('reference_address'),'current_primary_source_sha256':cur,'current_document_year_literals':cy,'cited_primary_source_sha256s':ss,'cited_document_year_literals':tys,'cited_original_context_ids':[z['context_id'] for z in members],'cited_source_refs':[z['source_ref'] for z in members],'single_calendar_year_identity_matches':len(cy)==1 and all(y==cy for y in tys) if tys else None,'same_edition_not_established_by_year_match_alone':True,'reference_source_locator_not_semantic_support_certificate':True})
jl(OUT/'explicit-source-reference-index-v3.jsonl',refs)
# Material binding updates include generated geometry, without changing rows.
rm=pr.readrows(OUT/'material-record-bindings-v2.jsonl');bd={r['id']:r for r in data}
for b in rm:
 r=bd[b['id']];b['projected_context_sha256']=sha(pr.canonical(r['contexts']).encode());b['projected_record_sha256']=sha(pr.canonical(r).encode());assert b['projected_body_sha256']==sha(r['text'].encode())
jl(OUT/'material-record-bindings-v3.jsonl',rm);family=json.loads((OUT/'family-exposure-impact-v2.json').read_text());family['source_projection_v3_sha256']=sf(path);family['v2_and_v3_bodies_byte_identical']=True;dump(OUT/'family-exposure-impact-v3.json',family)
dump(OUT/'source-changes-v3.json',{'preserved_v2':{'path':str(oldpath),'sha256':oldhash},'v3':{'path':str(path),'sha256':sf(path)},'unit_texts_v2_to_v3_unchanged':True,'all_original_24655_contexts_and_IDs_retained':True,'source_relation_metadata_N':len(rels),'original_NRs_resolve_within_row':True,'new_table_group_context_N':len(newnodes),'changes':changes})
pendingby=defaultdict(list)
for v in pending:pendingby[v['source_sha256']].append(v)
dump(OUT/'machine-human-interface-gaps-v3.json',{'status':'literal_and_geometry_gaps_recorded; not_zero_dimension_labels','source_only_QA_not_manual_development':True,'resolved_original_interface_omissions':{'opaque_NR_image_references_without_image_metadata':47,'actual_snapshot_images_added':5,'NMPA_full_original_table_images_added':3,'Word_attachment_row_header_merge_geometry_added_records':40,'NMPA_table_rows_actual_geometry_added':len(changes),'NHC_source_original_images_added':5},'known_remaining_or_pending':[{'source_sha256':s,'source_snapshot':BS[s]['snapshot'],'pending_occurrence_N':len(vs),'pending_unique_source_text_N':len({v['text_sha256'] for v in vs}),'body_pending_N':sum(v['context_id'] is None for v in vs),'reason':'Scanned/table/graph/page-layout or literal extraction gap. Existing text kept; original source resource remains accessible. No semantic outcome inferred.','machine_text_vs_human_image_completeness_certified':False,'all_pending_ids':sorted({v['record_id'] for v in vs})} for s,vs in pendingby.items()],'freeze_gate':'Before final human/machine validation freeze, material construction must resolve or explicitly mark all chosen units source insufficiencies, provide the same source content via stable source-resource IDs, and record parse/undetermined exclusions rather than using zero labels. No final sample is drawn here.','human_image_can_contain_substantive_content_not_yet_equivalently_transcribed_in_machine_JSON':True,'no_claim_all_graph_geometry_or_source_table_text_is_now_machine_equivalent':True})
qa=json.loads((OUT/'source-QA-summary-v2.json').read_text());qa.update({'status':'full_frame_source_only_v3_preflight_complete_with_explicit_pending_source_and_interface_gaps','output':{'path':str(path),'sha256':sf(path)},'source_identity_N':len(identities),'explicit_cited_reference_N':len(refs),'neutral_source_relation_metadata_N':len(rels),'source_relation_metadata_types':dict(Counter(r['kind'] for r in rels)),'all_CTX_and_NR_recursive_references_resolve':True,'actual_output_context_N':sum(len(r['contexts']) for r in data),'new_Word_geometry_context_N':40,'new_NMPA_table_group_context_N':len(newnodes),'new_AI_visual_source_field_checks_N':len(visual_checked),'pending_issue_N':len(pending),'pending_issue_types':dict(Counter(r['issue_type'] for r in pending)),'pending_unique_source_text_N':len({(r['source_sha256'],r['text_sha256']) for r in pending}),'preserved_v2_sha256':oldhash,'v3_unit_texts_unchanged_from_v2':True,'all_body_SHA_bindings_current':True,'machine_human_source_content_equivalence_complete':False,'final_material_freeze_completed':False,'all_original_24655_CTX_retained':True,'outputs':[{'path':str(p),'sha256':sf(p)} for p in sorted(OUT.glob('*-v3.json*'))]});dump(OUT/'source-QA-summary-v3.json',qa)
print(json.dumps({k:qa[k] for k in ['actual_output_context_N','source_identity_N','explicit_cited_reference_N','neutral_source_relation_metadata_N','new_AI_visual_source_field_checks_N','pending_issue_N','pending_unique_source_text_N','output']},ensure_ascii=False,indent=2))
