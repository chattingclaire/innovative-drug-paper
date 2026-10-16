"""Rebuild binary pairs in the NMPA/NHSA/NHC domain without changing labels.

Main frame: original 1268 first A/C references restricted to three departments
(1057 units). Supplemental frame: H427 restricted to that domain (411 units).
These are exposed development materials, not new independent human validation.

Uses the vectorized confusion-table formulas in the existing extended_metrics.py.
No comparison_masks.json, old LLM predictions or workbook labels are loaded.
"""
from pathlib import Path
from collections import Counter
import argparse
import csv
import hashlib
import importlib.util
import json
import math
import numpy as np
from sklearn.metrics import cohen_kappa_score, accuracy_score, precision_recall_fscore_support

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
RULE_DIR = ROOT / 'outputs/autocode-v28-review-20261004-111306'
INPUT = RULE_DIR / 'rule_inputs_v27.jsonl'
RULE = RULE_DIR / 'all_predictions.jsonl'
REFERENCES = ROOT / 'outputs/autocode-v25-20260927/current_1268_references.jsonl'
H_DIR = ROOT / 'outputs/autocode-v25-20260927/H427'
METADATA = ROOT / 'outputs/validation-expansion-20260926/frozen-inputs/classification--部门归属与年度系列-冻结v1.json'
DEFAULT_LLM = OUT / 'llm-v29/production-25-v29/all_predictions.jsonl'
GROUPS = ('NMPA', 'NHSA', 'NHC')
DIMS = ('S', 'E', 'Ec', 'I', 'F')
B = 5000
BASE_SEED = 20261007

spec = importlib.util.spec_from_file_location('previous_extended_metrics', RULE_DIR / 'extended_metrics.py')
extended = importlib.util.module_from_spec(spec)
spec.loader.exec_module(extended)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_jsonl(path):
    rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    by_id = {r['id']: r for r in rows}
    assert len(by_id) == len(rows), f'Duplicate ID in {path}'
    return by_id


def is_binary(value):
    return type(value) is int and value in (0, 1)


def check_labels(labels, context):
    assert set(labels) == set(DIMS), f'Incomplete dimensions: {context}'
    for dim, value in labels.items():
        assert is_binary(value) or value == '待定', f'Invalid label {context}/{dim}: {value!r}'


def load_frames(inputs):
    refs = read_jsonl(REFERENCES)
    assert len(refs) == 1268
    primary = {}
    for rid, row in refs.items():
        assert rid in inputs and row['original_id'] == inputs[rid]['original_id']
        values = {c: row['original_references'][c]['labels'] for c in ('A', 'C')}
        for coder, labels in values.items():
            check_labels(labels, f'main/{rid}/{coder}')
        primary[rid] = values
    mapping_path = H_DIR / 'admin_mapping.json'
    mapping_rows = json.loads(mapping_path.read_text())
    mapping = {r['id']: r for r in mapping_rows}
    assert len(mapping) == len(mapping_rows) == 427
    sources = [REFERENCES, mapping_path]
    coders = {}
    for coder in ('A', 'C'):
        folder = H_DIR / f'agent-{coder}'
        completion = folder / '完成清单.json'
        assert completion.exists(), f'Incomplete actual H427 coder {coder}'
        sources.append(completion)
        rows = []
        for n in range(1, 44):
            result_path = folder / f'结果-{n:02d}.json'
            packet_path = folder / f'材料-{n:02d}.json'
            result = json.loads(result_path.read_text())
            assert result['coder'] == coder
            assert result['protocol_version'] == 'CAL-5D-20260926-v1.3'
            assert result['protocol_acknowledged'] is True
            assert result['input_packet_sha256'] == sha(packet_path)
            rows.extend(result['rows'])
            sources.extend((result_path, packet_path))
        by_id = {r['id']: r for r in rows}
        assert len(by_id) == len(rows) == 427 and set(by_id) == set(mapping)
        coders[coder] = by_id
    supplement = {}
    for blind_id, meta in mapping.items():
        rid = meta['rerun_id']
        assert meta['original_id'] == inputs[rid]['original_id']
        assert hashlib.sha256(inputs[rid]['input']['unit_text'].encode()).hexdigest() == meta['text_sha256']
        values = {c: coders[c][blind_id]['labels'] for c in ('A', 'C')}
        for coder, labels in values.items():
            check_labels(labels, f'H427/{rid}/{coder}')
        supplement[rid] = values
    assert not set(primary) & set(supplement)
    return {'main1057': primary, 'supplement_H411': supplement}, sources


