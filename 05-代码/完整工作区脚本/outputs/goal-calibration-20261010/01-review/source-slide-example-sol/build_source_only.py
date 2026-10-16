from pathlib import Path
import json,hashlib,struct,datetime,subprocess
from zoneinfo import ZoneInfo
R=Path('/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010')
B=R/'01-review/context-projection-sol/full-frame-preflight'
O=R/'01-review/source-slide-example-sol'
H=['1be84453158f1e9232c845d36577b9055e87c03ea9a39c7415032ffc7d49ff54','da218af12c655b8b8a3156529820b7d12545decc2f9799dfb70272565408c877']
def sh(b):return hashlib.sha256(b).hexdigest()
def dump(name,x):
 with (O/name).open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
entries=[json.loads(s) for s in (B/'source-library/library-v11.jsonl').read_text().splitlines() if any(h in s for h in H)]
entries.sort(key=lambda e:H.index(e['source_sha256']))
g=json.loads((B/'source-material-gaps-v11.json').read_text())
def find(x):
 if isinstance(x,dict):
  if x.get('issue_id')=='SOURCE-GAP-SLIDE-EXAMPLE-TEXT':return x
  for v in x.values():
   a=find(v)
   if a:return a
 if isinstance(x,list):
  for v in x:
   a=find(v)
   if a:return a
 return None
