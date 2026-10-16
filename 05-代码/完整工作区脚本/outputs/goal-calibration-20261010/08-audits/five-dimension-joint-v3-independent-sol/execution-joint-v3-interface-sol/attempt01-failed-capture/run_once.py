#!/usr/bin/env python3
"""Run original hidden12 once against the already sealed final joint code.

The candidate receives only a source-only packet, never expected values,
unavailable synthetic originals or ROOT/owner regressions and answers.
"""
import copy
import datetime
import hashlib
import importlib
import json
import sys
import traceback
from pathlib import Path
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent
PREP=OUT.parent
ROOT=PREP.parents[1]
CANDIDATE=ROOT/'06-coding/rule-five-dimension-joint-root/versions/joint-v3-interface-sol'
PREP_SHA='c2f2033647918ae48c2dbea6bd960c1830b9b4588a5f5272787487eae260cec9'
CANDIDATE_SHA='909f4aaa1cbdd1f2222284f56bdffae458438b61b90a828a90ae0c1918916f93'
EXPECTED_MODULES={
    'source_packet':'637332307d059e7f03af94441aaf4a012843c0541b549a2820b386b370c80611',
    'source_receipts':'e9ac5bf9a810f1a482f06d76a8706e6bd81427d7f19c45741ee680dce2b20209',
    'evidence':'5ce0fc8c39862edbcab837c0b1fdc7f5c605758f34fbf0ab34487a0b4531cdb3',
    'relations':'24e6892ab12720253120f91343e85b868dccb56dd3204ab43a032f3cef65063f',
    'dimensions':'7e2ec8ec5b1a17e80551919f07f8c82c0c71089baf731fe2fee6a4ad3aa59ace',
}
DIMS=('S','E','Ec','I','F')


def bind(path):
    p=Path(path).resolve();raw=p.read_bytes()
    return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def load(path):return json.loads(Path(path).read_bytes())


def write(name,value):
    with (OUT/name).open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')


def cj(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)


assert not (OUT/'execution-results.json').exists()
assert bind(PREP/'preparation-seal.json')['sha256']==PREP_SHA
assert bind(CANDIDATE/'pre-execution-seal.json')['sha256']==CANDIDATE_SHA
preseal=load(PREP/'preparation-seal.json')
cseal=load(CANDIDATE/'pre-execution-seal.json')
for b in preseal['output_members']:assert bind(b['path'])==b
for b in cseal['modules'] + cseal['common_frozen_input_bindings'] + [cseal['manual'], cseal['algorithm_bindings']]:assert bind(b['path'])==b
assert cseal['algorithm_bindings']['sha256']=='805134f5861a7af988010e6bffffef2de6addea969b19c178b3bf92932dd3f32'
assert preseal['prepared_at_utc'] < cseal['at_utc']
# Exposed parent75/235 and owner-control contents are deliberately not read or used.
algorithm=load(CANDIDATE/'algorithm-bindings.json')
assert bind(algorithm['manual']['path'])==algorithm['manual']==preseal['manual_binding']
plan=load(PREP/'controls12-fixed-before-execution.json')
assert plan['case_N']==len(plan['cases'])==12
assert plan['candidate_algorithm_binding'] is None
assert preseal['candidate_judge_attempts_N']==0
snapshot=OUT/'code-snapshot';snapshot.mkdir(exist_ok=False)
bindings=[]
for module,sha in EXPECTED_MODULES.items():
    owner=CANDIDATE/(module+'.py');assert bind(owner)['sha256']==sha
    target=snapshot/(module+'.py')
    with target.open('xb') as stream:stream.write(owner.read_bytes())
    assert bind(target)['sha256']==sha
    bindings.append({'candidate':bind(owner),'executed_snapshot':bind(target)})
write('execution-input-and-code-seal.json',{
    'status':'original_hidden12_and_final_joint_code_verified_before_first_judge',
    'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'original_preparation_seal':bind(PREP/'preparation-seal.json'),
    'original_controls':bind(PREP/'controls12-fixed-before-execution.json'),
    'candidate_pre_execution_seal':bind(CANDIDATE/'pre-execution-seal.json'),
    'candidate_algorithm_binding':bind(CANDIDATE/'algorithm-bindings.json'),
    'all_five_active_modules_and_common_freeze_bindings_verified':True,
    'exposed_parent_control_answer_files_not_read':True,
    'original14_preparation_members_unchanged':True,
    'manual':algorithm['manual'],'snapshots':bindings,'runner':bind(__file__),
    'ROOT_parent75_or235_expected_or_result_tables_read':False,
    'candidate_judge_attempts_before_this_seal_N':0,
})
with (OUT/'executed-source-only-inputs.jsonl').open('x',encoding='utf-8') as stream:
    for case in plan['cases']:
        stream.write(json.dumps({'name':case['name'],'source_only_bundle':case['synthetic_bundle']},ensure_ascii=False,allow_nan=False)+'\n')
