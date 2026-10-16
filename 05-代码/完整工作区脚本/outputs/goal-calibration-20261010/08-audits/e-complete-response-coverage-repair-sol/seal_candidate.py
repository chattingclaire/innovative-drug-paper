"""Mechanical reporting and seal; no classifier imports or execution."""
from pathlib import Path
import datetime
import difflib
import hashlib
import json

A = Path(__file__).resolve().parent
B = A.parents[1]
V = B / '06-coding/rule-five-dimension-joint-root/versions/joint-v9-e-outcome-candidate-sol'
O = V.parent / 'joint-v9-generic-relationship-sol'

def bind(p):
    p=p.resolve(); raw=p.read_bytes()
    return dict(path=str(p), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())

def save(p,x):
    with p.open('x',encoding='utf8') as f:
        json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')

now=datetime.datetime.now(datetime.timezone.utc).isoformat()
pre=json.loads((A/'pre-edit-contract.json').read_bytes())
for item in pre['base_modules']+pre['original189_control_bindings']+[pre['source_candidate_freeze'],pre['targeted_controls']]:
    assert bind(Path(item['path']))==item, 'Pre-existing input changed: '+item['path']
read_seal=json.loads((A/'execution02/pre-execution-seal.json').read_bytes())
for item in read_seal['selected_original98_packet_bindings']:
    assert bind(Path(item['path']))==item
for execution in ('execution01','execution02'):
    saved=json.loads((A/execution/'output-seal.json').read_bytes())
    for item in saved['files']:
        assert bind(Path(item['path']))==item, 'Preserved actual execution file changed'
    for n in ('source_packet','source_receipts','evidence','relations','dimensions'):
        if execution=='execution02':
            assert (A/execution/'code-snapshot'/(n+'.py')).read_bytes()==(V/(n+'.py')).read_bytes()

rows=json.loads((A/'execution02/results.json').read_bytes())
s1=json.loads((A/'execution01/summary.json').read_bytes())
s2=json.loads((A/'execution02/summary.json').read_bytes())
assert len(rows)==213
actual_targeted=rows[189:]
assert len(actual_targeted)==24 and all(x['passed'] for x in actual_targeted)
assert sum(x['expected']['E']==0 for x in actual_targeted)==13
correction={'at_utc':now,'kind':'mechanical_report_count_correction_only','original_preserved':bind(A/'execution02/summary.json'),'field':'targeted24.case_N','serialized_value':s2['targeted24']['case_N'],'correct_value':len(actual_targeted),'derived_from':bind(A/'execution02/results.json'),'cause':'The copied control-report script retained the literal original22 count while the actual loop ran24 fixed targeted controls. Other counts, controls, expectation, classifier code and result rows unchanged.','reclassification':False,'original_summary_and_output_seal_unchanged':True}
save(A/'summary-count-correction.json',correction)
with (A/'attempt01-to-attempt02.diff').open('x',encoding='utf8') as f:
    for name in ('relations','dimensions'):
        before=(A/'execution01/code-snapshot'/(name+'.py')).read_text()
        after=(V/(name+'.py')).read_text()
        f.writelines(difflib.unified_diff(before.splitlines(keepends=True),after.splitlines(keepends=True),fromfile='execution01/'+name+'.py',tofile='execution02/'+name+'.py'))
