"""Dispatch one frozen batch in a new CLI context; never inspect label accuracy."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
RUN = ROOT / '06-coding/native-full4481-v1-sol'

def binding(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())

def save(path, obj):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch', type=int, required=True)
    parser.add_argument('--attempt', type=int, choices=(1, 2, 3), default=1)
    args = parser.parse_args()
    profile_path = HERE / 'CLI-execution-profile-amendment.json'
    profile = json.loads(profile_path.read_text())
    assert profile['status'] == 'frozen_before_first_CLI_coding_dispatch'
    assert 2 <= args.batch <= 504
    assert binding(Path(__file__)) == profile['dispatcher']
    for item in profile['executable_bindings']:
        assert binding(item['path']) == item
    batch = RUN / f'batch-{args.batch:04d}'
    selected = batch / 'root-selection.json'
    assert not selected.exists(), 'Already selected: never dispatch another response.'
    for earlier in range(1, args.attempt):
        receipt = json.loads((batch / f'root-attempt-reception-{earlier:04d}-v3.json').read_text())
        assert receipt['state'] == 'technical_invalid_whole_batch'
    scope = next(x for x in profile['batch_dispatch_bindings'] if x['batch_number'] == args.batch)
    assert binding(batch / 'assignment.json') == scope['assignment']
    assert binding(batch / 'dispatch-request.txt') == scope['original_fixed_core_dispatch_request']
    overlay_path = HERE / 'CLI-procedural-context-overlay.txt'
    assert binding(overlay_path) == profile['procedural_overlay']
    slot = batch / f'attempt-{args.attempt:04d}'
    slot.mkdir(exist_ok=True)
    assert not list(slot.iterdir()), 'Actual attempt slot must be empty.'
    logical = f'native_full4481v1_b{args.batch:04d}_a{args.attempt:02d}'
    # Routing metadata is explicit and separate from the frozen substantive request.
    metadata = {'logical_dispatch_label': logical, 'attempt_number': args.attempt,
                'own_output_slot': str(slot), 'execution_transport': 'fresh_codex_cli_exec'}
    prompt = (overlay_path.read_text() + '\n' +
              (batch / 'dispatch-request.txt').read_text() + '\n' +
              '请求外操作元数据（逻辑派发标签不是collaboration代理身份）：\n' +
              json.dumps(metadata, ensure_ascii=False) + '\n')
    prompt_path = slot / 'ROOT-cli-dispatch-prompt.txt'
    with prompt_path.open('x', encoding='utf-8') as stream:
        stream.write(prompt)
    cli = Path(profile['cli_launcher'])
    command = [str(cli), 'exec', '--ignore-user-config', '--skip-git-repo-check',
               '--ephemeral', '--json', '--color', 'never', '-C', str(slot),
               '--model', 'gpt-6.1-sol', '-c', 'model_reasoning_effort="ultra"',
               '-c', 'approval_policy="never"', '--sandbox', 'workspace-write',
               '-c', 'features.multi_agent=false', '-c', 'features.memories=false',
               '-c', 'web_search="disabled"', '-c', 'project_doc_max_bytes=0',
               '--output-last-message', str(slot / 'ROOT-cli-final-message.txt'), '-']
    save(slot / 'ROOT-cli-dispatch-start.json', {
        'status': 'actual_cli_process_about_to_start', 'created_at_utc': now(),
        'profile': binding(profile_path), 'assignment': scope['assignment'],
        'prompt': binding(prompt_path), 'original_fixed_core': scope['original_fixed_core_dispatch_request'],
        'metadata': metadata, 'argv': command, 'resumed_or_inherited_conversation': False,
        'provider_wire_or_independently_verified_serving_model_claimed': False,
    })
    out_path, err_path = slot / 'ROOT-cli-events.jsonl', slot / 'ROOT-cli-stderr.txt'
    with out_path.open('xb') as out_stream, err_path.open('xb') as err_stream:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=out_stream,
                                   stderr=err_stream, cwd=slot)
        process.communicate(prompt.encode('utf-8'))
    thread_ids = []
    counts = {}
    for line in out_path.read_text(errors='replace').splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind = item.get('type', 'unknown')
        counts[kind] = counts.get(kind, 0) + 1
        if kind == 'thread.started':
            thread_ids.append(item.get('thread_id'))
    receipt = {'status': 'actual_cli_process_terminal', 'created_at_utc': now(),
               'returncode': process.returncode, 'actual_cli_thread_ids': thread_ids,
               'event_type_counts': counts, 'requested_model': 'gpt-6.1-sol',
               'requested_reasoning_effort': 'ultra', 'context_unit': 'batch',
               'logical_dispatch_label': logical, 'collaboration_agent_identity_claimed': False,
               'raw_cli_events': binding(out_path), 'stderr': binding(err_path),
               'first_file_exists': (slot / 'first.json').exists(),
               'accuracy_compared': False, 'technical_reception_pending': True}
    save(slot / 'ROOT-cli-process-completion.json', receipt)
    print(json.dumps({k: receipt[k] for k in ('status', 'returncode', 'actual_cli_thread_ids',
                                             'first_file_exists')}, ensure_ascii=False))
    return 0

if __name__ == '__main__':
    sys.exit(main())
