from pathlib import Path
import json,hashlib,collections,datetime
W=Path('/PROJECT_ROOT');R=W/'outputs/coding-revision-20261007-r3'; O=W/'outputs/final-three-department-20261008-human-validation-template/method-difference-audit';H=R/'llm-candidate03-development/full-corpus-candidate03-material-v14-single-unit-reconciled-development'
files={'source':R/'effective_blind_inputs_v14.jsonl','rule_input':R/'rule_inputs_shared_v14.jsonl','rules':R/'rules-v36.2-development/all_predictions_material_v14.jsonl','LLM':H/'all_predictions.jsonl','row_provenance':H/'row_provenance.jsonl','classification':W/'outputs/validation-expansion-20260926/frozen-inputs/classification--部门归属与年度系列-冻结v1.json','manual':R/'protocol/完整五维手册-v1.3.md','operation':R/'protocol/共用操作说明-v1.4.md'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):return {'path':str(p),'sha256':sha(p)}
def rows(p):return {r['id']:r for r in map(json.loads,p.open())}
src=rows(files['source']);ri=rows(files['rule_input']);rules=rows(files['rules']);llm=rows(files['LLM']);prov=rows(files['row_provenance']);classes={Path(r['original_file']).stem:r['analysis_group'] for r in json.loads(files['classification'].read_text())['rows']}
assert list(src)==list(rules)==list(llm)
groups={i:classes[ri[i]['input']['original_file_stem']] for i in src}
dims=['S','E','Ec','I','F'];stats={}
for group in ['NMPA','NHSA','NHC']:
 ids=[i for i,g in groups.items() if g==group];a={d:sum(rules[i]['prediction']['labels'][d] for i in ids) for d in dims};b={d:sum(llm[i]['labels'][d] for i in ids) for d in dims};da=sum(a.values());db=sum(b.values())
 stats[group]={'units':len(ids),'rules_positive_counts':a,'LLM_positive_counts':b,'rules_total_positive_assignments':da,'LLM_total_positive_assignments':db,'rules_attention_share':{d:a[d]/da for d in dims},'LLM_attention_share':{d:b[d]/db for d in dims},'rules_unit_prevalence':{d:a[d]/len(ids) for d in dims},'LLM_unit_prevalence':{d:b[d]/len(ids) for d in dims},'cross_cells':{d:dict(collections.Counter(str(rules[i]['prediction']['labels'][d])+str(llm[i]['labels'][d]) for i in ids)) for d in dims}}
# Editorial case selection illustrates mechanisms, not random estimation of error rates.
specs=[
('00741','Ec','LLM_supported_extra_positive','本句明确以药品集采中选最高价作为参照药价格，属于药价实质内容，不要求再出现“经济性”。','表达词形覆盖不足：runtime rules_semantic_v35.py参照药价格式枚举加权平均价/最低挂网价等，未含“集采中选最高价”；rules_ec.py直接价格式也未命中该词形。并非没有价格语境或仅凭词频。'),
('01353','S','LLM_supported_extra_positive','药品调配交接及发放使用中的误选误用预防，直接属于用药损害预防。语境进一步明确高警示和易混淆药品。','词形与局部距离约束：v35防范式枚举用错药/错用药/用药差错/药物误用等，没有“误选误用”；rules_se.py药品到误用式限制同逗号片段及12字符，未覆盖本句分布式表达。'),
('00035','I','LLM_supported_extra_positive','本句实际安排审评人员，并据阶段资料对下一步方案提出意见；给定已核证书把程序对象限定为创新药/改良型新药。对象语境与当前实质指导可以组合，符合v1.4 I1。','规则含核验作用域与语境关系机制，但已声明支持表达未覆盖本句“安排相关审评人员…对下一步研究方案提出意见或者建议”的关系；没有输出抑制事件，属于关系覆盖不足，不能概括为规则不读语境。'),
('02845','I','LLM_definite_overinterpretation','申请人应开展药物警戒并识别管理风险，是S安全义务；当前句没有向创新研发提供指导人员、资源、优先便利或支持内容。LLM把指南给予一般安全要求本身解释为创新研发支持，违反当前命题边界。','规则S1/I0符合此处边界；LLM以创新药研发背景扩张I。'),
('03574','I','LLM_supported_extra_positive','口服制剂改注射制剂是相对既有产品的具体剂型/给药改变；否定批准不消除I内容，v1.4 I2不要求已证明优效。','具体改剂型式枚举口服/肌肉注射/静脉注射，未覆盖一般“注射制剂”目标词形，属表达覆盖不足。'),
('03576','I','LLM_definite_omission','明确大容量注射剂、小容量注射剂、注射用无菌粉针之间互改剂型，符合v1.4具体产品变化；LLM额外要求表述原创/改良创新，形成未获手册授权的门槛。','规则命中V27_I_specific_modification正确；LLM与03574的具体变化判断也显示局部不一致。'),
('01388','I','LLM_supported_extra_positive','当前定义自行取得未披露试验数据的保护对象及最长6年保护期，属于v1.4 I3专有试验数据权利实质内容。','当前规则未命中；规则包含专有保护期限/条件规则，但固定表达链未覆盖本句对象与“最长不超过6年”组合。'),
('01378','I','LLM_supported_extra_negative','当前句只是制定宗旨及办法发布施行，没有规定实体保护范围/期限/资格；依v1.4 I5应I0。','规则V27_I_data_protection_purpose把制定目的与保护制度同现直接判支持，当前发布句保护不足。'),
('01562','F','LLM_definite_omission','当前预算条件从已给父谓词恢复为“满足以下条件可以简易续约，续约有效期2年”，是实际保障连续性条件，符合v1.4 F2；LLM仅读预算前提漏掉控制父谓词。','规则通过source_bound_actual_drug_renewal_with_duration组合父谓词与条件，实际输出F1；显示现行规则也具有来源约束语境推理。'),
('01361','F','LLM_supported_extra_positive_under_current_manual','高不良反应/安全隐患药品实际退出本机构用药供应目录，依v1.4 F1实际供应范围及退出可计F，不要求扩张方向。此为当前宽构念下判定，不把F解释成已经改善社会公平。','规则F0，LLMF1；不优先作论文优势例，以免将具体供应退出与常识上的公平效果混同。')]
cases=[]
for tail,dim,verdict,reason,mechanism in specs:
 i='RECODE25-'+tail;x=ri[i]['input'];p=Path(x.get('unit_source') or x['source']);expected=x.get('unit_source_sha256') or x['source_sha256'];assert sha(p)==expected,(i,p)
 a=rules[i]['prediction']['labels'][dim];b=llm[i]['labels'][dim];assert a!=b
 cases.append({'id':i,'group':groups[i],'dimension':dim,'rules':a,'LLM':b,'source_title':src[i]['source_title'],'pages':src[i]['pages'],'text':src[i]['text'],'judgement':verdict,'audit_reason':reason,'implementation_diagnosis':mechanism,'manual_basis':'CAL-5D v1.3 + operation v1.4','original_source':bind(p),'source_unit_id':x['unit_id'],'actual_source_input':src[i],'actual_rules_row':rules[i],'actual_LLM_row':llm[i],'actual_LLM_row_provenance':prov[i]})
