import json, hashlib
from pathlib import Path
from datetime import datetime, timezone

ap=Path('/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/native-full4481-v1-sol/batch-0234/assignment.json')
a=json.loads(ap.read_text())
slot=Path('/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/native-full4481-v1-sol/batch-0234/attempt-0001')
label='native_full4481v1_b0234_a01'
transport='fresh_codex_cli_exec'
all_ids=a['source_ids']

def binding(path):
 p=Path(path); raw=p.read_bytes()
 return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

def ranges(path, intervals):
 return [{'range_kind':'unicode_code_points','range_basis':'Unicode code points; zero-based half-open intervals of actual file text','start':s,'end':e,'presentation_event':f'functions.exec / exec_command bounded text presentation: FILE {path}, CHARS [{s},{e})'} for s,e in intervals]

files=[]
def add_text(path, intervals, ids, method='python3 pathlib.read_text; bounded verbatim presentation through exec_command; each declared interval actually read by actor'):
 b=binding(path)
 files.append({**b,'actual_presented_ranges':ranges(path,intervals),'not_truncated':True,'read_method':method,'source_ids':ids})

add_text(ap,[(0,9519)],all_ids)
for key,end in [('actor_instructions',3277),('execution_prompt',1672),('run_scope_binding',1104)]:
 add_text(a[key]['path'],[(0,end)],all_ids)
add_text(a['manual']['path'],[(0,10000),(10000,16813)],all_ids)
for key,end in [('response_retention_policy',2833),('read_manifest_template',1016),('output_seal_template',500),('output_validation_contract',3508)]:
 add_text(a[key]['path'],[(0,end)],all_ids)
add_text(a['output_schema']['path'],[(0,10000),(10000,20000),(20000,30000),(30000,32217)],all_ids)
packet_ends=[35388,35399,34234,34209,35303]
for pb,end in zip(a['packets'],packet_ends):
 add_text(pb['path'],[(0,10000),(10000,20000),(20000,30000),(30000,end)],[pb['source_id']])
for asset in a['source_asset_bindings']:
 if not asset['path'].endswith('.png'):
  continue
 page=int(Path(asset['path']).stem.rsplit('-',1)[1])
 files.append({**binding(asset['path']),'actual_presented_ranges':[{'range_kind':'full_image','range_basis':f'Complete rendered image of physical PDF page {page}; actual view_image presentation','start':None,'end':None,'presentation_event':f'functions.exec / tools.view_image, then image(image_url): {asset["path"}'}],'not_truncated':True,'read_method':'tools.view_image default high; full page image actually displayed and read','source_ids':asset['source_ids'],'physical_page':page,'source_pdf_sha256':'a83ae5ab957464358bb62a9eefe6cd6bf3e0a944ca7382e308eeb24ebce73eda'})
add_text(a['campaign_scope_metadata_binding']['path'],[(0,1948)],all_ids)
add_text(a['attempt_output_routing']['path'],[(581433,582262)],all_ids,'Only /routes/699 (own logical dispatch label) presented verbatim; routing is output metadata only. Whole file parsed/hashed mechanically, no other route presented or claimed read.')

