"""Actual source image page1-3 transcription and SHA-bound correspondence only."""
from pathlib import Path
import copy,json,importlib.util,os
from collections import Counter
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
sp=importlib.util.spec_from_file_location('preflight',OUT/'build_full_frame_preflight_v2.py');pr=importlib.util.module_from_spec(sp);sp.loader.exec_module(pr)
rows=pr.readrows;sha=pr.sha;sf=pr.shafile;jl=pr.jsonl;dump=pr.dump
source=next(e for e in json.loads((ROOT/'00-baseline/source_files_manifest.json').read_text())['files'] if e['sha256'].startswith('a83ae5ab'));s=source['sha256'];assert sf(source['snapshot'])==s
paragraphs=[
([1],'罕见疾病创新药物研发鼓励试点计划（“关爱计划-延伸”）'),
([1],'一、背景'),
([1],'目前大多数罕见疾病尚无有效治疗药物。罕见疾病具有发病率与患病率极低、病情复杂的特点，且当前对其认知相对有限，显著增加了相关药物的研发难度。罕见疾病药物研发存在鲜明特殊性：一是临床试验数据有限，需依托自然病史研究数据、真实世界研究数据、患者体验数据等多维度、多层次信息构建完整证据链，为监管决策提供支持；二是药物研发经验不足，尤其是既往未开发过的罕见疾病适应症领域缺乏可循先例，需借助外部数据优化临床试验设计；三是研发过程需系统筹划，通过合理安排设计，提升研发效率。'),
([1],'2024年药审中心启动了“关爱计划”试点工作。“关爱计划”提供了自然病史研究、患者与医生调研、患者体验数据收集等多种研究方法的实践经验，这些经验和成果有待转化为对罕见疾病药物研发的具体推动与指导措施。为进一步满足罕见疾病患者急迫的治疗需求，激发罕见疾病药物领域的研发热情与活力，破解研发难题，转化实践经验，药审中心计划开展罕见疾病创新药物研发鼓励试点计划，即“关爱计划-延伸”试点工作。'),
([1],'二、主要内容'),
([2],'罕见疾病适应症开发需通盘规划，依托自然病史研究、真实世界研究等外部数据与证据构建完整证据链，以支持更为科学精巧的关键研究设计，因此监管机构采取“早期介入、一品一策”的工作模式，将为罕见疾病药物临床研发提供重要助力。'),
([2],'“关爱计划-延伸”项目的核心内容，是在罕见疾病药物研发早期，由申请人通过沟通交流途径递交《罕见疾病创新药物临床研发实施框架》，与药审中心就该适应症的开发计划进行讨论。当品种被纳入试点项目后，随着临床开发的推进，实施框架中的相关内容将不断完善；实施框架将成为该品种罕见疾病适应症的临床研发档案，便于在整个开发过程中及时高效地与药审中心开展沟通交流。'),
([2],'本试点工作旨在鼓励创新药向临床治疗需求迫切的罕见疾病领域布局，聚焦并解决源头性创新罕见疾病药研发中的科学问题，因此申请品种需同时满足以下条件：（1）拟开发的适应症为罕见疾病。（2）具有较强创新性。（3）对目标罕见疾病适应症的开发尚处于早期临床开发阶段。有关申报资格的具体要求详见《罕见疾病创新药物研发鼓励试点计划（“关爱计划-延伸”）申报指南》。'),
([2],'三、组织与实施'),
([2,3],'药审中心起草了《罕见疾病创新药物研发鼓励试点计划（“关爱计划-延伸”）申报指南》和《罕见疾病创新药物临床研发实施框架》，详细介绍了申请加入“关爱计划-延伸”试点工作的方法和具体要求，供有意向的申请人参考。'),
([3],'纳入试点项目的品种按计划开发罕见疾病适应症。申请人在依据现行法规和工作程序开展常规的药物申报及注册工作的同时，还需根据药审中心审评需求阶段性汇报相关工作进展或结果。'),
([3],'申请人基于自愿原则通过沟通交流途径，申请加入“关爱计划-延伸”试点工作。试点工作不设名额限制，招募期为5年。药审中心将组织审评团队对是否同意其纳入“关爱计划-延伸”试点工作进行评价，必要时将与申请人召开沟通交流会。'),
([3],'经评价拟同意纳入“关爱计划-延伸”试点工作后，药审中心将予以公示，公示期为5日，公示无异议的品种最终将纳入“关爱计划-延伸”试点工作。'),
([3],'附件：1.罕见疾病创新药物研发鼓励试点计划（“关爱计划-延伸”）申报指南 2.罕见疾病创新药物临床研发实施框架')]
pages=[{'physical_page':i,'printed_page':i,'source_pdf_sha256':s,'path':str(OUT/'source-visual-v7/pages'/f'cde-care-{i:02}.png'),'sha256':sf(OUT/'source-visual-v7/pages'/f'cde-care-{i:02}.png')} for i in [1,2,3]]
oldpath=OUT/'canonical_source_context-v5.jsonl';data=rows(oldpath);D={r['id']:r for r in data};body=rows(OUT/'body-source-QA-v6.jsonl');BQ={b['record_id']:b for b in body};ctx=rows(OUT/'context-source-QA-v6.jsonl');CQ={(q['record_id'],q['context_id']):q for q in ctx};pending=rows(OUT/'source-exceptions-v6.jsonl');resolved=[];remaining=[]
for e in pending:
 if e['source_sha256']!=s:remaining.append(e);continue
 r=D[e['record_id']];n=next((n for n in r['contexts'] if n['context_id']==e['context_id']),None);t=r['text'] if n is None else dict(pr.pr.text_values(n))[e['field']]
 matches=[(ps,tx) for ps,tx in paragraphs if pr.norm(t) in pr.norm(tx)]
 if not matches:remaining.append(e);continue
 ps,tx=matches[0];ev={**e,'review_status':'AI_visual_actual_binary_rendered_pages_and_independent_literal_transcription','physical_pages':ps,'source_pdf_sha256':s,'source_text_unchanged':True,'source_paragraph_transcription_sha256':sha(tx.encode()),'human_coding':False,'dimension_judgment':False};resolved.append(ev)
 if n is None:BQ[e['record_id']]['literal_status']='AI_visual_primary_scanned_page_independent_literal_correspondence';BQ[e['record_id']]['source_visual_review_v7']=ev
 else:
  for ft in CQ[(e['record_id'],e['context_id'])]['policy_text_fields']:
   if ft['field']==e['field']:ft['literal_status']='AI_visual_primary_scanned_page_independent_literal_correspondence';ft['source_visual_review_v7']=ev
 ats={a['attachment_id']:a for a in r.get('source_attachments',[])}
 for p in pages:
  if p['physical_page'] in ps:
   a={'attachment_id':'SOURCEPAGE-'+p['sha256'][:20],'sha256':p['sha256'],'relative_path':os.path.relpath(p['path'],OUT),'source_pdf_sha256':s,'physical_page':p['physical_page'],'printed_page':p['printed_page'],'kind':'original_binary_rendered_source_page'};ats[a['attachment_id']]=a
 r['source_attachments']=list(ats.values())
