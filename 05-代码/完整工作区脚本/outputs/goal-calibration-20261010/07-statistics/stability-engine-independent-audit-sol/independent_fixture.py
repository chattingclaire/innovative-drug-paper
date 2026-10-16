#!/usr/bin/env python3
"""Invented eleven-row audit fixture; no imports from the candidate implementation."""
import copy
import hashlib
import json
from pathlib import Path

DIMS = ['S', 'E', 'Ec', 'I', 'F']
RUNS = ['P', 'R1', 'R2', 'R3', 'W', 'H']
PAIRS = [['R1','R2'], ['R1','R3'], ['R2','R3'], ['W','R1'], ['H','R1']]
VERSION = 'prospective-stability-engine-sol-v1'
CHECKS = ['parseable','id_match','five_dimensions','response_schema','source_binding',
          'context_evidence','contiguous_quote','assets_reference']

def encoded(obj, canonical=False):
    return (json.dumps(obj, ensure_ascii=False, sort_keys=canonical,
                       separators=(',',':') if canonical else None,
                       indent=None if canonical else 2, allow_nan=False)
            + ('' if canonical else '\n')).encode('utf-8')

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def objsha(obj):
    return sha(encoded(obj, True))

def write_ref(base, path, data):
    target = Path(base) / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return {'path':path, 'sha256':sha(data)}

def response(i, values):
    ns = [d for d, v in zip(DIMS, values) if v is None]
    return {'assignedID':i, 'labels':dict(zip(DIMS, values)),
            'reasons':dict.fromkeys(DIMS, 'Independent invented arithmetic audit; no policy meaning.'),
            'null_reasons':dict.fromkeys(ns, 'Invented semantic pending state'),
            'material_requests':dict.fromkeys(ns, 'Invented missing material request'),
            'evidence':{d:[] for d in DIMS}}

def make_request(reg, prompt, manual, source, run):
    # Independent contract assembly, not the candidate's request_bytes function.
    text = json.dumps(source, ensure_ascii=False, indent=2) if run == 'W' else json.dumps(source, ensure_ascii=False, separators=(',',':'))
    heading = '判读说明\n' if run == 'H' else '判读要求\n'
    payload = {'settings':copy.deepcopy(reg['common_configuration']['request_settings']),
               'messages':[{'role':'system', 'content':prompt['system_prefix']+manual.decode('utf-8')+prompt['system_suffix']},
                           {'role':'user', 'content':heading+text+prompt['user_suffix']}]}
    return encoded(payload, True)

def seal_inputs(base, reg, led):
    reg.pop('registry_content_sha256', None)
    reg['registry_content_sha256'] = objsha(reg)
    raw = encoded(reg)
    (base/'registry.json').write_bytes(raw)
    led['registry_file_sha256'] = sha(raw)
    (base/'ledger.json').write_bytes(encoded(led))

