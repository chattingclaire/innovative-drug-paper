"""Seal static provenance and constructed results, without real inference."""
import ast
import datetime
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = ROOT / '05-validation/rule-request-routing-repair-sol'


def binding(path):
    p = Path(path).resolve()
    data = p.read_bytes()
    return {'path': str(p), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def write(name, value):
    with (HERE/name).open('x', encoding='utf8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


inputs = [BASE/n for n in ['source_packet.py','source_receipts.py','evidence.py','relations.py','dimensions.py',
           'rule_driver.py','interface_common.py','algorithm-bindings.json','formal-manual-binding.json','report.md','controls.py']]
inputs += [ROOT/'03-manual/common-manual-v1.3F-frozen/manual.txt',
           ROOT/'03-manual/human4-alignment-candidate-sol/manual.txt',
           ROOT/'logs/remaining4-calibration-delivery/report-inputs.json',
           ROOT/'06-coding/rule-routing-dev77-independent-sol/run77-once/predictions.jsonl']
inputs += [ROOT/('06-coding/development77-native-inputs-v14/packets/RECODE25-'+rid+'.compact.json')
           for rid in ['00005','03876','00138','02573']]
materials = json.loads((ROOT/'logs/remaining4-calibration-delivery/report-inputs.json').read_text())
inputs += [Path(m['path']) for m in materials['bindings'] if m['path'].endswith(('.pdf','.png'))]
original_bindings = [binding(p) for p in dict.fromkeys(inputs)]
write('input-bindings.json', {'scope':'static code/manual/explicit remaining-four necessary material review',
      'inputs': original_bindings, 'input_results_not_runtime_features':True,
      'real_policy_inference_runs':0, 'old_inputs_write_authorized':False,
      'old_prediction_review':'four selected old development records and nearest-candidate reasons only; no reference used in algorithm',
      'visual_review':'original PDF physical page 11 flow PNG inspected statically; this does not claim rule pixel inference',
      'real_77_800_4481_execution':False, 'formal800_Gold_unlisted_full_policy_body_read':False})

modules = [binding(HERE/(n+'.py')) | {'module':n} for n in
           ['source_packet','source_receipts','evidence','relations','dimensions']]
write('algorithm-bindings.json', {'version':'human4-general-semantic-repair-algorithm-bindings-1',
      'algorithm_version':'rule-v19-human4-general-repair-development-candidate-1','modules':modules,
      'positive_predicate_semantics_modified':True,'dependency_routing_and_null_scope_modified':True,
      'formal_freeze_or_execution_authorized':False,'real_cohort_inference_runs':0,
      'AI_development_repair':True,'calibration_labels_already_disclosed':True,'blind_validation':False})

def code_anchor(name, func, baseline=False):
    p = (BASE if baseline else HERE)/name
    node = next(n for n in ast.walk(ast.parse(p.read_text())) if isinstance(n,ast.FunctionDef) and n.name==func)
    return {'path':str(p),'function':func,'start_line':node.lineno,'end_line':node.end_lineno}

def block(key):
    return next(b for b in materials['blocks'] if b['key']==key)

evidence = []
for key in ['00005条件','00138语境2','00138语境3','00138语境4','03876补材9','03876补材21']:
    b=block(key)
    evidence.append({'key':key,'path':b['path'],'locator':b['locator'],'text':b['text'],
                     'text_sha256':b['text_sha256'],'source_available_in_report_inputs':True,
                     'static_review_only':True,'real_candidate_runtime_consumption':False})
write('material-evidence.json', {'source_index':binding(ROOT/'logs/remaining4-calibration-delivery/report-inputs.json'),
      'evidence':evidence,'material_version_change_required_for_old_03876_packet':True,
      'rule_runtime_receipts_for_real_material_not_yet_produced':True})

root_causes = [
 {'target':'00005-S','disclosed_human_recheck':1,'old_rule':0,
  'current_quote':materials['rows'][0][6],
  'old_zero_cause':'_standards的当前入口要求审核/核验/符合等条件表达；当前操作性临床优势申请命题没有这些词。当前S没有安全词，完整定义也未作为可用关系被展开，因此S为no_substantive_relation。',
  'baseline_code':[code_anchor('relations.py','_standards',True),code_anchor('dimensions.py','_safety_effect',True)],
  'new_code':[code_anchor('relations.py','_operative_value_definition'),code_anchor('dimensions.py','_safety_effect')],
  'chain':'当前明确临床优势申请条件 → 同源结构种子和唯一当前命题 → 同版具名程序的完整适用条件组 → 明显临床优势的具体定义 → 药物安全性优势分支 → S。',
  'source_keys':['00005条件'],'negative_boundary':'疾病严重程度、程序名称、宗旨和完整定义不存在S时不补S。'},
 {'target':'03876-Ec','disclosed_human_recheck':1,'old_rule':0,
  'current_quote':materials['rows'][1][6],
  'old_zero_cause':'_economics实质价格候选没有把价格协商节点与定价内容解析相接；原价格谓词不含实际磋商配置关系，最终以仅谈判阶段/名称排除。旧packet的FULLSOURCE、explicit/historical资源均为空，缺评估价定义仍被0处理。',
  'baseline_code':[code_anchor('dimensions.py','_economics',True)],
  'new_code':[code_anchor('relations.py','_price_arrangement_definition'),code_anchor('dimensions.py','_economics')],
  'chain':'当前实际目录/适应症成功分支中的价格协商节点 → 同PDF同版紧邻药品/目录对象与节点指代 → 评估确定的协商价格 → 实际现场磋商 → Ec价格配置。',
  'source_keys':['03876补材9','03876补材21'],'negative_boundary':'价格阶段或成功状态单独不足；商保推荐目录不推实际承保/医保支付。旧packet缺定价定义时新候选应请求Ec/null。'},
 {'target':'00138-I','disclosed_human_recheck':1,'old_rule':0,
  'current_quote':materials['rows'][2][6],
  'old_zero_cause':'_applicable_support只处理申请前适用同规范，_mechanisms一般具名路径没有解析主原件纳入后当前沟通与实际技术审评/补充技术资料关系。普通沟通词不在SUPPORT，故只记录创新身份/形式未满足I3。',
  'baseline_code':[code_anchor('relations.py','_applicable_support',True),code_anchor('dimensions.py','_innovation',True)],
  'new_code':[code_anchor('relations.py','_postadmission_technical_support'),code_anchor('dimensions.py','_innovation')],
  'chain':'当前对已纳入品种实际沟通 → 同源完整同程序唯一位置 → 适用范围中的创新/改良对象 → 纳入后技术审评优先沟通和补充技术资料反馈机会 → 当前同一实际服务 → I3对象—可用安排—直接联系。',
  'source_keys':['00138语境2','00138语境3','00138语境4'],'negative_boundary':'不借申请前研究反馈，不由程序身份、创新名、沟通形式或一般宗旨单独补I。'},
 {'target':'00138-F','disclosed_human_recheck':1,'old_rule':0,
  'current_quote':materials['rows'][3][6],
  'old_zero_cause':'没有同一程序纳入后关系，_fairness只看到当前一般沟通；当前缺口和该沟通优先配置均未被有限补足，因此没有F内容。',
  'baseline_code':[code_anchor('dimensions.py','_fairness',True)],
  'new_code':[code_anchor('relations.py','_postadmission_technical_support'),code_anchor('dimensions.py','_fairness')],
  'chain':'同程序范围中明确的供药/治疗选项缺口分支 → 以需要为条件的纳入对象 → 当前已纳入品种实际技术沟通 → 技术审评中这同一沟通服务可优先安排 → F按需审评服务机会。',
  'source_keys':['00138语境2','00138语境3','00138语境4'],'negative_boundary':'F机会只取本项优先技术沟通，不以所有创新/优先品种、一般提速或申请前服务代替。缺口无本项配置、配置无缺口均F=0。'}]
write('root-causes-and-chains.json', {'static_diagnosis':True,'real_candidate_run':False,
      'known_answers_disclosed_before_development':True,'not_a_blind_or_formal_validation':True,
      'root_causes':root_causes,'02573_Ec_expected':0,
      '02573_boundary':'甲乙分类优先基本药物未明示价格、费用、支付标准，保持0。'})

write('pre-run-expectations.json', {'status':'sealed_before_any_real_candidate_inference',
      'execution_authorization':'ROOT_pending; constructed controls only currently authorized',
      'AI_development_repair':True,'labels_already_disclosed':True,'blind_validation':False,
      'formal_validation':False,'kappa_1_target':False,'score_driven_definition_selection':False,
      'expected_target_slots_when_same_edition_necessary_material_uniformly_delivered':
      [{'record':'RECODE25-00005','dimension':'S','expected':1},
       {'record':'RECODE25-03876','dimension':'Ec','expected':1},
       {'record':'RECODE25-00138','dimension':'I','expected':1},
       {'record':'RECODE25-00138','dimension':'F','expected':1}],
      'negative_control':{'record':'RECODE25-02573','dimension':'Ec','expected':0},
      'old_03876_packet_without_new_same_PDF_price_definition_expected':{'Ec':None,'necessary_material_request':'price_arrangement'},
      'other_77_decisions':'not prescribed; independently retain what actual current and allowed source relations support',
      'implementation_error':'technical failure; never renamed classification 0/null',
      'accuracy_claim':'No claim that candidate is more accurate than old machine until actual authorized run and separate analysis.'})

patch=[]
for name in ['source_packet.py','source_receipts.py','evidence.py','relations.py','dimensions.py','rule_driver.py','interface_common.py']:
    patch += list(difflib.unified_diff((BASE/name).read_text().splitlines(True),(HERE/name).read_text().splitlines(True),
                                     fromfile='request-routing-candidate/'+name,tofile='human4-general-repair/'+name))
with (HERE/'actual-candidate.patch').open('x') as f:f.writelines(patch)
write('input-bindings-post-check.json', {'checked':len(original_bindings),
      'every_bound_input_unchanged':all(binding(b['path'])==b for b in original_bindings),
      'checks':[{'before':b,'after':binding(b['path'])} for b in original_bindings]})
print(json.dumps({'bound_static_inputs':len(original_bindings),'real_cohort_inference_runs':0,
                  'new_algorithm_modules':len(modules),'four_root_causes_documented':len(root_causes)},ensure_ascii=False))
