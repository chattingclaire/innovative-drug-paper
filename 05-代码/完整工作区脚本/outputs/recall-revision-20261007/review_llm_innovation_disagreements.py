"""Read-only case interpretation; never edits labels or declares human adjudication."""
from pathlib import Path
from collections import Counter
import hashlib,json,datetime
OUT=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
notes={
'00004':('政策目的与实体措施的计入粒度','current_prompt_exclusion_is_explicit','LLM将鼓励研究创制作为制定宗旨排除，A/C将明确创新研发政策目的计入。当前提示词确实要求仅有鼓励创新的宗旨不自动计入；此项不能直接按历史A/C认定为LLM漏识别。'),
'00009':('已核验创新对象与历史参照理由不同','current_material_supports_defensible_inclusion','本单元实质陈述比较临床优势，实际contexts的verified_innovation_scope_v27证书明确创新药/改良型新药。当前手册两个锚点均可定位；历史A/C理由称未给创新对象，不能据旧理由判本次LLM误纳。'),
'00028':('已核验创新对象与具体资源支持','current_material_supports_defensible_inclusion','当前明确优先配置沟通资源、加强指导促进研发，实际证书明确创新/改良对象；比单纯程序身份多了实体支持措施。LLM与规则的纳入有现行操作化依据，A/C原0保留作历史分歧。'),
'00032':('创新支持机制向程序实施事项扩散','implementation_boundary_requires_calibration','当前为申请人依计划提出沟通申请；LLM把其视为创新支持机制实施。存在把创新对象向一般申请义务传播的过宽风险，需固定实体支持措施与程序执行的边界；本复核不改标。'),
'00033':('创新支持机制向程序实施事项扩散','implementation_boundary_requires_calibration','当前仅列面对面/视频/电话/书面沟通形式，LLM借支持机制语境赋I。现行手册不从程序名称自动赋I；沟通方式是否属于实体创新支持的粒度尚需统一，不能用旧A/C或分数裁定。'),
'00034':('创新支持机制向程序实施事项扩散','implementation_boundary_requires_calibration','当前规定错过首次沟通期限后的提交路径；LLM将替代程序路径当创新研发支持内容，A/C按时点手续排除。应复核当前措施是否新增实质研发支持，而非沿支持对象泛化。'),
'00060':('创新支持机制向程序实施事项扩散','implementation_boundary_requires_calibration','当前要求列后续沟通时间点和问题，LLM依据创新对象证书将计划要求纳入支持。证书确实存在，但它不自动证明每条沟通手续皆是创新内容；这是实施粒度分歧。'),
'00061':('创新支持机制向程序实施事项扩散','implementation_boundary_requires_calibration','当前为阶段性资料提交计划；LLM以滚动沟通支持机制纳入，A/C按提交节奏排除。需区分针对创新的实质便利与通用报送义务。'),
'01385':('政策目的与实体措施的计入粒度','current_prompt_exclusion_is_explicit','当前以鼓励药品创新制定办法，LLM按只有宗旨排除，A/C计创新政策目的。当前提示词采取更窄的实体措施口径；不能把这项历史差异直接等同模型无视创新字样。'),
'01389':('数据专有保护实体权利与期限','rights_scope_boundary_requires_calibration','所属段落已定义给予最长6年保护期，当前句规定起算条件。LLM将实体专有保护期限纳入相关知识产权，A/C按时点程序排除；需统一实体权利期限与纯办理时点的边界。'),
'01393':('数据专有保护实体权利与对象范围','rights_scope_boundary_requires_calibration','当前定义首次用于境内上市、未公开且完整的数据；LLM按受保护对象范围纳入，C按数据条件非创新排除，A原待定未进入对应配对。需核专有保护对象定义是否已构成I属性，而非将所有保密数据纳入。'),
'01406':('数据专有保护实体权利与范围例外','rights_scope_boundary_requires_calibration','当前实质限定保护范围且排除BA/BE/疫苗免疫原性数据。LLM按权利范围纳入，C按未明创新排除，A原待定。不可把此实体范围与一般文件保密事务混为同类。'),
'01445':('创新研发框架承接与档案沟通用途','implementation_boundary_requires_calibration','实际同段明确罕见疾病创新药物临床研发实施框架；当前持续完善框架并贯穿研发沟通。LLM视为创新支持作用方式，A/C视为档案用途。语境有创新对象，分歧在当前命题是否构成实体支持。'),
'01694':('明示注册分类与类别名称排除','registration_classification_boundary_requires_review','原文明示按注册分类批准的1类化学药/生物制品等，A/C及规则将注册创新分类计入，LLM因整组未显式称创新而排除。存在把明确注册分类过度当一般类别名称排除的风险；正式裁定需绑定相应注册分类表。'),
'01728':('政策目的与实体措施的计入粒度','current_prompt_exclusion_is_explicit','当前为支持创新药研发制定并印发优化试点方案。LLM按宗旨/文件发布排除，A/C按制度支持部署计入。当前提示词明确仅发布标题含创新药文件不等于实体支持，属于操作化粒度差。'),
'02501':('政策目的与实体措施的计入粒度','current_prompt_exclusion_is_explicit','当前全链条支持创新药发展的措施印发句。LLM按未展开实体措施排除，A/C计政策支持目标。应统一政策关注测量是否计明确创新支持目的，不能为了κ将任一口径悄然回填。'),
'03484':('普通设计要求与具体药品改良','possible_LLM_overinclusion','本句规定计量装置刻度、易理解、随包装附带及图示，没有明确相对既有产品的变化或新颖性；LLM把普通具体设计直接称设计改变。当前手册明确普通设计/适宜性不自动等于I，存在过度纳入问题。'),
'03489':('明确改良设计与过严具体性要求','possible_LLM_underinclusion','当前已明示针对多病多药改善制剂特征，同段还给出缓释设计与计数/提醒设备。LLM以未指出具体设计属性排除，存在对已给改良命题及同段证据读取不足的问题。'),
'03894':('普通处方比较与创新属性信息','current_exclusion_has_manual_basis','当前仅要求说明与已上市处方对比情况，未明原创、改良或具体变化。LLM0与A0符合现行提示词对普通比较动作不自动赋I的边界；C1保留为较宽属性信息判读，不能直接叫LLM漏识别。'),
'04737':('一般商业秘密保密与创新知识产权','possible_LLM_overinclusion','当前是不披露商业秘密、未披露信息等的一般保密义务及法定例外，未具体规定创新属性、专有试验数据排他期或创新激励。LLM把受保护信息广泛等同创新相关知识产权，存在过度纳入风险。')}