def load_latest_llm(path, expected_ids):
    """Only an explicitly completed full v29 JSONL may enter this function.

    Accepts the execution agent's bare row contract or a prediction wrapper.
    No fallback to an older model, probe, or partial run is provided.
    """
    rows = read_jsonl(path)
    assert set(rows) == set(expected_ids) and len(rows) == 4924, 'Latest LLM requires exact full ID closure'
    result = {}
    for rid, row in rows.items():
        record = row.get('prediction', row)
        check_labels(record['labels'], f'LLM-v29/{rid}')
        result[rid] = record['labels']
    return result


def safe(value):
    return float(value) if np.isfinite(value) else None


def extended_measures(counts):
    counts = np.asarray(counts, dtype=float)
    original = extended.measures(counts)
    tp, fp, fn, tn = np.moveaxis(counts, -1, 0)
    n = tp + fp + fn + tn
    return np.concatenate((original, extended.ratio(tp + fp, n)[..., None],
                           extended.ratio(tp + fn, n)[..., None]), axis=-1)


METRIC_NAMES = ('kappa', 'agreement', 'precision', 'recall', 'f1', 'left_positive_rate', 'right_positive_rate')


def interval(values):
    finite = values[np.isfinite(values)]
    return {'low': float(np.quantile(finite, .025)) if len(finite) else None,
            'high': float(np.quantile(finite, .975)) if len(finite) else None,
            'defined_repetitions': int(len(finite)), 'undefined_repetitions': int(B-len(finite))}


