"""Record the completed author24 manual reading; no model or label edits.

The explicit per-cell comments below were written after reading all actual
inputs, given contexts, reasons, quotes, subtypes, quality fields and issues.
Mechanical matching is reported separately and is not used as semantic truth.
Never read independent16 content or private expectations in this writer.
"""
import json
import sys
from pathlib import Path

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(HERE))
from candidate08_support import binding,read,dump_new,DIMS,ROOT

# Each ordered tuple independently states S/E/Ec/I/F judgments and support.
COMMENTS={
'01-A':[(0,'当前只陈述获准人群变化，未涉及损害或风险。'),(0,'未说明疗效或临床获益；不由适用人群变化推断。'),(0,'窗口递交无费用或支付内容。'),(1,'明确原获准成人增补儿童，是相对原使用属性的变化；无需创新字样或优效。'),(0,'未说明患者获取缺口或保障覆盖；儿童身份本身不足。')],
'01-B':[(0,'只有首次递交/窗口登记，没有安全内容。'),(0,'没有治疗效果或效果资料要求。'),(0,'没有费用或支付内容。'),(0,'首次递交是办理时点，不表明产品改变或创新支持。'),(0,'登记不确定药物覆盖、治疗获取或负担。')],
'02-A':[(0,'未陈述缓释改变的风险；不从常识补出安全效果。'),(0,'未陈述疗效获益；制剂改变不自动带出E。'),(0,'备案上传无费用内容。'),(1,'同句明确即释改缓释，办理形式不抹去制剂属性改变。'),(0,'未述获取、患者负担或管理困难。')],
'02-B':[(0,'通用名称和上传要求无安全实质。'),(0,'未要求疗效内容。'),(0,'无费用支付实质。'),(0,'通用名称是识别字段，不证明原创或改良。'),(0,'备案单不决定覆盖或患者治疗获取。')],
'03-A':[(1,'毒性监测方案是当前指导的实际内容，属于药物风险监测。'),(0,'毒性指导未陈述治疗效果。'),(0,'技术指导未述费用或经济评价。'),(1,'服务机构向明确原创药物研发团队提供毒性监测技术指导，施事/受事与实质支持均成立。'),(0,'没有获取缺口、覆盖、患者负担或管理难度评价。')],
'03-B':[(1,'当前要求执行毒性监测并报告结果，安全义务本身计S。'),(0,'监测所指毒性，未承接疗效用途。'),(0,'无药费支付或预算内容。'),(0,'研发团队承担义务，不是向其提供创新支持；团队对象名称不复制属性评价。'),(0,'一般研发监测和报告无治疗获取或管理困难。')],
'04-A':[(1,'要求提交毒性结果及风险控制方案，属于当前明确安全证据/处置要求。'),(0,'毒性结果未被规定为效果资料。'),(0,'无费用或支付内容。'),(0,'未给定创新对象或实质研发支持，安全资料义务不自行成为I。'),(0,'未涉及覆盖、缺口或患者负担。')],
'04-B':[(0,'父段仅说明毒性主题；本句安排电话/更新联系方式，不要求安全内容或处理风险。'),(0,'没有当前效果资料要求。'),(0,'没有经济实质。'),(0,'普通沟通安排未给定实质创新研发支持。'),(0,'没有治疗获取、患者负担或管理难度内容。')],
'05-A':[(0,'父文明确安全资料已在别处评估，不是当前费用子条件。'),(0,'同理不复制父文的既有疗效评估。'),(1,'当前限制药物治疗费用增幅，有实际费用约束。'),(0,'父子均未给创新属性或支持。'),(1,'父谓词明确满足当前条件可续签并延续原药物保障一年，费用条件决定保障连续性。')],
'05-B':[(0,'不复制背景已评估的安全身份。'),(0,'不复制背景疗效。'),(1,'与A相同费用增幅约束仍成立。'),(0,'没有创新属性、支持或资格优势。'),(0,'父文只允许递交申请，是否续签另定，不能补成保障延续。')],
'06-A':[(1,'当前明确必须提交以下五项，后项毒性分析补足安全内容要求。'),(1,'同一明确引导关系使临床疗效数据成为本句效果资料要求。'),(1,'药费预算是当前必须提交的实质清单内容。'),(1,'原制剂改良信息为明确创新属性信息要求，无须先给改良结果。'),(1,'未细分的公平性信息被明确列为当前提交要求，按dimension_information记录。')],
'06-B':[(0,'统一版式及未来另发文件不引导当前安全要求；不能传播后列专题。'),(0,'未提出疗效内容要求，后列主题不能自行传播。'),(0,'未提出费用预算要求。'),(0,'未来文件规划不等于创新属性讨论或研发支持。'),(0,'未当前要求公平性信息或安排实际保障。')],
'07-A':[(0,'没有药物损害风险内容。'),(0,'没有效果内容。'),(0,'只组织协商/会场顺序，没有价格取值、支付计算或费用承担。'),(0,'没有创新属性、支持或资格。'),(0,'协商事务本身未确定保障或患者获取。')],
'07-B':[(0,'无安全内容。'),(0,'无疗效内容。'),(1,'明确以实际采购价计算基金支付上限，价格与支付标准均有实质。'),(0,'没有创新内容。'),(0,'计算上限本身不明确保障延续、缺口、患者负担或管理难度。')],
'08-A':[(0,'没有安全内容。'),(0,'没有效果内容。'),(0,'保障申请时段无价格、费用或支付标准。'),(0,'未给创新属性或支持。'),(0,'拟申请者预约只规定受理程序，当前没有确定覆盖结果。')],
'08-B':[(0,'没有安全内容。'),(0,'没有效果内容。'),(0,'纳入保障但未规定费用、价格或支付标准。'),(0,'未陈述创新属性或支持。'),(1,'当前方案拟定具体药物本年度覆盖，计划状态不排除实质保障内容。')],
'09-A':[(0,'未讨论试验药风险或安全资料。'),(0,'提供药物治疗不自行说明疗效。'),(0,'未述免费、费用承担或支付。'),(0,'研究药物名称不证明原创/改良或支持。'),(1,'患者明确缺少可获得治疗，同时安排研究药治疗，获取缺口与对应安排齐备。')],
'09-B':[(0,'无安全要求。'),(0,'只描述随机分配研究药，未说明效果比较或疗效用途。'),(0,'未述费用或支付。'),(0,'研究参与/药物不自带创新支持。'),(0,'面向已入组者一般分配，未说明治疗获取缺口，试验例外条件不成立。')],
'10-A':[(0,'疗效终点建议没有安全内容。'),(1,'当前建议直接针对疗效终点科学选择，明确承接效果证据设计。'),(0,'无费用或支付内容。'),(1,'父文补足原创药物研发受事，当前提供终点科学技术建议，属于研发支持。'),(0,'未说明临床用药管理难度或获取/负担障碍。')],
'10-B':[(0,'格式编号无安全内容。'),(0,'未规定效果资料内容。'),(0,'无费用内容。'),(0,'虽对象是创新团队，排版和编号仍是通用事务，不能因对象整体传I。'),(0,'没有临床获取或管理难度实质。')],
'11-A':[(0,'疾病复发是效果结局，此处未讨论药物损害。'),(1,'明确比较药物降低复发效果且要求预设终点结果，E实质充分。'),(0,'无费用/资源经济内容。'),(0,'研究程序未给创新属性或研发支持。'),(0,'未说明保障、获取缺口或管理负担。')],
'11-B':[(0,'访视日期记录未承接安全用途。'),(0,'也未承接效果用途，不把所有研究方法自动计E。'),(0,'没有经济内容。'),(0,'研究日期记录不构成创新属性或研发支持。'),(0,'一般记录程序不表明治疗障碍或临床管理困难。')],
'12-A':[(0,'无风险或安全证据。'),(0,'无效果或获益陈述。'),(1,'药费由保险机构承担，当前明确费用责任。'),(0,'无创新内容。'),(1,'具体药物纳入保障计access；没有独立患者难负担命题，不自动附加affordability。')],
'12-B':[(0,'无安全内容。'),(0,'无效果内容。'),(1,'明确自付药费及个人药费减免，属于费用责任调整。'),(0,'无创新内容。'),(1,'覆盖与患者难负担/减免是两个独立成分，分别支持access及affordability。')],
}


