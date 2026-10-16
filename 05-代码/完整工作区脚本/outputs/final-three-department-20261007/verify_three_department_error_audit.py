"""Read-only reconciliation of every weak-cell case and label-free packet."""
from pathlib import Path
from collections import Counter
import hashlib,json

OUT=Path(__file__).resolve().parent


def main():
    audit=json.loads((OUT/'error_audit.json').read_text())
    metrics=json.loads((OUT/'三部门编码指标.json').read_text())
    expected=[r for r in metrics['records'] if r['group']!='ALL' and (r['metrics']['kappa']['estimate'] is None or r['metrics']['kappa']['estimate']<.8)]
    assert len(expected)==audit['weak_comparison_count']==len(audit['weak_comparisons'])
    cases={c['case_key']:c for c in audit['cases']}
    assert len(cases)==audit['unique_case_dimension_count']
    inputs={r['id']:r for r in map(json.loads,Path(metrics['method_bindings']['rule']['inputs']).read_text().splitlines())}
    for case in cases.values():assert case['unit_text']==inputs[case['id']]['input']['unit_text']
    for r in audit['weak_comparisons']:
        assert len(r['all_unit_contributions'])==r['frame_n']
        counts=Counter(c['contribution'] for c in r['all_unit_contributions'])
        assert sum(v for k,v in counts.items() if k.startswith('excluded'))==r['excluded_n']
        for key,value in (r['cross_tab'] or r['confusion']).items():assert counts[key]==value
        for row in r['all_unit_contributions']:
            assert {'record_key':r['record_key'],'contribution':row['contribution']} in cases[row['case_key']]['metric_contributions']
    full=[json.loads(s) for s in (OUT/'blind_error_packet.jsonl').read_text().splitlines()]
    focus=[json.loads(s) for s in (OUT/'blind_error_packet_focus.jsonl').read_text().splitlines()]
    assert len(full)==len(cases) and len(focus)==audit['focus_case_dimension_count']
    allowed={'blind_id','task_dimension','unit_text','paragraph_context','nearest_preceding_heading','immediately_preceding_paragraph','verified_object_scope_texts'}
    mapping={c['blind_id']:c for c in cases.values()}
    assert len(mapping)==len(cases)
    assert all(set(row)==allowed for row in full+focus)
    assert {r['blind_id'] for r in full}==set(mapping)
    for row in full+focus:assert row['unit_text']==mapping[row['blind_id']]['unit_text']
    for row in focus:
        case=mapping[row['blind_id']]
        assert any(x==1 for x in (case['A'],case['C'],*case['machine_labels'].values()))
    result={'status':'passed','weak_comparisons':len(expected),'case_dimensions':len(cases),
            'blind_focus_cases':len(focus),'blind_fields':sorted(allowed),'all_contributions_reconcile':True,
            'current_rule_method':metrics['method_bindings']['rule']['method'],
            'files':{name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in ('error_audit.json','blind_error_packet.jsonl','blind_error_packet_focus.jsonl')}}
    (OUT/'error_audit_qa.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
