"""Strict, unweighted descriptive R200 summary; no population inference.

CLI after R200 independent submissions are complete:
  python -B challenge_results.py --freeze /abs/最终冻结清单.json \
      --challenge /abs/R200 --output /abs/new-R200-results.json
Optional --sampler /abs/archived-sample_challenge.py must match the released
sampler_sha256; default is this program's sibling sample_challenge.py.
  python -B challenge_results.py --synthetic-qa --output /abs/new-QA.json

No study files are read on import. assemble/evaluate accept byte snapshots:
  freeze, seal, sampler, postprocessor; frozen={freeze-name:bytes};
  released={R200-relative-path:bytes}; results={R200-relative-path:bytes}.
Actual n is 0..200, with ceil(n/25) material/result packets per AI coder. Frozen
bridge.validate_result and machine_labels enforce the original submission/null
contract. The released sampler hash, registered R200 rule, dictionary, protocol,
freeze, sealed packet hashes and complete ID sets must agree.

Only frozen survey_metrics.metrics_from_table is called, on raw integer 3x3
counts. Its legacy population_weight_total key is renamed sample_n. No analyze,
replicate_weights, bootstrap, interval estimation, H600 N_h/n_h or reference
column is used. A_vs_C and dictionary_vs_A/C describe this challenge set only.
Completion ranges are deterministic binary-completion bounds, NOT confidence
intervals. No consensus, adjudicated or generated reference labels are created.
Original submissions, mapping, material manifest and normalized A/C/dictionary
rows are archived. Runtime rereads all input hashes and inventories before the
frozen bridge's exclusive-partial/no-overwrite publishing function is called.
"""

from __future__ import annotations
import argparse
import copy
from datetime import datetime,timezone
import hashlib
import json
import math
import os
from pathlib import Path,PurePosixPath
import re

DIMS=('S','E','Ec','I','F')
REQUIRED={'holdout_results','survey_metrics','sampler','R200_plan','protocol','dictionary','dictionary_predictions'}
FORBIDDEN_WEIGHT_FIELDS={'N_h','n_h','weight','pi','stratum'}

def sha(data):return hashlib.sha256(data).hexdigest()
def require(condition,message):
    if not condition:raise ValueError(message)
