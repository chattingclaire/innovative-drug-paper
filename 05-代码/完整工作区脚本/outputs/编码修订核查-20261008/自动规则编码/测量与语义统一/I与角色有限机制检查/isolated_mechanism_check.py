"""One finite mechanism check; no whole coding entrance or reference labels."""
import copy,hashlib,json,sys,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RT=ROOT/'runtime';sys.path.insert(0,str(RT))
from current_unit_role import classify,permits_content_expansion
from current_innovation_support import current_support_relations
import common_innovation_relations14 as innovation
import common_medicine_access14 as medicine
import common_coverage_relations11 as coverage
import source_context_adapter_v34 as adapter
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=ROOT.parents[1]/'LLM编码/统一判据编码准备/共用纯来源材料04/rule_inputs_material04.jsonl'
# IDs choose already-diagnosed source passages only; never enter a rule.
ids={'RECODE25-03424','RECODE25-00087','RECODE25-03476','RECODE25-03474','RECODE25-01768','RECODE25-01818','RECODE25-00033','RECODE25-00046','RECODE25-01401'}
records=[]
for line in source.open():
 r=json.loads(line)
 if r['id'] in ids: records.append(r)
assert len(records)==len(ids)
controls=[
 ('structural_pointer','这些特征包括但不限于以下几个方面:', 'structural_reference_only',False),
 ('renamed_structure','上述要求包括以下几个方面:', 'structural_reference_only',False),
 ('current_obligation','药品评价应包括以下内容:', 'substantive_list_lead',True),
 ('current_benefit','以下符合条件的药品可以申请适用优先审评审批程序:', 'substantive_list_lead',True),
 ('mixed_current_content','应评价药品安全性。这些特征包括以下几个方面:', 'ordinary_or_mixed_substantive_unit',False),
]
results=[]
for name,text,role,expand in controls:
 actual=classify(text)
 results.append(dict(kind='synthetic_role_grammar_control',name=name,text=text,actual=actual,
  expected_mechanism_role=role,expected_expansion_gate=expand,mechanism_pass=(actual['role']==role and permits_content_expansion(text)==expand)))
support_controls=[
 ('ordinary_design','创新药临床研究应参考药代数据优化剂量安排。',False),
 ('actual_feedback','药审中心为创新药研发提供具体研究方案建议。',True),
 ('ordinary_evidence_submission','创新药申请人应提供技术指导资料。',False),
 ('withdrawal_presence','不再为创新药研发提供研发资源。',True),
 ('ordinary_tool_capability','创新药文档中的AI系统能够识别不良反应。',False),
 ('specific_convenience','创新药研发可以免于重复开展临床研究要求。',True),
]
for name,text,has in support_controls:
 frames=current_support_relations(text)
 results.append(dict(kind='synthetic_support_grammar_control',name=name,text=text,actual_frames=frames,
  expected_current_arrangement_presence=has,mechanism_pass=(bool(frames)==has),
  whole_sentence_preserved_for_final_negation_helper=True))
for r in records:
 text=r['input']['unit_text'];item=dict(kind='actual_source_isolated_module_control',id=r['id'],text=text,
  source_input_sha256=hashlib.sha256(json.dumps(r['input'],ensure_ascii=False,sort_keys=True).encode()).hexdigest(),
  current_role=classify(text),support_frames=current_support_relations(text))
 try:
  record=adapter.prepare(copy.deepcopy(r['input']))
  result={'evidence':[],'judgement_status':'determined','drug_object_in_unit':True}
  # Only changed origins/roles, no baseline stage, no final entrance labels.
  if item['current_role']['role']=='structural_reference_only':
   adapter.authenticate_target(record)
   item['actual_action']='source_identity_authenticated_structural_unit_not_expanded'
  else:
   coverage._guidance(record,text,result['evidence'],result)
   result=innovation.revise(record,result)
   result=medicine.revise(record,result)
  item['module_result']=result
  item['execution_status']='completed'
 except Exception as error:
  item.update(execution_status='failed',error_type=type(error).__name__,error=str(error),traceback=traceback.format_exc())
 results.append(item)
# Bad source identity is checked before pure-role zeroing; do not run encoder.
pure=next(r for r in records if r['id']=='RECODE25-03424')['input']
bad=copy.deepcopy(pure);bad['candidate_sha256']='0'*64
try:
 adapter.authenticate_target(bad)
 anomaly=dict(kind='source_anomaly_control',accepted_invalid_candidate_sha=True,mechanism_pass=False)
except Exception as error:
 anomaly=dict(kind='source_anomaly_control',accepted_invalid_candidate_sha=False,mechanism_pass=True,error_type=type(error).__name__,error=str(error))
results.append(anomaly)
output=ROOT/'I与角色有限机制检查/isolated_results.json'
output.write_text(json.dumps(dict(scope='11 synthetic function controls + 9 source-only isolated module controls + 1 source anomaly; no full coding entrance, not validity validation',input_path=str(source),input_sha256=sha(source),manual_sha256=innovation.MANUAL_SHA256,results=results),ensure_ascii=False,indent=2)+'\n')
for r in results:
 print(json.dumps({k:r[k] for k in ('name','id','kind','mechanism_pass','execution_status','error') if k in r},ensure_ascii=False))