def build(base, mode='eleven', context='record'):
    base = Path(base)
    if base.exists() and any(base.iterdir()):
        raise ValueError('Audit fixtures must be written to an empty directory')
    base.mkdir(parents=True, exist_ok=True)
    ids = [f'AUDIT-{j:03d}' for j in range(1,12)]
    weights = ['1/2','2','3','5','7','11','13','17','19','23','29']
    prompt = {'system_prefix':'Invented audit instructions\n', 'system_suffix':'\n',
              'user_prefix':'判读要求\n', 'user_suffix':'\nReturn the invented fixture structure.',
              'payload_template':{'settings':'{{REQUEST_SETTINGS}}', 'messages':[
                  {'role':'system','content':'{{SYSTEM_CONTENT}}'}, {'role':'user','content':'{{USER_CONTENT}}'}]}}
    manual = b'Independent invented source-only controls. Not a real coding manual.\n'
    files = {'manual':manual, 'prompt':encoded(prompt), 'output_schema':b'Invented fixed six-field response contract.\n',
             'adapter':b'Audit fixture constructor; no real source adapter.\n',
             'technical_validator':b'Constructed assertions only; no production quote validation.\n',
             'protocol':b'Finite independent statistical audit; no actual provider calls.\n'}
    artifacts = {k:{'version':'independent-toy-v1', 'artifact':write_ref(base, f'artifacts/{k}.txt',v)} for k,v in files.items()}
    records, packets = [], {}
    for i,w in zip(ids,weights):
        packet = {'assignedID':i, 'source_text':'Invented\ttext  with spaces\nNo real policy.',
                  'contexts':[{'CTXID':f'CTX-{i}', 'text':'Invented context only.'}]}
        packets[i] = packet
        ctx = [{'CTXID':f'CTX-{i}','source_pointer':'contexts/0'}]
        pending = i == ids[8] and mode == 'eleven'
        records.append({'assignedID':i, 'weight':w, 'inclusion_probability':None,
                        'material_state':'pending' if pending else 'complete',
                        'material_pending_reason':'Invented overlapping pending status' if pending else None,
                        'material':{'version':'independent-source-v1',
                                    'source_packet':write_ref(base,f'materials/{i}.json',encoded(packet)),
                                    'source_semantic_sha256':objsha(packet), 'ctx_binding':ctx,'ctx_binding_sha256':objsha(ctx)}})
    sample = {'selection_mode':'non_probability','weight_kind':'preassigned_analytic',
              'target_domain':'eleven invented audit units only','selection_rule':'all invented rows fixed by independent auditor',
              'scope_limit':'finite constructed audit; no real sample or population claim',
              'frame_seal_sha256':None, 'all_target_units_positive_pi_declared':False,
              'assigned_records':records,'ordered_assignedIDs':ids,
              'batches':[{'batch_id':'AUDIT-B1','members':ids[:6]}, {'batch_id':'AUDIT-B2','members':ids[6:]}]}
    reg = {'contract_version':VERSION,'data_mode':'synthetic_control','dimensions':DIMS,
           'registration':{'registry_id':'independent-eleven-'+mode+'-'+context,'status':'frozen_before_response_read',
                           'frozen_at':'2026-10-09T00:00:00+00:00','verification':'declaration_not_independently_verified'},
           'sample':sample,'common_artifacts':artifacts,
           'common_configuration':{'intended_model':'construct-only; never dispatched','intended_reasoning_effort':'ultra',
                                   'provider_requested':'none','request_settings':{'audit_setting':1},
                                   'provider_session_state':'unknown','actual_model_identity_status':'not_proven_by_requested_identity_or_hash'},
           'context_unit':context,'context_independence_declaration':{'declared_independent':True,
                            'verification':'not_independently_verified','basis':'Invented planned context identifiers; no provider execution'},
           'allow_pending_material_for_valid_response':True,
           'retry_policy':{'max_actual_attempts':3,'selection':'first_technically_valid_complete_response',
                           'semantic_null_stops_retry':True,'same_exact_request_only':True},
           'comparison_plan':{'pairs':PAIRS,'three_way':['R1','R2','R3'],'perturbation_baseline':'R1'},
           'stability_pass_threshold':None,'confidence_interval_gate':None,'conditions':{}}
    for run in RUNS:
        role = 'production' if run == 'P' else 'diagnostic_whitespace' if run == 'W' else 'diagnostic_heading' if run == 'H' else 'diagnostic_main'
        change = 'source_json_compact_to_indent2' if run == 'W' else 'user_first_line_synonym' if run == 'H' else 'none'
        units = ids if context == 'record' else ['AUDIT-B1','AUDIT-B2']
        reg['conditions'][run] = {'run_id':run,'role':role,'allowed_change':change,
                'common_configuration_sha256':objsha(reg['common_configuration']), 'common_artifacts_sha256':objsha(artifacts),
                'sample_plan_sha256':objsha(sample),'context_unit':context,
                'planned_contexts':{u:f'INDEPENDENT-{run}-{u}' for u in units},'requests':{}}
        for rec in records:
            i=rec['assignedID']; m=rec['material']
            reg['conditions'][run]['requests'][i] = {'exact_request':write_ref(base,f'requests/{run}/{i}.json',make_request(reg,prompt,manual,packets[i],run)),
                        'source_semantic_sha256':m['source_semantic_sha256'],'ctx_binding_sha256':m['ctx_binding_sha256']}
    z=[0]*5
    r1=[z,[0,1,0,1,0],[1,0,1,0,0],[1]*5,[None,1,0,0,0],[1,0,1,0,0],
        ['bad'], 'not_called',[0,None,0,0,0],['transport','transport'],'material_blocked']
    r2=[z,[1,1,0,1,0],[0,0,1,0,0],[1,0,0,0,0],[1,0,0,0,0],[0,0,1,None,0],
        [0,0,0,1,0],'not_called',[0,None,0,0,0],'creation_empty','not_called']
    r3=[z,[1,0,0,1,0],[0,1,1,0,1],[1,1,0,0,0],[0,1,0,0,0],[1,0,0,1,0],
        [0,0,0,0,1],'not_called',[0,None,0,0,0],'precheck_blocked',['bad','bad','bad']]
    production=[z,[1,None,0,0,0],['bad',[1,0,0,0,0]],['transport']*3]+[z]*7
    values={'P':production,'R1':r1,'R2':r2,'R3':r3,'W':copy.deepcopy(r2),'H':copy.deepcopy(r2)}
    if mode in ('zero','one'):
        values={r:[[0 if mode == 'zero' else 1]*5 for i in ids] for r in RUNS}
    elif mode == 'no-common':
        values={r:['not_called']*11 for r in RUNS}
    elif mode == 'missing-R3':
        values['R3']=['not_called']*11
    led={'contract_version':VERSION,'data_mode':'synthetic_control','registry_file_sha256':None,
         'firsts_selection_rule':'first_technically_valid_complete_response','runs':{}}
    for run in RUNS:
        c=reg['conditions'][run]; stream={'registered_condition_sha256':objsha(c),'records':[]}
        for index,i in enumerate(ids):
            batch='AUDIT-B1' if index < 6 else 'AUDIT-B2'; value=values[run][index]
            row={'assignedID':i,'order_index':index+1,'batch_id':batch,'attempts':[], 'not_called':None,'first':None}
            if isinstance(value,str):
                row['not_called']={'state':value,'reason':'Invented zero-request state: '+value}
            else:
                sequence=value if value and (isinstance(value[0],str) or isinstance(value[0],list)) else [value]
                for n,v in enumerate(sequence,1):
                    a={'attempt_number':n,'started_at':f'2026-10-09T01:00:{2*n:02d}+00:00','ended_at':f'2026-10-09T01:00:{2*n+1:02d}+00:00',
                       'executed_configuration':copy.deepcopy(reg['common_configuration']), 'request_binding':copy.deepcopy(c['requests'][i]),
                       'context':{'context_unit':context,'planned_context_id':c['planned_contexts'][i if context=='record' else batch],
                                  'previous_output_exposure_declared':False,'verification':'not_independently_verified'},
                       'provider_receipt':{'status':'unavailable','request_id':None,'returned_model':None,'configuration_evidence':None},
                       'transport_status':'failure' if v=='transport' else 'ok', 'transport_reason':'Invented transport interruption' if v=='transport' else None,
                       'raw_response':None,'validator_report':None}
                    if v=='transport':
                        # Preserve real *constructed* partial bytes, not a fabricated validator.
                        a['raw_response']=write_ref(base,f'responses/{run}/{i}/partial-{n}.txt',b'{"constructed_partial":')
                    else:
                        obj=response(i,z if v=='bad' else v)
                        checks=dict.fromkeys(CHECKS,True)
                        if v=='bad':
                            del obj['labels']['F'];checks['five_dimensions']=checks['response_schema']=False
                        raw=encoded(obj,True)
                        a['raw_response']=write_ref(base,f'responses/{run}/{i}/attempt-{n}.json',raw)
                        validation={'validator_artifact_sha256':artifacts['technical_validator']['artifact']['sha256'],
                           'exact_request_sha256':c['requests'][i]['exact_request']['sha256'],'raw_response_sha256':sha(raw),
                           'checks':checks,'failure_reasons':['Invented missing F'] if v=='bad' else []}
                        a['validator_report']=write_ref(base,f'responses/{run}/{i}/validation-{n}.json',encoded(validation))
                        if v!='bad':
                            row['first']={'run_id':run,'assignedID':i,'attempt_number':n,'raw_response':copy.deepcopy(a['raw_response']),'parsed_response_sha256':objsha(obj)}
                    row['attempts'].append(a)
            stream['records'].append(row)
        led['runs'][run]=stream
    seal_inputs(base,reg,led)
    return base/'registry.json', base/'ledger.json'
