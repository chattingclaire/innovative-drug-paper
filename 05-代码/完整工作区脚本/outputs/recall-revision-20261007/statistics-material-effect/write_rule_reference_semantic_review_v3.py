"""Record a read-only semantic review; never edit or rerun classifications."""
from pathlib import Path
from hashlib import sha256
from collections import Counter
import json

ROOT=Path(__file__).resolve().parent.parent
OUT=Path(__file__).resolve().parent
def sha(path):return sha256(Path(path).read_bytes()).hexdigest()
def rows(path):return [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]
NOTES={
'RECODE25-00126':('F','access_mechanism_vs_administrative_deadline',1,'supported_candidate_not_confirmed_code_defect',
 '当前句同时给出临床急需、境外已上市而境内未上市、罕见病用药和70日路径，具备将具体治疗缺口与加快上市安排联系起来的文字依据；并非仅有程序名称。严格按“时限是事务程序”处理也有边界理由，需领域裁定时限安排是否构成本研究的保障获取。不能从C=1直接宣布代码错误。',
 '其中临床急需的境外已上市境内未上市的罕见病药品审评时限为70日。',
 [53,55,95,121,152]),
'RECODE25-00225':('F','research_population_expansion_vs_treatment_access',0,'defensible_rule_boundary',
 '当前要求为未被富集人群开展研究并扩大治疗人群，具有治疗需求动机，但没有具体药品供应、保障或使原本不可得的人群获得治疗的安排。冻结手册区分研究代表性与获取；C把扩大治疗人群直接视为获取，属于可争议的较宽解释，不能据此认定规则漏判。',
 '在富集人群中的临床试验成功后,应基于科学开展临床试验,合理地扩大治疗人群范围。',
 [53,55,81,83]),
'RECODE25-00270':('F','trial_randomization_opportunity_vs_access',1,'supported_candidate_with_construct_boundary',
 '2:1并非单纯统计效率：当前句明确以让更多患者接受潜在更优治疗为目的，存在具体研究药物治疗机会的安排，因此较支持F。边界在于手册例外要求原本无法获得治疗，而随机分配概率改变不同于扩大原本不可及人群；不可把所有不等比例随机化纳入F。',
 '为了使更多患者接受到潜在的更优治疗,可以考虑用 2:1 的分配比例。',
 [55,57,81,83]),
'RECODE25-01503':('F','patient_experience_information_vs_drug_access_information',0,'defensible_rule_boundary',
 '已实际查看扫描PDF第14页。父句说明收集患者体验数据以指导研发；本项只列就诊路径和现有治疗选择，下一项未满足需求不能传播进本单元。本项没有供应、支付能力、获取限制或具体管理难度，按一般患者参与/诊疗现状信息判0有依据；C将路径信息作获取信息是可争议的宽边界。',
 '患者诊治现状:如患者就诊路径、当下患者的治疗选择',
 [53,57,65,81,152]),
'RECODE25-02912':('E','guide_membership_eligibility_vs_treatment_recommendation',0,'AI_reference_boundary_no_confirmed_rule_error',
 '当前已核验父谓词是目录外药品申报资格；本项借已纳入诊疗方案的身份划定可申报对象，没有药物推荐内容、疗效证据或获益结论。A据方案名称推定治疗推荐，C与规则按资格身份判0。当前同材没有发现缺父谓词，不宜把这一条相对A的FN当作明确漏识别。',
 '具备以下情形之一的目录外药品,可以按程序提出申报:',
 [29,31,65,95,121]),
'RECODE25-03090':('Ec','generic_medical_claims_cost_object_vs_drug_economic_object',0,'rare_positive_support_and_disputed_reference_scope',
 '条文定义医疗费用与干预赔付数据，确有费用内容；但对象是医疗保健总体，已核验药物监管研究适用范围不自动把每笔医疗费用转换成药品治疗或支付资源。规则排除泛费用命中有手册依据；A/C的经济资源数据解释也有文字来源。这是对象边界且两份参照仅各2个正例，不能由R=0.50推断药监经济性整体漏半。',
 '用以获得治疗和其它干预措施赔付的医疗费用及相关医疗信息汇编。',
 [35,37,95,101,121]),
'RECODE25-03425':('F','specific_medication_management_obstacle_vs_risk_only_description',1,'AI_reference_possible_false_negative_under_frozen_broad_F',
 '难以记住是否/何时/如何服药、混淆药品是具体药品使用障碍；手册允许实质障碍描述，不要求同时提出一个新的管理评价动作。规则F=1并记录clinical_management与S交叉有依据，C以没有提出评价为由判0较窄。此判断不把老年人名称本身或一般适老包装都纳入F。',
 '难以记住是否服药,何时服药,如何服药,或者混淆不同药品。',
 [53,55,73,77,123]),
'RECODE25-04703':('F','access_mechanism_vs_administrative_deadline',1,'supported_candidate_not_confirmed_code_defect',
 '当前为药品上市许可申请，并对临床急需、境外已上市罕见病用药设70日优先路径；与00126属同类政策机制。当前句不像00126另写境内未上市，不能从标题扩写对象，但许可申请和临床急需提供了明确市场进入/治疗需求联系。仍须区分实质获取安排与一般法定时限；是通用候选覆盖问题，不是追分所需改标。',
 '临床急需境外已上市罕见病用药优先审评审批程序的审评时限为七十日',
 [53,55,95,121,152]),
}

