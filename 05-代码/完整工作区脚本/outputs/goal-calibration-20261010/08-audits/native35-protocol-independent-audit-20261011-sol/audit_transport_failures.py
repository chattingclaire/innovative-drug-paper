#!/usr/bin/env python3
"""Extend the read-only audit with old terminal transport failures and a proposed interface.

No dispatcher/validator/model is executed; only this audit directory receives new files.
"""
import collections
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
OLD = ROOT / '06-coding/native-full4481-v1-sol'
NEW = ROOT / '06-coding/native-reference77-coverage-recovery-v1-sol'
PROFILE = ROOT / '06-coding/full4481-fresh-cli-dispatch-root/CLI-execution-profile-amendment.json'
INPUTS = set()

def load(p):
    p = p.resolve()
    INPUTS.add(p)
    return json.loads(p.read_text(encoding='utf8'))

def binding(p):
    p = p.resolve()
    raw = p.read_bytes()
    return {'path': str(p), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def save(name, x):
    with (OUT / name).open('x', encoding='utf8') as f:
        json.dump(x, f, ensure_ascii=False, indent=2)
        f.write('\n')

for p in (ROOT / '06-coding/full4481-fresh-cli-dispatch-root').glob('*'):
    if p.is_file():
        INPUTS.add(p.resolve())
for p in (ROOT / '06-coding/full4481-native-execution-adapter-sol/root-validator-amendment-01').glob('*'):
    if p.is_file():
        INPUTS.add(p.resolve())
profile = load(PROFILE)
new_manifest = load(NEW / 'manifest.json')
failed = []
attempts = []
for directory in sorted(OLD.glob('batch-*')):
    receipts = sorted(directory.glob('root-attempt-reception-*-v3.json'))
    # Read terminal receipts to establish the originally exhausted scope. No labels are read.
    rs = [(p, load(p)) for p in receipts]
    if len(rs) == 3 and not (directory / 'first.json').exists():
        assignment = load(directory / 'assignment.json')
        failed.append({'batch_id': assignment['batch_id'], 'source_N': assignment['expected_N'],
                       'source_ids': assignment['source_ids'], 'original_assignment_binding': binding(directory / 'assignment.json')})
        for p, receipt in rs:
            slot = directory / ('attempt-' + str(receipt['attempt_number']).zfill(4))
            for name in ('ROOT-cli-events.jsonl', 'ROOT-cli-process-completion.json', 'ROOT-cli-dispatch-start.json',
                         'ROOT-cli-stderr.txt', 'ROOT-cli-dispatch-prompt.txt'):
                if (slot / name).is_file():
                    INPUTS.add((slot / name).resolve())
            completion = load(slot / 'ROOT-cli-process-completion.json')
            start = load(slot / 'ROOT-cli-dispatch-start.json')
            events = [json.loads(x) for x in (slot / 'ROOT-cli-events.jsonl').read_text().splitlines()]
            error = receipt.get('error', {})
            message = error.get('message', '')
            category = 'missing seal.json' if error.get('type') == 'FileNotFoundError' and 'seal.json' in message else error.get('type', '') + ': ' + message
            rejected = any("model is not supported when using Codex with a ChatGPT account" in json.dumps(e) for e in events)
            attempts.append({'batch_id': directory.name, 'attempt_number': receipt['attempt_number'],
                             'returncode': completion['returncode'], 'receiver_category': category,
                             'explicit_model_not_supported_error': rejected,
                             'turn_failed': any(e['type'] == 'turn.failed' for e in events),
                             'turn_completed': any(e['type'] == 'turn.completed' for e in events),
                             'launcher': start['argv'][0], 'profile_binding': start['profile']})
assert len(failed) == 207 and len(attempts) == 621
new_start = [load(NEW / 'cases' / sid / 'attempt-0001/dispatch-start.json') for sid in new_manifest['source_ids']]
new_terminal = [load(NEW / 'cases' / sid / 'attempt-0001/terminal.json') for sid in new_manifest['source_ids']]
for b in profile['executable_bindings']:
    INPUTS.add(Path(b['path']).resolve())
pre = [binding(p) for p in sorted(INPUTS)]
save('transport-input-seal.json', {'input_N': len(pre), 'files': pre})

summary = {'failed_original_batch_N': len(failed), 'failed_original_source_N': sum(x['source_N'] for x in failed),
           'exhausted_attempt_N': len(attempts),
           'receiver_error_counts': dict(collections.Counter(x['receiver_category'] for x in attempts)),
           'process_returncode_counts': dict(collections.Counter(str(x['returncode']) for x in attempts)),
           'attempts_with_explicit_model_not_supported_error_N': sum(x['explicit_model_not_supported_error'] for x in attempts),
           'turn_failed_attempt_N': sum(x['turn_failed'] for x in attempts),
           'turn_completed_attempt_N': sum(x['turn_completed'] for x in attempts),
           'latest35_returncode_zero_N': sum(x['returncode'] == 0 for x in new_terminal),
           'old_launcher_paths': sorted(set(x['launcher'] for x in attempts)),
           'new_launcher_paths': sorted(set(x['argv'][0] for x in new_start)),
           'same_explicit_launcher_path_across_old_and_new': set(x['launcher'] for x in attempts) == set(x['argv'][0] for x in new_start),
           'old_profile_cli_launcher': profile['cli_launcher'],
           'old_and_new_declared_launcher_sha_equal': next(x['sha256'] for x in profile['executable_bindings'] if x['path'].endswith('/@openai/codex/bin/codex.js')) == new_manifest['shared']['cli_launcher']['sha256'],
           'causal_claim_cli_upgrade_fixed_failure': 'not established; old and new provenance already name the same explicit launcher path and hash',
           'independently_verified_serving_model_identity': False}

proposal = {
 'status': 'proposal_only_not_instantiated_or_executed',
 'objective': 'Complete the 207 exhausted original batches using an explicitly new transport-recovery campaign, with unchanged research inputs and whole-batch coding contract.',
 'recovery_campaign_id_example': 'native-full4481-batch-transport-recovery-v2-sol',
 'original_contract_run_id': 'native-full4481-v1-sol',
 'scope': 'Exactly the 207 terminal exhausted whole batches, in original batch order, 2349 source records; no label-based subset and no use of the 35 single-source outputs as batch components.',
 'old_attempt_policy': 'Original attempts 1..3 and technical failure receipts stay unchanged. New recovery attempts are numbered within the new campaign, never called original attempt 4.',
 'frozen_research_contract': ['Exact original manual and execution-prompt bytes.',
                              'Exact original 207 batch assignment bytes, source order and packet/source-asset bindings.',
                              'Original context_unit=batch, static <=12 / 260000-byte grouping and output schema.',
                              'Every 0/1 has exact packet pointer/quote/current-or-context role evidence; necessary original-source assets carry path/SHA/page and actual read receipt.',
                              'Actual bounded untruncated manual/prompt/all batch packet reading plus needed limited contexts/assets; no load/hash substitution.',
                              'No reference labels, metrics, other predictions, prior attempt or 35-row recovery read by coding actors.'],
 'transport_amendment_only': ['Freeze a new campaign envelope and immutable original-batch-to-new-slot routing map before first coding.',
                             'Continue the explicit launcher/model/effort argv currently observed to return successful complete turns; bind launcher, platform binary, package lock and procedural overlay.',
                             'Supersede only the original task-label/attempt-output routing with the new campaign logical label and new directory; retain original files read-only.',
                             'Retain original schema run/batch/scope constants as source-contract identity inside first.json, and add an external execution envelope that clearly identifies the new campaign. Never treat those inner constants as proof of an old attempt.',
                             'A new strict receiver allows only the prebound new slot for the exact original assignment; all original schema, type, order, quote, read coverage and seal checks remain.',
                             'The only validator filesystem condition needing mechanical adaptation is submission-path containment under the new frozen route; original assignment directory and all input hash checks stay unchanged.'],
 'interface': {
   'dispatcher_example': 'new_dispatcher --recovery-manifest <new sealed manifest> --original-assignment <frozen original batch assignment> --recovery-attempt 1',
   'dispatcher_effect': 'Fresh non-resumed ephemeral codex exec context, original frozen core request plus routing-only overlay, one full-batch first/report/seal in a new slot.',
   'cli_argv_template': [profile['cli_launcher'], 'exec', '--ignore-user-config', '--skip-git-repo-check', '--ephemeral', '--json', '--color', 'never', '-C', '<new bound slot>', '--model', 'gpt-6.1-sol', '-c', 'model_reasoning_effort="ultra"', '-c', 'approval_policy="never"', '--sandbox', 'workspace-write', '-c', 'features.multi_agent=false', '-c', 'features.memories=false', '-c', 'web_search="disabled"', '-c', 'project_doc_max_bytes=0', '--output-last-message', '<new bound slot>/final-message.txt', '-'],
   'receiver_example': 'new_strict_receiver --recovery-manifest <new sealed manifest> --original-assignment <frozen original assignment> --submission <new bound slot>/first.json --actor-completed',
   'required_receipt_fields': ['recovery_campaign_id', 'source_contract_run_id', 'original_batch_id', 'original_assignment_sha256', 'recovery_attempt_number', 'actual_cli_thread_id', 'original_schema_sha256', 'strict_validation', 'first/report/seal bindings', 'original_attempts_preserved', 'no_cross_attempt_or_cross_record_splicing'],
   'validation_rule': 'Strict JSON parsing; exact integer/null labels; original top constants, full record order/coverage and packet identities; exact packet string quotes; permitted source asset binding; real bounded read_manifest; exclusive first/report/seal hashes. Earliest complete technically valid whole-batch only.',
   'selection_destination': 'Canonical first mirror and selection receipt in the new campaign only; original canonical batch paths are never written.'},
 'launch_gate': ['Before expansion, take the first failed batch in deterministic original order as a whole-batch transport/strict-reception gate.',
                 'A fresh complete turn alone is insufficient: expand only after strict schema/read/quote/seal reception for that entire batch.',
                 'If server again explicitly rejects the model/account route, stop launching downstream batches and record campaign transport blockage; do not burn all per-batch attempts against the same global denial.',
                 'Actual available CLI events must preserve a full bounded-read receipt; for image tools absent from CLI JSON, preserve attributable actual image presentation evidence or keep verification unproven.'],
 'concurrency_and_retries': 'At most 3 concurrent coding batches; begin with 1 deterministic gate. New campaign first plus at most 2 fresh whole-batch technical retries under a frozen new policy; semantic disagreement/null never retries.',
 'read_transport_guidance': 'Print bounded chunks with explicit source path/start/end and readable end markers, small enough for the actual tool reply budget (e.g. <=4000 Unicode characters with sufficient output budget). Record the actual received range/event after seeing the untruncated reply, not a prefilled entire-file declaration.',
 'aggregate_interpretation': 'After success, total 4481 coverage would combine 297 original accepted batches with 207 separately identified recovered batches. Report the phase difference; it is not an uninterrupted original first-pass campaign, independent repeat, or proof of validity.',
 'no_action_in_this_audit': 'No new recovery campaign, dispatcher, slots or model requests were created; interfaces above are nonexecuted proposals.'}
save('transport-repair-audit.json', {'artifact_type': 'native_full4481_transport_repair_independent_addendum',
                                   'created_at_utc': datetime.now(timezone.utc).isoformat(),
                                   'observed_failure_summary': summary, 'proposed_minimal_recovery_contract': proposal,
                                   'fixed_failed_batch_scope': failed})

old_runner = ROOT / '06-coding/full4481-fresh-cli-dispatch-root/run_one_cli_batch.py'
adapter = ROOT / '06-coding/full4481-native-execution-adapter-sol/root-validator-amendment-01/receive_full4481_batch_v3.py'
text = f'''# 全量LLM缺失部分的最小运输恢复合同（只读审计补充）

**旧207批已经耗尽每批3次；恢复必须另开有明确身份的新运输恢复轮，不能冒称原协议内第4次。** 覆盖原既定207个完整batch、2349条，保留原批次顺序、手册、执行提示、packet与必要资产、严格schema、实际读取和逐字证据。此次未建立或执行新恢复轮。

## 已查明的失败主因

| 旧207失败批次内的621次尝试 | 次数 |
|---|---:|
| CLI明确报模型不支持ChatGPT账户，returncode=1；接收器因缺seal报错 | 615 |
| returncode=0，Packet exact quote mismatch | 1 |
| returncode=0，KeyError bytes | 2 |
| returncode=0，KeyError source_record | 3 |

615次原始error/turn.failed明确为“gpt-6.1-sol model is not supported when using Codex with a ChatGPT account”。这是接收前的服务请求拒绝，不能把missing seal.json当成仅需放宽封存检查的格式问题。另6次才是已经完成CLI turn后出现的技术输出/结构问题。旧原件、失败及任何不完整first都要保留。

身份归因须谨慎：旧[CLI冻结profile]({PROFILE}:1)与旧dispatch-start实际argv[0]，已经都指向isolated-codex-cli-0.162.1-root；其显式launcher SHA与35条新补跑manifest相同。新35条全部returncode=0表明该显式请求路径后来可返回完整turn，**没有证明CLI版本更换导致恢复，也没有解释服务端许可为什么变化**。不能改成别的默认模型后仍声称同模型。

## 最小恢复接口

1. 先冻结新campaign envelope及207原batch→新slot映射。旧assignment/手册/prompt/schema/资产不修改，旧attempt与canonical不写入；首答内部继续用原schema的contract run/batch/scope常量，外围真实执行回执明确recovery_campaign_id和source_contract_run_id，避免把常量冒充旧执行身份。
2. 将[原CLI派发器]({old_runner}:39)的读取及模型请求方式复用到新路由：完整既定batch、fresh ephemeral exec、gpt-6.1-sol/ultra、禁用用户配置/记忆/网页/代理。只机械替换逻辑标签与输出slot；原core request及实质prompt保持字节。绑定当前已成功运输的launcher、平台binary、package lock和routing overlay。
3. 采用新ROOT运输接收适配层，引用既有[v3严格接收器]({adapter}:1)及严格validator的约束。最小改动只有“submission必须位于原batch目录”改成“必须等于新恢复route map绑定slot”。原assignment路径合法性、schema、run/batch常量、严格JSON、整数类型、完整records次序/coverage、packet身份、逐字quote、允许资产、实际read_manifest、first/report/seal SHA均保留。不得用35条薄接收器，不准拆条拼批或在首答后修补缺证据。
4. 先执行原顺序第一个失败batch的整批运输及严格接收门槛，最多1并发。完整turn加35条薄接收器的历史成功不是整批通过；该完整batch只有在实读、证据、schema和封存均通过后才扩展到其余batch，总并发最多3。若模型/account再次系统性拒绝，立即停止新增派发，记录运输阻塞，避免继续消耗全部批次次数。
5. 读取应采用与实际工具输出预算相容的小段（例如最多4000 Unicode字符），显示路径和明确首尾区间；收到完整工具回复后才记录真正read_manifest。必要图像要有可归属实际查看记录；若CLI JSON不保存图像消息，保留额外真实呈现回执，不能仅复制packet的verified或SHA作为已读证明。
6. 新恢复轮每批首次加最多2次真正fresh整批技术重试；只选最早完整技术有效整批，保留所有失败和原字节。canonical与selection只写新恢复轮。结果可使297原成功batch与207恢复batch共同覆盖4481，但报告必须披露阶段与运输差异，不能叫原首次主运行从未失败或独立重复。

建议的接口是：new_dispatcher --recovery-manifest <新冻结清单> --original-assignment <原完整batch assignment> --recovery-attempt 1；new_strict_receiver --recovery-manifest <新冻结清单> --original-assignment <原assignment> --submission <新slot>/first.json --actor-completed。完整参数清单、必要回执字段和不可执行的合同提案见transport-repair-audit.json；它不是已经创建的命令或已经获得的完成回执。

本补充只读所有旧v3回执及207失败批的执行轨迹，未读取标签作语义比较、未重编码、未改旧目录。附加输入前后SHA见transport-input-seal.json和transport-input-integrity-readback.json；所有审查输出的最终SHA见final-output-seal.json。
'''
with (OUT / 'transport-repair-audit.md').open('x', encoding='utf8') as f:
    f.write(text)
post = [binding(Path(x['path'])) for x in pre]
changes = [{'before': old, 'after': new} for old, new in zip(pre, post) if old != new]
save('transport-input-integrity-readback.json', {'input_N': len(pre), 'changed_input_N': len(changes), 'changes': changes})
outputs = [binding(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name != 'final-output-seal.json']
save('final-output-seal.json', {'at_utc': datetime.now(timezone.utc).isoformat(), 'output_N': len(outputs),
                               'files': outputs, 'self_hash_included': False,
                               'original_inputs_written': False, 'model_requests_made': 0})
print(json.dumps(summary, ensure_ascii=False, indent=2))
