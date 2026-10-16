"""Bounded development mechanisms, not human/independent validity evidence."""
import copy
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
W=HERE.parents[3]
sys.path.insert(0,str(HERE/'runtime'))
import policy_coding_v27 as coding
import source_context_adapter_v34 as adapter
import common_innovation_relations13 as innovation
import common_medicine_access13 as access


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    folder=HERE/'controls';folder.mkdir(exist_ok=True)
    cases=[
      ('general_safety_obligation','创新药研发单位应定期更新安全性报告,并开展药物警戒。',{'I':0,'F':0}),
      ('innovation_object_payment_only','创新药的医保支付管理应符合年度目录要求。',{'I':0,'F':0}),
      ('institution_facility_service','研究机构应提供适老化设施设备和照护服务。',{'I':0,'F':0}),
      ('scientific_design_no_innovation_object','在设计过程中,应充分结合人因工程原则,考虑操作人员的视力和操作等能力。',{'I':0,'F':0}),
      ('trial_participation_representation','药物临床试验应关注受试者代表性,保障所有人公平参与研究的机会。',{'I':0,'F':0}),
      ('review_time_without_need','药品上市许可申请的审评时限为七十日。',{'F':0}),
      ('guideline_name_format','有关创新药研发的技术指导文件名称应按格式填报。',{'I':0,'F':0}),
      ('shortage_words_as_filename','对临床急需短缺药品的文件名,应在栏目中填写优先审评审批字样。',{'F':0}),
      ('general_patient_need_only','患者需要有效药物治疗。',{'F':0}),
      ('efficacy_evidence_without_access','药物应提供疗效比较数据。',{'F':0}),
      ('manual_direct_innovation_support','为创新药的临床研发提供技术指导。',{'I':1}),
      ('manual_direct_needs_based_access','按治疗需要保障患者持续获得药物治疗。',{'F':1}),
      ('specific_unmarketed_needed_drug_time','临床急需的境外已上市境内未上市的罕见病药品,审评时限为七十日。',{'F':1}),
      ('shortage_targeted_priority_creation','为鼓励新药研发,规范临床急需短缺药品优先审评审批,制定本工作程序。',{'F':1}),
      ('routine_format_communication','研发人员应就常规申报材料格式与药品技术审评机构沟通。',{'I':0}),
      ('actual_innovative_technical_communication','鼓励新药研发人员与药品技术审评机构密切沟通,以提高抗肿瘤创新药安全性数据的评价质量。',{'I':1})]
    source=folder/'synthetic_mechanism_source.txt'
    source.write_text('\n'.join(text for _,text,_ in cases)+'\n')
    cp=folder/'synthetic_mechanism_candidates.json'
    paragraphs=[dict(id=f'p{i:04d}',text=text,pages=[],line_ids=[f'L{i}'],source_lines=[i],type='text')
                for i,(_,text,_) in enumerate(cases,1)]
    units=[dict(id=f'u{i:04d}',paragraph_id=f'p{i:04d}',text=text,pages=[])
           for i,(_,text,_) in enumerate(cases,1)]
    lines=[dict(id=f'L{i}',line=i,text=text,raw_text=text) for i,(_,text,_) in enumerate(cases,1)]
    cp.write_text(json.dumps(dict(source=str(source),source_sha256=sha(source),
        paragraphs=paragraphs,unit_candidates=units,lines=lines),ensure_ascii=False,indent=2))
    results=[]
    for i,(name,text,expected) in enumerate(cases,1):
        record=dict(source=str(source),source_sha256=sha(source),unit_source=str(source),
            unit_source_sha256=sha(source),candidate_file=str(cp),candidate_sha256=sha(cp),
            unit_id=f'u{i:04d}',unit_text=text,pages=[],unit_type='prose_candidate',
            paragraph_context=[dict(paragraph_id=f'p{i:04d}',text=text,pages=[])],
            content_role='primary_policy_text',count_as_analysis_unit=True)
        result=coding.code_unit(record)
        observed={d:result['labels'][d] for d in expected}
        results.append(dict(name=name,material_type='synthetic_development_mechanism',
            text=text,expected_mechanism=expected,observed=observed,
            check_pass=observed==expected,result=result))
    actual={x['id']:x['input'] for x in map(json.loads,(HERE/'source04_selected29_inputs.jsonl').open())}
    for name,key,module in [
      ('actual_I_source_hash_anomaly','RECODE25-03476',innovation),
      ('actual_F_source_hash_anomaly','RECODE25-04615',access)]:
        r=adapter.prepare(copy.deepcopy(actual[key]));r['unit_source_sha256']='0'*64
        result=module.revise(r,dict(evidence=[],judgement_status='determined'))
        dim='I' if module is innovation else 'F'
        pending=bool((result.get('common13_pending_dimensions') or {}).get(dim))
        results.append(dict(name=name,material_type='source_binding_mutation_development',
            source_record_locator=key,pending_dimension=dim,observed_pending=pending,
            positive_evidence_emitted=any(e['dimension']==dim for e in result['evidence']),
            check_pass=pending and not any(e['dimension']==dim for e in result['evidence']),result=result))
    r=adapter.prepare(copy.deepcopy(actual['RECODE25-00033']))
    r['verified_innovation_scope_v27']['text']='不属于该程序的创新药范围。'
    result=innovation.revise(r,dict(evidence=[],judgement_status='determined'))
    pending=bool((result.get('common13_pending_dimensions') or {}).get('I'))
    results.append(dict(name='program_scope_unbound',material_type='source_binding_mutation_development',
        observed_pending=pending,check_pass=pending and not result['evidence'],result=result))
    for name,mutation in [('missing_decimal_interval','drop'),('wrong_decimal_chapter','chapter')]:
        r=adapter.prepare(copy.deepcopy(actual['RECODE25-03894']))
        groups=r['typed_contexts_v34']
        if mutation=='drop':
            r['typed_contexts_v34']=[g for g in groups if '1.3.9 项下' not in (g.get('reference_address') or '')]
        else:
            for g in groups:
                if 'reference_address' in g:
                    g['reference_address']=g['reference_address'].replace('化学药品与生物制品','其他章节')
        result=innovation.revise(r,dict(evidence=[],judgement_status='determined'))
        pending=bool((result.get('common13_pending_dimensions') or {}).get('I'))
        results.append(dict(name=name,material_type='source_binding_mutation_development',
            observed_pending=pending,check_pass=pending and not any(e['dimension']=='I' for e in result['evidence']),result=result))
    report=dict(scope='Finite implementation controls only; synthetic mechanisms and actual source-binding mutations. No human labels, model outputs, private selections or metrics.',
        manual_sha256=innovation.MANUAL_SHA256,case_count=len(results),
        all_mechanism_checks_pass=all(r['check_pass'] for r in results),
        independent_validity_claimed=False,formal_adoption=False,results=results)
    output=HERE/'development_controls_actual01.json';output.write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(dict(case_count=len(results),all_mechanism_checks_pass=report['all_mechanism_checks_pass'],
                         failed=[r['name'] for r in results if not r['check_pass']],output_sha256=sha(output)),ensure_ascii=False))


if __name__=='__main__':
    main()
