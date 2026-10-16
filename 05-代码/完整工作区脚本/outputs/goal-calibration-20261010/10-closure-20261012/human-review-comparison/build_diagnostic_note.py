"""Explain existing review disagreements; does not recode or amend any input."""
from collections import Counter
from datetime import datetime
from fractions import Fraction
from pathlib import Path
from zoneinfo import ZoneInfo
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
RESULTS = HERE / 'results'


def read(path):
    return json.loads(path.read_text())


def binding(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def main():
    comparison = read(RESULTS / 'comparison.json')
    for source in comparison['source_bindings'].values():
        assert binding(Path(source['path'])) == source
    joined = [json.loads(line) for line in (RESULTS / 'joined-dimension-records.jsonl').read_text().splitlines()]
    fairness = [row for row in joined if row['dimension'] == 'F']
    assert len(fairness) == 200
    output = {
        'created_at_shanghai': datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        'scope': 'Fixed200 human-review disagreement explanation; no new gold labels or accuracy validation',
        'source_bindings': {
            'comparison': binding(RESULTS / 'comparison.json'),
            'joined': binding(RESULTS / 'joined-dimension-records.jsonl'),
            'frozen_manual': binding(ROOT / '03-manual/full4481-common-release-20261010-root/manual.txt'),
        },
        'labels_modified': False,
        'weights_modified': False,
        'formal_acceptance': False,
        'fairness': {},
    }
    for method in ('rule', 'LLM'):
        raw = Counter()
        weighted = {cell: Fraction(0) for cell in ('TP', 'FP', 'FN', 'TN')}
        contributors = {cell: [] for cell in weighted}
        for row in fairness:
            prediction, reviewed = row[method], row['human_reviewed_value']
            if prediction is None or reviewed is None:
                continue
            cell = {(1, 1): 'TP', (1, 0): 'FP', (0, 1): 'FN', (0, 0): 'TN'}[(prediction, reviewed)]
            weight = Fraction(row['original_weight_exact'])
            raw[cell] += 1
            weighted[cell] += weight
            contributors[cell].append({'source_id': row['source_id'], 'weight_exact': str(weight)})
        published = next(row for row in comparison['numeric_comparisons']
                         if (row['group'], row['method'], row['dimension']) == ('all200', method, 'F'))
        order = published['cell_order']
        assert [raw[c] for c in order] == published['raw_cells']
        assert [str(weighted[c]) for c in order] == published['original_weighted_cells_exact']
        output['fairness'][method] = {
            'raw_cells': dict(raw),
            'weighted_cells_exact': {c: str(v) for c, v in weighted.items()},
            'contributors': contributors,
            'common_binary_N': published['common_binary_N'],
            'machine_lawful_null_N': published['machine_lawful_null_N'],
            'raw_metrics': published['raw_metrics'],
            'weighted_metrics': published['original_weighted_metrics'],
        }
    rule_heavy = sum((Fraction(row['original_weight_exact']) for row in fairness
                      if row['source_id'] in ('RECODE25-00104', 'RECODE25-04598')), Fraction(0))
    rule_fn = Fraction(output['fairness']['rule']['weighted_cells_exact']['FN'])
    llm_heavy = sum((Fraction(row['original_weight_exact']) for row in fairness
                     if row['source_id'] in ('RECODE25-00090', 'RECODE25-01112', 'RECODE25-01136')), Fraction(0))
    llm_fp = Fraction(output['fairness']['LLM']['weighted_cells_exact']['FP'])
    output['weight_concentration'] = {
        'rule_00104_04598_share_of_FN_weight_exact': str(rule_heavy / rule_fn),
        'rule_00104_04598_share_of_FN_weight': float(rule_heavy / rule_fn),
        'LLM_00090_01112_01136_share_of_FP_weight_exact': str(llm_heavy / llm_fp),
        'LLM_00090_01112_01136_share_of_FP_weight': float(llm_heavy / llm_fp),
    }
    ids = {row['source_id'] for row in fairness
           if any(row[m] is not None and row[m] != row['human_reviewed_value'] for m in ('rule', 'LLM'))}
    assert ids == {'RECODE25-' + n for n in ('00050', '00090', '00104', '00136', '01112', '01136', '01473', '04598')}
    output['fairness_disagreements'] = sorted((row for row in fairness if row['source_id'] in ids), key=lambda row: row['source_id'])
    extra_s = {'RECODE25-' + n for n in ('02854', '04130', '04374')}
    output['priority_safety_disagreements'] = [row for row in joined if row['dimension'] == 'S' and row['source_id'] in extra_s]
    assert len(output['priority_safety_disagreements']) == 3
    selected = {}
    machine_records = {}
    for method in ('rule', 'LLM'):
        file = Path(comparison['source_bindings'][method]['path'])
        records = {}
        for line in file.open():
            row = json.loads(line)
            if row['id'] in ids | extra_s:
                records[row['id']] = row
        assert len(records) == len(ids | extra_s)
        machine_records[method] = records
    for row in output['fairness_disagreements'] + output['priority_safety_disagreements']:
        sid, dim = row['source_id'], row['dimension']
        rule, llm = (machine_records[m][sid] for m in ('rule', 'LLM'))
        assert rule['labels'][dim] == row['rule'] and llm['labels'][dim] == row['LLM']
        packet = Path(llm['packet']['path'])
        assert binding(packet) == llm['packet']
        material = read(packet)['source_bundle']['source_record']
        selected[sid + '/' + dim] = {
            'current_text': material['text'],
            'source_ref': material.get('source_ref'),
            'packet': llm['packet'],
            'rule_reason': rule['decisions'][dim]['reason'],
            'rule_basis_path': rule['decisions'][dim]['basis_path'],
            'LLM_reason': llm['dimensions'][dim]['reason'],
            'LLM_evidence': llm['dimensions'][dim]['evidence'],
        }
    output['current_machine_reason_alignment'] = selected
    with (RESULTS / 'disagreement-diagnostic-details.json').open('x') as file:
        json.dump(output, file, ensure_ascii=False, indent=2)
        file.write('\n')
    print(json.dumps({'created': str(RESULTS / 'disagreement-diagnostic-details.json'),
                      'F_cells_match_published': True, 'F_disagreements': len(ids),
                      'priority_S': len(extra_s), 'weights': output['weight_concentration']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