# These reasons are the actor's single whole-batch judgment, after actual reading.
reasons=[
 {
 'S':'当前针对加入试点的沟通交流规定不建议合并其他事项，没有表达药物损害、用药风险或风险证据及控制要求。沟通事项的组织限制本身不构成安全性内容。',
 'E':'当前只限制申请沟通中合并其他事项，没有要求评价或提供药物防治效果、临床获益或效果证据。不能从研发计划的其他内容继承有效性。',
 'Ec':'不建议合并沟通事项是申请程序安排，未设置、评价或核验药品价格、治疗费用或支付内容。',
 'I':'当前规定沟通事项的组织方式，没有在本命题中设置创新研发可用的技术反馈、研发资源或实质创新资格条件。具名试点及相邻申请途径不能使这一程序限制继承创新支持。',
 'F':'当前没有将患者所需药品的保障缺口、获取差异或负担与按需优先机会相连。不合并其他事项的申请程序要求不能继承该计划整体的患者需求宗旨。'
 },
 {
 'S':'当前要求在申请栏目备注填写指定申请名称，属于标识和填写手续，没有药物风险内容或安全证据核验。',
 'E':'备注填写申请名称没有要求说明或评价药物效果、治疗获益或其证据，栏目名称不构成有效性内容。',
 'Ec':'当前只规定沟通申请的备注文字，未表达药品价格、治疗费用、支付范围或支付责任等实质信息。',
 'I':'指定备注“关爱计划-延伸申请”用于标识所递交申请，没有实质创新资格核验或研发支持安排。计划名称及申请对象身份不能使格式性填写获得创新性。',
 'F':'申请标识的备注要求没有提供按治疗需要配置的优先资源，也未讨论患者药品获取或负担障碍。不能由罕见疾病计划名称推出公平关系。'
 },
 {
 'S':'当前要求所有申请填写并提交具名实施框架，是资料填写与递交要求，未指定需要提供或核验何种药物风险实质内容。不能展开该框架全部安全字段赋予本句安全性。',
 'E':'当前没有明确要求说明、评价或核验药物防治效果及其证据，只要求填写并提交框架。框架内部另有疗效内容不使这项通用递交要求继承有效性。',
 'Ec':'实施框架的填写与递交未表达药品价格、治疗费用、支付标准或经济证据内容；一般沟通材料要求也不能展开为经济性。',
 'I':'“罕见疾病创新药物”在当前是待提交框架的题名，本句没有讨论创新属性或使用具体创新条件决定待遇，也未设置研发反馈、技术服务等支持安排。通用填写与递交义务不因题名而获得创新性。',
 'F':'所有申请填写并提交框架属于资料手续，当前没有把患者药品保障缺口或负担与按需机会配置直接相连。框架题名与计划的整体对象不足以构成公平关系。'
 },
 {
 'S':'当前允许申请人一并提交其认为有必要的其他资料，但未指定药物风险、安全信息或相应证据内容。资料内容未指定是本命题的完整规定，并非关键原文缺失。',
 'E':'其他资料用于支持申请，但当前没有表达这些资料须证明药物效果、临床获益或效果比较。一般可选资料提交不构成有效性证据要求。',
 'Ec':'当前的其他资料提交许可没有指定价格、治疗成本、报销或支付等经济信息，也没有相应实质安排。',
 'I':'允许一并提交申请人自行选择的其他资料是申报资料流转，没有设置技术审评反馈或明确创新研发可使用的专门服务。这里的“支持申请”不等于政策主体实际提供创新研发支持。',
 'F':'当前只允许一并递交其他申请资料，没有患者所需药品的可辨认保障缺口及以其为依据的优先、支持或负担安排。不能由试点对象继承公平性。'
 },
 {
 'S':'当前规定试点启动后五年为可提交申请的期间，没有药物损害、用药风险或风险评价及控制内容。完整跨页语境的截止与继续审评安排也未使该时间条款成为安全要求。',
 'E':'五年的申请期间属于申报时间安排，未评价、比较或要求证明药物防治效果与治疗获益。不能把计划其他资格或框架中的效果内容移入这一记录。',
 'Ec':'当前界定申请期间，没有药品价格、治疗费用、支付规则或预算内容；期限本身不是经济性安排。',
 'I':'当前仅界定具名试点申请的递交期间，没有在这一命题中设置研发资源、研究反馈、技术服务或实质创新条件。计划其他条款的创新研发支持不能由一般申请时间自动继承。',
 'F':'五年为一般申报期间，未将可辨认的患者药品保障缺口与按需优先机会、获取差异纠正或可负担安排直接相连。不能从罕见疾病对象或期限数字推出公平性，也不能推定该期限构成加快或优先。'
 }
]
records=[]
for pb,rs in zip(a['packets'],reasons):
 packet=json.loads(Path(pb['path']).read_text())
 current=packet['source_bundle']['source_record']['text']
 dims={}
 for d in ['S','E','Ec','I','F']:
  ev=[{'pointer':'/source_bundle/source_record/text','quote':current,'role':'current'}]
  if pb['source_id']=='RECODE25-01477' and d in ['S','E','I','F']:
   ev.append({'pointer':'/source_bundle/source_record/contexts/0/text','quote':packet['source_bundle']['source_record']['contexts'][0]['text'],'role':'context'})
  dims[d]={'value':0,'reason':rs[d],'evidence':ev}
 records.append({'source_id':pb['source_id'],'output_id':pb['output_id'],'packet_sha256':pb['sha256'],'dimensions':dims})

