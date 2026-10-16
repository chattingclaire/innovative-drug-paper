"""Seal the six saved mechanical checks, excluding this seal itself."""
from pathlib import Path
import datetime, hashlib, json

D=Path(__file__).resolve().parent
def bind(p):
    p=Path(p).resolve();b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def load(p): return json.loads(Path(p).read_bytes())
def write(name,v):
    with (D/name).open('x',encoding='utf8') as f: json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')

pre=load(D/'preparation-seal.json')
for m in pre['members']+pre['inputs']: assert bind(m['path'])==m
summary=load(D/'execution/summary.json'); assert summary['saved_check_results_N']==6 and summary['matching_fixed_checks_N']==6
checks=[]
for p in sorted((D/'execution/checks').glob('*.json')):
    j=load(p); assert j['matches_fixed_expectation'] is True
    checks.append({'path':str(p.resolve()),'record_id':j['record_id'],'version':j['log_version'],'errors':j['actual_output']['errors'],'stops':j['actual_output']['dependency_stop_reasons'],'check_sha256':bind(p)['sha256']})
assert {(c['record_id'],c['version']) for c in checks}=={(rid,v) for rid in pre['allowed_record_ids'] for v in ['original','alias']}
write('mechanical-integration-report.json',{'status':'three_existing_logs_old_and_alias_protocol_checks_match_fixed_contract','at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'records':checks,'summary':summary,'interpretation':'For these three saved logs, aliasing dependency_status=resolved to legacy status=resolved changes only the old checker stop caused by missing status. Original checks return errors=[] and stop missing_required_source; alias checks return errors=[] and no dependency stops. The no-stop alias result is a field-contract observation, not source acceptance, semantic validation, retained-label recovery, or GO.','driver_equivalent_stop_logic':'Uses the exact canonical request array from each corresponding log; original required stop N=1, alias required stop N=0. No source request is removed or selected by favorability.','mechanical_scope':'Frozen source inventory and saved protocol logs only; quote/closure/read-use integrity is referenced from the independent S3 audit and was not rebuilt here.','forbidden_calls':{'semantic_unit':0,'RelationView':0,'judge':0,'actual_reading_log':0,'full_domain_records':0,'classifier':0,'recovery':0},'original_technical_failures_and_ledgers_unchanged':True,'new_retained_labels_or_metrics':0})
write('failure-and-boundary-report.json',{'technical_failures_N':0,'contract_mismatch_N':0,'missing_source_stop_original_N':3,'missing_source_stop_alias_N':0,'not_recovered':True,'not_formal_or_human_validation':True,'retained_fields':['raw JSONL line bytes/line SHA','raw source packets and source bundle SHA','uniform source log','all read/use receipts','requirements','source inventory','material requests','saved diagnostic/capture and original ledger','original first inspection failure']})
readme='''三条已暴露历史source log的状态字段桥接机械集成检查已完成。每条原log与同一log的别名副本各调用旧protocol.check一次，共6次。semantic_unit、RelationView、judge、actual_reading_log、分类器及全域恢复调用均为0。

固定指针仅为 /uniform_source_reading_log/source_requests。原记录的dependency_status=resolved没有status。原副本按旧protocol缺失status默认unresolved，三条均返回errors=[]、dependency_stop_reasons=[missing_required_source]，driver等价停止数1。别名副本只增加status=resolved，其他日志字段、回执、要求、来源库存、材料请求、引文、消费和错误捕获保持同构；别名检查均errors=[]、stops=[]、driver等价停止数0。六项均匹配事前期待。

这是状态字段契约检查。别名清除的是旧协议对缺失status的机械停止，不能证明来源已接收、语义正确、闭合或消费合格，也不能恢复原technical_failure的labels/decisions、生成指标或放行全域运行。三条完整引文/闭合/read-use证据由独立v5-historical-S3-ledger-interface-sol审计引用，本目录没有重构semantic unit。

原始JSONL前缀与三行字节、raw source packet、source bundle SHA均绑定。原log和首轮ledger/diagnostic/capture不改。后续如需接收，需等待首轮终结和ROOT独立接收，另建正式目录，再机械验证完整保存的原字节、完整源库存、要求/回执、引用闭合、消费者范围和全部错误。不能用这一小组检查替代全域接收或正式验证。
'''
with (D/'README.md').open('x',encoding='utf8') as f:f.write(readme)
seal_path=(D/'output-seal.json').resolve()
members=[bind(p) for p in sorted(D.rglob('*')) if p.is_file() and p.resolve()!=seal_path]
assert all(Path(m['path']).resolve()!=seal_path for m in members)
inputs=pre['inputs']
write('output-seal.json',{'status':'sealed_three_historical_logs_mechanical_status_bridge_integration','at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'members':members,'inputs':inputs,'self_excluded':True,'records':pre['allowed_record_ids'],'check_calls_N':6,'matching_checks_N':6,'semantic_unit_RelationView_judge_actual_reading_log_calls_N':0,'full_domain_records_processed_N':0,'recovery_N':0,'retained_labels_N':0,'metrics_N':0})
for m in members+inputs: assert bind(m['path'])==m
print(json.dumps({'seal':bind(seal_path),'members_N':len(members),'inputs_N':len(inputs),'self_member_N':0,'checks_N':6,'all_readback_match':True},ensure_ascii=False))
