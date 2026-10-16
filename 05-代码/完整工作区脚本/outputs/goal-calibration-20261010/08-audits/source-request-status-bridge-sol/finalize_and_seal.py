"""Document only the already completed synthetic alias checks."""
from pathlib import Path
import datetime
import hashlib
import json

D=Path(__file__).resolve().parent
def bind(p):
    p=Path(p).resolve();raw=p.read_bytes()
    return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def write(name,v):
    with (D/name).open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
pre=json.loads((D/'preparation-seal.json').read_bytes())
for m in pre['members']:assert bind(m['path'])==m
inputs=json.loads((D/'frozen-interface-bindings.json').read_bytes())['inputs']
for m in inputs:assert bind(m['path'])==m
summary=json.loads((D/'execution/summary.json').read_bytes())
rows=[json.loads(line) for line in (D/'execution/first-results.jsonl').read_text().splitlines()]
report={'status':'candidate_prepared_and_synthetic_contract_checked_not_deployed','at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'interface':{'module':str(D/'status_bridge.py'),'pure_api':'bridge_json_bytes(raw: bytes, expected_sha256: str, pointer: str=/source_requests) -> (copied_document, alias_receipt)','request_api':'canonicalize_request(request) -> (copied_request, field_provenance)','CLI':'python3 status_bridge.py --input SAVED_JSON --input-sha256 EXACT_SHA --request-pointer /EXACT/PATH/source_requests --out NEW_DIRECTORY','CLI_scope':'one explicit request list; preparation only; no cohort loader/recovery/acceptance command'},'canonicalization':{'resolved':'only exact resolved in the sole present recognized field, or both fields exactly resolved','negative':'exact stopped/unresolved retain same status; do not delete request or material/quote/consumer fields','invalid':'present invalid/null/nonstring, unknown, missing, conflicting fields reject the entire selected list/document; do not choose favorable field','fields_changed':'only status added when absent; already valid status unchanged; dependency_status always retained','original_identity':'raw input bytes SHA must match explicit expected SHA; CLI saves exact input-original.json; receipt saves original request, pointer, original fields and canonical structural hashes','empty_list':'preserved empty, not a resolved source certification','duplicate_JSON_keys':'rejected, not last-key selection','scope_and_evidence':'no closure/consumer/quote/source check skipped or claimed; original fields remain unchanged'},'first_synthetic_results':summary,'preparation_seal':bind(D/'preparation-seal.json'),'actual_integrated_protocol_check_tested':False,'actual_recovery_tested':False,'original_data_requirements_for_future_mechanical_reception':['Wait for first-run terminal seal and independent ROOT reception; preserve all original first output/log/error bytes and frozen scope/algorithm/protocol/source input bindings. This candidate is not GO.','Retain complete first candidate_decisions_diagnostic_only for all five dimensions and original evidence-validator stage; retain real null, construction/technical failure and missing diagnostic states distinctly. Missing first output must not be rebuilt or called first.','Retain exact raw source_requests across exception_source_audit/source log/record and the entire accompanying material_requests. Use the complete selected list, never only favorable resolved requests; preserve unrelated stops and independent-positive audit.','Retain saved semantic unit/contexts, relation and source_relation traces, inventory, source_view_events, read/use receipts, requirements/reference_resolution and scope-review note needed by the existing validators. Source/view SHA, locator, same-version bounded proof and quote identity still require their original checks.','If processing JSONL later, bind the sealed whole ledger file SHA plus original line position/bytes and exact request JSON pointer outside this helper; retain exact original ledger and derived alias receipt. The helper SHA verifies supplied JSON bytes, not an actual producer or execution attestation.','A future authorized receiver must use the same canonical requests consistently in protocol.check and the driver-equivalent stopped-request logic while retaining the raw array separately. Re-run mechanical check of original saved events/proof only; this does not authorize semantic_unit/RelationView/judge or changed labels.','Only independently confirmed status-field mismatch failures may be mechanically reconsidered. Alias success does not clear other protocol errors, missing source/consumption/scope, unknown proof or failed evidence; such items remain blocked.','Write any future derived reception/output into a new authorized directory with original-to-derived bindings; never overwrite protocol/driver/v5, first-run diagnostics/errors/results, source records, reference or formal statistics scope.'],'actual_reads':{'read_code_only':['old protocol relevant status and source/read/use checks','frozen final-v5 driver raw request log and protocol/stop gate','v5 relations status producer'],'byte_binding_only':['frozen scope protocol binding','v5 preseal/algorithm and all five module bytes'],'full_domain_original_saved_outputs_read':False,'main_LLM_outputs_read':False,'classifier_or_actual_policy_run_executed':False},'no_new_source_authentication_framework_or_statistics_method':True}
write('report.json',report)
write('failures.json',{'failed_controls':[r for r in rows if not r['matches_fixed_expectation']],'first_outputs_preserved':True})
readme='''字段桥接候选已准备，尚未部署或执行恢复。旧protocol（source_reading_protocol_v12.py第58–59行）和final-v5 driver第370–373行只读status；v5发布dependency_status。已绑定真实冻结代码，不改原件。

接口：bridge_json_bytes(raw, expected_sha256, pointer='/source_requests')返回复制文档和别名receipt。只接受resolved/stopped/unresolved三个精确字符串；单字段明确resolved或两字段相等resolved才生成status resolved。stopped/unresolved保留停止；两字段冲突、缺失、null、未知、非字符串、重复JSON键及原字节SHA不符均拒绝，不产出可用canonical document。空列表只是空列表。

status以外字段、请求顺序、未解材料、引文、闭合证明及消费者限制全部保留。CLI只准备一个明确JSON指针，保存原字节和逐请求来源；不认证来源、实际阅读、消费或语义，也不运行protocol.check。若CLI生成候选，其文件SHA在receipt另存，结构canonical SHA与文件字节SHA分开。

代码和18项输入/预期在preparation-seal中事前固定；首次实际18/18匹配，0意外技术失败。执行结果在execution/first-results.jsonl逐项即时保存；仅核旧status谓词，完整protocol.check未执行，classifier/全域/恢复均0。没有读取实际全域首轮输出或主LLM标签。

未来只有在原首轮终结、独立接收及ROOT明确授权后，才可用已保存完整diagnostic/semantic unit/source logs作机械再接收。须核原完整封存字节、当前精确原文、同版有限proof、消费者与read/use receipts，保留所有独立stopped请求和其他错误；别名成功不能免检，不能用缺失首答重新分类填补。具体原全域保存要求见report.json。候选不是恢复GO、正式结果接收或统计认证。
'''
with (D/'README.md').open('x',encoding='utf8') as f:f.write(readme)
seal_path=(D/'output-seal.json').resolve()
members=[bind(p) for p in sorted(D.rglob('*')) if p.is_file() and p.resolve()!=seal_path]
assert all(Path(m['path']).resolve()!=seal_path for m in members)
write('output-seal.json',{'status':'sealed_prepared_status_alias_candidate_not_recovery','members':members,'inputs':inputs,'self_excluded':True,'synthetic_controls_N':18,'synthetic_matches_N':summary['matches_N'],'actual_full_domain_processed_N':0,'classifier_calls_N':0,'protocol_checks_N':0,'recovery_executed':False})
for m in members+inputs:assert bind(m['path'])==m
print(json.dumps({'seal':bind(seal_path),'members_N':len(members),'inputs_N':len(inputs),'self_member_N':0,'all_readback_match':True,'synthetic_matches_N':summary['matches_N']},ensure_ascii=False))
