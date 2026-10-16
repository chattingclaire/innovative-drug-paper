"""Actual page source review of remaining non-graph jobs. No label data is loaded."""
from pathlib import Path
import json,re,subprocess,copy,importlib.util,os
from collections import Counter,defaultdict
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
sp=importlib.util.spec_from_file_location('preflight',OUT/'build_full_frame_preflight_v2.py');pr=importlib.util.module_from_spec(sp);sp.loader.exec_module(pr)
rows=pr.readrows;sha=pr.sha;sf=pr.shafile;jl=pr.jsonl;dump=pr.dump
BS={r['sha256']:r for r in json.loads((ROOT/'00-baseline/source_files_manifest.json').read_text())['files']};data=rows(OUT/'canonical_source_context-v8.jsonl');D={r['id']:r for r in data};body=rows(OUT/'body-source-QA-v8.jsonl');BQ={r['record_id']:r for r in body};ctx=rows(OUT/'context-source-QA-v8.jsonl');CQ={(r['record_id'],r['context_id']):r for r in ctx};pending=rows(OUT/'source-exceptions-v8.jsonl');resolved=[];remaining=[];proofs=[];extract={};newnodes=[]
def getsha(pref):return next(s for s in BS if s.startswith(pref))
S4=getsha('1be84453158f1e92');S5=getsha('da218af12c655b8b');SN=getsha('b8524dded105cc5b');SF25=getsha('7f5b1829d0030b34');SF26=getsha('64ac48e587537802')
# Independent literal reading of the actual pictured instruction blocks (left of
# illustration slides), not the hypothetical example answers in the right block.
shared=[
('药品基本信息','包括但不限于：药品通用名称；注册规格；说明书适应症/功能主治（概述）；用法用量；中国大陆首次上市时间；目前大陆地区同通用名药品的上市情况；全球首个上市国家/地区及上市时间；是否为OTC药品；参照药品建议；所治疗疾病基本情况；未满足的治疗需求；大陆地区发病率；年发病患者总数等。'),
('安全性','包括但不限于：该药品在国内外不良反应发生情况；药品说明书收载的安全性信息；与目录内同类药品安全性方面的主要优势和不足。'),
('有效性','包括但不限于：临床试验或（和）真实世界中与对照药品疗效方面的主要优势和不足；临床指南/诊疗规范推荐情况；国家药品审评中心出具的《技术评审报告》中关于本药品有效性的描述。'),
('创新性','包括但不限于：主要创新点；该创新带来的疗效或安全性方面的优势；是否为国家“重大新药创制”科技重大专项支持上市药品；是否为自主知识产权的创新药；传承性（限中成药）情况。'),
('公平性','包括但不限于：所治疗疾病大陆地区年发病患者总数；是否能够弥补药品目录保障短板；临床管理难度及其他相关情况。')]
trans=[]
for s in [S4,S5]:
 for ix,(title,t) in enumerate(shared):
  page=[2,3,3,4,5 if s==S4 else 4][ix];num=[1,2,3,5 if s==S4 else 4,6 if s==S4 else 5][ix]
  trans.extend([{'source_sha256':s,'physical_pages':[page],'text':t,'original_block':'left_instruction_block_of_actual_slide','title':title}, {'source_sha256':s,'physical_pages':[page],'text':f'{num:02} {title}','original_block':'number_and_title_in_same_actual_slide_title_panel','source_title_number_spatially_related_not_adjacent_byte_string':True}])
