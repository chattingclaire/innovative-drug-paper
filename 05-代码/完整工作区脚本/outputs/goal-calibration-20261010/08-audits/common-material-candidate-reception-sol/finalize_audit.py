#!/usr/bin/env python3
"""Seal independent outputs; check inputs stayed exact without running a judge."""
import datetime
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
CAND = ROOT / '03-manual/common-material-projection-candidate-root'


def load(path):
    return json.loads(Path(path).read_bytes())


def bind(path):
    p = Path(path).resolve()
    raw = p.read_bytes()
    return {'path': str(p), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def write(name, value):
    with (OUT / name).open('x', encoding='utf8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


mechanical = load(OUT / 'mechanical-summary.json')
budget = load(OUT / 'compact-budget-summary.json')
finite = load(OUT / 'finite-interface-readback.json')
input_bindings = load(OUT / 'audited-input-bindings.json')['files']
input_bindings += [finite['algorithm_bindings'], *finite['actual_imported_modules']]
for item in input_bindings:
    assert bind(item['path']) == item, item['path']
assert len(load(OUT / 'all4481-reception-checks.json')) == 4481
assert len(load(OUT / 'all4481-compact-byte-measures.json')) == 4481
assert len(load(OUT / '17-original-copy-map-checks.json')) == 17
assert len(load(OUT / 'old504-assignment-budget-impact.json')) == 504
assert finite['source_packets_N'] == 5 and finite['relation_views_N'] == 3
assert finite['quotation_checks'] == 7
assert all(x['matches_exact_supplied_context'] and x['quote_matches_actual_copied_original']
           for x in load(OUT / 'finite-relation-quote-matches.json'))
assert any(x.get('cited_standard_stop_still_present') for x in finite['relations'])
assert all(x['no_old_or_candidate_files_modified'] for x in [finite])
report = {
    'status': 'independent_candidate_reception_and_budget_audit_complete_preparation_only',
    'candidate_seal_binding': bind(CAND / 'output-seal.json'),
    'shared_inventory_binding': bind(CAND / 'packet-inventory.json'),
    'mechanical_result': mechanical,
    'budget_result': budget,
    'finite_interface_result': {
        'actual_source_packets': [x['source_id'] for x in finite['cases']],
        'RelationView_source_ids': [x['source_id'] for x in finite['relations']],
        'old_frozen_consumers': finite['actual_imported_modules'],
        'literal_quote_and_locator_matches': 7,
        'A271_closed59_62_support_quotes': 7,
        'two_siblings_do_not_inherit_this_bounded_support': True,
        'A271_old_cited_standard_dependency_still_stopped': True,
        'dimension_decisions_produced': 0},
    'findings': [
        {'kind': 'passed_material_preparation_integrity',
         'description': '全4481当前源记录、旧资源前缀和未改变字段与父包相等；候选完整source_bundle及新封装逐条等于已审中性投影。1227缺失字面连续范围来自17份已绑定UTF8原件，字符/字节/物理行/全文与范围SHA全核对。'},
        {'kind': 'passed_equal_visibility_preparation',
         'description': '人工A/B、规则、LLM、裁定参照五入口声明绑定同一实际inventory；只准备，没有独立执行、正式裁定、结果或实际角色交付的认证。'},
        {'kind': 'passed_separate_portable_map',
         'description': '17复制件和原件逐字节相等；相对复制路径在候选根内精确解析，新增locator仍保留原snapshot/原档路径和位置。跨机器消费者必须显式按map解析；本审查未在另一机器测试加载，不改写locator。'},
        {'kind': 'budget_old_assignments_need_future_rebuild',
         'description': '按原紧凑整包+LF口径，候选最大245379B，无单条超260000；旧504分配若沿用则106组超限。同原上限/顺序的纯计量模拟为659组。材料变化放在原封装的反事实分解为655组，非已选定生产契约。未创建任何新批次。'},
        {'kind': 'consumer_stop_not_resolved_by_availability',
         'description': 'A271在实际新包中可见同版§59–62资格/具体支持/终止原文，旧关系接口形成有限支持引用；旧cited_standard仍stopped。不得称旧NULL已解决，亦未执行维度判读。'}],
    'actual_reading': {
        'all4481_and17_originals': '机械字节/SHA/JSON/range核验，不声称4481条或17整篇逐条语义阅读。',
        'semantic_source_reading': '5个当前命题；NMPA注册管理办法同版连续L197–208（§59–62及下一节标题），边界邻接L209–214。',
        'code_and_contract_reading': '当前准备脚本、中性投影源、原生产准备器紧凑序列化/分组口径、来源适配与关系/引文接口及其封存绑定。',
        'finite_machine_consumption': 'SourcePacket与来源inventory各5对旧/新包；RelationView只3个新包；7个有限引用匹配。完整材料加载不等于人已读完或可跨条款继承。'},
    'scope_limits': {
        'main_LLM_or_rule_judge_called': False,
        'main_partial_or_owner800_replay_labels_read': False,
        'neutral_projection_applied_to_old_inputs': False,
        'old_manual_predictions_packets_or_candidate_written': False,
        'human_results_created_or_certified': False,
        'new_model_dispatch_or_assigned_batch_files_created': False,
        'final_common_release_adopted_by_this_audit': False,
        'formal_accuracy_or_validation_conclusion': False,
        'new_statistics_methods_or_thresholds': False},
    'future_scope': 'ROOT可据完整性/可移植映射/紧凑预算及消费者停止现状决定另建未来共同材料release。旧主版本、77/200/AI800不得追认成该候选。'}
write('report.json', report)
write('execution-notes.json', {
    'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'mechanical_script_runs': 1, 'finite_interface_script_runs': 1,
    'audit_check_failure_N': 0,
    'exploratory_read_notes': [
        '文件清单/宽泛metadata读取曾因输出量大而截断，未据此声称读完；随后使用精确文件和机器全量绑定核验。',
        '原准备目录探索时请求不存在packet-inventory.json，得到FileNotFoundError；随后按已读准备器使用实际packet-bindings.json。未修改原目录。'],
    'input_bindings_unchanged_at_final_readback': True,
    'verified_input_bindings_with_duplicates_N': len(input_bindings),
    'no_classification_no_dispatch_no_new_Codex_CLI': True})
text = '''本独立审查完成共同材料候选的机械接收与有限接口核验，候选仍为准备状态。

4481条新包源记录、旧资源前缀、所有未改变字段和完整中性投影/包封装逐条一致。1227条补入1227个同版字面连续范围；3254条材料内容不变。17份原UTF8与复制件SHA、字节、映射相等。人工A/B、规则、LLM和裁定参照均绑定同一inventory，无实际交付或人类执行认证。旧手册/预测/包与候选未改。

预算使用原prepare-full4481.py的紧凑整包UTF8+一个LF。原总77905594B、最大244813B；候选紧凑总123466714B、最大245379B，无单条超260000。漂亮文件最大387254B不是该预算口径。旧504组若直接沿用，106组超限；只按原上限和冻结顺序计量模拟659组，未创建或派发新批次。原封装只换材料的反事实分解为655组，未采纳为未来执行契约。核心指令及外部资源按原准备器另计，260000B不是token/context认证。

实际读取范围：全4481/17原件完成机械JSON/SHA/range核验，不称全部语义阅读；语义读5个当前命题和同版注册管理办法§59–62连续文字及相邻标题/开头。SourcePacket/库存有限5包，旧封存RelationView仅3包，7个引文字符/字节/行位置精确匹配。A271新增可见同版§59资格和§61支持，引用限§59–62；§60提交及相邻附条件条款没有继承该支持关系。旧cited_standard仍stopped，没有dimensions/judge结果，不能把可见补足称旧NULL解除。

report.json是结论与边界；all4481-reception-checks.json逐条机械凭据；17-original-copy-map-checks.json原件映射；all4481-compact-byte-measures.json/old504-assignment-budget-impact.json/compact-budget-summary.json真实紧凑预算；finite-interface-readback.json/finite-relation-quote-matches.json保留有限接口及精确引文；audited-input-bindings.json与output-seal.json提供输入/输出封存。

ROOT可据此决定未来另冻共同材料release及其分组/消费者入口。没有改旧主运行、77/200/AI800材料；没有读取主LLM部分标签、所有者800回放标签；没有生成真人结果、正式准确率或派发模型任务。相对copy map保留原来源定位，但另一机器的实际解析/交付尚未测试。
'''
with (OUT / 'README.txt').open('x', encoding='utf8') as stream:
    stream.write(text)
members = [bind(p) for p in sorted(OUT.iterdir()) if p.is_file()]
write('output-seal.json', {
    'status': 'sealed_independent_preparation_reception_audit_not_release',
    'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'output_members': members, 'candidate_input_seal': bind(CAND / 'output-seal.json'),
    'shared_inventory': bind(CAND / 'packet-inventory.json'),
    'manual_binding': bind(CAND / 'manual.txt'), 'self_excluded': True})
for member in members:
    assert bind(member['path']) == member
print(json.dumps({'seal': bind(OUT / 'output-seal.json'), 'output_member_N': len(members),
                  'all_output_members_match': True, 'all_input_bindings_unchanged': True},
                 ensure_ascii=False))
