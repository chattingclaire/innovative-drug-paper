from pathlib import Path
import json,re,unicodedata,hashlib,collections
O=Path('/PROJECT_ROOT/outputs/coding-v26-20260930/context_repair')
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canon(s):return ''.join(t for t in unicodedata.normalize('NFKC',s) if t.isalnum()).lower()
def save(name,obj):
 with (O/name).open('x',encoding='utf8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
d=json.loads((O/'source_repair_working.json').read_text());src={s['path']:s for s in json.loads((O/'source_text_extractions.json').read_text())};inv=json.loads((O/'pending_inventory.json').read_text());reasons=json.loads((O/'all_pending_reason_records.json').read_text());packets={x['inventory']['id']:x for x in json.loads((O/'machine_pending_packets.json').read_text())}
checks=[]
for r in d['records']:
 if r['id']=='RECODE25-03226':
  r['repair_status']='existing_context_confirmed';r['material_explanation']='当前LLM及规则输入的 verified_supplemental_context 已包含第九条全部五个后项；本次核对同版PDF确认，并非新增原文。预测记录仍称条件缺失，需下游检查实际请求字段传递或阅读，不把已提供重新包装为新补料。'
 for b in r['context_blocks']:
  if b['source_normalized_substring_verified']:mode='normalized_substring_in_source';ok=True
  elif '关爱延伸-正式计划镜像.pdf' in b['source_path']:
   mode='actual_visual_check_of_source_page';ok=True;b['source_page_images']=[{'path':str(O/f'关爱计划原文-p{p}.png'),'sha256':h(O/f'关爱计划原文-p{p}.png')} for p in b['pages']]
  else:
   pages=src[b['source_path']]['pages'];lines=[]
   for p in b['pages']:
    for line in pages[p-1].splitlines():
     if re.fullmatch(r'\s*[—–-]?\s*\d+\s*[—–-]?\s*',line):continue
     if canon(line) in ['国家医疗保障局规章','国家医疗保障局发布','x']:continue
     lines.append(line)
   ok=canon(b['text']) in canon('\n'.join(lines));mode='normalized_substring_after_verified_page_header_footer_removal'
  assert ok,(r['id'],b['paragraph_id'])
  b['verification']={'verified':ok,'method':mode,'normalization':'NFKC并忽略标点/空白；不更改补充段落文本。需要去页眉页码者仅去PDF独立页码行、已见固定规章页眉。视觉核验的扫描页单独标明。'}
  checks.append({'id':r['id'],'paragraph_id':b['paragraph_id'],'source_path':b['source_path'],'source_sha256':b['source_sha256'],'pages':b['pages'],'method':mode,'passed':ok})
 r['original_input_exposure']={'rule_new_paragraph_blocks':sum(not b['present_in_original_rule_input'] for b in r['context_blocks']),'llm_new_paragraph_blocks':sum(not b['present_in_original_llm_contexts'] for b in r['context_blocks']),'table_structure_new':r['id']=='RECODE25-01434','comparison_basis':'逐块比对current_rule_inputs.input与current_llm_inputs.contexts所含字符串，包括已核验补充字段；只证明当前保存JSON是否含内容，不证明历史实际API请求是否传入。'}
 assert r['unit_text']==packets[r['id']]['llm_input']['text']==packets[r['id']]['rule_input']['input']['unit_text']
 assert hashlib.sha256(r['unit_text'].encode()).hexdigest()==r['unit_text_sha256']
 r['source_version_policy']='仅使用当前输入指向的同字节源文及候选文件；明确外引条款单独标来源与版本。没有修改原单元、候选文件、源文、原始参照或预测。'
final={'version':'v26-context-repair-20260930-r1','identity':{'kind':'AI','name':'V600独立评审A（本轮仅材料回查，不作标签）'},'scope':'机器待定并集53条的材料核验与补充语境；四方待定117条仅清点原始原因；不含最终0/1标签。','counts':dict(collections.Counter(r['repair_status'] for r in d['records'])),'records':d['records'],'source_extraction_audit_path':str(O/'source_text_extractions.json'),'original_pending_reasons_path':str(O/'all_pending_reason_records.json'),'limitations':['本轮未新增维度裁定，不声称待定已解决为0/1。','53条之外的64条只按原记录清点原因，本轮未逐条做源文修复；其中6条为概念边界，58条提出材料或结构缺口。','有2条仍存真实外引材料缺口；不得用空补丁或机械0替代。','保存JSON已含语境不等于历史API实际请求已传入；请求构造须另行核对。'],'input_hashes':inv['input_hashes'][:6]}
save('machine_pending_context_supplements_v26.json',final);save('source_verification_checks_v26.json',checks)
# Same payload for both methods; original units are not replaced or concatenated with context.
patch=[]
for r in d['records']:
 p={'id':r['id'],'original_id':r['original_id'],'unit_text_sha256':r['unit_text_sha256'],'repair_status':r['repair_status'],'verified_context_v26':{'version':final['version'],'contexts':r['context_blocks'],'usage':r['usage_boundary']},'unresolved_material_gaps':r['unresolved_material_gaps']}
 if 'verified_table_context' in r:p['verified_context_v26']['table_structure']=r['verified_table_context']
 patch.append(p)
save('label_free_context_patch53_v26.json',{'merge_policy':'按id+原单元SHA匹配，将同一个verified_context_v26对象提供给规则与LLM；不得覆盖text/unit_text、既有contexts/verified_supplemental_context、标签或单位边界；需确认两种执行器真正读取此新增字段。当前文件只是补料包，不是已运行的预测。','records':patch})
# Human-reason inventory groups selected from individual original reason records, not inferred outcome labels.
concept={'01384','01390','01391','01393','01406','01504'}
tables={'00453','00455','00462','00463','00464','00470','00472','00475','00484','00485','00486','00488','00491','01420','01423','01425','01426','01427','01428','01431','02884'}
refs={'01008','01234','01241','01332','01466','01468','02029','02287','02297','04272','04641'}
objects={'01804','02819','02871','04183'}
figs={'03701','03762'}
machine={r['id']:r for r in d['records']};index=[]
for rr in reasons:
 suffix=rr['id'].split('-')[1]
 if rr['id'] in machine:
  mr=machine[rr['id']];cat='机器并集已回查';state=mr['repair_status'];detail=mr['material_explanation']
 else:
  cat='概念边界（原记录认定材料完整）' if suffix in concept else '表题表头/列关系（部分并含引用）' if suffix in tables else '明确引用/前项条件缺失' if suffix in refs else '对象/指代/缩略语缺失' if suffix in objects else '图示缺失' if suffix in figs else '后续列项/完整结构缺失'
  state='conceptual_question_not_material_repair' if suffix in concept else 'not_source_repaired_in_this_pass'
  detail='按原提交原因清点；本轮未另行确认该缺口是否确实不存在于当前输入。'
 index.append({'id':rr['id'],'source_title':rr['source_title'],'unit_text_sha256':rr['unit_text_sha256'],'pending_methods':rr['pending_methods'],'in_machine_pending_union':rr['in_machine_pending_union'],'reason_group':cat,'review_state':state,'note':detail,'original_reasons':{k:{f:v for f,v in q.items() if f!='labels'} for k,q in rr['pending_records'].items()}})
save('all117_pending_material_reason_index_v26.json',{'scope':'材料原因清点，不给任何最终维度标签。六条概念未决与材料不足分开。','group_counts':dict(collections.Counter(x['reason_group'] for x in index)),'records':index})
# Re-check all frozen inputs and source bytes read, no modifications.
for x in inv['input_hashes']:assert h(x['path'])==x['sha256'],x['path']
for s in src.values():assert h(s['path'])==s['sha256'],s['path']
for r in d['records']:
 for b in r['context_blocks']:assert h(b['candidate_path'])==b['candidate_sha256']
print('status counts',final['counts']);print('checks',len(checks),collections.Counter(x['method'] for x in checks));print('reason groups',collections.Counter(x['reason_group'] for x in index));print('new original input paragraphs',sum(r['original_input_exposure']['llm_new_paragraph_blocks'] for r in d['records']));print('all original input/source/candidate hashes unchanged')