def main():
    diagnostic_path=ROOT/'指标诊断弱项与逐例原文.json'
    diagnostic=json.loads(diagnostic_path.read_text())
    disputes=[r for r in diagnostic['disagreements'] if r['method'] in {'rules_v31','A_C'}]
    dedup={}
    for r in disputes:dedup.setdefault((r['id'],r['dimension']),[]).append(r)
    assert len(disputes)==10 and len(dedup)==8
    inputs={r['id']:r['input'] for r in rows(ROOT/'rule_inputs_v31_shared_v3.jsonl')}
    predictions={r['id']:r['prediction'] for r in rows(ROOT/'rules-v31/all_predictions_completed_material_v3.jsonl')}
    reference_path=ROOT.parents[1]/'outputs/autocode-v25-20260927/current_1268_references.jsonl'
    references={r['id']:r for r in rows(reference_path)}
    cases=[]
    for (id,dimension),comparisons in sorted(dedup.items()):
        dim,boundary,preferred,strength,reason,quote,lines=NOTES[id];assert dim==dimension
        rec=inputs[id];pred=predictions[id];source=Path(rec.get('unit_source') or rec['source'])
        assert sha(source)==(rec.get('unit_source_sha256') or rec['source_sha256'])
        assert sha(rec['candidate_file'])==rec['candidate_sha256']
        source_check={'source_sha256':sha(source),'candidate_sha256':sha(rec['candidate_file']),
          'physical_pages':rec['pages'],'unit_matches_frozen_candidate':True,
          'source_reading':'Actual source page text inspected, isolated printed-page numbers removed before cross-page alphanumeric normalization; exact candidate text and source/candidate hashes retained.'}
        if id=='RECODE25-01503':
            image=OUT/'semantic-review-visual/care-extension-physical-page14.png'
            source_check.update(source_reading='Scanned original PDF page has no extractable text; actual rendered physical page 14 / printed page 2 opened and compared with the unit, parent and next sibling.',
                actual_visual_review={'path':str(image.resolve()),'sha256':sha(image),'actually_opened_and_viewed':True})
        cases.append({'id':id,'original_id':references[id]['original_id'],'group':comparisons[0]['group'],
          'dimension':dimension,'boundary_type':boundary,'review_preferred_binary_interpretation':preferred,
          'diagnostic_strength':strength,'semantic_review_reason':reason,'short_source_evidence':quote,
          'manual_line_numbers':lines,'unit_text':rec['unit_text'],'source_file':str(source),
          'source_check':source_check,'actual_shared_contexts_sha256':sha256(json.dumps(rec['llm_v29_shared_context'],ensure_ascii=False,sort_keys=True).encode()).hexdigest(),
          'full_context_reading_fields':list(rec['llm_v29_shared_context']),
          'verified_object_scope_read':rec.get('verified_object_scope',[]),
          'verified_parent_context_read':rec.get('verified_parent_context',[]),
          'rule_label':pred['labels'][dimension],'rule_original_evidence':pred['evidence'],
          'rule_original_suppressions':pred['suppressions'],
          'rule_original_natural_language_dimension_reason':'Not recorded in this rules output; no reason is retroactively attributed to the classifier.',
          'original_AI_reference_submissions':{c:{'label':references[id]['original_references'][c]['labels'][dimension],
             'reason':references[id]['original_references'][c]['dimension_reasons'][dimension]} for c in ['A','C']},
          'weak_comparison_records':comparisons,'changes_made':False})
    weak=[c for c in diagnostic['weak_comparisons'] if '/rules_v31/' in c['record_key'] or '/A_C/' in c['record_key']]
    sources=[diagnostic_path,ROOT/'指标诊断表.json',ROOT/'三种编码方法注意力共同结论核验.json',
      ROOT/'rules-v31/protocol-v1.3.md',ROOT/'rule_inputs_v31_shared_v3.jsonl',
      ROOT/'rules-v31/all_predictions_completed_material_v3.jsonl',reference_path,Path(__file__)]
    result={'status':'read_only_rule_and_AI_reference_weak_disagreement_semantic_review',
       'reference_identity':'Original first independent AI-agent A/C submissions and their original materials; not current independent human ground truth.',
       'review_scope':'All actual disagreements in weak primary main1057 rules_v31/A_C comparisons, deduplicated by original ID × dimension. Threshold0.80 is diagnostic only.',
       'comparison_row_count':len(disputes),'unique_id_dimension_count':len(cases),'weak_comparison_count':len(weak),
       'cases':cases,'diagnostic_strength_counts':dict(Counter(c['diagnostic_strength'] for c in cases)),
       'weak_comparisons':weak,
       'rare_support_conclusion':'NMPA Ec: 414 pairs, reference positive2, rule TP1/FN1; the single03090 scope dispute halves relative recall. NHSA E: A positive3/C positive2; one02912 guide-membership dispute explains A-C κ0.798701 and rule-A κ0.798705. No zero or undefined metric is treated as passed.',
       'candidate_general_work':[{'topic':'Urgent unavailable-drug market-entry mechanism versus ordinary administrative deadlines','evidence_ids':['RECODE25-00126','RECODE25-04703'],
          'action_if_pursued':'Before any code revision, freeze whether a concrete clinical-unmet-need + cross-border availability + accelerated domestic market-entry mechanism is F under current access definition. Test ordinary review deadlines and program-list updates as negative controls; do not use A/C agreement as the correctness criterion.'},
         {'topic':'Explicit trial-treatment opportunity versus trial efficiency/representativeness','evidence_ids':['RECODE25-00270','RECODE25-00225'],
          'action_if_pursued':'Resolve applicability of manual83 to unequal randomization and research population expansion as a symmetric boundary; do not automatically tag all trial design or all expanded populations F.'},
         {'topic':'Reference interpretation of concrete medication-use obstacles','evidence_ids':['RECODE25-03425'],
          'action_if_pursued':'Preserve original A/C; a future independent adjudication should apply the explicit management-obstacle condition and allow S/F co-occurrence.'}],
       'confirmed_input_defects_found_in_these_eight':[],
       'confirmed_code_edits_warranted_without_boundary_review':False,
       'labels_code_manuscript_or_frozen_QA_changed':False,'human_adjudication_completed':False,
       'source_sha256':{str(p.resolve()):sha(p) for p in sources}}
    target=OUT/'rule-reference-disagreement-semantic-review-v3.json'
    assert not target.exists(),'Preserve once-written review'
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    lines=['# 规则与原AI参照弱比较：逐例只读语义复核','',
      '10行比较分歧按ID×维度去重为8例。A/C为原AI首次提交，原标签和材料保留；本复核不替换其标签，也不把参照分歧直接认定为机器错误。已逐读原句、完整v3语境证书、冻结手册及原理由，并回查实际来源。','',
      '|ID|维度|边界|本次审读倾向|短依据|','|---|---|---|---:|---|']
    for c in cases:lines.append(f"|{c['id']}|{c['dimension']}|{c['boundary_type']}|{c['review_preferred_binary_interpretation']}|{c['semantic_review_reason']}|")
    lines+=['',result['rare_support_conclusion'],'',
      '值得继续的通用问题是急需药加快上市与一般时限的区分，以及明确试验治疗机会与纯研究设计的区分。当前8例未发现新的输入缺口；存在有文字依据的规则覆盖候选和参照边界分歧，尚不足以跳过边界裁定直接宣称代码缺陷。03425的具体服药障碍较支持现规则F=1，不能为追求与C一致删掉。','',
      '共同注意力方向可据全量结果报告；这些逐例差异说明点估计幅度和局部构念边界仍需解释。κ/P/R/F1只是对现有AI参照的符合表现，未构成独立真人效度。没有改编码、代码、论文、工作簿或冻结QA。']
    (OUT/'rule-reference-disagreement-semantic-review-v3.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'status':result['status'],'unique_cases':len(cases),'json_sha256':sha(target)},ensure_ascii=False))

if __name__=='__main__':main()
