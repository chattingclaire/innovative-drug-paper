"""Seal completed manual reading of inherited24+20; no model or original edits."""
import json
import sys
from pathlib import Path

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(HERE))
from candidate08_support import binding,read,sha,dump_new,DIMS,ROOT

# Own post-output working judgments, not replacement or added frozen expectations.
# The five comments are in S/E/Ec/I/F order and refer to the actual current input.
REVIEW={
'C06-PAIR-01-A':('00000','材料分组不涉及损害风险；分组送评不提出疗效要求；未规定费用支付；慢病/急救分组不说明创新属性；分组本身不决定保障获取'),
'C06-PAIR-01-B':('00001','美容用途排除没有安全命题；未讨论疗效或获益；未陈述费用责任或金额；用途名称不证明创新；明确药物保障不覆盖，负向范围仍属access'),
'C06-PAIR-02-A':('00000','编号日期核对无安全内容；未提出效果要求；协议登记不提供费用标准；未说明创新属性或支持；只核对原协议信息并归档，不当前规定延续'),
'C06-PAIR-02-B':('00001','无损害风险；无疗效评价；未给价格/药费责任；无创新属性或支持；当前规定药物保障协议有效十八个月，确定连续保障期间'),
'C06-PAIR-03-A':('00100','没有安全条件；没有效果条件；限制药费预算增幅，Ec独立成立；未给创新对象或支持；父文只许可再次谈判申请，未决定原有保障延续'),
'C06-PAIR-03-B':('00101','没有安全条件；没有效果条件；限制药费预算增幅；未给创新属性或支持；父文明确符合当前条件者保障延续十八个月，承接F结果'),
'C06-PAIR-04-A':('00000','只核对存档编号，不承接被存档毒性内容为当前要求；也不承接降低死亡率证据为当前要求；无经济内容；泛资格/存档不等创新资格；无保障或患者获取内容'),
'C06-PAIR-04-B':('11000','明确必须满足第九款毒性风险证据条件，S1；同一援引明确要求降低死亡率证据，E1；引用内容无费用评价；资格未给创新含义，S/E资格不自动I；条件不涉及保障/患者获取'),
'C06-PAIR-05-A':('00000','协商会安排无安全内容；无疗效内容；只定会场/签约手续，没有价格取值或费用责任；未给创新属性或支持；手续未确定保障延续或获取'),
'C06-PAIR-05-B':('00100','无安全内容；对照治疗在此仅费用基准，不是效果评价；价格相对治疗费用下调，有实际药价内容；未说明创新属性或创新支持；降价不独立证明患者支付能力或保障范围'),
'C06-PAIR-06-A':('00000','提交日期无安全实质；已列治疗方案只是延期对象，当前未推荐或评效果；无费用内容；无创新内容；延期提交资料不构成保障或获取安排'),
'C06-PAIR-06-B':('01000','无药物损害命题；当前推荐用药并陈述提高无进展生存目标，E1；无费用内容；未述创新/改良或支持；推荐不自动成为保障渠道或获取缺口'),
'C06-PAIR-07-A':('00000','毒性只是段落主题，当前预约沟通未要求安全内容；未述疗效；未述经济性；一般电话沟通未给创新研发支持；未述保障/患者负担/管理困难'),
'C06-PAIR-07-B':('10000','当前须补肝毒性发生率和监测结果，明确安全资料；毒性不是治疗效果；未述费用；安全资料义务不转为创新支持；监测结果本身不陈述管理难度或负担'),
'C06-PAIR-08-A':('00001','无安全内容；无效果内容；相邻明确另一独立任务的经济内容不能传入；无创新内容；自足地规定药物保障延续十八个月'),
'C06-PAIR-08-B':('00100','明确引导的两项没有安全内容；两项没有效果内容；当前以下内容引导疗程成本/费用分担，Ec1；两项无创新内容；费用分担未给患者支付能力或保障获取内容'),
'C06-PAIR-09-A':('00000','仅采购单据/入库职责，未明确质量安全或风险要求；未述疗效；核对单据不等陈述药价或费用责任；无创新内容；内部采购管理不确定患者获取渠道'),
'C06-PAIR-09-B':('00001','无安全内容；治疗药物称谓不等效果评价；覆盖但未规定费用责任；无创新内容；明确患者可在基层药房领取计划覆盖药物，access成立'),
'C06-PAIR-10-A':('00000','未给安全实质；未给效果实质；未给经济实质；无含义类别R7不能靠常识补创新；适用规定本身没有具体保障/获取内容'),
'C06-PAIR-10-B':('00010','定义只说明原创成分，无安全命题；无效果命题；无费用内容；给定R7定义明确首次开发活性成分的原创属性，attribute；适用规定未明确保障获取内容'),
'C06-PAIR-11-A':('00100','价格比例无安全内容；无效果内容；当前明确价格下调比例取值，Ec1；一般创新宗旨不证明无定义R7创新；价格比例不自行成为获取或患者可负担'),
'C06-PAIR-11-B':('00110','无安全内容；无效果内容；价格下调比例是当前药价内容；给定R7原创成分定义支持attribute，不从宗旨单独推I；价格规则未述患者支付能力或保障渠道'),
'C06-PAIR-12-A':('00000','联系人报告无安全内容；无效果内容；无费用内容；创新团队是对象，通用报送联系人义务不是支持；无临床获取或管理难度'),
'C06-PAIR-12-B':('00010','泛药学咨询未明示安全用途；未明示疗效用途；免费研发咨询不是治疗药费或药物支付；父文补足原创研发团队且当前持续技术咨询支持，research_support；未安排患者治疗获取或评价负担'),
'C07-PAIR-01-A':('00000','排版说明无安全内容；无效果内容；无费用内容；原创研发对象不把排版通用事务变实质支持；递文件便利不是临床药物获取'),
'C07-PAIR-01-B':('00010','泛方案设计未指风险；科学设计未具体承接疗效；无经济内容；明确向原创研发团队配置药学专家并给方案设计建议，research_support；没有患者获取/负担/管理困难'),
'C07-PAIR-02-A':('00100','无安全条件；无效果条件；药物治疗支出预算上限是经济约束；无创新内容；父文仅提交续约申请且是否续签另定，F0'),
'C07-PAIR-02-B':('00101','无安全条件；无效果条件；药物治疗支出上限是经济约束；无创新内容；父文将当前条件直接连接续签及有效十八个月，F1/access'),
'C07-PAIR-03-A':('00000','毒性仅主题，视频沟通/未来修订无当前安全实质；无效果内容；无经济内容；没有创新对象或实质支持；没有临床获取或管理困难'),
'C07-PAIR-03-B':('10000','当前逐项分析毒性成因且定风险控制措施，安全实质成立；无效果内容；无经济内容；没有创新支持；风险控制不自动等于临床管理困难'),
'C07-PAIR-04-A':('00001','确诊成人用于保障范围，不是损害风险；不是疗效判断；仅范围无药费责任或支付标准；无创新属性；当前拟限定具体药物保障人群，access成立'),
'C07-PAIR-04-B':('00101','保障人群未陈述风险；未述效果；基金承担70%药费明确费用责任；未述创新；拟定药物保障人群成立access，承担比例不自动加affordability'),
'C07-PAIR-05-A':('00000','资金稳定不是用药安全；未述效果；档案室储备资金未形成药物支付/治疗资源关系；无创新内容；无具体药物保障或临床负担'),
'C07-PAIR-05-B':('00100','医保基金可持续不是药物安全；无疗效命题；当前药品支付预算以基金可持续为约束，Ec1；无创新内容；未实质确定具体药物保障范围或患者负担'),
'C07-PAIR-06-A':('00000','无安全内容；无效果内容；无费用/预算内容；无创新内容；申请扩大范围前预约只给程序，未规定实际扩大'),
'C07-PAIR-06-B':('00001','无安全内容；无效果内容；覆盖未另给费用责任；没有产品改变或创新支持；当前拟本年度将具体药物纳入保障，access成立'),
'C07-PAIR-07-A':('00000','扫描件归档未述安全；无疗效内容；无经济内容；管理平台不证明药物创新；档案室/统计室连通未形成患者领药渠道'),
'C07-PAIR-07-B':('00001','未述安全用途；未述疗效；无费用内容；未述药物创新；处方转送协议药房并由患者领药，实际常规获取渠道成立'),
'C07-PAIR-08-A':('00000','减量未明示针对风险；剂量改变未明示疗效；未述药费或经济性；常规剂量调整不是产品创新；老年和减量本身不证明保障或管理困难'),
'C07-PAIR-08-B':('00001','监测未明示风险/毒性用途；未述治疗效果；管理负担未规定价格/药费或预算；未述创新；明确评价每日监测管理负担和社区实施难度，clinical_management'),
'C07-PAIR-09-A':('00101','无安全内容；无效果内容；保险承担药费为实际责任；无创新内容；明确覆盖为access，保险责任不另证患者可负担'),
'C07-PAIR-09-B':('00101','无安全内容；无效果内容；减免个人药费为费用责任调整；无创新内容；覆盖与患者难负担并减免各自支持access/affordability'),
'C07-PAIR-10-A':('01010','没有药物损害内容；当前比较终点反映治疗获益能力，明确效果设计用途；没有经济内容；原创研发对象配置专家及设计建议为research_support；未述患者获取或临床管理难度'),
'C07-PAIR-10-B':('10010','当前毒性风险监测方案建议有安全内容；没有治疗效果内容；没有经济内容；向原创研发对象配置专家及毒性技术建议为research_support；监测未陈述管理困难或患者获取'),
}