proof=json.loads((A/'static02/ast-isolation-proof.json').read_bytes())
components=json.loads((A/'static02/e-patch-components.json').read_bytes())
manual=B/'03-manual/full4481-common-release-20261010-root/manual.txt'
c_review=B/'08-audits/v10-generic-relationship-repair-sol/independent-E-control-review'
inputs=pre['base_modules']+pre['original189_control_bindings']+[pre['source_candidate_freeze'],pre['targeted_controls'],bind(A/'targeted24-fixed-before-second-edit.json'),bind(manual)]+[bind(c_review/x) for x in ('report.md','review.json','output-seal.json')]+[read_seal['sealed_original189_v9_actual_baseline']]+read_seal['selected_original98_packet_bindings']
save(A/'input-hashes.json',{'at_utc':now,'local_inputs':inputs,'original_file_readback_exact':True,'new200_or_remaining_materials_read':False,'only_original189_bound98_packet_files':True,'external_reference':{'url':'https://www.fda.gov/media/71195/download','title':'Clinical Trial Endpoints for the Approval of Cancer Drugs and Biologics, December 2018','sections':'III.B.2 Objective Response Rate; III.B.3 Complete Response','role':'terminology corroboration only, no material inserted into manual/prompt/production packets','local_download':False}})
target=next(x for x in rows if x['name']=='clinical_comparison_without_innovation')
report={'at_utc':now,'conclusion':'Minimal isolated E coverage candidate is reviewable and statically mergeable with the separate IF candidate; no production adoption or classifier execution performed.','candidate':str(V),'actual_finite_control_round_N':2,'finite_control_limit':2,'model_calls':0,'production_classifier_runs':0,'old_expectations_changed':False,'current_original_fixture':{'text':'应比较药物与现有治疗的完全应答率。','contexts':[],'fixed_expected':{'E':1,'I':0},'old_values':target['old_values'],'new_values':target['new_values'],'actual_E_decision':target['candidate']['decisions']['E']},'manual':bind(manual),'manual_grounds':{'common_substantive_threshold':'当前句段实质讨论、规定、评价、比较、要求证据，或实际安排直接对应某维内容的措施，均可表示关注','E_definition':'药物防治效果、健康收益、临床获益及支持这些判断的证据。','E_include':'疗效、疾病控制、生存、健康相关生命质量、治疗优势、对应的药效研究/效果比较及证据要求','negative_or_uncertain_also_included':True,'not_new_dimension_definition':True},'attempts':[{'attempt':1,'actual_summary':bind(A/'execution01/summary.json'),'targeted_case_N':22,'targeted_passed_N':22,'negative_N':12,'negative_E1_N':0,'original189_E_changed_N':1,'subsequently_static_found_boundary':'Comma-separated background drug object could donate to a later non-drug comparison; first results unchanged.'},{'attempt':2,'actual_summary':bind(A/'execution02/summary.json'),'count_correction':bind(A/'summary-count-correction.json'),'targeted_case_N':24,'targeted_passed_N':24,'negative_N':13,'negative_E1_N':0,'original189_E_changed_N':1,'change_from_attempt1':'Only the added producer comma delimiter; original22 fixed controls copied exact and two new necessary clinical-object relation controls fixed before second edit.'}],'original189':s2['original189'],'all_original_hard_failures_preserved':s2['all_failures'],'invariance':{'all_original_v9_AST_restored_after_removing_only_E_additions':True,'source_packet_receipts_evidence_byte_identical':True,'S_Ec_I_F_full_decision_mismatch_N':0,'gate_outside_all5_full_decision_mismatch_N':0,'legacy_relation_source_logs_mismatch_N':0,'technical_error_N':0,'filesystem_classifier_access_attempt_N':0,'evidence_validate_decisions_passed':True,'proof':bind(A/'static02/ast-isolation-proof.json')},'added_nodes_and_consumption':components['files'],'impact':{'selector':bind(V/'select_static_impact.py'),'gate_pattern':proof['raw_gate']['pattern'],'interface':'matches(current_original_raw_text)','contains_all_possible_new_E_paths':True,'include_old_E1_and_old_E0_and_null':True,'do_not_filter_by_ID_or_old_prediction_or_current_machine_disagreement':True,'parent_should_union_with_independent_IF_gate_before_one_actual_partial_run':True,'production_rows_read_or_selected_N':0,'actual_full_affected_N':None,'gate_is_candidate_superset_not_semantic_acceptance':True},'limitations':['The new producer is deliberately current explicit drug-object and endpoint focused; it does not fill elliptical, title-only or parent-dependent endpoint expressions. Existing v9 paths remain intact.','Comma splitting conservatively refuses cross-comma object donation; old paths remain available. The control set does not prove every possible complex clause correct.','Six exact endpoint forms and whitespace variants are operational coverage, not a claim that all response/remission words or all clinical endpoints count E.','All old IF hard failures and pending controls remain recorded; this is not a correction to human labels, a human review, an accuracy estimate, a kappa acceptance claim, or a production result.','Combined IF+E assembly and final union bindings still require ROOT validation before actual partial execution.']} 
save(A/'report.json',report)
md=f'''# 完全应答率 E 最小覆盖候选

候选可供 ROOT 与独立 I/F 修正组合审查。本轮只做了两次有限控制，没有调用模型、没有分类或选取全量/局部生产记录，也没有改手册、原期待、人工参照、native 首答或既有版本。最终采用附件是 `static02/v9-to-E.diff` 与 `static02/e-patch-components.json`；根目录同名静态附件属于保留的第一版。

## 同版依据与原失败

原固定 `clinical_comparison_without_innovation` 当前完整句为“应比较药物与现有治疗的完全应答率。”，`contexts=[]`，原期待 E=1、I=0 一直保留。药物对象、比较动作、现有治疗基准和临床反应指标均由当前原文直接表达。共同手册§一允许当前实质比较及证据要求，也允许否定、不确定和尚未实现要求；§四定义“药物防治效果、健康收益、临床获益及支持这些判断的证据。”，纳入“对应的药效研究/效果比较及证据要求”。因此 E=1 表示效果议题在场，不证明该药有效、优于对照或有创新属性。

C 的同版独立审查已说明，v8/v9 沿用的 `SE_EFFECT` 没覆盖该确切指标；原 fixture E=1 依据手册成立。手册 SHA256 `{bind(manual)['sha256']}`。FDA 2018 年原指导的 III.B.2/III.B.3 把客观/完全反应作为抗肿瘤药评价终点，同时区分反应活动与已证实临床获益；这里仅用作术语旁证，不替代同版手册，不写回生产材料。[FDA 原指导](https://www.fda.gov/media/71195/download)。部分/完全/客观“应答率”“缓解率”六个确切指标形式是本候选操作化范围，不能从“应答”一词机械扩散 E。

## 代码隔离

仅增加 `E_OUTCOME_ENTRY`、纯当前原文 `_e_outcome_gate`、`RelationView._e_current_outcome_relationships` 和 E-only `_e_current_outcome_consume`。两处原流程入口分别在 constructor 原末尾、`judge` 原 I/F consumer 后与 `finish` 前；producer/consumer 第一条语句都验证 raw current-text gate。producer 只写私有 `e_current_outcome_relations`，不进入旧 relation graph、不加材料请求；consumer 只调用 `acc.add('E', ...)`。

删除上述新增节点及两次受控调用后，relations/dimensions **完整剩余 AST 与冻结 v9 相同**；source_packet/source_receipts/evidence 三模块字节相同。旧 helper、GAPS、SE_EFFECT 与所有 S/Ec/I/F 路径未改。静态证明与逐字补丁在 `static02/`，它们给出每个新增节点和消费位置，便于机械移植到 C 的 I/F 版本，而不拿完整 v9 文件覆盖其改动。

## 两次真实有限控制

| 记录 | 预先固定控制 | 真实结果 | 保留项 |
| --- | --- | --- | --- |
| execution01 | 原189 + 新22 | 新22全部符合；12个负例无 E=1；原189只有目标 E 从0变1 | 原8个I/F未满足、15个pending完整保留 |
| execution02（最终） | 原189 + 保持原22 + 新2 | 新24全部符合；13个负例无 E=1；原189仍只有目标 E 从0变1 | 原8个I/F未满足、15个pending完整保留 |

原目标实际五维从 `S0/E0/Ec0/I0/F0` 到 `S0/E1/Ec0/I0/F0`。两轮中其他四维完整 decision、gate 外完整五维 decision、旧 relation/source 日志差异均0，技术错误0，原文逐字证据经原 evidence validator 验证。原189基线使用已封存真实 v9 attempt08 的 `candidate` 输出，没有重跑旧189，也没有把其 v8 `baseline` 当成 v9。

第一轮之后，静态发现“药物仅用于界定研究对象，应比较手术与放疗的完全应答率。”可能发生逗号前背景药物向后句捐赠对象。第二次编辑前固定该 E0 负例及“应比较该药与手术治疗的完全缓解率。”E1 正例，只将**新增 producer** 切段从句号/分号收紧到也包括逗号。第一轮输出与期待原样保存，最终两条均符合。此收紧是当前对象关系修正，与通过数量无关；没有进行第三轮。

第二轮 summary 的 `targeted24.case_N` 仍序列化为22，是复制报告脚本的硬编码遗漏；实际 results 有24个新控制、213总行、24通过。原 summary/seal 不改，`summary-count-correction.json` 按实际行数机械补正该单一元数据字段，未重分类。所有原失败如下：00093/F、00381/I、00649/I、01382/I、01402/I、01731/I、01743/I、01757/I。它们不属于本 E 修正范围。

## 足够的局部影响门槛

ROOT 可调用 `select_static_impact.py` 的 `matches(current_original_raw_text)`；CLI 为 `python3 select_static_impact.py --source-jsonl ORIGINAL_CURRENT_TEXT_ROWS --output NEW_GATE_MANIFEST`。源行必须实际暴露 `text` 或 `source_record.text`，缺失就拒绝，不能以语境或预测代替原文。本轮未读取/选取4481当前原文，实际命中 N 未知。

该 raw gate 与两模块入口字面相同，筛完整记录，不过滤旧 E=0/null，**包含已 E=1** 的潜在证据变化。gate 外新 producer/consumer 完全跳过，原 v9 AST 全部保留，故 gate 是可能受影响路径的充分超集，绝非自动 E=1。ROOT 应与 I/F 独立 gate 取并集、绑定封存原始材料后一次实际重算，不按目标 ID、旧预测或当前分歧筛选。

## 实际范围与未解项

分类器实际只接触原189控制内98个唯一已暴露 packet binding 和预先固定合成控制；运行期间文件访问被阻断，未打开新 human200 或 remaining 正文。输入、输出与两轮 code-snapshot 均绑定哈希。当前自足药物对象和确切终点是新分支范围；省略主语、只在标题/父项出现的指标不由本分支补足，跨逗号关联保守不新增，其他既有路径保持。有限正反例不证明所有复杂语句正确，也不是人工核定、准确率或 κ 验收。组合版本的静态接线、影响并集和生产实际差异仍由 ROOT 核验。
'''
with (A/'report.md').open('x',encoding='utf8') as f:f.write(md)
candidate={'at_utc':now,'status':'sealed_candidate_not_adopted','base_module_bindings':pre['base_modules'],'files':[bind(p) for p in sorted(V.rglob('*')) if p.is_file()],'finite_execution_rounds':2,'actual_control_results':bind(A/'execution02/results.json'),'final_patch':bind(A/'static02/v9-to-E.diff'),'patch_components':bind(A/'static02/e-patch-components.json'),'static_proof':bind(A/'static02/ast-isolation-proof.json'),'no_models_or_production_classification':True,'self_excluded':True}
save(V/'candidate-freeze.json',candidate)
save(A/'output-seal.json',{'at_utc':now,'files':[bind(p) for p in sorted(A.rglob('*')) if p.is_file()],'candidate_freeze':bind(V/'candidate-freeze.json'),'self_excluded':True,'original_inputs_and_preserved_execution_outputs_hash_exact':True})
print(json.dumps({'report':bind(A/'report.md'),'output_seal':bind(A/'output-seal.json'),'candidate_freeze':bind(V/'candidate-freeze.json'),'final_patch':bind(A/'static02/v9-to-E.diff'),'targeted24_passed':True,'original189_only_E_target_change':True,'classifier_rounds':2,'production_runs':0},ensure_ascii=False,indent=2))
