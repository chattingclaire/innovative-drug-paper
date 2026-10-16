"""Only XLSX lawful-null projection is extended; original engine/NA untouched."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
registered = json.loads((HERE / 'supplement-bindings.json').read_text())['dependencies']['original_bridge']
source = Path(registered['path'])
raw = source.read_bytes()
assert len(raw) == registered['bytes'] and hashlib.sha256(raw).hexdigest() == registered['sha256'], 'original registered bridge changed'
spec = importlib.util.spec_from_file_location('_unchanged_registered_statistics_bridge', source)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def __getattr__(name):
    return getattr(base, name)


def project_xlsx_derived_cells(derived_rows, side, rows):
    if side not in ('A', 'B') or len(derived_rows) != 4000:
        raise base.BridgeError('Expected independent A/B derived ledger of 4000 slots')
    assigned = {row[side + '_blind_id'] for row in rows}
    source_ids = {row[side + '_blind_id']: row['source_id'] for row in rows}
    projected, seen, original_status = [], set(), {}
    for raw in derived_rows:
        jid, dim = raw.get('blind_id'), raw.get('dimension')
        if raw.get('side') != side or jid not in assigned or dim not in base.DIMS:
            raise base.BridgeError('XLSX v2 row does not join its own issued blind side')
        if raw.get('expected_blind_id') != jid or raw.get('expected_dimension') != dim:
            raise base.BridgeError('XLSX v2 changed the issued slot binding')
        if (jid, dim) in seen:
            raise base.BridgeError('Duplicate independent XLSX slot')
        seen.add((jid, dim))
        status, value = raw.get('completion_status'), raw.get('value')
        finished = raw.get('finished_judgment')
        if status == 'filled':
            if type(value) is not int or value not in (0, 1) or finished is not True:
                raise base.BridgeError('Filled v2 value must be finished integer0/1')
            state = 'binary'
        elif status == 'lawful_null':
            if value is not None or finished is not True:
                raise base.BridgeError('Finished lawful_null requires null, never 0')
            state = 'semantic_null'
        elif status in ('unfilled', 'incomplete'):
            if value is not None or finished is not False:
                raise base.BridgeError('Unfinished slot must retain null and false completion')
            state = 'blank'
        else:
            raise base.BridgeError('Invalid/contradictory content remains upstream; no numerical input')
        projected.append({'join_id': jid, 'dimension': dim, 'state': state, 'value': value})
        original_status[source_ids[jid], dim] = status
    if seen != {(jid, dim) for jid in assigned for dim in base.DIMS}:
        raise base.BridgeError('XLSX v2 assigned coverage differs')
    outputs, statuses = base.project_parsed_cells(projected, side, rows)
    for cell in statuses:
        cell['xlsx_completion_status'] = original_status[cell['unit_id'], cell['dimension']]
    return outputs, statuses