sys.path.insert(0,str(snapshot))
source_packet=importlib.import_module('source_packet')
evidence=importlib.import_module('evidence')
relations=importlib.import_module('relations')
dimensions=importlib.import_module('dimensions')
for name in EXPECTED_MODULES:
    if name in sys.modules:assert Path(sys.modules[name].__file__).resolve()==snapshot/(name+'.py')

# Observation wrappers call original functions exactly once and return unchanged
# values. They record units and accepted positive additions, not synthetic
# relation/receipt injections or a repaired classifier.
units_observed=[];positive_events=[]
original_units=dimensions._units
original_add=dimensions.Accumulator.add


def observe_units(view):
    actual=original_units(view)
    for unit in actual:
        allowed=set(unit.details.get('affected_dimensions',DIMS))
        if unit.details.get('only_IF_consumers'):allowed &= {'I','F'}
        units_observed.append({'text':unit.text,'start':unit.a,'end':unit.b,
                               'kind':unit.kind,'inherited':unit.inherited,
                               'contexts':copy.deepcopy(unit.contexts),
                               'details':copy.deepcopy(unit.details),
                               'allowed_consumers_from_contract':[d for d in DIMS if d in allowed]})
    return actual


def observe_add(acc,dim,unit,path,reason,obj,details=None):
    before=len(acc.positive[dim])
    result=original_add(acc,dim,unit,path,reason,obj,details)
    if len(acc.positive[dim])>before:
        allowed=set(unit.details.get('affected_dimensions',DIMS))
        if unit.details.get('only_IF_consumers'):allowed &= {'I','F'}
        positive_events.append({'dimension':dim,'basis_path':path,'unit_kind':unit.kind,
            'unit_text':unit.text,'unit_inherited':unit.inherited,
            'unit_details':copy.deepcopy(unit.details),
            'unit_contexts':copy.deepcopy(unit.contexts),
            'accepted_positive':copy.deepcopy(acc.positive[dim][-1]),
            'allowed_consumers_from_contract':[d for d in DIMS if d in allowed],
            'consumer_route_matched':dim in allowed})
    return result


dimensions._units=observe_units
dimensions.Accumulator.add=observe_add


def recursively_citations(value):
    if isinstance(value,dict):
        if {'context_id','start','end','text','source_ref','usage'} <= set(value):yield value
        for child in value.values():yield from recursively_citations(child)
    elif isinstance(value,list):
        for child in value:yield from recursively_citations(child)


