"""Only the three predeclared purpose controls, no actual fixture/reference."""
import json
import sys
import hashlib
import importlib.util
from pathlib import Path
from relations import RelationView
from dimensions import judge

d = json.loads(Path(__file__).with_name('v09-purpose-branch-predeclaration.json').read_text())
results = []
revision = json.loads(Path(__file__).with_name('purpose-control-input-revision-v09.json').read_text())
for c in d['purpose_controls']:
    if c['name'] == 'independent_trial_approval_support_action_before_enactment':
        payload = Path(__file__).with_name(revision['positive_revised_input']).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == revision['positive_input_sha256']
        reader = Path(revision['old_reader_path'])
        assert hashlib.sha256(reader.read_bytes()).hexdigest() == revision['old_reader_sha256']
        spec = importlib.util.spec_from_file_location('frozen_v12_control_reader', reader)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        unit = module.semantic_unit(json.loads(payload))
    else:
        unit = {'text': c['text'], 'contexts': []}
    view = RelationView(unit)
    decisions = judge(view)
    actual = {key: value['value'] for key, value in decisions.items()}
    results.append(dict(c, actual_input_text=unit['text'], actual=actual, passed=actual == c['expected'],
        decisions=decisions, relation_traces=view.traces(), source_view_events=view.source_view_events))
r = {'controls': results, 'passed': sum(c['passed'] for c in results), 'failed': sum(not c['passed'] for c in results)}
print(json.dumps(r, ensure_ascii=False, indent=2))
sys.exit(0 if not r['failed'] else 1)
