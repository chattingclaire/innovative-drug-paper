"""Register incidental historical text exposure without printing policy text."""
import hashlib,json,re
from pathlib import Path
ROOT=Path('/PROJECT_ROOT')
ARCH=Path('/LOCAL_HOME/Desktop/战略院/创新药论文-完整归档-20260914')
OUT=ROOT/'outputs/autocode-v25-20260927'
TRUNC=ARCH/'11-编码检验复核-20260925/llm_input_truncation.json'
ORIGINAL=ARCH/'03-编码数据与脚本/all_sentences.json'
RESULTS=ARCH/'11-编码检验复核-20260925/results.json'
def digest(s): return hashlib.sha256(s.encode()).hexdigest()
t=json.loads(TRUNC.read_text())
original={x['id']:(i,x) for i,x in enumerate(json.loads(ORIGINAL.read_text()))}
observed={3,4,7,12,43,100,101,2996,3014,3023,3042,3045,3051,3155,3156,3204,3221,3222,3322,3336,3340,3375}
trunc_ids={x['id'] for x in t['truncated']}
assert observed<=trunc_ids
all_ids=trunc_ids|{2687,1009}
trunc_index={x['id']:i for i,x in enumerate(t['truncated'])}
entries=[]
for sid in sorted(all_ids):
 i,x=original[sid]
 source_text=x['sent']
 displayed=sid in observed or sid in {2687,1009}
 entry={'historical_sentence_id':sid,'status':'confirmed_displayed' if displayed else 'conservatively_register_possible_display',
        'registration_action':'exclude_or_map_to_excluded_exposure_before_future_holdout_draw',
        'original_source':str(ORIGINAL),'original_json_pointer':'/'+str(i),
        'original_text_sha256':digest(source_text),
        'whitespace_removed_sha256':digest(re.sub(r'\s+','',source_text)),
        'source_filename':x.get('file'),'department':x.get('dept')}
 if sid in trunc_ids:
  ti=trunc_index[sid];tr=t['truncated'][ti]
  entry.update({'display_source':str(TRUNC),'display_json_pointer':f'/truncated/{ti}',
                'display_fields':['preview','hidden'],
                'preview_sha256':digest(tr['preview']),'hidden_sha256':digest(tr['hidden']),
                'recombined_display_text_sha256':digest(tr['preview']+tr['hidden']),
                'reason':'直接cat审计输出被工具截断；确认可见头尾ID另标confirmed，其余139条全部保守纳入，避免假称未暴露。'})
 else:
  entry.update({'display_source':str(RESULTS),'display_json_pointer':'/invalid/A',
                'reason':'results.json结构摘要显示非法格对象中的sentence字段。'})
 entries.append(entry)
payload={'date':'2026-09-27','task':'historical_LLM_verification_check','identity':'autocode_error_audit subagent',
         'event':'一次exec_command cat旧llm_input_truncation.json产生政策正文preview/hidden可见输出；另有results.json非法格摘要可见原文。',
         'tool_output_limit':'cat步骤max_output_tokens=5500，组合结果另有截断；无法据截断输出保证完整识别实际显示子集。',
         'registration_policy':'对截断审计全部139个ID保守登记可能暴露，外加非法格2个ID；confirmed清单只列能在可见工具输出明确辨认的ID。',
         'original_full_corpus_text_printed':False,
         'new_v25_validation_candidate_files_opened':False,
         'must_not_assume_current_holdout_unexposed':'这些历史片段可能映射至当前未展示单元；必须由协调者据原文程序映射排除。',
         'counts':{'registered':len(entries),'truncation_audit_all_ids':len(trunc_ids),'confirmed_displayed':sum(e['status']=='confirmed_displayed' for e in entries),'possible_display_registered_conservatively':sum(e['status']!='confirmed_displayed' for e in entries)},
         'entries':entries,
         'source_hashes':[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [TRUNC,ORIGINAL,RESULTS]]}
(OUT/'历史LLM核查新增暴露登记.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(payload['counts'],ensure_ascii=False))
