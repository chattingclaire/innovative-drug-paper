from pathlib import Path
import json,hashlib,datetime,ast,sys,importlib.util
sys.dont_write_bytecode=True
A=Path(__file__).resolve().parent;R=A.parents[1];V=R/'06-coding/rule-five-dimension-joint-root/versions/joint-v10-generic-relationship-sol';OLD=V.parent/'joint-v9-generic-relationship-sol';NAMES=['evidence','source_packet','source_receipts','relations','dimensions'];D=R/'08-audits/v9-generic-relationship-repair-design-sol/revision02-bidirectional-before-implementation'
def bind(p):
 p=p.resolve();b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def save(p,x):
 with p.open('x') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
newspecs=[bind(V/(n+'.py')) for n in NAMES];oldspecs=[bind(OLD/(n+'.py')) for n in NAMES]
summary=json.loads((A/'attempt02-controls/summary.json').read_bytes());results=json.loads((A/'attempt02-controls/results.json').read_bytes())
assert summary['case_N']==201 and summary['hard_assertion_case_N']==186 and summary['hard_passed_N']==184 and summary['hard_failed_N']==2 and summary['pending_N']==15
for n in NAMES:assert (V/(n+'.py')).read_bytes()==(A/'attempt02-controls/code-snapshot'/(n+'.py')).read_bytes()
for key in ['SEEc_complete_decision_mismatch','outside_gate_complete_decision_mismatch','old_relation_mismatch','source_state_mismatch','unproved_v10_positive','filesystem_access_attempts']:assert not summary[key]
initial=json.loads((A/'design-freeze-before-edit.json').read_bytes())
for spec in initial['inputs']:assert bind(Path(spec['path']))==spec
# Audit source reading: controls 130 dimensions on 98 already exposed packets,
# seven targeted diagnostic originals, manual and bounded source/code artifacts.
packet_specs={c['packet_binding']['path']:c['packet_binding'] for c in results if c.get('packet_binding')}
for spec in packet_specs.values():assert bind(Path(spec['path']))==spec
controls=[D/'real-controls-fixed-before-edit.json',D/'synthetic-controls-fixed-before-edit.json']+[OLD/p for p in ['supplemental-controls-before-attempt02.json','supplemental-controls-b-before-attempt02.json','supplemental-controls-before-attempt04.json','supplemental-controls-before-attempt06.json']]+[A/'new-controls-fixed-before-edit.json',A/'additional-counter-controls-fixed-before-attempt02.json']
source_files=[R/'03-manual/full4481-common-release-20261010-root/manual.txt',R/'08-audits/v9-remaining8-diagnostic-sol/diagnosis8.json',R/'08-audits/v9-remaining8-diagnostic-sol/evidence8.json',A/'independent-E-control-review/output-seal.json']
save(A/'actual-opened-input-bindings.json',{'packet_N':len(packet_specs),'actual_packets':[packet_specs[k] for k in sorted(packet_specs)],'controls':[bind(p) for p in controls],'other_inputs':[bind(p) for p in source_files],'identity_manifest_read_scope':'metadata keys and first record binding only; no semantic body','supplemental_01402_not_opened_or_consumed_in_v10':True,'no_unselected_sibling_original_body_or_human200_or_remaining':True,'selected_130_read_authorization_inherited':True,'no_classifier_or_LLM_population_run':True})
manifest=R/'08-audits/v9-static-selection-manifest-root/full4481-identity-manifest.json';baseline=R/'06-coding/rule-full4481-v9-delta-merged-root/predictions.jsonl';baseline_seal=R/'06-coding/rule-full4481-v9-delta-merged-root/seal.json'
contract={'schema_version':'v10_static_impact_contract_candidate_1','manifest_binding':bind(manifest),'baseline_prediction_binding':bind(baseline),'baseline_seal_binding':bind(baseline_seal),'old_modules':oldspecs,'candidate_modules':newspecs,'selector_binding':bind(V/'select_static_impact.py'),'static_gate_binding':bind(V/'static_gate.py'),'global_baseline_error':False,'manual_static_audit':{'approved':False,'record_local_only':True,'new_relation_not_consumed_by_old_units':True,'only_IF_decision_or_explicit_IF_request_mutations':True,'same_packets_adapter_evidence_wrapper':True,'actual_v9_baseline_compatible_verified':False,'identity':'author proof only; ROOT/A must independently freeze caller/evidence-wrapper and actual-v9 baseline compatibility before bounded reuse','proof_artifact_bindings':[bind(A/'ast-isolation-proof.json'),bind(A/'side-effect-contract.md')]},'selection_feature_contract':'exact current normalized pure compound gate dominates all new effects; all gate-in 0/1/null records selected; IDs/resource IDs/hashes only mechanical identity binding, metadata departments, gold/native/reference and values never semantic selection features','selected_recompute_scope':'whole record, every old/new unit and complete positive/negative/null evidence and anchor chain, not merely 7 examples or native-positive cases','fallback':'all4481 if any input/module/caller/proof/baseline compatibility prerequisite fails; author did not execute full population static selection','output_schema':{'status':'static_selection_only_no_classifier_execution','record_N':'4481','selected_N':'integer','reusable_N':'integer','affected_records':'[{id, packet_binding, gate_matched, reasons, recompute_scope}]','selected_record_ids':'ordered list','reusable_record_ids':'ordered list','full_fallback_reasons':'list','contract_binding':'exact','manifest_binding':'exact','baseline_prediction_binding':'exact','selector_binding':'exact'},'execute_after_independent_approval':['python3',str(V/'select_static_impact.py'),'--contract','PATH_TO_ROOT_APPROVED_NEW_CONTRACT']}
save(A/'selector-contract.json',contract)
freeze={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate_directory':str(V),'five_modules':newspecs,'evidence_source_packet_source_receipts_byte_same_v9':True,'final_actual_controls_directory':str(A/'attempt02-controls'),'final_five_modules_identical_last_actual_control_snapshot':True,'fixed_original_189_control_N':189,'new_necessary_control_N':12,'total_control_N':201,'hard_assertion_N':186,'hard_passed_N':184,'hard_failed_N':2,'pending_N':15,'actual_local_candidate_control_executions':2,'further_control_execution_needed_for_hash_binding':False,'remaining_hard_failures':bind(A/'remaining-hard-failures.json'),'classifier_or_LLM_population_run':False,'01402_material_change_not_included':True,'manual_reference_native_prompts_predictions_old_candidate_unchanged':True,'candidate_frozen':True,'formal_semantic_acceptance':False,'selector_contract':bind(A/'selector-contract.json'),'static_gate':bind(V/'static_gate.py'),'limitations':'exposed development controls are not independent gold or final accuracy; pending remains unadjudicated; full actual affected population and ROOT/A approval remain'}
save(A/'candidate-freeze.json',freeze)
# Count original cases distinctly, never pending as a hard pass.
original=results[:189];assert len(original)==189
save(A/'complete-controls-report.json',{'final_summary':summary,'original189':{'N':189,'hard_N':sum(c['hard_assertion'] for c in original),'hard_passed_N':sum(c['hard_assertion']and c['passed'] for c in original),'hard_failed_N':sum(c['hard_assertion']and not c['passed']for c in original),'pending_N':sum(not c['hard_assertion'] for c in original)},'new12':{'N':12,'hard_N':12,'hard_passed_N':12,'hard_failed_N':0},'all_15_pending':[{'name':c['name'],'pending_dimensions':c.get('pending_dimensions'),'expected':c['expected'],'new_values':c['new_values'],'no_forced_new_positive':c.get('restricted_mother_no_new_positive')} for c in results if not c['hard_assertion']],'all_attempt_failure_history':bind(A/'all-attempts-report.json'),'all_actual_results':bind(A/'attempt02-controls/results.json'),'final_five_modules':newspecs,'strict_separate_pending':True,'gold_accuracy_or_machine_threshold_claim':False})
report='''本轮 v10 I/F 候选已冻结，当前五模块逐字等于第二次完整控制实际快照。仅新增关系/维度中隔离的 I/F 路径；evidence、source_packet、source_receipts 字节与 v9 相同。原 v9、共同手册、原 packets、所有原期待和人工/native 值未改；没有模型调用、全4481分类或实际全体静态选取。

控制实际执行两次，均完整保留。最终共 201 项（原189 + 必要新反例12），其中186有硬断言：184通过、2失败；15 pending 单列。原189为174硬断言（172通过、2失败）与15 pending；新12全部通过。pending 的 expected 仍为空，不按通过计算。首轮01731失败完整保留，原因是实际“完成审评审批”后尚有并列通知内容，原字面句尾条件未取出该操作范围；第二轮只修正实际操作引文的句尾范围并补独立取数受益对象排除，无原期待改变。

| 已曝光开发项 | 新闭合关系 | 开发当前结果 |
|---|---|---|
|00093/F|实际急需境外已上市境内未上市药品的优先申请明确按完整当前成员引用；不借优先程序的其他需要/优势分支|v9=0，candidate=1|
|00381/I|具体工具选择及自行工具接受的监管沟通；同名附件角色、页区间、段落序及参考边界限定创新临床对象|v9=0，candidate=1|
|00649/I|当前所建支持创新机制实际按同段药品创新价值量化分级；属于实质创新价值评价，无需笼统支付支持推断|v9=0，candidate=1|
|01382/I|当前经实质条件审核后执行数据保护；只消费原包完整创新保护条款及例外，其他独立取数对象不能继承原创新持有人待遇|v9=0，candidate=1|
|01731/I|当前具备条件区域实际开展试点，完整方案限定创新项目及排除条件，且真实确认后审评便利存在|v9=0，candidate=1|
|01743/I|当前项目申请前实际可用监管沟通，项目申请组成部分绑定合格申请人；未引用纳入后30日替代申请前服务|v9=0，candidate=1|
|01757/I|当前机构项目立项、方案审核和风险评估技术培训，有限同方案试点机构服务创新项目；非试点机构分支不推断创新身份|v9=0，candidate=1|

这七项的逐字当前锚、原文引文、有限角色凭据和原包绑定保存在 seven-current-relationship-evidence.json。结果是开发关系证据闭合，不把固定期待视为金标准，不按机器阈值或一致率筛改。

保留两项硬失败。01402/I=0（原期待1），本轮原投影中仍缺所需对象定义，独立补材未进入代码或 packet；其材料变更须单独批准路径。clinical_comparison_without_innovation：E=0、I=0（原期待E=1/I=0），原句“应比较药物与现有治疗的完全应答率。”已由共同手册逐字支持效果比较议题；v8/v9遗留E词义覆盖不足，本轮I/F不修改E，也不改期待。独立E审查封存于 independent-E-control-review。

错完整成员、无需要只有优势、错主体/药型、纯填表、宗旨印发、只向非试点角色服务、另一机制创新标准、参考文献后工具条款、其他独立取数者等必要反例保留为12项固定控制。S/E/Ec 完整决策、gate-out五维完整决策、旧全部关系、material/source requests/events 均无差异，新反例无不证实新增v10关系，classifier零文件读取尝试。

影响契约以纯当前文本 compound gate 提名，已独立导出 static_gate.py；构造器、新 builder 首句、新消费者首句均由同一入口支配。入口内全部旧0/1/null都必须重算完整记录、旧新全部单位及完整依据链。入口外移除新定义/常量/import/两个guard后精确恢复v9 AST，旧共享字段及消费者不读新kind；完整23函数调用树、副作用与未放宽旧GAPS证明随附。作者未执行全4481 selector；selector-contract.json 的独立 approval=false，需要 ROOT/A 审核生产caller、真实v9兼容baseline及哈希后，在另封契约中允许复用；任何证明不成立保守全量fallback。
'''
(A/'implementation-report.md').write_text(report)
# Exact candidate-only seal, included in the final overall mandatory-members seal.
module_seal={'files':[bind(p) for p in sorted(V.rglob('*')) if p.is_file()],'candidate_freeze_binding':bind(A/'candidate-freeze.json'),'self_excluded':True,'frozen_candidate_not_semantic_acceptance':True}
save(V/'output-seal.json',module_seal)
required=[V/(n+'.py') for n in NAMES]+[V/'select_static_impact.py',V/'static_gate.py',V/'run_finite_controls.py',V/'output-seal.json']+[A/p for p in ['candidate-freeze.json','selector-contract.json','ast-isolation-proof.json','side-effect-contract.md','implementation-report.md','complete-controls-report.json','remaining-hard-failures.json','seven-current-relationship-evidence.json','actual-opened-input-bindings.json','all-attempts-report.json','design-freeze-before-edit.json','new-controls-fixed-before-edit.json','additional-counter-controls-fixed-before-attempt02.json','attempt01-controls/output-seal.json','attempt02-controls/output-seal.json','independent-E-control-review/output-seal.json']]
allpaths=sorted({p.resolve() for p in A.rglob('*') if p.is_file()}|{p.resolve() for p in V.rglob('*') if p.is_file()})
seal={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'schema_version':'v10_final_candidate_total_seal_1','mandatory_members':[str(p.resolve()) for p in required],'files':[bind(p) for p in allpaths],'self_excluded':True,'all_original_actual_attempts_and_failures_retained':True,'candidate_frozen_not_semantic_acceptance':True}
save(A/'output-seal.json',seal)
for item in seal['files']:assert bind(Path(item['path']))==item
assert set(seal['mandatory_members'])<=set(item['path'] for item in seal['files'])
print(json.dumps({'final_total_seal':bind(A/'output-seal.json'),'candidate_freeze':bind(A/'candidate-freeze.json'),'candidate_module_hashes':{Path(x['path']).name:x['sha256'] for x in newspecs},'files_N':len(seal['files']),'mandatory_N':len(required),'actual_runs':2,'hard_passed':184,'hard_failed':2,'pending':15},ensure_ascii=False,indent=2))