trans.extend([
{'source_sha256':S4,'physical_pages':[4],'text':'04 经济性','original_block':'number_and_title_in_same_actual_slide_title_panel','source_title_number_spatially_related_not_adjacent_byte_string':True},
{'source_sha256':S4,'physical_pages':[4],'text':'包括但不限于：目前的市场价格（如未定，可介绍预期价格）；各省份挂网情况；2020-2022年大陆地区药品销售金额（含全部规格，如非独家，可主要介绍本企业产品的情况）。与目录内同治疗领域药品经济性方面的优势和不足。','original_block':'left_instruction_block_of_actual_slide'},
{'source_sha256':SN,'physical_pages':[1],'text':'为进一步加强我国临床合理用药管理，根据《国家重点监控合理用药药品目录调整工作规程》（国卫办医函〔2021〕474号），我委确定了《第二批国家重点监控合理用药药品目录》（以下简称《目录》）。现印发给你们，供各地在加强合理用药管理、开展公立医院绩效考核等工作中使用。','original_block':'actual_original_notice_first_paragraph'},
{'source_sha256':SN,'physical_pages':[1],'text':'各地要以规范临床用药行为、促进合理用药为工作目标，对纳入本目录的药品制定完善临床应用指南，明确临床应用的条件和原则，加强合理用药监管。《第一批国家重点监控合理用药药品目录》（国卫办医函〔2019〕558号）中的药品纳入本《目录》的，按照要求加强重点监控；未纳入本《目录》的，应当持续监控至少满1年后可不再监控，以促进临床合理用药水平持续提高。','original_block':'actual_original_notice_second_paragraph'},
{'source_sha256':SF25,'physical_pages':[12,13],'text':'商保创新药目录设定主要有以下几点考虑：一是遴选范围方面。商保创新药目录主要聚焦创新程度高、临床价值大、患者获益显著，但因超出“保基本”定位暂时无法纳入基本目录的药品。按照本年度《工作方案》，在5年内批准上市的新通用名或治疗罕见病的独家药品可以申报。二是使用范围方面。商保创新药目录推荐商业健康保险等多层次医疗保障体系参考使用，基本医保不予支付。三是制定程序方面。商保创新药目录由国家医保局组织制定，与基本目录调整工作同步开展。程序与基本目录调整基本一致，但商保专家在对药品是否进入商保创新药目录以及价格协商具有重要决策权。申报阶段，基本目录和商保创新药目录同时申报，允许企业根据自身意愿选择单独申报基本目录或是商保创新药目录，或者同时申报。在评审阶段，基本目录和商保创新药目录评审同时进行。对综合组专家建议纳入商保创新药目录的药品，组织商保专家评审，形成最终评审结果（见图3商保创新药目录申报全流程示意图）。四是支持商保创新药患者可及。国家医保局将探索优化调整支付管理政策，商保创新药目录内药品可不计入基本医保自费率指标和集采中选可替代品种监测的范围，符合条件的商业健康保险保障范围内的创新药应用病例可不纳入按病种付费范围，经审核评议程序后支付。','original_block':'actual_question2_answer_spanning_physical12_13'},
])
formulaA={'printed_name':'比值A','numerator':'本协议期实际发生的纳入支付范围的药品费用','denominator':'本协议期纳入支付范围的药品费用预算','multiplier':'×100%'}
formulaB={'printed_name':'比值B','numerator':'因本次调整支付范围所致的纳入支付范围的药品费用预算增加值','denominator':'较高值（原支付范围的纳入支付范围的药品费用预算或本协议期内实际发生的纳入支付范围的药品费用）','multiplier':'×100%'}
expr25='比值A='+formulaA['numerator']+'/'+formulaA['denominator']+'×100%,比值B='+formulaB['numerator']+'/'+formulaB['denominator']+'×100%。'
expr26='比值A=（'+formulaA['numerator']+'／'+formulaA['denominator']+'）×100%；比值B=〔'+formulaB['numerator']+'／'+formulaB['denominator']+'〕×100%。'
trans.extend([{'source_sha256':SF25,'physical_pages':[14],'text':expr25,'original_block':'actual_two_horizontal_fraction_formulae','neutral_formula_geometry':[formulaA,formulaB]}, {'source_sha256':SF26,'physical_pages':[16],'text':expr26,'original_block':'actual_two_horizontal_fraction_formulae','neutral_formula_geometry':[formulaA,formulaB]}])
trans.append({'source_sha256':SF25,'physical_pages':[13,14,15],'text':'答:《续约规则》体现了医保药品目录调整工作“分类管理,精准施策”的管理思路,从而实现资源优化配置和管理效率最大化。《续约规则》中需要特别说明几点:一是2017年纳入的谈判药品,截至2025年12月31日仍为协议期内的,符合连续纳入8年的条件,在依据续约规则确定支付标准和支付范围后转入常规目录乙类。二是符合简易续约的药品支付标准的计算。根据比值A、比值B的计算结果,对符合简易续约的药品支付标准进行分档下调。'+expr25+'比值A强调的是原支付范围的药品实际销量与企业预测的比值,重点关注药品是否超出当期销售预期;比值B强调的是拟调整支付范围部分的新增值与原支付范围的企业预测和实际销量二者中的高值相比,重点关注对医保基金带来的额外占用影响。三是比值A和比值B计算方面,几种常见情景需额外注意支付标准下调比例的计算:(1)协议到期前一年新增适应症,扣减比值A降幅。在计算最终降幅时,先计算前一年因比值A导致的降幅Z%,再计算本续约年份因比值A导致的降幅X%,比值B导致的降幅为Y%,最终降幅为1-[1-(X%-Z%)](1-Y%)。(2)满4年降幅减半的计算要点。如果连续纳入目录“协议期内谈判药品部分”达到或超过4年(今年调整是指2022年1月1日之前纳入目录),且要进行支付标准调整,则降幅减半。例如比值A导致的降幅为X%,比值B导致的降幅为Y%,在最终降幅上减半,计算公式为[1-(1-X%)(1-Y%)]/2。(3)药品在简易续约触发支付标准下调,需考虑药品纳入支付范围的年均药品费用和/或纳入支付范围的药品费用预算年均增加值。(4)协议未到期谈判药品申报新增适应症,比值A、比值B的计算。例如协议到期时间为2026年12月31日,2025年申报新增适应症,计算比值A、比值B的实际发生的纳入支付范围的药品费用和纳入支付范围的药品费用预算均取2025年数据,计算比值B的未来一年因调整支付范围所致的纳入支付范围药品费用预算增加值取2026年数据。','original_block':'actual_question3_answer_spanning_physical13_14_15; fraction geometry explicitly retained','neutral_formula_geometry':[formulaA,formulaB]})
def cleaned_raw(s):
 if s in extract:return extract[s]
 raw=subprocess.run(['pdftotext','-raw',BS[s]['snapshot'],'-'],capture_output=True,text=True,timeout=30);assert raw.returncode==0
 pages=raw.stdout.split('\f');ps=[];removed=[]
 for i,p in enumerate(pages,1):
  ls=p.splitlines()
  if s.startswith('85457d52') and len(ls)>=4 and ls[:3]==['国家医疗保障局规章','X','国家医疗保障局发布'] and re.fullmatch(r'- \d+ -',ls[3]):removed.extend({'physical_page':i,'literal':t,'physical_role':'actual_letterhead/emblem or footer/page_number; PDF stream places these four before policy body'} for t in ls[:4]);ls=ls[4:]
  elif s.startswith('41fd5850') and len(ls)>=2 and '国务院公报' in ls[-1] and '部门文件' in ls[-1] and re.fullmatch(r'\s*[—－\-]+\s*[０-９0-9]+\s*[—－\-]+\s*',ls[-2]):removed.extend({'physical_page':i,'literal':t,'physical_role':'actual running header or printed page footer placed after body in raw stream'} for t in ls[-2:]);ls=ls[:-2]
  elif s.startswith('7e3a7d01') and len(ls)>=3 and ls[0].startswith('更多医疗政策全文') and ls[1]=='数据，尽在健康界医享库！' and ls[2].isdigit():removed.extend({'physical_page':i,'literal':t,'physical_role':'actual third-party republication advertising footer or page number'} for t in ls[:3]);ls=ls[3:]
  elif s.startswith('b5f4e415') and len(ls)>=2 and ls[0]=='国家卫生健康委员会公报 2024·11' and re.fullmatch(r'-\d+-',ls[1]):removed.extend({'physical_page':i,'literal':t,'physical_role':'actual running header and page footer placed before body in raw stream'} for t in ls[:2]);ls=ls[2:]
  ps.append('\n'.join(ls))
 cleaned='\f'.join(ps);extract[s]={'cleaned_raw':cleaned,'removed':removed,'raw_extraction_sha256':sha(raw.stdout.encode()),'cleaned_audit_extraction_sha256':sha(cleaned.encode())};return extract[s]