jl(OUT/'canonical_source_context-v7.jsonl',data);jl(OUT/'body-source-QA-v7.jsonl',body);jl(OUT/'context-source-QA-v7.jsonl',ctx);jl(OUT/'source-exceptions-v7.jsonl',remaining);dump(OUT/'source-visual-review-v7.json',{'source_pdf':source,'source_PDF_no_extractable_text_layer':True,'pages_opened_and_AI_read':pages,'source_independent_transcriptions':[{'physical_pages':ps,'text':t,'text_sha256':sha(t.encode())} for ps,t in paragraphs],'resolved_occurrences':resolved,'uncertain_or_unmatched_source_glyphs_not_silently_repaired':True,'labels_or_coder_outputs_read':False})
rm=rows(OUT/'material-record-bindings-v5.jsonl')
for b in rm:b['projected_record_sha256']=sha(pr.canonical(D[b['id']]).encode());assert b['projected_body_sha256']==sha(D[b['id']]['text'].encode())
jl(OUT/'material-record-bindings-v7.jsonl',rm);fa=json.loads((OUT/'family-exposure-impact-v5.json').read_text());fa['source_projection_v7_sha256']=sf(OUT/'canonical_source_context-v7.jsonl');fa['v5_v7_bodies_and_contexts_byte_identical']=True;dump(OUT/'family-exposure-impact-v7.json',fa)
ids=rows(OUT/'source-document-identities-v4.jsonl')
for r in ids:
 if r['source_sha256']==s:r['source_document_title_actual_image_verified']='罕见疾病创新药物研发鼓励试点计划（“关爱计划-延伸”）';r['source_title_visual_evidence']={'source_pdf_sha256':s,'physical_page':1,'rendered_page_sha256':pages[0]['sha256']};r['document_publication_date_established_from_scanned_pages']=False;r['2024_in_body_is_recalled_earlier_care_pilot_not_current_document_publication_year']=True
jl(OUT/'source-document-identities-v7.jsonl',ids)
qa=json.loads((OUT/'source-QA-summary-v6.json').read_text());qa.update({'status':'full_frame_source_preflight_v7_scanned_plan_core_text_AI_review; pending_items_retained; not_material_freeze','output':{'path':str(OUT/'canonical_source_context-v7.jsonl'),'sha256':sf(OUT/'canonical_source_context-v7.jsonl')},'v7_unit_and_context_text_unchanged_from_v5':True,'new_primary_scanned_page_AI_visual_occurrence_N':len(resolved),'pending_issue_N':len(remaining),'pending_unique_source_text_N':len({(e['source_sha256'],e['text_sha256']) for e in remaining}),'final_material_freeze_completed':False});dump(OUT/'source-QA-summary-v7.json',qa)
print(json.dumps({'resolved_occurrences_N':len(resolved),'remaining_N':len(remaining),'unique_remaining_N':qa['pending_unique_source_text_N'],'canonical_sha256':qa['output']['sha256']},ensure_ascii=False,indent=2))
