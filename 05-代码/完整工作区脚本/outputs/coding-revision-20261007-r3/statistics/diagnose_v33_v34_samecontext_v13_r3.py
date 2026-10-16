"""SHA-bound development diagnosis; preserve all frozen methods and references.

This script never supplies its findings to source/rule/LLM implementers and never
promotes post-exposure v34 to independent confirmation or v14 final results.
"""
from pathlib import Path
import datetime
import json
import numpy as np
import statistical_core_r3 as c
import final_binding_io_r3 as io
from run_final_statistics_r3 import point_undefined_reasons

RUN = c.RUN
OUT = RUN / 'statistics/v33-v34-v13-stage-diagnostic'


def bd(path):
    return {'path': str(path), 'sha256': c.sha(path)}


def independent_metrics(cells):
    tp, fp, fn, tn = cells.values()
    n = tp + fp + fn + tn
    po = (tp + tn) / n if n else None
    pe = ((tp + fp) * (tp + fn) + (fn + tn) * (fp + tn)) / n**2 if n else None
    return {'kappa': (po-pe)/(1-pe) if pe is not None and 1-pe > 1e-12 else None,
            'precision': tp/(tp+fp) if tp+fp else None,
            'recall': tp/(tp+fn) if tp+fn else None,
            'f1': 2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None}


