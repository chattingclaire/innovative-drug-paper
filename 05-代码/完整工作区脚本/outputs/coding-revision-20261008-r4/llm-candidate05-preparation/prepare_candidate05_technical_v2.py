"""Preserve v1; freeze v2 technical event/raw acceptance gate. No model call."""
import datetime
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bind(path):
    return {'path': str(Path(path).resolve()), 'sha256': sha(path)}


def save_new(path, content):
    if path.exists():
        assert path.read_text() == content, f'Frozen v2 file differs: {path}'
    else:
        path.write_text(content)


def main():
    original = HERE / 'candidate05_development_freeze.json'
    freeze = json.loads(original.read_text())
    for name in ['candidate05_prompt', 'exposed240_input', 'synthetic62_input', 'synthetic_expected_private']:
        assert sha(freeze[name]['path']) == freeze[name]['sha256']
    for name in ['validate_binary_output.py', 'output_schema_codex_compatible.json']:
        assert (HERE / 'runtime-v2' / name).read_bytes() == (HERE / 'runtime' / name).read_bytes()
    for bound in json.loads((HERE / 'candidate05_package_manifest.json').read_text())['files']:
        assert sha(bound['path']) == bound['sha256'], f'Original v1 package changed: {bound["path"]}'
    freeze['status'] = 'PREPARED_FROZEN_V2_TECHNICAL_GATE_NO_MODEL_CALLS_ROOT_EXECUTION_DECISION_PENDING'
    freeze['created_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    freeze['previous_v1_freeze_preserved'] = bind(original)
    freeze['previous_v1_package_preserved'] = bind(HERE / 'candidate05_package_manifest.json')
    freeze['runtime'] = {name: bind(HERE / 'runtime-v2' / name) for name in ['run_production_v32.py', 'validate_binary_output.py', 'output_schema_codex_compatible.json']}
    freeze['technical_version'] = 'candidate05-technical-v2-unique-completed-agent-message-raw-binding'
    freeze['acceptance_gate_addition'] = 'Before accepting a result, require exactly one item.completed agent_message, parse its JSON, compare type-preserving canonical JSON to raw_output JSON, and fail technically on count/parse/mismatch. Same-request technical retries only.'
    freeze['new_gate_audit_file'] = 'event_output_binding_audit.json, SHA bound in per-attempt metadata'
    freeze['semantic_prompt_input_schema_validator_changed_vs_v1'] = False
    freeze['actual_v2_model_calls'] = 0
    path = HERE / 'candidate05_development_freeze_v2.json'
    if path.exists():
        freeze['created_at'] = json.loads(path.read_text())['created_at']
    save_new(path, json.dumps(freeze, ensure_ascii=False, indent=2) + '\n')
    wrapper = (HERE / 'run_bounded_candidate05.py').read_text()
    wrapper = wrapper.replace('candidate05_package_manifest.json', 'candidate05_package_manifest_v2.json')
    wrapper = wrapper.replace('candidate05_development_freeze.json', 'candidate05_development_freeze_v2.json')
    wrapper = wrapper.replace("HERE / 'runtime/run_production_v32.py'", "HERE / 'runtime-v2/run_production_v32.py'")
    save_new(HERE / 'run_bounded_candidate05_v2.py', wrapper)
    print(json.dumps({'status': freeze['status'], 'freeze_v2': bind(path), 'model_calls': 0,
                      'prompt_schema_validator_input_unchanged': True}, ensure_ascii=False))


if __name__ == '__main__':
    main()