def encoded(value):return (json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
def program(data,name):
    scope={'__name__':'_challenge_frozen_helper','__file__':name}
    exec(compile(data,name,'exec'),scope)
    return scope
def relative(name):
    require(isinstance(name,str) and name and '\\' not in name,'Invalid relative file name')
    path=PurePosixPath(name)
    require(not path.is_absolute() and '..' not in path.parts and str(path)==name and name!='.','Unsafe relative file name')
    return name

def assemble(bundle):
    """Validate exact frozen/issued byte snapshots; generate no labels or metrics."""
    provisional=json.loads(bundle['freeze'])
    require(isinstance(provisional,dict) and isinstance(provisional.get('files'),dict),'Freeze file manifest required')
    files=provisional['files']
    require(REQUIRED<=set(files) and set(bundle['frozen'])==set(files),'Required frozen file inventory mismatch')
    for name,entry in files.items():
        require(isinstance(entry,dict) and isinstance(entry.get('path'),str) and Path(entry['path']).is_absolute(),'Frozen absolute path required')
        require(sha(bundle['frozen'][name])==entry.get('sha256'),'Frozen file changed: '+name)
    bridge=program(bundle['frozen']['holdout_results'],'<frozen holdout_results.py>')
    parse=bridge['read_json'];unique=bridge['unique_rows']
    freeze=parse(bundle['freeze'],'freeze');seal=parse(bundle['seal'],'R200 seal')
    require(freeze.get('status')=='frozen_for_reference_label_holdout','Final freeze required')
    version=bridge['nonempty'](freeze.get('protocol_version'),'protocol_version')
    require(seal.get('freeze_manifest_sha256')==sha(bundle['freeze']),'R200/freeze hash mismatch')
    require(seal.get('sampler_sha256')==sha(bundle['sampler']),'Released R200 sampler version/hash mismatch')
    require(seal.get('machine_parser_sha256')==files['holdout_results']['sha256'],'Released/frozen machine parser mismatch')
    n=seal.get('n');remaining=seal.get('remaining_pool_N')
    require(type(n) is int and 0<=n<=200 and type(remaining) is int and remaining>=0 and n==min(200,remaining),'Invalid R200 actual size/remaining pool')
    expected_status='drawn_challenge_not_representative' if n else 'no_remaining_candidates'
    expected_release='ready_for_blind_review' if n else 'no_packets_created'
    require(seal.get('status')==expected_status and seal.get('release_status')==expected_release,'R200 release state invalid')
    require(seal.get('seed')==2026092604,'R200 registered seed mismatch')
    bridge['hash_value'](seal.get('H600_results_sha256'),'recorded H600 results hash')
    targets=seal.get('targets')
    require(isinstance(targets,list) and targets and len(set(targets))==len(targets) and all(d in DIMS for d in targets),'Invalid R200 target dimensions')
    output_files=seal.get('output_files')
    require(isinstance(output_files,dict) and output_files and set(bundle['released'])==set(output_files),'R200 released file inventory mismatch')
    for name,digest in output_files.items():
        relative(name);require(sha(bundle['released'][name])==bridge['hash_value'](digest,name),'Released R200 file changed: '+name)
    mapping_name='抽样清单-研究者.json'
    require(mapping_name in output_files,'R200 mapping not sealed')
    mapping=parse(bundle['released'][mapping_name],mapping_name);plan=mapping.get('plan')
    require(isinstance(plan,dict) and all(key in seal and value==seal[key] for key,value in plan.items()),'R200 mapping/seal plan mismatch')
    for key in ('status','n','remaining_pool_N','seed','targets','freeze_manifest_sha256','sampler_sha256','machine_parser_sha256','H600_results_sha256'):
        require(key in plan,'Missing R200 mapping plan field: '+key)
    maps=unique(mapping.get('rows'),'id','R200 mapping')
    original=unique(mapping['rows'],'review_id','R200 original IDs')
    require(len(maps)==n and list(maps)==[f'R200-{i:04d}' for i in range(1,n+1)],'R200 mapping count/ID order mismatch')
    for row in maps.values():
        require(not FORBIDDEN_WEIGHT_FIELDS&set(row),'H600 strata/weights forbidden in R200 mapping')
        require('inclusion_probability' in row and row['inclusion_probability'] is None,'No R200 population inclusion probability may be supplied')
        bridge['hash_value'](row.get('unit_text_sha256'),'R200 source text hash')
    batches=math.ceil(n/25)
    materials={f'agent-{c}/材料-{b:02d}.json' for c in ('A','C') for b in range(1,batches+1)}
    results={f'agent-{c}/结果-{b:02d}.json' for c in ('A','C') for b in range(1,batches+1)}
    manuals={f'agent-{c}/五维共用编码协议.md' for c in ('A','C')} if n else set()
    require(set(output_files)==materials|manuals|{mapping_name},'Unexpected/incomplete R200 released set')
    require(set(bundle['results'])==results,'Missing/extra R200 result batches')
    submitted={'A':{},'C':{}};raw_submissions={};packet_manifest={};submission_manifest={}
    for coder in (('A','C') if n else ()):
        require(bundle['released'][f'agent-{coder}/五维共用编码协议.md']==bundle['frozen']['protocol'],'R200 manual differs from frozen protocol')
        for batch in range(1,batches+1):
            pn=f'agent-{coder}/材料-{batch:02d}.json';rn=f'agent-{coder}/结果-{batch:02d}.json'
            raw_packet=bundle['released'][pn];packet=parse(raw_packet,pn)
            require(raw_packet==bundle['released'][f'agent-A/材料-{batch:02d}.json'],'A/C R200 packets differ')
            require(packet.get('protocol_version')==version and packet.get('purpose')=='challenge_AI_independent_not_representative','R200 material version/purpose mismatch')
            require(type(packet.get('batch')) is int and packet['batch']==batch and type(packet.get('total_batches')) is int and packet['total_batches']==batches,'R200 batch header mismatch')
            packet_rows=unique(packet.get('rows'),'id',pn)
            expected=list(maps)[(batch-1)*25:batch*25]
            require(list(packet_rows)==expected,'R200 material IDs differ from their mapped batch')
            text_hashes={}
            for key,row in packet_rows.items():
                require(isinstance(row.get('text'),str),'R200 material text must be a string; empty retained')
                text_hashes[key]=sha(row['text'].encode())
                require(text_hashes[key]==maps[key]['unit_text_sha256'],'R200 material/source text hash mismatch')
                require(isinstance(row.get('contexts'),dict) and isinstance(row.get('input_assessment'),dict),'R200 contexts/assessment object required')
            result=parse(bundle['results'][rn],rn)
            rrows=bridge['validate_result'](result,coder,version,packet,sha(raw_packet),rn)
            require(not set(submitted[coder])&set(rrows),'Duplicate R200 submitted ID across batches')
            submitted[coder].update(rrows);raw_submissions[rn]=result
            packet_manifest[pn]={'sha256':sha(raw_packet),'batch':batch,'ids':expected,'unit_text_sha256':text_hashes}
            submission_manifest[rn]={'sha256':sha(bundle['results'][rn]),'coder':coder,'input_packet_sha256':sha(raw_packet),'ids':list(rrows)}
        require(set(submitted[coder])==set(maps),'R200 coder does not cover complete challenge set')
    predictions_doc=parse(bundle['frozen']['dictionary_predictions'],'frozen dictionary predictions')
    predictions=unique(predictions_doc.get('rows'),'id','frozen dictionary predictions')
    require(set(original)<=set(predictions),'Missing sampled R200 machine prediction')
    normalized=[];selected_predictions={};pending_ids=[];machine_versions=set()
    for key,row in maps.items():
        prediction=predictions[row['review_id']]
        require(prediction.get('unit_text_sha256')==row['unit_text_sha256'],'R200 prediction/source text hash mismatch')
        machine_versions.add(bridge['nonempty'](prediction.get('version'),'dictionary row version'))
        values,was_pending=bridge['machine_labels'](prediction)
        if was_pending:pending_ids.append(key)
        selected_predictions[key]=prediction
        normalized.append({'id':key,'review_id':row['review_id'],
                           'A':bridge['labels'](submitted['A'][key]['labels'],'A'),
                           'C':bridge['labels'](submitted['C'][key]['labels'],'C'),'dictionary':values})
    require(len(machine_versions)<=1,'Mixed R200 dictionary prediction versions')
    machine_version=next(iter(machine_versions)) if machine_versions else predictions_doc.get('version')
    if n and 'version' in predictions_doc:require(predictions_doc['version']==machine_version,'Dictionary document/row version mismatch')
    if n and 'dictionary_version' in freeze:require(freeze['dictionary_version']==machine_version,'Frozen dictionary/row version mismatch')
    dictionary_info={'description':'Frozen dictionary on this directed challenge set only. Each AI comparison uses its original independent labels.',
                     'version':machine_version,'implementation':files['dictionary'],'predictions':files['dictionary_predictions'],
                     'pending_rule':bridge['PENDING_RULE'],'pending_conversion_ids':pending_ids}
    coder_info={c:{'kind':'AI','coder':c,'description':f'Original independent AI coder {c}; no generated/adjudicated reference.',
                  'submissions':{name:{**submission_manifest[name],'identity':obj['identity'],'completed_at':obj['completed_at']}
                                 for name,obj in raw_submissions.items() if name.startswith(f'agent-{c}/')}} for c in ('A','C')}
    archive={'freeze_manifest_original':freeze,'release_seal_original':seal,'sampling_manifest_original':mapping,
             'raw_coder_submissions':raw_submissions,'packet_manifest':packet_manifest,'original_submission_manifest':submission_manifest,
             'normalized_rows_without_generated_reference':normalized,'selected_machine_records_by_blind_id':selected_predictions,
             'input_snapshot_hashes':{'freeze':sha(bundle['freeze']),'seal':sha(bundle['seal']),
                 'challenge_sampler':sha(bundle['sampler']),'postprocessor':sha(bundle['postprocessor']),
                 'frozen':{name:sha(data) for name,data in bundle['frozen'].items()},'released':dict(output_files),
                 'submissions':{name:sha(data) for name,data in bundle['results'].items()}},
             'registered_R200_rule_binding':files['R200_plan'],'machine_null_conversion_rule':bridge['PENDING_RULE'],
             'pending_machine_ids':pending_ids,'reference_created_by_consensus_or_imputation':False}
    return normalized,archive,coder_info,dictionary_info,bridge

def describe(rows,left,right,classification,metric_function):
    """Raw counts and deterministic completion ranges, never a survey design."""
    result={'left':left,'right':right,'dimensions':{}}
    for dim in DIMS:
        table=[[0,0,0] for _ in range(3)]
        for row in rows:
            a=2 if row[left][dim]=='待定' else row[left][dim]
            b=2 if row[right][dim]=='待定' else row[right][dim]
            table[a][b]+=1
        values,flags=metric_function(table,classification)
        require(values.pop('population_weight_total')==len(rows),'Raw challenge count changed')
        renamed={'sample_n':len(rows)}
        for key,value in values.items():
            if key.startswith('binary_total_'):key=key.replace('binary_total_','binary_count_');value=int(value)
            elif key.endswith('_total'):key=key[:-6]+'_n';value=int(value)
            elif key in {'TP','FP','FN','TN'}:value=int(value)
            renamed[key]=value
        result['dimensions'][dim]={'table_axis_order':[0,1,'待定'],'raw_3x3_counts':table,
                                  'descriptive_values':renamed,'completion_and_undefined_flags':flags}
    return result

def evaluate(bundle):
    rows,archive,coder_info,dictionary_info,_=assemble(bundle)
    comparisons={}
    if rows:
        metrics=program(bundle['frozen']['survey_metrics'],'<frozen survey_metrics.py>')
        point_function=metrics['metrics_from_table']
        comparisons['A_vs_C']=describe(rows,'A','C',False,point_function)
        comparisons['A_vs_C']['left_source_info']=coder_info['A'];comparisons['A_vs_C']['right_source_info']=coder_info['C']
        for coder in ('A','C'):
            item=describe(rows,'dictionary',coder,True,point_function)
            item['right_source_info']=coder_info[coder];item['dictionary_info']=dictionary_info
            comparisons['dictionary_vs_'+coder]=item
    return {'status':'completed_challenge_descriptive_ID_join_not_validation_pass' if rows else 'challenge_no_observations',
            'created_at':datetime.now(timezone.utc).isoformat(),'sample_n':len(rows),
            'scope':'Directed R200 challenge set only; no population inference or pooling with H600.',
            'population_inference':False,'population_weights_used':False,'confidence_intervals_computed':False,
            'reference_generated':False,'comparisons':comparisons,'archive':archive,
            'interpretation':['Every observation has raw count one; no H600 N_h/n_h are borrowed.',
                'Two dictionary comparisons share the same challenge set; they are not independent samples or human gold truth.',
                'Binary ratios condition on both labels being definite; coverage and pending counts remain explicit.',
                'Completion ranges are deterministic bounds for this supplied set, not confidence intervals or completed labels.',
                'Frozen hashes establish file consistency, not correct labels, honest independence or external generalization.']}

def load_snapshot(freeze_path,challenge_path,sampler_path):
    require(all(p.is_absolute() for p in (freeze_path,challenge_path,sampler_path)),'Use absolute input paths')
    tracked={}
    def read(path):
        path=Path(path);data=path.read_bytes();key=str(path)
        require(key not in tracked or tracked[key]==sha(data),'Input changed during snapshot read')
        tracked[key]=sha(data);return data
    fb=read(freeze_path);freeze=json.loads(fb)
    require(isinstance(freeze.get('files'),dict) and REQUIRED<=set(freeze['files']),'Required frozen bindings missing')
    frozen={name:read(Path(entry['path'])) for name,entry in freeze['files'].items()}
    sb=read(challenge_path/'封存信息.json');seal=json.loads(sb);released={}
    for name in seal.get('output_files',{}):
        relative(name);path=challenge_path/name
        require(path.resolve().is_relative_to(challenge_path.resolve()),'Released path escapes R200')
        released[name]=read(path)
    inventory={kind:sorted(str(p.relative_to(challenge_path)) for p in challenge_path.glob(f'agent-*/{prefix}-*.json'))
               for kind,prefix in [('materials','材料'),('results','结果')]}
    require(inventory['materials']==sorted(name for name in released if re.fullmatch(r'agent-[AC]/材料-\d{2}\.json',name)),'Unsealed/missing R200 material inventory')
    results={}
    for name in inventory['results']:
        path=challenge_path/name
        require(path.resolve().is_relative_to(challenge_path.resolve()),'Result path escapes R200')
        results[name]=read(path)
    return {'freeze':fb,'seal':sb,'sampler':read(sampler_path),'postprocessor':read(Path(__file__).resolve()),
            'frozen':frozen,'released':released,'results':results},tracked,inventory

def _synthetic_bundle(bridge_bytes,metrics_bytes,sampler_bytes,own_bytes):
    bridge=program(bridge_bytes,'<synthetic helper bridge>')
    base=bridge['_synthetic_bundle'](metrics_bytes,bridge_bytes)
    frozen=base['frozen'];frozen['R200_plan']=b'SYNTHETIC REGISTERED R200 RULE ONLY'
    freeze=json.loads(base['freeze']);freeze['files']['R200_plan']={'path':'/synthetic-only/R200_plan','sha256':sha(frozen['R200_plan'])}
    fb=encoded(freeze)
    def renamed(value):
        if isinstance(value,str) and value.startswith('H600-'):return value.replace('H600-','R200-',1)
        if isinstance(value,list):return [renamed(x) for x in value]
        if isinstance(value,dict):return {k:renamed(v) for k,v in value.items()}
        return value
    oldmap=renamed(json.loads(base['released']['抽样清单-研究者.json']))
    maps=[{k:r[k] for k in ('id','review_id','unit_text_sha256')}|{'candidate_bucket':'synthetic_private_bucket','inclusion_probability':None} for r in oldmap['rows']]
    plan={'status':'drawn_challenge_not_representative','n':26,'remaining_pool_N':26,'targets':['S'],'seed':2026092604,
          'freeze_manifest_sha256':sha(fb),'sampler_sha256':sha(sampler_bytes),
          'machine_parser_sha256':sha(bridge_bytes),'H600_results_sha256':sha(b'SYNTHETIC HASH ONLY; NO H600 RESULT FILE')}
    released={'抽样清单-研究者.json':encoded({'plan':plan,'rows':maps})};results={}
    for coder in ('A','C'):
        released[f'agent-{coder}/五维共用编码协议.md']=frozen['protocol']
        for batch in (1,2):
            pn=f'agent-{coder}/材料-{batch:02d}.json';rn=f'agent-{coder}/结果-{batch:02d}.json'
            packet=renamed(json.loads(base['released'][pn]));packet['purpose']='challenge_AI_independent_not_representative'
            released[pn]=encoded(packet)
            result=renamed(json.loads(base['results'][rn]));result['input_packet_sha256']=sha(released[pn]);results[rn]=encoded(result)
    seal={**plan,'release_status':'ready_for_blind_review','output_files':{name:sha(data) for name,data in released.items()}}
    return {'freeze':fb,'seal':encoded(seal),'sampler':sampler_bytes,'postprocessor':own_bytes,'frozen':frozen,'released':released,'results':results}

def self_test():
    out=Path(__file__).parent
    bridge_bytes=(out/'holdout_results.py').read_bytes();metrics_bytes=(out/'survey_metrics.py').read_bytes()
    sampler_bytes=(out/'sample_challenge.py').read_bytes();own_bytes=Path(__file__).read_bytes()
    fixture=_synthetic_bundle(bridge_bytes,metrics_bytes,sampler_bytes,own_bytes)
    result=evaluate(fixture);checks={};rejected={}
    require(result['sample_n']==26 and set(result['comparisons'])=={'A_vs_C','dictionary_vs_A','dictionary_vs_C'},'Challenge comparison/size mismatch')
    values=result['comparisons']['dictionary_vs_C']['dimensions']['S']['descriptive_values']
    require(values['sample_n']==26 and abs(values['coverage_both_definite']-24/26)<1e-12 and values['TP']==12 and values['TN']==12,'Unweighted hand-calculated table mismatch')
    require(result['comparisons']['A_vs_C']['dimensions']['S']['descriptive_values']['kappa_definite']==1,'Descriptive kappa mismatch')
    normalized=result['archive']['normalized_rows_without_generated_reference']
    require(all(not FORBIDDEN_WEIGHT_FIELDS&set(row) and 'reference' not in row for row in normalized),'Weights/generated reference entered normalized rows')
    require(normalized[0]['dictionary']=={d:'待定' for d in DIMS} and normalized[1]['C']=={d:'待定' for d in DIMS},'Pending labels changed')
    checks['26_rows_two_batches_unweighted_hand_counts_pending_and_original_submissions']='passed'
    def bad(name,mutate,needle=None):
        candidate=copy.deepcopy(fixture);mutate(candidate)
        try:assemble(candidate)
        except (ValueError,KeyError,TypeError) as exc:
            if needle:require(needle in str(exc),'Unexpected failure for '+name+': '+str(exc))
            rejected[name]=str(exc)
        else:raise AssertionError('Invalid challenge input accepted: '+name)
    def result_change(b,change):
        name='agent-A/结果-01.json';obj=json.loads(b['results'][name]);change(obj);b['results'][name]=encoded(obj)
    def release_change(b,name,change):
        obj=json.loads(b['released'][name]);change(obj);b['released'][name]=encoded(obj)
        seal=json.loads(b['seal']);seal['output_files'][name]=sha(b['released'][name]);b['seal']=encoded(seal)
    def prediction_change(b,change):
        obj=json.loads(b['frozen']['dictionary_predictions']);change(obj);b['frozen']['dictionary_predictions']=encoded(obj)
        freeze=json.loads(b['freeze']);freeze['files']['dictionary_predictions']['sha256']=sha(b['frozen']['dictionary_predictions']);b['freeze']=encoded(freeze)
        name='抽样清单-研究者.json';mapping=json.loads(b['released'][name]);mapping['plan']['freeze_manifest_sha256']=sha(b['freeze']);b['released'][name]=encoded(mapping)
        seal=json.loads(b['seal']);seal['freeze_manifest_sha256']=sha(b['freeze']);seal['output_files'][name]=sha(b['released'][name]);b['seal']=encoded(seal)
    bad('missing_result_batch',lambda b:b['results'].pop('agent-C/结果-02.json'),'result batches')
    bad('duplicate_result_ID',lambda b:result_change(b,lambda x:x['rows'].append(copy.deepcopy(x['rows'][0]))),'duplicate')
    bad('crossed_batch_ID',lambda b:result_change(b,lambda x:x['rows'][0].update(id='R200-0026')),'ID set')
    bad('changed_result_version',lambda b:result_change(b,lambda x:x.update(protocol_version='changed')),'version')
    bad('changed_packet_hash',lambda b:result_change(b,lambda x:x.update(input_packet_sha256='0'*64)),'packet hash')
    bad('empty_evidence_contract',lambda b:result_change(b,lambda x:x['rows'][0].update(evidence='')),'evidence')
    bad('invalid_subtype_contract',lambda b:result_change(b,lambda x:x['rows'][0].update(fairness_subtypes=['unknown'])),'subtypes')
    bad('changed_R200_sampler',lambda b:b.update(sampler=b'CHANGED SYNTHETIC SAMPLER'),'sampler version')
    bad('changed_registered_rule',lambda b:b['frozen'].update(R200_plan=b'CHANGED RULE'),'Frozen file')
    bad('changed_frozen_dictionary',lambda b:b['frozen'].update(dictionary=b'CHANGED DICTIONARY'),'Frozen file')
    bad('changed_frozen_protocol',lambda b:b['frozen'].update(protocol=b'CHANGED PROTOCOL'),'Frozen file')
    bad('changed_freeze_bytes',lambda b:b.update(freeze=b['freeze']+b' '),'freeze hash')
    bad('H600_weights_in_mapping',lambda b:release_change(b,'抽样清单-研究者.json',lambda x:x['rows'][0].update(N_h=100,n_h=2)),'strata/weights forbidden')
    bad('wrong_inclusion_probability',lambda b:release_change(b,'抽样清单-研究者.json',lambda x:x['rows'][0].update(inclusion_probability=1)),'inclusion probability')
    bad('machine_boolean_label',lambda b:prediction_change(b,lambda x:x['rows'][0]['labels'].update(F=True)),'literal integer')
    bad('machine_text_hash_mismatch',lambda b:prediction_change(b,lambda x:x['rows'][0].update(unit_text_sha256='0'*64)),'text hash')
    bad('machine_mixed_None',lambda b:prediction_change(b,lambda x:x['rows'][0]['labels'].update(S=None)),'partial null')
    checks['strict_frozen_contract_and_source_binding']={'status':'passed','rejected_cases':rejected}
    # Poison forbidden functions in a synthetic module snapshot; point function is untouched.
    guarded=metrics_bytes+b'\ndef _no_inference(*args, **kwargs):\n    raise AssertionError("Forbidden population inference called")\nanalyze=replicate_weights=interval_summary=_no_inference\n'
    guarded_result=evaluate(_synthetic_bundle(bridge_bytes,guarded,sampler_bytes,own_bytes))
    require(not guarded_result['population_inference'] and not guarded_result['confidence_intervals_computed'],'Inference flags wrong')
    require(guarded_result['comparisons']==result['comparisons'],'Point result changed with forbidden functions disabled')
    checks['analyze_bootstrap_and_interval_functions_disabled_without_effect']='passed'
    zero=copy.deepcopy(fixture);mapping=json.loads(zero['released']['抽样清单-研究者.json'])
    mapping['plan'].update(status='no_remaining_candidates',n=0,remaining_pool_N=0);mapping['rows']=[]
    zero['released']={'抽样清单-研究者.json':encoded(mapping)};zero['results']={}
    zero['seal']=encoded({**mapping['plan'],'release_status':'no_packets_created','output_files':{'抽样清单-研究者.json':sha(zero['released']['抽样清单-研究者.json'])}})
    empty=evaluate(zero);require(empty['status']=='challenge_no_observations' and not empty['comparisons'],'Zero challenge generated estimates')
    checks['zero_remaining_pool_has_no_estimates_or_packets']='passed'
    bridge=program(bridge_bytes,'<frozen bridge>')
    try:bridge['check_unchanged']({'synthetic':'a'},{'synthetic':'b'})
    except ValueError:checks['snapshot_change_guard']='passed'
    else:raise AssertionError('Changed inputs accepted')
    return {'status':'passed_synthetic_QA_only','code_sha256':sha(own_bytes),'checks':checks,
            'helper_program_sha256':{'holdout_results':sha(bridge_bytes),'survey_metrics':sha(metrics_bytes),'sample_challenge':sha(sampler_bytes)},
            'real_policy_text_read':False,'real_predictions_read':False,'real_A_C_labels_read':False,'real_H600_results_read':False,
            'real_freeze_manifest_read':False,'real_challenge_results_created':False,
            'limits':['Only synthetic records and pure source programs were read.',
                      'Actual input inventories, real label semantics and real filesystem publication were not exercised.',
                      'Reported completion ranges are deterministic within-set bounds, not confidence intervals.']}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--freeze',type=Path);parser.add_argument('--challenge',type=Path);parser.add_argument('--sampler',type=Path)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--synthetic-qa',action='store_true');args=parser.parse_args()
    require(not os.path.lexists(args.output) and not os.path.lexists(args.output.with_name('.'+args.output.name+'.partial')),'Refusing existing output or partial')
    if args.synthetic_qa:
        require(args.freeze is None and args.challenge is None and args.sampler is None,'Synthetic QA accepts no study input paths')
        output=self_test();bridge=program(Path(__file__).with_name('holdout_results.py').read_bytes(),'<bridge publication helper>')
    else:
        require(args.freeze is not None and args.challenge is not None,'Explicit --freeze and --challenge required')
        sampler=args.sampler or Path(__file__).resolve().with_name('sample_challenge.py')
        bundle,tracked,inventory=load_snapshot(args.freeze,args.challenge,sampler)
        output=evaluate(bundle);bridge=program(bundle['frozen']['holdout_results'],'<frozen bridge publication helper>')
        bridge['check_unchanged'](tracked,{path:sha(Path(path).read_bytes()) for path in tracked})
        current={kind:sorted(str(p.relative_to(args.challenge)) for p in args.challenge.glob(f'agent-*/{prefix}-*.json')) for kind,prefix in [('materials','材料'),('results','结果')]}
        bridge['check_unchanged'](inventory,current)
        output['archive']['filesystem_snapshot_manifest']=tracked;output['archive']['input_inventory']=inventory
    bridge['publish_json'](args.output,output)
    print(json.dumps({'output':str(args.output),'status':output['status']},ensure_ascii=False))

if __name__=='__main__':main()
