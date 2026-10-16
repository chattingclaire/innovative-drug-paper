"""Read-only review record. This script never mutates labels, prompts, or code."""
from pathlib import Path
from hashlib import sha256
from collections import Counter
import json

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent

def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()

def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]

# Human-readable audit notes written by the reviewing AI agent after reading the
# complete actual v3 unit/context, original outputs/reasons, manual and prompt.
# These are diagnostic interpretations, not fresh human labels or adjudications.
B = 'construct_boundary_requires_domain_adjudication'
S = 'current_output_supported_reference_disputed'
E = 'clear_execution_overreach_candidate'
P = 'possible_execution_overreach_requires_scope_adjudication'
T = 'operational_boundary_tension'
NOTES = {
'00005': (B, 'qualification_unmet_need_vs_actual_access', '突破性治疗适用条件中的尚无有效防治手段具有未满足需求含义，但当前命题仍是申请资格；是否仅凭治疗缺口即计F，与要求具体获取安排的执行口径不同。当前L0有执行口径依据，不能直接当成漏判。'),
'00009': (B, 'qualification_unmet_need_vs_actual_access', '完整语境含创新药或改良型新药对象证书，本项尚无有效防治手段且该药可提供手段属于资格比较内容。对象没有遗漏；治疗效果缺口是否同时构成保障获取仍需裁定，不能由创新资格或临床优势自动传播F。'),
'00126': (B, 'urgent_market_entry_vs_administrative_deadline', '当前同时有临床急需、境外已上市境内未上市、罕见病用药和70日上市审评通道，具备缺口与进入安排的联系；但加速时限是否属于保障获取，尚未独立裁定。仅列领域裁定候选，不作为改标依据。'),
'00174': (B, 'nonresponse_vs_treatment_access', 'PD-1治疗有效率及其余患者未获有效治疗描述的是疗效不足和研发需求，未说明供药、费用或治疗获得障碍。L0可按疗效与获取区分解释；原A/C以未满足需求赋F属于较宽边界。'),
'00239': (B, 'childhood_research_need_vs_access_arrangement', '当前鼓励针对儿童肿瘤迫切需求开展研发，超出仅有人群名称，但没有现行药品保障或获取措施。研发填补治疗空白与实际可及之间的构念界线应统一裁定。'),
'00255': (B, 'research_population_vs_treatment_access', '尽早开展特殊人群研究以满足其医疗需求是研究覆盖安排，不直接说明原不可得治疗者取得药物。L0符合研究代表性不自动F的执行规则；原参照把治疗需求作F依据。'),
'00256': (B, 'research_evidence_gap_vs_treatment_access', '肝功能损害人群试验资料不足会影响满足上市后治疗需求，但当前要求仍为开展人群研究。把研究证据缺口与药品获取缺口分开有依据，不能直接认定漏判。'),
'00270': (B, 'randomization_probability_vs_new_access', '2:1分配目的为使更多已入组患者接受潜在更优治疗；冻结手册例外要求原本不能获得治疗的人群，候选03明确排除仅改变分组概率。当前L0是遵循明确执行澄清；较宽的治疗机会读法须领域裁定，不能以审读倾向改标。'),
'00322': (B, 'drug_supply_purpose_vs_substantive_arrangement', '当前把用药监测评价作为基本药物和药品供应保障制度的基础要求，具有明确药品保障联系，但主要陈述制度目的。应裁定目的性注意力是否足以构成实质获取命题；不能仅因抽象而排除，也不能只凭保障字样赋F。'),
'00589': (S, 'mixed_flowchart_actual_coverage_branch', '完整流程图不只有商保推荐目录，还包含谈判成功后实际纳入基本医保目录的分支。候选03要求逐分支判断，L1有实际医保纳入依据；原A/C0不能用商保目录不等于承保一概解释整图。'),
'00646': (S, 'actual_basic_insurance_inclusion', '当前规定确认医保支付标准后纳入基本目录，是实际给付覆盖安排。冻结口径不要求另写患者已受益，L1有依据；原A0可能把保障纳入条件读得过窄。'),
'00653': (B, 'fairness_principle_vs_contextual_definition', '当前维护医保制度公平性是原则性句子，后文解释治疗领域和保障空白。是否后文定义足以消解当前公平性原则，还是属于不同命题标签传播，需统一界定；不自动填dimension_information。'),
'00749': (S, 'coverage_exclusion_in_budget_example', '测算示例明确美容适应症不属医保支付范围，因此排除其相关费用。条件或示例不使明确给付范围失去F，当前L1有执行口径依据；不能只因同时为经济性示例就删除F。'),
'00837': (S, 'already_covered_management_reclassification', '已核验上位对象为协议到期谈判药品转常规目录分支，原则纳入乙类是在既有保障下转换管理类型。当前没有另定实际纳排或患者负担，L0符合候选03的对称排除。'),
'00952': (S, 'explicit_payment_scope_content_requirement', '当前明确要求论证确定药品支付范围，并非只列文件名或评议程序。政策对保障范围内容的关注不要求已完成覆盖改善，L1有实质内容要求依据。'),
'01009': (S, 'verified_parent_actual_directory_exit', '本项撤销药品批准证明文件的药品承接已核验调出目录药品范围父谓词。完整命题为实际目录退出条件，L1不能被简写成仅许可证状态；旧参照0可能未充分使用该谓词。'),
'01051': (S, 'conditional_actual_inclusion_exclusion', '报价不高于医保支付意愿时纳入乙类，否则不纳入，明确规定条件性实际纳排。限制或否定方向仍可构成F，L1有依据，不能因其同时涉及价格就只计Ec。'),
'01062': (S, 'already_covered_management_reclassification', '已竞价药品在标准到期后经专家同意转常规乙类，当前主要是既有覆盖管理转类。下一句暂按原标准等内容不自动复制进本句，L0有对称边界依据。'),
'01087': (B, 'guideline_formulation_purpose_vs_access', '为健全药品供应保障制度制定综合评价指南，当前具有药品保障对象但实际谓词是制定指南。制度目的与实质获取安排之间存在边界，不宜把目的语一律当作获取，也不能用没有具体药名作为排除理由。'),
'01149': (B, 'clinical_need_evaluation_vs_access', '当前创新性评价比较药品满足临床需求的情况，邻句强调填补治疗空白。满足需求与可及障碍并非同一命题；是否将评价治疗缺口计作F，需要与药监同类句统一，不从下一句无条件传播。'),
'01242': (S, 'verified_parent_actual_directory_exit', '撤销或未批准药品批准证明文件的药品承接调出目录范围父句，是实际医保退出条件。L1有完整父谓词依据；原A/C仅按许可状态判0可能忽略当前列表承接。'),
'01503': (S, 'general_patient_path_information', '患者体验资料中的就诊路径和当下治疗选择是一般诊治现状信息。相邻未满足需求是独立列表项，不应传播；本项未独立要求获取渠道、供应或支付障碍资料，L0可辩护。'),
'01723': (E, 'procedural_fallback_inferred_as_continued_coverage', '调整支付范围谈判失败后，企业可选以原范围重新谈判或按原范围简易续约；当前安排的是可选择的办理退路，未保证谈判成功或继续给付。L理由把办理路径推成实际保障，与候选03重新谈判路径不得推定继续给付的明确排除有冲突。'),
'01994': (B, 'expert_work_assignment_vs_content_requirement', '专家组就目录、主要规格、参照药和医保支付范围提出意见，同时有实质评价对象和专家任务归属。是否属于明确评价范围内容还是评议工作安排，需要统一；不能把所有专家工作都F，也不能删除其明确内容要求。'),
'02179': (S, 'explicit_payment_scope_content_requirement', '当前要求论证确定拟谈判竞价药品医保支付范围，已经是给付范围内容要求。L1符合内容要求可计入维度的冻结原则，不要求先证明患者获取改善。'),
'02272': (S, 'commercial_recommendation_not_actual_underwriting', '商保创新药目录供商业健康保险或医疗互助参考，当前没有某保险计划实际承保安排。L0符合推荐目录不等于实际保障覆盖的明确规则，原A/C更宽的多层次保障解释不能直接作为真值。'),
'02290': (S, 'verified_parent_conditional_directory_exit', '标签信息不完整等条件承接重点考虑调出基本目录的父谓词，当前实质为指定药品的退出范围条件。L1有实际给付纳排内容依据，重点考虑或条件性不自动使其失去F。'),
'02317': (S, 'explicit_payment_scope_content_requirement', '专家确定下一协议期支付标准和支付范围，当前独立提出范围内容，并非只说转为某管理类别。L1具有实质范围安排依据。'),
'02358': (P, 'general_formulary_optimization_vs_actual_scope', '医疗机构依据安全有效经济和病种特征及时优化用药目录，具有药品配备选择含义，但未写具体纳排范围或当前供药条件。L把优化目录直接认作实际范围，可能过宽；需先裁定一般目录优化原则与具体配备安排的界线，不直接改标。'),
'02361': (S, 'general_pharmacy_organization', '鼓励医联体县域医共体建立药品联动机制并规范目录，当前是一般组织机制。没有具体配备范围、获取限制或临床管理困难，L0有依据。'),
'02391': (S, 'general_pharmacist_service_organization', '探索医院间临床药师会诊是药学服务组织安排，没有当前具体药品获取障碍或用药管理难度。L0符合一般服务不自动F。'),
'02393': (S, 'general_family_doctor_drug_services', '家庭医生开展咨询、管理监测、药箱指导和科普是一般药学服务包；未独立描述获取或具体管理困难，L0可辩护。不能因为含管理二字即计clinical_management。'),
'02563': (E, 'directory_work_categories_inferred_as_actual_coverage', '本项仅说明目录调整涉及三类药品，工作分为调入和调出两项。它没有规定某药或某类别实际被纳入排除、具体给付条件或范围。L从调入调出工作类别推实际覆盖，与候选03评议工作归属及一般目录事务排除有冲突。'),
'02570': (P, 'adjustment_object_eligibility_vs_actual_coverage', '国家层面中药饮片调整对象仅限国家标准饮片，限定的是调整工作的对象资格或管辖范围，不必然等于最终给付覆盖。L直接作为实际给付纳入条件可能过宽；需与一般申报资格和实质覆盖条件对称裁定。'),
'02598': (S, 'expert_consideration_not_actual_coverage', '目录外国家基本药物仅作为请专家重点考虑的对象，当前不保证进入医保。L0遵循一般评议资格不等于实际给付覆盖，与01723应作对称控制。'),
'03005': (B, 'rare_disease_research_design_vs_access', '真实世界研究应用于缺乏有效治疗的罕见病，并采用单臂外部对照，当前实际谓词为研究设计。未满足治疗需求是明确背景，是否同时构成保障获取仍需裁定；不能由罕见病或试验对象自动赋F。'),
'03274': (S, 'verified_parent_actual_fund_payment_condition', '以疾病诊断或治疗为目的承接参保人目录内药品费用符合条件可由基金支付的父谓词，完整命题是实际给付用途条件。L1有明确保障条件依据，A/C0另要求获取障碍或患者负担比当前执行口径更窄。'),
'03282': (S, 'already_covered_management_reclassification', '协议期内谈判药品纳入乙类管理，只给既有谈判药品分类，没有独立给付纳排、费用或保障连续性条件。L0符合已覆盖药品甲乙分类不自动F。'),
'03361': (S, 'verified_parent_new_payment_scope_condition', '独家药品承接协议未到期且调整支付范围的条件列表，父谓词明确以补充协议确定新的支付标准和支付范围。当前不是孤立类别名称，L1有真实范围内容；原A/C0可能未充分使用父谓词。'),
'03425': (S, 'specific_cognitive_medication_management_obstacle', '难以记住是否何时如何服药或混淆药品，是具体药品使用管理障碍。手册不要求描述障碍后还必须另提出评价动作；L1有依据，C0的附加要求偏窄。'),
'03430': (T, 'specific_motor_obstacle_vs_administration_convenience', '肌力下降导致打开包装、准确量取和使用药物时遇到困难，是明确具体操作障碍。L理由称必须另有管理安排，手册73允许直接实质讨论管理障碍；但候选03同时排除仅给药操作便利。应裁定具体身体功能障碍与一般便利性的界线，暂不将其认定为已确认执行漏判。'),
'03482': (P, 'general_cognitive_adaptation_vs_identified_obstacle', '当前要求设计适配老年患者认知水平，上文仅说认知能力影响合理用药和管理。L理由将其直接称为认知障碍，但本句未像03425指出具体混淆或管理困难。一般认知适配与有明确障碍的适配需要对称核对；当前F1可能偏宽。'),
'03715': (S, 'application_eligibility_not_actual_coverage', '已在商保目录的药品可申报基本目录、不受五年上市限制，当前仅放宽申请资格，未承诺实际纳入基本医保。L0遵循明确资格排除。'),
'03759': (B, 'price_warning_with_burden_purpose', '本句规定挂网价格红黄标预警，前句明确减轻患者负担目的。价格预警是否已形成当前可负担机制，或目的不应传播到价格标识内容，是实际目的承接边界；不能把价格自动F，也不能无视真实患者负担联系。'),
'03803': (S, 'commercial_directory_fact_used_for_application_eligibility', '商保推荐目录药品数量及撤市调出事实在当前用于限定基本目录申报条件，未形成实际承保或给付。L0符合资格用途和商保推荐不自动覆盖的规则。'),
'04094': (E, 'ordinary_trial_supply_inferred_as_treatment_access', '申办者向研究者和试验机构提供试验用药品，是常规试验物资职责。当前没有原本无法获得治疗者及相应安排，L仅凭提供药品推获取，与手册83及候选03试验获取例外条件冲突。'),
'04099': (E, 'ordinary_trial_supply_inferred_as_treatment_access', '伦理监管批准后应及时向研究机构提供试验药，增加时间要求仍是一般试验供药流程。无当前治疗缺口和原不可得人群，L以具体配备推F，与试验获取例外所需条件冲突。'),
'04703': (B, 'urgent_market_entry_vs_administrative_deadline', '药品上市许可审评中对临床急需境外已上市罕见病用药设70日通道，有进入机制和临床需求联系，但当前不像00126另写境内未上市。只列领域裁定候选，不将较快时限直接等同实际保障，也不当作确定漏判。'),
}

