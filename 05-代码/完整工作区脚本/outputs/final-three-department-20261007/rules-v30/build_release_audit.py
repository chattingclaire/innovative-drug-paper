"""Bind the v30 release and compare only matched-input rule predictions."""
from pathlib import Path
from collections import Counter, defaultdict
import datetime, difflib, hashlib, json

B=Path(__file__).resolve().parent
W=B.parents[2]
OLD=W/'outputs/autocode-v28-review-20261004-111306'
DIMS=('S','E','Ec','I','F')
VERSION='v30-three-department-semantic-audit-20261007'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rows(p):return {r['id']:r for r in map(json.loads,Path(p).read_text().splitlines())}
def write(name,value):(B/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def main():
    inp=rows(B/'rule_inputs_v30_shared.jsonl')
    old=rows(B/'v28_on_v29_shared_predictions.jsonl')
    new=rows(B/'all_predictions.jsonl')
    orig=rows(OLD/'all_predictions.jsonl')
    shared=W/'outputs/final-three-department-20261007/llm-v29/rule_inputs_v29_shared.jsonl'
    assert sha(shared)==sha(B/'rule_inputs_v30_shared.jsonl')
    assert inp.keys()==old.keys()==new.keys()==orig.keys()
    assert len(inp)==4924
    metadata=W/'outputs/validation-expansion-20260926/frozen-inputs/classification--部门归属与年度系列-冻结v1.json'
    groups={Path(r['original_file']).stem:r['analysis_group'] for r in json.loads(metadata.read_text())['rows']}
    label_changes=[];evidence_changes=[];contexts=[]
    directions=Counter();by_group=Counter();causes=Counter()
    counts=defaultdict(lambda:Counter({d:0 for d in DIMS}));ns=Counter()
    preserved=[];release_metadata_only=[]
    for i,row in inp.items():
        record=row['input'];a=old[i]['prediction'];z=new[i]['prediction']
        assert z['version']==VERSION
        assert a['unit_text_sha256']==z['unit_text_sha256']==hashlib.sha256(record['unit_text'].encode()).hexdigest()
        g=groups[record['original_file_stem']];ns[g]+=1;counts[g].update(z['labels'])
        for d in DIMS:
            if orig[i]['prediction']['labels'][d]!=a['labels'][d]:
                contexts.append({'id':i,'dimension':d,'old_input_label':orig[i]['prediction']['labels'][d],'shared_input_label':a['labels'][d]})
            if a['labels'][d]!=z['labels'][d]:
                assert d=='E'
                ae=[e for e in a['evidence'] if e['dimension']==d]
                ze=[e for e in z['evidence'] if e['dimension']==d]
                cause=('eligibility_identity_without_treatment_proposition' if any(e['rule']=='V28_E_guideline_inclusion_relation' for e in ae)
                       else 'bare_clinical_value_without_specific_effect_evidence' if z['labels'][d]==0
                       else 'explicit_patient_benefit_anchor')
                rationale={'eligibility_identity_without_treatment_proposition':'该单元以纳入某诊疗方案的身份限定申报或续约对象，未陈述治疗推荐、效果/获益或其证据。',
                           'bare_clinical_value_without_specific_effect_evidence':'旧E证据仅为宽泛临床价值词；阅读当前单元未发现独立疗效、临床获益或相应证据，局部抑制后E=0。',
                           'explicit_patient_benefit_anchor':'当前单元明确陈述药物研发实现患者获益最大化，独立获益命题构成E；无需由宽泛临床价值词代替。'}[cause]
                label_changes.append({'id':i,'original_id':row['original_id'],'dimension':d,'old':a['labels'][d],'new':z['labels'][d],
                    'analysis_group':g,'original_file_stem':record['original_file_stem'],'source':record['source'],
                    'source_sha256':record['source_sha256'],'unit_id':record['unit_id'],'pages':record.get('pages',[]),
                    'unit_text':record['unit_text'],'unit_text_sha256':z['unit_text_sha256'],
                    'change_cause':cause,'review_rationale':rationale,'old_evidence':ae,'new_evidence':ze,
                    'new_suppressions':[s for s in z['suppressions'] if s.get('rule','').startswith('V30_')]})
                directions[f'{d}:{a["labels"][d]}->{z["labels"][d]}']+=1;by_group[g]+=1;causes[cause]+=1
        # Evidence-level changes remain visible even where an independent
        # effect anchor keeps the binary E label unchanged.
        ae=[e for e in a['evidence'] if e['dimension']=='E'];ze=[e for e in z['evidence'] if e['dimension']=='E']
        semantic_a=[{k:v for k,v in e.items() if k!='rule_release'} for e in ae]
        semantic_z=[{k:v for k,v in e.items() if k!='rule_release'} for e in ze]
        if semantic_a!=semantic_z:
            evidence_changes.append({'id':i,'original_file_stem':record['original_file_stem'],'unit_text':record['unit_text'],
                                     'old_E':a['labels']['E'],'new_E':z['labels']['E'],'old_evidence':ae,'new_evidence':ze})
        elif ae!=ze:
            release_metadata_only.append(i)
        if any(s.get('rule')=='V30_E_bare_clinical_value' for s in z['suppressions']) and z['labels']['E']==1:
            preserved.append({'id':i,'unit_text':record['unit_text'],'remaining_E_evidence':ze})
    assert not contexts
    assert directions=={'E:1->0':40,'E:0->1':1}
    assert new['RECODE25-03090']['prediction']['labels']['Ec']==0
    assert [i for i,r in new.items() if groups[inp[i]['input']['original_file_stem']]=='NMPA' and r['prediction']['labels']['Ec']]==['RECODE25-03016','RECODE25-04088']
    write('changes_by_id_dimension.json',{'comparison':'v28 and v30 run on byte-identical v29 shared input','n_changed_units':len(label_changes),
          'changes':label_changes,'manual_semantic_review':'本实现者逐条核读变化单元及旧新E证据；属于开发语义复核，不是另增独立准确性验证。'})
    write('evidence_changes_by_id.json',{'n_semantic_changes':len(evidence_changes),'changes':evidence_changes,
          'release_metadata_only_ids':release_metadata_only,'bare_value_removed_but_independent_E_preserved':preserved})
    write('shared_input_comparison.json',{'original_v28_vs_v28_on_shared_input_label_changes':contexts,
          'n':len(inp),'note':'共享输入加入的上下文显示字段未改变v28标签；新旧规则变化均在相同输入下比较。'})
    summary={'version':VERSION,'n':4924,'pending_n':0,'same_input_label_changes':dict(directions),'changed_units_by_group':dict(by_group),
             'causes':dict(causes),'semantic_evidence_changed_units':len(evidence_changes),
             'release_metadata_only_evidence_changed_units':len(release_metadata_only),'independent_E_retained_after_value_suppression':len(preserved),
             'other_four_dimensions_unchanged':True,'new_counts_by_group':{g:dict(c) for g,c in counts.items()},
             'units_by_group':dict(ns),'NMPA_Ec_positive_ids':['RECODE25-03016','RECODE25-04088'],
             'general_medical_claims_definition_Ec_zero_id':'RECODE25-03090','A_C_reference_labels_modified':False,
             'test_result_path':str(B/'semantic_test_results.json')}
    write('change_summary.json',summary)
    tests=json.loads((B/'semantic_test_results.json').read_text())
    amendment={'version':VERSION,'protocol':{'path':str(B/'protocol-v1.3.md'),'sha256':sha(B/'protocol-v1.3.md'),
                  'E_definition':'讨论药物防治效果、临床获益、治疗优势、疗效终点、相关生活质量、指南药物治疗推荐或相应证据；不确定/负面陈述仍可计E。'},
       'confirmed_defects':[{'old_rule':'V28_E_guideline_inclusion_relation','change':'移除将纳入诊疗方案这一身份自动视为E的补充规则；独立治疗推荐规则和效果证据仍保留。'},
                           {'old_rule':'E01 bare 临床价值 evidence','change':'按宽泛价值词的局部证据跨度抑制E，不按句子或文件整体抑制；明确患者获/受益、风险收益比较以独立证据锚点保留。'}],
       'scope':'通用语义谓词与局部证据抑制，新增函数不读取ID、来源或文件名；未改CAL定义、A/C标签和其他四维逻辑。',
       'development_controls':tests,'disputed_Ec_definition':{'id':'RECODE25-03090','decision':0,
          'rationale':'医疗赔付资料的通用数据定义未讨论药品费用、药物经济学比较或药品支付安排；保留此独立判断，不为参考标签改为1。'},
       'exposure_and_validation':'依据已封存的14条语义复核及CAL边界修订；已暴露RWE与GCP两例已如实标为语义复核。新边界测试为开发控制，不能宣称新的盲法达标。'}
    write('semantic_amendment_record.json',amendment)
    diff=[]
    for name in ('rules_se.py','rule_support.py','policy_coding_v27.py'):
        diff.extend(difflib.unified_diff((OLD/name).read_text().splitlines(True),(B/name).read_text().splitlines(True),
                                        fromfile='v28/'+name,tofile='v30/'+name))
    (B/'runtime_changes.patch').write_text(''.join(diff))
    run=json.loads((B/'all_predictions.run.json').read_text())
    assert all(Path(p).is_relative_to(B) for p in run['runtime_code_sha256'])
    assert all(sha(p)==h for p,h in run['runtime_code_sha256'].items())
    files={str(p.relative_to(B)):sha(p) for p in sorted(B.rglob('*'))
           if p.is_file() and '__pycache__' not in p.parts and p.name!='release_manifest.json'}
    manifest={'release':VERSION,'frozen_at':datetime.datetime.now().astimezone().isoformat(),
              'n':4924,'shared_input_original_path':str(shared),'shared_input_sha256':sha(shared),
              'baseline_prediction_path':str(OLD/'all_predictions.jsonl'),'baseline_prediction_sha256':sha(OLD/'all_predictions.jsonl'),
              'metadata_sha256':sha(metadata),'runtime_code_loaded_only_from_release_directory':True,
              'runtime_code_sha256':run['runtime_code_sha256'],'files_sha256':files,
              'summary':summary,'validation':'167 applicable legacy controls + 9 new constructed test methods pass; historical 168 includes one honestly recorded superseded expectation.'}
    write('release_manifest.json',manifest)
    print(json.dumps(summary,ensure_ascii=False))

if __name__=='__main__':main()
