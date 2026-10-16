"""One bounded follow-up development round; candidate03 artifacts remain immutable."""
import json,hashlib,pathlib,datetime
H=pathlib.Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
prior=H/'candidate03_prompt.txt';text=prior.read_text()
assert sha(prior)=='8576d9a1be10b0dd7b69b4c12367f4c357f55abf4ca30d979d5b333493089ba4'
text=text.replace('全五维LLM语义执行说明 v32 候选03-development','全五维LLM语义执行说明 v32 候选04-development',1)
clarification='''
## 候选04：保障期限、控制性父谓词与沟通动作的窄范围澄清

以下只澄清v1.3及v1.4已规定的保障连续性、实质条件和创新实体支持；其他标准不改。

**保障协议期限是实质内容时。** 先从给定正文确定协议实际约定什么。已明确承接药物医保给付或用药保障关系的协议，其生效、持续、到期、续期及续后有效期间可直接限定保障连续性；不能仅因表达为“协议有效期”“可续约”而要求另写“患者权益不受影响”才计F。无须已对某个患者执行。但一般行政合同期限、提交申请的截止日、仅可再次申请/谈判的机会，或只改变目录管理分类而没有实际保障持续关系的事项，仍不自动计F。

**父谓词控制条件的双向检查。** 对列表子项，先在给定语境中找出真正支配该子项的谓词及其结果。若父句实质规定符合条件者的既有药物保障延续到某期间、保障退出或实际给付范围改变，则决定是否实现该结果的当前实质条件属于同一保障命题，即使子项以预算比例、期限或其他条件表达；保留该条件本身的Ec等维度，不要求子项再重复保障结果。若父句只是把材料分流到不同办理路线、允许申请，或纯目录工作分类，则不把所谈药品已有的保障关系带给条件。这是恢复被省略的控制谓词，而非把父段所有维度复制过来。单纯“符合条件后公示/备案”的办事动作仍不复制此前所有评价维度。

**沟通申请的议题和形式不是实际提供的支持。** 当前行为若是申请人提出沟通申请、选择单/多专业沟通形式、指定申请时间或议题，不能只因议题具体、服务于上市申请或适用于创新药，就解释为已经规定了实体研发支持。只列可以讨论某种研发材料仍属申请内容/形式。当前另外实际安排专门指导人员、配置资源、授予优先辅导、提供研发技术支持措施或改变该支持资格时，才按相应明确证据判I；实际支持不要求已经完成辅导。不要反向排除专门团队、资源或实质指导内容，也不要以创新药对象名称替代这个动作差别。

教学构造对照：
- 已明确给付关系的药物协议“在原期满后继续生效若干年”可表达保障连续；“期满后可再次递交申请材料”本身不承诺延续。
- 父句规定满足条件即可延续药物保障时，“上一年度用药支出在预算限度内”可同时涉及Ec和F；相同文字只决定材料办理先后时，不能据此补F。
- 创新药申请人“选择会谈议题及参与专业”不自动赋I；机构“安排专门研发顾问向该创新药提供技术辅导”具有实体支持内容。

上述差别均须由本条与其真实控制语境共同证明。不能按部门、文件标题、样本编号或预期标签判断。完整五维仍由同一次阅读生成，不修改证据原句。

'''
text=text.replace('--- 冻结的完整手册（原样） ---',clarification+'\n--- 冻结的完整手册（原样） ---')
prompt=H/'candidate04_prompt.txt';assert not prompt.exists();prompt.write_text(text)
for p in [H.parent/'protocol/完整五维手册-v1.3.md',H.parent/'llm-v32/共用实质操作说明-v1.4-运行摘录.txt']:
 assert p.read_text().strip() in text
assert 'RECODE25-' not in text and '0.80' not in text

tests=json.loads((H/'synthetic30_expected_PRIVATE.json').read_text())['tests']
def add(text,positives,rationale,contexts=None):
 rid=f'C04-CONTROL-{len(tests)+1:03d}'
 tests.append({'input':{'id':rid,'text':text,'contexts':contexts or {}},'labels':{d:int(d in positives) for d in ['S','E','Ec','I','F']},'rationale':rationale})
