"""Mechanical formal800 v15 statistics input bridge; no coding or inference.

Only --prepare-only is presently enabled. The separately documented upstream
reception adapter supplies already parsed, genuinely released submissions.
No metadata boolean supplied at this CLI can authenticate a human participant.
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import importlib.util
import json
import math
import sys
from collections import Counter
from fractions import Fraction
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DRAW = ROOT / '05-validation/full800-common-v15-prerelease-sol/coordinator-private/draw-contract.json'
MAPPING = ROOT / '05-validation/full800-common-v15-prerelease-sol/coordinator-private/mapping.json'
CONTRACT = ROOT / '02-methods/prospective-statistical-contract-v2/validation-design-v2.json'
DOMAIN_ENGINE = ROOT / '07-statistics/prospective-engine-domain-sol/metrics_engine.py'
DOMAIN_CONTRACT = ROOT / '07-statistics/prospective-engine-domain-sol/input-contract.json'
YEAR_CANDIDATE = ROOT / '07-statistics/prospective-engine-year-independent-audit-sol/metrics_engine_repaired.py'
YEAR_CONTRACT = ROOT / '07-statistics/prospective-engine-year-independent-audit-sol/input-contract-repaired.json'
DIMS = ('S', 'E', 'Ec', 'I', 'F')
METHODS = ('A', 'B', 'reference', 'rule', 'LLM')
REPLICATES = 5000
SEED = 20261010
CELL_STATES = ('binary', 'semantic_null', 'blank', 'not_submitted',
               'missing_return', 'method_failure', 'dimension_failure')


class BridgeError(ValueError):
    pass


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json_exclusive(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def binding(path):
    path = Path(path).resolve()
    return {'absolute_path': str(path), 'bytes': path.stat().st_size, 'sha256': sha256(path)}


def load_engine(path=DOMAIN_ENGINE):
    spec = importlib.util.spec_from_file_location('readonly_registered_domain_engine', path)
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    return engine


def load_management():
    """Read only the authorized draw/mapping; project a whitelist of metadata."""
    draw = read_json(DRAW)
    raw_mapping = read_json(MAPPING)
    if draw.get('actual_drawn') is not True or draw.get('sampling_execution') != 'completed':
        raise BridgeError('The existing mechanical draw must actually be completed')
    if draw.get('sample_n') != 800 or draw.get('sampling_seed') != SEED:
        raise BridgeError('Expected the registered full800 draw and sampling seed')
    if draw.get('domain_sample_n') != {'remaining': 600, 'exposed': 200}:
        raise BridgeError('Expected the existing remaining600/exposed200 allocation')
    keep = ('source_id', 'stratum', 'domain', 'department', 'N_h', 'n_h',
            'pi', 'pi_exact', 'weight', 'weight_exact', 'A_blind_id', 'B_blind_id')
    rows = [{key: row[key] for key in keep} for row in raw_mapping['records']]
    if len(rows) != 800:
        raise BridgeError('Do not drop assigned units')
    ids = [row['source_id'] for row in rows]
    if len(set(ids)) != 800 or ids != draw['selected_record_ids_in_frame_order']:
        raise BridgeError('Mapping does not match all draw IDs in frozen order')
    if hashlib.sha256(('\n'.join(ids) + '\n').encode()).hexdigest() != draw['selected_ID_UTF8_LF_sha256']:
        raise BridgeError('The original ID UTF8/LF binding differs')
    for method in ('A', 'B'):
        blind = [row[method + '_blind_id'] for row in rows]
        if len(set(blind)) != 800 or any(not isinstance(x, str) or not x for x in blind):
            raise BridgeError('Human blind-ID mapping is not bijective')
    strata = []
    index = {}
    for raw in draw['selected_strata']:
        hid = raw['stratum']
        if hid in index:
            raise BridgeError('Duplicate original stratum')
        N, n = raw['N_h'], raw['n_h']
        if type(N) is not int or type(n) is not int or not 1 <= n <= N:
            raise BridgeError('Invalid original N_h/n_h')
        if n == 1 and N > 1:
            raise BridgeError('Registered engine cannot bootstrap noncensus singleton')
        if raw['domain'] not in ('remaining', 'exposed'):
            raise BridgeError('Unregistered domain')
        if len(raw['selected_ids_sorted']) != n:
            raise BridgeError('Stratum selected count differs from n_h')
        item = {'id': hid, 'N': N, 'n': n, 'department': raw['department'], 'domain': raw['domain']}
        strata.append(item)
        index[hid] = raw
    if len(index) != 41:
        raise BridgeError('Expected all 41 original strata')
    seen = Counter()
    for row in rows:
        raw = index.get(row['stratum'])
        if raw is None:
            raise BridgeError('Unregistered assigned stratum')
        for key in ('domain', 'department', 'N_h', 'n_h'):
            if row[key] != raw[key]:
                raise BridgeError('Assigned metadata differs from frozen stratum: ' + key)
        if row['source_id'] not in raw['selected_ids_sorted']:
            raise BridgeError('Source ID not in its registered draw stratum')
        pi, weight = Fraction(raw['n_h'], raw['N_h']), Fraction(raw['N_h'], raw['n_h'])
        for container in (raw, row):
            if Fraction(container['pi_exact']) != pi or Fraction(container['weight_exact']) != weight:
                raise BridgeError('Exact pi/weight does not match original n_h/N_h')
            if not math.isclose(container['pi'], float(pi), rel_tol=1e-14):
                raise BridgeError('Numeric pi does not match exact pi')
            if not math.isclose(container['weight'], float(weight), rel_tol=1e-14):
                raise BridgeError('Numeric weight does not match exact weight')
        seen[row['stratum']] += 1
    if any(seen[hid] != raw['n_h'] for hid, raw in index.items()):
        raise BridgeError('Missing rows in an original stratum')
    domain_n = {d: sum(r['domain'] == d for r in rows) for d in ('remaining', 'exposed')}
    domain_N = {d: sum(h['N'] for h in strata if h['domain'] == d) for d in domain_n}
    if domain_N != {'remaining': 1444, 'exposed': 3037}:
        raise BridgeError('Domain population mismatch')
    exact_W = {d: sum((Fraction(r['weight_exact']) for r in rows if r['domain'] == d), Fraction()) for d in domain_n}
    if exact_W != {d: Fraction(N) for d, N in domain_N.items()}:
        raise BridgeError('Exact assigned domain weights do not recover original N')
    department_N = {g: sum(h['N'] for h in strata if h['department'] == g) for g in ('NMPA', 'NHSA', 'NHC')}
    if department_N != {'NMPA': 1848, 'NHSA': 2100, 'NHC': 533}:
        raise BridgeError('Department population mismatch')
    design = {'kind': 'stratified_srswor', 'sampling_unit': 'source_unit', 'strata': strata,
              'assigned_ids_sha256': canonical_hash(sorted(ids)), 'domain_partition': 'remaining_exposed',
              'domain_population_N': domain_N}
    summary = {'assigned_n': len(rows), 'dimensions_per_method': len(rows) * len(DIMS),
               'original_strata_n': len(strata), 'domain_assigned_n': domain_n,
               'domain_population_N': domain_N, 'exact_weighted_assigned_population':
               {'ALL': str(sum(exact_W.values())), **{d: str(x) for d, x in exact_W.items()}},
               'department_assigned_n': dict(Counter(row['department'] for row in rows)),
               'department_population_N': department_N, 'all_id_joins_exact': True,
               'blind_A_and_B_each_bijective': True, 'all_stratum_n_and_exact_pi_weight_match': True,
               'source_year_admin_fields_present': False, 'source_year_policy': 'unknown_null; year engine disabled',
               'draw_release_status': draw.get('release_status'), 'mapping_distribution_status': raw_mapping.get('distribution_status'),
               'exposed_domain_label': 'development-exposed audit domain; never holdout'}
    return rows, design, summary


def metadata_template(design):
    flags = ('common_manual', 'common_materials', 'design_before_answers',
             'initial_submissions_before_discussion', 'reference_before_machine_comparison',
             'final_rule_and_LLM_before_test_feedback')
    return {'analysis_stage': 'combined', 'design': design,
            'scope': {'kind': 'full_4481_audit', 'population_N': 4481, 'frame_ids_sha256': None},
            'input_seals': {m: {'sealed': False, 'sha256': None, 'joined_projection_sha256': None} for m in METHODS},
            'artifact_seals': {a: {'sealed': False, 'sha256': None} for a in
                               ('common_manual', 'common_materials', 'design', 'rule_protocol', 'LLM_protocol')},
            'identities': {m: None for m in ('A', 'B', 'reference')},
            'freeze_attestations': {flag: None for flag in flags},
            'identity_and_source_evidence_reviewed': None}


def project_parsed_cells(parsed_cells, method, rows):
    """Pure mechanical projection of an already admitted, parsed method ledger.

    This function does not read files or certify admission. Each cell has only
    join_id/dimension/state/value. A/B join via distinct blind IDs; reference,
    rule and LLM join via source IDs. A/B never become the reference. Missing
    cells retain an explicit not_submitted origin in the sidecar. It is intended
    for the upstream adapter, after that adapter has admitted actual material.
    """
    if method not in METHODS:
        raise BridgeError('Unknown method')
    key = method + '_blind_id' if method in ('A', 'B') else 'source_id'
    join = {row[key]: row['source_id'] for row in rows}
    accepted = {}
    for cell in parsed_cells:
        if set(cell) != {'join_id', 'dimension', 'state', 'value'}:
            raise BridgeError('Parsed statistics cell must contain only join_id/dimension/state/value')
        jid, dim, state, value = (cell[x] for x in ('join_id', 'dimension', 'state', 'value'))
        if jid not in join or dim not in DIMS or state not in CELL_STATES:
            raise BridgeError('Unassigned join, dimension or status')
        slot = (join[jid], dim)
        if slot in accepted:
            raise BridgeError('Duplicate method slot')
        if state == 'binary':
            if type(value) is not int or value not in (0, 1):
                raise BridgeError('Binary requires integer0/1; bool/string prohibited')
        elif value is not None:
            raise BridgeError('Every nonbinary state must carry null, never 0')
        accepted[slot] = {'state': state, 'value': value, 'origin': 'provided_parsed_cell'}
    outputs, status_rows = {}, []
    for row in rows:
        cells = {}
        for dim in DIMS:
            cell = accepted.get((row['source_id'], dim),
                                {'state': 'not_submitted', 'value': None, 'origin': 'absent_parsed_cell'})
            cells[dim] = cell
            status_rows.append({'unit_id': row['source_id'], 'method': method, 'dimension': dim, **cell})
        # All-method missing and failure remain distinct in the retained ledger.
        states = [cell['state'] for cell in cells.values()]
        if all(state in ('not_submitted', 'missing_return') for state in states):
            output = None
        elif all(state == 'method_failure' for state in states):
            output = {'status': 'execution_failure', 'labels': {}, 'failure_code': 'reported_method_failure'}
        else:
            if 'method_failure' in states:
                raise BridgeError('Method failure must cover all five dimensions; inconsistent parsed ledger')
            labels, dimension_status = {}, {}
            for dim, cell in cells.items():
                labels[dim] = cell['value']
                if cell['state'] not in ('binary', 'semantic_null'):
                    dimension_status[dim] = 'execution_failure'
            output = {'status': 'completed', 'labels': labels}
            if dimension_status:
                output['dimension_status'] = dimension_status
        outputs[row['source_id']] = output
    if len(status_rows) != 4000 or len(outputs) != 800:
        raise BridgeError('Never drop assigned source or dimension slots')
    return outputs, status_rows


def coverage_summary(status_rows, rows):
    """A coverage report, not an acceptance test and not a numeric score gate."""
    lookup = {row['source_id']: row for row in rows}
    result = {}
    for method in sorted({row['method'] for row in status_rows}):
        result[method] = {}
        for domain in ('ALL', 'remaining', 'exposed'):
            selected = [cell for cell in status_rows if cell['method'] == method and
                        (domain == 'ALL' or lookup[cell['unit_id']]['domain'] == domain)]
            result[method][domain] = {}
            for dim in DIMS:
                cells = [cell for cell in selected if cell['dimension'] == dim]
                counts = Counter(cell['state'] for cell in cells)
                weight = {state: str(sum((Fraction(lookup[cell['unit_id']]['weight_exact'])
                                         for cell in cells if cell['state'] == state), Fraction()))
                          for state in CELL_STATES}
                result[method][domain][dim] = {'assigned_n': len(cells), 'state_n': dict(counts),
                                              'state_weight_exact': weight,
                                              'all_assigned_dimensions_binary': counts.get('binary', 0) == len(cells),
                                              'metric_interpretation': 'determinate pair subdomain if any unresolved; not full800 coverage'}
    return result


def project_xlsx_derived_cells(derived_rows, side, rows):
    """Mechanical adapter for formal800-xlsx-reception-1 derived-A/B.jsonl.

    Called only AFTER upstream admission. The upstream adapter retains the exact
    XLSX bytes, free-text reasons, cell positions, normalization and declarations;
    none of those is reclassified as an original human JSON submission here.
    unfilled is an unfilled blank, never semantic_null. Invalid content cannot
    enter numerical analysis. A missing method/file is handled separately as
    not_submitted, without inventing a 4000-row submission.
    """
    if side not in ('A', 'B') or len(derived_rows) != 4000:
        raise BridgeError('Expected one independently parsed A/B ledger with 4000 assigned slots')
    assigned = {row[side + '_blind_id'] for row in rows}
    projected, seen = [], set()
    for raw in derived_rows:
        jid, dim = raw.get('blind_id'), raw.get('dimension')
        if raw.get('side') != side or jid not in assigned or dim not in DIMS:
            raise BridgeError('XLSX derived row does not join its own assigned blind side')
        if raw.get('expected_blind_id') != jid or raw.get('expected_dimension') != dim:
            raise BridgeError('XLSX derived row changed the issued slot binding')
        if (jid, dim) in seen:
            raise BridgeError('Duplicate independent XLSX slot')
        seen.add((jid, dim))
        status, value = raw.get('completion_status'), raw.get('value')
        if status == 'filled':
            if type(value) is not int or value not in (0, 1):
                raise BridgeError('Filled normalized XLSX value must be integer0/1')
            state = 'binary'
        elif status == 'unfilled':
            if value is not None:
                raise BridgeError('Unfilled XLSX slot carries a nonnull value')
            state = 'blank'
        else:
            raise BridgeError('Invalid or unsupported XLSX content must remain upstream; no calculation')
        projected.append({'join_id': jid, 'dimension': dim, 'state': state, 'value': value})
    if seen != {(jid, dim) for jid in assigned for dim in DIMS}:
        raise BridgeError('XLSX parsed assigned coverage differs')
    return project_parsed_cells(projected, side, rows)


def assemble_engine_payload(parsed_inputs, sealed_metadata, rows, design):
    """Pure conversion candidate for an upstream ADMITTED set of parsed files.

    No file is opened here and no actual person or release is authenticated.
    The caller must already possess actual stage-specific release/reception/seal
    evidence. This is deliberately not an alternative to upstream admission.
    parsed_inputs maps a method to its independent minimal 4000-slot projection.
    The original raw-byte SHA is supplied by its existing input_seals; only the
    mechanically joined projection hash is derived here, never a credible-ref
    or independent-human flag. The CLI remains fail-closed pending actual files.
    """
    metadata = copy.deepcopy(sealed_metadata)
    stage = metadata.get('analysis_stage')
    active = {'human_first': ('A', 'B'), 'machine_reference': ('reference', 'rule', 'LLM'),
              'combined': METHODS}.get(stage)
    if active is None or set(parsed_inputs) != set(active):
        raise BridgeError('Independent parsed methods must exactly match the registered analysis stage')
    if canonical_hash(metadata.get('design')) != canonical_hash(design):
        raise BridgeError('Do not change the frozen800 original design')
    if metadata.get('scope', {}).get('kind') != 'full_4481_audit' or metadata['scope'].get('population_N') != 4481:
        raise BridgeError('full800 is the registered all4481 audit design')
    if 'year_mapping' in metadata:
        raise BridgeError('Year candidate not promoted; no verified per-source mapping in this delivery')
    projections, all_statuses = {}, []
    for method in active:
        outputs, statuses = project_parsed_cells(parsed_inputs[method], method, rows)
        projections[method] = outputs
        all_statuses.extend(statuses)
    records = [{'unit_id': row['source_id'], 'stratum_id': row['stratum'], 'department': row['department'],
                'outputs': {method: projections[method][row['source_id']] for method in active}} for row in rows]
    engine = load_engine()
    for method in active:
        seal = metadata.get('input_seals', {}).get(method)
        if not isinstance(seal, dict) or seal.get('sealed') is not True or not engine._valid_hash(seal.get('sha256')):
            raise BridgeError('Missing existing original submission seal for ' + method)
        projected_hash = engine.projection_hash(records, method)
        previous = seal.get('joined_projection_sha256')
        if previous is not None and previous != projected_hash:
            raise BridgeError('Existing joined projection differs: ' + method)
        seal['joined_projection_sha256'] = projected_hash
    # Engine prepare validates seals, assigned IDs, state shape and original n_h.
    payload = {'data_role': 'sealed_project', 'metadata': metadata, 'records': records}
    engine.prepare(payload)
    return payload, all_statuses, coverage_summary(all_statuses, rows)


def verify_metadata_only(rows, design):
    """Call original prepare/Rao-Wu functions with no supplied label values.

    Temporary data_role=synthetic is only a parser-shape device in memory. No
    analyze() call is made, no synthetic predictions or agreement values exist.
    The actual ID/stratum/N/n projection and W are administrative draw data.
    """
    import numpy as np
    engine = load_engine()
    payload = {'data_role': 'synthetic', 'metadata': {'analysis_stage': 'human_first', 'design': design,
               'scope': {'kind': 'full_4481_audit', 'population_N': 4481}},
               'records': [{'unit_id': row['source_id'], 'stratum_id': row['stratum'],
                            'department': row['department'], 'outputs': {}} for row in rows]}
    prepared = engine.prepare(payload)
    if len(prepared['records']) != 800:
        raise BridgeError('Registered engine dropped units')
    W = engine.rao_wu_weights(prepared, replicates=REPLICATES, seed=SEED)
    if W.shape != (5000, 800) or not np.isfinite(W).all():
        raise BridgeError('Original full-design W shape/finite check failed')
    denominators = {}
    for domain, expected in (('ALL', 4481), ('remaining', 1444), ('exposed', 3037)):
        mask = np.ones(800, dtype=bool) if domain == 'ALL' else prepared['unit_domains'] == domain
        totals = W @ mask.astype(float)
        maximum_error = float(np.max(np.abs(totals - expected)))
        if maximum_error > 1e-8:
            raise BridgeError('Common original W does not retain domain denominator')
        denominators[domain] = {'expected_denominator': expected, 'mask_length': len(mask),
                                'selected_n': int(mask.sum()), 'replicate_denominator_min': float(totals.min()),
                                'replicate_denominator_max': float(totals.max()),
                                'max_absolute_floating_error': maximum_error}
    return {'verification_kind': 'actual_draw_management_metadata_only; no label/result analysis',
            'parser_shape_device': 'synthetic role only in memory with every output absent; no predictions',
            'engine_entry': str(DOMAIN_ENGINE), 'engine_sha256': sha256(DOMAIN_ENGINE),
            'assigned_ids_sha256': design['assigned_ids_sha256'],
            'common_W_shape': list(W.shape), 'bootstrap_replicates': REPLICATES, 'bootstrap_seed': SEED,
            'common_W_sha256': hashlib.sha256(np.ascontiguousarray(W).tobytes()).hexdigest(),
            'common_W_denominator_checks': denominators, 'analyze_called': False,
            'real_label_values_read': 0, 'numeric_results_generated': 0, 'formal_acceptance': False}


def prepare_only(output_dir):
    # New output directory only. Original files remain read-only.
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(mode=0o700, parents=False, exist_ok=False)
    rows, design, summary = load_management()
    meta = metadata_template(design)
    write_json_exclusive(output_dir / 'analysis-metadata.UNFILLED.template.json',
                         {'status': 'prepare_only_unfilled_not_an_execution', 'metadata': meta})
    records = [{'unit_id': row['source_id'], 'stratum_id': row['stratum'], 'department': row['department'],
                'outputs': {method: None for method in METHODS}} for row in rows]
    write_json_exclusive(output_dir / 'engine-input.UNFILLED.template.json',
                         {'data_role': None, 'bridge_status': 'prepare_only_unfilled_engine_must_reject',
                          'metadata': meta, 'records': records})
    write_json_exclusive(output_dir / 'assigned-design-metadata.json',
                         {'status': 'actual_draw_management_metadata_only', 'bindings': [binding(DRAW), binding(MAPPING)],
                          'records': [{**row, 'policy_year': None,
                                       'policy_year_status': 'no_authorized_verified_per_source_year_map'} for row in rows]})
    write_json_exclusive(output_dir / 'draw-design-readback.json', summary)
    for method in METHODS:
        join_key = method + '_blind_id' if method in ('A', 'B') else 'source_id'
        with (output_dir / (method + '-parsed4000.UNFILLED.slots.csv')).open('x', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=('join_id', 'dimension', 'state', 'value'))
            writer.writeheader()
            for row in rows:
                for dim in DIMS:
                    writer.writerow({'join_id': row[join_key], 'dimension': dim, 'state': 'not_submitted', 'value': ''})
    write_json_exclusive(output_dir / 'metadata-only-entry-validation.json', verify_metadata_only(rows, design))
    write_json_exclusive(output_dir / 'missing-upstream.json', missing_upstream())
    return {'status': 'prepare_only_complete_unfilled', 'output_dir': str(output_dir), **summary,
            'no_formal_release_or_submission_assumed': True}


def missing_upstream():
    return {'status': 'blocked_before_labels_currently_no_formal800_execution',
            'actual_known_missing': [
                'final joint formal800 common-v15 release; 00131/F real-person decision and resulting manual/material release handled upstream',
                'actual A and B independent initial submissions, each 800x5 slots, frozen before discussion with real-user execution/independence declaration',
                'separately retained credible machine-blind human adjudication reference and its submission seal',
                'final rule and primary LLM real800 results and their independent seals/protocol bindings',
                'existing upstream reception output and release/independence/seal review contract for admitted true files',
                'final common manual/material/design/rule_protocol/LLM_protocol artifact bindings and target-frame-ID binding'],
            'year_status': 'no permitted verified per-source year map; null retained in administrative template; year interface disabled',
            'missing_is_not_zero': True, 'reference_is_not_auto_A_or_B': True,
            'no_0_80_score_gate_on_calculation': True,
            'truth_limit': 'SHA256 checks integrity, not human identity or source truth; reviewed actual release/submission evidence belongs to upstream reception',
            'no_new_research_gate': 'No old JSON explanation sidecar/eight-field requirement; no added statistics, threshold or CI gate',
            'no_authenticated_execute_adapter_yet': True,
            'registered_engine_year_candidate_status': 'read-only independent repair candidate not promoted'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--prepare-only', action='store_true')
    group.add_argument('--calculate', action='store_true')
    group.add_argument('--convert-only', action='store_true')
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--analysis-stage', choices=('human_first', 'machine_reference', 'combined'), default='combined')
    parser.add_argument('--method-input', action='append', default=[], metavar='METHOD=PATH',
                        help='Future admitted parsed input; never inspected before upstream formal admission')
    parser.add_argument('--upstream-reception', type=Path,
                        help='Existing reviewed upstream admission record; schema alignment pending')
    args = parser.parse_args()
    if not args.prepare_only:
        # Fail before opening result inputs. There is no authentic upstream
        # admission/release artifact available in this delivery. Adding manual
        # true flags would bypass real execution evidence, so is not supported.
        print(json.dumps({**missing_upstream(), 'status': 'fail_closed_before_result_inputs', 'requested_mode':
                          'calculate' if args.calculate else 'convert-only',
                          'method_input_files_opened': 0}, ensure_ascii=False, indent=2))
        return 2
    if args.method_input or args.upstream_reception:
        parser.error('--prepare-only cannot read label/reception inputs')
    if args.output_dir is None:
        parser.error('--prepare-only requires a new --output-dir')
    try:
        print(json.dumps(prepare_only(args.output_dir), ensure_ascii=False, indent=2))
    except (BridgeError, FileExistsError) as error:
        parser.exit(2, str(error) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
