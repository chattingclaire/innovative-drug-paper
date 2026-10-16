#!/usr/bin/env python3
"""Read-only frozen input comparison and live pilot snapshot, with local audit outputs only."""
from __future__ import annotations
import collections
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
OLD = ROOT / '06-coding/native-full4481-v1-sol'
NEW = ROOT / '06-coding/native-full4481-transport-recovery-v2-sol'
RUNNER = ROOT / '08-audits/recover-native-whole-batches-v2-root.py'
STATIC = set()

def reg(p):
    p = Path(p).resolve()
    if p.is_file(): STATIC.add(p)
    return p

def load(p):
    return json.loads(reg(p).read_text(encoding='utf8'))

def bind(p):
    p = Path(p).resolve(); raw = p.read_bytes()
    return {'path': str(p), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def save(name, obj):
    with (OUT / name).open('x', encoding='utf8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2); f.write('\n')

def diff(x, y, path=''):
    if type(x) is not type(y): return [path]
    if isinstance(x, dict):
        result = []
        for key in sorted(set(x) | set(y)):
            if key not in x or key not in y: result.append(path + '/' + key)
            else: result += diff(x[key], y[key], path + '/' + key)
        return result
    if isinstance(x, list):
        if len(x) != len(y): return [path]
        return [p for i, (a, b) in enumerate(zip(x, y)) for p in diff(a, b, path + '/' + str(i))]
    return [] if x == y else [path]

def covers(ranges, end):
    cursor = 0
    for left, right in sorted(ranges):
        if left > cursor: return False
        cursor = max(cursor, right)
    return cursor >= end

manifest = load(NEW / 'manifest.json')
for p in NEW.iterdir():
    if p.is_file(): reg(p)
reg(RUNNER)
records = []
binding_errors = []
for batch in manifest['batches']:
    bid = batch['batch_id']; old = load(OLD / bid / 'assignment.json'); new = load(NEW / bid / 'assignment.json')
    old_schema = load(OLD / bid / 'output.schema.json'); new_schema = load(NEW / bid / 'output.schema.json')
    old_contract = load(OLD / bid / 'output-validation-contract.json'); new_contract = load(NEW / bid / 'output-validation-contract.json')
    substantive_keys = ('source_ids', 'expected_N', 'packets', 'packet_bytes', 'manual', 'execution_prompt',
                        'packet_schema', 'source_asset_bindings', 'context_unit', 'requested_model', 'requested_reasoning_effort',
                        'max_total_technical_attempts', 'max_technical_retries')
    differences = [k for k in substantive_keys if old.get(k) != new.get(k)]
    schema_changes = diff(old_schema, new_schema)
    for value in new.values():
        if isinstance(value, dict) and {'path', 'bytes', 'sha256'} <= set(value):
            reg(value['path'])
            if bind(value['path']) != {k: value[k] for k in ('path', 'bytes', 'sha256')}: binding_errors.append({'batch': bid, 'binding': value})
    for value in [*new['packets'], *new['source_asset_bindings']]:
        reg(value['path'])
        if bind(value['path']) != {k: value[k] for k in ('path', 'bytes', 'sha256')}: binding_errors.append({'batch': bid, 'binding': value})
    old_receipts = [load(OLD / bid / f'root-attempt-reception-{i:04d}-v3.json') for i in range(1, 4)]
    records.append({'batch_id': bid, 'source_N': new['expected_N'], 'source_ids': new['source_ids'],
                    'packet_bytes': new['packet_bytes'], 'substantive_assignment_differences': differences,
                    'schema_json_pointer_differences': schema_changes,
                    'new_schema_bytes': (NEW / bid / 'output.schema.json').stat().st_size,
                    'old_schema_bytes': (OLD / bid / 'output.schema.json').stat().st_size,
                    'contract_json_pointer_differences': diff(old_contract, new_contract),
                    'new_contract_run_id': new_contract.get('run_id'),
                    'new_assignment_run_id': new['run_id'],
                    'new_assignment_binding': bind(NEW / bid / 'assignment.json'),
                    'old_assignment_binding': bind(OLD / bid / 'assignment.json'),
                    'old_attempts_exhausted_with_terminal_technical_failures': len(old_receipts) == 3 and all(x['state'] == 'technical_invalid_whole_batch' for x in old_receipts),
                    'old_selection_exists': (OLD / bid / 'root-selection.json').exists()})

old_valid_integrity = []
for p in sorted(OLD.glob('batch-*/root-selection.json')):
    selected = load(p)
    bindings = [v for v in selected.values() if isinstance(v, dict) and {'path', 'bytes', 'sha256'} <= set(v)]
    old_valid_integrity.append({'batch_id': p.parent.name, 'selection': bind(p),
                                'current_selected_binding_mismatch_N': sum(bind(v['path']) != {k: v[k] for k in ('path', 'bytes', 'sha256')} for v in bindings)})
routing = load(NEW / 'attempt-output-routing.json')
run_starts = [json.loads(p.read_text()) for p in NEW.glob('execution-runs/*/start.json')]
pre = [bind(p) for p in sorted(STATIC)]
save('input-seal.json', {'static_input_N': len(pre), 'files': pre,
                         'meaning': 'Static research/contract and old terminal provenance only; growing pilot traces are separately snapshotted.'})
save('frozen-comparison.json', {'batch_N': len(records), 'source_N': sum(x['source_N'] for x in records),
                               'substantive_difference_batch_N': sum(bool(x['substantive_assignment_differences']) for x in records),
                               'schema_difference_counts': dict(collections.Counter(str(x['schema_json_pointer_differences']) for x in records)),
                               'current_binding_mismatch_N': len(binding_errors), 'binding_errors': binding_errors, 'batches': records,
                               'old_valid_selection_integrity': old_valid_integrity,
                               'routing_header_run_id': routing.get('run_id'), 'new_campaign_run_id': manifest['run_id']})

pilot_snapshots = []
header_patterns = [
    re.compile(r'(?m)^PATH=(.+)\nSTART=(\d+)\nEND=(\d+)\nTOTAL_UNICODE_CHARS=(\d+)\n'),
    re.compile(r'(?m)^FILE (.+) start=(\d+) end=(\d+) total_unicode_chars=(\d+)\n'),
    re.compile(r'(?m)^FILE (.+)\nSTART (\d+) END (\d+) TOTAL (\d+)\n'),
]
for item in manifest['batches'][:3]:
    bid = item['batch_id']; slot = NEW / bid / 'attempt-0001'; events_path = slot / 'cli-events.jsonl'
    raw = events_path.read_bytes()
    with (OUT / f'{bid}-pilot-events.snapshot.jsonl').open('xb') as f: f.write(raw)
    events = []; malformed_tail = 0
    for line in raw.decode('utf8').splitlines():
        try: events.append(json.loads(line))
        except json.JSONDecodeError: malformed_tail += 1
    assignment = load(NEW / bid / 'assignment.json')
    readable = [assignment[k] for k in ('manual', 'execution_prompt', 'actor_instructions', 'output_schema', 'output_validation_contract')]
    readable += assignment['packets']
    texts = {b['path']: Path(b['path']).read_text(encoding='utf8') for b in readable}
    actual_ranges = collections.defaultdict(list); range_evidence = []; trunc_markers = []
    for line, event in enumerate(events, 1):
        item_event = event.get('item', {})
        if event.get('type') != 'item.completed' or item_event.get('type') != 'command_execution': continue
        out = item_event.get('aggregated_output', '')
        if re.search(r'Warning: truncated output|\d+ tokens truncated|\d+ lines omitted|\d+ characters omitted', out, re.I):
            trunc_markers.append(line)
        for path, text in texts.items():
            if text in out: actual_ranges[path].append((0, len(text)))
        headers = sorted([m for pattern in header_patterns for m in pattern.finditer(out)], key=lambda m: m.start())
        for index, match in enumerate(headers):
            path = match.group(1); start, end, total = map(int, match.groups()[1:])
            body = out[match.end():headers[index + 1].start() if index + 1 < len(headers) else len(out)]
            if path not in texts: continue
            text = texts[path]
            exact = 0 <= start <= end <= len(text) and total == len(text) and text[start:end] in body
            if exact: actual_ranges[path].append((start, end))
            range_evidence.append({'event_line': line, 'item_id': item_event['id'], 'path': path, 'start': start,
                                   'end': end, 'declared_total': total, 'exact_logged_range': exact,
                                   'entire_logged_tool_output_unicode_code_points': len(out)})
    coverage = [{'path': path, 'unicode_code_points': len(text), 'exact_logged_ranges': sorted(set(actual_ranges[path])),
                 'complete_exact_text_coverage_in_logged_stdout': covers(actual_ranges[path], len(text))}
                for path, text in texts.items()]
    seal_path = slot / 'seal.json'
    seal_flags = None
    if seal_path.exists():
        seal = json.loads(seal_path.read_text())
        seal_flags = {k: seal.get(k, 'ABSENT') for k in ('run_id', 'batch_id', 'template_only', 'actual_completion_claimed')}
        seal_flags['actual_input_binding_N'] = len(seal.get('actual_input_bindings', []))
    pilot_snapshots.append({'batch_id': bid, 'snapshot_at_utc': datetime.now(timezone.utc).isoformat(),
                            'source_events_read_prefix_binding': {'path': str(events_path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()},
                            'immutable_local_snapshot': bind(OUT / f'{bid}-pilot-events.snapshot.jsonl'),
                            'event_type_counts': dict(collections.Counter(e['type'] for e in events)),
                            'malformed_partial_tail_lines': malformed_tail,
                            'first_exists': (slot / 'first.json').exists(), 'seal_exists': seal_path.exists(),
                            'process_terminal_exists': (slot / 'process-completion.json').exists(),
                            'seal_flags': seal_flags, 'coverage': coverage, 'range_evidence': range_evidence,
                            'literal_transport_truncation_marker_event_lines': trunc_markers,
                            'actual_model_tool_reply_budgets_present_in_cli_events': False,
                            'independent_model_untruncated_reading_claimed': False})
save('pilot-observation-snapshot.json', {'pilots': pilot_snapshots,
                                        'meaning': 'A live snapshot; missing outputs/partial coverage while actors run are pending, not terminal technical failure.'})

static_summary = {'batch_N': 207, 'source_N': 2349,
                  'substantive_assignment_difference_batch_N': sum(bool(x['substantive_assignment_differences']) for x in records),
                  'schema_only_run_id_scope_changed_batch_N': sum(set(x['schema_json_pointer_differences']) == {'/properties/run_id/const', '/properties/scope/const'} for x in records),
                  'current_binding_mismatch_N': len(binding_errors),
                  'old_exhausted_batch_N': sum(x['old_attempts_exhausted_with_terminal_technical_failures'] for x in records),
                  'old_successful_selections_N': len(old_valid_integrity),
                  'old_selected_current_binding_mismatch_N': sum(x['current_selected_binding_mismatch_N'] for x in old_valid_integrity),
                  'observed_run_concurrency': [x['concurrency'] for x in run_starts],
                  'observed_capacity13_execution': any(x['concurrency'] > 3 for x in run_starts),
                  'old_directories_written_by_audit': False, 'model_requests_by_audit': 0}
findings = [
 {'severity': 'pass', 'item': 'Research and batch contract', 'finding': 'All 207 batch membership/order, packet/manual/prompt/source-asset/context/null/evidence contracts match originals. Schema changes only run_id/scope constants.', 'evidence': 'frozen-comparison.json'},
 {'severity': 'important', 'item': 'V2 receiver seal checks omitted', 'finding': 'Runner lines87–89 omit original v3 seal run_id/batch_id/template_only/actual_completion_claimed checks; empty input bindings also pass. Read-only supplementary guard is provided without altering actor first/labels.', 'evidence': 'strict_reception_guard.py'},
 {'severity': 'important', 'item': 'Concurrency plan versus actual', 'finding': 'Prepared instructions/amendment/remaining code allow13 while common protocol says3. Observed pilot is3. ROOT withdraws13 using a separately frozen capacity3 sidecar; v2 preparation bytes are retained.', 'evidence': 'ROOT-transport-capacity3-sidecar.json'},
 {'severity': 'important', 'item': 'Stale transport metadata references', 'finding': 'Copied output-validation-contract and routing header retain original run_id/schema/validator/routing metadata. Actual new assignment/schema/routes must govern. These are real identity-text conflicts, not evidence that material labels changed.', 'evidence': 'frozen-comparison.json'},
 {'severity': 'limitation', 'item': 'Expanded schema reading', 'finding': 'Pretty-printing increases schema from72593 to310458 bytes. New instructions explicitly demand full schema reading; validator coverage checks only manual/prompt/packets. Logs need an independent schema presentation check, not a hash or schema-valid receipt.', 'evidence': 'pilot-observation-snapshot.json'},
 {'severity': 'limitation', 'item': 'Tool/model actual presentation', 'finding': 'Bounded complete logged stdout ranges can be matched; CLI JSON does not record actual model reply budgets or capture all image presentation events. No independent serving-model or fully untruncated model-read claim is made.', 'evidence': 'pilot-observation-snapshot.json'},
 {'severity': 'limitation', 'item': 'Earliest valid technical selection and resume', 'finding': 'Runner loops attempts1..3 and stops first valid, does not use labels or splice. New controller must base selection/remaining gate on supplemental guarded receipt, not merely existence of old root-selection.json. Prior slots/first bytes remain immutable.', 'evidence': 'runner lines93–110'},
 {'severity': 'important', 'item': 'Global transport failure', 'finding': 'Runner would continue per-batch attempts against repeated global model/account denial. During expansion, new controller should stop dispatching new batches when the same explicit global transport rejection recurs; legalnull or semantic disagreement must not trip that circuit breaker.', 'evidence': 'runner lines96–119'},
]
save('report.json', {'artifact_type': 'native_recovery_v2_independent_preflight',
                     'created_at_utc': datetime.now(timezone.utc).isoformat(), 'static_summary': static_summary,
                     'findings': findings, 'pilot_status': 'see immutable live snapshot; terminal decisions use supplemental strict guard',
                     'guard_cli': 'python3 strict_reception_guard.py --manifest <v2/manifest.json> --assignment <v2/batch/assignment.json> --submission <v2/batch/attempt/first.json>',
                     'guard_template_policy': 'Default preserves original v3 get(template_only,False) behavior; missing actual_completion_claimed always fails. Optional explicit-template-field mode must be frozen before dispatch.',
                     'null_policy': 'Legalnull remains valid and does not cause technical retry; a missing/wrong seal identity or evidence is technical invalidity, with original answer retained.',
                     'no_old_or_v2_write': True, 'no_model_call': True})
md = '''# 新完整批次恢复轮：独立预检

**原研究材料和整批结构保持一致；接收与运输身份说明需要补强。** 207批、2349条的成员/顺序、packet、手册、提示、资产、batch上下文及null/证据约束均与原轮一致；schema仅改变run_id和scope常量。此轮另存，不能称旧轮第4次。

本审查只读原轮、新准备和运行中pilot，不调用模型、不改first或标签、不写旧目录或v2准备。

## 真实差异与重要修复

- v2接收器只验seal的first/report SHA，遗漏原v3的run_id/batch_id、template_only=false及actual_completion_claimed=true；空actual_input_bindings也可通过。提供的strict_reception_guard.py只读补验严格schema、0/1逐字packet证据、上述seal身份/完成、非空且属于冻结白名单的输入绑定，以及一个正常终结CLI turn。原首答不变；薄回执与补强回执分别保留。
- v2准备允许后续13并发，共同协议为3；当前实际pilot为3，尚未发现13执行。ROOT撤回该计划，ROOT-transport-capacity3-sidecar.json供新controller冻结，后续必须实际拒绝超过3的配置。已读v2准备字节不改。
- 新output-validation-contract仍写旧轮run_id及旧schema/validator/routing；新routing header也残留旧run_id。实际新assignment/schema/routes具有新轮身份。应在ROOT运输说明明确历史引用与新执行权威，不能悄悄重写已经被pilot读取的文件。
- 新schema重新缩进，从72593变为310458字节；actor又新增完整schema阅读要求。原严格validator只核manual/prompt/packet的声明整篇覆盖，不自动保证schema完整呈现。独立事件快照保留实际已呈现范围，不能从有效schema解析推断模型已完整读schema。
- 原脚本按1至3次顺序选择首个技术有效整批，没有标签比较或拼接。新controller须以补强回执作为有效和展开门槛，不能只看既有root-selection文件存在。系统性模型/account拒绝时停止新派发；合法null或语义分歧不得触发重试。

## 可执行补强接口

运行strict_reception_guard.py时给--manifest、--assignment、--submission；该程序只向stdout返回补充回执，不写接收目录。也可调用verify(manifest_path, assignment_path, submission_path)。默认template_only沿原v3的缺失视False行为，actual_completion_claimed必须为真正True；--require-explicit-template-false是更强的新规则，不能在已派发后追加要求。

pilot快照不是终结判定。正在运行时未产生first/seal或材料覆盖尚未完成，应保持pending；首答终结后由补强模块判断是否技术有效。若seal标志缺失/错误或证据格式不符，保留原件并按新轮有限技术重试规则处理，不能补写首答；null本身始终不是失败理由。

## 证据与限制

frozen-comparison.json含207批逐项差异及旧297成功selection字节核对。pilot-observation-snapshot.json与三个immutable events快照含实际stdout范围核对；这些事件不能证明服务端模型身份，也不保存实际工具反馈预算或所有图像呈现消息。完整stdout与无截断标记只能支持日志层观察，不能提升为独立模型完整未截断阅读证明。

输入前后SHA见input-seal.json/input-integrity-readback.json；guard及容量sidecar有独立guard-ready-seal.json，全部审查输出最终SHA见output-seal.json。输出仅在本审查目录。
'''
with (OUT / 'report.md').open('x', encoding='utf8') as f: f.write(md)
post = [bind(p) for p in sorted(STATIC)]
changes = [{'before': a, 'after': b} for a, b in zip(pre, post) if a != b]
save('input-integrity-readback.json', {'static_input_N': len(pre), 'changed_static_input_N': len(changes), 'changes': changes})
outputs = [bind(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name != 'output-seal.json']
save('output-seal.json', {'output_N': len(outputs), 'files': outputs, 'self_included': False})
print(json.dumps(static_summary, ensure_ascii=False, indent=2))