quote_checks=[];results=[];attempts=0
for case in plan['cases']:
    units_observed.clear();positive_events.clear()
    packet=copy.deepcopy(case['synthetic_bundle']);unit=None;view=None;decision=None
    actual_error=None;evidence_valid=False
    try:
        # The only input made visible to the algorithm is the source-only bundle.
        unit=source_packet.semantic_unit(packet)
        assert 'id' not in unit and 'expected_values_fixed_before_execution' not in unit
        view=relations.RelationView(unit)
        attempts+=1;decision=dimensions.judge(view)
        evidence.validate_decisions(unit,decision);evidence_valid=True
    except Exception as error:
        actual_error={'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()}
    traces=view.traces() if view is not None else []
    requests=copy.deepcopy(getattr(view,'source_requests',[])) if view is not None else []
    material=copy.deepcopy(getattr(view,'material_requests',[])) if view is not None else []
    actual_values={d:decision[d]['value'] for d in DIMS} if decision is not None else None
    mismatched=[d for d in DIMS if actual_values is None or actual_values[d]!=case['expected_values_fixed_before_execution'][d]]
    local_quotes=[];quote_error=None
    try:
        if unit is not None:
            contexts={c['context_id']:c for c in unit['contexts']}
            assert len(contexts)==len(unit['contexts'])
            docs={d['binding']['sha256']:d for d in case['synthetic_documents']}
            source_docs=docs[packet['source_record']['source_ref']['sha256']]
            row=packet['source_record'];rlo,rhi=row['source_ref']['locator']['unicode_code_point_interval_half_open']
            assert source_docs['text'][rlo:rhi]==row['text']
            seen=set()
            for quote in recursively_citations([decision,traces,requests,material,positive_events]):
                key=cj(quote)
                if key in seen:continue
                seen.add(key)
                ctx=contexts[quote['context_id']]
                assert ctx['text'][quote['start']:quote['end']]==quote['text']
                assert ctx['source_ref']==quote['source_ref']
                doc=docs[quote['source_ref']['sha256']]
                loc=ctx['source_ref']['locator'];ca,cb=loc['unicode_code_point_interval_half_open']
                ba,bb=loc['utf8_byte_interval_half_open']
                assert doc['text'][ca:cb]==ctx['text']
                assert doc['text'].encode('utf-8')[ba:bb].decode('utf-8')==ctx['text']
                a=ca+quote['start'];b=ca+quote['end']
                assert doc['text'][a:b]==quote['text']
                byte_a=ba+len(ctx['text'][:quote['start']].encode('utf-8'))
                byte_b=ba+len(ctx['text'][:quote['end']].encode('utf-8'))
                assert doc['text'].encode('utf-8')[byte_a:byte_b].decode('utf-8')==quote['text']
                record={'case':case['name'],'context_id':quote['context_id'],
                    'context_kind':ctx['kind'],'context_structure':copy.deepcopy(ctx['structure']),
                    'context_relative_unicode_span':[quote['start'],quote['end']],
                    'synthetic_document_unicode_span':[a,b],
                    'synthetic_document_utf8_byte_span':[byte_a,byte_b],
                    'synthetic_document_line_interval':[doc['text'][:a].count('\n')+1,doc['text'][:b].count('\n')+1],
                    'quote':quote['text'],'usage':quote['usage'],'source_ref':quote['source_ref'],
                    'synthetic_source_binding':doc['binding'],'literal_binding_valid':True,
                    'this_is_not_a_semantic_applicability_validation':True}
                local_quotes.append(record)
    except Exception as error:
        quote_error={'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()}
    quote_checks.extend(local_quotes)
    case_result={'name':case['name'],'pair_group':case['pair_group'],
        'expected_values_fixed_before_execution':case['expected_values_fixed_before_execution'],
        'actual_values':actual_values,'mismatched_dimensions':mismatched,
        'values_matched':not mismatched and actual_error is None,
        'full_five_decisions_first_execution':decision,'execution_error':actual_error,
        'evidence_validator_passed':evidence_valid,
        'independent_literal_quote_N':len(local_quotes),'independent_quote_error':quote_error,
        'source_relation_traces':traces,'source_requests':requests,'material_requests':material,
        'resolved_receipts':[r for r in requests if r.get('dependency_status')=='resolved'],
        'stopped_requests':[r for r in requests if r.get('dependency_status','stopped')=='stopped'],
        'source_view_events':copy.deepcopy(getattr(view,'source_view_events',[])) if view is not None else [],
        'source_scope_review':copy.deepcopy(getattr(view,'source_scope_review',None)) if view is not None else None,
        'observed_units':copy.deepcopy(units_observed),'accepted_positive_events':copy.deepcopy(positive_events),
        'consumer_route_violations':[e for e in positive_events if not e['consumer_route_matched']],
        'only_IF_actual_observed_units_N':sum(bool(u['details'].get('only_IF_consumers')) for u in units_observed),
        'complete_synthetic_original_semantically_review_pending_separate_from_literal_check':True,
        'expected_or_candidate_changed':False,'formal_human_validation':False}
    results.append(case_result)
assert attempts==12 and len(results)==12
write('execution-results.json',{'status':'first12_independent_joint_candidate_execution_retained',
    'candidate_pre_execution_seal':bind(CANDIDATE/'pre-execution-seal.json'),
    'original_preparation_seal':bind(PREP/'preparation-seal.json'),
    'candidate_judge_attempts_N':attempts,'cases':results})
with (OUT/'execution-results.jsonl').open('x',encoding='utf-8') as stream:
    for result in results:stream.write(json.dumps(result,ensure_ascii=False,allow_nan=False)+'\n')
write('literal-quote-first-execution-validation.json',{
    'quote_N':len(quote_checks),'quotes':quote_checks,
    'case_quote_errors':[{'name':r['name'],'error':r['independent_quote_error']} for r in results if r['independent_quote_error']],
    'available_or_parsed_does_not_mean_applicable':True,
})
summary={'case_N':12,'candidate_judge_attempts_N':attempts,
    'matched_N':sum(r['values_matched'] for r in results),
    'failed_N':sum(not r['values_matched'] for r in results),
    'mismatched_dimensions_N':sum(len(r['mismatched_dimensions']) for r in results),
    'execution_exceptions_N':sum(r['execution_error'] is not None for r in results),
    'evidence_validator_passed_N':sum(r['evidence_validator_passed'] for r in results),
    'independent_quote_errors_N':sum(r['independent_quote_error'] is not None for r in results),
    'independent_literal_quote_N':len(quote_checks),
    'accepted_positive_consumer_route_violations_N':sum(len(r['consumer_route_violations']) for r in results),
    'only_IF_observed_units_N':sum(r['only_IF_actual_observed_units_N'] for r in results),
    'typed_subset_observed_units_N':sum('affected_dimensions' in u['details'] and set(u['details']['affected_dimensions'])!=set(DIMS) for r in results for u in r['observed_units']),
    'only_IF_accepted_positive_events_N':sum(bool(e['unit_details'].get('only_IF_consumers')) for r in results for e in r['accepted_positive_events']),
    'typed_subset_accepted_positive_events_N':sum('affected_dimensions' in e['unit_details'] and set(e['unit_details']['affected_dimensions'])!=set(DIMS) for r in results for e in r['accepted_positive_events']),
    'failed_case_names':[r['name'] for r in results if not r['values_matched']],
    'parent75_or235_answers_read':False,'full77_800_4481_execution_N':0,
    'original_hidden12_expectations_unchanged':True,'candidate_source_unchanged':True,
    'actual_human_validation_N':0}
write('execution-summary.json',summary)
print(json.dumps(summary,ensure_ascii=False))