def get_text(r,n,f):return r['text'] if n is None else dict(pr.pr.text_values(n))[f]
def attach(r,s,ps):
 ats={x['attachment_id']:x for x in r.get('source_attachments',[])}
 for i in ps:
  path=OUT/'source-visual-v9/pages'/f'{s[:16]}-{i}.png';assert path.exists();a={'attachment_id':'SOURCEPAGE-'+sf(path)[:20],'sha256':sf(path),'relative_path':os.path.relpath(path,OUT),'source_pdf_sha256':s,'physical_page':i,'kind':'original_binary_rendered_source_page'};ats[a['attachment_id']]=a
 r['source_attachments']=list(ats.values())
for e in pending:
 s=e['source_sha256'];r=D[e['record_id']];n=next((z for z in r['contexts'] if z['context_id']==e['context_id']),None);t=get_text(r,n,e['field']);nt=pr.norm(t);ps=e.get('pages',e.get('locator',{}).get('pages',[]));method=None;mt=None
 # The explicitly assigned source-graph jobs, including graph3 misclassified in
 # v6 because it has no arrow glyph, remain for the separate reviewer.
 if e.get('fragment_type') in ['diagram_branch_and_geometry_transcription','flattened_table_row_requires_original_cell_geometry'] or t.startswith('图3 商保创新药目录申报全流程示意图'):remaining.append(e);continue
 for p in trans:
  if p['source_sha256']==s and nt in pr.norm(p['text']):mt=p;method='AI_visual_actual_original_page_and_independent_source_block_literal_correspondence';ps=p['physical_pages'];break
 if not method and s.startswith(('85457d52','41fd5850','7e3a7d01','b5f4e415')):
  x=cleaned_raw(s);target=pr.norm(t.replace('。','.') if s.startswith('41fd') else t)
  if target in pr.norm(x['cleaned_raw']):method='actual_primary_PDF_source_specific_running_header_footer_or_republisher_ad_exclusion_and_literal_page_join'
 if not method:remaining.append(e);continue
 assert sf(BS[s]['snapshot'])==s;attach(r,s,ps)
 ev={**e,'source_literal_status':method,'actual_primary_source_sha256':s,'physical_pages':ps,'rendered_source_page_sha256':[sf(OUT/'source-visual-v9/pages'/f'{s[:16]}-{i}.png') for i in ps],'source_field_text_unchanged':True,'AI_source_visual_review_not_human_coding':True}
 if mt:ev['independent_source_transcription_sha256']=sha(mt['text'].encode());ev['original_block']=mt['original_block']
 else:ev['source_running_header_footer_audit_extraction_sha256']=extract[s]['cleaned_audit_extraction_sha256'];ev['source_glyph_map_if_any']='only target Chinese fullstop。→source extraction ASCII. on the visually checked same PDF' if s.startswith('41fd') else None
 resolved.append(ev)
 if n is None:BQ[r['id']]['literal_status']=method;BQ[r['id']]['source_visual_review_v9']=ev
 else:
  for ft in CQ[(r['id'],n['context_id'])]['policy_text_fields']:
   if ft['field']==e['field']:ft['literal_status']=method;ft['source_visual_review_v9']=ev
 if mt and mt.get('neutral_formula_geometry'):
  for f in mt['neutral_formula_geometry']:
   gid='CTX-SRCFORMULA-'+sha((r['id']+s+f['printed_name']).encode())[:20]
   if any(z['context_id']==gid for z in r['contexts']):continue
   page=14 if s==SF25 else 16;st={'physical_pages':[page],'source_layout_relation':'horizontal_fraction_then_right_multiplier','numerator_cell_index':0,'denominator_cell_index':1,'right_multiplier_cell_index':2,'related_context_ids':[n['context_id']] if n else [],'source_image_sha256':sf(OUT/'source-visual-v9/pages'/f'{s[:16]}-{page}.png')};gn={'context_id':gid,'kind':'source_formula_geometry','source_document':'D-'+s[:16],'caption':f['printed_name'],'row_cells':[f['numerator'],f['denominator'],f['multiplier']],'structure':st,'source_ref':{'sha256':s,'source_resource_id':'SOURCE-'+s,'locator':copy.deepcopy(st)}};r['contexts'].append(gn);newnodes.append({'record_id':r['id'],'context_id':gid,'source_sha256':s,'physical_page':page,'caption':f['printed_name'],'literal_fraction_geometry_only':True})
   ctx.append({'record_id':r['id'],'context_id':gid,'kind':gn['kind'],'primary_source_sha256':s,'source_identity_methods':['actual_horizontal_fraction_and_multiplier_source_typography'],'policy_text_fields':[{'field':k,'projected_text_sha256':sha(v.encode()),'literal_status':'AI_visual_actual_source_horizontal_fraction_cells'} for k,v in pr.pr.text_values(gn)],'textless_structure':False})
