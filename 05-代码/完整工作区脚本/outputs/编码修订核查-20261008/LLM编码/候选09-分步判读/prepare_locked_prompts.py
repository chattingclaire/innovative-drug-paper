"""Offline-only preparation. No CLI/model calls; never changes prior files."""
import datetime
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
PRIOR=HERE.parent/'候选08-命题与证据判定'
PROTOCOL=PROJECT/'outputs/coding-revision-20261007-r3/protocol'

STAGE_A='''# 当前命题与语境使用记录：StageA

本阶段逐条完整阅读rows中的原始text、递归contexts及来源信息，只形成可审查的当前命题与语境使用记录，不输出五维标签或子类。后附完整v1.3手册及v1.4实质操作部分原文；它们规定语义边界，本阶段尚不生成最终编码。不得按部门、标题、编号、其他记录、历史标签或预期分布判断；不读取外部材料，不调用工具。记录是简短结论及原文依据，不输出冗长推理过程。

1. 对每个原单元列出current_propositions。保留当前句明确陈述的全部对象、动作、属性、并列成分和限定条件，不能仅保留办理主谓词而丢掉同句产品改变，也不能把作为对象的既有身份展开为其全部评价。定义、否定、目标、拟议和条件性内容均如实保留，不以是否已实施决定是否记录。每项用proposition_id按p1、p2依次编号；subject_or_object写对象，actions_attributes_and_qualifiers写当前动作/属性/全部限定，conditional_outcome写当前条件决定的结果；没有该关系时明确说没有，不补常识效果。unit_quotes为同ID当前text的连续逐字引文，至少一条。分析并列内容不拆并统计单元。

2. 逐一核对context_path_inventory列出的给定语境文本路径，并填context_records。库存只证明材料路径和字面内容，不证明语义关系。status为used、not_used或ambiguous：used仅限语境实际补足当前对象、指代、直接控制的父谓词、必须满足的实质条件与结果、表列关系或当前明确引导/援引的清单；相邻、同主题、来源标题、背景身份及未来另发文件不自动成为当前内容。父条款其余并列条件不全传下去；当前子条件若确实决定既有保障延续等结果，也不能只留子项字面而丢结果。用contribution普通语言说明具体补什么、为什么不补或哪里有解释边界；来源证书只证明出处/边界，字段名称不授予承接。

3. 每个context_record列paths、status、proposition_ids、unit_quotes、context_quote和contribution。paths使用库存提供的完整JSON Pointer；所有库存路径恰好覆盖一次，不漏、不增加。只有原文完全相同、作用和状态也相同的路径可合为一条。context_quote必须是该路径原文的连续逐字引文，不拼接。used须指向实际被补足的proposition_ids，并给当前text中建立对象/条件/援引/引导关系的unit_quotes；not_used的proposition_ids和unit_quotes均为空。ambiguous可列相关命题及原文，但须说明不确定处。无库存路径时context_records为空；原始contexts仍完整保留，不能把库存之外的来源元数据当作当前实质内容。

4. material_status只用sufficient、material_issue或boundary，material_note写实际依据。material_issue仅指原始给定材料确缺关键对象、指代、条件或表列，必须说明缺什么；完整自足句没有实质正类依据不等于缺料。完整材料下的解释分歧记boundary，不为一致强迫。不能把自己误连/遗漏语境当作材料缺口，也不能为了二元完整猜测。

按输出schema返回JSON：stage固定current_proposition_context_record，rows按输入ID完整原序返回；每行只含id、current_propositions、context_records、material_status、material_note。每项命题只含proposition_id、subject_or_object、actions_attributes_and_qualifiers、conditional_outcome、unit_quotes。不生成labels、dimension_reasons、evidence或五维结论，不声称真人编码，不输出Markdown或前后解释。
'''

