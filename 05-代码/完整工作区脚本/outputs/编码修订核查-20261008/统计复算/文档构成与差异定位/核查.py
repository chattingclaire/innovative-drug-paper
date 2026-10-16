"""Describe source composition and locate existing coding differences; never label text."""
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
W = HERE.parents[1]
DIMS = ['S', 'E', 'Ec', 'I', 'F']
PATHS = {
    'frame': W/'人工参照复核/全量目标框验证准备01/source_only_frame_all4481.jsonl',
    'rule': W/'自动规则编码/共同定义候选/candidate12/composite-source04-actual01/all_predictions.jsonl',
    'llm': W/'LLM编码/统一判据编码准备/runtime/composite-source04-actual01/all_predictions.jsonl',
}
EXPECTED = {
    'frame': '301f05240c8ada00129ed8f84bc68e5047118cdedef9777937f01d49cad17c29',
    'rule': 'a799245fab064e8e47a76658946c7ebd25b6d1bbaa5d0a768bd27c1136d7b78e',
    'llm': '8b257a22fcc082e73380f1542ca7aa9e23ee7ba94e472de75a491fcc7296fc59',
}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load(path):
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    assert len({r['id'] for r in rows}) == len(rows)
    return {r['id']: r for r in rows}

def binary(labels):
    return isinstance(labels, dict) and all(type(labels.get(d)) is int and labels[d] in (0, 1) for d in DIMS)

def main():
    for key, path in PATHS.items():
        assert digest(path) == EXPECTED[key], key
    frame, rule, llm = [load(PATHS[k]) for k in ['frame', 'rule', 'llm']]
    assert len(frame) == 4481
    docs, unknown = {}, []
    for rid, unit in frame.items():
        group, source = unit['analysis_group'], unit['source_document_stem']
        key = (group, source)
        if key not in docs:
            docs[key] = {'department': group, 'document': source, 'n_units': 0,
                         'n_paired_complete': 0, 'n_unknown': 0, 'families': set(),
                         **{f'{m}_{d}': 0 for m in ['rule', 'llm'] for d in DIMS}}
        doc = docs[key]
        doc['n_units'] += 1
        doc['families'].add(unit['normalized_text_family']['family_id'])
        a, b = rule[rid]['prediction'].get('labels'), llm[rid].get('labels')
        # Raw historic outputs can contain binary placeholders for a material
        # issue later established by source review. Retain the unit but do not
        # reuse those values as resolved labels in a new diagnostic derivative.
        unresolved = any(i.get('status', '').startswith('unresolved')
                         for i in unit.get('known_material_issues', []))
        if unresolved or not (binary(a) and binary(b)):
            doc['n_unknown'] += 1
            unknown.append(rid)
            continue
        doc['n_paired_complete'] += 1
        for dim in DIMS:
            doc[f'rule_{dim}'] += a[dim]
            doc[f'llm_{dim}'] += b[dim]
    rows = []
    for key, doc in sorted(docs.items()):
        doc['n_unique_current_texts'] = len(doc.pop('families'))
        for dim in DIMS:
            doc[f'net_difference_{dim}_llm_minus_rule'] = doc[f'llm_{dim}']-doc[f'rule_{dim}']
        rows.append(doc)
    summary = {}
    for group in ['NMPA', 'NHSA', 'NHC']:
        selected = [r for r in rows if r['department'] == group]
        total = sum(r['n_units'] for r in selected)
        top_volume = sorted(selected, key=lambda r: (-r['n_units'], r['document']))[:3]
        top_gap = sorted(selected, key=lambda r: (-abs(r['net_difference_I_llm_minus_rule']), r['document']))[:5]
        summary[group] = {
            'n_documents': len(selected), 'n_units': total,
            'n_unknown': sum(r['n_unknown'] for r in selected),
            'top3_document_unit_share': sum(r['n_units'] for r in top_volume)/total,
            'top3_documents_by_units': [{k:r[k] for k in ['document','n_units']} for r in top_volume],
            'dimension_counts': {m:{d:sum(r[f'{m}_{d}'] for r in selected) for d in DIMS} for m in ['rule','llm']},
            'I_difference_by_largest_documents': [{k:r[k] for k in ['document','n_units','rule_I','llm_I','net_difference_I_llm_minus_rule']} for r in top_gap],
        }
    assert sum(x['n_units'] for x in summary.values()) == 4481
    assert unknown == ['RECODE25-00064'], unknown
    with (HERE/'逐文件构成与编码句次.csv').open('w', encoding='utf-8-sig', newline='') as out:
        writer = csv.DictWriter(out, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    record = {'status':'diagnostic_existing_outputs_not_new_coding', 'bindings':{k:{'path':str(v),'sha256':digest(v)} for k,v in PATHS.items()},
              'summary':summary, 'unknown_retained':unknown, 'no_new_labels':True,
              'no_adoption':True, 'no_causal_attribution':True, 'no_automatic_recode_selection':True,
              'script_sha256':digest(Path(__file__))}
    (HERE/'构成核查记录.json').write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__ == '__main__':
    main()
