"""Exclusive preparation only. Does not import runner or invoke a model/CLI."""
from pathlib import Path
import ast, copy, datetime, hashlib, json
import jsonschema
HERE=Path(__file__).resolve().parent;B=HERE.parents[1]
OLD=B/'06-coding/native-full4481-v1-sol';batch=OLD/'batch-0216'
V16=B/'01-review/source-interface-v16-article6-addendum-sol'

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def load(p):return json.loads(Path(p).read_bytes())
def binding(p):
    p=Path(p).resolve();raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def exact(b):assert binding(b['path'])=={k:b[k] for k in ('path','bytes','sha256')}
def save(name,x):
    with (HERE/name).open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
def text(name,s):
    with (HERE/name).open('x',encoding='utf8') as f:f.write(s)
def diffs(a,b,p=''):
    if type(a)!=type(b):return [p]
    if isinstance(a,dict):return [p+'/'+k for k in set(a)^set(b)]+sum((diffs(a[k],b[k],p+'/'+k) for k in a.keys()&b.keys()),[])
    if isinstance(a,list):return [p] if len(a)!=len(b) else sum((diffs(x,y,p+'/'+str(i)) for i,(x,y) in enumerate(zip(a,b))),[])
    return [] if a==b else [p]

def main():
    old=load(batch/'assignment.json');assert old['source_ids']==['RECODE25-01402','RECODE25-01403','RECODE25-01404']
    for v in old.values():
        if isinstance(v,dict) and {'path','bytes','sha256'}<=set(v):exact(v)
    for v in old['packets']+old['source_asset_bindings']:exact(v)
    proof=load(V16/'byte-and-source-interface-proof.json');exact(proof['new_packet']);exact(proof['original_packet']);exact(proof['new_common']);assert proof['other_4480_packet_bindings_exact_reused'] is True and proof['current_source_record_contexts_unchanged'] is True
    # Decode only authorized01402, never01403/01404, human200 or remaining bodies.
    newpacket=load(proof['new_packet']['path']);oldpacket=load(old['packets'][0]['path']);assert oldpacket['source_bundle']['source_record']==newpacket['source_bundle']['source_record']
    raw=json.dumps(newpacket['source_bundle'],ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode();assert hashlib.sha256(raw).hexdigest()==newpacket['source_bundle_sha256']==proof['new_bundle_canonical_sha256']
    directory=HERE/'batch-0216';directory.mkdir()
    for n in range(1,4):(directory/f'attempt-{n:04d}').mkdir()
    (HERE/'execution.lock').touch(exist_ok=False)
    validator=B/'06-coding/full4481-native-execution-adapter-sol/root-validator-amendment-01/validate-structured-batch-production-binding-v2.py'
    with (HERE/'base-validator.py').open('xb') as f:f.write(validator.read_bytes())
    routes=[dict(batch_id='batch-0216',attempt_number=n,runtime_task_name='native_v16_material_batch0216_a'+str(n),output_directory=str(directory/f'attempt-{n:04d}'),first_path=str(directory/f'attempt-{n:04d}'/'first.json'),report_path=str(directory/f'attempt-{n:04d}'/'report.txt'),seal_path=str(directory/f'attempt-{n:04d}'/'seal.json')) for n in range(1,4)]
    save('attempt-output-routing.json',dict(run_id=HERE.name,routes=routes,fresh_ephemeral_CLI_each_attempt=True,max_total_technical_attempts=3,route_is_operational_not_scientific_definition=True))
    packets=copy.deepcopy(old['packets']);packets[0].update(**proof['new_packet'],source_bundle_sha256=newpacket['source_bundle_sha256'],source_bundle_utf8_bytes=len(raw))
    scope='separate actual v16 same-version material recoding of original whole batch-0216; not prior v15 technical recovery or independent stability repeat'
    contract=dict(artifact_type='neutral_v16_material_delta_transport_contract',at_utc=now(),run_id=HERE.name,scope=scope,batch_id='batch-0216',source_ids=old['source_ids'],changed_material_source_ids=['RECODE25-01402'],old_packet=old['packets'][0],new_packet=packets[0],unchanged_other_two_packets=packets[1:],current_source_record_and_contexts_unchanged=True,source_snapshot_SHA_unchanged=proof['source_snapshot_SHA_unchanged'],added_material='same source/version complete article6 four consecutive paragraphs and next article header only; no definition or expected conclusion added',manual=old['manual'],execution_prompt=old['execution_prompt'],protocol=old['run_scope_binding'],requested_model='gpt-6.1-sol',requested_reasoning_effort='ultra',context_unit='batch',max_total_technical_attempts=3,actual_concurrency_cap=1,maximum_common_protocol_concurrency=3,semantic_or_null_retry_prohibited=True,earliest_technically_valid_complete_new_material_batch=True,original_results_immutable=True,first_is_actor_structured_submission_not_provider_wire=True,actual_execution_or_label_authorized_by_this_preparation=False,provider_serving_model_independently_verified=False)
    save('neutral-material-transport-contract.json',contract)
    instructions=(OLD/'actor-instructions.txt').read_text()
    instructions=instructions.replace('本研究全量4481条政策材料生产编码中的','本次独立v16同版材料修订原整批0216中的').replace('ROOT以fork_turns=none的新上下文派发真正coding actor','ROOT以fresh ephemeral CLI新上下文派发真正coding actor').replace('本批v15政策packet','本批assignment明确绑定的v15原packet或v16同版补材packet').replace('旧v16目录、A/B/GOLD','未由本批assignment绑定的旧v16候选目录、A/B/GOLD').replace('ROOT以fresh fork_turns=none派发','ROOT以fresh ephemeral CLI新上下文派发').replace('所有批次合计一次全量4481材料生产运行，尚待正式800条真人参照验证；各批不构成独立重复或真人编码。','本轮仅处理原整批0216的3条：01402使用明确绑定的v16同版中性补材，另外两条原packet不变；它是另存实际材料重编码，不是旧v15技术重试，也不构成独立稳定性重复或真人编码。')
    instructions+='\n本轮中性材料变化仅依assignment绑定的neutral-material-transport-contract；不读任何开发诊断、预期、参照或旧答案。所有真实文字呈现使用assignment.presentation_helper按至多6500 Unicode字符的连续区间，记录输出PRESENTATION头内的presentation_event和精确start/end；工具必须有足够输出预算且无截断，截断区间必须另行补读。完整读本批assignment、手册、execution prompt、actor instructions、output schema、output contract及本中性材料contract，再按既定成员顺序完整读三个packet。不能读取common_source_jsonl_identity_only全量正文。呈现输出是可观测工具文字，不独立证明服务模型身份。首答候选可在自己的slot暂存，使用assignment.submit_helper独占复制其原字节到自己的first；该helper不检查/修订答案。first保存后只写自己的report与seal；seal明确run_id/batch_id/template_only=false/actual_completion_claimed=true、first_binding/report_binding和非空全部真实已读输入绑定。仅ROOT验收，不因合法null或语义结果重试。\n'
    text('actor-instructions.txt',instructions)
    schema=load(batch/'output.schema.json');schema['properties']['run_id']['const']=HERE.name;schema['properties']['scope']['const']=scope;schema['properties']['records']['prefixItems'][0]['properties']['packet_sha256']['const']=packets[0]['sha256']
    jsonschema.Draft202012Validator.check_schema(schema);save('batch-0216/output.schema.json',schema)
    validation=load(batch/'output-validation-contract.json');validation.update(run_id=HERE.name,output_schema_binding=binding(directory/'output.schema.json'),strict_technical_validator=binding(HERE/'base-validator.py'),attempt_output_routing=binding(HERE/'attempt-output-routing.json'),new_material_round=True,observable_pre_first_literal_readback_required=True,explicit_actor_template_only_false_required=True)
    save('batch-0216/output-validation-contract.json',validation)
    assignment=copy.deepcopy(old);assignment.update(run_id=HERE.name,scope=scope,state='prepared_new_v16_material_not_dispatched',output_directory=str(directory),packets=packets,packet_bytes=sum(x['bytes'] for x in packets),common_source_jsonl_identity_only=proof['new_common'],original_assignment_binding=binding(batch/'assignment.json'),actor_instructions=binding(HERE/'actor-instructions.txt'),output_schema=binding(directory/'output.schema.json'),output_validation_contract=binding(directory/'output-validation-contract.json'),strict_technical_validator=binding(HERE/'base-validator.py'),attempt_output_routing=binding(HERE/'attempt-output-routing.json'),campaign_scope_metadata_binding=binding(HERE/'neutral-material-transport-contract.json'),presentation_helper=binding(HERE/'emit-presentation.py'),submit_helper=binding(HERE/'submit-first.py'))
    article=V16/'source-library/article6-original-complete-with-next-boundary.json';assignment['source_asset_bindings'].append(dict(**binding(article),source_ids=['RECODE25-01402'],consumer_read_status='not_recorded',consumer_use_status='not_recorded',neutral_same_version_material=True))
    assert assignment['packet_bytes']==223991<=260000 and assignment['packets'][1:]==old['packets'][1:]
    save('batch-0216/assignment.json',assignment)
    text('dispatch-core.txt','''你是独立原生政策文本编码执行者，仅作本轮原整批0216完整一次提交。先完整阅读 {ASSIGNMENT}，只按其绑定的共同手册和execution-prompt执行五维原样标准。
所有真实必需文字呈现使用 {PRESENT_HELPER} --assignment 本批assignment绝对路径 --path 绑定文件绝对路径 --start 起点 --end 终点；连续每段不超过6500 Unicode字符，工具输出预算须足够。记录其PRESENTATION头中的真实区间和presentation_event；截断时补读，不得把程序load/hash当阅读。先完整读assignment、手册、提示、actor instructions、schema、output contract及中性material contract，再按01402/01403/01404顺序完整读所有packet。限定必要同版材料范围，不读全量共同JSONL正文、参照、预测、指标、旧尝试、别批、开发诊断或用户配置，不委派、不搜索。
本轮仅01402使用已绑定同版v16中性补材，其他两条packet原字节不变；依原手册判断，不能预设任何维度答案。同一整批上下文，gpt-6.1-sol ultra请求。每个0/1至少一条已读packet内真实JSON pointer和逐字quote；合法null如实保留，缺项说明，禁止未知填0。
首个完整整批结构化候选按schema和原成员顺序保存自己的slot暂存文件，再使用 {SUBMIT_HELPER} --assignment 本批assignment绝对路径 --input-file 自己slot暂存文件绝对路径 --first-path {FIRST} 独占复制其原字节。只提交一次，不执行validator、不根据反馈修改首答、不跨尝试拼接。只在首答之后写自己的 {REPORT} 与 {SEAL}；seal必须含本轮run_id/batch_id、template_only=false、actual_completion_claimed=true、准确first/report绑定及非空全部真实已读文件绑定。不要把空slot/模板当尝试，不宣称provider wire或服务身份已独立核验。共同并发上限3，本单批运输实际最多1进程；技术重试仅由ROOT管理，null和语义分歧不触发重试。
''')
    root_metadata=dict(at_utc=now(),original_assignment=binding(batch/'assignment.json'),original_packet=old['packets'][0],new_packet=packets[0],old_common=proof['old_common'],new_common=proof['new_common'],v16_material_seal=binding(V16/'output-seal.json'),neutral_material_byte_proof=binding(V16/'byte-and-source-interface-proof.json'),ROOT_material_diagnostic_adoption=binding(B/'08-audits/ROOT-v16-article6-material-diagnostic-adoption.json'),readable_actor_binding_excludes_C_diagnostics_and_expectations=True,source_lineage_changed=True,source_record_contexts_same=True,other_two_packet_bytes_same=True,source_snapshot_original_SHA_same=proof['source_snapshot_SHA_unchanged'],no_model_calls=True,no_classifier_calls=True,no_production_dispatch=True)
    save('ROOT-source-lineage-proof.json',root_metadata)
    m=dict(at_utc=now(),run_id=HERE.name,scope=scope,source_N=3,batch_N=1,batches=[dict(batch_id='batch-0216',source_ids=assignment['source_ids'],assignment=binding(directory/'assignment.json'))],runner=binding(HERE/'runner.py'),receiver=binding(HERE/'strict-readback-receiver.py'),base_guard=binding(B/'08-audits/native-recovery-v2-preflight-sol/strict_reception_guard.py'),validator=binding(HERE/'base-validator.py'),cli_launcher=binding(B/'06-coding/isolated-codex-cli-0.162.1-root/node_modules/.bin/codex'),instructions=binding(HERE/'actor-instructions.txt'),transport_contract=binding(HERE/'neutral-material-transport-contract.json'),presentation_helper=binding(HERE/'emit-presentation.py'),submit_helper=binding(HERE/'submit-first.py'),original_assignment=binding(batch/'assignment.json'),original_controller=binding(B/'08-audits/recover-native-whole-batches-v4-root.py'),original_capacity3=binding(B/'08-audits/native-recovery-v2-preflight-sol/ROOT-transport-capacity3-sidecar.json'),v16_material_seal=binding(V16/'output-seal.json'),max_total_technical_attempts=3,actual_concurrency_cap=1,conceptual_protocol_cap=3,technical_states_only=True,actual_remaining_result_required=str(B/'06-coding/native-full4481-transport-recovery-v2-sol/execution-runs/20261011T150825641847Z/result.json'),model_requested='gpt-6.1-sol',reasoning_requested='ultra',provider_identity_verified=False,formal_validation_complete=False,actual_execution=False)
    save('manifest.json',m)
    changes=sorted(diffs(load(batch/'output.schema.json'),schema));assert changes==['/properties/records/prefixItems/0/properties/packet_sha256/const','/properties/run_id/const','/properties/scope/const']
    save('static-binding-schema-checks.json',dict(at_utc=now(),schema_checked=True,output_schema_changed_paths_only=changes,assignment_changed_paths=sorted(diffs(old,assignment)),manual_prompt_protocol_packet_schema_and_model_unchanged=True,other_two_packets_full_binding_equal=True,member_order_equal=True,original_packet_bytes=old['packet_bytes'],new_packet_bytes=assignment['packet_bytes'],under_original260000_budget=True,base_validator_exact_v4_used_bytes=binding(validator)['sha256']==binding(HERE/'base-validator.py')['sha256'],original_inputs_verified=[binding(v['path']) for v in old['packets']],no_labels_or_expected_values_loaded=True,actor_binding_audit_paths_excluded=True))
    for file in HERE.glob('*.py'):ast.parse(file.read_text(),filename=str(file))
    save('future-compatible-merge-contract.json',dict(artifact_type='future_native_v16_material_composite_contract_only',run_id=HERE.name,parent_required={'record_N':4481,'batch_N':504,'full_corpus_complete':True,'identity':'actual original v15 whole batch collection with immutable original/recovery origins'},new_delta_required={'batch_id':'batch-0216','source_ids':old['source_ids'],'whole_batch_record_N':3,'earliest_valid_new_material_attempt':True,'strict_schema_seal_and_observable_event_readback':True},result_record_N=4481,parent_unchanged_record_N=4478,new_actual_record_N=3,replacement_by_original_member_ids_only=True,preserve_new_actual_all_five_dimensions_and_reasons=True,no_cross_attempt_or_dimension_splicing=True,parent_other4478_original_jsonl_line_bytes_preserved=True,original_v15_0216_results_not_deleted_or_overwritten=True,origins=['original_v15_selected_whole_batch','v15_transport_recovery_selected_whole_batch','new_actual_v16_material_whole_batch0216'],compatible_material_version_disclosure='Only01402 source lineage changed to v16;01403/01404 packet bytes unchanged but newly encoded in same new-material batch context.',not_all4481_reencoded_in_v16=True,not_independent_stability_or_human_validation=True,old_collector_not_modified_and_cannot_accept_new_packet_as_original_v15=True,mechanical_adapter_required_after_real_new_result=True,actual_merge_performed=False))
    text('PREPARATION-NOTE.md','''# 0216 同版v16材料整批运输准备

只准备，未调用模型或CLI，未授权实际执行、标签或合并。共同manual/execution-prompt/protocol原字节、模型6.1 Sol ultra、原三成员顺序与五维规则不变。01402换用已封存同源同版完整第六条中性材料packet；01403/01404原packet不变。新总packet223991字节，仍满足原260000静态批预算。schema仅改run_id、scope、首条packet_sha256三处const。

这将是另存的真实材料重编码，不是v15技术恢复的第4次，也不是独立稳定性重复。至多3个fresh技术attempt，ROOT只选择最早有效完整整批；0/1逐字packet证据，合法null不重试。新封存receiver复用v4 schema/seal guard，另核实际pre-first事件文字覆盖、声明区间、必需actor输入收据与原packet顺序。所见真实工具文字不独立证明服务身份或provider内部上下文。输入hash/read helper本身不是阅读。

actor只见新assignment中绑定的中性材料合同，不绑定C诊断、expected、开发值或人工200。ROOT-source-lineage-proof仅是ROOT溯源元数据，不在actor可读绑定中。旧原件、controller、接收件与正在运行的session28945不变；本单批最多1真实子进程，无capacity13切换。

未来入口由ROOT提供真实GO：system Python runner.py --mode run --go ROOT未来实际GO文件。GO须绑定本准备seal/runner、真实remaining运行20261011T150825641847Z/result.json（不能用旧pilot）、全部已派恢复子进程末态清单、无存活CLI/原controller，以及完整4481/504父native collection。当前缺GO，准备不启动。只读预检：runner.py --mode preflight。

未来兼容合并须新建机械adapter，把完整父4481中的原三成员整批替换为此最早真实新3记录，其余4478原行字节不变，保留三类真来源和旧0216首答；不得称4481全量v16重新推理。已有collector硬核原packet相等，不能直接把增材首答冒称原v15成功。此处只冻结合并接口合同，不提前制造结果。
''')
    print(json.dumps({'prepared':str(HERE),'schema_diff_N':len(changes),'actual_model_calls':0,'actual_classifier_calls':0},ensure_ascii=False))

if __name__=='__main__':main()
