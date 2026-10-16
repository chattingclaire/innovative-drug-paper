"""Check a sealed native AI first run, preserving all semantic nulls."""
from pathlib import Path
import hashlib
import importlib.util
import json
from fractions import Fraction
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / '06-coding/native-llm41-sol/first-run'
DEST = ROOT / '06-coding/root-machine-review/native-llm41-first-run'
FIXTURE = ROOT / '06-coding/development-reference41-v11'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

def rows(path):
    sequence = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    assert len(sequence) == len({x['id'] for x in sequence})
    return {x['id']: x for x in sequence}

def ratio(a, b):
    return None if not b else float(Fraction(a, b))

def main():
    seal = json.loads((RUN/'seal.json').read_text())
    assert seal['status'] == 'sealed' and not seal['reference_read']
    for entry in seal['files']:
        path = RUN/entry['name']
        assert sha(path) == entry['sha256'] and path.stat().st_size == entry['bytes']
    submission = json.loads((RUN/'submission.json').read_text())
    assert submission['identity']['actor_type'] == 'AI'
    for entry in submission['actual_read_research_assets']:
        path = Path(entry['path'])
        assert sha(path) == entry['sha256'] and path.stat().st_size == entry['bytes']
    assert sha(RUN/'predictions.jsonl') == submission['predictions_sha256']
    pred, source, ref = (rows(RUN/'predictions.jsonl'), rows(FIXTURE/'source.jsonl'),
                         rows(FIXTURE/'reference.jsonl'))
    assert set(pred) == set(source) == set(ref) and len(pred) == 41
    spec = importlib.util.spec_from_file_location('independent_math', ROOT/'scripts/audit_pilot.py')
    math = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(math)
    metrics, comparison, quality = {}, [], []
    for dim in ['S', 'E', 'Ec', 'I', 'F']:
        cells, nine, unknown = [0, 0, 0, 0], Counter(), []
        for ident in sorted(pred):
            item = pred[ident]
            value, reference = item['labels'][dim], ref[ident]['labels'][dim]
            assert value is None or type(value) is int and value in (0, 1)
            assert type(reference) is int and reference in (0, 1)
            evidence = item['evidence'][dim]
            assert evidence['value'] == value and evidence['current_quote'] == source[ident]['text']
            assert evidence['reason']
            byctx = {c['context_id']: c for c in source[ident]['contexts']}
            for quote in evidence['contexts_used']:
                context = byctx[quote['context_id']]
                text = quote['quote']
                available = [context[k] for k in ['text', 'headers', 'row_cells', 'title', 'caption']
                             if isinstance(context.get(k), str)]
                available += [s for k in ['headers', 'row_cells']
                              for s in (context.get(k) or []) if isinstance(s, str)]
                if text is None and not any(available):
                    # A textless structural node is evidence of a relation,
                    # never a fabricated quotation of a source sentence.
                    continue
                if not text or not any(text in s for s in available):
                    quality.append({'id': ident, 'dimension': dim, 'quote': text})
            nine[f'{value}|{reference}'] += 1
            comparison.append({'id': ident, 'dimension': dim, 'prediction': value,
                               'reference': reference, 'source_text': source[ident]['text'],
                               'prediction_evidence': evidence,
                               'reference_evidence_A': ref[ident]['evidence_A'][dim],
                               'reference_evidence_B': ref[ident]['evidence_B'][dim],
                               'material_requests': item.get('material_requests', []),
                               'comparison': 'unknown_prediction' if value is None else
                               'agree' if value == reference else 'FP' if value else 'FN'})
            if value is None:
                unknown.append({'id': ident, 'reference': reference})
            else:
                cells[2*value+reference] += 1
        tn, fn, fp, tp = cells
        point = math.statistics(*cells)
        positives = sum(x['labels'][dim] for x in ref.values())
        unknown_positive = sum(x['reference'] for x in unknown)
        metrics[dim] = {'assigned_n': 41, 'comparable_n': sum(cells),
                        'unknown_prediction_n': len(unknown), 'unknown_reference_n': 0,
                        'execution_failure_n': 0,
                        'four_cells': {'TP': tp, 'FP': fp, 'FN': fn, 'TN': tn},
                        'kappa': point['kappa'], 'precision': ratio(tp, tp+fp),
                        'recall': ratio(tp, tp+fn), 'F1': ratio(2*tp, 2*tp+fp+fn),
                        'Po': point['agreement'],
                        'Ppos': point['positive_specific_agreement'],
                        'Pneg': point['negative_specific_agreement'],
                        'specificity': ratio(tn, tn+fp),
                        'full_3x3': {f'{a}|{b}': nine[f'{a}|{b}']
                                     for a in ['0', '1', 'None'] for b in ['0', '1', 'None']},
                        'unknown': unknown,
                        'recall_completion_bounds': {
                            'lower': ratio(tp, positives),
                            'upper': ratio(tp+unknown_positive, positives),
                            'meaning': 'Marginal binary-completion bounds, no imputation, not a 95% CI'},
                        'CI95': None, 'CI_reason': 'Nonprobability historically exposed development fixture'}
    assert not quality, quality
    result = {'identity': 'native_Codex_AI_vs_AI_consensus_development', 'n': 41,
              'per_dimension': metrics, 'quality_issues': quality, 'comparison_n': len(comparison),
              'binary_disagreements': [{'id': x['id'], 'dimension': x['dimension'],
                                       'direction': x['comparison']} for x in comparison
                                      if x['comparison'] in ['FP', 'FN']],
              'source_sha256': sha(FIXTURE/'source.jsonl'),
              'manual_sha256': seal['input_manual_sha256'],
              'predictions_sha256': sha(RUN/'predictions.jsonl'),
              'reference_sha256': sha(FIXTURE/'reference.jsonl'), 'seal_sha256': sha(RUN/'seal.json'),
              'semantic_nulls_preserved': True, 'unknown_not_counted_as_zero': True,
              'first_judgments_unchanged': True, 'human_validation': False,
              'formal_acceptance': False, 'underlying_provider_model_calls': None}
    DEST.mkdir(exist_ok=True)
    with (DEST/'arithmetic-and-quality-audit.json').open('x') as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    with (DEST/'comparison205.jsonl').open('x') as stream:
        stream.write(''.join(json.dumps(x, ensure_ascii=False)+'\n' for x in comparison))
    print(json.dumps({'metrics': {d: {k: v[k] for k in ['comparable_n', 'unknown_prediction_n',
                      'four_cells', 'kappa', 'precision', 'recall', 'F1']} for d, v in metrics.items()},
                      'binary_disagreements': result['binary_disagreements']}, ensure_ascii=False))

if __name__ == '__main__':
    main()
