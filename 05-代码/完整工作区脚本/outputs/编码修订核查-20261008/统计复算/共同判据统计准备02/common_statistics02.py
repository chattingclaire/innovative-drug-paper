"""Explicit-bound common-definition statistics; no model/coder calls or label edits.

This entry imports only unchanged, SHA-bound mathematical modules. It never calls
their historical context/reference/method loaders. Preparation does not execute it.
"""
from pathlib import Path
from collections import Counter
from itertools import combinations
import argparse
import copy
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
    require(sha(HERE / 'common_statistics02.py') == freeze['entry_sha256'], '02 entry changed after freeze')
    baseline = bound_json(freeze['baseline_code_and_design_freeze'])
    require(sha(bound_path(freeze['baseline_entry'])) == baseline['entry_sha256'], '01 baseline entry changed')
    require(freeze['mathematical_sources'] == baseline['mathematical_sources'], '01 mathematics lock changed')
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


def load_composite(entry, ctx):
    """Read actual provenance before labels; retain each component's honest status."""
    summary = bound_json(entry['execution_summary'])
    plan = bound_json(entry['composite_plan'])
    require(summary['status'] == 'complete_actual_composite_lineage', 'Composite incomplete')
    require(summary['n'] == plan['n'] == 4924 and
            summary['original_batch_count'] == plan['original_batch_count'] == 197, 'Composite size differs')
    for key, binding in [('input_sha256', ctx['material']['llm_inputs']),
                         ('output_sha256', entry['output']), ('lineage_sha256', entry['composite_lineage']),
                         ('plan_sha256', entry['composite_plan']), ('manual_sha256', ctx['material']['manual'])]:
        require(summary[key] == binding['sha256'], 'Composite binding differs: ' + key)
    require(summary['input_sha256'] == entry['input_sha256'] and summary['selected_tool_event_count'] == 0 and
            summary['metric_or_reference_label_based_selection'] is False and
            plan['metric_or_reference_label_based_selection'] is False, 'Composite execution/selection differs')
    require(plan['material_input'] == ctx['material']['llm_inputs'] and
            plan['manual'] == ctx['material']['manual'], 'Composite current material/manual differs')
    prompt_path = bound_path(plan['prompt'])
    require(summary['prompt_sha256'] == plan['prompt']['sha256'], 'Composite prompt differs')
    manual_text = bound_path(ctx['material']['manual']).read_text().strip()
    require(manual_text and manual_text in prompt_path.read_text(), 'Actual prompt omits fixed manual text')
    components = {r['component_id']: r for r in plan['components']}
    require(len(components) == len(plan['components']) and
            set(components) == {'base', 'source03', 'network', 'technical155', 'source04'}, 'Composite components differ')
    cache = {}
    def get(binding):
        key = (binding['path'], binding['sha256'])
        if key not in cache:
            cache[key] = bound_json(binding)
        return cache[key]
    component_plans = {}
    for name, component in components.items():
        cp = get(component['run_plan']); cs = get(component['summary'])
        component_plans[name] = cp
        require(cp['prompt_sha256'] == summary['prompt_sha256'], 'Component prompt differs: ' + name)
        run_dir = bound_path(component['run_plan']).parent
        actual_prompt = run_dir / 'frozen_prompt.txt'
        if not actual_prompt.is_file():
            actual_prompt = Path(cp['source_prompt_path'])
        require(actual_prompt.is_absolute() and sha(actual_prompt) == cp['prompt_sha256'], 'Actual component prompt differs')
        require(manual_text in actual_prompt.read_text(), 'Component prompt omits fixed manual')
        # The base/technical155 summary may remain partial. It is not rewritten into a complete single run.
        for key in ('input_sha256', 'prompt_sha256'):
            require(cs[key] == cp[key], 'Actual component summary/plan differs: ' + key)
        require(cs['plan_sha256'] == component['run_plan']['sha256'], 'Component plan SHA differs')
        bound_path({'path': str((run_dir / cp['frozen_input_relative_path']).resolve()),
                    'sha256': cp['input_sha256']})
    base = component_plans['base']
    require(base['n'] == 4924 and base['batch_count'] == 197 and base['batch_size'] == 25, 'Original batch plan differs')
    base_plan_path = bound_path(components['base']['run_plan'])
    original_input_path = base_plan_path.parent / base['frozen_input_relative_path']
    original_binding = {'path': str(original_input_path.resolve()), 'sha256': base['input_sha256']}
    original = (list(bound_jsonl(original_binding)) if base['input_format'] == 'jsonl'
                else [r['id'] for r in bound_json(original_binding)['rows']])
    require(len(original) == 4924 and set(original) == set(ctx['llm_inputs']), 'Original/current ID frame differs')
    original_batches = {i // 25 + 1: original[i:i + 25] for i in range(0, len(original), 25)}
    batch_plan = {r['original_batch']: r for r in plan['batches']}
    require(len(batch_plan) == len(plan['batches']) == 197 and set(batch_plan) == set(range(1, 198)),
            'Original 197 batch coverage differs')
    for number, batch in batch_plan.items():
        require(batch['ids'] == original_batches[number], 'Original batch ID order differs')
    counts = Counter(r['component_id'] for r in plan['batches'])
    require(dict(counts) == summary['component_batch_counts'], 'Composite component batch counts differ')
    require(counts == Counter({'base': 171, 'source03': 3, 'network': 21, 'technical155': 1, 'source04': 1}),
            'Expected retained/replaced component coverage differs')
    require(batch_plan[155]['component_id'] == 'technical155' and batch_plan[156]['component_id'] == 'source04',
            '155 recovery or full 156 replacement absent')
    require({n for n, b in batch_plan.items() if b['component_id'] == 'source03'} == {38, 79, 92} and
            {n for n, b in batch_plan.items() if b['component_id'] == 'network'} == set(range(174, 195)),
            'Actual source/network replacement batches differ')
    lineage = bound_jsonl(entry['composite_lineage'])
    require(set(lineage) == set(ctx['llm_inputs']) and len(lineage) == 4924, 'Composite lineage IDs differ')
    # Only after complete provenance metadata is bound is the raw derived output opened.
    output = bound_jsonl(entry['output'])
    require(set(output) == set(lineage), 'Composite output/lineage IDs differ')
    per_batch = {}
    for rid, line in lineage.items():
        number = line['original_batch']; batch = batch_plan[number]; component = components[line['component_id']]
        require(line['component_id'] == batch['component_id'] and line['selection_record'] == batch['selection_record'],
                'Row component/selection differs: ' + rid)
        require(line['prompt_sha256'] == summary['prompt_sha256'] and
                line['manual_sha256'] == summary['manual_sha256'], 'Row prompt/manual differs')
        require(type(line['technical_recovery']) is bool and line['technical_recovery'] == (number == 155),
                'Technical recovery flag differs')
        packet = get(line['input_packet']); raw = get(line['raw_output']); selection = get(line['selection_record'])
        ii, oi = line['input_row_index0'], line['output_row_index0']
        require(type(ii) is int and type(oi) is int and 0 <= ii < len(packet['rows']) and 0 <= oi < len(raw['rows']),
                'Row source index invalid')
        inp, pred = packet['rows'][ii], raw['rows'][oi]
        require(inp['id'] == pred['id'] == rid and inp == ctx['llm_inputs'][rid] and pred == output[rid],
                'Current source04 or original raw prediction differs: ' + rid)
        require(canonical_sha(inp) == line['source_input_row_sha256'] and
                canonical_sha(pred) == line['prediction_row_sha256'], 'Canonical row SHA differs')
        signature = tuple((line[k]['path'], line[k]['sha256']) for k in ('input_packet', 'raw_output', 'selection_record'))
        if number not in per_batch:
            require([r['id'] for r in packet['rows']] == batch['ids'] == [r['id'] for r in raw['rows']],
                    'Full original batch input/output order differs')
            if line['technical_recovery']:
                require(number == 155 and selection['status'] == 'corrected_technical_event_binding' and
                        selection['all_fields_unchanged'] is True and selection['old_failed_status_preserved'] is True and
                        selection['original_raw_output_sha256'] == selection['recovered_raw_output_sha256'] == line['raw_output']['sha256'],
                        '155 original raw recovery differs')
                event = get(line['technical_event_record'])
                require(event['status'] == 'corrected_technical_event_binding' and event['actual_tool_event_n'] == 0 and
                        event['unknown_event_n'] == 0 and event['unique_different_completed_output_n'] == 1 and
                        event['turn_completed_n'] == 1 and event['output_full_object_canonical_sha256'] == canonical_sha(raw),
                        '155 corrected event binding differs')
                require(event['message_bindings'] and all(m['raw_bytes_equal'] is True and
                        m['text_sha256'] == line['raw_output']['sha256'] for m in event['message_bindings']),
                        '155 actual completed output bytes differ')
                metadata_binding = {'path': str(Path(line['raw_output']['path']).parent / 'original_run_metadata.json'),
                                    'sha256': selection['files']['original_run_metadata.json']}
            else:
                require(selection['status'] == 'accepted_first_valid_actual_attempt' and
                        selection['selection_uses_metric_or_label_values'] is False and
                        selection['selected_output_sha256'] == line['raw_output']['sha256'], 'Actual selected attempt differs')
                selected_dir = bound_path(component['run_plan']).parent / selection['selected_relative_path']
                require(selected_dir.resolve() == Path(line['raw_output']['path']).parent.resolve(), 'Selected raw path differs')
                selected_attempt = next(r for r in selection['attempts']
                                        if r['relative_path'] == selection['selected_relative_path'])
                metadata_binding = {'path': str(selected_dir / 'run_metadata.json'),
                                    'sha256': selected_attempt['metadata_sha256']}
            metadata = get(metadata_binding)
            require(metadata['exit_code'] == 0 and metadata['input_sha256'] == line['input_packet']['sha256'] and
                    metadata['raw_output_sha256'] == line['raw_output']['sha256'] and
                    metadata['prompt_sha256'] == line['prompt_sha256'], 'Actual attempt metadata differs')
            if not line['technical_recovery']:
                require(metadata['status'] == 'accepted_structural_literal_zero_tools' and metadata['tool_event_count'] == 0,
                        'Selected actual attempt did not pass technical gate')
            per_batch[number] = {'signature': signature, 'input_indices': set(), 'output_indices': set(),
                                 'technical_recovery': line['technical_recovery']}
        seen = per_batch[number]
        require(seen['signature'] == signature and seen['technical_recovery'] == line['technical_recovery'],
                'Cannot replace isolated rows inside an original batch')
        seen['input_indices'].add(ii); seen['output_indices'].add(oi)
    require(set(per_batch) == set(range(1, 198)), 'Lineage omits original batch')
    for number, seen in per_batch.items():
        require(seen['input_indices'] == seen['output_indices'] == set(range(len(batch_plan[number]['ids']))),
                'Original batch row coverage incomplete')
    ctx['composite_execution_evidence'] = {'summary': entry['execution_summary'], 'plan': entry['composite_plan'],
                                          'lineage': entry['composite_lineage'], 'component_batch_counts': dict(counts)}
    return output


def load_methods(manifest, ctx, c):
    methods = {}
    for name in ('rules', 'LLM'):
        entry = manifest['methods'][name]
        require(entry['manual_sha256'] == ctx['material']['manual']['sha256'], 'Method manual not current')
        input_key = 'llm_inputs' if name == 'LLM' else 'rule_inputs'
        require(entry['input_sha256'] == ctx['material'][input_key]['sha256'],
                'Method input not the actual bound input')
        qa = bound_json(entry['execution_qa'])
        require(qa.get('all_checks_pass') is True, name + ' execution QA gate not passed')
        require(qa['output_sha256'] == entry['output']['sha256'] and qa['input_sha256'] == entry['input_sha256'],
                name + ' execution QA must explicitly bind actual input/output SHA')
        if name == 'LLM':
            # Require terminal execution metadata before opening any labels.
            summary = bound_json(entry['execution_summary'])
            if summary['status'] == 'complete_actual_composite_lineage':
                rows = load_composite(entry, ctx)
            else:
                rows = load_single_llm(entry, summary)
        else:
            rows = None
        if rows is None:
            rows = bound_jsonl(entry['output'])
        require(set(rows) == set(ctx['inputs']), name + ' IDs differ from current corpus')
        for rid, row in rows.items():
            labels = row.get('prediction', row)['labels']
            require(set(labels) == set(DIMS), 'Missing/extra dimensions: ' + rid)
            require(all(c.binary(v) or v is None for v in labels.values()), 'Invalid label type: ' + rid)
        methods[name] = rows
    return methods


def load_single_llm(entry, summary):
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
    return bound_jsonl(entry['output'])


def analysis_methods(manifest, ctx, raw_methods):
    """Apply source uncertainty only to a deep copy; retain every raw prediction."""
    binding = manifest['analysis_source_missing_policy']
    policy = bound_json(binding)
    require(len(policy['rows']) == 1, 'Only the explicitly recorded source gap may be masked')
    record = policy['rows'][0]
    require(record['id'] == 'RECODE25-00064' and set(record['dimensions']) == set(DIMS) and
            len(record['dimensions']) == 5 and record['no_implicit_zero'] is True and record['reason'],
            '00064 source-gap record differs')
    require(record['id'] in ctx['inputs'], 'Source-gap ID absent')
    derived = copy.deepcopy(raw_methods)
    ledger = {'scope': 'analysis derivative only; raw predictions retained', 'policy_binding': binding,
              'policy_record': record, 'raw_predictions_modified': False, 'methods': {}}
    for name, rows in derived.items():
        rid = record['id']; before = canonical_sha(raw_methods[name][rid])
        for dim in record['dimensions']:
            rows[rid].get('prediction', rows[rid])['labels'][dim] = None
        require(canonical_sha(raw_methods[name][rid]) == before, 'Raw prediction was modified')
        ledger['methods'][name] = {'raw_output_binding': manifest['methods'][name]['output'],
                                  'raw_row_sha256': before, 'analysis_row_sha256': canonical_sha(rows[rid]),
                                  'masked_dimensions': list(record['dimensions'])}
    return derived, ledger


def missing_bounds(rows, ids, c):
    """Sharp multilabel bounds over independent unresolved binary cells."""
    positive = {d: sum(c.label(rows[r], d) == 1 for r in ids if c.binary(c.label(rows[r], d))) for d in DIMS}
    missing = {d: sum(not c.binary(c.label(rows[r], d)) for r in ids) for d in DIMS}
    total = sum(positive.values()); unresolved = sum(missing.values()); n = len(ids)
    attention, coverage = {}, {}
    for d in DIMS:
        t, m, other = positive[d], missing[d], unresolved - missing[d]
        ld, ud = total + other, total + m
        lower = t / ld if ld else None
        upper = (t + m) / ud if ud else None
        # When total known positives are zero, the all-zero completion has undefined q.
        # Report exact bounds conditional on q being defined as well as literal formula NA.
        conditional_lower, conditional_upper = lower, upper
        if total == 0:
            if m and other:
                conditional_lower, conditional_upper = 0.0, 1.0
            elif m:
                conditional_lower = conditional_upper = 1.0
            elif other:
                conditional_lower = conditional_upper = 0.0
            else:
                conditional_lower = conditional_upper = None
        attention[d] = {'lower': lower, 'upper': upper, 'lower_denominator': ld, 'upper_denominator': ud,
                        'NA_reason': 'zero denominator' if not ld or not ud else None,
                        'defined_completion_lower': conditional_lower,
                        'defined_completion_upper': conditional_upper,
                        'undefined_completion_possible': total == 0,
                        'any_defined_completion': total + unresolved > 0}
        coverage[d] = {'lower': t / n if n else None, 'upper': (t + m) / n if n else None,
                       'denominator': n, 'NA_reason': 'empty unit scope' if not n else None}
    return {'known_positive_T': positive, 'unresolved_m': missing, 'sum_T': total, 'sum_m': unresolved,
            'attention_share': attention, 'coverage': coverage,
            'attention_formula': 'lower=T_d/(sum T+sum_other m); upper=(T_d+m_d)/(sum T+m_d)',
            'scope': 'all units and known dimension cells; missing is never imputed as zero'}


def machine_agreement(methods, ids, c):
    records = {}
    names = ('kappa', 'agreement', 'left_positive_rate', 'right_positive_rate')
    for dim in DIMS:
        matrix, valid = c.cells(methods['rules'], methods['LLM'], dim, ids)
        counts = matrix.sum(axis=0); point = c.metrics(counts)[0]
        records[dim] = {'unit_n': len(ids), 'valid_n': int(valid.sum()),
                        'pending_ids': [r for r, ok in zip(ids, valid) if not ok],
                        'cell_order': ['11', '10', '01', '00'], 'cells': counts.tolist(),
                        'metrics': {name: c.safe(point[c.METRIC_NAMES.index(name)]) for name in names}}
    return {'interpretation': 'machine-to-machine agreement only; neither is a validity reference',
            'left': 'rules', 'right': 'LLM', 'records': records, 'confidence_intervals': None}


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


def descriptive(manifest, ctx, methods, c, e, a, raw_methods=None, missing_ledger=None):
    out = {'scope': 'full4481 descriptive comparison of two actual machine outputs',
           'reference': None, 'confidence_intervals': None, 'departments': {},
           'source_context_relationship': ctx['source_context_qa'],
           'analysis_source_missing_policy': missing_ledger,
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
                              'complete_support_profile': conditional,
                              'all_unit_missing_bounds': missing_bounds(rows, ids, c),
                              'all10_pairs': [pair_counts(rows, ids, x, y, c) for x, y in combinations(DIMS, 2)]}
        full = [profiles[n]['profile'] for n in ('rules', 'LLM')]
        qdiff = ({d: full[0]['attention_share'][d] - full[1]['attention_share'][d]
                  if full[0]['attention_share'][d] is not None and full[1]['attention_share'][d] is not None
                  else None for d in DIMS} if all(p is not None for p in full) else None)
        qbounds = {}
        for d in DIMS:
            left = profiles['rules']['all_unit_missing_bounds']['attention_share'][d]
            right = profiles['LLM']['all_unit_missing_bounds']['attention_share'][d]
            sub = lambda x, y: x - y if x is not None and y is not None else None
            qbounds[d] = {'lower': sub(left['lower'], right['upper']),
                          'upper': sub(left['upper'], right['lower']),
                          'defined_completion_lower': sub(left['defined_completion_lower'], right['defined_completion_upper']),
                          'defined_completion_upper': sub(left['defined_completion_upper'], right['defined_completion_lower']),
                          'NA_policy': 'undefined endpoint remains null; defined-completion bounds are explicitly conditional'}
        out['departments'][group] = {'methods': profiles, 'rules_minus_LLM_attention_share': qdiff,
                                    'rules_minus_LLM_attention_share_missing_bounds': qbounds,
                                    'machine_agreement': machine_agreement(methods, ids, c)}
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
                         'source': ctx['sources'][rid],
                         'rules_analysis_row': left, 'LLM_analysis_row': right,
                         'rules_actual_row': (raw_methods or methods)['rules'][rid],
                         'LLM_actual_row': (raw_methods or methods)['LLM'][rid]})
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
    raw_methods = load_methods(manifest, ctx, c)
    methods, missing_ledger = analysis_methods(manifest, ctx, raw_methods)
    args.out.mkdir(parents=True, exist_ok=False)
    write_json(args.out / 'execution_binding.json', {'bindings': str(args.bindings.resolve()),
               'bindings_sha256': args.bindings_sha256, 'mode': args.mode,
               'code_and_design_freeze': manifest['code_and_design_freeze'],
               'human_reference_manifest': manifest.get('human_reference_manifest') if args.mode == 'human' else None,
               'analysis_source_missing_policy': manifest['analysis_source_missing_policy'],
               'composite_execution_evidence': ctx.get('composite_execution_evidence'),
               'adoption_status': manifest['adoption_status'], 'no_model_or_coder_calls': True})
    if args.mode == 'descriptive':
        result, differences = descriptive(manifest, ctx, methods, c, e, a, raw_methods, missing_ledger)
        write_json(args.out / 'full4481_descriptive.json', result)
        write_jsonl(args.out / 'full4481_unit_differences.jsonl', differences)
    else:
        write_json(args.out / 'human_reference_statistics.json', human_statistics(ref, refs, ctx, methods, c, inference))
    write_json(args.out / 'analysis_source_missing_policy_applied.json', missing_ledger)
    files = {p.name: sha(p) for p in args.out.iterdir() if p.is_file()}
    write_json(args.out / 'completion.json', {'status': 'complete_bound_statistics', 'mode': args.mode,
               'files_sha256': files, 'source_inputs_and_labels_modified': False})
    print(json.dumps({'status': 'complete_bound_statistics', 'mode': args.mode, 'out': str(args.out.resolve())}, ensure_ascii=False))


if __name__ == '__main__':
    main()
