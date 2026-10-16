"""Finite source-copy extension; all original adapters/bridge/engine stay intact."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
ROOT = HERE.parent.parent
OLD = ROOT / '05-validation/formal800-xlsx-reception-adapter-sol'
BRIDGE = ROOT / '07-statistics/formal800-v15-statistics-input-bridge-sol'


def binding(p):
    raw = p.read_bytes()
    return {'path': str(p.resolve()), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


dependencies = {name: binding(path) for name, path in {
    'original_adapter': OLD / 'adapter.py', 'original_bindings': OLD / 'bindings.json',
    'original_derived_schema': OLD / 'derived-row.schema.json', 'original_bridge': BRIDGE / 'bridge.py',
    'original_human_first_driver': BRIDGE / 'human_first_driver.py',
    'original_bridge_output_seal': BRIDGE / 'output-seal.json',
    'original_human_first_supplement_seal': BRIDGE / 'human-first-supplement-output-seal.json',
}.items()}
changes = []


def replace(text, before, after, name, count=1):
    assert text.count(before) == count, (name, text.count(before))
    changes.append({'change': name, 'matching_sites': count})
    return text.replace(before, after)


text = (OLD / 'adapter.py').read_text()
text = replace(text, "VERSION = 'formal800-xlsx-reception-1'", "VERSION = 'formal800-xlsx-lawful-null-reception-2'", 'explicit version')
text = replace(text, 'def normalize(c):', 'def _normalize_binary(c):', 'reuse exact binary parser')
extension = '''def normalize(c, reason_cell=None):
    value, status, method = _normalize_binary(c)
    literal = (reason_cell is not None and reason_cell['formula'] is None
               and reason_cell['cell_type'] in ('s', 'inlineStr', 'str'))
    reason = reason_cell['resolved_value'] if literal else None
    if status == 'filled' and isinstance(reason, str) and reason.startswith('待定'):
        return value, 'invalid', 'binary_pending_marker_conflict'
    if status != 'unfilled' or reason_cell is None or blank(reason_cell):
        return value, status, method
    if not literal:
        return None, 'invalid', 'nonliteral_null_reason_not_allowed'
    for prefix in ('待定：', '待定:'):
        if reason.startswith(prefix):
            if reason[len(prefix):].strip():
                return None, 'lawful_null', 'explicit_pending_prefix_with_nonempty_missing_reason'
            return None, 'incomplete', 'pending_prefix_without_missing_reason'
    return None, 'incomplete', 'blank_D_ordinary_reason_needs_clarification'


'''
text = replace(text, 'def preflight():', extension + 'def preflight():', 'explicit null representation')
text = replace(text, 'issues, normalized = [], []', 'issues, normalized, completion_warnings = [], [], []', 'incomplete separate from technical errors')
text = replace(text, 'value, status, method = normalize(d)', 'value, status, method = normalize(d, e)', 'read D/E together')
text = replace(text, "if status == 'invalid':\n                issue('invalid_value', d['address'], method, original_cell=d)",
               "if status == 'invalid':\n                if method == 'binary_pending_marker_conflict':\n                    issue('binary_pending_marker_conflict', e['address'], method, value_cell=d, reason_cell=e)\n                elif method == 'nonliteral_null_reason_not_allowed':\n                    issue('invalid_null_reason', e['address'], method, original_cell=e)\n                else:\n                    issue('invalid_value', d['address'], method, original_cell=d)\n            if status == 'incomplete':\n                completion_warnings.append({'code': method, 'sheet': sheet_name, 'cell': e['address'], 'value_cell': d['address'], 'requires_clarification': True})",
               'conflict exact location and incomplete warnings')
text = replace(text, "if status == 'filled':\n                try:", "if status in ('filled', 'lawful_null'):\n                try:", 'reason for finished judgment')
text = replace(text, "'value': value, 'completion_status': status, 'reason': reason,", "'value': value, 'completion_status': status, 'reason': reason,\n                               'finished_judgment': status in ('filled', 'lawful_null'),", 'finished null recorded')
text = replace(text, "'expected_rows': 4000, 'expected_blind_ids': 800, 'fully_filled': counts.get('filled') == 4000 and not issues}, normalized",
               "'expected_rows': 4000, 'expected_blind_ids': 800, 'fully_filled': counts.get('filled') == 4000 and not issues,\n                'fully_completed': counts.get('filled', 0) + counts.get('lawful_null', 0) == 4000 and not issues,\n                'completion_warnings': completion_warnings}, normalized", 'finished null qualifies without forcing binary')
text = replace(text, "if not report.get('fully_filled'):\n        pending.append('4000_values_and_reasons_not_complete')", "if not report.get('fully_completed'):\n        pending.append('4000_finished_binary_or_lawful_null_judgments_not_complete')", 'content completion gate')
text = replace(text, "COMMON.verify_binding(release['manual'])", "COMMON.verify_binding(release['manual'])\n            representation = release['input_representation_supplement']\n            COMMON.verify_binding(representation)\n            require(representation['sha256'] == file_binding(HERE / 'input-representation-supplement.txt')['sha256'], 'release null input representation differs')", 'release binds operational representation only')
text = replace(text, "pending = left['completion_status'] != 'filled' or right['completion_status'] != 'filled'\n                status = 'pending' if pending else 'disagreement' if left['value'] != right['value'] else 'agreement'",
               "pending = left['completion_status'] not in ('filled', 'lawful_null') or right['completion_status'] not in ('filled', 'lawful_null')\n                has_null = left['completion_status'] == 'lawful_null' or right['completion_status'] == 'lawful_null'\n                status = 'pending' if pending else 'lawful_null' if has_null else 'disagreement' if left['value'] != right['value'] else 'agreement'", 'null never binary agreement')
text = replace(text, "if status == 'disagreement':\n                    differences.append(pair)", "if status == 'disagreement' or status == 'lawful_null' and left['value'] != right['value']:\n                    differences.append(pair)", 'binary/null difference retained')
text = replace(text, "if status in ('pending', 'disagreement'):\n                    todos.append(dict(pair, required_action='await_actual_independent_input' if pending else 'coordinator_adjudication',", "if status in ('pending', 'disagreement', 'lawful_null'):\n                    todos.append(dict(pair, required_action='await_actual_independent_input' if pending else 'coordinator_material_null_review' if has_null else 'coordinator_adjudication',", 'null material review todo without auto adjudication')
text = replace(text, "'binding_contract': file_binding(CONTRACT)}", "'binding_contract': file_binding(CONTRACT),\n              'input_representation_supplement': file_binding(HERE / 'input-representation-supplement.txt')}", 'report representation binding')
text = replace(text, "'adapter_code': file_binding(Path(__file__)),", "'adapter_code': file_binding(Path(__file__)),\n            'input_representation_supplement': file_binding(HERE / 'input-representation-supplement.txt'),\n            'supplement_dependencies': file_binding(HERE / 'supplement-bindings.json'),", 'seal new code and operation binding')
with (HERE / 'adapter.py').open('x') as f:
    f.write(text)
with (HERE / 'bindings.json').open('xb') as f:
    f.write((OLD / 'bindings.json').read_bytes())

schema = json.loads((OLD / 'derived-row.schema.json').read_text())
schema['title'] = 'XLSX v2 diagnostic row; finished lawful null is not binary agreement'
schema['properties']['completion_status']['enum'] = ['filled', 'lawful_null', 'unfilled', 'incomplete', 'invalid']
schema['properties']['finished_judgment'] = {'type': 'boolean'}
schema['required'].append('finished_judgment')
schema['allOf'] = [
    {'if': {'properties': {'completion_status': {'const': 'lawful_null'}}}, 'then': {'properties': {'value': {'type': 'null'}, 'finished_judgment': {'const': True}, 'reason': {'type': 'string', 'minLength': 1}}}},
    {'if': {'properties': {'completion_status': {'const': 'filled'}}}, 'then': {'properties': {'value': {'type': 'integer', 'enum': [0, 1]}, 'finished_judgment': {'const': True}}}},
    {'if': {'properties': {'completion_status': {'enum': ['unfilled', 'incomplete']}}}, 'then': {'properties': {'value': {'type': 'null'}, 'finished_judgment': {'const': False}}}},
    {'if': {'properties': {'completion_status': {'const': 'invalid'}}}, 'then': {'properties': {'finished_judgment': {'const': False}}}},
]
schema['x-eligibility'] = 'Check content_valid, fully_completed and declaration qualification. filled+lawful_null may finish 4000 slots; unfilled/incomplete never become 0 or semantic_null. Invalid rows remain diagnostics. Raw E and original XLSX are retained.'
with (HERE / 'derived-row.schema.json').open('x') as f:
    f.write(json.dumps(schema, ensure_ascii=False, indent=2) + '\n')

driver = (BRIDGE / 'human_first_driver.py').read_text()
driver = replace(driver, "ADAPTER = ROOT / '05-validation/formal800-xlsx-reception-adapter-sol/adapter.py'", "ADAPTER = HERE / 'adapter.py'", 'driver binds new adapter path')
driver = replace(driver, "seal = bridge.read_json(HERE / 'output-seal.json')", "seal = bridge.read_json(ROOT / '07-statistics/formal800-v15-statistics-input-bridge-sol/output-seal.json')", 'prior registered bridge seal remains read only')
driver = replace(driver, "'formal800-xlsx-reception-1'", "'formal800-xlsx-lawful-null-reception-2'", 'driver accepts explicit v2 reception')
driver = replace(driver, "require(sr.get('fully_filled') is True, 'upstream complete handoff is internally inconsistent')", "require(sr.get('fully_completed') is True, 'upstream finished binary/null handoff is internally inconsistent')", 'driver completed null gate')
with (HERE / 'human_first_driver.py').open('x') as f:
    f.write(driver)
with (HERE / 'supplement-bindings.json').open('x') as f:
    f.write(json.dumps({'version': 'formal800-lawful-null-input-supplement-1', 'dependencies': dependencies,
                        'patches': changes, 'original_registered_engine_changed': False}, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'source_patches_N': len(changes), 'original_files_modified': False}))