jl(OUT/'canonical_source_context-v9.jsonl',data);jl(OUT/'body-source-QA-v9.jsonl',body);jl(OUT/'context-source-QA-v9.jsonl',ctx);jl(OUT/'source-exceptions-v9.jsonl',remaining)
dump(OUT/'source-page-review-v9.json',{'status':'source_only_actual_page_read_and_literal_audit_not_human_validation','actual_independent_source_transcriptions':[{**p,'text_sha256':sha(p['text'].encode())} for p in trans],'resolved_occurrences':resolved,'new_neutral_formula_geometry_nodes':newnodes,'source_specific_audit_running_header_footer_exclusions':[{'source_sha256':s,**x,'cleaned_raw':None} for s,x in extract.items()],'public_text_changes_N':0,'material_final_freeze':False,'untouched_separate_graph_review_jobs':True})
rm=rows(OUT/'material-record-bindings-v8.jsonl')
for x in rm:r=D[x['id']];assert x['projected_body_sha256']==sha(r['text'].encode());x['projected_context_sha256']=sha(pr.canonical(r['contexts']).encode());x['projected_record_sha256']=sha(pr.canonical(r).encode())
jl(OUT/'material-record-bindings-v9.jsonl',rm);fam=json.loads((OUT/'family-exposure-impact-v8.json').read_text());fam['source_projection_v9_sha256']=sf(OUT/'canonical_source_context-v9.jsonl');fam['all_body_bytes_identical_between_v8_and_v9']=True;dump(OUT/'family-exposure-impact-v9.json',fam)
jobs=rows(OUT/'grouped-source-review-jobs-v8.jsonl');keys={(e['source_sha256'],e['text_sha256']) for e in remaining};jobs=[x for x in jobs if (x['actual_primary_source_sha256'],x['text_sha256']) in keys]
for x in jobs:x['occurrences']=[e for e in remaining if (e['source_sha256'],e['text_sha256'])==(x['actual_primary_source_sha256'],x['text_sha256'])];x['occurrence_N']=len(x['occurrences'])
jl(OUT/'grouped-source-review-jobs-v9.jsonl',jobs)
counts=Counter('body_literal_'+q['literal_status'] for q in body);counts.update({'contexts':len(ctx),'textless_contexts':sum(q.get('textless_structure',False) for q in ctx)})
for q in ctx:
 for f in q['policy_text_fields']:counts['context_literal_'+f['literal_status']]+=1
