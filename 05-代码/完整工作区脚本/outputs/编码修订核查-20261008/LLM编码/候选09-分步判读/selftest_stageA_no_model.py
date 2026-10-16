"""Run only self-authored minimal technical mocks; no models or corpus inputs."""
import sys
sys.dont_write_bytecode = True
import copy
import datetime
import hashlib
import importlib.util
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNTIME = HERE / 'runtime'
OUT = HERE / 'selftest_stageA_no_model_result.json'
if OUT.exists():
    raise SystemExit('Refusing to overwrite StageA selftest result')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


inventory_module = load_module('stageA_test_inventory', RUNTIME / 'stageA_context_inventory.py')
validation_module = load_module('stageA_test_validator', RUNTIME / 'validate_stageA.py')
legacy_module = load_module('stageA_test_legacyB', RUNTIME / 'validate_binary_output.py')
schema = json.loads((RUNTIME / 'stageA_output_schema.json').read_text())
source_paths = [HERE / 'prompt_lock.json', HERE / 'stageA_prompt.txt', HERE / 'stageB_prompt.txt', RUNTIME / 'validate_binary_output.py']
source_start = {str(path): sha(path) for path in source_paths}
tests = []


def record(name, passed):
    tests.append({'name': name, 'pass': bool(passed)})


def schema_errors(value, node, path='root'):
    """Small independent checker for exactly the JSON Schema subset used here."""
    errors = []
    types = {'object': dict, 'array': list, 'string': str}
    if not isinstance(value, types[node['type']]):
        return [path + ':type']
    if 'enum' in node and value not in node['enum']:
        errors.append(path + ':enum')
    if isinstance(value, dict):
        if set(node.get('required', [])) - set(value):
            errors.append(path + ':required')
        if node.get('additionalProperties') is False and set(value) - set(node['properties']):
            errors.append(path + ':additionalProperties')
        for key in set(value) & set(node['properties']):
            errors.extend(schema_errors(value[key], node['properties'][key], path + '.' + key))
    elif isinstance(value, list):
        if len(value) < node.get('minItems', 0):
            errors.append(path + ':minItems')
        for index, item in enumerate(value):
            errors.extend(schema_errors(item, node['items'], path + '[' + str(index) + ']'))
    else:
        if len(value) < node.get('minLength', 0):
            errors.append(path + ':minLength')
        if 'pattern' in node and re.search(node['pattern'], value) is None:
            errors.append(path + ':pattern')
    return errors


def pointer_get(row, pointer):
    value = row
    for token in pointer.split('/')[1:]:
        token = token.replace('~1', '/').replace('~0', '~')
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


# This toy vocabulary is unrelated to any study or control material.
packet = {'rows': [
    {'id': 'toy-a', 'text': 'Alpha does beta under gamma.', 'contexts': {
        'text': 'root alpha', 'headers': 'header alpha',
        'row_cells': ['naked list strings are ignored', {'text': 'cell alpha'}],
        'caption': 'caption alpha', 'definition': 'definition alpha',
        'title': 'title alpha', 'note': 'note alpha',
        'opaque': {'text': 'nested alpha', 'ignored_string': 'not quotable',
                   'more': [{'note': 'nested note'}, 'also ignored']},
        'slash/~': {'text': 'exact duplicate'},
        'copy': {'text': 'exact duplicate'}, 'empty': {'note': ''},
        'raw_headers': {'headers': ['ignored raw header', {'title': 'nested title'}]},
    }},
    {'id': 'toy-b', 'text': 'Delta remains epsilon.', 'contexts': {}},
]}
packet_original = copy.deepcopy(packet)


def make_output():
    rows = []
    for inp in packet['rows']:
        grouped = {}
        for leaf in inventory_module.inventory(inp):
            grouped.setdefault(leaf['text'], []).append(leaf['path'])
        records = []
        for index, (text, paths) in enumerate(grouped.items()):
            status = 'used' if index == 0 else ('ambiguous' if index == 1 else 'not_used')
            records.append({'paths': paths, 'status': status,
                            'proposition_ids': ['p1'] if status != 'not_used' else [],
                            'unit_quotes': [inp['text']] if status != 'not_used' else [],
                            'context_quote': text,
                            'contribution': 'Toy technical relation or omission record.'})
        rows.append({'id': inp['id'], 'current_propositions': [{
            'proposition_id': 'p1', 'subject_or_object': 'Toy object.',
            'actions_attributes_and_qualifiers': 'Toy action with qualifiers.',
            'conditional_outcome': 'No outcome is asserted in this technical mock.',
            'unit_quotes': [inp['text']],
        }], 'context_records': records, 'material_status': 'sufficient',
                     'material_note': 'Self-authored technical mock only.'})
    return {'stage': validation_module.STAGE, 'rows': rows}