def main():
    assert not OUT.exists(), 'Preserve previous diagnostic outputs'
    ctx = c.load_context('v13')
    ctx['material_version'] = 'v13'
    manifest_path = RUN/'rules-v34-audit/architecture/audit_candidate_manifest.json'
    manifest = c.read(manifest_path)
    assert manifest['strict_new_confirmation_claim_allowed'] is False
    assert manifest['status'] == 'sealed_source_blind_minimal_candidate_not_released'
    assert all(c.sha(p) == digest for p, digest in manifest['sealed_snapshot_py_sha256'].items())
    v34_run = io.bound(manifest['sealed_runs']['v13']) if 'path' in manifest['sealed_runs']['v13'] else io.bound({
        'path': manifest['sealed_runs']['v13']['manifest'], 'sha256': manifest['sealed_runs']['v13']['sha256']})
    v33_run_path = RUN/'rules-v33/all_predictions_material_v13.run.json'
    v33_run = c.read(v33_run_path)
    methods = {}
    run_bindings = {}
    for name, run in [('v33', v33_run), ('v34', v34_run)]:
        assert run['input_sha256'] == c.sha(RUN/'rule_inputs_shared_v13.jsonl')
        assert c.sha(run['prediction_path']) == run['prediction_sha256']
        methods[name] = c.jsonl(run['prediction_path'])
        assert set(methods[name]) == set(ctx['inputs']) and len(methods[name]) == 4924
        assert all(c.binary(c.label(row, dim)) for row in methods[name].values() for dim in c.DIMS)
        run_bindings[name] = {'prediction': bd(Path(run['prediction_path'])),
            'run': bd(v33_run_path if name == 'v33' else Path(manifest['sealed_runs']['v13']['manifest']))}
    ref_manifest_path = RUN/'statistics/T参照59-v12阶段绑定.json'
    ref_manifest = c.read(ref_manifest_path)
    refs, ref_audit = io.final_references(ref_manifest, ctx)
    stored_candidate = c.jsonl(RUN/'reference/candidate_reference_v12_STAGE.jsonl')
    assert refs['candidate'] == stored_candidate
    third = c.jsonl(RUN/'reference/agent_T_first59_current_v12_STAGE.jsonl')
    equivalence = c.read(RUN/'reference/当前AC_T59及稳定性材料-v13逐字段等价QA.json')
    assert equivalence['all_checks_pass'] is True
    changes = [{'id': rid, 'dimensions': {dim: {'v33': c.label(methods['v33'][rid], dim),
        'v34': c.label(methods['v34'][rid], dim)} for dim in c.DIMS
        if c.label(methods['v33'][rid], dim) != c.label(methods['v34'][rid], dim)}}
        for rid in ctx['inputs'] if any(c.label(methods['v33'][rid], d) != c.label(methods['v34'][rid], d) for d in c.DIMS)]
    sample_changes = [row for row in changes if row['id'] in ctx['sample']]
    cache = {}
    records = []
    for component in ('probability_canonical', 'enriched_challenge'):
        eligible = [rid for rid, row in ctx['sample'].items() if row['component'] == component]
        for group, kind in c.groups_and_weights(component):
            ids = sorted(rid for rid in eligible if group == 'ALL' or ctx['sample'][rid]['group'] == group)
            if not ids:
                continue
            for method, predictions in methods.items():
                for reference, target in refs.items():
                    for dim in c.DIMS:
                        row = c.comparison(ctx, predictions, target, dim, ids, component, group, kind,
                                           method, reference, cache)
                        row['undefined_point_reasons'] = point_undefined_reasons(row)
                        row['FP_ids'] = [rid for rid in ids if c.label(predictions[rid], dim) == 1 and c.label(target[rid], dim) == 0]
                        row['FN_ids'] = [rid for rid in ids if c.label(predictions[rid], dim) == 0 and c.label(target[rid], dim) == 1]
                        assert row['paired_n'] == len(ids)
                        assert len(row['FP_ids']) == row['raw_confusion']['FP']
                        assert len(row['FN_ids']) == row['raw_confusion']['FN']
                        for key, expected in independent_metrics(row['weighted_confusion']).items():
                            actual = row['metrics'][key]['estimate']
                            assert (expected is None and actual is None) or np.isclose(expected, actual)
                        records.append(row)
    keys = ('component', 'group', 'weighting', 'reference', 'dimension')
    lookup = {(row['method'], *(row[k] for k in keys)): row for row in records}
    deltas = []
    for row in records:
        if row['method'] != 'v33':
            continue
        newer = lookup['v34', *(row[k] for k in keys)]
        deltas.append({**{k: row[k] for k in keys}, 'paired_n': row['paired_n'],
            'metric_changes': {name: {'v33': row['metrics'][name]['estimate'],
                'v34': newer['metrics'][name]['estimate'],
                'delta_v34_minus_v33': (newer['metrics'][name]['estimate']-row['metrics'][name]['estimate'])
                if all(r['metrics'][name]['estimate'] is not None for r in (row, newer)) else None}
                for name in ('kappa', 'precision', 'recall', 'f1')},
            'v33_FP_ids': row['FP_ids'], 'v33_FN_ids': row['FN_ids'],
            'v34_FP_ids': newer['FP_ids'], 'v34_FN_ids': newer['FN_ids']})
    ledger = []
    for rid in ctx['sample']:
        for dim in c.DIMS:
            mismatches = [{'method': m, 'reference': ref,
                'classification': 'FP' if c.label(pred[rid], dim) else 'FN'}
                for m, pred in methods.items() for ref, target in refs.items()
                if c.label(pred[rid], dim) != c.label(target[rid], dim)]
            if not mismatches:
                continue
            source = ctx['llm_inputs'][rid]
            reasons = {ref: refs[ref][rid]['dimension_reasons'][dim] for ref in ('A', 'C')}
            if rid in third:
                reasons['T'] = third[rid]['dimension_reasons'][dim]
            label_source = refs['candidate'][rid]['dimension_label_source'][dim]
            ledger.append({'id': rid, 'dimension': dim, 'component': ctx['sample'][rid]['component'],
                'group': ctx['sample'][rid]['group'], 'source_title': source['source_title'],
                'pages': source['pages'], 'text': source['text'], 'contexts': source['contexts'],
                'predictions': {m: c.label(pred[rid], dim) for m, pred in methods.items()},
                'references': {r: c.label(target[rid], dim) for r, target in refs.items()},
                'candidate_dimension_label_source': label_source, 'reference_reasons': reasons,
                'reference_literal_evidence': {ref: [e for e in rows[rid]['evidence'] if e['dimension'] == dim]
                    for ref, rows in {'A': refs['A'], 'C': refs['C'], 'T': third}.items() if rid in rows},
                'mismatches_relative_to_references_not_semantic_gold': mismatches,
                'method_diagnostics': {m: {k: pred[rid]['prediction'].get(k) for k in
                    ('evidence', 'suppressions', 'review_flags', 'source_context_adaptation_log_v33',
                     'source_field_consumption_v34', 'typed_contexts_v34')} for m, pred in methods.items()}})
    provenance = {'status': 'development_diagnostic_stage_v13_same_context_reference_v12',
        'created_at': datetime.datetime.now().astimezone().isoformat(), 'human_validation_completed': False,
        'v34_is_independent_confirmation': False, 'formal_baseline_retained': 'rules-v33',
        'v14_final_results': False, 'source_or_method_or_reference_labels_modified': False,
        'sample_reference_n': 240, 'probability_n': 180, 'challenge_n': 60,
        'full_corpus_binary_changed_case_n': len(changes), 'sample_binary_changed_case_n': len(sample_changes),
        'bindings': {'v34_seal': bd(manifest_path), 'methods': run_bindings,
            'reference_manifest': bd(ref_manifest_path), 'stored_candidate': bd(RUN/'reference/candidate_reference_v12_STAGE.jsonl'),
            'third': bd(RUN/'reference/agent_T_first59_current_v12_STAGE.jsonl'),
            'source_context_equivalence': bd(RUN/'reference/当前AC_T59及稳定性材料-v13逐字段等价QA.json')},
        'script_sha256': c.sha(Path(__file__)), 'analysis_notes': c.analysis_notes()}
    OUT.mkdir()
    c.write_json(OUT/'comparisons.json', {'provenance': provenance, 'comparisons': records})
    c.write_json(OUT/'actual_metric_differences.json', {'provenance': provenance, 'comparisons': deltas,
        'full_corpus_binary_changes': changes, 'sample_binary_changes': sample_changes})
    c.write_json(OUT/'false_positive_negative_ledger_PRIVATE.json', {'provenance': provenance, 'case_dimension_records': ledger})
    c.write_json(OUT/'independent_numeric_and_material_QA.json', {'status': 'pass', 'all_checks_pass': True,
        'reference_material_current_v13_checked': {r: len(ref_audit[r]['material_ids_checked']) for r in 'AC'},
        'third_reviewed_n': len(ref_audit['T']['reviewed_original_ids']), 'stored_candidate_exact_reconstruction': True,
        'comparison_n': len(records), 'independent_scalar_checks_n': 4*len(records),
        'FP_FN_ID_counts_match': True, 'reference_files_unchanged': all(c.sha(x['path']) == x['sha256']
            for x in ref_manifest['references'].values()), 'source_sha256': c.sha(OUT/'comparisons.json')})
    fmt = lambda x: 'NA' if x is None else f'{x:.3f}'
    lines = ['v33 / v34 阶段诊断（v13 同材料；参考为 v12 阶段 A/C/T）', '',
        'v34 为已暴露后的开发诊断，不能称独立确认。正式规则基准仍为 v33。参考由 AI agent 给出，尚非真人金标；这不是 v14 终版。', '',
        f'全库二元标签变化 {len(changes)} 条；固定 240 条样本中变化 {len(sample_changes)} 条。概率样本180条与挑战样本60条分开报告，不合并估计总体表现。', '',
        '每组表中依次列出 κ / Precision / Recall / F1。NA 表示分母为零；NA 的差值也为 NA。0.80 只作诊断工作目标，不是普遍发表门槛。', '']
    for component, weighting, title in [('probability_canonical', 'unweighted', '概率样本180：等额样本构成'),
        ('probability_canonical', 'eligible_design_weighted', '概率样本180：抽样框设计加权'),
        ('enriched_challenge', 'unweighted', '挑战样本60：描述统计')]:
        lines += [title, '', '|参考|维度|v33 κ / P / R / F1|v34 κ / P / R / F1|变化 κ / P / R / F1|', '|---|---|---|---|---|']
        for row in deltas:
            if (row['component'], row['group'], row['weighting']) != (component, 'ALL', weighting):
                continue
            cells = [' / '.join(fmt(v[key]) for v in row['metric_changes'].values())
                     for key in ('v33', 'v34', 'delta_v34_minus_v33')]
            lines.append(f"|{row['reference']}|{row['dimension']}|{'|'.join(cells)}|")
        lines.append('')
    lines += ['候选参考下的具体误报/漏报 ID（相对 AI 候选参考，不等于确定语义错误）', '',
              '|样本|维度|FP|FN|', '|---|---|---|---|']
    for row in deltas:
        if row['reference'] == 'candidate' and row['group'] == 'ALL' and row['weighting'] == 'unweighted':
            lines.append(f"|{row['component']}|{row['dimension']}|{', '.join(row['v33_FP_ids']) or '无'}|{', '.join(row['v33_FN_ids']) or '无'}|")
    lines += ['', '逐条原文、全部语境、A/C/T理由、逐字证据和规则触发/抑制信息见 false_positive_negative_ledger_PRIVATE.json。各部门指标、区间及其未定义重复次数见 comparisons.json。', '',
        '设计加权只推断剩余 canonical 抽样框 NMPA947 / NHSA760 / NHC60；NHC 是该框全查。区间条件于固定材料和标注，并不量化语义真值不确定性；稀有阳性或全查可出现退化区间。', '']
    (OUT/'diagnostic_tables.md').write_text('\n'.join(lines))
    c.write_json(OUT/'output_freeze.json', {'files': {p.name: c.sha(p) for p in OUT.iterdir() if p.is_file()}})
    print(json.dumps({'status': 'complete_stage_diagnostic', 'output': str(OUT), 'comparisons': len(records),
        'full_binary_changed_n': len(changes), 'sample_binary_changed_n': len(sample_changes),
        'unique_error_case_dimension_n': len(ledger)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