qa=json.loads((OUT/'source-QA-summary-v8.json').read_text());qa.update({'status':'full_frame_source_preflight_v9_actual_source_running_layout_scan_and_formula_review; pending_retained; not_material_freeze','counts':dict(counts),'output':{'path':str(OUT/'canonical_source_context-v9.jsonl'),'sha256':sf(OUT/'canonical_source_context-v9.jsonl')},'pending_issue_N':len(remaining),'pending_issue_types':dict(Counter(x['issue_type'] for x in remaining)),'pending_unique_source_text_N':len(jobs),'pending_unique_job_fragment_types':dict(Counter(t for x in jobs for t in x['fragment_types'])),'v9_resolved_occurrences_N':len(resolved),'v9_body_changes_N':0,'v9_context_text_changes_N':0,'v9_added_fraction_geometry_node_N':len(newnodes),'final_material_freeze_completed':False});dump(OUT/'source-QA-summary-v9.json',qa)
print(json.dumps({'source_resolved_occurrences_N':len(resolved),'pending_occurrences_N':len(remaining),'pending_unique_jobs_N':len(jobs),'new_neutral_formula_geometry_nodes_N':len(newnodes),'canonical_sha256':sf(OUT/'canonical_source_context-v9.jsonl'),'remaining_types':qa['pending_unique_job_fragment_types']},ensure_ascii=False,indent=2))
