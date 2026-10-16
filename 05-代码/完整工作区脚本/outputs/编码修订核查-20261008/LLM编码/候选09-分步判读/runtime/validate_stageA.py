"""Pure structural/literal Stage A validation; no semantic or label judgments.

material_issue and boundary are valid record statuses, never retry triggers by
themselves. A wrapper must separately gate Stage B on the accepted statuses.
"""
from collections import Counter
from pathlib import Path
import importlib.util

try:
    from .stageA_context_inventory import inventory
except ImportError:
    # Support direct file-based runner imports without changing global sys.path.
    _spec = importlib.util.spec_from_file_location(
        '_stageA_inventory_for_validator', Path(__file__).with_name('stageA_context_inventory.py'))
    _module = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_module)
    inventory = _module.inventory

STAGE = 'current_proposition_context_record'
ROW_FIELDS = {'id', 'current_propositions', 'context_records', 'material_status', 'material_note'}
PROPOSITION_FIELDS = {'proposition_id', 'subject_or_object', 'actions_attributes_and_qualifiers', 'conditional_outcome', 'unit_quotes'}
CONTEXT_FIELDS = {'paths', 'status', 'proposition_ids', 'unit_quotes', 'context_quote', 'contribution'}
MATERIAL_STATUSES = {'sufficient', 'material_issue', 'boundary'}
CONTEXT_STATUSES = {'used', 'not_used', 'ambiguous'}


def _exact(value, keys, location, errors):
    if not isinstance(value, dict):
        errors.append(location + ':not_object')
        return False
    if set(value) != keys:
        errors.append(location + ':fields')
        return False
    return True


def _nonempty_string(value):
    return isinstance(value, str) and bool(value.strip())


def _string_list(value, location, errors, nonempty=False, unique=False):
    if not isinstance(value, list):
        errors.append(location + ':not_array')
        return False
    if nonempty and not value:
        errors.append(location + ':empty_array')
    if any(not isinstance(item, str) or not item for item in value):
        errors.append(location + ':not_nonempty_strings')
        return False
    if unique and len(value) != len(set(value)):
        errors.append(location + ':duplicate')
    return True


def _unit_quotes(value, text, location, errors, required=False):
    if _string_list(value, location, errors, nonempty=required):
        if any(quote not in text for quote in value):
            errors.append(location + ':nonliteral_quote')


def validate(packet, output):
    """Return errors list; accept all three material statuses structurally."""
    errors = []
    if not isinstance(packet, dict) or not isinstance(packet.get('rows'), list):
        return ['input:rows_not_array']
    inputs = packet['rows']
    input_ids = [row.get('id') if isinstance(row, dict) else None for row in inputs]
    if any(not _nonempty_string(value) for value in input_ids):
        errors.append('input.rows:id_not_nonempty_string')
    elif len(set(input_ids)) != len(input_ids):
        errors.append('input.rows:duplicate_id')
    if not _exact(output, {'stage', 'rows'}, 'root', errors):
        return errors
    if output['stage'] != STAGE:
        errors.append('root:stage')
    if not isinstance(output['rows'], list):
        return errors + ['root.rows:not_array']
    output_ids = [row.get('id') if isinstance(row, dict) else None for row in output['rows']]
    if any(not _nonempty_string(value) for value in output_ids):
        errors.append('root.rows:id_not_nonempty_string')
    elif len(set(output_ids)) != len(output_ids):
        errors.append('root.rows:duplicate_id')
    if input_ids != output_ids:
        errors.append('root.rows:id_count_or_order')

    for index, (inp, row) in enumerate(zip(inputs, output['rows'])):
        loc = 'rows[' + str(index) + ']'
        if not isinstance(inp, dict):
            errors.append('input.' + loc + ':not_object')
            continue
        text = inp.get('text')
        if not isinstance(text, str):
            errors.append('input.' + loc + ':text_not_string')
            continue
        if not _exact(row, ROW_FIELDS, loc, errors):
            continue
        if not isinstance(row['material_status'], str) or row['material_status'] not in MATERIAL_STATUSES:
            errors.append(loc + ':material_status')
        if not _nonempty_string(row['material_note']):
            errors.append(loc + ':empty_material_note')
        propositions = row['current_propositions']
        valid_prop_ids = set()
        if not isinstance(propositions, list):
            errors.append(loc + '.current_propositions:not_array')
            propositions = []
        if text and row['material_status'] in ('sufficient', 'boundary') and not propositions:
            errors.append(loc + ':nonempty_sufficient_or_boundary_unit_without_proposition')
        for pindex, prop in enumerate(propositions, 1):
            ploc = loc + '.current_propositions[' + str(pindex - 1) + ']'
            if not _exact(prop, PROPOSITION_FIELDS, ploc, errors):
                continue
            expected_pid = 'p' + str(pindex)
            if prop['proposition_id'] != expected_pid:
                errors.append(ploc + ':proposition_id_not_sequential')
            else:
                valid_prop_ids.add(expected_pid)
            for field in ['subject_or_object', 'actions_attributes_and_qualifiers', 'conditional_outcome']:
                if not _nonempty_string(prop[field]):
                    errors.append(ploc + ':' + field + '_empty')
            _unit_quotes(prop['unit_quotes'], text, ploc + '.unit_quotes', errors, required=True)

        leaves = inventory(inp)
        leaf_texts = {leaf['path']: leaf['text'] for leaf in leaves}
        records = row['context_records']
        if not isinstance(records, list):
            errors.append(loc + '.context_records:not_array')
            continue
        covered = []
        for cindex, record in enumerate(records):
            cloc = loc + '.context_records[' + str(cindex) + ']'
            if not _exact(record, CONTEXT_FIELDS, cloc, errors):
                continue
            paths_ok = _string_list(record['paths'], cloc + '.paths', errors, nonempty=True, unique=True)
            paths = record['paths'] if paths_ok else []
            covered.extend(paths)
            known_paths = [path for path in paths if path in leaf_texts]
            if len(known_paths) != len(paths):
                errors.append(cloc + ':unknown_context_path')
            originals = [leaf_texts[path] for path in known_paths]
            if originals and any(value != originals[0] for value in originals[1:]):
                errors.append(cloc + ':grouped_original_text_not_identical')
            status = record['status']
            if not isinstance(status, str) or status not in CONTEXT_STATUSES:
                errors.append(cloc + ':status')
            refs_ok = _string_list(record['proposition_ids'], cloc + '.proposition_ids', errors, unique=True)
            refs = record['proposition_ids'] if refs_ok else []
            if any(pid not in valid_prop_ids for pid in refs):
                errors.append(cloc + ':unknown_proposition_reference')
            _unit_quotes(record['unit_quotes'], text, cloc + '.unit_quotes', errors, required=status == 'used')
            if status == 'used' and not refs:
                errors.append(cloc + ':used_without_proposition_reference')
            if status == 'not_used' and (record['proposition_ids'] != [] or record['unit_quotes'] != []):
                errors.append(cloc + ':not_used_has_reference_or_anchor')
            quote = record['context_quote']
            if not isinstance(quote, str):
                errors.append(cloc + ':context_quote_not_string')
            elif any(quote not in original for original in originals):
                errors.append(cloc + ':nonliteral_context_quote')
            elif quote == '' and any(original != '' for original in originals):
                errors.append(cloc + ':empty_quote_for_nonempty_context')
            if not _nonempty_string(record['contribution']):
                errors.append(cloc + ':empty_contribution')
        counts = Counter(covered)
        if set(counts) != set(leaf_texts) or any(count != 1 for count in counts.values()):
            errors.append(loc + ':context_inventory_not_covered_exactly_once')
    return errors
