from pathlib import Path
import ast,json,sys,hashlib
B=Path(__file__).resolve().parent;W=B.parents[1];RT=B/'runtime'
for p in RT.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
sys.path.insert(0,str(RT))
from common_if_relations import inspect_innovation,inspect_fairness
import common_coverage_relations11 as coverage
from common_definition_stage import _supplemental_current_relations
from common_medicine_access14 import current_medicine_relations
P=W/'统计复算/来源读取与图示校正/规则输入4480.jsonl'
rows={r['id']:r['input'] for r in map(json.loads,P.read_text().splitlines())}
cases=[
 ('actual_03710_postposed_value',rows['RECODE25-03710']['unit_text'],True,True),
 ('actual_02206_review_convenience',rows['RECODE25-02206']['unit_text'],True,True),
 ('nominal_quantification_table','药品创新价值量化分级表',True,False),
 ('quantification_field_format','创新价值量化字段不能为空',True,False),
 ('actual_required_quantification','药品创新价值应进行量化。',True,True),
 ('actual_object_quantification','对药品创新价值进行量化。',True,True),
 ('negative_quantification','药品创新价值尚不能进行量化和分级。',True,True),
 ('non_drug_value_even_with_drug_scope','设备创新价值应进行量化；药品风险另行评价。',True,False),
 ('review_support_withdrawal','程序终止后，不再加速完成创新药临床试验申请审评审批。',True,True),
 ('purpose_without_arrangement','为加速完成创新药临床试验申请审评审批，制定本文件。',True,False),
 ('ordinary_safety_obligation','创新药研发中，申请人应提交安全性报告。',True,False),
 ('identity_excluded','该药不属于创新药，按普通程序申报。',True,False),
 ('review_form_submission','提交《加速完成创新药临床试验申请审评审批》材料。',True,False),
]
results=[]
for name,text,scope,expected in cases:
 evidence=inspect_innovation(text,drug_scope=scope);actual=bool(evidence)
 results.append({'name':name,'text':text,'assumed_drug_scope':scope,'expected_presence_for_mechanism_control_only':expected,'actual_presence':actual,'passed':actual==expected,'evidence':evidence})
fresults=[]
for name,text in [('actual_01090_general_basic_supply',rows['RECODE25-01090']['unit_text']),('general_patient_need','保障患者合理的用药需要。')]:
 out=[];coverage._direct_needs(text,out)
 fresults.append({'name':name,'text':text,'expected_shortcut_evidence':False,'actual_shortcut_evidence':out,'passed':not out})
text='减轻贫困患者的药费，保障持续接受药物治疗。';out=inspect_fairness(text,drug_scope=True)
fresults.append({'name':'independent_patient_affordability_preserved','text':text,'expected_independent_equity_evidence':True,'actual_evidence':out,'passed':bool(out)})
# Report mixed actual units separately. No full-entry call, no silent semantic zero.
observations=[]
for rid in ('RECODE25-02556','RECODE25-03206'):
 text=rows[rid]['unit_text'];out=inspect_fairness(text,drug_scope=True)
 for dim,relation in _supplemental_current_relations(text,True):
  if dim=='F':out.append(relation)
 extra=[]
 coverage._capacity_constraints(text,extra);coverage._direct_needs(text,extra);coverage._linked_needs(text,extra)
 out.extend(e for e in extra if e['dimension']=='F')
 access=current_medicine_relations(text)
 observations.append({'id':rid,'text':text,'current_independent_F_candidates':out,'medicine_access_relation_candidates':access,'independent_F_candidate_present':bool(out or access),'full_entry_not_run':True,'manual_relation_observation':'explicit保障短板+目录调整+患者需要' if rid.endswith('02556') else 'patient capacity linked to drug guarantee level','uncovered_relation_flag':not bool(out or access)})
report={'scope':'isolated mechanism checks only; not full-entry predictions or validity','input_sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'manual_sha256':hashlib.sha256((W/'定义溯源核查/测量与计数统一/共用编码手册.md').read_bytes()).hexdigest(),'innovation_controls':results,'equity_controls':fresults,'n_controls':len(results)+len(fresults),'controls_all_pass':all(r['passed'] for r in results+fresults),'mixed_actual_equity_observations':observations,'independent_mixed_F_relations_all_covered':all(r['independent_F_candidate_present'] for r in observations),'source_or_model_labels_not_used':True,'full_coder_called':False}
assert not (B/'模块机制检查01.json').exists()
(B/'模块机制检查01.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'controls_all_pass':report['controls_all_pass'],'failures':[r for r in results+fresults if not r['passed']],'mixed_actual_equity_observations':observations},ensure_ascii=False,indent=2))
