"""Explicit-bound common-definition statistics; no model/coder calls or label edits.

This entry imports only unchanged, SHA-bound mathematical modules. It never calls
their historical context/reference/method loaders. Preparation does not execute it.
"""
from pathlib import Path
from collections import Counter
from itertools import combinations
import argparse
import hashlib
import importlib
import json
import sys

DIMS = ('S', 'E', 'Ec', 'I', 'F')
GROUPS = ('NMPA', 'NHSA', 'NHC')
EXPECTED_CORPUS = {'NMPA': 1848, 'NHSA': 2100, 'NHC': 533, 'GOV': 443}
HERE = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical_sha(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def bound_path(binding):
    require(isinstance(binding, dict), 'Unbound input')
    path = Path(binding['path'])
    require(path.is_absolute(), 'Binding path must be absolute')
    require(isinstance(binding.get('sha256'), str) and len(binding['sha256']) == 64,
            'A real frozen SHA is required: ' + str(path))
    require(sha(path) == binding['sha256'], 'SHA mismatch: ' + str(path))
    return path


def bound_json(binding):
    return json.loads(bound_path(binding).read_text())


def bound_jsonl(binding):
    rows = [json.loads(line) for line in bound_path(binding).read_text().splitlines() if line.strip()]
    by_id = {r['id']: r for r in rows}
    require(len(by_id) == len(rows), 'Duplicate IDs: ' + binding['path'])
    return by_id


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def write_jsonl(path, rows):
    Path(path).write_text(''.join(json.dumps(r, ensure_ascii=False, allow_nan=False) + '\n' for r in rows))


def mathematics(freeze):
    require(sha(HERE / 'common_statistics01.py') == freeze['entry_sha256'], 'Entry changed after freeze')
    paths = {name: bound_path(binding) for name, binding in freeze['mathematical_sources'].items()}
    require(set(paths) == {'statistical_core_r3', 'statistical_extensions_r3', 'final_attention_r3'},
            'Only the three reviewed mathematical modules are permitted')
    require(len({p.parent for p in paths.values()}) == 1, 'Math modules must share frozen directory')
    sys.path.insert(0, str(next(iter(paths.values())).parent))
    order = ('statistical_core_r3', 'statistical_extensions_r3', 'final_attention_r3')
    modules = {name: importlib.import_module(name) for name in order}
    for name, module in modules.items():
        require(Path(module.__file__).resolve() == paths[name].resolve(), 'Unexpected imported module')
    c, e, a = (modules[n] for n in order)
    require(tuple(c.DIMS) == DIMS and tuple(c.GROUPS) == GROUPS, 'Mathematical definition mismatch')
    return c, e, a


def load_material(manifest):
    material = manifest['material']
    bound_path(material['manual'])
    rule_inputs = bound_jsonl(material['rule_inputs'])
    llm_inputs = bound_jsonl(material['llm_inputs'])
    require(len(rule_inputs) == len(llm_inputs) == 4924 and set(rule_inputs) == set(llm_inputs),
            'Both current material inputs must contain exactly the same 4924 IDs')
    for rid in rule_inputs:
        require(rule_inputs[rid]['input']['unit_text'] == llm_inputs[rid]['text'],
                'Current unit text differs: ' + rid)
    # Equal unit text is not a claim that all source/context material is equal.
    comparison = bound_json(material['source_context_comparison_qa'])
    require(comparison['all_current_unit_text_equal'] is True and comparison['n'] == 4924,
            'Current unit-text QA must be complete')
    for key in ('manual', 'rule_inputs', 'llm_inputs'):
        require(comparison[key + '_sha256'] == material[key]['sha256'], 'Material QA binding differs')
    require(comparison['relationship'] in ('same_shared_material', 'source_supplement_difference_disclosed'),
            'Actual scope relationship must be stated; matching unit_text is insufficient')
    require(comparison.get('context_scope_evidence'), 'Scope equality/difference evidence is required')
    metadata = bound_json(manifest['department_metadata'])
    meta = {Path(r['original_file']).stem: r for r in metadata['rows']}
    require(len(meta) == len(metadata['rows']), 'Duplicate metadata file stem')
    groups = {rid: meta[r['input']['original_file_stem']]['analysis_group'] for rid, r in rule_inputs.items()}
    require(Counter(groups.values()) == Counter(EXPECTED_CORPUS), 'Frozen corpus/department scope differs')
    sources = {rid: r['input'].get('unit_source', r['input']['source']) for rid, r in rule_inputs.items()}
    return {'inputs': rule_inputs, 'llm_inputs': llm_inputs, 'groups': groups, 'sources': sources,
            'metadata': meta, 'material': material, 'source_context_qa': comparison}


def load_methods(manifest, ctx, c):
    methods = {}
    for name in ('rules', 'LLM'):
        entry = manifest['methods'][name]
        require(entry['manual_sha256'] == ctx['material']['manual']['sha256'], 'Method manual not current')
        input_key = 'llm_inputs' if name == 'LLM' else 'rule_inputs'
        require(entry['input_sha256'] == ctx['material'][input_key]['sha256'],
                'Method input not the actual bound input')
        if name == 'LLM':
            # Require terminal execution metadata before opening any labels.
            summary = bound_json(entry['execution_summary'])
            plan = bound_json(entry['run_plan'])
            require(summary['status'] == 'complete_actual_calls_structurally_valid', 'LLM run incomplete')
            require(summary['n'] == 4924 and summary['accepted_batch_count'] == summary['expected_batch_count']
                    == plan['batch_count'] and plan['n'] == 4924, 'LLM completion count mismatch')
            require(summary['selected_tool_event_count'] == 0 and summary['source_unchanged_during_run'] is True,
                    'LLM actual execution/source gate failed')
            require(summary['metric_or_reference_label_based_selection'] is False, 'Output selection not permitted')
            require(summary['input_sha256'] == summary['source_input_current_sha256'] == entry['input_sha256']
                    == plan['input_sha256'], 'LLM executed another input')
            require(summary['plan_sha256'] == entry['run_plan']['sha256'] and
                    summary['prompt_sha256'] == plan['prompt_sha256'] and
                    summary['output_sha256'] == entry['output']['sha256'], 'LLM plan/output differs')
        qa = bound_json(entry['execution_qa'])
        require(qa.get('all_checks_pass') is True, name + ' independent execution QA not passed')
        require(qa['output_sha256'] == entry['output']['sha256'] and qa['input_sha256'] == entry['input_sha256'],
                name + ' execution QA must explicitly bind actual input/output SHA')
        rows = bound_jsonl(entry['output'])
        require(set(rows) == set(ctx['inputs']), name + ' IDs differ from current corpus')
        for rid, row in rows.items():
            labels = row.get('prediction', row)['labels']
            require(set(labels) == set(DIMS), 'Missing/extra dimensions: ' + rid)
            require(all(c.binary(v) or v is None for v in labels.values()), 'Invalid label type: ' + rid)
        methods[name] = rows
    return methods


def pair_counts(rows, ids, a, b, c):
    counts = [0, 0, 0, 0]
    pending = []
    for rid in ids:
        x, y = c.label(rows[rid], a), c.label(rows[rid], b)
        if not (c.binary(x) and c.binary(y)):
            pending.append(rid)
        else:
            counts[{(1, 1): 0, (1, 0): 1, (0, 1): 2, (0, 0): 3}[x, y]] += 1
    both, a_only, b_only, neither = counts
    div = lambda x, y: x / y if y else None
    return {'dimension_a': a, 'dimension_b': b, 'unit_n': len(ids), 'valid_n': sum(counts),
            'pending_ids': pending, 'both_n': both, 'a_only_n': a_only, 'b_only_n': b_only,
            'neither_n': neither, 'both_unit_fraction': div(both, sum(counts)),
            'p_b_given_a': div(both, both + a_only), 'p_a_given_b': div(both, both + b_only),
            'denominator_scope': 'complete pairs; pending retained, never set to zero'}


def descriptive(manifest, ctx, methods, c, e, a):
    out = {'scope': 'full4481 descriptive comparison of two actual machine outputs',
           'reference': None, 'confidence_intervals': None, 'departments': {},
           'source_context_relationship': ctx['source_context_qa'],
           'method_identity': {k: v['method_id'] for k, v in manifest['methods'].items()}}
    diff = []
    for group in ('ALL', *GROUPS):
        ids = sorted(r for r in ctx['inputs'] if ctx['groups'][r] in GROUPS and
                     (group == 'ALL' or ctx['groups'][r] == group))
        profiles = {}
        for name, rows in methods.items():
            pending = [r for r in ids if not all(c.binary(c.label(rows[r], d)) for d in DIMS)]
            pending_set = set(pending)
            complete = [r for r in ids if r not in pending_set]
            # Full estimates are withheld if pending; conditional values remain explicitly separate.
            conditional = a.full_summary(rows, complete) if complete else None
            if conditional is not None:
                conditional['coverage'] = {d: conditional['coding_count'][d] / len(complete) for d in DIMS}
            profiles[name] = {'unit_n': len(ids), 'complete_n': len(complete), 'pending_ids': pending,
                              'profile': conditional if not pending else None,
                              'complete_support_profile': conditional if pending else None,
                              'all10_pairs': [pair_counts(rows, ids, x, y, c) for x, y in combinations(DIMS, 2)]}
        full = [profiles[n]['profile'] for n in ('rules', 'LLM')]
        qdiff = ({d: full[0]['attention_share'][d] - full[1]['attention_share'][d]
                  if full[0]['attention_share'][d] is not None and full[1]['attention_share'][d] is not None
                  else None for d in DIMS} if all(p is not None for p in full) else None)
        out['departments'][group] = {'methods': profiles, 'rules_minus_LLM_attention_share': qdiff}
    for rid in sorted(ctx['inputs']):
        if ctx['groups'][rid] not in GROUPS:
            continue
        left, right = methods['rules'][rid], methods['LLM'][rid]
        differing = [d for d in DIMS if c.label(left, d) != c.label(right, d)]
        pending = [d for d in DIMS if not (c.binary(c.label(left, d)) and c.binary(c.label(right, d)))]
        if differing or pending:
            diff.append({'id': rid, 'group': ctx['groups'][rid], 'dimensions_differing': differing,
                         'pending_dimensions': pending, 'current_text': ctx['llm_inputs'][rid]['text'],
                         'material_row_sha256': canonical_sha(ctx['llm_inputs'][rid]),
                         'source': ctx['sources'][rid], 'rules_actual_row': left, 'LLM_actual_row': right})
    out['difference_unit_n'] = len(diff)
    return out, diff


def human_references(binding, ctx, c):
    """Require actual current human reviews; no historical A/B/T fallback."""
    ref = bound_json(binding)
    require(ref['review_round_id'] and ref['actual_human_review_completed'] is True,
            'Current actual human reference not yet bound')
    require(ref['manual_sha256'] == ctx['material']['manual']['sha256'], 'Human manual differs')
    require(ref['material_input_sha256'] == ctx['material']['llm_inputs']['sha256'], 'Human material differs')
    qa = bound_json(ref['review_execution_qa'])
    require(qa['all_checks_pass'] is True and qa['actual_human_identity_verified'] is True and
            qa['review_round_id'] == ref['review_round_id'] and qa['manual_sha256'] == ref['manual_sha256'] and
            qa['material_input_sha256'] == ref['material_input_sha256'], 'Actual current human review QA required')
    registry = {r['reviewer_id']: r for r in ref['reviewer_registry']}
    require(len(registry) == len(ref['reviewer_registry']), 'Duplicate reviewer identity')
    def identity(reviewer, event):
        who = registry[reviewer]
        require(who['human_reviewer'] is True and who['AI_agent'] is False and
                who['actual_identity'] and event in who['completed_review_event_ids'],
                'Actual human identity/completed review evidence required')
    refs = {}
    for coder in ('A', 'B'):
        rows = bound_jsonl(ref['independent_reviews'][coder]['output'])
        require(qa['independent_review_output_sha256'][coder] == ref['independent_reviews'][coder]['output']['sha256'],
                'Human review QA/output binding differs')
        for rid, row in rows.items():
            identity(row['reviewer_id'], row['review_event_id'])
            require(row['manual_sha256'] == ref['manual_sha256'] and
                    row['material_row_sha256'] == canonical_sha(ctx['llm_inputs'][rid]),
                    'Human row is not current shared material: ' + rid)
            require(set(row['labels']) == set(DIMS) and
                    all(c.binary(v) or v is None for v in row['labels'].values()), 'Human label shape invalid')
        refs[coder] = rows
    require(set(refs['A']) == set(refs['B']) and set(refs['A']), 'A/B sample IDs differ/empty')
    for rid in refs['A']:
        require(refs['A'][rid]['reviewer_id'] != refs['B'][rid]['reviewer_id'], 'A/B identities are not independent')
    if ref.get('consensus') is not None:
        entry = ref['consensus']
        require(entry['assembly_policy'] == 'agreement_or_actual_human_adjudication', 'T replacement is not consensus')
        require(qa['consensus_output_sha256'] == entry['output']['sha256'] and
                qa['adjudication_log_sha256'] == entry['adjudication_log']['sha256'], 'Consensus QA/log binding differs')
        rows = bound_jsonl(entry['output'])
        records = bound_json(entry['adjudication_log'])['records']
        logs = {r['record_id']: r for r in records}
        require(len(logs) == len(records) and set(rows) == set(refs['A']), 'Consensus/log coverage invalid')
        for rid, row in rows.items():
            require(row['manual_sha256'] == ref['manual_sha256'] and
                    row['material_row_sha256'] == canonical_sha(ctx['llm_inputs'][rid]), 'Consensus material differs')
            for dim in DIMS:
                z = row['labels'][dim]
                require(c.binary(z) or z is None, 'Consensus label invalid')
                x, y = (c.label(refs[n][rid], dim) for n in ('A', 'B'))
                resolution = row['dimension_resolution'][dim]
                if resolution['basis'] == 'independent_agreement':
                    require(c.binary(x) and x == y == z, 'Agreement consensus does not follow A/B')
                elif resolution['basis'] == 'actual_human_adjudication':
                    log = logs[resolution['adjudication_record_id']]
                    identity(log['adjudicator_id'], log['review_event_id'])
                    require(log['id'] == rid and log['dimension'] == dim and log['final_label'] == z and
                            log['manual_sha256'] == ref['manual_sha256'] and
                            log['material_row_sha256'] == canonical_sha(ctx['llm_inputs'][rid]),
                            'Actual adjudication record does not bind final dimension')
                else:
                    require(resolution['basis'] == 'unresolved' and z is None, 'Unknown consensus policy')
        refs['consensus'] = rows
    return ref, refs


def sampling_context(ref, ctx, freeze, c):
    design = bound_json(ref['sampling_design'])
    sample = {r['original_id']: r for r in design['sample']}
    require(len(sample) == len(design['sample']), 'Duplicate sample IDs')
    for rid, row in sample.items():
        require(rid in ctx['inputs'] and row['group'] == ctx['groups'][rid], 'Sample department/ID differs')
        require(row['unit_text_sha256'] == hashlib.sha256(ctx['llm_inputs'][rid]['text'].encode()).hexdigest(),
                'Sample current text changed')
    mode = ref['inference_mode']
    require(mode in ('point_only', 'original_probability180_and_challenge60'), 'Unapproved inference mode')
    if mode == 'original_probability180_and_challenge60':
        require(ref['sampling_design'] == freeze['original_sampling_design'],
                'Original 180 bootstrap cannot be applied to a new 240 design')
        require(design['frame_N_by_group'] == c.EXPECTED_ELIGIBLE and
                Counter((r['component'], r['group']) for r in sample.values()) == Counter(
                    {('probability_canonical', g): 60 for g in GROUPS} |
                    {('enriched_challenge', g): 30 for g in ('NMPA', 'NHSA')}), 'Original design differs')
        for row in sample.values():
            if row['component'] == 'probability_canonical':
                n, population = row['sample_n'], row['canonical_frame_N']
                require(n == 60 and population == c.EXPECTED_ELIGIBLE[row['group']] and
                        abs(row['inclusion_probability'] - n / population) < 1e-12 and
                        abs(row['analysis_weight'] - population / n) < 1e-12, 'Probability design invalid')
            else:
                require(row['analysis_weight'] is None, 'Challenge cases have no population weights')
    return {**ctx, 'design': design, 'sample': sample}, mode


def human_statistics(ref, refs, ctx, methods, c, mode):
    require(set(refs['A']) == set(ctx['sample']), 'Reference sample differs from bound design')
    components = sorted({r['component'] for r in ctx['sample'].values()})
    records = []
    comparisons = [('A_B', refs['A'], refs['B'], 'independent pre-adjudication A/B', False)]
    if 'consensus' in refs:
        comparisons += [(name, rows, refs['consensus'], 'actual current human consensus', True)
                        for name, rows in methods.items()]
    for component in components:
        eligible = sorted(r for r, row in ctx['sample'].items() if row['component'] == component)
        for group in ('ALL', *GROUPS):
            ids = [r for r in eligible if group == 'ALL' or ctx['sample'][r]['group'] == group]
            if not ids:
                continue
            kinds = ['unweighted']
            if mode == 'original_probability180_and_challenge60' and component == 'probability_canonical':
                kinds.append('eligible_design_weighted')
            for kind in kinds:
                w = c.weighting(ctx, ids, kind)
                factors = None
                if mode == 'original_probability180_and_challenge60':
                    mechanism = ('department_unit_rescaled_SRSWOR' if component == 'probability_canonical'
                                 else 'department_unit_conditional_WR')
                    factors = c.replicate_factors(ctx, ids, component, mechanism)
                for name, left, right, reference, directional in comparisons:
                    for dim in DIMS:
                        matrix, valid = c.cells(left, right, dim, ids)
                        counts = (w[:, None] * matrix).sum(axis=0)
                        point = c.metrics(counts)[0]
                        names = c.METRIC_NAMES if directional else ('kappa', 'agreement', 'left_positive_rate', 'right_positive_rate')
                        bootstrap = c.metrics((factors * w[None, :]) @ matrix) if factors is not None else None
                        metrics = {n: {'point': c.safe(point[c.METRIC_NAMES.index(n)]),
                                       'CI': c.interval(bootstrap[:, c.METRIC_NAMES.index(n)]) if bootstrap is not None else None}
                                   for n in names}
                        records.append({'component': component, 'group': group, 'weighting': kind,
                                        'method': name, 'reference': reference, 'dimension': dim,
                                        'unit_n': len(ids), 'valid_n': int(valid.sum()),
                                        'pending_ids': [r for r, ok in zip(ids, valid) if not ok],
                                        'cell_order': ['11', '10', '01', '00'], 'cells': counts.tolist(),
                                        'metrics': metrics, 'inference_mode': mode,
                                        'CI_scope': 'original frozen sampling design; conditional on labels' if factors is not None else None})
    return {'review_round_id': ref['review_round_id'], 'actual_human_reference': True,
            'consensus_bound': 'consensus' in refs, 'records': records,
            'unresolved_policy': 'pairwise missing retained; no automatic zero or T replacement',
            'sampling_scope': 'original eligible canonical frame only when its exact frozen design is bound; never full4481 by default'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bindings', type=Path, required=True)
    parser.add_argument('--bindings-sha256', required=True)
    parser.add_argument('--mode', choices=('descriptive', 'human'), required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    require(not args.out.exists(), 'Never overwrite an earlier calculation')
    manifest = bound_json({'path': str(args.bindings.resolve()), 'sha256': args.bindings_sha256})
    require(manifest['execution_authorized_by_root'] is True and manifest['round_id'], 'Unreviewed statistical binding')
    freeze = bound_json(manifest['code_and_design_freeze'])
    c, e, a = mathematics(freeze)
    ctx = load_material(manifest)
    # Human gate precedes machine-label access in human mode.
    if args.mode == 'human':
        ref, refs = human_references(manifest['human_reference_manifest'], ctx, c)
        ctx, inference = sampling_context(ref, ctx, freeze, c)
    methods = load_methods(manifest, ctx, c)
    args.out.mkdir(parents=True, exist_ok=False)
    write_json(args.out / 'execution_binding.json', {'bindings': str(args.bindings.resolve()),
               'bindings_sha256': args.bindings_sha256, 'mode': args.mode,
               'code_and_design_freeze': manifest['code_and_design_freeze'],
               'human_reference_manifest': manifest.get('human_reference_manifest') if args.mode == 'human' else None,
               'adoption_status': manifest['adoption_status'], 'no_model_or_coder_calls': True})
    if args.mode == 'descriptive':
        result, differences = descriptive(manifest, ctx, methods, c, e, a)
        write_json(args.out / 'full4481_descriptive.json', result)
        write_jsonl(args.out / 'full4481_unit_differences.jsonl', differences)
    else:
        write_json(args.out / 'human_reference_statistics.json', human_statistics(ref, refs, ctx, methods, c, inference))
    files = {p.name: sha(p) for p in args.out.iterdir() if p.is_file()}
    write_json(args.out / 'completion.json', {'status': 'complete_bound_statistics', 'mode': args.mode,
               'files_sha256': files, 'source_inputs_and_labels_modified': False})
    print(json.dumps({'status': 'complete_bound_statistics', 'mode': args.mode, 'out': str(args.out.resolve())}, ensure_ascii=False))


if __name__ == '__main__':
    main()
