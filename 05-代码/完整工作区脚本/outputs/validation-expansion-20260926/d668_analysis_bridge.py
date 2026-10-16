"""D668/R600 original-submission bridge. Import has no study I/O.

Joins exact first submissions to frozen sampling IDs, never machine columns.
CLI requires all 54 D submissions/receipts and all 48 frozen R originals.
All runtime inputs are byte-hashed before and after analysis. No overwrites.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import sys
import types

DIMS = ('S', 'E', 'Ec', 'I', 'F')
CODERS = ('A', 'C')
FROZEN_SORTED_DESIGN_SHA256 = 'a49f6635df0d53db26d4b700b95e4cd380e022354ecea10c7dbff1daf8d4f62d'


def require(value, message):
    if not value: raise ValueError(message)


def sha(raw): return hashlib.sha256(raw).hexdigest()


def encoded(obj):
    return (json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()


def read_json(raw):
    def pairs(items):
        result = {}
        for k, v in items:
            require(k not in result, 'Duplicate JSON key')
            result[k] = v
        return result
    def bad(_): raise ValueError('Nonfinite JSON constant')
    result = json.loads(raw, object_pairs_hook=pairs, parse_constant=bad)
    require(isinstance(result, dict), 'JSON object required')
    return result


def load_source(raw, name, path):
    module = types.ModuleType(name); module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def standardized_labels(labels):
    require(isinstance(labels, dict) and set(labels) == set(DIMS), 'Five labels required')
    result = {}
    for dim in DIMS:
        value = labels[dim]
        require((type(value) is int and value in (0, 1)) or (type(value) is str and value == '待定'), 'Illegal literal label')
        result[dim] = 'pending' if value == '待定' else str(value)
    return result


def validate_frozen_design(design):
    """Check the complete metadata signature, allowing only stratum reordering."""
    require(isinstance(design, dict) and set(design) ==
            {'population_size', 'sample_size', 'department_sizes', 'strata'}, 'Invalid design schema')
    require(type(design['population_size']) is int and type(design['sample_size']) is int,
            'Literal integer design sizes required')
    require(isinstance(design['department_sizes'], dict) and
            all(type(v) is int for v in design['department_sizes'].values()), 'Literal department sizes required')
    require(isinstance(design['strata'], list) and len(design['strata']) == 29, 'All 29 frozen strata required')
    for s in design['strata']:
        require(isinstance(s, dict) and set(s) == {'stratum_id', 'phase', 'department', 'N', 'n'}, 'Invalid stratum schema')
        require(isinstance(s['stratum_id'], str) and type(s['N']) is int and type(s['n']) is int,
                'Literal stratum IDs and sizes required')
    normalized = {**design, 'strata': sorted(design['strata'], key=lambda s: s['stratum_id'])}
    raw = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    require(sha(raw) == FROZEN_SORTED_DESIGN_SHA256, 'Design differs from frozen 29-stratum metadata')


def validate_runtime(runtime):
    """Fail closed if the executable dependency versions differ from the freeze."""
    import numpy
    import scipy
    actual = {'python_version': platform.python_version(), 'numpy': numpy.__version__, 'scipy': scipy.__version__}
    require(isinstance(runtime, dict) and all(runtime.get(k) == v for k, v in actual.items()),
            'Python/NumPy/SciPy runtime differs from prospective freeze')
    return {**actual, 'python_executable': sys.executable,
            'numpy_module_path': numpy.__file__, 'scipy_module_path': scipy.__file__}


def assemble_rows(r_mapping, d_mapping, original_documents, design):
    """Pure ID join. original_documents={'R':{relative:doc},'D':{...}}."""
    validate_frozen_design(design)
    require(isinstance(original_documents, dict) and set(original_documents) == {'R', 'D'}, 'R and D originals required')
    strata = {s['stratum_id']: s for s in design['strata']}
    units = []; seen = set(); provenance = []; stratum_counts = {sid: 0 for sid in strata}
    for phase, mapping, count in [('R', r_mapping, 600), ('D', d_mapping, 668)]:
        require(isinstance(mapping, dict) and isinstance(mapping.get('rows'), list), 'Mapping rows required')
        rows = mapping['rows']; require(len(rows) == count, 'Mapping count mismatch')
        require(all(isinstance(r, dict) and isinstance(r.get('id'), str) and r['id'].strip() == r['id'] and r['id'] for r in rows),
                'Nonempty literal blind ID required')
        blind = {r['id']: r for r in rows}; require(len(blind) == count, 'Duplicate blind mapping ID')
        by_coder = {c: {} for c in CODERS}
        expected = {f'agent-{c}/结果-{b:02d}.json' for c in CODERS for b in range(1, (24 if phase == 'R' else 27) + 1)}
        require(isinstance(original_documents[phase], dict) and set(original_documents[phase]) == expected,
                'All 48 R or 54 D original batch documents required')
        for relative, document in original_documents[phase].items():
            coder = relative.split('/')[0][-1]
            require(isinstance(document, dict) and coder in CODERS and document.get('coder') == coder, 'Coder identity mismatch')
            require(isinstance(document.get('rows'), list), 'Original submission rows required')
            for row in document['rows']:
                require(isinstance(row, dict) and isinstance(row.get('id'), str), 'Original row ID required')
                require(row['id'] not in by_coder[coder], 'Duplicate submission ID')
                by_coder[coder][row['id']] = row
        require(all(set(by_coder[c]) == set(blind) for c in CODERS), 'Missing or extra original submission ID')
        for row in rows:
            rid = row['review_id']; require(isinstance(rid, str) and rid and rid.strip() == rid and rid not in seen, 'Duplicate or empty global ID')
            seen.add(rid)
            group = row['group']
            stratum = 'R|' + row['stratum'] if phase == 'R' else 'D|' + group
            require(stratum in strata, 'Unknown stratum')
            s = strata[stratum]
            require(s['phase'] == phase and s['department'] == group, 'Phase/department mismatch')
            for key, target in [('N_h', s['N']), ('n_h', s['n'])]:
                require(type(row[key]) is int and row[key] == target, 'Stratum size differs from prospective design')
            for key in ('pi', 'weight'):
                require(type(row[key]) in (int, float) and math.isfinite(row[key]), 'Finite literal design probabilities/weights required')
            require(math.isclose(row['pi'], s['n']/s['N'], rel_tol=1e-12, abs_tol=1e-12), 'Inclusion probability mismatch')
            require(math.isclose(row['weight'], s['N']/s['n'], rel_tol=1e-12, abs_tol=1e-12), 'Design weight mismatch')
            require(isinstance(row.get('unit_text_sha256'), str) and re.fullmatch(r'[0-9a-f]{64}', row['unit_text_sha256']),
                    'Valid frozen unit text SHA-256 required')
            labels = {c: standardized_labels(by_coder[c][row['id']]['labels']) for c in CODERS}
            units.append({'unit_id': rid, 'stratum_id': stratum, 'labels': labels})
            stratum_counts[stratum] += 1
            provenance.append({'phase': phase, 'blind_id': row['id'], 'review_id': rid,
                               'stratum_id': stratum, 'unit_text_sha256': row['unit_text_sha256']})
    require(len(units) == len(seen) == 1268, 'Unique sample count must be 1268')
    require(all(stratum_counts[sid] == s['n'] for sid, s in strata.items()), 'Per-stratum sample count differs from frozen n')
    payload = {'schema_version': 'd668-v1', 'data_kind': 'observed_coding', 'design': design,
               'coders': list(CODERS), 'dimensions': list(DIMS), 'units': units}
    return payload, provenance


def run(freeze_path, receipts, output):
    freeze_path, receipts, output = [p.resolve() for p in (freeze_path, receipts, output)]
    partial = output.with_name(output.name + '.partial')
    require(not output.exists() and not partial.exists(), 'Output/partial already exists')
    tracked = {}
    def snapshot(path, expected=None):
        path = Path(path)
        require(path.is_absolute() and path.is_file() and not path.is_symlink(), 'Regular absolute input required')
        raw = path.read_bytes(); digest = sha(raw)
        if expected is not None: require(digest == expected, 'Input SHA-256 mismatch: ' + path.name)
        tracked[str(path)] = digest
        return raw
    freeze_raw = snapshot(freeze_path); freeze = read_json(freeze_raw)
    require(freeze['status'] == 'frozen_for_D668_supplementary_AI_content_analysis' and freeze['phase'] == 'D668', 'Final D freeze required')
    runtime = validate_runtime(freeze.get('runtime'))
    frozen = {k: snapshot(v['path'], v['sha256']) for k, v in freeze['files'].items()}
    require(sha(Path(__file__).read_bytes()) == freeze['files']['analysis_bridge']['sha256'], 'Running bridge is not frozen')
    admin = load_source(frozen['admin_receiver'], '_D668_bound_admin', freeze['files']['admin_receiver']['path'])
    stats = load_source(frozen['statistics'], '_D668_bound_statistics', freeze['files']['statistics']['path'])
    release = Path(freeze['release_directory'])
    context = admin.prepare(freeze_path, release)
    for path, digest in context['tracked'].items(): snapshot(path, digest)
    binding = read_json(snapshot(receipts / '接收绑定.json'))
    require(binding == context['binding'], 'First-receipt binding mismatch')
    expected_d = {f'agent-{c}/结果-{b:02d}.json' for c in CODERS for b in range(1, 28)}
    require(set(admin.result_inventory(release)) == set(admin.result_inventory(receipts)) == expected_d, 'All 54 D originals and first receipts required')
    require(set(admin.result_inventory(receipts / 'receipt-records')) == expected_d, 'All 54 D first-receipt records required')
    documents = {'R': {}, 'D': {}}; raw_manifest = {'R': {}, 'D': {}}
    for relative in sorted(expected_d):
        raw = snapshot(receipts / relative)
        require(snapshot(release / relative) == raw, 'D source differs from first receipt')
        record = read_json(snapshot(receipts / 'receipt-records' / relative))
        require(record['sha256'] == sha(raw) and record['byte_count'] == len(raw) and record['binding'] == binding
                and record['file'] == relative, 'Invalid first-receipt record')
        admin.validate_submission(raw, relative, context)
        documents['D'][relative] = read_json(raw)
        raw_manifest['D'][relative] = {'sha256': sha(raw), 'byte_count': len(raw)}
    r_sources = read_json(frozen['r600_source_manifest'])
    require(r_sources['n'] == 600 and r_sources['N_R'] == 1531, 'R source frame mismatch')
    require(r_sources['protocol_version'] == freeze['protocol_version'], 'R/D manual version mismatch')
    def source_entry(key):
        entry = r_sources[key]; return read_json(snapshot(entry['path'], entry['sha256']))
    r_freeze = source_entry('source_original_freeze'); r_seal = source_entry('source_release_seal'); r_mapping = source_entry('source_mapping')
    require(r_seal['freeze_manifest_sha256'] == r_sources['source_original_freeze']['sha256'], 'R seal/freeze binding mismatch')
    require(r_sources['source_mapping']['sha256'] == freeze['files']['v600_sampling_manifest']['sha256'], 'R mapping not frozen input')
    for key in ('protocol', 'protocol_clarifications'):
        require(r_freeze['files'][key]['sha256'] == freeze['files'][key]['sha256'], 'R/D common document mismatch')
    expected_r = {f'agent-{c}/结果-{b:02d}.json' for c in CODERS for b in range(1, 25)}
    require(set(r_sources['raw_submissions']) == expected_r, 'R source manifest must bind 48 files')
    legacy = context['legacy']
    for relative in sorted(expected_r):
        entry = r_sources['raw_submissions'][relative]
        raw = snapshot(entry['first_receipt']['path'], entry['first_receipt']['sha256'])
        require(snapshot(entry['original']['path'], entry['original']['sha256']) == raw, 'R original changed')
        document = read_json(raw); coder = relative.split('/')[0][-1]
        packet_rel = relative.replace('结果-', '材料-'); pe = r_sources['material_packets'][packet_rel]
        packet_raw = snapshot(pe['path'], pe['sha256'])
        require(r_seal['output_files'][packet_rel] == sha(packet_raw), 'R packet does not match release seal')
        legacy.validate_result(document, coder, freeze['protocol_version'], read_json(packet_raw), sha(packet_raw), 'R first submission')
        documents['R'][relative] = document
        raw_manifest['R'][relative] = {'sha256': sha(raw), 'byte_count': len(raw)}
    d_mapping = read_json(snapshot(release / '抽样清单-研究者.json', context['seal']['output_files']['抽样清单-研究者.json']))
    payload, join = assemble_rows(r_mapping, d_mapping, documents, stats.frozen_design())
    statistics = stats.analyze(payload)
    result = {'status': 'completed_supplementary_AI_content_analysis_not_human_validation', 'phase': 'R600_plus_D668',
              'created_at': datetime.now(timezone.utc).isoformat(), 'statistics': statistics,
              'archive': {'freeze_original': freeze, 'release_seal_original': context['seal'],
                          'R_source_manifest_original': r_sources, 'R_mapping_original': r_mapping, 'D_mapping_original': d_mapping,
                          'raw_coder_submissions': documents, 'original_submission_manifest': raw_manifest,
                          'normalized_analysis_payload': payload, 'ID_join_provenance': join,
                          'input_snapshot_hashes': tracked, 'normalization': 'literal int 0/1 -> string 0/1; literal 待定 -> pending; nothing imputed',
                          'verified_runtime': runtime,
                          'no_machine_predictions_or_consensus_used': True},
              'limits': ['AI following human coding procedure, not actual human experts.',
                         'Intervals condition on fixed operational coding functions and the declared finite sampling design.',
                         'D is supplementary content analysis, not a new unseen validation.']}
    require(set(admin.result_inventory(release)) == set(admin.result_inventory(receipts)) == expected_d, 'D inventory changed during analysis')
    require(set(admin.result_inventory(receipts / 'receipt-records')) == expected_d, 'D receipt-record inventory changed during analysis')
    for path, digest in tracked.items(): require(sha(Path(path).read_bytes()) == digest, 'Input changed during analysis')
    output.parent.mkdir(parents=True, exist_ok=True)
    with partial.open('xb') as handle:
        handle.write(encoded(result)); handle.flush(); os.fsync(handle.fileno())
    os.link(partial, output); partial.unlink()
    return {'status': result['status'], 'output': str(output), 'sha256': sha(output.read_bytes()), 'unique_units': 1268}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze', type=Path, required=True)
    parser.add_argument('--receipts', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.freeze, args.receipts, args.output), ensure_ascii=False, indent=2))
