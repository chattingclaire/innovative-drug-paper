"""Finalize existing S3 output only; no candidate imports or executions."""
from pathlib import Path
import datetime
import hashlib
import json

D = Path(__file__).resolve().parent
ROOT = D.parents[1]
CODE = ROOT / '06-coding/rule-five-dimension-joint-root/versions/joint-v5-primary-standard-bridge-sol'
PLAN = ROOT / '08-audits/common-candidate-actual-interface-sol/historical-human-S3-development-plan'
BASE = ROOT / '08-audits/common-candidate-actual-interface-v4-execution-sol'

def bind(p):
    p = Path(p).resolve(); raw = p.read_bytes()
    return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

def load(p): return json.loads(Path(p).read_bytes())

def write(name,value):
    with (D / name).open('x',encoding='utf8') as f:
        json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False); f.write('\n')

assert not (D/'output-seal.json').exists()
summary = load(D/'execution-summary.json'); rows = load(D/'execution-results.json')
readback = load(D/'trace-readback-summary.json'); started = load(D/'execution-started.json')
original = (D/'preflight01-failed-capture/execute_once.original.py').read_bytes()
fixed = (D/'execute_once.py').read_bytes()
oldkey = b"pre['post_independent_result_mutation_allowed']"
newkey = b"pre['post_independent_algorithm_edit_allowed']"
assert original.count(oldkey) == 1 and fixed == original.replace(oldkey,newkey)
capture = load(D/'preflight01-failed-capture/output-seal.json')
for member in capture['members']:
    assert bind(member['path']) == member
repair = {'preflight_process_01':{'exit_code':1,'failure':'KeyError: post_independent_result_mutation_allowed','candidate_imports_or_semantic_unit_or_RelationView_or_judge_calls':0,'preserved_archive_seal':bind(D/'preflight01-failed-capture/output-seal.json')},'ROOT_followup_authority':'这属于已授权执行中的常规前置runner修正，直接继续；仅改实际v5字段post_independent_algorithm_edit_allowed=false。imports之前KeyError不算三条已执行或语义/技术重试，纠正后各条仍首次一次。','audit_runner_change':{'only_changed_field':True,'before':'post_independent_result_mutation_allowed','after':'post_independent_algorithm_edit_allowed','original_runner':bind(D/'preflight01-failed-capture/execute_once.original.py'),'corrected_runner':bind(D/'execute_once.py')},'static_AST_preflight':{'exit_code':0,'candidate_calls':0},'first_candidate_execution_process':{'command':'python3 '+str(D/'execute_once.py'),'exit_code':0,'candidate_calls':summary['calls'],'classification_retries':0},'saved_trace_readback_process':{'command':'python3 '+str(D/'analyze_saved_trace.py'),'exit_code':0,'additional_candidate_calls':0},'total_candidate_executions_by_record':{r['record_id']:r['calls'] for r in rows},'not_total_Python_process_count_one':True}
write('runner-preflight-correction-and-tool-receipt.json',repair)
failures = [{'record_id':r['record_id'],'complete_first_output':r} for r in rows if r['execution_error'] or r['validator_error'] or r['trace_inspection_error'] or not r['matches_historical_S']]
write('candidate-failures-full-inputs-and-results.json',{'failures':failures,'failures_N':len(failures),'preflight_runner_failure_preserved_separately':True,'filled_or_rewritten_values_N':0})
pre = load(CODE/'pre-execution-seal.json'); planseal = load(PLAN/'output-seal.json')
sources = [bind(CODE/'pre-execution-seal.json'),bind(CODE/'algorithm-bindings.json'),bind(PLAN/'output-seal.json'),bind(BASE/'output-seal.json')] + pre['five_modules'] + [pre['manual']] + pre['common_frozen_input_bindings'] + planseal['members'] + planseal['inputs']
sources += [bind(ROOT/'00-baseline/source-files/980acf76a2fb9b95-NMPA-突破性治疗等三程序-2020-附件正文.txt')]
inputs = {}
for m in sources:
    assert bind(m['path']) == m
    inputs[m['path']] = m
