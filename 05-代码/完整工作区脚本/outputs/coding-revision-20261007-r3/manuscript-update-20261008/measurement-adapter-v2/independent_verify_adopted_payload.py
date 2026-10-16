"""Independently check a real adopted manuscript payload; never author DOCX.

V2 explicitly supports candidate03 196+25 reconciliation.
Only Python standard-library code is used. No adapter or statistics calculation
function is imported or executed. PENDING adoption stops before payload,
prediction, reference, metadata or statistics files are opened.
"""
from pathlib import Path
from fractions import Fraction
from collections import Counter
import argparse
import hashlib
import json
import math
import re
import sys

DIMS = ('S', 'E', 'Ec', 'I', 'F')
GROUPS = ('NMPA', 'NHSA', 'NHC')
CN_DIMS = dict(zip(DIMS, ('安全性', '有效性', '经济性', '创新性', '公平性')))
CN_GROUPS = dict(zip(GROUPS, ('药监', '医保', '卫健')))
METRICS = ('kappa', 'precision', 'recall', 'f1')
GROUP_N = {'NMPA':1848, 'NHSA':2100, 'NHC':533, 'GOV':443}
FRAME_N = {'NMPA':947, 'NHSA':760, 'NHC':60}
MANUAL = {
    'FINAL_CONCLUSION_ATTENTION_SUMMARY', 'FINAL_CORE_SENSITIVITY_SUMMARY',
    'FINAL_DEPARTMENT_COMPARISON_SUMMARY', 'FINAL_ERROR_PATTERN_SUMMARY',
    'FINAL_FULL_CORPUS_COMPOSITION_SUMMARY', 'FINAL_LLM_EXECUTION_SUMMARY',
    'FINAL_LLM_STABILITY_SUMMARY', 'PROBABILITY180_ATTENTION_SUMMARY',
}
PLACEHOLDER = re.compile(r'\{\{([A-Za-z][A-Za-z0-9_]*)\}\}')
EXPECTED_COUNTS = {'fields':39, 'replacements':52, 'table2_points':80,
                   'table2_primary_CIs':80, 'table3_q':30,
                   'department_directions':15}


class VerificationError(ValueError):
    pass


def demand(condition, explanation):
    if not condition:
        raise VerificationError(explanation)


def file_hash(path):
    hasher = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024 * 1024), b''):
            hasher.update(chunk)
    return hasher.hexdigest()


