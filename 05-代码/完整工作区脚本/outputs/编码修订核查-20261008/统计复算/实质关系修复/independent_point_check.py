"""Independent counts and elementary four-cell arithmetic for current outputs."""
import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIMS = ('S', 'E', 'Ec', 'I', 'F')

def load(path):
    return json.loads(Path(path).read_text())

def rows(path):
    return [json.loads(s) for s in Path(path).read_text().splitlines() if s.strip()]

def main():
    bundle_path = HERE / '当前同材料结果/同材料结果绑定.json'
    bundle = load(bundle_path)
    output = HERE / '当前同材料结果/数据汇总独立核对.json'
    assert not output.exists()
    def bound(role):
        ref = bundle[role]
        assert hashlib.sha256(Path(ref['path']).read_bytes()).hexdigest() == ref['sha256']
        return rows(ref['path'])
    frame = {r['id']: r for r in bound('frame')}
    rule = {r['id']: r['result']['labels'] for r in bound('rule_output')}
    llm = {r['id']: r['labels'] for r in bound('llm_output')}
    assert len(rule) == len(llm) == 4480 and set(rule) == set(llm)
    unknown = sorted(set(frame) - set(rule))
    assert unknown == ['RECODE25-00064']
    assert all(v in (0, 1) for source in (rule, llm) for row in source.values() for v in row.values())
    groups = sorted({r['analysis_group'] for r in frame.values()})
    result = {'bundle_path': str(bundle_path),
        'bundle_sha256': hashlib.sha256(bundle_path.read_bytes()).hexdigest(),
        'basis': 'unweighted_complete_same_material_method_comparison_not_human_validation',
        'target_n': len(frame), 'executed_n': len(rule), 'unknown_ids': unknown,
        'groups': {}}
    for group in ['ALL'] + groups:
        ids = [i for i in rule if group == 'ALL' or frame[i]['analysis_group'] == group]
        missing = [i for i in unknown if group == 'ALL' or frame[i]['analysis_group'] == group]
        g = {'n': len(ids), 'missing_ids': missing, 'methods': {}, 'dimensions': {}}
        for name, source in [('rule', rule), ('llm', llm)]:
            counts = {d: sum(source[i][d] for i in ids) for d in DIMS}
            total = sum(counts.values())
            shares = {d: counts[d] / total * 100 for d in DIMS}
            assert abs(sum(shares.values()) - 100) < 1e-10
            g['methods'][name] = {'counts': counts, 'five_dimension_total': total, 'attention_percent': shares}
            if missing:
                assert len(missing) == 1
                bounds = {d: [] for d in DIMS}
                for bits in itertools.product((0, 1), repeat=5):
                    for d, bit in zip(DIMS, bits):
                        bounds[d].append((counts[d] + bit) / (total + sum(bits)) * 100)
                g['methods'][name]['missing_one_record_math_bounds_percent_not_CI'] = {
                    d: [min(v), max(v)] for d, v in bounds.items()}
        for d in DIMS:
            cells = {str(a) + str(b): sum(rule[i][d] == a and llm[i][d] == b for i in ids)
                     for a, b in itertools.product((0, 1), repeat=2)}
            n = len(ids)
            agreement = (cells['00'] + cells['11']) / n
            r1 = (cells['10'] + cells['11']) / n
            l1 = (cells['01'] + cells['11']) / n
            chance = r1 * l1 + (1 - r1) * (1 - l1)
            g['dimensions'][d] = {'four_cells_rule_llm': cells,
                'agreement': agreement, 'chance_agreement': chance,
                'kappa': (agreement - chance) / (1 - chance) if chance != 1 else None,
                'discordant_n': cells['01'] + cells['10'],
                'attention_difference_llm_minus_rule_pp': g['methods']['llm']['attention_percent'][d] - g['methods']['rule']['attention_percent'][d]}
        result['groups'][group] = g
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'output': str(output), 'kappa': {d: result['groups']['ALL']['dimensions'][d]['kappa'] for d in DIMS},
        'counts': {m: result['groups']['ALL']['methods'][m]['counts'] for m in ('rule', 'llm')}}, ensure_ascii=False))

if __name__ == '__main__':
    main()