for m in pre['five_modules']:
    assert bind(D/'code-snapshot'/Path(m['path']).name)['sha256']==m['sha256']
write('input-bindings-and-final-readback.json',{'inputs':list(inputs.values()),'all_exact_bytes_readback':True,'candidate_and_plan_and_v4_originals_unchanged':True,'expected_dimensions_only':['S'],'other_dimension_values_observation_only':True,'no_main_LLM_partial_labels_or_other_cohort_predictions_read':True})
readme = '''三条历史S3在最终joint-v5冻结算法上各首次执行一次，S=[1,1,1]，与事前历史真人确认S=1匹配。其他四维仅观察，完整首次输出均保存。semantic_unit、RelationView、judge各3次，构造/执行/validator/trace异常均0，validator3通过，没有候选重试。

第一次Python进程在导入候选前因审计runner沿用v4字段而退出1；candidate调用0。原runner、工具异常和capture seal保留在preflight01-failed-capture。ROOT确认这是常规前置修正；只把该字段读取改为v5实际post_independent_algorithm_edit_allowed=false，逐字差异已核。纠正后的候选执行exit0，不能把本目录描述成总共只有一个Python进程。

输入严格复用historical-human-S3-development-plan的三份source-only packet；只将source_bundle传给冻结adapter，不传历史预期或记录ID，不注入unit/resolved/proof/标签。原v4各一次S=[0,0,0]失败基线、计划和代码均保持，v5是新增版本级开发回归。

已保存trace的15个source_textleaf范围、46条唯一context引文（1303处出现）及24个当前锚点核对通过；46条均核到严格UTF8原件、SHA、Unicode/byte/行位置。实际语义阅读为三条完整当前命题，以及同版突破性治疗组件原件第3–38行必要标准/终止/边界；其他程序仅做字节/leaf机械校验，不称读完。

00036/00038以纳入条件完整组核操作性标准—终止后果，S正消费者具体来自原件第15行安全性优势条件；00038保留整个或命题，手续未交说明分支不被解释为安全问题。00045以终止标准有限组核资格审核/终止，S依据第33行重大安全性问题条件；第35行品种清单尾段仅闭合证明，第36行下一标题仅边界证明。三条不表示具体药品不安全、风险已经发生或所有条件均失败。

自然产生29个受限S/E/Ec标准单位，6个该路径正消费者均为S/E，14个全部正消费者均满足其已有消费者声明。本S3自然only_IF单位0，未实测only_IF正消费者交集；未注入伪关系。依据为共同手册5ea7第9、29、31、40–41、44、46行，原文/范围/消费完整读回见standard-consumer-and-boundary-readback.json。

这是三条已开发暴露历史目标的版本回归，不是新真人、正式准确率、稳定性或全4481验证。未执行其他cohort，未读取主LLM部分标签，未改任何旧冻结材料、手册、协议、候选或原预期；无新增政策ID/真人结果/正式指标。
'''
with (D/'README.md').open('x',encoding='utf8') as f: f.write(readme)
seal_path = (D/'output-seal.json').resolve()
files = sorted(p.resolve() for p in D.rglob('*') if p.is_file() and p.resolve()!=seal_path)
assert all(p!=seal_path for p in files)
members = [bind(p) for p in files]
write('output-seal.json',{'status':'sealed_first_v5_historical_S3_development_execution_and_saved_trace_review','at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'members':members,'inputs':list(inputs.values()),'self_excluded':True,'candidate_calls':summary['calls'],'classification_retry_N':0,'preflight_candidate_calls_N':0,'actual_S':summary['actual_S'],'only_IF_positive_intersection_tested':False,'formal_metrics_N':0,'new_human_results_N':0})
seal = load(seal_path)
assert not any(Path(m['path']).resolve()==seal_path for m in seal['members'])
for m in seal['members']+seal['inputs']: assert bind(m['path'])==m
print(json.dumps({'seal':bind(seal_path),'members_N':len(seal['members']),'inputs_N':len(seal['inputs']),'all_readback_match':True,'self_member_N':0,'actual_S':summary['actual_S']},ensure_ascii=False))
