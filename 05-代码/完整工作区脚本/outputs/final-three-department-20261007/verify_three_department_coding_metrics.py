"""Independent standard-library checks of the paired coding metric artifacts."""
from pathlib import Path
from collections import Counter
import csv
import hashlib
import json
import math

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]


def read_jsonl(path):
    return {r['id']: r for r in map(json.loads, Path(path).read_text().splitlines())}


def binary(value):
    return type(value) is int and value in (0, 1)


def close(actual, expected):
    assert actual is None if expected is None else actual is not None and abs(actual-expected) < 1e-12


def main():
    target = OUT/'三部门编码指标.json'
    target_sha256 = hashlib.sha256(target.read_bytes()).hexdigest()
    result = json.loads(target.read_text())
    records = result['records']
    csv_rows = list(csv.DictReader((OUT/'三部门编码指标.csv').open(encoding='utf-8-sig')))
    lookup = {(r['frame'],r['group'],r['dimension'],r['method'],r['reference']): r for r in records}
    assert len(lookup) == len(records)
    for row in csv_rows:
        r = lookup[tuple(row[k] for k in ('frame','group','dimension','method','reference'))]
        metric = r['metrics'][row['metric']]
        for key in ('estimate','low','high'):
            value = metric['estimate'] if key == 'estimate' else metric['ci95'][key]
            assert row[key] == '' if value is None else float(row[key]) == value
        assert int(row['defined_repetitions']) + int(row['undefined_repetitions']) == 5000
    assert len(csv_rows) == sum(len(r['metrics']) for r in records)
    for r in records:
        assert r['n'] + r['excluded_n'] == r['frame_n']
        assert sum(r['exclusions'].values()) == len(r['excluded_units']) == r['excluded_n']
        assert sum((r['confusion'] or r['cross_tab']).values()) == r['n']
        if r['method'] == 'A_C':
            assert not {'precision','recall','f1'} & r['metrics'].keys()
            assert r['confusion'] is None and r['accuracy_claim'] is False
        for metric in r['metrics'].values():
            assert metric['estimate'] is None or math.isfinite(metric['estimate'])
            assert metric['ci95']['defined_repetitions'] + metric['ci95']['undefined_repetitions'] == 5000
    for path, digest in result['source_sha256'].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path

    # Independently reconstruct every main-frame comparison from the original
    # references, rule predictions and department metadata, with scalar formulas.
    bindings=result['method_bindings']
    inputs = read_jsonl(bindings['rule']['inputs'])
    rules = read_jsonl(bindings['rule']['rules'])
    machines={bindings['rule']['method']:{rid:row['prediction']['labels'] for rid,row in rules.items()}}
    if bindings['llm']['path']:
        machines[bindings['llm']['method']]={rid:row.get('prediction',row)['labels'] for rid,row in read_jsonl(bindings['llm']['path']).items()}
    refs = read_jsonl(ROOT/'outputs/autocode-v25-20260927/current_1268_references.jsonl')
    metadata_rows = json.loads((ROOT/'outputs/validation-expansion-20260926/frozen-inputs/classification--部门归属与年度系列-冻结v1.json').read_text())['rows']
    metadata = {Path(r['original_file']).stem: r['analysis_group'] for r in metadata_rows}
    frame_refs={'main1057':refs}
    h=ROOT/'outputs/autocode-v25-20260927/H427'
    mapping=json.loads((h/'admin_mapping.json').read_text())
    coder_rows={}
    for coder in ('A','C'):
        coder_rows[coder]={}
        for p in sorted((h/f'agent-{coder}').glob('结果-*.json')):
            for row in json.loads(p.read_text())['rows']:
                assert row['id'] not in coder_rows[coder]
                coder_rows[coder][row['id']]=row
    frame_refs['supplement_H411']={row['rerun_id']:{'original_references':{coder:coder_rows[coder][row['id']] for coder in ('A','C')}} for row in mapping}
    verified = 0
    verified_by_frame=Counter()
    for r in records:
        counts = Counter()
        exclusions = Counter()
        eligible_ids = []
        for rid, ref in frame_refs[r['frame']].items():
            group = metadata[inputs[rid]['input']['original_file_stem']]
            if group not in result['scope'] or (r['group'] != 'ALL' and r['group'] != group):
                continue
            dim = r['dimension']
            left = ref['original_references']['A']['labels'][dim] if r['method'] == 'A_C' else machines[r['method']][rid][dim]
            right = ref['original_references'][r['reference']]['labels'][dim]
            if binary(left) and binary(right):
                counts[left,right] += 1
                eligible_ids.append(rid)
            else:
                reason = 'both_pending' if not binary(left) and not binary(right) else 'left_pending_only' if not binary(left) else 'right_pending_only'
                exclusions[reason] += 1
        tp,fp,fn,tn = (counts[key] for key in ((1,1),(1,0),(0,1),(0,0)))
        assert [tp,fp,fn,tn] == list((r['cross_tab'] or r['confusion']).values())
        assert dict(exclusions) == {k:v for k,v in r['exclusions'].items() if v}
        assert hashlib.sha256('\n'.join(sorted(eligible_ids)).encode()).hexdigest() == r['eligible_ids_sha256']
        n = tp+fp+fn+tn
        po = (tp+tn)/n
        pe = ((tp+fp)*(tp+fn)+(fn+tn)*(fp+tn))/n**2
        expected = {'kappa':(po-pe)/(1-pe) if pe != 1 else None,
                    'agreement':po,'left_positive_rate':(tp+fp)/n,'right_positive_rate':(tp+fn)/n}
        if r['method'] != 'A_C':
            expected.update(precision=tp/(tp+fp) if tp+fp else None,
                            recall=tp/(tp+fn) if tp+fn else None,
                            f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None)
        for metric, value in expected.items():
            close(r['metrics'][metric]['estimate'],value)
        verified += 1
        verified_by_frame[r['frame']]+=1
    assert hashlib.sha256(target.read_bytes()).hexdigest() == target_sha256, 'Target changed during verification'
    summary = {'status':'passed','target':str(target.resolve()),'target_sha256':target_sha256,
               'comparison_records':len(records),'csv_metric_intervals':len(csv_rows),
               'records_independently_reconstructed':verified,
               'main_records_independently_reconstructed':verified_by_frame['main1057'],
               'reconstructed_by_frame':dict(verified_by_frame),
               'unchanged_source_hashes':len(result['source_sha256']),
               'checks':['Original main-frame binary pairing and pending exclusions',
                         'Scalar confusion-table kappa, agreement, P/R/F1 and class proportions',
                         'Eligible ID hashes','JSON/CSV identical values and nulls',
                         '5000 defined plus undefined repetitions for every metric',
                         'A/C symmetric reporting without accuracy claims','Unchanged source SHA256 hashes'],
               'latest_llm':result['latest_llm']}
    (OUT/'三部门编码指标核验.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary,ensure_ascii=False))


if __name__ == '__main__':
    main()
