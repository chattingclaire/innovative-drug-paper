#!/usr/bin/env python3
"""Execute presealed administration/refusal controls once; never statistics."""
import copy
import datetime
import hashlib
import importlib.util
import json
import sys
import traceback
from pathlib import Path
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
OWNER=ROOT/'07-statistics/human200-machine-reference-handoff-sol'
PRE_SHA='f78ca1aa4855c496d7294dc3edc297829fd9b21f53744a4148675bc1fd9f3e50'


def bind(path):
    p=Path(path).resolve();raw=p.read_bytes()
    return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def load(path):return json.loads(Path(path).read_bytes())


def write(name,value):
    with (OUT/name).open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')


pre=load(OUT/'pre-execution-seal.json')
assert bind(OUT/'pre-execution-seal.json')['sha256']==PRE_SHA
for b in pre['output_members']:assert bind(b['path'])==b
plan=load(OUT/'controls12-fixed-before-execution.json')
assert bind(OWNER/'handoff.py')==plan['code_binding']
assert bind(OWNER/'output-seal.json')==plan['owner_seal_binding']
assert not (OUT/'execution-results.json').exists()
write('execution-code-seal.json',{'status':'one_finite_execution_runner_bound_before_import',
    'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'preparation_seal':bind(OUT/'pre-execution-seal.json'),
    'runner':bind(__file__),'candidate':plan['code_binding'],'case_N':12})
spec=importlib.util.spec_from_file_location('_independent_sealed_historical200_handoff',OWNER/'handoff.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
c=load(OWNER/'bindings.json')
manifest=load(c['frozen_inputs']['LLM_manifest']['path'])
approved=load(c['frozen_inputs']['LLM_frame_ids']['path'])['approved_record_ids']
guard_events=[];administrative_reads=[];active_case=None


def forbidden(name):
    def stop(*args,**kwargs):
        event={'case':active_case,'attempted_function':name,'blocked_before_any_label_or_metric_read':True}
        guard_events.append(event)
        raise AssertionError('Forbidden real-data/statistical path attempted: '+name)
    return stop


# The tested entry gates remain original. Guards do not make an input valid,
# choose labels, repair a test or fake a receipt; they prevent unneeded I/O if
# an expected early refusal fails.
for name in ('human_initial','initial_projection','reference_projection','rule_projection',
             'llm_projection','year_join','module','jsonlines'):
    setattr(h,name,forbidden(name))
original_load=h.load
protected_rule=Path(c['frozen_inputs']['rule_predictions']['path']).resolve()


def tracked_admin_load(path):
    p=Path(path).resolve()
    if p==protected_rule or p.name=='first.json' or p.name.startswith('derived-'):
        return forbidden('label_file_load:'+str(p))()
    administrative_reads.append({'case':active_case,'binding':bind(p)})
    return original_load(p)


h.load=tracked_admin_load
results=[]
for case in plan['cases']:
    active_case=case['name'];assert bind(case['input_binding']['path'])==case['input_binding']
    data=load(case['input_binding']['path']);fn=case['function'];actual={}
    before=len(guard_events)
    try:
        if fn=='frozen_frame':
            out=h.frozen_frame(data)
            actual={'outcome':'accept','record_N':len(out),'approved_order_exact':out==approved,
                    'unapproved_ID_N':len(set(out)-set(approved)),
                    'canonical_order_sha256':h.canonical(out)}
        elif fn=='build':
            out=h.build(OUT/'NONEXISTENT-NO-ACTUAL-RECEPTION',data['review'],c,data['stage'],data['annual'])
            actual={'outcome':'accept','unexpected_return_type':type(out).__name__}
        elif fn=='terminal_inventory_gate':
            out=h.terminal_inventory_gate(data,{},c)
            actual={'outcome':'accept','unexpected_terminal_entry_N':len(out[1])}
        elif fn=='reference_output':
            out=h.reference_output(data['row'],data['identity'],data['codes'])
            actual={'outcome':'accept','unexpected_return':out}
        else:
            raise AssertionError('Unknown presealed function')
    except Exception as error:
        actual={'outcome':'reject','exception_class':type(error).__name__,
                'message':str(error),'traceback':traceback.format_exc()}
    target=case['expected_before_execution']
    matched=all(actual.get(k)==v for k,v in target.items() if k!='message_contains')
    if 'message_contains' in target:
        matched=matched and target['message_contains'] in actual.get('message','')
    results.append({'name':case['name'],'function':fn,'input_binding':case['input_binding'],
                    'expected_before_execution_unchanged':target,'actual':actual,'matched':matched,
                    'original_scope':case['scope'],'guard_events':guard_events[before:],
                    'actual_statistics_run':False,'actual_human_reference_received':False})
assert len(results)==12
write('execution-results.json',{'status':'finite_independent_handoff_gate_execution_not_statistics',
    'case_N':12,'candidate':plan['code_binding'],'preparation_seal':bind(OUT/'pre-execution-seal.json'),
    'cases':results})
with (OUT/'execution-results.jsonl').open('x',encoding='utf-8') as stream:
    for r in results:stream.write(json.dumps(r,ensure_ascii=False,allow_nan=False)+'\n')
write('execution-scope-and-IO-receipt.json',{
    'attempted_control_calls_N':12,'each_presealed_case_executed_once':True,
    'forbidden_real_data_or_statistical_path_attempts':guard_events,
    'actual_administrative_JSON_reads_in_candidate':administrative_reads,
    'guards_not_called':not guard_events,
    'original_entry_or_classification_source_not_modified':True,
    'actual_human_label_reception_N':0,'actual_reference_N':0,
    'actual_machine_label_reception_N':0,'statistical_engine_imports_N':0,
    'year_join_calls_N':0,'actual_year_metrics_N':0,'actual_statistics_N':0,
    'only_synthetic_helper_cell_value_created':'one integer0 in a refusal fixture, no200 reference or prediction',
})
summary={'case_N':12,'matched_N':sum(r['matched'] for r in results),
    'mismatched_N':sum(not r['matched'] for r in results),
    'failed_control_names':[r['name'] for r in results if not r['matched']],
    'guard_calls_N':len(guard_events),'actual_human_reference_statistics_N':0,
    'expected_values_changed_after_execution':False}
write('execution-summary.json',summary)
print(json.dumps(summary,ensure_ascii=False))