gap=find(g);assert gap
# All definitions are manually transcribed after viewing each original page and
# same-SHA 300dpi rendering. Code only serializes bounded source regions.
base_instruction='包括但不限于：药品通用名称；注册规格；说明书适应症/功能主治（概述）；用法用量；中国大陆首次上市时间；目前大陆地区同通用名药品的上市情况；全球首个上市国家/地区及上市时间；是否为OTC药品；参照药品建议；所治疗疾病基本情况；未满足的治疗需求；大陆地区发病率；年发病患者总数等。'
safety_instruction='包括但不限于：该药品在国内外不良反应发生情况；药品说明书收载的安全性信息；与目录内同类药品安全性方面的主要优势和不足。'
effect_instruction='包括但不限于：临床试验或（和）真实世界中与对照药品疗效方面的主要优势和不足；临床指南/诊疗规范推荐情况；国家药品审评中心出具的《技术评审报告》中关于本药品有效性的描述。'
economy_instruction='包括但不限于：目前的市场价格（如未定，可介绍预期价格）；各省份挂网情况；2020-2022年大陆地区药品销售金额（含全部规格，如非独家，可主要介绍本企业产品的情况）。与目录内同治疗领域药品经济性方面的优势和不足。'
innovation_instruction='包括但不限于：主要创新点；该创新带来的疗效或安全性方面的优势；是否为国家“重大新药创制”科技重大专项支持上市药品；是否为自主知识产权的创新药；传承性（限中成药）情况。'
fair_instruction='包括但不限于：所治疗疾病大陆地区年发病患者总数；是否能够弥补药品目录保障短板；临床管理难度及其他相关情况。'
facts=['通用名：盐酸二甲双胍片。','注册规格：0.5g/片,0.25g/片。','中国大陆首次上市时间：1999年。','目前大陆地区同通用名药品的上市情况：共108家。','全球首个上市国家/地区及上市时间：1957年，美国。','是否为OTC药品：否。','参照药品建议：盐酸吡格列酮片。']
indication='本品首选用于单纯饮食控制及体育锻炼控制血糖无效的2型糖尿病。对于成人，本品可用于单药治疗，也可以与磺脲类药物或胰岛素联合治疗。对于10岁及以上的儿童和青少年，本品可用于单药治疗或与胰岛素联合治疗。'
disease='2型糖尿病是最常见的糖尿病类型，由于多发于成年，又称成人发病型糖尿病。该病由多种病因导致体内胰岛素分泌不足或者胰岛素抵抗致血糖水平升高，可表现为多尿、多饮、多食、消瘦或体重减轻。我国18岁以上成年人，2型糖尿病的发病率占10.4%，60岁以上的老年人患病率高达20%。'
dose='肾功能正常（eGFR≥90mL/min/1.73m²）的成人\n单药治疗以及与磺脲类药物联合治疗\n通常本品的起始剂量为500毫克，每日二次；随餐服用。可每周增加500毫克逐渐加至每日2000毫克，分次服用。成人最大推荐剂量为每日2500毫克。对需进一步控制血糖患者，剂量可以加至每日2500毫克。每日剂量超过2000毫克时，为了更好的耐受，药物最好随三餐分次服用。10至15天后，应根据血糖水平调整剂量。缓慢增加剂量可以改善胃肠道耐受性。'
safety_sample=['不良反应情况：初始治疗时，最常见的不良反应有恶心、呕吐、腹泻、腹痛和食欲不振，大多数患者通常可以自行缓解。','安全性方面优势和不足：XXXX。']
effect_sample=['与对照药品疗效方面优势和不足：XXXX。','临床指南/诊疗规范推荐：中华医学会XXXX指南等，一线推荐。']
economy_sample=['市场价格：**元/片（500mg）；**元/片（250mg）','各省份挂网情况：','2020-2022年大陆地区销售金额：总计**元。','目录内同治疗领域药品经济性优势和不足：XXXX。']
innovation_sample=['创新点:调节肠道菌群。研究发现,对于初始治疗的2型糖尿病患者,使用二甲双胍治疗4个月可以对肠道菌群的组成类别产生重要影响,明确了二甲双胍可以通过调控肠道菌群达到降糖的效果。与二甲双胍的降糖及抗炎机制密切相关。','优势：XXXX。']
fair_sample=['年发病患者总数：XXXX万人。','弥补药品目录短板：弥补了目录内无降糖药的短板。','临床管理难度：患者服药依从性高，临床便于便利等。']
texts=[]; geometry=[]; assets=[]; docs=[]
TOP=[38,73,502,334];LOW=[38,386,502,647]
# Coordinates are manually padded regions in PDF points, top-left origin.
# They are display bounds, not glyph-exact OCR boxes or policy implication links.
def add(e,p,slide,role,key,text,bbox,section=None,notes=None):
 rid='SOURCEVISUAL-'+sh((e['source_sha256']+'|'+str(p)+'|'+str(slide)+'|'+key).encode())[:20]
 asset=next(a for a in e['source_page_assets'] if a['physical_page']==p)
 res={'source_resource_id':rid,'kind':'bounded_visual_source_text','source_sha256':e['source_sha256'],'source_document_resource_id':e['source_resource_id'],'physical_page':p,'printed_page':p,'slide_region_id':slide,'role':role,'section_heading_verbatim':section,'text':text,'text_sha256':sh(text.encode()),'representation':'人工AI逐区域视觉转写；段内视觉换行及字符间排版空格归并，保留段落、数字、否定、例示占位符、上标和原词；不是原PDF完整文字层或原文规范结论。','source_locator':{'coordinate_system':'PDF points, top-left origin','page_size_points':[540,720],'bbox_points_xyxy':bbox,'bbox_status':'visually_verified_manual_padded_region_approximate','original_page_asset_absolute_path':asset['absolute_path'],'original_page_asset_sha256':asset['sha256'],'new_300dpi_asset_relative_path':'pages/'+e['source_sha256'][:16]+'-'+str(p)+'.png','bbox_300dpi_px_xyxy':[round(v*300/72,2) for v in bbox]},'actual_visual_read':True,'uncertain_characters':[]}
 if notes:res['source_preservation_note']=notes
 texts.append(res);return rid