valid_output = make_output()
record('valid_mock_structure_and_quotes', validation_module.validate(packet, valid_output) == [])
record('valid_mock_schema', schema_errors(valid_output, schema) == [])
record('all_seven_fields_present', all(any('/' + field in leaf['path'] for leaf in inventory_module.inventory(packet['rows'][0])) for field in inventory_module.QUOTABLE_FIELDS))
record('inventory_exact_legacy_leaf_sequence', all([leaf['text'] for leaf in inventory_module.inventory(row)] == list(legacy_module.iter_context_text(row.get('contexts', {}))) for row in packet['rows']))
record('rfc6901_paths_resolve_exact_original', all(pointer_get(row, leaf['path']) == leaf['text'] for row in packet['rows'] for leaf in inventory_module.inventory(row)))
record('pointer_escape_slash_and_tilde', '/contexts/slash~1~0/text' in [leaf['path'] for leaf in inventory_module.inventory(packet['rows'][0])])
record('naked_list_strings_ignored_exactly_as_B', all('ignored' not in leaf['text'] for leaf in inventory_module.inventory(packet['rows'][0])))
record('empty_context_leaf_preserved', any(leaf['text'] == '' for leaf in inventory_module.inventory(packet['rows'][0])))
index = inventory_module.inventory_packet(packet['rows'])
record('packet_index_hashes_exact_original_utf8', all(item['text_sha256'] == hashlib.sha256(pointer_get(row, item['path']).encode()).hexdigest() for row in packet['rows'] for item in index[row['id']]['paths']))
record('packet_index_groups_only_exact_duplicates', any(len(group['paths']) == 2 for group in index['toy-a']['text_sha256_groups']) and all(len({pointer_get(packet['rows'][0], path) for path in group['paths']}) == 1 for group in index['toy-a']['text_sha256_groups']))
record('helpers_do_not_modify_input', packet == packet_original)
for status in ['sufficient', 'boundary', 'material_issue']:
    candidate = copy.deepcopy(valid_output)
    candidate['rows'][0]['material_status'] = status
    record('material_status_' + status + '_structurally_valid', validation_module.validate(packet, candidate) == [] and schema_errors(candidate, schema) == [])
candidate = copy.deepcopy(valid_output)
candidate['rows'][1]['material_status'] = 'material_issue'
candidate['rows'][1]['current_propositions'] = []
record('material_issue_empty_propositions_no_technical_retry', validation_module.validate(packet, candidate) == [] and schema_errors(candidate, schema) == [])


def mutation(name, alter, expected_error):
    candidate = copy.deepcopy(valid_output)
    alter(candidate)
    errors = validation_module.validate(packet, candidate)
    record(name, any(expected_error in error for error in errors))


mutation('reject_wrong_stage', lambda out: out.update(stage='other'), 'root:stage')
mutation('reject_extra_label_root', lambda out: out.update(labels={}), 'root:fields')
mutation('reject_extra_label_row', lambda out: out['rows'][0].update(labels={}), 'rows[0]:fields')
mutation('reject_wrong_id_order', lambda out: out['rows'].reverse(), 'id_count_or_order')
mutation('reject_duplicate_id', lambda out: out['rows'][1].update(id='toy-a'), 'duplicate_id')
mutation('reject_proposition_gap', lambda out: out['rows'][0]['current_propositions'][0].update(proposition_id='p2'), 'not_sequential')
mutation('reject_empty_subject', lambda out: out['rows'][0]['current_propositions'][0].update(subject_or_object=' '), 'subject_or_object_empty')
mutation('reject_empty_qualifiers', lambda out: out['rows'][0]['current_propositions'][0].update(actions_attributes_and_qualifiers=''), 'actions_attributes_and_qualifiers_empty')
mutation('reject_empty_outcome', lambda out: out['rows'][0]['current_propositions'][0].update(conditional_outcome=''), 'conditional_outcome_empty')
mutation('reject_empty_prop_quote_array', lambda out: out['rows'][0]['current_propositions'][0].update(unit_quotes=[]), 'empty_array')
mutation('reject_fabricated_unit_quote', lambda out: out['rows'][0]['current_propositions'][0].update(unit_quotes=['not in source']), 'nonliteral_quote')
mutation('reject_missing_context_path', lambda out: out['rows'][0]['context_records'].pop(), 'not_covered_exactly_once')
mutation('reject_duplicate_context_path', lambda out: out['rows'][0]['context_records'].append(copy.deepcopy(out['rows'][0]['context_records'][0])), 'not_covered_exactly_once')
mutation('reject_unknown_context_path', lambda out: out['rows'][0]['context_records'][0].update(paths=['/contexts/absent/text']), 'unknown_context_path')
mutation('reject_duplicate_path_in_record', lambda out: out['rows'][0]['context_records'][0]['paths'].append(out['rows'][0]['context_records'][0]['paths'][0]), '.paths:duplicate')
mutation('reject_empty_paths', lambda out: out['rows'][0]['context_records'][0].update(paths=[]), '.paths:empty_array')
mutation('reject_group_different_original_text', lambda out: out['rows'][0]['context_records'][0]['paths'].append(out['rows'][0]['context_records'][1]['paths'][0]), 'grouped_original_text_not_identical')
mutation('reject_used_no_reference', lambda out: out['rows'][0]['context_records'][0].update(proposition_ids=[]), 'used_without_proposition_reference')
mutation('reject_unknown_proposition_reference', lambda out: out['rows'][0]['context_records'][0].update(proposition_ids=['p9']), 'unknown_proposition_reference')
mutation('reject_used_no_anchor', lambda out: out['rows'][0]['context_records'][0].update(unit_quotes=[]), '.unit_quotes:empty_array')
mutation('reject_not_used_refs', lambda out: out['rows'][0]['context_records'][2].update(proposition_ids=['p1']), 'not_used_has_reference_or_anchor')
mutation('reject_not_used_anchors', lambda out: out['rows'][0]['context_records'][2].update(unit_quotes=['Alpha']), 'not_used_has_reference_or_anchor')
mutation('reject_context_quote_from_wrong_path', lambda out: out['rows'][0]['context_records'][0].update(context_quote='header alpha'), 'nonliteral_context_quote')
mutation('reject_empty_quote_for_nonempty_context', lambda out: out['rows'][0]['context_records'][0].update(context_quote=''), 'empty_quote_for_nonempty_context')
mutation('reject_empty_contribution', lambda out: out['rows'][0]['context_records'][0].update(contribution=' '), 'empty_contribution')
mutation('reject_invalid_material_status', lambda out: out['rows'][0].update(material_status='unknown'), 'material_status')
mutation('reject_empty_material_note', lambda out: out['rows'][0].update(material_note=''), 'empty_material_note')
mutation('reject_nonempty_sufficient_without_proposition', lambda out: out['rows'][1].update(current_propositions=[]), 'without_proposition')
mutation('reject_nonempty_boundary_without_proposition', lambda out: out['rows'][1].update(current_propositions=[], material_status='boundary'), 'without_proposition')

