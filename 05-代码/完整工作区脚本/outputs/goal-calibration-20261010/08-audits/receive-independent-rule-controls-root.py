"""ROOT receipt for fixed independent developer controls; no classification rerun."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);args=parser.parse_args()
SOURCE=ROOT/'08-audits'/args.source
OUT=ROOT/'08-audits/independent-rule-control-reception-root'/args.source

def bind(p):
    p=Path(p).resolve();raw=p.read_bytes()
    return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

def exact(b):assert bind(b['path'])=={k:b[k]for k in ('path','bytes','sha256')},b['path']

def load(p):return json.loads(Path(p).read_text())

def save(p,v):
    with Path(p).open('x',encoding='utf8')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')

seal=load(SOURCE/'output-seal.json');members=seal['output_members']
for member in members:exact(member)
controls=load(SOURCE/'controls-fixed-before-execution.json');execution=load(SOURCE/'execution-results.json')
cases=controls['cases'];results=execution['cases']
assert len(cases)==len(results)==20
assert len({c['name']for c in cases})==20
counts={'cases':20,'passed':0,'failed':0,'mismatched_dimensions':0,'evidence_validation_passed':0}
recomputed=[]
for control,result in zip(cases,results):
    assert control['name']==result['name']
    assert control['expected']==result['expected']
    assert control['manual_reason']==result['manual_reason']
    assert control['synthetic_input']['text']==result['current_text']
    observed={dim:result['decisions'][dim]['value']for dim in control['expected']}
    assert observed==result['observed']
    difference=[{'dimension':dim,'expected':value,'observed':observed[dim]}for dim,value in control['expected'].items()if value!=observed[dim]]
    assert difference==result['mismatches']
    passed=not difference;assert result['passed']==passed
    counts['passed']+=passed;counts['failed']+=not passed;counts['mismatched_dimensions']+=len(difference)
    counts['evidence_validation_passed']+=bool(result['evidence_validation_passed'])
    recomputed.append({'name':control['name'],'expected':control['expected'],'observed':observed,'mismatches':difference,'passed':passed,'synthetic_control_not_real_policy_record':True,'new_gold_standard_created':False})
assert counts['passed']==13 and counts['failed']==7 and counts['evidence_validation_passed']==20
if args.source.startswith('SE-'):
    inputs=load(SOURCE/'audited-input-bindings.json')['inputs']
    for b in inputs:exact(b)
    basis=load(SOURCE/'manual-basis-quotes.json');exact(basis['manual_binding'])
    manual=Path(basis['manual_binding']['path']).read_text()
    for q in basis['quotes']:
        assert manual[q['start']:q['end']]==q['quote']
        assert manual[:q['start']].count('\n')+1==q['line']
    quote_N=len(basis['quotes']);authority_N=0
    expected_mismatches=8
else:
    summary=load(SOURCE/'execution-summary.json')
    manifest=load(summary['algorithm_bindings']['path']);exact(summary['algorithm_bindings'])
    inputs=[]
    def collect(v):
        if isinstance(v,dict):
            if all(k in v for k in ('path','bytes','sha256')):inputs.append({k:v[k]for k in('path','bytes','sha256')})
            for child in v.values():collect(child)
        elif isinstance(v,list):
            for child in v:collect(child)
    collect(manifest)
    for b in inputs:exact(b)
    basis=load(SOURCE/'authority-and-manual-basis.json');exact(basis['manual'])
    manual=Path(basis['manual']['path']).read_text()
    for q in basis['manual_quotes']:
        assert manual[q['start']:q['end']]==q['quote']
        assert manual[:q['start']].count('\n')+1==q['line']
    quote_N=len(basis['manual_quotes']);authority_N=0
    for q in basis['authority_quotes']:
        exact(q['source']);raw=Path(q['source']['path']).read_bytes();text=raw.decode('utf8')
        a,b=q['unicode_code_point_interval_half_open'];ba,bb=q['utf8_byte_interval_half_open']
        assert text[a:b]==q['current_continuous_quote'] and raw[ba:bb].decode('utf8')==q['current_continuous_quote']
        authority_N+=1
    expected_mismatches=10
assert counts['mismatched_dimensions']==expected_mismatches
OUT.mkdir(parents=True,exist_ok=False)
save(OUT/'actual-reception.json',{'status':'ROOT_received_fixed_independent_development_controls','at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_audit_seal':bind(SOURCE/'output-seal.json'),'sealed_output_member_N':len(members),'actual_input_binding_checks':inputs,'counts_recomputed_from_all20':counts,'exact_manual_quote_N':quote_N,'original_basis_char_and_UTF8_quote_checked_N':authority_N,'fixed_expectations_equal_actual_execution_record':True,'raw_values_including_NULL_preserved':True,'classification_or_whole_cohort_repeated_by_ROOT':False,'ROOT_read_current20_and_targeted_full_IF_contexts':True,'ROOT_semantically_read_all_original_basis_documents':False,'formal_accuracy_or_human_reference_created':False,'remaining_static_risks_are_not_executed_failures':True,'specific_IF_foreign_single_unlisted_boundary':'fixed expected 0 and output NULL retained; negative attribution to need allocation requires interpretation, not a confirmed positive-label error'if expected_mismatches==10 else None,'recomputed_cases':recomputed})
save(OUT/'output-seal.json',{'output_members':[bind(OUT/'actual-reception.json')],'receiver':bind(__file__),'self_excluded':True})
print(json.dumps({'source':str(SOURCE),'destination':str(OUT),'counts':counts,'manual_quotes':quote_N,'authority_quotes':authority_N},ensure_ascii=False))