for e in entries:
 h=e['source_sha256'];prefix=h[:16];count=5 if h==H[0] else 4
 b=Path(e['snapshot']).read_bytes();assert sh(b)==h
 doc={'source_resource_id':e['source_resource_id'],'source_sha256':h,'snapshot':e['snapshot'],'snapshot_bytes':len(b),'physical_page_count':count,'page_size_points':[540,720],'attachment_verbatim':'附件2-2' if count==5 else '附件2-3','affected_existing_record_ids':next(x['affected_record_ids'] for x in gap['source_documents'] if x['source_sha256']==h),'source_provenance':'existing_same_SHA_snapshot_pixel_transcription_not_new_external_source','publication_date_status':'未在本限定任务中核公开发布时间；PDF元数据创建时间仅记录为元数据，不推定公告年份。'}
 docs.append(doc)
 for a in e['source_page_assets']:
  original=Path(a['absolute_path']);ob=original.read_bytes();assert sh(ob)==a['sha256']
  high=O/'pages'/f'{prefix}-{a["physical_page"]}.png';hb=high.read_bytes();w,hh=struct.unpack('>II',hb[16:24]);assert [w,hh]==[2250,3000]
  assets.append({'source_sha256':h,'physical_page':a['physical_page'],'printed_page':a['physical_page'],'original_asset_absolute_path':str(original),'original_asset_sha256':a['sha256'],'original_asset_pixels':list(struct.unpack('>II',ob[16:24])),'original_asset_actual_viewed':True,'new_asset_relative_path':str(high.relative_to(O)),'new_asset_sha256':sh(hb),'new_asset_bytes':len(hb),'new_asset_pixels':[w,hh],'new_asset_render_dpi':300,'new_asset_actual_viewed':True,'render_tool':'/opt/homebrew/bin/pdftoppm','render_source_sha_verified':True})
 def slide(p,pos,title,section):
  sid=f'SLIDE-{prefix}-p{p}-{pos}'
  geometry.append({'region_id':sid,'kind':'source_slide_frame','source_sha256':h,'physical_page':p,'printed_page':p,'position':pos,'bbox_points_xyxy':TOP if pos=='upper' else LOW,'coordinate_system':'PDF points, top-left origin','region_bounds_status':'manual_padded_approximate','title_verbatim':title,'section_heading_verbatim':section,'children_resource_ids':[],'layout_relations':[],'interpretation':'纯展示分区与同框关系；无维度标签，不推断样例为规范结论。'})
  return sid
 def reg(p,sid,role,key,text,bbox,section=None,notes=None):
  rid=add(e,p,sid,role,key,text,bbox,section,notes)
  if sid:next(x for x in geometry if x['region_id']==sid)['children_resource_ids'].append(rid)
  return rid
 # Physical page 1: cover and complete table of contents.
 sid=slide(1,'upper','示例封面',None)
 reg(1,sid,'source_attachment_identifier','attachment',doc['attachment_verbatim'],[55,86,108,103])
 reg(1,sid,'illustration_scope_notice','notice','本短片仅做参考',[222,120,315,139],notes='原件为“短片”，不擅自改成“片”或“模板”。')
 reg(1,sid,'example_cover_drug_name','drug','盐酸二甲双胍片',[226,255,314,270])
 reg(1,sid,'example_cover_placeholder','trade','（商品名）',[239,271,302,285])
 reg(1,sid,'example_cover_placeholder','company','企业名称',[247,289,281,303])
 sid=slide(1,'lower','目录',None)
 reg(1,sid,'toc_heading','toc','目录\nCONTENTS',[65,420,151,460])
 toc=['01 药品基本信息','02 安全性','03 有效性','04 经济性','05 创新性','06 公平性'] if count==5 else ['01 药品基本信息','02 安全性','03 有效性','04 创新性','05 公平性']
 bxs=[[207,423,325,451],[363,423,452,451],[216,491,306,520],[363,491,452,520],[216,557,306,588],[363,557,452,588]]
 for i,t in enumerate(toc):reg(1,sid,'toc_item',f'toc-{i+1}',t,bxs[i])
 # Physical page 2: paired instruction/sample above, then three example blocks.
 sid=slide(2,'upper','01 药品基本信息','药品基本信息')
 head=reg(2,sid,'section_heading','heading','01\n药品基本信息\nBasic Information',[92,132,208,221],'药品基本信息')
 ins=reg(2,sid,'body_instruction','instruction',base_instruction,[91,236,286,284],'药品基本信息')
 sampleids=[]
 for i,t in enumerate(facts):sampleids.append(reg(2,sid,'right_side_example',f'fact-{i+1}',t,[322,150+i*15.5,483,163+i*15.5],'药品基本信息'))
 next(x for x in geometry if x['region_id']==sid)['layout_relations'].append({'type':'same_frame_horizontal_instruction_and_example','heading_resource_id':head,'instruction_resource_id':ins,'example_resource_ids':sampleids,'example_is_not_body_instruction':True})
 sid=slide(2,'lower','01 药品基本信息','药品基本信息')
 reg(2,sid,'section_heading','heading','01 药品基本信息',[32,403,204,431],'药品基本信息')
 for key,title,txt,titlebox,bodybox in [('indication','适应症',indication,[109,445,147,460],[109,465,452,489]),('disease','疾病基本情况',disease,[109,506,164,521],[109,525,452,551]),('dose','用法用量',dose,[109,565,150,580],[109,587,453,635])]:
  reg(2,sid,'example_subheading',key+'-heading',title,titlebox,'药品基本信息')
  reg(2,sid,'lower_slide_example',key,txt,bodybox,'药品基本信息',notes='保留原示例语句；本任务不确认其药学正确性或适用现状。' if key=='dose' else None)
 # Page 3: two distinct bounded sections.
 for pos,num,title,en,instruction,samples in [('upper','02','安全性','Security',safety_instruction,safety_sample),('lower','03','有效性','Validity',effect_instruction,effect_sample)]:
  sid=slide(3,pos,num+' '+title,title)
  y=0 if pos=='upper' else 313
  head=reg(3,sid,'section_heading','heading',num+'\n'+title+'\n'+en,[92,132+y,171,221+y],title)
  ins=reg(3,sid,'body_instruction','instruction',instruction,[91,242+y,276,288+y],title)
  ss=[]
  for i,t in enumerate(samples):
   box=([238,142+i*42,473,179+i*42] if pos=='upper' else [215,465+i*16,501,481+i*16])
   ss.append(reg(3,sid,'right_side_example',f'example-{i+1}',t,box,title))
  next(x for x in geometry if x['region_id']==sid)['layout_relations'].append({'type':'same_frame_horizontal_instruction_and_example','heading_resource_id':head,'instruction_resource_id':ins,'example_resource_ids':ss,'example_is_not_body_instruction':True})
 # Remaining sections retain the differing source numbering.
 blocks=[(4,'upper','04','经济性','Economy',economy_instruction,economy_sample),(4,'lower','05','创新性','Innovativeness',innovation_instruction,innovation_sample),(5,'upper','06','公平性','Fairness',fair_instruction,fair_sample)] if count==5 else [(4,'upper','04','创新性','Innovativeness',innovation_instruction,innovation_sample),(4,'lower','05','公平性','Fairness',fair_instruction,fair_sample)]
 for p,pos,num,title,en,instruction,samples in blocks:
  sid=slide(p,pos,num+' '+title,title);y=0 if pos=='upper' else 313
  head=reg(p,sid,'section_heading','heading',num+'\n'+title+'\n'+en,[92,132+y,173,221+y],title)
  insbox=[91,238+y,276,284+y] if title!='公平性' else [91,247+y,273,273+y]
  ins=reg(p,sid,'body_instruction','instruction',instruction,insbox,title)
  ss=[]
  if title=='经济性':boxes=[[240,138,485,154],[240,155,395,170],[240,171,474,186],[240,188,489,204]]
  elif title=='创新性':boxes=[[239,142+y,485,202+y],[239,207+y,314,224+y]]
  else:boxes=[[239,139+y,399,156+y],[239,157+y,485,174+y],[239,175+y,490,192+y]]
  for i,t in enumerate(samples):ss.append(reg(p,sid,'right_side_example',f'example-{i+1}',t,boxes[i],title,notes='“临床便于便利等”为原示例可见文字，照录不改。' if title=='公平性' and i==2 else None))
  next(x for x in geometry if x['region_id']==sid)['layout_relations'].append({'type':'same_frame_horizontal_instruction_and_example','heading_resource_id':head,'instruction_resource_id':ins,'example_resource_ids':ss,'example_is_not_body_instruction':True})
 for p in range(1,count+1):reg(p,None,'printed_page_number','footer',str(p),[522,704,536,720])