# No output field from a private source is used in these malformed-shape mocks.
for name, output in [('null_output', None), ('rows_scalar', {'stage': validation_module.STAGE, 'rows': 3}), ('row_null', {'stage': validation_module.STAGE, 'rows': [None]})]:
    record(name + '_returns_errors_without_exception', bool(validation_module.validate(packet, output)))
record('invalid_packet_returns_errors', bool(validation_module.validate(None, valid_output)))
record('no_contexts_requires_empty_records', valid_output['rows'][1]['context_records'] == [])
record('prompt_and_legacyB_sources_unchanged', all(sha(path) == digest for path, digest in source_start.items()))
record('schema_all_objects_require_exact_fields', schema['additionalProperties'] is False and schema['properties']['rows']['items']['additionalProperties'] is False and schema['properties']['rows']['items']['properties']['current_propositions']['items']['additionalProperties'] is False and schema['properties']['rows']['items']['properties']['context_records']['items']['additionalProperties'] is False)
failures = [test['name'] for test in tests if not test['pass']]
report = {'status': 'PASS_NO_MODEL_TECHNICAL_SELFTEST' if not failures else 'FAIL_NO_MODEL_TECHNICAL_SELFTEST', 'created_at_UTC': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'tests_passed': len(tests) - len(failures), 'tests_total': len(tests), 'failures': failures, 'tests': tests, 'source_bindings': [{'path': path, 'sha256': digest, 'unchanged': sha(path) == digest} for path, digest in source_start.items()], 'implementation_bindings': [{'path': str(path), 'sha256': sha(path)} for path in [RUNTIME / 'stageA_context_inventory.py', RUNTIME / 'validate_stageA.py', RUNTIME / 'stageA_output_schema.json', Path(__file__)]], 'inputs': 'Only self-authored two-row toy objects in this selftest script; no project/corpus/heldout/control files read.', 'model_calls': 0, 'model_CLI_invocations': 0, 'real_policy_or_reserved_text_reads': 0, 'semantic_correctness_verified': False, 'material_issue_policy': 'Structurally valid, no technical retry due to material_status; later wrapper must gate StageB.', 'limits': ['Schema enforces local shape only; validate enforces exact coverage, cross-references and literal anchors.', 'Grouped paths can be checked for exact original text only; whether their semantic role/status is truly the same is not technically established.', 'Legacy naked list strings stay out of inventory while original contexts are retained unchanged.']}
with OUT.open('x', encoding='utf-8') as handle:
    handle.write(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'status': report['status'], 'tests_passed': report['tests_passed'], 'tests_total': report['tests_total'], 'failures': failures, 'result_path': str(OUT), 'result_sha256': sha(OUT)}, ensure_ascii=False))
raise SystemExit(1 if failures else 0)
