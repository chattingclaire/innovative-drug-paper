"""One bounded development check. No reference answers or scores are read."""
from pathlib import Path
import sys,json,copy,hashlib,time,traceback
base=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
sys.path.insert(0,str(base/'runtime'))
from common_innovation_relations14 import current_scientific_guidance,current_pointer,_document,_authenticate_paragraph,revise as innovation_revise
from common_medicine_access14 import current_medicine_relations
from common_se_ec_relations import inspect_economics
from visual_source_reader import authenticate_visual_paragraph
from policy_coding_v27 import code_unit
checks=[]
def check(name,expected,fn):
 try:
  actual=fn(); checks.append(dict(name=name,expected=expected,actual=actual,pass_check=actual==expected))
 except Exception as e:
  checks.append(dict(name=name,expected=expected,actual=None,pass_check=False,error_type=type(e).__name__,error=str(e)))
# These are mechanics derived from the fixed manual, not calibration answers.
check('noun_design_before_modal',True,lambda:bool(current_scientific_guidance('在设计过程中，应充分结合人因工程原则，考虑患者操作能力。')))
check('modal_before_design',True,lambda:bool(current_scientific_guidance('应在设计过程中结合人因工程原则，考虑患者操作能力。')))
check('ordinary_safety_duty',False,lambda:bool(current_scientific_guidance('申请人应提交安全性报告并更新药物警戒管理计划。')))
check('postmarketing_tool_function',False,lambda:bool(current_scientific_guidance('在上市后监测阶段，AI能够分析临床研究数据并监测用药风险。')))
check('explicit_list_programme_predicate',True,lambda:current_pointer('以下药品可以申请适用优先审评审批程序：'))
check('directory_navigation_is_not_pointer',False,lambda:current_pointer('申报材料目录详见工作方案。'))
check('general_social_influence_not_equity',False,lambda:bool(current_medicine_relations('经济状况、家庭支持等影响患者对药物治疗的接受度和持续性。')))
check('earlier_unrelated_limit_not_bind',True,lambda:bool(current_medicine_relations('心理因素限制社交活动。因经济条件限制患者持续接受药物治疗。')))
check('trial_crossover_not_equity',False,lambda:bool(current_medicine_relations('对照组患者发生疾病进展后，有机会交叉至试验组接受该治疗。')))
check('long_cost_targeted_guarantee',True,lambda:bool(current_medicine_relations('对使用周期较长、疗程费用较高的药品，可建立单独药品保障机制。')))
check('explicit_payment_content_verification',True,lambda:bool(inspect_economics('企业确认药品协议信息（支付标准、支付范围），并完成协议签订。')))
check('payment_field_format_not_content',False,lambda:bool(inspect_economics('只检查药品支付标准字段是否填写完整、格式正确。')))
check('pure_signature_not_content',False,lambda:bool(inspect_economics('确认药品协议已签字盖章。')))
rows=[json.loads(l) for l in (base/'development_inputs15.jsonl').read_text().splitlines()]
source=next(q['input'] for q in rows if q['case_id']=='CAL-08')
def invalid_innovation_source():
 bad=copy.deepcopy(source);bad['unit_source_sha256']='0'*64
 if 'source_sha256' in bad:bad['source_sha256']='0'*64
 result={'labels':{'S':0,'E':0,'Ec':0,'I':0,'F':0},'evidence':[],'judgement_status':'determined'}
 innovation_revise(bad,result)
 return bool(result.get('common14_pending_dimensions',{}).get('I'))
check('triggered_scientific_source_SHA_invalid_is_pending',True,invalid_innovation_source)
x=json.loads((base/'visual_source_check_input.json').read_text());doc,paras,i=_document(x);par=paras[i]
check('visual_actual_bound_paragraph',True,lambda:bool(_authenticate_paragraph(x,par,doc).get('authentication_v34',{}).get('visual_transcription_reproduced_in_current_runtime')))
wrongpage=copy.deepcopy(par);wrongpage['pages']=[1]
check('visual_wrong_page_rejected',True,lambda:authenticate_visual_paragraph(x,wrongpage) is None)
wrongtext=copy.deepcopy(par);wrongtext['text']+='额外未认证内容'
check('visual_wrong_paragraph_rejected',True,lambda:authenticate_visual_paragraph(x,wrongtext) is None)
(base/'function_and_source_checks_once.json').write_text(json.dumps({'checks':checks,'passed':sum(c['pass_check'] for c in checks),'total':len(checks),'failures':[c for c in checks if not c['pass_check']],'actual_model_calls':0,'reference_answers_read':False,'development_only':True},ensure_ascii=False,indent=2))
# Exactly one actual full-entry invocation for each of the 15 source inputs.
assert not (base/'development_outputs15.jsonl').exists(), 'existing run must not be overwritten'
start=time.time(); outputs=[]
with (base/'development_outputs15.jsonl').open('x') as out:
 for row in rows:
  try:
   result=code_unit(copy.deepcopy(row['input']))
   payload={'case_id':row['case_id'],'id':row['id'],'result':result,'status':'completed'}
  except Exception as e:
   payload={'case_id':row['case_id'],'id':row['id'],'status':'failed','error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc()}
  outputs.append(payload);out.write(json.dumps(payload,ensure_ascii=False)+'\n');out.flush()
report={'actual_rows':len(outputs),'completed':sum(q['status']=='completed' for q in outputs),'failed':sum(q['status']=='failed' for q in outputs),'elapsed_seconds':time.time()-start,'finite_run_count':1,'full_population_run':False,'model_calls':0,'reference_answers_read':False,'labels_not_compared_with_answers':True,'function_failures':[c for c in checks if not c['pass_check']]}
(base/'finite_execution_once.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False))
for q in outputs:print(q['case_id'],q['id'],q['status'],q.get('result',{}).get('labels'),q.get('error',''))