def text_hash(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def same_file_binding(left, right):
    return (isinstance(left, dict) and isinstance(right, dict)
            and left.get('path') == right.get('path')
            and left.get('sha256') == right.get('sha256'))


def number_matches(actual, exact):
    if exact is None:
        return actual is None
    return (type(actual) in (int, float) and math.isfinite(actual)
            and math.isclose(actual, float(exact), abs_tol=1e-10, rel_tol=1e-10))


def display_number(exact, places=3):
    return 'NA' if exact is None else format(float(exact), '.' + str(places) + 'f')


def ratio(numerator, denominator):
    return None if denominator == 0 else numerator / denominator


def exact_statistics(cells):
    """Compute kappa using the 2x2 determinant form, not adapter's po/pe code."""
    tp, fp, fn, tn = cells
    cross_margin = (tp + fp) * (fp + tn) + (tp + fn) * (fn + tn)
    return {
        'kappa':ratio(2 * (tp * tn - fp * fn), cross_margin),
        'precision':ratio(tp, tp + fp),
        'recall':ratio(tp, tp + fn),
        'f1':ratio(2 * tp, 2 * tp + fp + fn),
    }


class Inputs:
    """Verify file evidence independently, including nested historical bindings."""
    def __init__(self):
        self.bindings = {}
        self.cache = {}
        self.expanded = set()
        self.label_files_opened = []

    def bind(self, binding):
        demand(isinstance(binding, dict), 'Input binding must be an object')
        path, expected = binding.get('path'), binding.get('sha256')
        demand(isinstance(path, str) and Path(path).is_absolute(), 'Absolute input path required')
        demand(isinstance(expected, str) and re.fullmatch('[0-9a-f]{64}', expected), 'Valid input SHA required: ' + path)
        p = Path(path)
        demand(p.is_file(), 'Bound file missing: ' + path)
        key = str(p.resolve())
        demand(key not in self.bindings or self.bindings[key]['sha256'] == expected, 'Conflicting bound SHA: ' + path)
        demand(file_hash(p) == expected, 'Bound file changed: ' + path)
        self.bindings[key] = {'path':path, 'sha256':expected}
        return p

    def object(self, binding):
        p = self.bind(binding)
        key = str(p.resolve())
        if key not in self.cache:
            self.cache[key] = read_json(p)
        return self.cache[key]

    def closure(self, item):
        if isinstance(item, list):
            for child in item:
                self.closure(child)
        elif isinstance(item, dict):
            if 'path' in item and 'sha256' in item:
                p = self.bind(item)
                key = str(p.resolve())
                if p.suffix.lower() == '.json' and key not in self.expanded:
                    self.expanded.add(key)
                    self.closure(self.object(item))
            for key, value in item.items():
                if key.endswith('_path') and key[:-5] + '_sha256' in item and isinstance(value, str):
                    self.bind({'path':value, 'sha256':item[key[:-5] + '_sha256']})
                if isinstance(value, (dict, list)):
                    self.closure(value)

    def records(self, binding, labels=False):
        p = self.bind(binding)
        if labels:
            self.label_files_opened.append(str(p))
        result = {}
        for line in p.read_text(encoding='utf-8').splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            identity = record.get('original_id', record.get('id'))
            demand(isinstance(identity, str) and identity not in result, 'Duplicate or missing record ID')
            demand(record.get('id') == identity, 'Record ID alias differs: ' + identity)
            result[identity] = record
        return result

    def unchanged(self):
        for binding in self.bindings.values():
            demand(file_hash(binding['path']) == binding['sha256'], 'Evidence changed while checking: ' + binding['path'])


def adopted_configuration(config):
    missing = []
    if config.get('status') != 'root_confirmed_complete_method_adoption':
        missing.append('status=root_confirmed_complete_method_adoption')
    for name in ('root_adopted_methods_confirmed', 'root_semantic_adoption_confirmed'):
        if config.get(name) is not True:
            missing.append(name)
    for name in ('root_approved_at', 'root_adoption_note'):
        if not config.get(name):
            missing.append(name)
    for role in ('rules', 'LLM'):
        method = config.get('methods', {}).get(role, {})
        for name in ('method_id', 'statistics_method_key', 'statistics_frozen_method_id', 'execution_profile'):
            if not method.get(name):
                missing.append('methods.' + role + '.' + name)
        for name in ('output', 'execution_binding', 'classification', 'statistics_manifest', 'statistics_QA', 'statistics_freeze'):
            binding = method.get(name)
            if not isinstance(binding, dict) or not binding.get('path') or not binding.get('sha256'):
                missing.append('methods.' + role + '.' + name)
    for name in ('reference_manifest', 'candidate_reference', 'staged_replacements', 'preflight_report', 'preflight_freeze',
                 'bibliography', 'AC_statistics', 'AC_statistics_manifest', 'AC_statistics_freeze', 'mathematical_QA', 'manual_narratives'):
        binding = config.get(name)
        if not isinstance(binding, dict) or not binding.get('path') or not binding.get('sha256'):
            missing.append(name)
    return missing


def reconciled_execution_header(method, evidence):
    """Independently read complete execution metadata before any payload/labels."""
    demand(sys.flags.optimize == 0, 'Python optimization must be disabled')
    profile = 'LLM03_single_unit_reconciled_execution_v2'
    identity = 'LLM-v32-candidate03-single-unit-reconciled-development'
    demand(method['execution_profile'] == profile and method['method_id'] == identity, 'Reconciled profile/ID differs')
    full = evidence.object(method['execution_binding'])
    demand(full.get('status') == 'complete_actual_full_corpus_development_reconciled_QA_PASS', 'Reconciled run incomplete; labels remain unread')
    demand(full['method_id'] == identity and full['n'] == 4924 and full['batches'] == 221, 'Reconciled scope is not4924/221')
    demand(full['source_production_batches'] == 197 and full['original_terminal_failed_batches'] == [115]
           and full['original_execution_status'] == 'partial_or_failed_preserved', 'Original failed115 must remain explicit')
    demand(full['formal_adoption'] is False and full['independent_validation'] is False and full['all_240_exposed_development'] is True, 'Development exposure concealed')
    demand(same_file_binding(full['output'], method['output']), 'Adopted output differs from actual complete reconciliation')
    qa = evidence.object(full['technical_QA']); summary = evidence.object(full['execution_summary'])
    original = evidence.object(full['original_run_QA']); recovery = evidence.object(full['recovery_QA'])
    demand(qa['status'] == 'PASS' and summary['status'] == 'complete_reconciled_actual_development_with_disclosed_protocol_supplement', 'Reconciled QA/summary incomplete')
    expected = {'method_id':identity, 'n':4924, 'source_production_batches':197, 'original_accepted_batches':196,
                'original_terminal_failed_batches':[115], 'original_execution_status':'partial_or_failed_preserved',
                'recovery_logical_single_unit_calls':25, 'accepted_model_request_batches':221,
                'batch_partition_changed_only_for_original_batch115':True, 'original_max3_protocol_not_claimed_successful':True,
                'new_requests_semantically_five_dimensional':True, 'references_or_metrics_used_to_select':False,
                'rows_or_quotes_manually_changed':False, 'dimension_splicing':False,
                'formal_adoption':False, 'independent_validation':False, 'all_240_exposed_development':True}
    for key, value in expected.items():
        demand(qa.get(key) == value and summary.get(key) == value, 'Reconciled header differs: ' + key)
    for left, right in [('output','output'), ('row_provenance','row_provenance'), ('original_incomplete_run_QA','original_run_QA'),
                        ('recovery_QA','recovery_QA'), ('protocol_supplement','protocol_supplement'), ('authorization','root_authorization')]:
        demand(same_file_binding(qa[left], full[right]), 'QA binds different reconciliation evidence')
    for key in ('original_run_unchanged','formal_candidate02_unchanged','candidate03_previous_artifacts_unchanged'):
        demand(qa.get(key) is True, 'Preservation QA missing')
    demand(original['status'] == 'PASS_AUDIT_OF_TECHNICALLY_INCOMPLETE_RUN'
           and (original['n_input_rows'],original['logical_batches'],original['accepted_batches'],original['accepted_rows'],original['terminal_failed_batches']) == (4924,197,196,4899,[115]), 'Original incomplete audit scope differs')
    demand(recovery['status'] == 'PASS'
           and (recovery['n_input_rows'],recovery['logical_batches'],recovery['accepted_batches'],recovery['accepted_rows'],recovery['terminal_failed_batches']) == (25,25,25,25,[]), 'Recovery audit scope differs')
    demand(full['protocol_supplement']['sha256'] == 'd0cf693884e16e86c317c523e20a63263407d8758e32f069a23d9ca6ee7d4188'
           and same_file_binding(full['protocol_supplement'],full['run_plan']), 'Wrong authorized v2 supplement')
    authorization = evidence.object(full['root_authorization'])
    demand(authorization['status'] == 'passed_root_independent_recovery_review'
           and authorization['plan_sha256'] == full['protocol_supplement']['sha256']
           and authorization['new_calls_authorized'] == 25 and authorization['technical_max_attempts'] == 75, 'Recovery authorization differs')
    demand(full['source_input']['sha256'] == qa['same_v14_input_sha256'] == summary['same_v14_input_sha256']
           == '6829d554cf5514e49565c7c58c4ffdb6f7768f9999b0eea49f114db023c03763', 'Reconciled source differs')
    demand(full['prompt']['sha256'] == qa['same_frozen_prompt_sha256'] == summary['same_frozen_prompt_sha256']
           == '8576d9a1be10b0dd7b69b4c12367f4c357f55abf4ca30d979d5b333493089ba4', 'Semantic prompt differs')
    for name, q in [('original',original),('recovery',recovery)]:
        demand(q['first_valid_selected_without_post_valid_calls'] is True and q['all_selected_raw_objects_equal_actual_final_event_JSON'] is True, 'First-valid/event-object evidence missing')
        demand(len(q['batch_audits']) == q['logical_batches'] and len(q['attempt_audits']) == q['actual_attempts'], 'Actual attempt coverage differs')
        demand(summary[name+'_actual_attempts'] == q['actual_attempts'] and summary[name+'_failed_attempts_preserved'] == q['failed_attempts_preserved'], 'Attempt count differs')
        demand(all(not item['event_check']['violations'] for item in q['attempt_audits']), 'Tool events in actual execution')
    return full


def full_execution_gate(method, role, manifest, evidence):
    """Require complete bound execution evidence before opening method labels."""
    execution = evidence.object(method['execution_binding'])
    profile = method['execution_profile']
    source = manifest['material']['rule_inputs' if role == 'rules' else 'llm_inputs']
    if profile == 'LLM03_single_unit_reconciled_execution_v2':
        demand(role == 'LLM', 'Reconciled LLM profile on non-LLM role')
        actual = reconciled_execution_header(method, evidence)
        demand(same_file_binding(actual['source_input'], source), 'Reconciled source differs from current v14 manifest')
    elif profile == 'LLM03_full_execution':
        demand(role == 'LLM', 'LLM03 execution on non-LLM role')
        demand(execution['status'] == 'complete_actual_full_corpus_development_comparison_QA_PASS', 'Partial LLM03 is not readable by this checker')
        demand(execution['n'] == 4924 and execution['batches'] == 197 and execution['method_id'] == method['method_id'], 'LLM03 full scope/identity missing')
        demand(same_file_binding(execution['output'], method['output']) and same_file_binding(execution['source_input'], source), 'LLM03 adopted output/source differ')
        qa = evidence.object(execution['technical_QA'])
        summary = evidence.object(execution['execution_summary'])
        demand(qa['status'] == 'PASS' and qa['n'] == 4924 and qa['batches'] == 197, 'LLM03 execution QA is incomplete')
        demand(qa['output_sha256'] == method['output']['sha256'] and qa['full_v14_source_sha256'] == source['sha256'], 'LLM03 QA binds other output/source')
        demand(summary['status'] == 'complete_actual_calls_structurally_valid' and summary['accepted_batch_count'] == 197, 'LLM03 summary is incomplete')
        demand(summary['output_sha256'] == method['output']['sha256'] and summary['source_unchanged_during_run'] is True, 'LLM03 summary output/source changed')
        demand(qa['labels_spliced_or_quotes_repaired'] is False and qa['reference_or_metric_based_selection'] is False, 'LLM03 selected/spliced after measurement')
    elif profile == 'LLM02_reconciled_execution':
        demand(role == 'LLM' and method['method_id'] == 'LLM-v32-candidate02', 'Wrong LLM02 execution identity')
        frozen = manifest['methods']['LLM']
        demand(same_file_binding(frozen['output'], method['output']) and same_file_binding(frozen['execution_qa'], method['execution_binding']), 'LLM02 differs from frozen execution')
        demand(execution['all_checks_pass'] is True and execution['n'] == 4924 and execution['batch_count'] == 197, 'LLM02 execution incomplete')
        demand(execution['final_output_sha256'] == method['output']['sha256'] and execution['final_material_version'] == 'v14', 'LLM02 output/material differs')
    elif profile == 'rules_development_candidate':
        demand(role == 'rules' and execution['scope_closed'] is True, 'Rule development execution not closed')
        demand(same_file_binding(execution['prediction'], method['output']) and same_file_binding(execution['input'], source), 'Rule execution binds another output/source')
        demand(execution['reference_labels_edited'] is False and execution['not_independent_validation'] is True and execution['exposed240_used_for_development'] is True, 'Rule development identity differs')
        qa, run = evidence.object(execution['QA']), evidence.object(execution['run'])
        demand(qa['all_checks_pass'] is True and run['n'] == 4924 and run['pending_n'] == 0, 'Rule run incomplete')
        demand(run['prediction_sha256'] == method['output']['sha256'] and run['input_sha256'] == source['sha256'], 'Rule run output/source differ')
    elif profile == 'rules33_confirmed_execution':
        demand(role == 'rules' and method['method_id'] == 'rules-v33', 'Wrong v33 execution identity')
        frozen = manifest['methods']['rules']
        demand(same_file_binding(frozen['output'], method['output']) and same_file_binding(frozen['execution_qa'], method['execution_binding']), 'v33 differs from frozen execution')
        demand(execution.get('all_checks_pass') is True or execution.get('status') in ('pass', 'pass_independent_execution_QA'), 'v33 execution QA failed')
        demand(execution['n'] == 4924 and execution['source_input_sha256'] == source['sha256'], 'v33 full scope/source differs')
    else:
        raise VerificationError('Unknown execution profile; explicit checker review required: ' + str(profile))


def extract_labels(records, wanted_ids):
    demand(set(records) == set(wanted_ids), 'Labels do not cover exactly the required ID scope')
    output = {}
    for identity, record in records.items():
        labels = record.get('prediction', record).get('labels')
        demand(isinstance(labels, dict) and set(labels) == set(DIMS), 'Missing five-dimensional labels: ' + identity)
        demand(all(type(v) is int and v in (0, 1) for v in labels.values()), 'Nonbinary or pending labels: ' + identity)
        output[identity] = labels
    return output


def context_inputs(config, manifest, evidence):
    demand(manifest['root_final_bindings_confirmed'] is True, 'Reference manifest is not confirmed')
    demand(manifest['material']['version'] == config['material_version'] == 'v14', 'Input material must be v14')
    demand(evidence.object(manifest['material']['source_qa'])['all_checks_pass'] is True, 'Source QA missing')
    source = evidence.records(manifest['material']['rule_inputs'])
    llm_source = evidence.records(manifest['material']['llm_inputs'])
    demand(len(source) == len(llm_source) == 4924 and set(source) == set(llm_source), 'Shared inputs are not complete 4924')
    metadata = evidence.object(manifest['metadata'])['rows']
    by_stem = {Path(row['original_file']).stem:row for row in metadata}
    demand(len(by_stem) == len(metadata), 'Ambiguous frozen metadata stems')
    groups = {}
    for identity, record in source.items():
        demand(record['input']['unit_text'] == llm_source[identity]['text'], 'Shared unit text differs')
        demand(record['input']['llm_v29_shared_context'] == llm_source[identity]['contexts'], 'Shared context differs')
        groups[identity] = by_stem[record['input']['original_file_stem']]['analysis_group']
    demand(Counter(groups.values()) == Counter(GROUP_N), 'Metadata groups do not sum to 4481+443')
    design = evidence.object(manifest['sampling_design'])
    sample = {item['original_id']:item for item in design['sample']}
    demand(len(sample) == len(design['sample']) == 240 and design['frame_N_by_group'] == FRAME_N, 'Frozen sampling design differs')
    cells = Counter((item['component'], item['group']) for item in sample.values())
    demand(cells == Counter({('probability_canonical', g):60 for g in GROUPS} | {('enriched_challenge', g):30 for g in ('NMPA', 'NHSA')}), 'Sample component/group scope differs')
    probability = sorted(identity for identity, item in sample.items() if item['component'] == 'probability_canonical')
    n_by_group = Counter(sample[identity]['group'] for identity in probability)
    weights = {}
    for identity, item in sample.items():
        group = groups[identity]
        demand(group == item['group'] and text_hash(llm_source[identity]['text']) == item['unit_text_sha256'], 'Sample group/text changed')
        if identity in probability:
            population, sampled = design['frame_N_by_group'][group], n_by_group[group]
            demand(item['canonical_frame_N'] == population and item['sample_n'] == sampled, 'Sample frame sizes differ')
            weights[identity] = Fraction(population, sampled)
            demand(number_matches(item['analysis_weight'], weights[identity]) and number_matches(item['inclusion_probability'], Fraction(sampled, population)), 'Sample weight or inclusion probability differs')
        else:
            demand(item['analysis_weight'] is None, 'Challenge records cannot carry population weights')
    references = {}
    for coder in ('A', 'C'):
        rows = evidence.records(manifest['references'][coder], labels=True)
        references[coder] = extract_labels(rows, sample)
        for identity, record in rows.items():
            demand(record['effective_material_version'] == 'v14', 'A/C reference uses old material')
            provenance = record['annotation_provenance']['effective']
            packet = evidence.object({'path':provenance['packet_path'], 'sha256':provenance['packet_sha256']})
            matches = [item for item in packet['rows'] if item['id'] == provenance['blind_id']]
            demand(len(matches) == 1, 'A/C reference packet ID is ambiguous')
            demand(all(matches[0][key] == llm_source[identity][key] for key in ('text', 'source_title', 'pages', 'contexts', 'context_usage')), 'A/C source packet is not current v14')
    return source, llm_source, groups, probability, weights, references


def statistics_input(config, binding, manifest_binding, seal_binding, evidence, required_extra=()):
    document = evidence.object(binding)
    statistical_manifest = evidence.object(manifest_binding)
    provenance = document['provenance']
    demand(provenance['material_version'] == 'v14' and provenance['human_validation_completed'] is False, 'Statistical material/identity differs')
    declared = provenance.get('bindings') or {'path':provenance.get('binding_manifest_path'), 'sha256':provenance.get('binding_manifest_sha256')}
    demand(same_file_binding(declared, manifest_binding), 'Statistical provenance binds another manifest')
    if statistical_manifest.get('stage') == 'development_only_all240_exposed':
        demand(statistical_manifest['root_development_bindings_confirmed'] is True, 'Development statistics not confirmed')
        demand(same_file_binding(statistical_manifest['reference_manifest'], config['reference_manifest']), 'Different statistical A/C reference manifest')
        demand(same_file_binding(statistical_manifest['existing_candidate_reference'], config['candidate_reference']), 'Different statistical candidate reference')
        demand(provenance['all240_exposed'] is True and provenance['independent_validation'] is False, 'Development scope misrepresented')
    else:
        demand(statistical_manifest.get('stage') == 'final' and same_file_binding(manifest_binding, config['reference_manifest']), 'Unknown statistics provenance schema')
    demand(provenance['analysis_notes']['replications'] == 5000, 'Statistical replication count is not 5000')
    seal = evidence.object(seal_binding)
    directory = Path(seal_binding['path']).parent
    demand(seal['bindings_sha256'] == manifest_binding['sha256'], 'Statistical seal belongs to another manifest')
    for expected in (binding,) + tuple(required_extra):
        demand(Path(expected['path']).parent == directory and seal['files'][Path(expected['path']).name] == expected['sha256'], 'Statistical output not in same sealed directory')
    for name, digest in seal['files'].items():
        evidence.bind({'path':str(directory / name), 'sha256':digest})
    return document, statistical_manifest


def check_interval(interval, metric):
    defined, undefined = interval['defined_repetitions'], interval['undefined_repetitions']
    demand(type(defined) is int and type(undefined) is int and min(defined, undefined) >= 0 and defined + undefined == 5000, 'Primary CI repetitions incomplete')
    low, high = interval['low'], interval['high']
    if defined == 0:
        demand(low is None and high is None, 'Zero defined replicates must have NA interval')
    else:
        demand(type(low) in (int, float) and type(high) in (int, float) and math.isfinite(low) and math.isfinite(high) and low <= high, 'Primary interval is malformed')
        demand(low >= (-1 if metric == 'kappa' else 0) - 1e-10 and high <= 1 + 1e-10, 'Primary interval outside metric domain')


def compare_stat_record(document, method_key, reference_key, dimension, predicted, reference, probability, weights, ac=False):
    selector = dict(component='probability_canonical', group='ALL', weighting='eligible_design_weighted',
                    method=method_key, reference=reference_key, dimension=dimension)
    matches = [(index, item) for index, item in enumerate(document['comparisons']) if all(item.get(key) == value for key, value in selector.items())]
    demand(len(matches) == 1, 'Statistical selector must identify exactly one record: ' + str(selector))
    index, record = matches[0]
    demand(record['paired_n'] == record['unit_frame_n'] == 180 and record['excluded_pending_n'] == 0, 'Statistics do not describe the complete probability180')
    demand(sorted(record['paired_ids']) == probability and not record['excluded_ids'], 'Statistical paired IDs differ')
    demand(record['primary_bootstrap_mechanism'] == 'department_unit_rescaled_SRSWOR', 'Primary CI mechanism differs')
    # Independent marginal-cell accumulation: TP, FP, FN, TN.
    raw = [0, 0, 0, 0]
    weighted = [Fraction(0) for _ in range(4)]
    for identity in probability:
        positive = predicted[identity][dimension]
        target = reference[identity][dimension]
        location = (0 if target else 1) if positive else (2 if target else 3)
        raw[location] += 1
        weighted[location] += weights[identity]
    names = ('A1_C1', 'A1_C0', 'A0_C1', 'A0_C0') if ac else ('TP', 'FP', 'FN', 'TN')
    raw_key = 'symmetric_raw_cells' if ac else 'raw_confusion'
    weighted_key = 'symmetric_weighted_cells' if ac else 'weighted_confusion'
    demand([record[raw_key][name] for name in names] == raw, 'Source raw cells disagree with adopted labels')
    demand(all(number_matches(record[weighted_key][name], value) for name, value in zip(names, weighted)), 'Source weighted cells disagree with exact design weights')
    recomputed = exact_statistics(weighted)
    audits = {}
    for metric in (('kappa',) if ac else METRICS):
        actual = record['metrics'][metric]
        demand(number_matches(actual['estimate'], recomputed[metric]), 'Statistical point estimate differs from independent arithmetic: ' + metric)
        interval = actual['ci95_primary']
        check_interval(interval, metric)
        reason = record.get('undefined_point_reasons', {}).get(metric)
        if recomputed[metric] is None:
            demand(isinstance(reason, str) and bool(reason.strip()), 'Undefined point estimate lacks a reason')
        audits[metric] = {'estimate':actual['estimate'], 'exact_fraction':None if recomputed[metric] is None else str(recomputed[metric]),
                         'ci95_primary':interval, 'undefined_point_reason':reason,
                         'json_pointer':f'/comparisons/{index}/metrics/{metric}'}
    return {'selector':selector, 'row_json_pointer':f'/comparisons/{index}',
            'raw_cells':dict(zip(names, raw)), 'exact_weighted_cells':dict(zip(names, map(str, weighted))), 'metrics':audits}, recomputed


def verify(config, payload, adoption_binding, evidence, counts):
    demand(payload.get('status') in ('assembled_pending_independent_QA', 'ready_for_authoring'), 'A real assembled payload is required')
    demand(payload.get('adapter_is_not_DOCX_authoring') is True, 'Unexpected payload execution identity')
    demand(payload.get('remaining_fields') == [], 'Payload still has unresolved fields')
    expected_gates = ['independent_payload_QA'] if payload['status'] == 'assembled_pending_independent_QA' else []
    demand(payload.get('remaining_gates') == expected_gates, 'Payload has unrelated remaining gates')
    demand(same_file_binding(payload['root_adoption_binding'], adoption_binding), 'Payload uses another adoption configuration')
    manifest = evidence.object(config['reference_manifest'])
    # Complete-run evidence is checked before the prediction files are parsed.
    for role in ('rules', 'LLM'):
        full_execution_gate(config['methods'][role], role, manifest, evidence)
    evidence.closure(config)
    listed_bindings = {}
    for binding in payload['input_bindings']:
        evidence.bind(binding)
        listed_bindings[str(Path(binding['path']).resolve())] = binding['sha256']
    source, llm_source, groups, probability, weights, refs = context_inputs(config, manifest, evidence)
    staged = evidence.object(config['staged_replacements'])
    preflight = evidence.object(config['preflight_report'])
    freeze = evidence.object(config['preflight_freeze'])
    bibliography = evidence.object(config['bibliography'])
    demand(len(staged['measurement_fields']) == 39 and len(staged['replacements']) == 52, 'Staged field/paragraph contract differs')
    demand(preflight['all_old_text_hash_checks_pass'] is True and preflight['replacements_n'] == 52, 'Preflight paragraph QA missing')
    demand(preflight['inputs'][config['staged_replacements']['path']]['sha256'] == config['staged_replacements']['sha256'], 'Preflight uses another staged draft')
    preflight_dir = Path(config['preflight_freeze']['path']).parent
    demand(preflight_dir == Path(config['preflight_report']['path']).parent == Path(config['bibliography']['path']).parent, 'Mixed preflight snapshots')
    for name, digest in freeze['files'].items():
        evidence.bind({'path':str(preflight_dir / name), 'sha256':digest})
    demand(len(bibliography['used_bibliography']) == 61 and [item['new_number'] for item in bibliography['used_bibliography']] == list(range(1, 62)), 'Final reference set must be exactly the reviewed 61')
    demand(same_file_binding(payload['bibliography_binding'], config['bibliography']), 'Payload bibliography binding differs')
    predictions, statistical_docs = {}, {}
    for role in ('rules', 'LLM'):
        method = config['methods'][role]
        records = evidence.records(method['output'], labels=True)
        demand(len(records) == 4924, 'Adopted method is not a complete 4924 output')
        predictions[role] = extract_labels(records, source)
        if role == 'rules':
            demand(all(record['prediction']['unit_text_sha256'] == text_hash(llm_source[identity]['text']) for identity, record in records.items()), 'Rule output text hashes differ')
        stats, stats_manifest = statistics_input(config, method['classification'], method['statistics_manifest'], method['statistics_freeze'], evidence, (method['statistics_QA'],))
        declared = stats_manifest['methods'][method['statistics_method_key']]
        demand(declared['frozen_method_id'] == method['statistics_frozen_method_id'] and same_file_binding(declared['output'], method['output']), 'Statistics belong to another method output')
        demand(declared['material_version'] == 'v14', 'Statistics use another material version')
        statistics_qa = evidence.object(method['statistics_QA'])
        demand(statistics_qa.get('all_checks_pass') is True or statistics_qa.get('status') in ('PASS', 'pass'), 'Complete-statistics QA missing')
        statistical_docs[role] = stats
        mapping = {'adopted_id':method['method_id'], 'statistics_key':method['statistics_method_key'],
                   'statistics_frozen_id':method['statistics_frozen_method_id'], 'actual_output':method['output']}
        demand(payload['method_id_mapping'][role] == mapping, 'Payload method-ID mapping differs')

    profiles, fractions, auto = [], {}, {'FINAL_RULES_ID':config['methods']['rules']['method_id'], 'FINAL_LLM_ID':config['methods']['LLM']['method_id']}
    for role in ('rules', 'LLM'):
        for group in GROUPS:
            identities = [identity for identity in source if groups[identity] == group]
            positive_n = {dim:sum(predictions[role][identity][dim] for identity in identities) for dim in DIMS}
            denominator = sum(positive_n.values())
            demand(denominator > 0, 'Five-dimensional attention denominator is zero')
            joint = sum(1 for identity in identities if predictions[role][identity]['Ec'] == predictions[role][identity]['F'] == 1)
            ec, fairness = positive_n['Ec'], positive_n['F']
            conditional = None if not ec else Fraction(joint, ec)
            dims = {}
            for dim in DIMS:
                value = Fraction(positive_n[dim], denominator)
                fractions[role, group, dim] = value
                dims[dim] = {'count':positive_n[dim], 'exact_fraction':str(value), 'value':float(value),
                             'percentage':float(100 * value), 'coverage_exact_fraction':str(Fraction(positive_n[dim], len(identities)))}
                if role == 'rules':
                    auto[f'RULE_Q_{group}_{dim}'] = display_number(100 * value, 2)
            demand(sum(fractions[role, group, dim] for dim in DIMS) == 1, 'Exact attention shares do not sum to 1')
            profiles.append({'group':group, 'method_role':role, 'unit_n':len(identities), 'denominator':denominator, 'dimensions':dims,
                             'Ec_F':{'Ec':ec, 'F':fairness, 'joint':joint, 'Ec_only':ec-joint, 'F_only':fairness-joint,
                                     'neither':len(identities)-ec-fairness+joint,
                                     'P_F_given_Ec':{'exact_fraction':None if conditional is None else str(conditional), 'value':None if conditional is None else float(conditional)}}})
            if group in ('NHSA', 'NHC'):
                demand(conditional is not None, 'Cannot fill adopted conditional-proportion prose with zero Ec denominator')
                prefix = 'RULE' if role == 'rules' else 'LLM'
                auto[f'{prefix}_Ec_{group}'] = str(ec)
                auto[f'{prefix}_JOINT_{group}'] = str(joint)
                auto[f'{prefix}_P_F_GIVEN_Ec_{group}'] = display_number(100 * conditional, 2)
    demand(payload['figure2_data'] == profiles and payload['tables']['3']['audit'] == profiles, 'All six five-dimensional figure/table profiles must equal independent recomputation')
    t3 = [['部门', '方法'] + [CN_DIMS[dim] + '（%）' for dim in DIMS]]
    for group in GROUPS:
        for role in ('rules', 'LLM'):
            values = [display_number(100 * fractions[role, group, dim], 2) for dim in DIMS]
            t3.append([CN_GROUPS[group], '规则' if role == 'rules' else 'LLM'] + values)
            counts['table3_q'] += len(values)
    demand(payload['tables']['3']['rows'] == t3, 'Table3 cells differ from independently computed exact q')
    demand(payload['tables']['3']['rows_include_header'] is True and payload['tables']['3']['n_data_rows'] == 6
           and payload['tables']['3']['q_n'] == 30, 'Table3 declared schema differs from six rows / 30 q cells')
    directions = []
    for one, two in (('NMPA', 'NHSA'), ('NMPA', 'NHC'), ('NHSA', 'NHC')):
        for dim in DIMS:
            differences = {role:fractions[role, one, dim] - fractions[role, two, dim] for role in ('rules', 'LLM')}
            signs = {role:0 if value == 0 else 1 if value > 0 else -1 for role, value in differences.items()}
            directions.append({'department_one':one, 'department_two':two, 'dimension':dim, 'difference':'one_minus_two',
                               'exact_q_differences':{role:str(value) for role, value in differences.items()}, 'signs':signs,
                               'same_direction':signs['rules'] == signs['LLM']})
            counts['department_directions'] += 1
    demand(payload['department_pair_directions'] == directions, 'Department direction records differ')
    auto['DEPARTMENT_DIRECTION_MATCH_N'] = str(sum(item['same_direction'] for item in directions))
    ac_doc, _ = statistics_input(config, config['AC_statistics'], config['AC_statistics_manifest'], config['AC_statistics_freeze'], evidence)
    ac_audit, ac_values = {}, []
    for dim in DIMS:
        checked, computed = compare_stat_record(ac_doc, 'A_C', 'symmetric A/C', dim, refs['A'], refs['C'], probability, weights, ac=True)
        ac_audit[dim] = checked
        ac_values.append(display_number(computed['kappa']))
    demand(payload['AC_before_third_audit'] == {'binding':config['AC_statistics'], 'dimensions':ac_audit}, 'A/C pre-third reference audit differs')
    auto['AC_KAPPA_S_E_Ec_I_F'] = '、'.join(ac_values)
    t2 = [['维度', '方法', 'κ（A/C）', 'P（A/C）', 'R（A/C）', 'F1（A/C）']]
    t2_audit = []
    for dim in DIMS:
        for role in ('rules', 'LLM'):
            method = config['methods'][role]
            checked_refs, estimates = {}, {}
            for ref in ('A', 'C'):
                checked, computed = compare_stat_record(statistical_docs[role], method['statistics_method_key'], ref, dim, predictions[role], refs[ref], probability, weights)
                checked_refs[ref], estimates[ref] = checked, computed
                counts['table2_points'] += len(computed)
                counts['table2_primary_CIs'] += len(checked['metrics'])
            t2_audit.append({'dimension':dim, 'method_role':role, 'method_id':method['method_id'], 'classification_binding':method['classification'], 'references':checked_refs})
            t2.append([CN_DIMS[dim], '规则' if role == 'rules' else 'LLM'] + ['/'.join(display_number(estimates[ref][metric]) for ref in ('A', 'C')) for metric in METRICS])
    demand(payload['tables']['2']['rows'] == t2 and payload['tables']['2']['audit'] == t2_audit, 'Table2 display or its 80 same-record primary CIs differ')
    demand(payload['tables']['2']['rows_include_header'] is True and payload['tables']['2']['n_data_rows'] == 10
           and payload['tables']['2']['point_n'] == payload['tables']['2']['same_source_primary_CI_n'] == 80
           and payload['tables']['2']['metric_unit'] == 'original decimal units; no percentage scaling',
           'Table2 declared schema or units differ from ten rows / 80 points and CIs')
    demand(len(auto) == 31 and set(auto) == set(staged['measurement_fields']) - MANUAL, 'Automatic field scope must be exactly 31')
    manual = evidence.object(config['manual_narratives'])
    demand(manual['root_explicitly_supplied'] is True and set(manual['fields']) == MANUAL, 'Exactly eight explicit root narrative fields required')
    output_hashes = {role:config['methods'][role]['output']['sha256'] for role in ('rules', 'LLM')}
    demand(manual['method_output_sha256'] == output_hashes and manual['reference_manifest_sha256'] == config['reference_manifest']['sha256'] and manual['staged_replacements_sha256'] == config['staged_replacements']['sha256'], 'Manual narrative bundle has other output/reference/staged bindings')
    fields = dict(auto)
    for name in sorted(MANUAL):
        entry = manual['fields'][name]
        demand(entry['root_approved'] is True and entry['method_output_sha256'] == output_hashes, 'Root narrative is not approved for adopted outputs')
        demand(isinstance(entry.get('source_bindings'), list) and bool(entry['source_bindings']), 'Narrative source bindings missing')
        for binding in entry['source_bindings']:
            evidence.bind(binding)
        demand(isinstance(entry['text'], str) and bool(entry['text'].strip()) and not PLACEHOLDER.search(entry['text']), 'Empty/unresolved narrative field')
        fields[name] = entry['text']
    demand(payload['manual_narrative_bindings'] == manual, 'Payload narrative provenance differs')
    demand(payload['resolved_fields39'] == fields, 'Resolved 39 fields differ from independent reconstruction')
    counts['fields'] = len(fields)
    resolved = []
    seen_indices = set()
    for original in staged['replacements']:
        index = original['zero_based_body_p_index']
        demand(index not in seen_indices, 'Duplicate staged paragraph index')
        seen_indices.add(index)
        text = PLACEHOLDER.sub(lambda match:fields[match[1]], original['replacement_text'])
        demand('{{' not in text and '}}' not in text, 'Unresolved paragraph marker')
        resolved.append({'zero_based_body_p_index':index, 'old_text_sha256':original['old_text_sha256'], 'replacement_text':text})
    demand(payload['resolved_replacements'] == resolved, '52 paragraphs differ from exact staged field substitution')
    counts['replacements'] = len(resolved)
    expected_scope = {'full_output_n_each':4924, 'three_department_n':4481, 'excluded_GOV_n':443, 'groups':GROUP_N,
                      'same_probability_n':180, 'probability_frames':FRAME_N, 'challenge_n':60, 'AI_references':True,
                      'human_validation_completed':False, 'development_exposure_not_removed_by_adoption':True}
    demand(payload['source_scope'] == expected_scope, 'Payload source or validation identity differs')
    for path, binding in evidence.bindings.items():
        # The checker script/its input payload are added after adapter assembly.
        if path not in (str(Path(__file__).resolve()),):
            demand(listed_bindings.get(path) == binding['sha256'], 'Adopted evidence missing from payload bindings: ' + path)
    demand(counts == EXPECTED_COUNTS, 'Independent arithmetic coverage incomplete')
    return {'automatic_fields_checked':len(auto), 'root_narrative_binding_fields_checked':len(MANUAL),
            'AC_kappa_and_CI_records_checked':len(ac_audit), 'full_method_outputs_checked':2,
            'probability_ids_n':len(probability), 'figure2_groups_checked':len(profiles),
            'Ec_F_four_cell_tables_checked':len(profiles),
            'CI_check_scope':'80 table2 primary CIs matched exactly to their adopted source records, with 5000/NA checks; bootstrap percentiles were not independently rerun',
            'narrative_check_scope':'eight root-approved field/source/output bindings only; semantic assessment belongs to root',
            'method':'fresh binary-cell accumulation with exact design fractions; determinant-form kappa; full-output dimension counts and exact ratios'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--adoption', type=Path, required=True)
    parser.add_argument('--payload', type=Path, required=True)
    parser.add_argument('--adapter', type=Path, required=True,
                        help='Exact adapter script that assembled the adopted payload; hash only, never imported')
    parser.add_argument('--out', type=Path)
    parser.add_argument('--check-only', action='store_true', help='Print result; write no report')
    args = parser.parse_args()
    demand(args.check_only or args.out is not None, '--out is required unless --check-only')
    demand(args.out is None or not args.out.exists(), 'Refuse to overwrite an existing QA report')
    script = {'path':str(Path(__file__).resolve()), 'sha256':file_hash(__file__)}
    report = {'status':'BLOCKED', 'all_checks_pass':False, 'independent_of_adapter_execution':True,
              'adoption_sha256':None, 'adapter_sha256':None, 'payload_content_sha256':None,
              'checked_counts':{key:0 for key in EXPECTED_COUNTS}, 'script':script,
              'DOCX_generated_or_modified':False, 'bootstrap_reexecuted':False,
              'prediction_files_opened':[], 'errors':[]}
    evidence = Inputs()
    try:
        demand(args.adoption.is_file(), 'Actual adoption configuration does not exist')
        adoption_binding = {'path':str(args.adoption.resolve()), 'sha256':file_hash(args.adoption)}
        report['adoption_sha256'] = adoption_binding['sha256']
        config = read_json(args.adoption)
        missing = adopted_configuration(config)
        demand(not missing, 'PENDING adoption; no payload/prediction/statistical files opened: ' + ', '.join(missing))
        if config['methods']['LLM']['execution_profile'] == 'LLM03_single_unit_reconciled_execution_v2':
            reconciled_execution_header(config['methods']['LLM'], evidence)
        demand(args.payload.is_file(), 'Actual assembled payload does not exist')
        payload_binding = {'path':str(args.payload.resolve()), 'sha256':file_hash(args.payload)}
        payload = read_json(args.payload)
        report['payload'] = payload_binding
        demand(args.adapter.is_file(), 'Actual adopted adapter script does not exist')
        adapter_binding = {'path':str(args.adapter.resolve()), 'sha256':file_hash(args.adapter)}
        report['adapter_sha256'] = adapter_binding['sha256']
        excluded = {'status', 'input_bindings', 'limits', 'payload_content_sha256', 'remaining_gates', 'independent_payload_QA_binding'}
        serialized = json.dumps({key:value for key, value in payload.items() if key not in excluded}, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
        content_hash = text_hash(serialized)
        demand(payload.get('payload_content_sha256') == content_hash, 'Payload core SHA is stale')
        report['payload_content_sha256'] = content_hash
        evidence.bind(adoption_binding)
        evidence.bind(adapter_binding)
        details = verify(config, payload, adoption_binding, evidence, report['checked_counts'])
        evidence.unchanged()
        demand(file_hash(args.payload) == payload_binding['sha256'], 'Payload changed during QA')
        demand(file_hash(__file__) == script['sha256'], 'Checker changed during QA')
        report.update(status='PASS', all_checks_pass=True, independent_results=details,
                      verified_input_bindings=sorted(evidence.bindings.values(), key=lambda value:value['path']))
    except (VerificationError, KeyError, IndexError, TypeError, ValueError, OSError) as error:
        report['errors'].append(str(error))
    report['prediction_files_opened'] = evidence.label_files_opened
    report['actual_complete_payload_numerical_QA_performed'] = report['all_checks_pass']
    if not args.check_only:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open('x', encoding='utf-8') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write('\n')
    print(json.dumps(report, ensure_ascii=False, allow_nan=False))
    return 0 if report['all_checks_pass'] else 2


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (VerificationError, OSError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(2)