runtime=R/'rules-v36.2-development/runtime';code=[runtime/n for n in ['rules_semantic_v35.py','rules_se.py','rules_ec.py','rules_if.py']]
prior=R/'manuscript-update-20261008/full03-evidence-review-20261008/完整03三条创新性分歧语义复核.json'
out={'status':'COMPLETE_READONLY_CASE_AUDIT_NO_LABEL_CHANGE','created':datetime.datetime.now().astimezone().isoformat(),'scope':'当前rules-v36.2-development与reconciled03，主要三部门4481；10个目的性例证，其中NMPA创新性6例，非全量人工裁决或错误率估计','method_ids':['rules-v36.2-development','LLM-v32-candidate03-single-unit-reconciled-development'],'human_validation_completed':False,'new_model_calls':0,'labels_edited':False,'reference_labels_used_for_case_judgement':False,'bindings':{k:bind(v) for k,v in files.items()},'code_read':list(map(bind,code)),'prior_readonly_audit':bind(prior),'counts':stats,'cases':cases,'interpretation':['一致性是方法之间的可重复程度，不等于效度；共同漏判也可增加一致性。应按同一手册和原文解释差异。','LLM补识别在这些个案上有证据，但也存在I过度推断、I具体变化漏判、F父条件漏读。不能由个案推断总体更准。','注意力份额分母是同部门五维阳性赋码总次数，不是单元总数；多标签和其他维度变化同时影响份额。','当前规则包含语境证书、父谓词组合和排除条件，不宜描述为仅关键词。','这些例证属于开发后解释性审计，不是独立人类验证。']}
(O/'当前两方法具体差异审计.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
g=stats['NMPA'];a=g['rules_positive_counts']['I'];b=g['LLM_positive_counts']['I'];da=g['rules_total_positive_assignments'];db=g['LLM_total_positive_assignments'];cells=g['cross_cells']['I']
md=['# 当前两方法具体差异审计','',out['scope']+'。所有判定只依当前原文、给定语境及v1.3/v1.4；不改标签、不追加调用，尚非真人验证。','',f'药监I：规则{a}/{da}={a/da:.4%}，LLM{b}/{db}={b/db:.4%}，注意力差{100*(b/db-a/da):.4f}个百分点。单元覆盖率分别{a}/1848={a/1848:.4%}、{b}/1848={b/1848:.4%}。I四格按规则/LLM顺序：{cells}。所以6.57个百分点不能直接当成多识别6.57%的句子。','', '| ID | 维度 | 规则/LLM | 判断 | 原文短摘 |','|---|---|---|---|---|']
for c in cases:md.append(f"| {c['id']} | {c['dimension']} | {c['rules']}/{c['LLM']} | {c['judgement']} | {c['text'][:100]} |")
md+=['']
for c in cases:md += [f"**{c['id']}**：{c['audit_reason']} {c['implementation_diagnosis']}",f"来源：{c['original_source']['path']}；SHA `{c['original_source']['sha256']}`。",'']
md += ['一致性不应成为标签选择目标。可支持的优势是对具体价格含义、药物差错预防及部分来源约束关系的补识别；不应概括成LLM全面优于规则。原始逐条输出、模型理由、来源证书、完整SHA与全量分母均在同名JSON。']
(O/'当前两方法具体差异审计.md').write_text('\n'.join(md)+'\n')
print(json.dumps({'audit':bind(O/'当前两方法具体差异审计.json'),'markdown':bind(O/'当前两方法具体差异审计.md'),'NMPA':stats['NMPA']},ensure_ascii=False,indent=2))
