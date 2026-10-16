from pathlib import Path
import json, hashlib
from datetime import datetime, timezone
B=Path('/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010')
D=B/'08-audits/current-freeze-stability-readiness-20261012-sol'
O=D/'supplement-two-design-options'
O.mkdir(exist_ok=False)
def now(): return datetime.now(timezone.utc).isoformat()
def binding(p):
 p=Path(p); raw=p.read_bytes(); return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def save(name,obj):
 raw=(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode() if not isinstance(obj,str) else obj.encode()
 with (O/name).open('xb') as f:f.write(raw)
 return binding(O/name)
original_seal=json.loads((D/'seal.json').read_bytes())
original_checks=[{'expected':f,'actual':binding(f['path']),'exact':binding(f['path'])==f} for f in original_seal['files']]
assert all(x['exact'] for x in original_checks)
rels=['完整Goal指令.md','06-coding/llm-protocol-sol/稳定性与运行封存预设.md','02-methods/prospective-statistical-contract-v2/validation-design-v2.json','03-manual/full4481-common-release-20261010-root/common-execution-protocol.txt','06-coding/current-freeze-stability-binding-plan-sol/plan.json','06-coding/current-freeze-stability-binding-plan-sol/README.md','06-coding/current-freeze-stability800-v1-root/run-manifest.json','06-coding/current-freeze-stability800-v1-root/actor-instructions.txt','06-coding/current-freeze-stability-execution-root/run_one.py','06-coding/native-full4481-v1-sol/run-manifest.json']
inputs=[binding(B/r) for r in rels]
for name in ['seal.json','report.json','report.md','input-bindings.json','observed-real-attempt-inventory.json','proposed-original-whole-batch-scope.json','condition-request-binding-comparison.json','minimal-next-scope-and-transport-proposal.json']:
 inputs.append(binding(D/name))
plan=json.loads((B/'06-coding/current-freeze-stability-binding-plan-sol/plan.json').read_bytes())
manifest=json.loads((B/'06-coding/current-freeze-stability800-v1-root/run-manifest.json').read_bytes())
full=json.loads((B/'06-coding/native-full4481-v1-sol/run-manifest.json').read_bytes())
closure=json.loads((D/'proposed-original-whole-batch-scope.json').read_bytes())
preset=(B/'06-coding/llm-protocol-sol/稳定性与运行封存预设.md').read_text()
goal=(B/'完整Goal指令.md').read_text()
protocol=(B/'03-manual/full4481-common-release-20261010-root/common-execution-protocol.txt').read_text()
validation=json.loads((B/'02-methods/prospective-statistical-contract-v2/validation-design-v2.json').read_bytes())
repeat_stage=next(x for x in validation['required_metric_matrix'] if x['stage']=='重复稳定性')
quotes=[
 {'source':str(B/rels[0]),'location':'步骤5','quote':'依成熟方法检查输出稳定性及下游注意力结构的稳健性，其他诊断指标按适用性预先确定，不能机械赋同一阈值。','interpretation':'Goal要求实施合适稳定性诊断，没有在此要求所有4481或P原批次严格复现。'},
 {'source':str(B/rels[0]),'location':'步骤6','quote':'将分类效度、输出重复性与聚合结果稳健性分别解释。','interpretation':'诊断可单列用途，不能由重复性推正确性或完整Goal验收。'},
 {'source':str(B/rels[1]),'location':'§3','quote':'诊断使用事前选定的同一来源ID样本。','interpretation':'允许事前样本范围，不预设必须重复所有生产记录。'},
 {'source':str(B/rels[1]),'location':'§3 M12','quote':'M12设置3次相互独立的主提示诊断运行，记为R1、R2、R3。三次使用完全相同的主提示、来源包、请求字节、顺序、批次及实际可控制配置；会话上下文相互独立。R1、R2、R3均为单独诊断，不是替换生产结果的候选池。','interpretation':'相同批次要求约束R三条件相互之间；这段没有要求R批次等同P。'},
 {'source':str(B/rels[1]),'location':'§3末段','quote':'所有诊断原始响应、技术失败、语义null和重试分别封存，隔离于生产首次有效选择。重复或微扰输出不得补齐生产失败、替换生产null或用于挑选较好标签。','interpretation':'P及其技术恢复与R/W/H身份分开。'},
 {'source':str(B/rels[1]),'location':'§1','quote':'每个记录、重复和微扰均使用独立上下文，只含同一冻结说明及该记录来源包，不包含其他记录的回答、旧标签、讨论、诊断结果或前次失败反馈。','interpretation':'旧最小协议最初按记录写；现共同协议改为每批新上下文，必须披露该方法变体，不能声称逐条独立上下文。'},
 {'source':str(B/rels[1]),'location':'§3抽样','quote':'样本选择只依据事前规定的来源特征，不使用旧编码答案或本轮结果。','interpretation':'旧800层名含历史机器I/F辅助分层信息，不能把它说成纯来源特征样本；当前复用依据是已封存抽样和后续事前诊断计划，不能无条件宣称与这条旧表述字面一致。'},
 {'source':str(B/rels[3]),'location':'LLM执行段','quote':'批次合计一次主运行，各批不等于独立重复，不声称逐条新上下文。','interpretation':'现共同协议明确实际上下文单位是batch。'},
 {'source':str(B/rels[3]),'location':'末段','quote':'正式机器参照检验、预定重复/稳健性及结论分析依既定统计契约执行','interpretation':'生产与稳定性分别实施。'},
 {'source':str(B/rels[2]),'location':'required_metric_matrix/stage=重复稳定性/required/0','quote':repeat_stage['required'][0],'interpretation':'“主次序第1次”需登记解释：对本固定诊断顺序指R1第一诊断结果，生产P仍是另一个不被替换的主运行；该条未明确写P原批成员必须用于R。'},
]
texts={str(B/rels[0]):goal,str(B/rels[1]):preset,str(B/rels[3]):protocol,str(B/rels[2]):json.dumps(validation,ensure_ascii=False)}
for q in quotes: assert q['quote'] in texts[q['source']],q
# New snapshot is inventory only, without loading any policy packet or responses.
nonempty=[]
for row in manifest['routes']:
 p=Path(row['output_directory']) if 'output_directory' in row else Path(row['output_slot'])
 if p.exists() and any(p.iterdir()):nonempty.append(str(p))
assert not nonempty,nonempty
assert plan['primary_P']['may_be_R1'] is False
assert closure['original_whole_batch_N']==351 and closure['actual_carried_record_N']==3759
base_b=manifest['batches'][0]
# These are instructions/assignment metadata, not packet/source body.
for p in [base_b['assignments']['raw']['path'],base_b['requests']['base']['path'],base_b['requests']['H']['path']]:inputs.append(binding(p))
options={
 'P_whole_batch_context_replication':{'target_N':800,'actual_carried_record_N':3759,'original_whole_batch_N':351,'companions_retained_not_scored_N':2959,'M12_fresh_first_batch_dispatches':1053,'M13_fresh_first_batch_dispatches':702,'all_five_fresh_first_batch_dispatches':1755,'minimum_if_all_planned_terminal_and_no_retries_or_blocks':True,'necessary_for_claim':'Exact reproduction of the original P co-batch membership/order/context setting for the800 targets.','not_required_by_explicit_preset':'No reviewed preset text explicitly requiresR batch partition to equalP.','new_preparation_required':True,'metadata_proposal':str(D/'proposed-original-whole-batch-scope.json'),'executed':False},
 'fixed_87_batch_diagnostic_partition':{'target_N':800,'actual_carried_record_N':800,'fixed_diagnostic_batch_N':87,'original_whole_batch_exact_coincidences_N':13,'M12_fresh_first_batch_dispatches':261,'M13_fresh_first_batch_dispatches':174,'all_five_fresh_first_batch_dispatches':435,'max_technical_attempt_slots':1305,'R1':'new first main-prompt diagnostic execution','R2':'new complete independent repeat1 ofR1 diagnostic setting','R3':'new complete independent repeat2 ofR1 diagnostic setting','P_used_as_any_R':False,'W':'one separately new presentation/JSON-indent perturbation compared withR1','H':'one separately new neutral-header perturbation compared withR1','use':'Can implement theGoal sample repeat-stability diagnostic, conditional on this prospectively fixed87-batch setting and successful real execution/terminal reporting.','not_supported':['Exact originalP whole-batch reproduction','Record-level new-context independence','Classification truth/accuracy','New independent human coding','Completion ofallGoal requirements'],'preparation':str(B/'06-coding/current-freeze-stability800-v1-root'),'old_executor':str(B/'06-coding/current-freeze-stability-execution-root'),'need_new_transport_sidecar_before_GO':True,'executed':False}}
transport={
 'status':'method_and_preparation_recommendation_only_not_authorization_or_implemented_code',
 'preserve_existing_inputs':'Do not change old800 plan/manifest/assignments/prompt/actor files. Copy only transport execution instructions into a new separately sealed namespace and bind originals. Manual/commonexecutionprompt/protocol/packet semantics/87 groups/sample/weights remain frozen.',
 'common_visible_R_request':'One common readonly batch directory/assignment/schema/input instruction set perdiagnosticbatch. R1/R2/R3 and technical retries receive identical frozen user-stdin request bytes. Condition/attempt/output label/thread/time/selected slot remain ROOT-only external ledger data, not appended userprompt and not exposed as prior answers.',
 'old_runner_not_ready_unchanged':'run_one.py line40 appends condition/attempt/logicaldispatchlabel/uniqueoutputslot metadata tostdin. Theoldactor/request also require actor to match that label torouting table. Simply deleting theappend will leave an undefined output route; a stable, same-acrossR mechanical delivery overlay must supersede label-based output routing beforedispatch.',
 'preferred_shared_readonly_CWD_capture_interface':{
  'prospective_argv_shape':'codex exec [fixed CLI/profile flags] -C <same readonly batch directory> --output-last-message <ROOT-only unique capture path> - ; stdin=<same frozen common request bytes>',
  'visible_delivery_rule':'A same-acrossR transport instruction asks actor to submit exactly one complete structuredfirst JSON in its final message, with the unchanged strict first schema/read_manifest/evidence. ROOT retains the captured final-message UTF8 bytes without canonicalization or reserialization as the originalfirst artifact, then mechanically writes separate ROOT report/seal/receipt from real events/process/output hashes.',
  'necessary_identity_disclosure':'This changes delivery from actor-created slot/first/report/seal files to ROOT-captured original first message plus ROOT transport封存. Do not call ROOT seal an actor-created seal or captured message provider network wire. Receiver must explicitly bind capture bytes and issuer, not quietly reuse actor-file provenance claims. First schema/concepts/evidence/null/wholebatch earliest valid selection remain unchanged.',
  'request_and_output_checks':'Freeze emitted request length/SHA; R1/R2/R3 exactbytes checked beforelaunch. Only complete unadorned JSON final-message is accepted; no partial extraction from prose or repair. Capture destination arguments are external address metadata; rawargv/logs retained. Provider hidden wrapper/full wire/context/servingmodel remain unknown.'},
 'if_actor_written_three_files_are_retained':'Use a same-acrossR mechanical relative-output instruction and new isolated output CWD for eachattempt, with identical research inputs/userstdin. CWD/path may be visible through CLI environment; explicitly disclose this as nonsemantic transport address variation, not all model context/wire bytes identical. Do not claim same readonly -C ifactually launching inuniqueoutputslot.',
 'W_and_H_identity':'W has only the frozen indent2 packet presentation variant with decoded strings/objectvalues/arrays/memberorder preserved; H only the prescribed first-line synonym. No R condition number in model instructions. Keep W/H separate fromR; W/H retries remain technicalattemptswithin thatcondition.',
 'reception':'Use verified Python3.14/jsonschema and sealed CLI0.162.1. Adapt production strictschema/pointerquote/read checks plus v4 explicit sealflags and real nonempty allowedinput binding. Require actual completeprocess/event receipt. Do not demand optional first.attempt_number or convert legal null intoretry.',
 'capacity_and_timing':'Wait for genuinely terminal primary/recovery controller and children beforeGO. Oldprimary sharedlock doesnot coverrecoveryv4. Fresh controller max3 global actual processes; no semanticfeedback/history/resume/fork. Never dispatch samecondition/batch twice or modify current runningrecovery.',
 'terminal_statistics':'All fivecondition batch terminals retained before fixedpairs/triple metrics. Each condition/batch earliest entire technicalvalid response including legal null; retriesmax3 not independentR. Use fixed5pairs and jointbinary denominators, null/failure/notcalled separately; unchangedweights and math. No new passline or CI gate.'}
report={'at_utc':now(),'status':'supplement_to_immutable_readiness_audit_no_actual_execution','completed_actual_R1_R2_R3':0,'completed_extra_R2_R3':0,'completed_W_H':0,'recommendation':'Prefer existingfixed800/87 diagnosticpartition forGoal sample repeat-stability requirement, with prospectively sealed literal commonRstdin and externalrouting repair; strict351batch closure onlyif claiming originalPco-batch-context replication.','explicit_P_partition_requirement_found':False,'basis_scope':'Reviewed completeGoal text, fullLLM stabilitypreset, repetitionmetricmatrix, currentcommonprotocol and sealed800bindingplan. This is interpretation ofthese localcontracts, not externalmethod research or allGoal acceptance.','contract_wording_to_disclose':['Initial perrecord independentcontext changed in currentcommonprotocol toperbatch context','Historical machineI/F stratumauxiliary information in reused800draw isnot pure sourcefeature sampling; no newRoutputs were used tochoose this frozen sample','The prospective statistical matrix first main result wording is registered asdiagnosticR1; P unchanged andseparate','Oldfullsent userprompt routevariation is repaired prospectively in newtransport; oldbytes preserved'],'options':options,'source_quotes_and_interpretation':quotes,'transport_preparation_interface':transport,'source_policy_body_reads_by_this_supplement':0,'human200_workbook_or_answer_reads':0,'model_or_classifier_calls':0,'old_inputs_or_progress_modified':False,'current_rule_byte_reproduction':'Separate unresolved currentalgorithm reproducibility question; legacy v2 rule repeat recommendation isnot currentversion evidence, no rule rerun startedhere.','all_goal_complete':False,'independent_serving_model_verified':False}
save('report.json',report)
md='''固定 **87 个诊断批**的新 R1/R2/R3，可以实施完整Goal中的**抽样重复稳定性诊断**。这项判断依据已封存的未来诊断协议，不是把生产 P 或技术重试追认为重复；目前真实 R1/R2/R3、W/H 均为 **0**。原报告及其封印保持不变。

《稳定性与运行封存预设》§3明确：“诊断使用事前选定的同一来源ID样本”，且“R1、R2、R3均为单独诊断，不是替换生产结果的候选池”。同节的相同请求、顺序和批次要求约束三次R之间，未明确要求其批次等同生产P。完整Goal步骤5要求检查输出稳定性，步骤6要求将分类效度、输出重复性与聚合稳健性分别解释；没有要求为此重复4481全部材料。统计矩阵“冻结LLM主次序第1次为主结果，另2次完整独立重复”的 wording 应在本诊断发布中登记为R1第一诊断结果，P继续单独保留，不能由此替换P或挑最好R。

| 方案 | 每次实际读取 | M12三次新R首次批执行 | M13新W/H首次批执行 | 全部五条件首次批执行 | 能支持的范围 |
|---|---:|---:|---:|---:|---|
| 原P完整批语境复现 | 351原批、3759条 | 1053 | 702 | 1755 | 固定800目标在P原批成员/顺序及同批上下文条件下的重复诊断 |
| 原固定87诊断分批 | 87批、800条 | 261 | 174 | 435 | 同一事前诊断partition内的抽样重复/微扰稳定性 |

第一方案的2959条伴随材料只为保留原整批，必须保留整批输出，但不加入800统计目标或改变权重。它需要新scope/namespace；当前元数据闭包建议不是已采纳执行合同。第二方案复用原封存800、87批、共同材料与统计数学；只有13诊断批恰好与P原整批相同，不能据此称全800已复现P语境。没有必要仅为一般抽样稳定性另跑伴随2959条。

选择第二方案时应披露：这是同批新上下文诊断，不是逐记录新上下文；87分组不同于P；800为remaining600/exposed200，并且原抽样层名含历史机器I/F辅助信息，不可说成全部未曝光或纯来源属性抽样。后续实际三次R不能使用本轮输出重选样本、批次或比较域。初始最小preset按“每个记录”写且说不使用旧答案；现共同协议明确按批，当前800绑定方案采用旧已登记抽样。这些沿革应明确登记，不能无条件称与初始最小协议逐字全同。它们不妨碍按实际现行预设实施有范围限定的样本稳定性，但也不证明生产P原分批的逐条可重复性。

实施前需另封运输修订，旧准备文件不改。原启动器把条件/attempt/逻辑标签/唯一输出地址追加进真实user请求；原actor和request也依赖这个标签定位写入槽。只删追加段会留下未定义的输出位置。新运输说明应对三次R完全相同，将条件、尝试与输出地址仅放ROOT外台账。可以以同一只读batch目录作CLI工作目录，以外部 `--output-last-message` 参数指定捕获位置，让actor只提交一个完整严格JSON首答；ROOT保留捕获UTF8原字节并另做真实进程/输入/输出哈希封存。这须明确改为“ROOT捕获的首答及ROOT运输封存”，不能沿用“actor已写first/report/seal”的来源声称，也不能把CLI文本当provider网络wire。若继续保留actor写三文件，则使用稳定相对输出说明和独立slot工作目录，并披露地址/CLI环境可能可见，不能声称全部模型context/wire字节相同。两者都保持研究schema、判据、成员、实读与逐字证据要求。

R1是新的诊断第一结果，R2/R3是两次完整独立重复；P不属于任何R。W仅做预定JSON缩进变体，H仅做首行同义变体，各与固定R1比较；两者及其技术重试均不得代替任何R。五条件共435次首次批执行，1305预留技术槽只是最大attempt额度。合法null入选后停止重试，保留全部失败与未调用；全部五条件真实末态后再按固定五对及三方计算共同二元稳定、κ、阳性变化、null/失败/覆盖，不设新稳定阈值。

实际派发前还需已验证Python3.14/jsonschema、CLI0.162.1、整批严格接收及非空真实输入白名单绑定、最多3进程，以及当前生产恢复及子进程真实终态。旧共享锁不能证明当前recoveryv4已结束。当前只给方法与准备建议，无GO、模型调用、分类器运行、标签修改或progress写入；本结论不代表分类效度、真人信度、规则当前版本复现或完整Goal已验收。
'''
save('report.md',md)
save('old-readiness-seal-preservation-check.json',{'at_utc':now(),'old_seal':binding(D/'seal.json'),'members':original_checks,'all_exact':True})
save('input-bindings.json',{'at_utc':now(),'files':inputs,'file_N':len(inputs),'packet_bodies_read':False,'human_answers_read':False})
checks=[{'expected':f,'actual':binding(f['path']),'exact':binding(f['path'])==f} for f in inputs]
assert all(x['exact'] for x in checks)
save('readback-check.json',{'at_utc':now(),'all_input_metadata_exact':True,'checks':checks,'real_attempt_directory_N':len(manifest['routes']),'nonempty_N':len(nonempty),'no_model_calls':True,'old_seal_members_unchanged':True})
save('seal.json',{'at_utc':now(),'files':[binding(p) for p in sorted(O.iterdir()) if p.is_file()],'self_excluded':True,'actual_models_called':0,'classification_calls':0,'preserves_initial_seal':binding(D/'seal.json')})
print(json.dumps({'output':str(O),'seal':binding(O/'seal.json'),'old_seal':binding(D/'seal.json')},ensure_ascii=False))
