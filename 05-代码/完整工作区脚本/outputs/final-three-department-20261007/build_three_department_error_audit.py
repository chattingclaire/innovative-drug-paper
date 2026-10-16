"""Read-only audit of sparse or low-kappa cells; exports label-free text packets."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import random

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
DIMS = ('S','E','Ec','I','F')
GROUPS = ('NMPA','NHSA','NHC')
NAMES = {'S':'安全性','E':'有效性','Ec':'经济性','I':'创新性','F':'公平性'}


def jsonl(path):
    return {r['id']:r for r in map(json.loads,Path(path).read_text().splitlines())}


def binary(value):
    return type(value) is int and value in (0,1)


def main():
    m=json.loads((OUT/'三部门编码指标.json').read_text())
    binding=m['method_bindings']
    inputs=jsonl(binding['rule']['inputs'])
    rules=jsonl(binding['rule']['rules'])
    machines={binding['rule']['method']:rules}
    if binding['llm']['path']:
        machines[binding['llm']['method']]=jsonl(binding['llm']['path'])
    refs=jsonl(ROOT/'outputs/autocode-v25-20260927/current_1268_references.jsonl')
    frames={'main1057':{rid:{c:row['original_references'][c] for c in ('A','C')} for rid,row in refs.items()}}
    h=ROOT/'outputs/autocode-v25-20260927/H427'
    mapping=json.loads((h/'admin_mapping.json').read_text())
    hcoders={}
    for coder in ('A','C'):
        rows=[]
        for p in sorted((h/f'agent-{coder}').glob('结果-*.json')):
            rows.extend(json.loads(p.read_text())['rows'])
        hcoders[coder]={r['id']:r for r in rows}
    frames['supplement_H411']={r['rerun_id']:{c:hcoders[c][r['id']] for c in ('A','C')} for r in mapping}
    metadata=json.loads((ROOT/'outputs/validation-expansion-20260926/frozen-inputs/classification--部门归属与年度系列-冻结v1.json').read_text())['rows']
    groups={Path(r['original_file']).stem:r['analysis_group'] for r in metadata}
    cases={}
    weak=[]
    for r in m['records']:
        k=r['metrics']['kappa']['estimate']
        if r['group']=='ALL' or (k is not None and k>=.8):
            continue
        record_key='/'.join(str(r[k]) for k in ('frame','group','dimension','method','reference'))
        rows=[]
        d=r['dimension']
        for rid,coders in frames[r['frame']].items():
            inp=inputs[rid]['input']
            if groups[inp['original_file_stem']]!=r['group']:
                continue
            a,c=coders['A']['labels'][d],coders['C']['labels'][d]
            rule=rules[rid]['prediction']['labels'][d]
            machine_labels={method:rows[rid].get('prediction',rows[rid])['labels'][d] for method,rows in machines.items()}
            left=a if r['method']=='A_C' else machine_labels[r['method']]
            right=coders[r['reference']]['labels'][d]
            if binary(left) and binary(right):
                contribution={('A_C',1,1):'A1_C1',('A_C',1,0):'A1_C0',('A_C',0,1):'A0_C1',('A_C',0,0):'A0_C0'}.get((r['method'],left,right))
                contribution=contribution or {(1,1):'TP',(1,0):'FP',(0,1):'FN',(0,0):'TN'}[left,right]
            else:
                contribution='excluded_both_pending' if not binary(left) and not binary(right) else 'excluded_left_pending' if not binary(left) else 'excluded_right_pending'
            case_key=f'{r["frame"]}/{rid}/{d}'
            if case_key not in cases:
                cases[case_key]={'case_key':case_key,'id':rid,'original_id':inputs[rid]['original_id'],
                    'frame':r['frame'],'group':r['group'],'dimension':d,'dimension_name':NAMES[d],
                    'policy_entry':inp['original_file_stem'],'unit_text':inp['unit_text'],
                    'paragraph_context':inp.get('paragraph_context',[]),
                    'nearest_preceding_heading':inp.get('nearest_preceding_heading'),
                    'immediately_preceding_paragraph':inp.get('immediately_preceding_paragraph'),
                    'verified_object_scope_texts':[x['text'] for x in inp.get('verified_object_scope',[])],
                    'source_file':inp.get('unit_source') or inp['source'],'pages':inp.get('pages',[]),
                    'A':a,'C':c,'rule':rule,
                    'machine_labels':machine_labels,
                    'A_reason':coders['A'].get('dimension_reasons',{}).get(d),
                    'C_reason':coders['C'].get('dimension_reasons',{}).get(d),
                    'rule_evidence':[x for x in rules[rid]['prediction'].get('evidence',[]) if x.get('dimension')==d],
                    'rule_suppressions':[x for x in rules[rid]['prediction'].get('suppressions',[]) if x.get('dimension')==d or d in x.get('dimensions',[])],
                    'metric_contributions':[]}
            cases[case_key]['metric_contributions'].append({'record_key':record_key,'contribution':contribution})
            rows.append({'case_key':case_key,'id':rid,'contribution':contribution})
        weak.append({'record_key':record_key,**{key:r[key] for key in ('frame','group','dimension','method','reference','n','frame_n','excluded_n','source_clusters','left_positive_n','right_positive_n','cross_tab','confusion','metrics')},
                     'reason':'single_class_all_zero_kappa_undefined' if k is None else 'observed_kappa_below_0.8',
                     'all_unit_contributions':rows})
    positivity=[]
    for group in GROUPS:
        chosen=[rid for rid in frames['main1057'] if groups[inputs[rid]['input']['original_file_stem']]==group]
        for d in DIMS:
            methods={}
            count_methods = ['A', 'C', 'rule'] + (['LLM'] if binding['llm']['path'] else [])
            for coder in count_methods:
                values={rid:(rules[rid]['prediction']['labels'][d] if coder=='rule'
                             else machines[binding['llm']['method']][rid].get('prediction',machines[binding['llm']['method']][rid])['labels'][d] if coder=='LLM'
                             else frames['main1057'][rid][coder]['labels'][d]) for rid in chosen}
                count=Counter(values.values())
                positive_ids=[rid for rid,v in values.items() if v==1]
                methods[coder]={'positive':count[1],'negative':count[0],'pending':count['待定'],'frame_n':len(chosen),
                                'positive_source_clusters':len({inputs[rid]['input'].get('unit_source') or inputs[rid]['input']['source'] for rid in positive_ids}),
                                'positive_ids':positive_ids}
            positivity.append({'group':group,'dimension':d,'methods':methods,'min_positive_n':min(x['positive'] for x in methods.values())})
    packet=[]
    focus=[]
    for key,case in cases.items():
        blind_id='BDEPT-'+hashlib.sha256(key.encode()).hexdigest()[:12]
        case['blind_id']=blind_id
        # Only original language/context and the target dimension enter the packet.
        row={'blind_id':blind_id,'task_dimension':case['dimension_name'],
             'unit_text':case['unit_text'],'paragraph_context':case['paragraph_context'],
             'nearest_preceding_heading':case['nearest_preceding_heading'],
             'immediately_preceding_paragraph':case['immediately_preceding_paragraph'],
             'verified_object_scope_texts':case['verified_object_scope_texts']}
        packet.append(row)
        if any(x==1 for x in (case['A'],case['C'],*case['machine_labels'].values())):
            focus.append(row)
    random.Random(20261007).shuffle(packet)
    random.Random(20261007).shuffle(focus)
    result={'date':'2026-10-07','scope':list(GROUPS),'threshold_for_audit_only':.8,
            'labels_modified':False,'rule_code_modified':False,'independent_validation_claim':False,
            'interpretation':'The 0.8 threshold selects audit cells only. It is not a criterion for changing labels or passing validity.',
            'weak_comparison_count':len(weak),'unique_case_dimension_count':len(cases),
            'focus_case_dimension_count':len(focus),'weak_comparisons':weak,'cases':list(cases.values()),
            'main1057_class_counts':positivity,
            'notes':['All units of every weak department/dimension cell are listed, including TN and excluded pending units; NA cells are not evidence that every negative is substantively correct.',
                     'Focus blind packet contains cases with at least one positive current label. It is targeted error review, not a probability sample or independent accuracy validation.',
                     'Full blind packet and focus packet contain no labels, reasons, metric contributions, department labels, error type, scores, or original IDs. Mapping is retained only in this audit.',
                     'Source statements are unchanged. Parent paragraph and heading are context, not extra counted units.'],
            'latest_llm':m['latest_llm'],'method_bindings':binding}
    (OUT/'error_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for name,rows in [('blind_error_packet.jsonl',packet),('blind_error_packet_focus.jsonl',focus)]:
        (OUT/name).write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows))
    print(json.dumps({'weak_comparison_count':len(weak),'unique_case_dimension_count':len(cases),'focus_case_dimension_count':len(focus),
                      'main_class_minima':[{'group':x['group'],'dimension':x['dimension'],'min_positive_n':x['min_positive_n']} for x in positivity]},ensure_ascii=False))


if __name__=='__main__':
    main()
