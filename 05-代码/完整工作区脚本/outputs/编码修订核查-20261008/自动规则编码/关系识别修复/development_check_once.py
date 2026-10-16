"""Finite mechanics plus one 15-row regression; no reference labels read."""
from pathlib import Path
import json,sys,copy,hashlib,time,traceback
sys.dont_write_bytecode=True
b=Path(__file__).resolve().parent;sys.path.insert(0,str(b/'runtime'))
import pypdf
from common_definition_stage import _disease_severity_not_drug_harm
from common_se_ec_relations import inspect_safety,inspect_economics,_payment_relation
from rule_support import RuleView
from rules_se import _add_effectiveness
from policy_coding_v27 import code_unit
checks=[]
def test(name,expected,fn):
 try:
  actual=fn();checks.append({'name':name,'expected':expected,'actual':actual,'matches_mechanism_expectation':actual==expected})
 except Exception as e:checks.append({'name':name,'expected':expected,'actual':None,'matches_mechanism_expectation':False,'error_type':type(e).__name__,'error':str(e)})
def safety(text):
 return [(r['quote'],r['subtype']) for r in inspect_safety(text,drug_scope=True) if not _disease_severity_not_drug_harm(r['quote'])]
def effect(text):
 result={'evidence':[],'labels':{'S':0,'E':0,'Ec':0,'I':0,'F':0}}
 _add_effectiveness(RuleView({'unit_text':text},result))
 return [e['text'] for e in result['evidence'] if e['dimension']=='E']
test('condition_severity_is_not_drug_harm',False,lambda:bool(safety('严重危及生命是指病情严重、不可治愈或者发展不可逆。')))
test('disease_death_is_not_drug_harm',False,lambda:bool(safety('疾病严重，病情发展导致患者死亡。')))
test('drug_causes_condition_worsening_is_harm',True,lambda:bool(safety('药物引起病情恶化并危及生命。')))
test('adjacent_drug_risk_preserved',True,lambda:any('不良反应' in q for q,t in safety('病情严重危及生命。药物可能导致不良反应。')))
test('disease_quote_not_retained_beside_drug_risk',False,lambda:any('病情' in q for q,t in safety('病情严重危及生命。药物可能导致不良反应。')))
test('non_drug_information_security',False,lambda:bool(safety('数据安全制度应完善，避免网络风险。')))
test('nested_payment_reduction_rate_rises',True,lambda:_payment_relation('支付标准的下调比例增加4个百分点'))
test('nested_payment_reduction_rate_falls',True,lambda:_payment_relation('支付标准的下调比例减少2个百分点'))
test('nested_payment_fronted_instruction',True,lambda:_payment_relation('将支付标准的下调比例提高2个百分点'))
test('negative_payment_change_is_content',True,lambda:_payment_relation('支付标准的下调比例不增加'))
test('nested_payment_character_format',False,lambda:_payment_relation('支付标准的下调比例增加1位小数'))
test('nested_equipment_payment_is_not_medicine',False,lambda:_payment_relation('设备采购支付标准的下调比例增加4个百分点'))
test('non_drug_adjacent_payment_proposition',False,lambda:bool(inspect_economics('药品需签字。设备采购支付标准的下调比例增加4个百分点。',drug_scope=True)))
test('medicine_trial_superiority_result',True,lambda:bool(effect('药物临床试验已经达到预设优效结果。')))
test('negative_superiority_is_effect_content',True,lambda:bool(effect('药物临床试验尚未达到预设优效结果。')))
test('uncertain_superiority_is_effect_content',True,lambda:bool(effect('需要验证该药试验是否达到预设优效结果。')))
test('adjacent_software_superiority_not_drug_effect',False,lambda:bool(effect('药物需提交资料。软件试验达到预设优效结果。')))
test('non_drug_training_superiority',False,lambda:bool(effect('药品需签字。员工培训试验达到优效结果。')))
test('bare_clinical_value_not_effect',False,lambda:bool(effect('药物试验以临床价值为导向。')))
test('quoted_superiority_wording_format',False,lambda:bool(effect('复制“药物试验达到预设优效结果”字样。')))
(b/'mechanism_checks_once.json').write_text(json.dumps({'checks':checks,'failures':[c for c in checks if not c['matches_mechanism_expectation']],'mechanism_count':len(checks),'reference_answers_read':False,'development_only':True},ensure_ascii=False,indent=2))
# No adaptive correction or second full-entry run is performed.
inputs=[json.loads(l) for l in (b/'development_inputs15.jsonl').read_text().splitlines()]
assert len(inputs)==15 and not (b/'development_outputs15.jsonl').exists()
start=time.time();outputs=[]
with (b/'development_outputs15.jsonl').open('x') as out:
 for row in inputs:
  try:result=code_unit(copy.deepcopy(row['input']));payload={'case_id':row['case_id'],'id':row['id'],'status':'completed','result':result}
  except Exception as e:payload={'case_id':row['case_id'],'id':row['id'],'status':'failed','error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc()}
  outputs.append(payload);out.write(json.dumps(payload,ensure_ascii=False)+'\n');out.flush()
parent=b.parent/'统一操作判据实施';old=[json.loads(l) for l in (parent/'development_outputs15_with_environment_recovery.jsonl').read_text().splitlines()]
changes=[]
for before,after in zip(old,outputs):
 assert before['case_id']==after['case_id'] and before['id']==after['id']
 if after['status']!='completed':continue
 oldlabels=before['result']['labels'];newlabels=after['result']['labels']
 delta={d:{'before':oldlabels[d],'after':newlabels[d]} for d in newlabels if oldlabels[d]!=newlabels[d]}
 if delta:changes.append({'case_id':after['case_id'],'id':after['id'],'label_changes':delta,'new_current_evidence':after['result'].get('evidence',[])})
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
state=json.loads((b/'pre_edit_state.json').read_text());modified=[name for name,value in state['parent_runtime_sha256'].items() if sha(b/'runtime'/name)!=value]
IF_files=['common_if_relations.py','common_if_extensions03.py','common_if_current_relations05.py','common_innovation_relations14.py','common_medicine_access14.py','common_cited_list_conditions12.py']
report={'status':'completed_development_regression_not_final_validation','python_executable':sys.executable,'pypdf_version':pypdf.__version__,'actual_input_rows':15,'completed':sum(r['status']=='completed' for r in outputs),'failed':sum(r['status']=='failed' for r in outputs),'full_entry_run_count':1,'elapsed_seconds':time.time()-start,'input_sha256':sha(b/'development_inputs15.jsonl'),'input_matches_parent':sha(b/'development_inputs15.jsonl')==sha(parent/'development_inputs15.jsonl'),'modified_runtime_files':modified,'IF_modules_byte_identical':all(sha(b/'runtime'/name)==state['parent_runtime_sha256'][name] for name in IF_files),'label_changes_against_prior_rule_actual':changes,'unchanged_label_rows':[r['id'] for r,o in zip(outputs,old) if r['status']=='completed' and r['result']['labels']==o['result']['labels']],'mechanism_failures':[c for c in checks if not c['matches_mechanism_expectation']],'reference_labels_read':False,'metrics_computed':False,'models_called':0,'semantic_validation_pass_claimed':False}
(b/'actual_regression_execution.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print({k:v for k,v in report.items() if k not in ['label_changes_against_prior_rule_actual','unchanged_label_rows']})
for r in outputs: print(r['case_id'],r['id'],r['status'],r.get('result',{}).get('labels'),r.get('error',''))
for c in changes: print('CHANGE',c['id'],c['label_changes'])