# Deliver only additive neutral resources. No existing canonical body is edited.
now=datetime.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
identity={'identity_type':'AI','agent':'/root/pilot01_a_sol','model':'GPT-6.1 Sol','reasoning_setting':'ultra','task':'指定两份原PDF九页的来源图文转写核验','is_human':False,'is_label_coding':False,'start_at':'2026-10-10T04:18:58+08:00','end_at':now}
input_manifest={'source_gap_file':{'path':str(B/'source-material-gaps-v11.json'),'sha256':sh((B/'source-material-gaps-v11.json').read_bytes())},'source_library_file':{'path':str(B/'source-library/library-v11.jsonl'),'sha256':sh((B/'source-library/library-v11.jsonl').read_bytes())},'selected_issue_id':gap['issue_id'],'selected_source_sha256':H,'skill':{'path':'/Users/rainbow/.codex/plugins/cache/openai-primary-runtime/pdf/26.909.12148/skills/pdf/SKILL.md','sha256':sh(Path('/Users/rainbow/.codex/plugins/cache/openai-primary-runtime/pdf/26.909.12148/skills/pdf/SKILL.md').read_bytes()),'read_and_announced':True,'read_only_PDF_work_no_authoring_marker_required':True},'read_scope':'只选该gap与library中两源条目、两同SHA PDF和其九原页；未读12条标签、正文/预测或其他政策材料。'}
dump('input-manifest.json',input_manifest)
dump('source-page-assets.json',{'source_pdf_N':2,'physical_page_N':9,'actual_original_page_views':9,'actual_new_300dpi_page_views':9,'assets':assets})
dump('source-region-structure.json',{'representation':'source_display_geometry_not_continuous_normative_sentence','page_coordinate_system':'PDF points from top-left; page 540x720','bbox_accuracy':'人工有界区域，非逐字精确框；边框及文本框均有padding。','source_pdfs':docs,'regions':geometry,'arrows_or_normative_implication_edges_added':False})
with (O/'source-text-resources.jsonl').open('x',encoding='utf-8') as f:
 for x in texts:f.write(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n')
supp={'schema_version':'source-only-slide-example-v1','identity':identity,'issue_id':gap['issue_id'],'source_pdfs':docs,'source_text_resource_N':len(texts),'resources':texts,'source_geometry_file':'source-region-structure.json','asset_manifest_file':'source-page-assets.json','existing_record_count':12,'existing_record_bodies_modified':False,'labels_or_dimension_advice_produced':False,'external_sources_acquired':0,'scope_notice':'封面注明“本短片仅做参考”；各右侧/下方内容依展示角色为例示。左侧“包括但不限于”块单列为填写正文指示，不将右侧示例升级为规范性结论。','unresolved_lexical_characters':[],'remaining_limits':['段内排版空格和自动换行归并；中英文标点、上标的最终字形以所绑定原页图为准。','bbox为人工视觉复核的宽松区域，不称精确OCR字框。','仅对这两源九页的可见文本作来源核验；未认证全部语料、临床事实、官方公开日期或任何五维结论。']}
dump('source-only-supplement.json',supp)
counts={role:sum(x['role']==role for x in texts) for role in sorted({x['role'] for x in texts})}
checks=[]
for h in H:
 for phrase in ['1999年','共108家','本品首选用于单纯饮食控制']:
  hits=[x['source_resource_id'] for x in texts if x['source_sha256']==h and phrase in x['text']]
  assert hits;checks.append({'source_sha256':h,'phrase':phrase,'actual_source_physical_page':2,'resource_ids':hits,'check_type':'已全页/全区转写之后的遗漏定位核验；不是以3词代替转写。'})
review={'identity':identity,'source_document_N':2,'original_physical_page_N':9,'actual_original_pages_viewed':9,'new_300dpi_pages_rendered_and_viewed':9,'source_text_resource_N':len(texts),'role_counts':counts,'source_display_slide_N':len(geometry),'gap_status':'这两源九页全部可见文本按区域补足；已知缺失短语均回接原页。','known_missing_phrase_checks':checks,'uncertain_lexical_characters':[],'preserved_source_words':['本短片仅做参考','临床便于便利等','XXXX','**'],'numbering_difference':'附件2-2：04经济性、05创新性、06公平性；附件2-3：04创新性、05公平性。','source_doc_year_handling':'原页市场示例为2020-2022；PDF创建元数据为2022，不由RECODE25编号或元数据推定新年份。','new_external_sources_N':0,'old_canonical_and_labels_touched':False,'existing_12_record_count_preserved':True,'common_interface_recommendation':'由来源owner将这些添加型SOURCEVISUAL资源和纯展示区域结构统一加入下一共同材料版本。保留原固定12正文与其编号；所有方法用同版新增资源，图像依原页SHA绑定。','not_a_coding_or_human_validation_report':True}
dump('source-review.json',review)
md=['# 指定示例PDF九页来源补材核验','',f'执行者：AI GPT-6.1 Sol，ultra。起止：{identity["start_at"]}—{identity["end_at"]}。本任务只做来源转写，不产生五维标签，不是真人编码。','',f'两份同SHA原件均已核字节SHA，原九页和本目录300dpi九页均实际view_image查看。按可见区域转写{len(texts)}个文本资源、记录{len(geometry)}个展示页框；每段含原页SHA、源PDF SHA、物理/印刷页与有界坐标。','', '附件2-2有“04 经济性、05 创新性、06 公平性”；附件2-3为“04 创新性、05 公平性”。两源分别保留，没有按标题近似合并。','', '两份物理第2页的右侧例示分别恢复通用名、注册规格、1999年首次上市、共108家、1957年美国、OTC否与参照药品建议；下方恢复适应症、疾病基本情况和完整用法用量。其余页的所有可见栏目/指示/例示、封面、目录、企业名称与页号分别保存。已知3个遗漏短语的定位检查仅在完整转写后进行。','', '封面原字为“本短片仅做参考”，忠实保留；右侧和下方药品内容为例示，左侧“包括但不限于”块为填写指示。样例中的“临床便于便利等”、XXXX和**保留，不校正其临床或药学意义。PDF创建时间只记作元数据，不视为官方公开日期。','', '本次没有发现仍无法辨认的词。段内视觉换行/排版空格归并，原图保留最终字形；坐标为人工复核的宽松边界，不称逐字OCR坐标。原12条正文、标签和v11文件未写入或改动。来源owner可将新增资源统一投影为下一版共同材料；本交付不代表全部4481材料认证。','', '文件：source-only-supplement.json（主资源）；source-text-resources.jsonl（逐区域资源）；source-region-structure.json（展示结构）；source-page-assets.json（图SHA/实际查看）；input-manifest.json；source-review.json；pages/（新清晰页图）。','']
(O/'source-review.md').write_text('\n'.join(md),encoding='utf-8')
print(json.dumps({'text_resources':len(texts),'slides':len(geometry),'role_counts':counts,'original_views':9,'new_views':9,'source_supplement_sha256':sh((O/'source-only-supplement.json').read_bytes())},ensure_ascii=False))
