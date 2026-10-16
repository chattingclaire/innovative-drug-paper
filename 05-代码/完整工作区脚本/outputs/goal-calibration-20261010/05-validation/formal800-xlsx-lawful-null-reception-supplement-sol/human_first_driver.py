"""Bound XLSX reception -> registered human_first engine, no human authentication.

Supplement only: the original bridge.py preparation limits and seal stay intact.
--convert/--calculate require an actual receive report with both existing content
qualifications and original release/declarations, plus an explicitly SHA-bound
human_first metadata file. --coverage-only can retain lawful partial receive
content as pending diagnostics. dry-run can never enter real conversion/analysis.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ADAPTER = HERE / 'adapter.py'
spec = importlib.util.spec_from_file_location('sealed_formal800_preparation_bridge', HERE / 'bridge.py')
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


class ReceptionError(bridge.BridgeError):
    pass


def require(condition, message):
    if not condition:
        raise ReceptionError(message)


def verify_binding(item):
    require(isinstance(item, dict), 'binding must be a mapping')
    path = Path(item.get('path', item.get('absolute_path', ''))).resolve()
    require(path.is_file(), 'bound file is missing: ' + str(path))
    raw = path.read_bytes()
    require(type(item.get('bytes')) is int and len(raw) == item['bytes'], 'bound byte size differs: ' + str(path))
    require(bridge.sha256(path) == item.get('sha256'), 'bound SHA differs: ' + str(path))
    return path


def verify_prior_output_seal():
    """The already sealed bridge source/output files may not change."""
    seal = bridge.read_json(ROOT / '07-statistics/formal800-v15-statistics-input-bridge-sol/output-seal.json')
    for item in seal['members']:
        verify_binding(item)
    return len(seal['members'])


def verify_reception_files(directory):
    """Byte integrity only; no derived coding values are parsed here."""
    directory = Path(directory).resolve()
    require(directory.is_dir(), 'upstream reception directory is missing')
    seal = bridge.read_json(directory / 'seal.json')
    require(seal.get('version') == 'formal800-xlsx-lawful-null-reception-2', 'unsupported existing reception version')
    members = {}
    for item in seal.get('output_members', []):
        path = verify_binding(item)
        require(directory in path.parents, 'output member is outside its sealed reception directory')
        name = path.relative_to(directory).as_posix()
        require(name not in members and name != 'seal.json', 'duplicate/self-referential reception member')
        members[name] = item
    inventory = {path.relative_to(directory).as_posix() for path in directory.rglob('*')
                 if path.is_file() and path.name != 'seal.json'}
    require(set(members) == inventory, 'reception seal does not cover every stored output file')
    for name in ('report.json', 'original-A.xlsx', 'original-B.xlsx', 'derived-A.jsonl', 'derived-B.jsonl'):
        require(name in members, 'required reception output not sealed: ' + name)
    count = len(members)
    for group in ('input_bindings', 'reused_helper_bindings', 'input_xlsx'):
        require(isinstance(seal.get(group), dict), 'missing reception seal group: ' + group)
        for item in seal[group].values():
            verify_binding(item)
            count += 1
    require('adapter_code' in seal, 'reception does not bind its adapter code')
    require(verify_binding(seal['adapter_code']) == ADAPTER.resolve(), 'reception adapter path differs')
    count += 1
    report = bridge.read_json(directory / 'report.json')
    require(report.get('version') == seal['version'], 'report/seal versions differ')
    verify_binding(report['binding_contract'])
    count += 1
    require(seal.get('original_byte_copies_verified') is True, 'upstream original copies were not verified')
    for side in ('A', 'B'):
        sr = report.get('sides', {}).get(side)
        require(isinstance(sr, dict), 'missing independent side report')
        archive_path = verify_binding(sr['archived_original'])
        verify_binding(sr['input_original'])
        count += 2
        require(archive_path == directory / ('original-' + side + '.xlsx'), 'archived original path differs')
        require(sr['archived_original']['sha256'] == members['original-' + side + '.xlsx']['sha256'] ==
                sr['input_original']['sha256'] == seal['input_xlsx'][side]['sha256'],
                'original XLSX bindings disagree')
    require(seal['input_bindings']['mapping']['sha256'] == bridge.sha256(bridge.MAPPING), 'reception mapping differs')
    require(seal['input_bindings']['draw_contract']['sha256'] == bridge.sha256(bridge.DRAW), 'reception draw differs')
    return directory, report, seal, members, count


def require_actual_receive(report, complete):
    require(report.get('command') == 'receive', 'upstream command is dry-run, not an actual receive')
    require(report.get('status') == 'originals_archived_content_parsed', 'upstream content was not lawfully parsed')
    require(report.get('alignment_withheld_due_to_content_errors') is False, 'invalid content alignment is withheld')
    for side in ('A', 'B'):
        sr = report['sides'][side]
        require(sr.get('content_valid') is True and sr.get('issues') == [], 'upstream content invalid for ' + side)
        require(sr.get('expected_rows') == 4000 and sr.get('expected_blind_ids') == 800, 'assigned coverage shape differs')
        if complete:
            q = sr.get('qualification', {})
            require(q.get('status') == 'content_received_on_bound_declarations' and
                    q.get('content_reception_complete') is True and
                    q.get('eligible_for_downstream_content_handoff') is True and
                    q.get('pending') == [] and q.get('issues') == [],
                    'bound-declaration content handoff remains pending for ' + side)
            require(sr.get('fully_completed') is True, 'upstream finished binary/null handoff is internally inconsistent')


def load_readonly_adapter():
    spec = importlib.util.spec_from_file_location('readonly_existing_xlsx_reception_adapter', ADAPTER)
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    return adapter


def recheck_existing_declarations(directory, report, seal, members):
    """Reuse existing qualification logic; do not build a new identity registry."""
    for name in ('release.json', 'declaration-A.json', 'declaration-B.json'):
        require(name in members, 'actual saved release/declaration is missing: ' + name)
    adapter = load_readonly_adapter()
    require(report['binding_contract']['sha256'] == bridge.sha256(adapter.CONTRACT), 'upstream binding contract differs')
    require(seal['input_bindings'] == adapter.BIND['inputs'], 'reception uses other registered source/template inputs')
    require(seal['reused_helper_bindings'] == adapter.BIND['dependencies'], 'reception helper bindings differ')
    release = bridge.read_json(directory / 'release.json')
    declarations = {side: bridge.read_json(directory / ('declaration-' + side + '.json')) for side in ('A', 'B')}
    require(declarations['A'].get('executor_code') != declarations['B'].get('executor_code'), 'A/B declarations name the same executor')
    for side in ('A', 'B'):
        raw = (directory / ('original-' + side + '.xlsx')).read_bytes()
        # submission_A/B is the already bound packet/manual/count metadata, not
        # a coding-value ledger. Actual returned XLSX remains separately sealed.
        data = {'submission': adapter.load_bound('submission_' + side)}
        qualification = adapter.declared_qualification(side, report['sides'][side], raw, data, release, declarations)
        require(qualification['eligible_for_downstream_content_handoff'] is True,
                'existing actual release/independence declaration check failed for ' + side)
    return adapter, release, declarations


def read_derived_projection(directory, rows, adapter=None):
    """After gate (or explicitly authorized blank check), parse independent rows."""
    parsed, all_statuses = {}, []
    joins = {side: {row['source_id']: row[side + '_blind_id'] for row in rows} for side in ('A', 'B')}
    derived_counts = {}
    for side in ('A', 'B'):
        path = directory / ('derived-' + side + '.jsonl')
        raw_rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
        if adapter is not None:
            index = adapter.load_bound('index_' + side)
            bundle = {entry['blind_id']: entry['source_bundle_canonical_sha256'] for entry in index['entries']}
            for record in raw_rows:
                require(record.get('source_bundle_canonical_sha256') == bundle.get(record.get('blind_id')),
                        'derived source bundle binding differs')
        outputs, statuses = bridge.project_xlsx_derived_cells(raw_rows, side, rows)
        cells = [{'join_id': joins[side][cell['unit_id']], 'dimension': cell['dimension'],
                  'state': cell['state'], 'value': cell['value']} for cell in statuses]
        # Reuse the internal minimal projection and compare it with the XLSX
        # projection. Reasons/raw cells stay intact in the upstream originals.
        repeated, _ = bridge.project_parsed_cells(cells, side, rows)
        require(repeated == outputs, 'independent parsed projection differs')
        parsed[side] = cells
        all_statuses.extend(statuses)
        derived_counts[side] = len(raw_rows)
    return parsed, all_statuses, derived_counts


def blank_mechanical_readback(directory):
    """Only the current already-authorized real blank dry-run; no analysis."""
    directory, report, seal, members, hashes_checked = verify_reception_files(directory)
    require(report.get('command') == 'dry-run', 'mechanical blank check requires a dry-run report')
    for side in ('A', 'B'):
        require(report['sides'][side]['counts'] == {'unfilled': 4000}, 'mechanical check is not the real all-blank packet')
        require(report['sides'][side]['qualification']['eligible_for_downstream_content_handoff'] is False,
                'dry-run has an unexpected content qualification')
    rows, design, management = bridge.load_management()
    parsed, statuses, counts = read_derived_projection(directory, rows)
    require(all(cell['state'] == 'blank' and cell['value'] is None for cell in statuses),
            'blank-only check found a value; stop without analysis')
    coverage = bridge.coverage_summary(statuses, rows)
    return {'status': 'mechanical_blank4000x2_join_only_not_a_submission',
            'upstream_reception': str(directory), 'upstream_command': report['command'],
            'reception_bindings_hashed': hashes_checked, 'derived_rows': counts,
            'assigned_source_ids': len(rows), 'independent_slots': len(statuses),
            'all_blank_null_preserved': True, 'source_id_blind_id_dimension_join_verified': True,
            'coverage': coverage, 'real_human_submissions_claimed': 0,
            'binary_labels_created': 0, 'engine_analyze_called': False,
            'formal_acceptance': False}


def metadata_for_human_first(path, expected_sha, report, release, declarations):
    require(isinstance(expected_sha, str) and len(expected_sha) == 64, 'explicit statistics metadata SHA is required')
    require(bridge.sha256(path) == expected_sha, 'statistics metadata exact byte SHA differs')
    document = bridge.read_json(path)
    metadata = document.get('metadata', document)
    require(isinstance(metadata, dict) and metadata.get('analysis_stage') == 'human_first',
            'statistics metadata analysis_stage must be human_first')
    require('year_mapping' not in metadata, 'year mapping not enabled in this finite driver')
    engine = bridge.load_engine()
    for side in ('A', 'B'):
        submission = metadata.get('input_seals', {}).get(side, {})
        require(submission.get('sealed') is True and engine._valid_hash(submission.get('sha256')),
                'actual independent original submission seal missing for ' + side)
        require(submission['sha256'] == report['sides'][side]['archived_original']['sha256'],
                'metadata original XLSX SHA differs for ' + side)
        identity = metadata.get('identities', {}).get(side)
        if isinstance(identity, dict) and identity.get('identity_code') is not None:
            require(identity['identity_code'] == declarations[side]['executor_code'],
                    'metadata identity code differs from the actual saved declaration')
    manual = metadata.get('artifact_seals', {}).get('common_manual', {})
    if manual.get('sha256') is not None:
        require(manual['sha256'] == release['manual']['sha256'], 'metadata common manual differs from actual release')
    # Preserve all identity/freeze flags verbatim for existing engine review.
    # They are assertions, never programmatically authenticated human facts.
    return metadata


def execute(args):
    args._engine_analyze_called = False
    args._execution_output_dir = None
    previous_members = verify_prior_output_seal()
    directory, report, seal, members, hashes_checked = verify_reception_files(args.upstream_reception)
    complete = not args.coverage_only
    require_actual_receive(report, complete=complete)
    if complete:
        require(args.statistics_metadata is not None and args.statistics_metadata_sha256 is not None,
                'convert/calculate requires a genuine statistics metadata file and explicit SHA')
        adapter, release, declarations = recheck_existing_declarations(directory, report, seal, members)
        metadata = metadata_for_human_first(args.statistics_metadata, args.statistics_metadata_sha256,
                                            report, release, declarations)
    else:
        adapter = None
    rows, design, management = bridge.load_management()
    parsed, statuses, counts = read_derived_projection(directory, rows, adapter=adapter)
    coverage = bridge.coverage_summary(statuses, rows)
    if complete:
        payload, statuses, coverage = bridge.assemble_engine_payload(parsed, metadata, rows, design)
    destination = Path(args.output_dir).resolve()
    require(HERE in destination.parents and not destination.exists(), 'output must be a new directory inside this bridge-owned directory')
    destination.mkdir(mode=0o700)
    args._execution_output_dir = destination
    context = {'mode': 'coverage-only' if args.coverage_only else 'calculate' if args.calculate else 'convert',
               'status': 'pending_receive_coverage_diagnostic' if args.coverage_only else 'bound_content_converted_for_human_first',
               'upstream_reception_seal': bridge.binding(directory / 'seal.json'),
               'upstream_report': bridge.binding(directory / 'report.json'),
               'upstream_qualification': {side: report['sides'][side]['qualification'] for side in ('A', 'B')},
               'derived_rows': counts, 'original_bridge_seal_members_unchanged': previous_members,
               'reception_bindings_hashed': hashes_checked, 'formal_acceptance': False,
               'human_identity_independence_or_start_time_authenticated': False,
               'metadata_and_hashes_authenticate_human_identity': False,
               'threshold_is_not_a_running_gate': True,
               'accuracy_reference_or_machine_outputs_used': False,
               'no_blank_null_to_zero': True, 'original_engine_changed': False,
               'incomplete_receive_cannot_claim_complete800_validation': args.coverage_only,
               'engine_analyze_called': bool(args.calculate)}
    if complete:
        context['statistics_metadata'] = bridge.binding(args.statistics_metadata)
        bridge.write_json_exclusive(destination / 'engine-input.json', payload)
    bridge.write_json_exclusive(destination / 'coverage-state.json', coverage)
    with (destination / 'retained-status4000x2.jsonl').open('x', encoding='utf-8') as stream:
        for row in statuses:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True, allow_nan=False) + '\n')
    if args.calculate:
        engine = bridge.load_engine()
        args._engine_analyze_called = True
        result = engine.analyze(payload, replicates=5000, seed=20261010, guard_mode='single_category')
        bridge.write_json_exclusive(destination / 'human-first-results.json', result)
        context['status'] = 'human_first_numerics_executed_not_formal_acceptance'
    bridge.write_json_exclusive(destination / 'execution-context.json', context)
    bridge.write_json_exclusive(destination / 'seal.json',
                         {'status': context['status'], 'self_excluded': True,
                          'members': [bridge.binding(path) for path in sorted(destination.rglob('*')) if path.is_file()],
                          'formal_acceptance': False, 'human_identity_authenticated': False})
    return {'status': context['status'], 'output_dir': str(destination), 'derived_rows': counts,
            'engine_analyze_called': bool(args.calculate), 'formal_acceptance': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--convert', action='store_true')
    modes.add_argument('--calculate', action='store_true')
    modes.add_argument('--coverage-only', action='store_true')
    parser.add_argument('--upstream-reception', required=True, type=Path)
    parser.add_argument('--statistics-metadata', type=Path)
    parser.add_argument('--statistics-metadata-sha256')
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(execute(args), ensure_ascii=False, indent=2))
    except (ReceptionError, bridge.BridgeError, OSError, KeyError, TypeError, ValueError, AttributeError) as error:
        attempted = getattr(args, '_engine_analyze_called', False)
        failure = {'status': 'numerical_execution_failed' if attempted else 'fail_closed_before_numerical_execution',
                   'reason': str(error), 'engine_analyze_called': attempted,
                   'attempt_started': attempted, 'formal_acceptance': False}
        destination = getattr(args, '_execution_output_dir', None)
        if destination is not None:
            try:
                bridge.write_json_exclusive(destination / 'failure.json', failure)
                bridge.write_json_exclusive(destination / 'failure-seal.json',
                    {'status': 'failed_attempt_files_preserved', 'engine_analyze_called': attempted,
                     'attempt_started': attempted, 'self_excluded': True, 'formal_acceptance': False,
                     'members': [bridge.binding(path) for path in sorted(destination.rglob('*')) if path.is_file()]})
                failure['failure_artifacts_saved_in'] = str(destination)
            except (OSError, ValueError) as save_error:
                failure['failure_artifact_write_error'] = str(save_error)
        print(json.dumps(failure, ensure_ascii=False, indent=2))
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
