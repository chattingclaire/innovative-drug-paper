#!/usr/bin/env python3
"""Execute only presealed finite controls, one call per fixed input."""
import copy
import hashlib
import importlib.util
import json
import sys
import traceback
from pathlib import Path

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent


def load(path):
    return json.loads(Path(path).read_bytes())


def bind(path):
    p=Path(path).resolve();raw=p.read_bytes()
    return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def write(name,value):
    with (OUT/name).open('x',encoding='utf8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')


assert not (OUT/'execution-results.json').exists(), 'finite controls already executed'
preseal=load(OUT/'pre-execution-seal.json')
for item in preseal['inputs']:
    assert bind(item['path'])==item,item['path']
verification=load(OUT/'sealed-input-verification.json')
for item in verification['files']:
    assert bind(item['path'])==item,item['path']
for name in ('evidence','source_packet','source_receipts','relations','dimensions'):
    path=OUT/'code-snapshot'/f'{name}.py'
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
adapter=sys.modules['source_packet'];relations=sys.modules['relations']
dimensions=sys.modules['dimensions'];evidence=sys.modules['evidence']
controls=[]
for suite,name in (('legacy20','legacy20-controls.json'),('new20','new20-fixed-before-execution.json'),
                   ('owner_closure3','owner-closure3-fixed-before-execution.json')):
    for case in load(OUT/name)['cases']:
        controls.append((suite,case))
assert len(controls)==43
results=[];quote_checks=[]
for suite,case in controls:
    row={'suite':suite,'name':case['name'],'expected':case['expected'],
         'manual_reason':case['manual_reason'],'manual_lines':case.get('manual_lines'),
         'historical_expected_unchanged':case.get('historical_expected_unchanged'),
         'synthetic_only':case.get('synthetic_only',True),
         'source_adapter_called':False,'relation_view_attempted':False,'judge_attempted':False,
         'evidence_validation_passed':False,'passed':False}
    try:
        if 'synthetic_input' in case:
            unit=copy.deepcopy(case['synthetic_input'])
        else:
            raw=copy.deepcopy(case.get('synthetic_bundle',case.get('bound_source_bundle')))
            if 'source_binding' in case:
                assert bind(case['source_binding']['path'])==case['source_binding']
            row['source_adapter_called']=True
            unit=adapter.semantic_unit(raw)
            assert 'id' not in unit and 'id' not in unit['source_bundle']['source_record']
        untouched=copy.deepcopy(unit)
        row['current_text']=unit['text']
        row['relation_view_attempted']=True
        view=relations.RelationView(unit)
        row['relation_traces']=view.traces()
        row['material_requests']=view.material_requests
        row['source_requests']=view.source_requests
        row['judge_attempted']=True
        decisions=dimensions.judge(view)
        row['decisions']=decisions
        row['observed_all5']={dim:decisions[dim]['value'] for dim in ('S','E','Ec','I','F')}
        row['observed']={dim:decisions[dim]['value'] for dim in case['expected']}
        row['mismatches']=[{'dimension':dim,'expected':value,'observed':decisions[dim]['value']}
                           for dim,value in case['expected'].items() if decisions[dim]['value']!=value]
        evidence.validate_decisions(unit,decisions)
        assert unit==untouched,'consumer modified supplied unit'
        row['evidence_validation_passed']=True
        contexts={c['context_id']:c for c in unit['contexts']}
        docs={x['sha256']:x['text'] for x in case.get('synthetic_documents',[])}
        for dim,decision in decisions.items():
            if decision['value']!=1:continue
            records=[decision]+decision['details'].get('additional_evidence',[])
            for ri,record in enumerate(records):
                for qi,q in enumerate(record['context_evidence']):
                    c=contexts[q['context_id']];a,b=q['start'],q['end']
                    assert c['text'][a:b]==q['text'] and c['source_ref']==q['source_ref']
                    check={'suite':suite,'name':case['name'],'dimension':dim,
                           'record_index':ri,'quote_index':qi,'quote':q['text'],
                           'context_id':q['context_id'],'context_range':[a,b],
                           'source_ref':q['source_ref'],'exact_supplied_context':True,
                           'supplied_source_ref_unchanged':True,
                           'real_policy_SHA_certification':False}
                    sha=q['source_ref']['sha256']
                    if sha in docs:
                        text=docs[sha]
                        assert hashlib.sha256(text.encode()).hexdigest()==sha
                        start=c['source_ref']['locator']['unicode_code_point_interval_half_open'][0]+a
                        end=c['source_ref']['locator']['unicode_code_point_interval_half_open'][0]+b
                        assert text[start:end]==q['text']
                        check.update({'synthetic_document_range':[start,end],
                                      'synthetic_document_exact_match':True})
                    quote_checks.append(check)
        row['passed']=not row['mismatches']
    except Exception as exc:
        row['error']={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
    results.append(row)

suite_summary={}
for suite in ('legacy20','new20','owner_closure3'):
    rows=[x for x in results if x['suite']==suite]
    suite_summary[suite]={'case_N':len(rows),'passed_N':sum(x['passed'] for x in rows),
                         'failed_N':sum(not x['passed'] for x in rows),
                         'mismatched_dimensions_N':sum(len(x.get('mismatches',[])) for x in rows),
                         'exceptions_N':sum('error' in x for x in rows),
                         'evidence_validation_passed_N':sum(x['evidence_validation_passed'] for x in rows),
                         'failed_names':[x['name'] for x in rows if not x['passed']]}
summary={'status':'independent_finite_execution_complete_not_formal_validation',
         'candidate_algorithm_sha256':preseal['algorithm_sha256'],
         'preseal_binding':bind(OUT/'pre-execution-seal.json'),
         'actual_imports':{name:bind(sys.modules[name].__file__) for name in
                           ('source_packet','source_receipts','evidence','relations','dimensions')},
         'case_N':len(results),'candidate_judge_attempts_N':sum(x['judge_attempted'] for x in results),
         'unique_presealed_inputs_once_each':True,'suite_summary':suite_summary,
         'quote_checks_N':len(quote_checks),
         'full77_or800_replay_N':0,'new_neutral_projection_used':False,
         'main_LLM_partial_or_owner800_labels_read':False,'human_reference_used_or_created':False,
         'expected_changed_after_execution':False,'owner_candidate_mutated':False}
write('execution-results.json',{'summary':summary,'cases':results})
with (OUT/'execution-results.jsonl').open('x',encoding='utf8') as stream:
    for row in results:stream.write(json.dumps(row,ensure_ascii=False)+'\n')
write('execution-summary.json',summary)
write('literal-quote-validation.json',quote_checks)
print(json.dumps(summary,ensure_ascii=False,indent=2))