def main():
    folder=HERE/'runtime-unchanged-v2/new24-candidate08-first-run'
    actual=read(folder/'all_predictions.json')
    raw_lines=[json.loads(s) for s in (folder/'all_predictions.jsonl').read_text().splitlines() if s.strip()]
    assert actual['rows']==raw_lines and actual['issue_records']==[]
    projection_path=HERE/'execution-audit/new-controls/candidate08_author_and_inherited_controls_PRIVATE.json'
    tests=read(projection_path)['tests']
    assert len(tests)==24 and len(COMMENTS)==24
    pairs=read(HERE/'synthetic24_pairs_PRIVATE_PROPOSED.json')['pairs']
    pair_by_id={m['input']['id']:p for p in pairs for m in p['members']}
    records=[]
    for test in tests:
        source=test['input'];row=test['candidate08_intact_actual_row'];short=source['id'].removeprefix('C08-PAIR-')
        remarks=COMMENTS[short];assert len(remarks)==5
        cells={d:{'actual_label':row['labels'][d],'reviewer_working_judgment_NOT_GOLD':v,
            'judgment_support':why,'actual_dimension_reason':row['dimension_reasons'][d],
            'actual_reason_semantically_supported':True,'manual_basis':pair_by_id[source['id']]['manual_basis'],
            'status':'SUPPORTED_BY_CURRENT_MATERIAL_AND_MANUAL'} for d,(v,why) in zip(DIMS,remarks)}
        assert all(c['actual_label']==c['reviewer_working_judgment_NOT_GOLD'] for c in cells.values())
        quotes=[]
        for ev in row['evidence']:
            d=ev['dimension']
            semantic=next(why for dim,(_,why) in zip(DIMS,remarks) if dim==d)
            if ev['source']=='context':
                if short=='05-A':semantic='父谓词明确保障续签/延续，补足当前费用子条件所控制的F结果。'
                elif short=='10-A':semantic='父文明确当前服务受事为原创药物研发团队，补足I研究支持对象。'
                else:semantic='当前以下五项的明确引导把此实质内容纳入本单元的当前提交要求。'
            quotes.append({**ev,'literal_and_source_binding':'PASS_FROZEN_VALIDATOR_AND_MANUAL_REVIEW',
                'semantic_relevance':'SUPPORTED','semantic_support':semantic})
        records.append({'id':source['id'],'input_intact':source,'actual_intact_row':row,'dimension_review':cells,
            'all_five_actual_reasons_read':True,'evidence_review':quotes,
            'innovation_subtypes_review':{'actual':row['innovation_subtypes'],'status':'SUPPORTED',
                'basis':'属性改变或改良信息对应attribute；向明确原创研发对象提供技术指导对应research_support；其余无子类。'},
            'fairness_subtypes_review':{'actual':row['fairness_subtypes'],'status':'SUPPORTED',
                'basis':'覆盖/连续性/治疗获取为access，未细分公平信息为dimension_information；仅12-B另有明确患者难负担及减免才加affordability。'},
            'safety_quality_basis_review':{'actual':row['safety_quality_basis'],'status':'SUPPORTED',
                'basis':'全部无质量标准、质量属性或质量安全依据；毒性安全本身不转为质量依据。'},
            'issue_records_for_id':[],'issue_review':'输入自足或由给定关系补足；没有需material_issue或boundary_note的未解缺口。',
            'confirmed_errors':[],'unresolved_boundaries':[]})
    assert sum(len(x['dimension_review']) for x in records)==120
    assert sum(len(x['evidence_review']) for x in records)==32
    protocol=ROOT/'outputs/coding-revision-20261007-r3/protocol'
    qa=HERE/'execution-audit/new-controls/candidate08_technical_QA.json'
    out=Path(__file__).parent
    report={'status':'NO_CONFIRMED_SEMANTIC_ERROR_FOUND_IN_AUTHOR24_DEVELOPMENT_CONTROLS',
        'review_scope':'Only author24 actual inputs, contexts, all 120 labels/reasons, 32 quotes, I/F subtypes, quality and top-level issues.',
        'author_controls_and_expectations_visible_to_reviewer':True,'reviewer_is_prompt_author_not_external_independent_human_validator':True,
        'technical_audit_actual_exit_code':0,'technical_QA':binding(qa),'actual_logical_requests_stage':2,'actual_attempts_stage':2,
        'author24_JSON':binding(folder/'all_predictions.json'),'author24_JSONL':binding(folder/'all_predictions.jsonl'),
        'JSON_rows_equal_JSONL_rows_actual_checked':True,'top_level_metadata':{k:v for k,v in actual.items() if k!='rows'},
        'top_level_issue_records_intact':[],'top_level_issue_records_review':'Empty is appropriate; all24 materials sufficient under given relations.',
        'source_bindings':[binding(HERE/'design_freeze.json'),binding(HERE/'candidate08_prompt_PROPOSED.txt'),
            binding(HERE/'synthetic24_new_inputs_PROPOSED.jsonl'),binding(HERE/'synthetic24_pairs_PRIVATE_PROPOSED.json'),
            binding(projection_path),binding(protocol/'完整五维手册-v1.3.md'),binding(protocol/'共用操作说明-v1.4.md')],
        'unit_count':24,'dimension_cells_actually_read':120,'actual_dimension_reasons_read':120,'quotes_actually_read':32,
        'I_subtypes_F_subtypes_and_quality_records_read':24,'confirmed_error_count':0,'unresolved_boundary_count':0,
        'mechanical_expected_label_mismatches':sum(len(x['mechanical_different_dimensions']) for x in tests),
        'mechanical_expected_additional_field_mismatches':sum(sum(x['mechanical_additional_field_mismatches'].values()) for x in tests),
        'mechanical_match_not_treated_as_semantic_truth':True,'rows':records,
        'NOT_RUN':{'inherited62':62,'inherited24':24,'inherited20':20,'exposed240':240},
        'independent16_content_or_expectations_semantically_read_by_this_reviewer':False,
        'independent16_actual_semantics_not_concluded_here':True,'stage_continuation_PASS_gate_written':False,
        'next_stage_or_model_started_by_reviewer':False,'labels_prompt_expectations_or_manuscript_modified':False,
        'limits':['Only new synthetic development behavior reviewed; no claim that six real exposed cases, inherited106, 240 or4924 have improved.',
            'No external human validity, κ target, distribution alignment, score selection or causal isolation claim. Root must separately combine technical and independent16 reviews and authorize any continuation.']}
    dump_new(out/'author24_actual_full_semantic_review.json',report)
    md=['# 候选08首阶段作者24实际语义审查','',
        '冻结技术审计实际exit0：首阶段2逻辑/2尝试，均首个技术有效；技术PASS不等于语义已证。',
        '作者24全部120维标签及理由、32条引文、I/F子类、质量依据与顶层issues已经实际审读，当前确定错误0、未决边界0。旧期待标签/附加字段机械差异也均0，但不以匹配代替手册判断。',
        '作者24 JSON SHA：'+report['author24_JSON']['sha256'],
        '作者24 JSONL SHA：'+report['author24_JSONL']['sha256'],
        '实际核对JSON.rows与JSONL逐行相同；顶层issue_records为空，metadata符合冻结结构。','',
        '| 构造对 | 当前实际判读 |','|---|---|']
    for pair in pairs:
        ms=pair['members'];vals=[]
        for m in ms:
            r=next(x for x in records if x['id']==m['input']['id'])
            vals.append(r['id'][-1]+': '+','.join(f'{d}{r["actual_intact_row"]["labels"][d]}' for d in DIMS))
        md.append('| '+pair['pair_id']+' | '+'；'.join(vals)+' |')
    md+=['','重点边界均按当前实质区分：属性变化保留；申请人安全义务不变创新支持；父条件仅传直接保障延续结果；未来专题文件不传播五维；价格协商程序Ec0；拟申请与拟覆盖不同；试验获取缺口需与安排同时成立；保险费用责任不自动增加affordability。',
        '完整逐维理由、逐条引文相关性和附加字段意见保存在同名JSON。此为提示作者对可见期望的合成开发控制审查，不是独立真人效度验证。',
        '独立16正文/期望未人工审读；由独立检查者另报。本报告没有写继续PASS门禁、没有启动任何模型或后续范围。继承106和原240仍NOT_RUN，不声称六例或完整语料已修好。','']
    path=out/'author24_actual_full_semantic_review.md'
    content='\n'.join(md)
    if path.exists():assert path.read_text()==content
    else:path.write_text(content)
    print(json.dumps({'status':report['status'],'report':binding(out/'author24_actual_full_semantic_review.json'),
        'markdown':binding(path),'technical_QA':binding(qa),'confirmed_errors':0,'independent16_semantic_read':False,
        'stage_gate_written':False},ensure_ascii=False))


if __name__=='__main__':main()