add('原协议期满后，申请人可以再次提交续约申请材料。',[],'单纯再次申请机会未承诺保障延续。')
add('本药保障协议期满后继续为符合条件的患者供应治疗药物，延续期限为三年。',['F'],'实际药物供应保障的延续与期限。')
add('该药年度治疗费用不超过预算的一点五倍。',['Ec','F'],'费用条件由延续实际药费保障的父谓词直接控制。',{'verified_parent_context':[{'text':'满足下列条件的药品，保险继续承担其治疗费用三年。'}]})
add('该药年度治疗费用不超过预算的一点五倍。',['Ec'],'同一费用描述只决定材料办理排序，没有保障持续结果。',{'verified_parent_context':[{'text':'以以下条件安排申报材料的审核先后次序，此排序本身不决定药品保障关系。'}]})
add('申请人可自行选择单一专业或跨专业的沟通形式，讨论上市申请所需的研究方案。',[],'创新范围下申请形式及议题仍非实际指导资源。',{'verified_parent_context':[{'text':'本节适用于创新药研发项目。'}]})
add('机构为创新药研发专门配备专家团队，持续提供研究方案技术辅导。',['I'],'明确专门人员资源和研发指导。')
add('已经纳入创新药支持项目的申请人，应于每季末报告研究进度。',[],'已有创新项目身份与报告事务不自动成为当前支持。')
add('经评价确认具有原创属性的药物，可以获得本计划配置的专门研发资源。',['I'],'当前明确属性判定与获取实际支持的资格。')
assert len(tests)==38
inp=H/'synthetic38_candidate04_inputs.jsonl';inp.write_text(''.join(json.dumps(t['input'],ensure_ascii=False)+'\n' for t in tests))
expected=H/'synthetic38_candidate04_expected_PRIVATE.json'
dump(expected,{'status':'predeclared_before_candidate04_model_calls','prior30_reused_as_development_controls':True,'new_independent_validation':False,'tests':tests})
priorfreeze=json.loads((H/'candidate03_development_freeze.json').read_text())
freeze={**priorfreeze,'status':'candidate04_bounded_development_frozen_before_calls','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method_id':'LLM-v32-candidate04-development','prior_candidate03_prompt_sha256':sha(prior),'prompt_sha256':sha(prompt),'synthetic_control_expected_sha256':sha(expected),'synthetic38_input_sha256':sha(inp),'candidate03_all_outputs_preserved':True,'planned_calls':{'exposed240':10,'synthetic38':2,'development_total_nominal':12,'technical_maximum':36},'round_limit':'One authorized additional semantic revision only. Deliver all improvements and regressions after this round; root must confirm any full-corpus execution. No looping toward a kappa target.','scope_of_new_changes':['actual drug-benefit agreement duration','controlling parent predicate for substantive conditions','application communication form/topic versus actual support resources']}
freeze.pop('synthetic30_input_sha256',None)
dump(H/'candidate04_development_freeze.json',freeze)
audit=(H/'audit_development.py').read_text()
audit=audit.replace("'candidate03_development_freeze.json'","'candidate04_development_freeze.json'").replace("'candidate03_prompt.txt'","'candidate04_prompt.txt'").replace("'synthetic30_expected_PRIVATE.json'","'synthetic38_candidate04_expected_PRIVATE.json'").replace("'exposed240-first-run'","'exposed240-candidate04-first-run'").replace("'synthetic30-first-run',30","'synthetic38-candidate04-first-run',38").replace("'synthetic30-first-run/all_predictions.jsonl'","'synthetic38-candidate04-first-run/all_predictions.jsonl'").replace("'exposed240-first-run/all_predictions.jsonl'","'exposed240-candidate04-first-run/all_predictions.jsonl'").replace('LLM-v32-candidate03-development','LLM-v32-candidate04-development').replace('candidate03\'','candidate04\'').replace("'development_actual_QA_and_changes_PRIVATE.json'","'candidate04_actual_QA_and_changes_PRIVATE.json'")
(H/'audit_candidate04.py').write_text(audit)
print(json.dumps({'prompt_sha256':sha(prompt),'freeze_sha256':sha(H/'candidate04_development_freeze.json'),'control_n':len(tests)},ensure_ascii=False))