def main():
 audit_path=OUT/'指标诊断弱项与逐例原文.json';audit=read(audit_path);rows={}
 for r in audit['disagreements']:
  if r['method']!='llm_gpt56_sol_v30' or r['dimension']!='I':continue
  if r['id'] not in rows:rows[r['id']]={'id':r['id'],'group':r['group'],'text':r['unit_text'],'LLM_label':r['left_label'],'LLM_reason':r['left_reason'],'original_AI_references':{},'actual_shared_contexts':r['actual_shared_contexts']}
  rows[r['id']]['original_AI_references'][r['reference']]={'label':r['reference_label'],'reason':r['reference_reason'],'comparison_scope':'Original exposed AI reference; not new human adjudication.'}
 assert {rid.removeprefix('RECODE25-') for rid in rows}==set(notes) and len(rows)==20
 for rid,r in rows.items():
  category,interpretation,reason=notes[rid.removeprefix('RECODE25-')];r.update({'disagreement_category':category,'read_only_interpretation':interpretation,'interpretation_reason':reason,'revised_label_issued':False,'human_adjudication':False})
 sources=[audit_path,OUT/'effective_blind_inputs_v30_v3.jsonl',OUT/'llm-v30/protocol-v1.3.md',OUT/'llm-v30/完整系统提示词-v30-候选03.txt',OUT/'三部门编码指标.json',Path(__file__)]
 report={'status':'completed_read_only_semantic_review','checked_at':datetime.datetime.now().astimezone().isoformat(),'scope':'20 unique main1057 LLM innovation disagreement units from all weak overall/department comparisons; no claim to review all 4924 semantic labels.',
 'reviewer':'statistics agent read-only policy-text/method audit','actual_shared_contexts_fully_read':True,'unit_count':20,'category_counts':dict(Counter(r['disagreement_category'] for r in rows.values())),
 'interpretation_counts':dict(Counter(r['read_only_interpretation'] for r in rows.values())),
 'core_findings':['Some old A/C reasons explicitly deny the innovation scope anchor that is present in the current full verified certificate (00009/00028). Such relative disagreement is not proof that the current machine label is wrong.',
 'Program-purpose clauses versus concrete support measures, implementation mechanics, and data-protection rights show a substantive granularity/operational-boundary difference between historical AI readings and the current prompt.',
 'Ordinary device design, general commercial confidentiality and an explicit formulation-improvement instruction contain identifiable overinclusion/underinclusion risks in the LLM reading; aggregate direction agreement does not cure them.'],
 'historical_reference_vs_current_material_warning':'Original A/C submissions are not overwritten and were not rerun on the current full v3 display. Their reasons/labels remain exposed development references, not a current human gold standard.',
 'labels_modified':False,'prompt_or_code_modified':False,'human_validation_completed':False,'semantic_ground_truth_claim':False,'cases':list(rows.values()),'source_sha256':{str(p):sha(p) for p in sources}}
 path=OUT/'llm-v30/I-disagreement-semantic-review-v3.json';path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 lines=['# LLM创新性分歧只读复核','', '逐读主1057中20个独特分歧单元的原句、完整当前共同语境、证书、现行手册和双方理由；不改变标签，不作为真人裁定。','',
 '分歧来自当前完整语境与历史AI理由不一致、创新支持计入粒度不同，以及可定位的LLM过度纳入或漏读风险。不能把相对AI参照的FP/FN全部解释为已裁定错误。','',
 '|类型|单元数|','|---|---:|']
 for k,v in report['category_counts'].items():lines.append(f'|{k}|{v}|')
 lines+=['','|ID|LLM|原AI参照|类型与只读判断|','|---|---:|---|---|']
 for r in rows.values():lines.append('|'+ '|'.join([r['id'],str(r['LLM_label']),', '.join(c+'='+str(v['label']) for c,v in r['original_AI_references'].items()),r['disagreement_category']+'：'+r['interpretation_reason']])+'|')
 lines+=['','00009/00028的当前创新对象证书真实存在；创新支持实施步骤仍需区分实体资源支持与一般申请/提交义务。03484、03489、04737说明共同宏观排序并不能替代逐句执行检查。原A/C未被回填成当前材料的真人金标准。']
 (OUT/'llm-v30/I-disagreement-semantic-review-v3.md').write_text('\n'.join(lines)+'\n');print(json.dumps({'status':report['status'],'n':20,'categories':report['category_counts'],'labels_modified':False,'output':str(path)},ensure_ascii=False))
if __name__=='__main__':main()