first={
 'artifact_type':'native_coding_actor_first_structured_whole_batch_submission',
 'run_id':a['run_id'],'batch_id':a['batch_id'],'context_unit':'batch',
 'requested_model':a['requested_model'],'requested_reasoning_effort':a['requested_reasoning_effort'],
 'manual_binding':a['manual'],'execution_prompt_binding':a['execution_prompt'],
 'execution_transport':transport,'logical_dispatch_label':label,'attempt_number':1,
 'identity_statement':'Fresh Codex CLI coding actor; logical dispatch label identifies only the frozen output reservation, not a collaboration agent identity. Actual CLI thread id retained by ROOT, not read by actor.',
 'actual_serving_model_independently_verified':False,
 'provider_wire_capture_claimed':False,
 'first_definition':'原生编码者首个完整结构化整批提交文件原字节；不是 provider 网络原始响应或 wire body。',
 'read_manifest':{'artifact_type':'actual_actor_read_manifest','run_id':a['run_id'],'batch_id':a['batch_id'],'context_unit':'batch','actor_id':None,'logical_dispatch_label':label,'execution_transport':transport,'actual_read_or_use_claimed':True,'template_only':False,'files':files,'coverage_statement':'Full manual, execution prompt, common protocol and all five assigned packets actually presented and read without tool truncation. Complete assigned rendered pages 6, 7, 8 actually viewed. Routing read limited to own row. Hashing and parsing are identity checks, not reading evidence.','semantic_use_statement':'Each record is judged from its current proposition and necessary local paragraph/heading context. Embedded whole-source paragraphs were read as part of the full packets; their labels are not inherited. Cross-page CARE-P040 / current-record context was used only to retain the complete application-period proposition for RECODE25-01477.'},
 'records':records,'scope':a['scope']
}
first_bytes=(json.dumps(first,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n').encode('utf-8')
with (slot/'first.json').open('xb') as f:
 f.write(first_bytes)
first_binding={'path':str(slot/'first.json'),'bytes':len(first_bytes),'sha256':hashlib.sha256(first_bytes).hexdigest()}

report=f'''执行方式：{transport}
逻辑派发标签：{label}
attempt_number：1
context_unit：batch
batch_id：{a['batch_id']}
自身覆盖：依 assignment 顺序一次完整提交 5 条记录（RECODE25-01473、RECODE25-01474、RECODE25-01475、RECODE25-01476、RECODE25-01477），逐条独立判断 S/E/Ec/I/F，共 25 项，附理由及 packet 逐字证据。

实际阅读：assignment [0,9519)；actor-instructions [0,3277)；manual [0,10000)、[10000,16813)；execution-prompt [0,1672)；common-execution-protocol [0,1104)。所有区间为 Unicode code points、0-based half-open。
五份 packet 均按顺序完整呈现，各自分段 [0,10000)、[10000,20000)、[20000,30000) 及末段：01473 [30000,35388)；01474 [30000,35399)；01475 [30000,34234)；01476 [30000,34209)；01477 [30000,35303)。这些已呈现区间均未截断，均实际阅读。
实际完整打开并阅读 cde-care-06.png、cde-care-07.png、cde-care-08.png，分别为绑定 PDF 的物理页 6、7、8；适用 source_id 依 first.read_manifest 明确绑定。第 7—8 页申请时间跨页段落已核对。
输出/读取/保留协议、schema、run-scope 的实际呈现区间和哈希见 first.read_manifest。attempt-output-routing 仅呈现并核对自身 /routes/699，原文件字符 [581433,582262)，未呈现其他派发槽。

语义使用范围：当前固定命题、其局部段落/标题及跨页完整申请时间段落。packet 内联同版全文已完整阅读，但不向每条继承全文标签；外部同版文字资源 care-full-source-v8.json 和 PDF 文件本身未打开，未声称这些独立文件已经实际阅读。原件视觉核对通过 assignment 绑定的三张完整图页完成。一般法规/管理办法题名不作无限递归补全。
关键材料缺失：未发现影响本批逐维判断的关键原文或指代缺失；不存在不可读的必要图页。未用未知填 0。

本次只有一个完整整批结构化提交，未自行派代理、未自行重试、未读取其他批/其他 attempt/参照答案/预测/指标/历史对话/用户配置或记忆。未运行 ROOT 验证器，未读取 ROOT 接收回执，未写 canonical。已保存首答不作重排、重构或修改。
first.json 定义：执行者首个完整结构化整批提交文件原字节，不是 provider 网络原始响应。请求 model/effort 依 assignment 为 gpt-6.1-sol / ultra，未独立核验实际 serving model。逻辑派发标签仅用于匹配冻结输出槽，不声称 collaboration 代理身份；CLI thread id 由 ROOT 留存，执行者未读取其留痕文件。
本批属于一次全量4481条主生产运行的批次，非逐 record 独立上下文，不构成独立重复，正式800验证与稳定性/重复检验另行进行。

first 原件：{first_binding['path']}
first bytes：{first_binding['bytes']}
first SHA256：{first_binding['sha256']}
实际候选/失败文件：无。
保存方式：first.json、report.txt、seal.json 均以 xb 独占创建；仅自身唯一 attempt slot。
ROOT 技术有效性选择：尚待 ROOT 独立执行，执行者不声明已通过。
'''
report_bytes=report.encode('utf-8')
with (slot/'report.txt').open('xb') as f:
 f.write(report_bytes)
report_binding={'path':str(slot/'report.txt'),'bytes':len(report_bytes),'sha256':hashlib.sha256(report_bytes).hexdigest()}
seal={
 'artifact_type':'native_coding_actor_output_seal','template_only':False,
 'run_id':a['run_id'],'batch_id':a['batch_id'],'context_unit':'batch',
 'execution_transport':transport,'logical_dispatch_label':label,'attempt_number':1,
 'own_output_slot':str(slot),'actual_created_at':datetime.now(timezone.utc).isoformat(),
 'actual_completion_claimed':True,'completion_scope':'Own original whole-batch structured submission and report saved; all five assigned records and twenty-five dimensions covered. ROOT technical validity has not been checked by actor.',
 'first_definition':first['first_definition'],'first_binding':first_binding,'report_binding':report_binding,
 'first_valid_candidate_binding':None,'first_and_candidate_bytes_identical':None,
 'original_submission_unit':'one complete ordered assigned batch; no separate first-unit or reconstructed candidate',
 'actual_candidate_failure_bindings':[],
 'actual_input_bindings':[{k:f[k] for k in ['path','bytes','sha256']} for f in files],
 'input_identity_note':'All accessed file bytes and hashes match the frozen assignment where a binding is provided. Read intervals/view events are recorded separately and are not inferred from hashes.',
 'technical_validation_performed_by_actor':False,'ROOT_receipt_read':False,'canonical_written':False,
 'provider_wire_capture_claimed':False,'actual_serving_model_independently_verified':False,
 'collaboration_agent_identity_claimed':False,'logical_label_only':True,
 'request_model':a['requested_model'],'request_reasoning_effort':a['requested_reasoning_effort'],
 'execution_identity_note':'fresh_codex_cli_exec as specified by request-outside metadata; logical dispatch label is not a collaboration agent identity; actual CLI thread id is retained by ROOT and not inspected by actor.'
}
seal_bytes=(json.dumps(seal,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n').encode('utf-8')
with (slot/'seal.json').open('xb') as f:
 f.write(seal_bytes)
print(json.dumps({'saved_with':'xb','first':first_binding,'report':report_binding,'seal':{'path':str(slot/'seal.json'),'bytes':len(seal_bytes),'sha256':hashlib.sha256(seal_bytes).hexdigest()},'records':len(records),'dimensions':25,'ROOT_validator_run':False},ensure_ascii=False))