STAGE_B='''# 根据完整材料逐维编码：StageB

本阶段读取rows的全部原始text、递归contexts、来源信息，以及stageA_records中同ID已封存的当前命题与语境使用记录。后附完整v1.3手册及v1.4实质操作部分原文；五维定义及原输出结构保持。StageA记录是待核的前序模型判断，不是已认证事实、人工标签或新材料，不能替换原文，也不能据它删去原contexts。输入包含每条记录SHA及前阶段封存绑定。不得按部门、标题、编号、其他记录、历史标签或预期分布判定，不使用外部材料或工具。

1. 先用原文核对StageA是否保留当前全部对象、谓词、产品属性、并列限定及实际条件结果，语境是否真的补足当前命题。定义、否定、拟议、条件和资料要求均按实质内容判断，不要求已有正面结果。必要父谓词、控制性援引及明确内容清单不能丢掉；独立邻段、背景主题、既有身份和未来文件不能自动传播。

2. 若StageA遗漏或误连，仍依据完整原材料独立判断，在对应dimension_reasons及同ID issue_records简短说明前序记录与原文关系不一致之处，不静默把它当真值，也不为迎合它改变标签。完整材料下两阶段分歧是执行审查事项，不自动记material_issue。真正影响判断的原材料缺口才记material_issue、说明缺什么，不猜该ID最终标签；解释边界保留本人判断及boundary_note。StageA原响应不得改写。

3. 对完整当前命题分别按共用手册核S、E、Ec、I、F及排除边界，五维可同时1或全0。每维理由说明当前内容与该维关系，不能以主题、引文出现维度词或前序判断代替依据。每个1至少给同ID source=unit的连续逐字引文；依赖原contexts时另给source=context连续逐字引文，不能引用StageA文字作为政策证据。0不附正类证据，全0证据为空。I/F子类各须独立内容依据，不能自动相互带出；S质量依据按原手册记录。

4. 返回原最终编码JSON：protocol_version固定CAL-5D-20260926-v1.3，execution_version固定LLM-binary-v32，release_stage固定final_binary_labels；rows按原ID完整原序，每行保留id、labels、dimension_reasons、evidence、fairness_subtypes、innovation_subtypes、safety_quality_basis，另有顶层issue_records。labels及理由均完整S、E、Ec、I、F，标签为整数0/1。原schema和枚举不变，不增加中间字段，不输出Markdown或前后解释，不声称真人编码。
'''

def binding(p):
    p=Path(p); b=p.read_bytes()
    return {'path':str(p.resolve()),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}

def put_new(p,data):
    data=data if isinstance(data,bytes) else data.encode()
    if p.exists():assert p.read_bytes()==data,f'Already locked file differs: {p}'
    else:p.write_bytes(data)

def main():
    a=PROTOCOL/'完整五维手册-v1.3.md'; b=PROTOCOL/'共用操作说明-v1.4.md'
    assert binding(a)['sha256']=='75ff8ebda018a15e008bc1075892000fb9c9c053943d05f04bbe193176c605a6'
    assert binding(b)['sha256']=='1b894ea4b6a7e7c06f04a9cbc38d8eaa7c9f28ffe536e839c7a48e0183fc27ee'
    # Only outer framing is added. The substantive source strings are verbatim,
    # including their source newlines; the v1.4 validation tail stays excluded.
    substantive=b.read_text().split('## 版本与验证纪律')[0]
    suffix='\n--- 冻结的完整v1.3手册原文 ---\n\n'+a.read_text()+'\n--- 冻结的v1.4实质操作部分原文 ---\n\n'+substantive
    for name,prefix in [('stageA_prompt.txt',STAGE_A),('stageB_prompt.txt',STAGE_B)]:
        assert 'RECODE25-' not in prefix and 'C05-NEW-' not in prefix and '0.80' not in prefix
        put_new(HERE/name,prefix+suffix)
    put_new(HERE/'manual_suffix_UNCHANGED.txt',suffix)
    runtime=HERE/'runtime';runtime.mkdir(exist_ok=True)
    for name in ['run_production_v32.py','validate_binary_output.py','output_schema_codex_compatible.json']:
        put_new(runtime/name,(PRIOR/'runtime-unchanged-v2'/name).read_bytes())
    report={'status':'PROMPTS_LOCKED_BEFORE_INDEPENDENT_REVIEW_NO_MODEL_CALLS',
      'created_at_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'candidate':'candidate09-two-step','model':'gpt-5.6-sol','reasoning_effort':'medium',
      'prompts':[binding(HERE/'stageA_prompt.txt'),binding(HERE/'stageB_prompt.txt')],
      'manual_suffix':binding(HERE/'manual_suffix_UNCHANGED.txt'),'manual_sources':[binding(a),binding(b)],
      'manual_scope':'Full v1.3 source text and v1.4 source substantive portion before validation discipline; no source line changed.',
      'B_runtime_byte_identical_copies':[binding(runtime/name)for name in ['run_production_v32.py','validate_binary_output.py','output_schema_codex_compatible.json']],
      'new_model_calls':0,'real_CLI_invocations':0,'independent_review_feedback_received_before_this_lock':False,
      'initial_scope':'Only a separately root/state frozen 11-row known-development input, not supplied here.',
      'old08_status':'FAIL; unchanged'}
    lock=HERE/'prompt_lock.json'
    if lock.exists():report['created_at_UTC']=json.loads(lock.read_text())['created_at_UTC']
    put_new(lock,json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'prompt_lock':binding(lock),'prompts':report['prompts'],'new_model_calls':0,'real_CLI_invocations':0},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
