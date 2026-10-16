"""Finite management/template-only readback. No real or synthetic binary labels."""
from pathlib import Path
import csv
import importlib.util
import json
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('bridge_under_readback', HERE / 'bridge.py')
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


def main():
    rows, design, management = bridge.load_management()
    prepared = HERE / 'prepared-unfilled'
    template = bridge.read_json(prepared / 'engine-input.UNFILLED.template.json')
    if template['data_role'] is not None or len(template['records']) != 800:
        raise ValueError('Unfilled800 role/shape changed')
    if template['metadata']['design'] != design:
        raise ValueError('Original design changed')
    if any(record['outputs'] != {m: None for m in bridge.METHODS} for record in template['records']):
        raise ValueError('Unfilled output should contain no binary predictions')
    if any('policy_year' in record for record in template['records']) or 'year_mapping' in template['metadata']:
        raise ValueError('Year mode was silently enabled')
    slot_checks = {}
    for method in bridge.METHODS:
        with (prepared / (method + '-parsed4000.UNFILLED.slots.csv')).open(newline='', encoding='utf-8') as stream:
            slots = list(csv.DictReader(stream))
        join_key = method + '_blind_id' if method in ('A', 'B') else 'source_id'
        expected = {(row[join_key], dim) for row in rows for dim in bridge.DIMS}
        if len(slots) != 4000 or {(cell['join_id'], cell['dimension']) for cell in slots} != expected:
            raise ValueError('A method lost or duplicated assigned slots')
        if any(cell['state'] != 'not_submitted' or cell['value'] != '' for cell in slots):
            raise ValueError('Blank template carries a coding value')
        # No cell values are supplied: verify full expansion of absent slots.
        outputs, statuses = bridge.project_parsed_cells([], method, rows)
        if len(outputs) != 800 or len(statuses) != 4000 or any(value is not None for value in outputs.values()):
            raise ValueError('Absent inputs became values or dropped rows')
        if any(cell['state'] != 'not_submitted' or cell['value'] is not None or
               cell['origin'] != 'absent_parsed_cell' for cell in statuses):
            raise ValueError('Absence origin was changed')
        slot_checks[method] = {'slots': len(slots), 'blank_values': len(slots), 'absent_projection_slots': len(statuses)}
    engine = bridge.load_engine()
    try:
        engine.prepare(template)
    except engine.DataError as error:
        rejection = str(error)
    else:
        raise ValueError('Old engine accepted an unfilled input template')
    blocked_checks = {}
    for mode in ('--calculate', '--convert-only'):
        result = subprocess.run([sys.executable, str(HERE / 'bridge.py'), mode,
                                 '--method-input', 'A=/must/not/open/a/result.jsonl'],
                                capture_output=True, text=True)
        if result.returncode != 2:
            raise ValueError('Calculation mode did not fail closed')
        readback = json.loads(result.stdout)
        if readback['method_input_files_opened'] != 0:
            raise ValueError('Result inputs opened before qualification')
        blocked_checks[mode] = {'exit_code': result.returncode, 'method_input_files_opened': 0}
    result = {'status': 'passed_finite_management_and_unfilled_template_readback',
              'management': management, 'template_slots': slot_checks,
              'unfilled_engine_rejection': rejection, 'fail_closed_cli_checks': blocked_checks,
              'real_or_synthetic_binary_label_values_created': 0, 'analyze_calls': 0,
              'no_real_label_or_source_prose_read': True, 'no_formal_validation_claimed': True}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    destination = HERE / 'finite-readback.json'
    if destination.exists():
        if bridge.read_json(destination) != result:
            raise ValueError('Existing finite readback differs; no overwrite')
    else:
        bridge.write_json_exclusive(destination, result)


if __name__ == '__main__':
    main()
