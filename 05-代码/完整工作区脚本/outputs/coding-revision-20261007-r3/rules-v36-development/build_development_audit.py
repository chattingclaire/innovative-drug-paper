"""Reporting only: exposed references are never imported by production code."""
import collections, datetime, hashlib, json, re
from pathlib import Path
R=Path(__file__).resolve().parent
B=R.parent
DIMS=('S','E','Ec','I','F')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def jl(p):return [json.loads(s) for s in Path(p).read_text().splitlines() if s]
def save(name,obj):(R/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
oldpath=B/'rules-v35.1-development/all_predictions_material_v14.jsonl'
newpath=R/'all_predictions_material_v14_v36.1.jsonl'
inp=B/'rule_inputs_shared_v14.jsonl'
rows=jl(inp); inputs={r['id']:r['input'] for r in rows}
oldrows=jl(oldpath); newrows=jl(newpath)
old={r['id']:r['prediction'] for r in oldrows}; new={r['id']:r['prediction'] for r in newrows}
assert [r['id'] for r in rows]==[r['id'] for r in oldrows]==[r['id'] for r in newrows]
assert len(new)==4924
assert [r['original_id'] for r in rows]==[r['original_id'] for r in oldrows]==[r['original_id'] for r in newrows]

REASONS={
 'V36_E_patient_benefit_from_drug':'患者从试验药物中获益，明确药物—患者获益关系；不把普通参与福利算E。',
 'V36_E_effective_treatment_for_drug_recipients':'药物上市后目标患者接受有效治疗，明示药物效果而非单纯入组设计。',
 'V36_E_active_comparator_therapeutic_choice':'对照药须代表最佳治疗选择，要求治疗优势参照，非单纯对照设计。',
 'V36_E_same_study_endpoint_validation':'当前该研究主要终点验证，承接同段明确药物减少骨折有效性研究；只恢复效果证据关系，不复制安全性。',
 'V36_I_specific_dosing_frequency_modification':'明确改良给药频次属于产品给药属性变化，不要求新靶点或已证优效。',
 'V36_I_postposed_drug_innovation_degree':'创新程度高等限定语跨并列成分修饰后置药品对象，实质讨论创新程度。',
 'V36_I_resources_for_innovative_development':'明确优化审评审批资源配置并以提升创新药临床研发为用途，属于支持内容。',
 'V36_I_innovation_project_scientific_support_function':'试点当前明确创新研发对象与解决研发科学问题的支持作用；讨论支持措施不要求效果已经实现。',
 'V36_I_technical_guidance_resource_with_innovation_target':'实际编制面向创新药研发的技术指南，并独立明确研发风险管理指导功能；标题只消解支持对象。',
 'V36_F_current_drug_market_shortage':'当前明确市场短缺或临床急需且境内未上市的特定药品获取缺口；不从罕见病或急迫性单独推断。',
 'V36_F_no_standard_treatment':'药物对照选择明确以适应症确无标准治疗为条件，涉及实际治疗空白。',
 'V36_F_loss_of_treatment_opportunity':'药物不良反应导致患者失去治疗机会，明示治疗获取损失。',
 'V36_F_actual_commercial_formulary_membership':'明确协商成功后的实际目录纳入或已有充分保障品种不纳入，不是申报资格。',
 'V36_F_drug_renewal_necessary_condition':'不申报药品无法续约，构成已有药品保障连续的必要条件。',
 'V36_F_negotiated_drug_agreement_duration':'直接规定谈判药品协议有效期，限定现有保障持续时间；并非提交时限。',
 'V36_F_current_exit_criterion':'当前列举药品条件与已核验父条款直接调出目录谓词合成实际退出条件，不继承其他维度。',
 'V36_F_target_indication_unmet_need_information':'已核验父级要求总结目标适应症诊疗情况，当前项明确未满足临床需求内容。',
 'V36_F_same_paragraph_drug_guarantee_level':'当前确定保障水平承接最近一句单独药品保障机制，对象明确。',
 'V36_Ec_explicit_drug_insurance_payment':'明确药品纳入医保支付机制或异地直接结算范围，规定药物支付安排。',
 'V36_F_urgency_without_gap':'需求迫切或急迫本身未明示未获满足、无可用治疗或药物供应缺口，撤销仅此依据。',
 'V36_E_disease_definition_counterfactual':'疾病严重程度定义中的不治疗反事实没有评价药物效果，撤销局部E。',
 'V36_SE_rights_object_not_evaluation':'安全/有效仅界定受保护数据类别，当前为专有权范围而非另行评价或数据要求；保留I及独立评价内容。',
 'V36_F_pricing_subject_not_admission':'新纳入药品是支付标准规则主语，当前只定价，不独立决定实际纳入。',
 'V36_Ec_filing_premise_not_payment_rule':'是否申请调整支付标准是申报前提，未规定价格水平、经济评价或费用责任。',
}
changes=[]; flips=collections.Counter(); directions=collections.Counter()
for rid,p in new.items():
    ds=[d for d in DIMS if p['labels'][d]!=old[rid]['labels'][d]]
    if not ds:continue
    details=[]
    for d in ds:
        evidence=[e for e in p['evidence'] if e['dimension']==d and e['rule'].startswith('V36_')]
        suppressed=[e for e in p['suppressions'] if d in e.get('dimensions',[]) and e['rule'].startswith('V36_')]
        rules=sorted({e['rule'] for e in evidence+suppressed});assert rules
        details.append({'dimension':d,'old':old[rid]['labels'][d],'new':p['labels'][d],
                        'rules':rules,'reasons':[REASONS[k] for k in rules],
                        'current_evidence':evidence,'suppressed_old_evidence':suppressed})
        flips[d]+=1;directions[f'{d}:{old[rid]["labels"][d]}->{p["labels"][d]}']+=1
    changes.append({'id':rid,'text':inputs[rid]['unit_text'],'dimension_changes':details})
save('actual_full_corpus_changes_vs_v35.1.json',{'stage':'development_not_independent_validation','input_sha256':sha(inp),
      'old_output_sha256':sha(oldpath),'new_output_sha256':sha(newpath),'changed_unit_n':len(changes),
      'changed_dimension_n':sum(flips.values()),'dimension_flip_counts':dict(flips),'directions':dict(directions),'records':changes})

# Each remaining exposed disagreement is retained explicitly, rather than being
# relabelled or declared impossible simply because no generic repair was added.
KEEP={
 '03157':'当前是治疗分配概率的协变量例示；需以后句疗效估计含义作跨句推断，未用一般协变量/敏感性关键词赋E。',
 '03065':'新增适应症研究、外部对照本身未明确效果指标；需要药物治疗用途研究的语义推断，保留与T分歧。',
 '00086':'已有明确短缺药品内容，维持F=1；制定程序宗旨是否只有名称是A/C边界分歧。',
 '00771':'相关数据的科学及时准确是数据获取要求，经济对象要跨句推断；未把相关数据统一赋Ec。',
 '00919':'明确援引与一般申报资格的界限仍有分歧，保留现有引用隔离，不按参考向量整体传播S/E/Ec。',
 '02072':'转类/续约路径图与实际保障持续条件的界线尚未形成可可靠执行的通用图结构解析；当前F=1仍有争议，未宣称已修复。',
 '02542':'已有创新药病例审核后支付及病种付费例外的实质支付安排，维持F；与C判断仍有分歧。',
 '01955':'适应症/功能主治获批变更未明确原创、改良或相对产品改变，维持I=0。',
 '02158':'年度调整对象明确援引条文，但不能将引用的所有终局价值/退出后果自动复制为当前；通用实质引用解析仍未解决。',
 '02144':'建立高效医保支付机制的宏观宗旨与具体药物支付安排有边界争议，当前未形成可靠局部关系，未新增。',
 '03763':'谈判材料用于医保底价测算，已有价格决定证据关系，维持Ec=1；不因另一参考0而删除。',
 '04894':'电子处方流转基础设施与常规药物获取渠道之间需要语义推断，当前未明确给付或供应条件，维持0。',
 '03704':'雪中送炭/锦上添花需保障隐喻解读，未将成语设为F关键词。',
 '02462':'价格费用数据截至日期属于时点要求，未把数据名直接转为经济评价要求。',
 '04346':'处方审核资料中的过敏/用药史是否已构成风险证据有分歧；未因一般审核信息要求强制S。',
 '00529':'混合门诊手术/化疗/输液服务的质量安全管理仍可能涉及用药风险；现规则未可靠拆分并列对象，保留可继续改进的S漏判。',
 '01432':'数据保护资格中引用实质安全/效果条件仍缺可靠的引用适用关系解析；不传播被引条文整套标签。',
 '02233':'当前已经组织开展审批优化试点以支持创新研发，维持现有I=1；与C仍有边界分歧。',
 '04162':'当前常规按专业/利益冲突组建团队，创新对象与新增支持资源需更远范围及后句合成；不将所有审评团队组建判I。',
 '03415':'一般适老研发设计宗旨与具体创新指导支持的界限仍有分歧，未从创新药名称和具体设计直接推定创新。',
 '00162':'无法治愈陈述的当前主体是肿瘤，缺少局部药物治疗关系；不将所有严重疾病或无法治愈判E。',
 '00099':'明确临床急需短缺药品，即使规定优审范围也仍述供应缺口，维持现有F=1。',
 '01562':'已给父条款明确简易续约及两年有效期，可能支持连续保障条件；当前通用父谓词实现尚未覆盖该结构，仍是可改进漏判，不称不可规则化。',
 '00964':'价格协商只有程序动作没有价格水平/费用责任，Ec保持0；其实际目录纳入F已另修。',
 '02764':'仅获批适应症重大变化不足以确证创新属性，维持I=0。',
 '03876':'图中价格协商是流程节点；创新药目录名称/新通用名/适应症变更未明示创新属性，不扩展Ec或I。',
 '01979':'拟谈判阶段支付范围论证与实际给付边界决定的作用关系仍有分歧，维持现有0并保留争议。',
 '00891':'父条款已将费用阈值作为补充协议确定新支付范围的条件，维持F=1；与A分歧不据此删证据。',
 '02573':'甲乙类别调整工作优先次序未具体确定保障范围或负担，維持F=0。',
}
errors=read(B/'statistics/v33-v34.1-v35.1-v14-development-diagnostic/FN_FP_PRIVATE.json')['errors']
groups={}
for e in errors:
    if e['method']=='v35.1':groups.setdefault((e['id'],e['dimension']),[]).append(e)
change_lookup={(x['id'],d['dimension']):d for x in changes for d in x['dimension_changes']}
ledger=[]
for (rid,d),es in groups.items():
    changed=(rid,d) in change_lookup
    reason='；'.join(change_lookup[(rid,d)]['reasons']) if changed else KEEP[rid.split('-')[-1]]
    ledger.append({'id':rid,'dimension':d,'text':inputs[rid]['unit_text'],'v35_1':old[rid]['labels'][d],
                   'v36_1':new[rid]['labels'][d],'action':'bounded_relation_repair' if changed else 'retained_without_claim_of_correctness',
                   'manual_review_reason':reason,'preexisting_reference_disagreements':es,
                   'reference_labels_modified':False})
assert len(ledger)==65
save('exposed65_case_dimension_review_PRIVATE.json',{'stage':'development_only','n':len(ledger),'reference_is_human_gold':False,
     'records':ledger,'remaining_semantic_I_example':'RECODE25-04162','additional_known_implementation_frontier':['RECODE25-01562:F','RECODE25-00529:S','RECODE25-02072:F']})

# Descriptive group counts are calculated only AFTER the final code/run freeze.
metadata_path=B.parent/'validation-expansion-20260926/frozen-inputs/classification--部门归属与年度系列-冻结v1.json'
metadata=read(metadata_path);meta={Path(r['original_file']).stem:r for r in metadata['rows']}
group_by_id={rid:meta[x['original_file_stem']]['analysis_group'] for rid,x in inputs.items()}
def summary(pred,ids):
    counts={d:sum(pred[rid]['labels'][d] for rid in ids) for d in DIMS}
    cells={f'F{f}_Ec{e}':sum(pred[rid]['labels']['F']==f and pred[rid]['labels']['Ec']==e for rid in ids) for f in (0,1) for e in (0,1)}
    assert sum(cells.values())==len(ids)
    return {'n':len(ids),'five_dimension_counts':counts,'five_dimension_prevalence':{d:counts[d]/len(ids) for d in DIMS},
            'dimension_sum':sum(counts.values()),'F_Ec_four_cells':cells}
v33path=B/'rules-v33/all_predictions_material_v14.jsonl';v33={r['id']:r['prediction'] for r in jl(v33path)}
tables={name:{g:summary(pred,[rid for rid in inputs if group_by_id[rid]==g]) for g in ('NMPA','NHSA','NHC','GOV')}
        for name,pred in [('v33_frozen_baseline',v33),('v35.1_development',old),('v36.1_development',new)]}
save('frozen_metadata_group_counts_and_F_Ec.json',{'stage':'descriptive_development_outputs_not_effects_or_weights',
    'calculated_after_final_runtime_freeze':True,'metadata_path':str(metadata_path),'metadata_sha256':sha(metadata_path),
    'group_assignment':'join exact original_file_stem to metadata rows original_file stem, then use analysis_group; no prefix inference',
    'corpus_n':4924,'three_department_n':sum(group_by_id[rid]!='GOV' for rid in inputs),
    'GOV_kept_separate':True,'predictions_sha256':{'v33':sha(v33path),'v35.1':sha(oldpath),'v36.1':sha(newpath)},'tables':tables})

checks={}
for freeze_file in [B/'rules-v35.1-development/candidate_freeze.json',R/'candidate_freeze.json',R/'candidate_freeze_v36.1.json']:
    f=read(freeze_file);checks[str(freeze_file.relative_to(B))+'_code_unchanged']=all(sha(p)==h for p,h in f['production_code_sha256'].items())
run=read(newpath.with_suffix('.run.json'))
checks.update(n_4924_unique_complete=len(new)==4924,all_five_dimensions_binary=all(set(p['labels'])==set(DIMS) and all(type(v) is int and v in (0,1) for v in p['labels'].values()) for p in new.values()),
    ids_and_original_ids_order_unchanged=True,input_sha_unchanged=sha(inp)==run['input_sha256']=='fbee2777afe7e437ef1d2e0773e12a41ec3682914510f05f2dad2f31db7b6a6a',
    original_text_sha_unchanged=all(p['unit_text_sha256']==hashlib.sha256(inputs[rid]['unit_text'].encode()).hexdigest() for rid,p in new.items()),
    evidence_and_suppression_literal_spans=all(inputs[rid]['unit_text'][e['start']:e['end']]==e['text'] for rid,p in new.items() for e in p['evidence']+p['suppressions'] if all(k in e for k in ('start','end','text'))),
    all_source_candidate_files_unchanged=all(sha(p)==h for p,h in run['actual_source_and_candidate_sha256'].items()),
    manual_hashes_unchanged=all(sha(p)==h for p,h in read(R/'candidate_freeze_v36.1.json')['manuals'].items()),
    prior_read_dependencies_unchanged=all(sha(p)==h for p,h in read(R/'development_exposure_registration.json')['read_dependencies_sha256'].items()),
    constructed67_pass=read(R/'constructed_semantic_controls_v36.1.json')['all_checks_pass'],legacy19_pass=read(R/'legacy_v35_controls.json')['all_checks_pass'],
    all_changed_dimensions_have_literal_reasons=True,all_65_prior_disagreements_reviewed=len(ledger)==65,
    all_group_cells_sum_to_group_n=True)
code=(R/'runtime-v36.1/rules_semantic_v36.py').read_text()
checks['new_classifier_has_no_case_ID_department_or_reference_table']=not re.search(r'RECODE25-|NMPA|NHSA|NHC|PRIVATE|reference\[|statistics/',code)
checks['new_classifier_has_no_file_io']=not re.search(r'\bopen\(|read_text\(|read_bytes\(|json\.load',code)
assert all(checks.values()),checks
save('final_development_QA.json',{'all_checks_pass':True,'checks':checks,'n':4924,'changed_unit_n':len(changes),'changed_dimension_n':sum(flips.values()),
    'literal_span_checks':run['checks'],'code_and_data_status':'development_not_independent_validation','input_sha256':sha(inp),'output_sha256':sha(newpath),
    'no_new_independent_test_claim':True,'first_failed_attempt':'System Python lacked pypdf, aborted before writing predictions. Successful runs used bundled Python.',
    'pdf_parser_messages':'pypdf emitted existing wrong-pointing-object warnings; all source SHA/authentication assertions and full-run checks passed.'})
save('final_candidate_binding.json',{'status':'sealed_development_candidate','selected_version':'v36.1-bounded-semantic-relations-development',
    'runtime_dir':str(R/'runtime-v36.1'),'prediction':{'path':str(newpath),'sha256':sha(newpath)},
    'run':{'path':str(newpath.with_suffix('.run.json')),'sha256':sha(newpath.with_suffix('.run.json'))},
    'freeze':{'path':str(R/'candidate_freeze_v36.1.json'),'sha256':sha(R/'candidate_freeze_v36.1.json')},
    'input':{'path':str(inp),'sha256':sha(inp)},'qa':{'path':str(R/'final_development_QA.json'),'sha256':sha(R/'final_development_QA.json')},
    'retained_initial_v36_prediction':{'path':str(R/'all_predictions_material_v14.jsonl'),'sha256':sha(R/'all_predictions_material_v14.jsonl')},
    'not_independent_validation':True,'report_script_sha256':sha(__file__)})
print(json.dumps({'changed_units':len(changes),'dimension_flips':dict(flips),'directions':dict(directions),'output_sha256':sha(newpath),'all_checks_pass':True,'group_tables':tables['v36.1_development']},ensure_ascii=False))