def evaluate(frame, group, dimension, method, reference, rows):
    chosen = [r for r in rows if group == 'ALL' or r['group'] == group]
    source_names = sorted({r['source_file'] for r in chosen})
    index = {source: n for n, source in enumerate(source_names)}
    counts = np.zeros((len(source_names), 4), dtype=int)
    exclusions = Counter()
    pairs = []
    eligible_ids = []
    excluded_ids = []
    for row in chosen:
        left = row['A' if method == 'A_C' else method][dimension]
        right = row[reference][dimension]
        left_known, right_known = is_binary(left), is_binary(right)
        if left_known and right_known:
            cell = {(1,1):0, (1,0):1, (0,1):2, (0,0):3}[left, right]
            counts[index[row['source_file']], cell] += 1
            pairs.append((left, right))
            eligible_ids.append(row['id'])
        else:
            reason = 'both_pending' if not left_known and not right_known else 'left_pending_only' if not left_known else 'right_pending_only'
            exclusions[reason] += 1
            excluded_ids.append({'id': row['id'], 'reason': reason, 'left': left, 'right': right})
    total = counts.sum(axis=0)
    point = extended_measures(total)
    n = int(total.sum())
    seed = BASE_SEED + int(hashlib.sha256(f'{frame}/{group}'.encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    # Sample all observed files, including files with no common decidable pair.
    # Their zero contribution preserves the actual cluster frame after exclusions.
    weights = rng.multinomial(len(source_names), np.full(len(source_names), 1/len(source_names)), size=B)
    boot = extended_measures(weights @ counts)
    if n:
        left_values, right_values = map(np.array, zip(*pairs))
        sklearn_kappa = cohen_kappa_score(right_values, left_values)
        if np.isfinite(point[0]):
            assert abs(point[0]-sklearn_kappa) < 1e-12
        else:
            assert not np.isfinite(sklearn_kappa)
        assert abs(point[1]-accuracy_score(right_values, left_values)) < 1e-12
        if method != 'A_C':
            prf = precision_recall_fscore_support(right_values, left_values, average='binary', zero_division=0)[:3]
            for actual, expected in zip(point[2:5], prf):
                if np.isfinite(actual):
                    assert abs(actual-expected) < 1e-12
    names = ('kappa', 'agreement', 'left_positive_rate', 'right_positive_rate') if method == 'A_C' else METRIC_NAMES
    metrics = {name: {'estimate': safe(point[j]), 'ci95': interval(boot[:, j])}
               for j, name in enumerate(METRIC_NAMES) if name in names}
    entry = {'frame': frame, 'group': group, 'dimension': dimension, 'method': method, 'reference': reference,
             'role': 'AI A and AI C, symmetric agreement' if method == 'A_C' else 'machine relative to unchanged AI reference',
             'n': n, 'frame_n': len(chosen), 'excluded_n': len(chosen)-n,
             'exclusions': {name: exclusions[name] for name in ('left_pending_only', 'right_pending_only', 'both_pending')},
             'source_clusters': len(source_names), 'paired_source_clusters': int(np.sum(counts.sum(axis=1)>0)),
             'source_entry_clusters': len({r['policy_entry'] for r in chosen}),
             'left_positive_n': int(total[0]+total[1]), 'right_positive_n': int(total[0]+total[2]),
             'left_positive_rate': safe(point[5]), 'right_positive_rate': safe(point[6]),
             'metrics': metrics, 'bootstrap_seed': seed,
             'eligible_ids_sha256': hashlib.sha256('\n'.join(sorted(eligible_ids)).encode()).hexdigest(),
             'excluded_units': excluded_ids}
    if method == 'A_C':
        entry['cross_tab'] = dict(zip(('A1_C1','A1_C0','A0_C1','A0_C0'), map(int,total)))
        entry['confusion'] = None
        entry['accuracy_claim'] = False
    else:
        entry['confusion'] = dict(zip(('TP','FP','FN','TN'), map(int,total)))
        entry['cross_tab'] = None
    return entry


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rules', type=Path, default=RULE, help='Actual full rule prediction JSONL')
    parser.add_argument('--inputs', type=Path, default=INPUT, help='Actual rule input JSONL with identical IDs and unit texts')
    parser.add_argument('--rule-method', help='Output method key; required for a non-default rule file')
    parser.add_argument('--rule-version', help='Exact prediction version; required for a non-default rule file')
    parser.add_argument('--llm', type=Path, help='Completed actual v29 full 4924-row predictions only')
    parser.add_argument('--llm-method', default='llm_gpt56_sol_v29')
    args = parser.parse_args()
    if args.rules.resolve() != RULE.resolve() and (not args.rule_method or not args.rule_version):
        parser.error('Non-default --rules requires explicit --rule-method and --rule-version')
    args.rule_method = args.rule_method or 'rules_v28_2'
    args.rule_version = args.rule_version or 'v28.2-five-dimension-discrepancy-audit-20261004'
    if args.rule_method == 'rules_v28_2' and args.rule_version != 'v28.2-five-dimension-discrepancy-audit-20261004':
        parser.error('A new rule version cannot be labelled rules_v28_2')
    if args.rule_method in ('A_C','A','C') or args.rule_method == args.llm_method:
        parser.error('Method keys must remain distinct from reference keys')
    inputs = read_jsonl(args.inputs)
    raw_predictions = read_jsonl(args.rules)
    assert len(inputs) == 4924 and set(raw_predictions) == set(inputs)
    meta = json.loads(METADATA.read_text())['rows']
    metadata = {Path(r['original_file']).stem: r for r in meta}
    assert len(metadata) == len(meta)
    frames, reference_sources = load_frames(inputs)
    sources = [args.inputs, args.rules, METADATA, RULE_DIR/'extended_metrics.py', Path(__file__), *reference_sources]
    llm = load_latest_llm(args.llm, inputs) if args.llm else None
    if args.llm:
        sources.append(args.llm)
    rows_by_frame = {}
    population_by_group = Counter()
    rule = {}
    for rid, row in inputs.items():
        group = metadata[row['input']['original_file_stem']]['analysis_group']
        if group in GROUPS:
            population_by_group[group] += 1
        record = raw_predictions[rid]['prediction']
        assert record['version'] == args.rule_version, f'Rule version mismatch for {rid}'
        assert record['unit_text_sha256'] == hashlib.sha256(row['input']['unit_text'].encode()).hexdigest()
        check_labels(record['labels'], f'rule/{rid}')
        rule[rid] = record['labels']
    assert sum(population_by_group.values()) == 4481
    for frame, refs in frames.items():
        rows = []
        for rid, labels in refs.items():
            inp = inputs[rid]['input']
            policy_entry = inp['original_file_stem']
            group = metadata[policy_entry]['analysis_group']
            if group not in GROUPS:
                continue
            item = {'id': rid, 'group': group, 'policy_entry': policy_entry,
                    'source_file': inp.get('unit_source') or inp['source'],
                    'A': labels['A'], 'C': labels['C'], args.rule_method: rule[rid]}
            if llm is not None:
                item[args.llm_method] = llm[rid]
            rows.append(item)
        rows_by_frame[frame] = rows
    assert len(rows_by_frame['main1057']) == 1057
    assert len(rows_by_frame['supplement_H411']) == 411
    before = {str(p): sha(p) for p in sources}
    records = []
    methods = [args.rule_method] + ([args.llm_method] if llm is not None else [])
    for frame, rows in rows_by_frame.items():
        for group in ('ALL', *GROUPS):
            for dim in DIMS:
                records.append(evaluate(frame, group, dim, 'A_C', 'C', rows))
                for method in methods:
                    for ref in ('A', 'C'):
                        records.append(evaluate(frame, group, dim, method, ref, rows))
    assert before == {str(p): sha(p) for p in sources}, 'Source changed during read-only computation'
    result = {'created_date':'2026-10-07','reference_identity':'A/C original independent first AI-agent submissions; unchanged; computed under dual-coder reporting standards',
              'validation_status':'Exposed development/reference comparisons; not new independent human validation',
              'scope':GROUPS,'population_n':4481,'population_by_group':dict(population_by_group),
              'frame_n':{f:len(rows) for f,rows in rows_by_frame.items()},
              'frame_by_group':{f:dict(Counter(r['group'] for r in rows)) for f,rows in rows_by_frame.items()},
              'weighting':'Unweighted descriptive classification metrics on each actual binary paired subset; not design-weighted population accuracy. Historical attention-estimation weights are not reused as kappa weights.',
              'pairing':'Per method/reference/dimension actual common binary pairs; no old fixed mask and no filtering by any other method. Explicit pending excluded and counted separately.',
              'method_bindings':{'rule':{'inputs':str(args.inputs.resolve()),'rules':str(args.rules.resolve()),
                                        'method':args.rule_method,'version':args.rule_version},
                                  'references':str(REFERENCES),'metadata':str(METADATA),
                                  'llm':{'path':str(args.llm.resolve()) if args.llm else None,'method':args.llm_method}},
              'bootstrap':{'repetitions':B,'base_seed':BASE_SEED,'confidence_level':.95,
                  'method':'Nonparametric source-file cluster percentile bootstrap. Sample all source files observed in the selected frame/group with replacement; retain all their units, including zero-pair clusters after pending exclusions.',
                  'cluster_field':'rule_input.input.unit_source if present, else rule_input.input.source',
                  'undefined_repetitions':'Omitted separately per metric, counts reported; no undefined metric is replaced by zero.',
                  'small_cluster_note':'Department-specific intervals with few source files are conditional and may be unstable; number of clusters accompanies every result.',
                  'limits':['Conditional on fixed exposed samples, labels and model versions.','Does not account for method selection, shared AI errors, construct validity or inference beyond the corpus.','Source files, rather than broader annual policy series, form clusters.']},
              'latest_llm':{'status':'actual_completed_v29_loaded' if llm else 'not_loaded; awaiting actual v29 full output',
                            'path':str(args.llm) if args.llm else str(DEFAULT_LLM),'expected_total_ids':4924,'old_llm_loaded':False},
              'independent_sklearn_point_checks':True,'source_sha256':before,'records':records}
    json_path = OUT/'三部门编码指标.json'
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    flat=[]
    for r in records:
        base={k:r[k] for k in ('frame','group','dimension','method','reference','role','n','frame_n','excluded_n','source_clusters','paired_source_clusters','source_entry_clusters','left_positive_n','right_positive_n','left_positive_rate','right_positive_rate','bootstrap_seed')}
        base.update(r['exclusions'])
        if r['confusion']:
            base.update(r['confusion'])
        else:
            base.update({x:None for x in ('TP','FP','FN','TN')})
        base.update(r['cross_tab'] or {x:None for x in ('A1_C1','A1_C0','A0_C1','A0_C0')})
        for name, values in r['metrics'].items():
            flat.append({**base,'metric':name,'estimate':values['estimate'],**values['ci95']})
    with (OUT/'三部门编码指标.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(flat[0]));writer.writeheader();writer.writerows(flat)
    brief=[]
    for r in records:
        if r['frame']=='main1057' and r['group']=='ALL':
            brief.append({'dimension':r['dimension'],'method':r['method'],'reference':r['reference'],'n':r['n'],
                          **{m:round(v['estimate'],6) if v['estimate'] is not None else None for m,v in r['metrics'].items()}})
    print(json.dumps({'comparison_records':len(records),'metric_intervals':len(flat),'frames':result['frame_n'],
                      'llm_status':result['latest_llm']['status'],'main_overall':brief},ensure_ascii=False))


if __name__ == '__main__':
    main()