def main():
    source=HERE/'posthoc-inherited-audit-v1/outputs/inherited-controls/candidate08_author_and_inherited_controls_PRIVATE.json'
    selected=[r for r in read(source)['tests'] if r['input']['id'] in REVIEW]
    assert len(selected)==len(REVIEW)==44
    own_f={i:['access'] for i in ['C06-PAIR-01-B','C06-PAIR-02-B','C06-PAIR-03-B','C06-PAIR-08-A','C06-PAIR-09-B',
        'C07-PAIR-02-B','C07-PAIR-04-A','C07-PAIR-04-B','C07-PAIR-06-B','C07-PAIR-07-B','C07-PAIR-09-A']}
    own_f['C07-PAIR-09-B']=['access','affordability'];own_f['C07-PAIR-08-B']=['clinical_management']
    own_i={'C06-PAIR-10-B':['attribute'],'C06-PAIR-11-B':['attribute'],'C06-PAIR-12-B':['research_support'],
        'C07-PAIR-01-B':['research_support'],'C07-PAIR-10-A':['research_support'],'C07-PAIR-10-B':['research_support']}
    records=[]
    for test in selected:
        ident=test['input']['id'];row=test['candidate08_intact_actual_row'];vector,comments=REVIEW[ident]
        comments=comments.split('；');assert len(comments)==5
        cells={d:{'actual_label':row['labels'][d],'reviewer_working_judgment_NOT_GOLD':int(v),
            'reviewer_support':why,'actual_dimension_reason':row['dimension_reasons'][d],
            'actual_reason_semantically_supported':True,'status':'SUPPORTED'} for d,v,why in zip(DIMS,vector,comments)}
        assert all(c['actual_label']==c['reviewer_working_judgment_NOT_GOLD'] for c in cells.values())
        assert row['fairness_subtypes']==own_f.get(ident,[]) and row['innovation_subtypes']==own_i.get(ident,[])
        assert row['safety_quality_basis']=='no_quality_basis'
        evidence=[]
        for q in row['evidence']:
            why=cells[q['dimension']]['reviewer_support']
            if q['source']=='context':
                why='给定父条件/明确援引/引导后项或类别定义补足该维当前实质：'+why
            evidence.append({**q,'literal_binding_verified_by_frozen_validator':True,
                'semantic_relevance_after_actual_reading':'SUPPORTED','reviewer_support':why})
        availability=test['additional_field_expectation_availability']
        records.append({'id':ident,'input_intact':test['input'],'actual_intact_row':row,
            'dimension_review':cells,'evidence_review':evidence,'all_five_actual_reasons_read':True,
            'fairness_subtype_review':{'actual':row['fairness_subtypes'],'reviewer_working_subtypes_NOT_FROZEN_EXPECTATIONS':own_f.get(ident,[]),'status':'SUPPORTED'},
            'innovation_subtype_review':{'actual':row['innovation_subtypes'],'reviewer_working_subtypes_NOT_FROZEN_EXPECTATIONS':own_i.get(ident,[]),'status':'SUPPORTED'},
            'safety_quality_review':{'actual':row['safety_quality_basis'],'status':'SUPPORTED','basis':'无质量属性、质量标准或质量安全要求；毒性安全不自动转为质量依据。'},
            'inherited_additional_expectation_availability':availability,
            'inherited_additional_field_mechanical_mismatches':test['mechanical_additional_field_mismatches'],
            'inherited_label_mechanical_differences':test['mechanical_different_dimensions'],
            'issue_records_for_id':[],'material_complete_for_current_judgment':True,'confirmed_errors':[],'unresolved_boundaries':[]})
    attempts=[];raw_bindings=[]
    for key,n in [('inherited24',24),('inherited20',20)]:
        run=HERE/f'runtime-unchanged-v2/{key}-candidate08-first-run'
        aggregate=read(run/'all_predictions.json')
        assert aggregate['rows']==[json.loads(x) for x in (run/'all_predictions.jsonl').read_text().splitlines() if x.strip()]
        assert len(aggregate['rows'])==n and aggregate['issue_records']==[]
        raw_bindings.append({'run_key':key,'JSON':binding(run/'all_predictions.json'),'JSONL':binding(run/'all_predictions.jsonl'),
            'actual_rows_equal':True,'top_level_metadata':{k:v for k,v in aggregate.items() if k!='rows'},'top_level_issue_records_review':'空列表合适；当前44材料自足或由给定关系补足。'})
        for attempt in sorted((run/'batches').glob('*/attempts/attempt-*')):
            raw=read(attempt/'raw_output.json');validation=read(attempt/'validation.json')
            assert raw['issue_records']==[] and validation['valid'] and validation['errors']==[]
            attempts.append({'run_key':key,'attempt_path':str(attempt),'raw_output':binding(attempt/'raw_output.json'),
                'events':binding(attempt/'events.jsonl'),'validation':binding(attempt/'validation.json'),
                'actual_issue_records':[],'ever_material_issue_flags':[],'actual_flags_semantically_reviewed':True,
                'no_flags_is_observed_not_assumed_from_final_selection':True})
    assert len(attempts)==2
    assert sum(len(r['dimension_review']) for r in records)==220
    assert sum(len(r['evidence_review']) for r in records)==48
    original_qa=HERE/'execution-audit/inherited-controls/candidate08_technical_QA.json'
    assert sha(original_qa)=='6ab8b607c32687310ba8c35e5db41d50ef0d56c29476cf67f970625d32c12a34'
    original_execution=HERE/'posthoc-inherited-audit-v1/frozen_audit_actual_execution.json'
    adapted_execution=HERE/'posthoc-inherited-audit-v1/adapted_audit_actual_execution.json'
    assert read(original_execution)['exit_code']==1 and read(adapted_execution)['exit_code']==0
    protocol=ROOT/'outputs/coding-revision-20261007-r3/protocol'
    report={'status':'NO_CONFIRMED_SEMANTIC_ERROR_FOUND_WITHIN_INHERITED44_ONLY',
        'scope':'inherited24 + inherited20; all original inputs/contexts, 220 labels/reasons,48 evidence quotes, subtypes, quality, issues and every actual attempt.',
        'reviewer_is_prompt_author_not_external_human_validator':True,'inherited_expectations_visible':True,
        'source_bindings':[binding(HERE/'design_freeze.json'),binding(HERE/'candidate08_prompt_PROPOSED.txt'),binding(source),
            binding(HERE/'synthetic24_inputs_UNCHANGED.jsonl'),binding(HERE/'synthetic20_inputs_PROPOSED.jsonl'),
            binding(HERE/'synthetic106_expected_INHERITED_PRIVATE.json'),binding(protocol/'完整五维手册-v1.3.md'),binding(protocol/'共用操作说明-v1.4.md')],
        'original_frozen_audit_actual_exit':1,'original_frozen_audit_failure_and_traceback':binding(original_execution),
        'original_partial_technical_QA_preserved':binding(original_qa),'original_partial_is_not_claimed_complete_audit_exit0':True,
        'posthoc_minimal_adapter_actual_exit':0,'posthoc_adapter_execution_record':binding(adapted_execution),
        'posthoc_adapter_script':binding(HERE/'posthoc-inherited-audit-v1/audit_candidate08_field_availability_adapter.py'),
        'posthoc_exact_diff':binding(HERE/'posthoc-inherited-audit-v1/exact_adapter.diff'),
        'posthoc_separate_technical_QA':binding(HERE/'posthoc-inherited-audit-v1/outputs/inherited-controls/candidate08_technical_QA.json'),
        'old_missing_expected_fields_NOT_PREDECLARED_and_mismatch_null':True,'old_expected_labels_and_existing_fields_unchanged':True,
        'current_44_missing_additional_expected_cells':72,'current44_declared_additional_expected_cells':60,
        'mechanical_label_mismatches':sum(len(x['mechanical_different_dimensions']) for x in selected),
        'declared_additional_field_mismatches':sum(sum(v is True for v in x['mechanical_additional_field_mismatches'].values()) for x in selected),
        'mechanical_match_not_semantic_truth':True,'actual_binding_by_run':raw_bindings,'all_scope_actual_attempts':attempts,
        'units_actually_read':44,'dimension_cells_actually_read':220,'actual_dimension_reasons_read':220,'evidence_quotes_actually_read':48,
        'subtype_and_quality_records_actually_read':44,'actual_attempts_in_44_scope':2,'ever_material_issue_flags_in_44_scope':0,
        'confirmed_error_count_in_this_scope':0,'unresolved_boundary_count_in_this_scope':0,'rows':records,
        'inherited62_semantics_not_read_by_this_reviewer':True,'independent16_content_and_expectations_not_read_by_this_reviewer':True,
        'boundaries_in_other_scope_not_overruled_or_forced_here':True,'no_overall08_or_inherited106_PASS_conclusion':True,
        'next_exposed240':'NOT_RUN_AND_MUST_NOT_START_UNDER_PARENT_STOP_DECISION',
        'stage_PASS_gate_written':False,'models_restarted_or_next_stage_started':False,
        'original_prompt_runner_inputs_expectations_labels_or_manuscript_modified':False,
        'limitations':['This is synthetic development review of only44; it cannot cancel the separately confirmed62-scope error or validate real240/full4924.',
            'Missing inherited expected fields remain undeclared. The reviewer judgments recorded after reading actual output do not retrofit frozen expectations.',
            'Technical success, expected matching and this44 review are not external human validity or κ-target evidence. No new candidate iteration is proposed.']}
    out=Path(__file__).parent
    dump_new(out/'inherited44_actual_full_semantic_review.json',report)
    md=['# 候选08继承44实际语义审查','',
        '已完整实读继承24＋20共44条：220维标签及理由、48条引文、I/F子类、质量依据、顶层issue_records，以及两次实际尝试的全部材料flags（均未出现）。当前44范围确定错误0、未决边界0。',
        '冻结audit实际exit1，原KeyError、traceback及partial QA保留。另存最小只读适配实际exit0；旧86条未声明附加期望保持NOT_PREDECLARED、mismatch=null。当前44中继承24的72个附加期望单元未声明，继承20的60个已声明字段照原比较；未补造旧期望。',
        '44的标签机械差异0，已声明附加字段差异0；全部实际附加字段另按手册实读，机械匹配不代替语义判断。','',
        '| 实际批次 | JSON SHA | JSONL SHA | 顶层issues |','|---|---|---|---|']
    for b in raw_bindings:md.append('| '+b['run_key']+' | '+b['JSON']['sha256']+' | '+b['JSONL']['sha256']+' | [] |')
    md+=['','两包均实际核对JSON.rows与JSONL逐行相同。各批次只有attempt-01，raw issues为空、validation无错误；不由最终选中结果反推未读尝试。',
        '原审计、适配脚本、精确diff、运行记录、原partial QA与新独立输出目录均绑定同名JSON，逐条220维判断和48条引文相关性也在其中。',
        '此报告仅审44，不人工审62或独立16的语义/期望，不改其他范围的不同意见。44未见确定错误不能抵消独立62已报告的015传播误报；不生成08/继承106继续PASS门禁。原240依根停止决定保持NOT_RUN，不全量、不采纳、不拼接、不自动设计09。','']
    path=out/'inherited44_actual_full_semantic_review.md';text='\n'.join(md)
    if path.exists():assert path.read_text()==text
    else:path.write_text(text)
    print(json.dumps({'status':report['status'],'report':binding(out/'inherited44_actual_full_semantic_review.json'),
        'markdown':binding(path),'confirmed_errors_in44':0,'total_candidate_PASS_claim':False,'next240':'NOT_RUN'},ensure_ascii=False))


if __name__=='__main__':main()
