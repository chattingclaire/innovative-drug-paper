from pathlib import Path
import json,hashlib,datetime,importlib.util,re,zipfile,xml.etree.ElementTree as E
root=Path('/PROJECT_ROOT')
out=root/'outputs/编码修订核查-20261008/定义映射独立核查'
spec=importlib.util.spec_from_file_location('red',root/'outputs/coding-revision-20261008-r4/validation-state-audit/reserved_context_redactor.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);red=m.ReservedContextRedactor()
paths={
 'nhsa_pdf':root/'政策文件/NHSA-目录调整申报指南-2026-正式版.pdf',
 'nhsa_txt':root/'政策文件/txt_extracted/NHSA-目录调整申报指南-2026-正式版.txt',
 'nhc_local_summary':root/'政策文件/NHC-规范开展药品临床综合评价工作通知及管理指南-2021.md',
 'early_candidate_manual':root/'outputs/validation-expansion-20260926/agent-A/编码手册.txt',
 'current_v13':root/'outputs/coding-revision-20261007-r3/protocol/完整五维手册-v1.3.md',
 'current_v14':root/'outputs/coding-revision-20261007-r3/protocol/共用操作说明-v1.4.md',
 'current_docx':root/'outputs/编码修订核查-20261008/本轮结果/创新药评价的注意力配置差异与协调路径.docx'}
def binding(p):return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
bindings={k:binding(p) for k,p in paths.items()}
initial=json.loads((out/'definition_reading_scope_metadata_INITIAL.json').read_text())
scope=[];hits=[]
for k in ['nhc_local_summary','early_candidate_manual','nhsa_txt']:
 p=paths[k];selected=[{'line':n,'text':line} for n,line in enumerate(p.read_text().splitlines(),1) if re.search('公平|可及|适宜|管理难度|渠道|申报',line)]
 safe,h=red.redact_object(selected,k);hits+=h
 scope.append({'source_key':k,'reading':'initial keyword locator; matching lines displayed, not whole file','line_numbers':[x['line'] for x in selected],'full_normalized_match_metadata':h})
webmeta=json.loads((out/'official_web_retrieval_full_match_METADATA.json').read_text())
exposure={'recorded_at_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reader':'agent /root/validation_state_oct8','authorization':'Root requested necessary original-definition review including official primary sources. No protected labels permitted.','local_source_bindings':bindings,'initial_keyword_locator_scopes':scope,'nhsa_pdf_physical_pages':[7,8],'nhsa_pdf_visual_review_original_pngs':[binding(out/f'NHSA2026-physical-{n}.png') for n in [7,8]],'docx_displayed_paragraph_indices':initial['docx_paragraph_indices'],'initial_targeted_pdf_and_docx_full_matches':initial['mechanical_full_normalized_match_metadata'],'official_web_scope':{'NHC2021':'Search tool retrieved substantial inline official notice/management-guide body; semantic focus chapter2 dimensions including appropriateness/availability; ordinary direct open failed412.','NHSA2021May10':'Official search returned full double-channel notice; semantic focus definition/preamble and sectionVI. Earlier tool result not archived verbatim; no zero-intersection claim.','NHSA2021Sep10':'Official opened notice body lines21–58 returned; semantic focus sectionII.','unrelated_search_results':'Returned snippets not used as definition evidence, not expanded.'},'official_archived_retrieval_metadata':webmeta,'protected_member_ids_in_archived_retrieval':sorted({h['reserved_unit_id'] for h in webmeta['hits']}),'protected_member_ids_in_initial_keyword_locator':sorted({h['reserved_unit_id'] for h in hits}),'current_matched_original_texts_or_labels_output':False,'all_protected_text_unread_claim':False,'scope_limit':'Exact whole-unit normalization does not detect arbitrary partial or paraphrased overlap. Prior02822 authorized semantic access remains separately registered; this report does not restore independence. No protected prediction/human labels read.'}
(out/'definition_reading_exposure_addendum_METADATA.json').write_text(json.dumps(exposure,ensure_ascii=False,indent=2))
print(json.dumps({'bindings':bindings,'initial_locator_full_hit_count':len(hits),'matched_member_ids':exposure['protected_member_ids_in_initial_keyword_locator'],'exposure_metadata_sha256':binding(out/'definition_reading_exposure_addendum_METADATA.json')['sha256']},ensure_ascii=False,indent=2))