def main():
    diag_path = ROOT/'指标诊断弱项与逐例原文.json'
    diag = json.loads(diag_path.read_text())
    comparisons = [r for r in diag['disagreements'] if r['method']=='llm_gpt56_sol_v30' and r['dimension']=='F']
    dedup = {}
    for row in comparisons:
        dedup.setdefault(row['id'], []).append(row)
    assert len(comparisons)==161 and len(dedup)==48
    assert {id.split('-')[-1] for id in dedup} == set(NOTES)
    inp_path=ROOT/'effective_blind_inputs_v30_v3.jsonl'
    rule_in_path=ROOT/'rule_inputs_v31_shared_v3.jsonl'
    pred_path=ROOT/'llm-v30/sealed-final-material-v3/all_predictions.jsonl'
    rule_path=ROOT/'rules-v31/all_predictions_completed_material_v3.jsonl'
    ref_path=ROOT.parents[1]/'outputs/autocode-v25-20260927/current_1268_references.jsonl'
    inp={r['id']:r for r in rows(inp_path)}
    rule_in={r['id']:r['input'] for r in rows(rule_in_path)}
    pred={r['id']:r for r in rows(pred_path)}
    rule={r['id']:r['prediction'] for r in rows(rule_path)}
    refs={r['id']:r for r in rows(ref_path)}
    cases=[]
    for id, comp in sorted(dedup.items()):
        cls, boundary, reason = NOTES[id.split('-')[-1]]
        current=inp[id]; source=rule_in[id]
        assert current['text']==source['unit_text']
        assert current['contexts']==source['llm_v29_shared_context']
        cases.append({
            'id':id, 'original_id':refs[id]['original_id'], 'group':comp[0]['group'],
            'dimension':'F', 'review_class':cls, 'boundary_type':boundary,
            'semantic_review_reason':reason,
            'actual_unit_text':current['text'],
            'actual_shared_contexts':current['contexts'],
            'actual_shared_contexts_sha256':sha256(json.dumps(current['contexts'],ensure_ascii=False,sort_keys=True).encode()).hexdigest(),
            'current_llm_label':pred[id]['labels']['F'],
            'current_llm_reason':pred[id]['dimension_reasons']['F'],
            'current_llm_evidence':[e for e in pred[id]['evidence'] if e['dimension']=='F'],
            'current_llm_fairness_subtypes':pred[id]['fairness_subtypes'],
            'current_rule_label':rule[id]['labels']['F'],
            'original_AI_references':{c:{'label':refs[id]['original_references'][c]['labels']['F'],
                'reason':refs[id]['original_references'][c]['dimension_reasons']['F']} for c in ['A','C']},
            'weak_comparison_records':comp,
            'source_binding':{k:source[k] for k in ['source','source_sha256','candidate_file','candidate_sha256','pages'] if k in source},
            'binary_adjudication_performed':False, 'label_changed':False,
        })
    groups={key:[c['id'] for c in cases if c['review_class']==key] for key in [E,P,T,B,S]}
    weak=[r for r in diag['weak_comparisons'] if '/llm_gpt56_sol_v30/' in r['record_key'] and '/F/' in r['record_key']]
    sources=[diag_path,inp_path,rule_in_path,pred_path,rule_path,ref_path,ROOT/'rules-v31/protocol-v1.3.md',ROOT/'llm-v30/完整系统提示词-v30-候选03.txt',ROOT/'三种编码方法注意力共同结论核验.json',Path(__file__)]
    result={
        'status':'read_only_all_weak_llm_F_disagreements_semantically_reviewed',
        'scope':'All main1057 primary weak LLM F comparisons; comparison rows deduplicated by ID×F. Not the whole corpus and not a fresh performance test.',
        'comparison_row_count':len(comparisons),'unique_id_dimension_count':len(cases),
        'reviewer_identity':'AI reviewing agent; not independent human adjudication.',
        'reference_identity':'Original A/C AI first submissions and original materials retained; not current same-material independent human gold labels.',
        'actual_material_read':'Full actual v3 unit and recursively all supplied context fields, including verified_context_certificates; original LLM and A/C reasons; frozen manual and candidate03 prompt. No claim that every underlying PDF attachment was newly visually inspected.',
        'review_class_counts':dict(Counter(c['review_class'] for c in cases)),
        'review_class_ids':groups, 'cases':cases, 'weak_comparisons':weak,
        'confirmed_missing_input_context_found':[],
        'next_round_generic_work':[
            {'issue':'Do not infer actual coverage from a procedural fallback or work classification', 'evidence_ids':['RECODE25-01723','RECODE25-02563'],
             'positive_controls':['RECODE25-00646','RECODE25-01051','RECODE25-03274','RECODE25-03361'],
             'negative_controls':['RECODE25-02598','RECODE25-03715'],
             'proposed_scope':'Reapply already frozen distinction to actual predicates. Do not suppress all directory or payment scope mentions.'},
            {'issue':'Specific trial drug supply is not by itself the treatment-access exception', 'evidence_ids':['RECODE25-04094','RECODE25-04099'],
             'proposed_scope':'Require current explicit formerly unavailable treatment population and corresponding access arrangement for the trial exception; preserve ordinary real-world drug supply/shortage as a separate positive control.'},
            {'issue':'Resolve physical medication obstacle vs ordinary convenience and general adaptation',
             'evidence_ids':['RECODE25-03425','RECODE25-03430','RECODE25-03482'],
             'proposed_scope':'Freeze a symmetric domain decision before any new encoding. Concrete cognitive or physical obstacles cannot be excluded only for lacking an extra assessment action, but ordinary adaptation cannot be presumed to describe an obstacle.'},
            {'issue':'Separate therapy-effect/R&D unmet need from drug-access unmet need',
             'evidence_ids':['RECODE25-00005','RECODE25-00009','RECODE25-00174','RECODE25-00239','RECODE25-00255','RECODE25-00256','RECODE25-03005'],
             'proposed_scope':'Domain adjudication of manual55 and actual-access condition, not copying reference positives. New definitions, if any, require transparent versioning and all methods same definition.'},
        ],
        'common_attention_interpretation':{
            'supported_descriptive_claim':'Four existing estimates (three method families) agree on primary departmental direction: NMPA safety leads and S+E exceeds half; NHSA economic attention leads; NHC highest dimension lies in S/F. Each specified lead/majority statement also holds within each method across61 prespecified sensitivity cases.',
            'quantitative_disagreement':'Primary NMPA I is11.7284% rules vs17.9161% LLM; NHSA F is20.5658% rules vs26.7794% LLM. Shared direction does not mean shared magnitudes.',
            'prohibited_overstatement':'No conclusion that every sentence is valid, that all61 cases preserve strict top-two order, that all label differences are machine errors, or that AI agreement establishes independent human empirical validity.',
            'validation_next_step':'After symmetric generic boundary decisions and any new model version are frozen, use a separate same-material independent human sample to assess precision/recall/agreement and the departmental attention estimates. Do not relabel the existing references until0.80 or use the current48 development disputes as a fresh holdout.'
        },
        'labels_code_prompt_manuscript_or_frozen_QA_changed':False,
        'new_kappa_or_error_rates_claimed_from_review':False,
        'source_sha256':{str(p.resolve()):digest(p) for p in sources},
    }
    dst=OUT/'llm-F-disagreement-semantic-review-v3.json'
    assert not dst.exists(), 'Preserve a once-written review'
    dst.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    labels={E:'较明确的执行过度推断候选',P:'可能偏宽，须先裁定范围',T:'具体障碍与便利性的操作边界张力',B:'构念边界，须领域裁定',S:'当前结果有依据，原参照可争议'}
    md=['# LLM公平性48例：只读语义复核','',
        '161行薄弱比较分歧按ID×F去重为48例。逐读完整实际v3单元、全部语境证书、当前LLM理由、原A/C理由和冻结手册及候选03提示词。A/C为原AI首次参照，本复核也由AI完成；没有新增真人金标准，没有修改任何标签或代码。','',
        '|复核类型|例数|ID|','|---|---:|---|']
    for cls in [E,P,T,B,S]:
        md.append(f"|{labels[cls]}|{len(groups[cls])}|{', '.join(id.split('-')[-1] for id in groups[cls])}|")
    md+=['','最明确的后续核查对象是01723、02563、04094和04099：分别把办理退路、目录工作分类、常规试验供药职责推成实际保障获取。这些判断与现有执行排除存在直接冲突，值得按通用命题规则重新验证；此处没有替换它们的标签。','',
         '反向控制应保留00646/01051等实际纳排、03274的基金支付条件和03361的新支付范围条件；它们与原AI参照不一致，并不构成删除F的理由。01009/01242/02290的目录退出父谓词也应完整阅读，不能按孤立子项作判断。','',
         '03430的具体身体功能障碍与给药便利排除之间、00270随机分配概率与原不可得治疗例外之间，必须先统一边界。00126/04703急需境外药上市时限只列领域裁定候选。不能为提高召回把所有治疗未满足、研发需求、目录事务或优先时限都计F。','',
         '|ID|当前LLM/规则/A/C|类型|原文与复核理由|','|---|---|---|---|']
    for c in cases:
        labs='/'.join(str(x) for x in [c['current_llm_label'],c['current_rule_label'],c['original_AI_references']['A']['label'],c['original_AI_references']['C']['label']])
        txt=c['actual_unit_text'].replace('|','／').replace('\n',' ')
        if len(txt)>180:txt=txt[:180]+'…'
        md.append(f"|{c['id'].split('-')[-1]}|{labs}|{labels[c['review_class']]}|{txt}；{c['semantic_review_reason']}|")
    md+=['','当前共同注意力结论与局部分歧可以同时成立：三个方法家族的四份估计共同支持药监侧重安全、医保侧重经济性、卫健最高维度在安全/公平之间；方法间幅度仍有差别，不能把宏观排序一致当作逐句效度。原AI参照正例支持有限且并非新材料真人标签，当前κ/P/R/F1是与该参照的符合表现。','',
         '下一轮应先冻结对称通用边界，再用独立真人同材样本评估模型与部门注意力估计。本48例属于开发诊断，不应作为调整后的新留出验证集。0.80只用于发现薄弱比较，不能用来倒推或改写真值。']
    (OUT/'llm-F-disagreement-semantic-review-v3.md').write_text('\n'.join(md)+'\n')
    print(json.dumps({'status':result['status'],'counts':result['review_class_counts'],'json_sha256':digest(dst)},ensure_ascii=False))

if __name__=='__main__':main()
