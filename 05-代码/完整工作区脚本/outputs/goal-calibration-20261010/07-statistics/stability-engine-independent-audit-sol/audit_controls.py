#!/usr/bin/env python3
"""Finite independent mathematical controls, contract mutations and CLI seal audits."""
import argparse
import ast
import copy
import importlib.util
import json
import math
import os
import shutil
import subprocess
import sys
from fractions import Fraction as F
from pathlib import Path
from independent_fixture import build, encoded, sha, objsha, seal_inputs, write_ref, make_request, DIMS, RUNS

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
SOURCE = BASE.parent / 'prospective-stability-engine-sol'
RESULTS = []

def load_engine(path):
    spec=importlib.util.spec_from_file_location('audited_engine_'+sha(str(path).encode())[:12],path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

def check(name, fn):
    try:
        info=fn()
        RESULTS.append({'control':name,'status':'passed','details':info})
    except Exception as exc:
        RESULTS.append({'control':name,'status':'failed','exception':repr(exc)})

def close(value, expected):
    assert math.isclose(value,float(expected),rel_tol=1e-12,abs_tol=1e-12),(value,expected)

def report(engine,folder):
    return engine.analyze_registry(folder/'registry.json',folder/'ledger.json')[0]

def clone(name):
    folder=BASE/'inputs'/name
    shutil.copytree(BASE/'inputs'/'independent-eleven',folder)
    return folder,json.loads((folder/'registry.json').read_text()),json.loads((folder/'ledger.json').read_text())

def mutate_case(engine,name,fn,pattern):
    folder,reg,led=clone(name)
    fn(reg,led,folder)
    seal_inputs(folder,reg,led)
    try:
        report(engine,folder)
    except (engine.ContractError,KeyError,TypeError) as exc:
        assert pattern in str(exc),str(exc)
        return {'rejected_reason':str(exc)}
    raise AssertionError('Invalid mutation accepted: '+name)

def complete_rebind(reg,led):
    for run in RUNS:
        c=reg['conditions'][run]
        c['sample_plan_sha256']=objsha(reg['sample'])
        c['common_configuration_sha256']=objsha(reg['common_configuration'])
        c['common_artifacts_sha256']=objsha(reg['common_artifacts'])
        led['runs'][run]['registered_condition_sha256']=objsha(c)
        for row in led['runs'][run]['records']:
            for a in row['attempts']:
                a['request_binding']=copy.deepcopy(c['requests'][row['assignedID']])

def cli(engine_path,folder,outname):
    target=BASE/outname
    args=[sys.executable,'-B',str(engine_path),'analyze','--registry',str(folder/'registry.json'),'--ledger',str(folder/'ledger.json'),'--out-dir',str(target)]
    proc=subprocess.run(args,text=True,capture_output=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    log={'argv':args,'returncode':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr}
    (BASE/'verification').mkdir(exist_ok=True)
    (BASE/'verification'/(outname.replace('/','__')+'.json')).write_bytes(encoded(log))
    return proc,target

def expected_input_paths(folder):
    reg=json.loads((folder/'registry.json').read_text()); led=json.loads((folder/'ledger.json').read_text())
    paths={str((folder/'registry.json').resolve()),str((folder/'ledger.json').resolve())}
    refs=[a['artifact'] for a in reg['common_artifacts'].values()]
    refs += [r['material']['source_packet'] for r in reg['sample']['assigned_records']]
    refs += [b['exact_request'] for c in reg['conditions'].values() for b in c['requests'].values()]
    refs += [a[k] for stream in led['runs'].values() for row in stream['records'] for a in row['attempts'] for k in ('raw_response','validator_report') if a[k] is not None]
    paths.update(str((folder/ref['path']).resolve()) for ref in refs)
    return paths

def verify_analysis_seal(out,folder,engine_path):
    seal=json.loads((out/'seal.json').read_text())
    got={item['path'] for item in seal['inputs']}
    assert got==expected_input_paths(folder),{'missing':sorted(expected_input_paths(folder)-got),'extra':sorted(got-expected_input_paths(folder))}
    assert len(got)==len(seal['inputs'])
    assert {i['path'] for i in seal['outputs']}=={'report.json','firsts.json','audit-ledger.json','report.md'}
    for item in seal['inputs']+[{**i,'path':str(out/i['path'])} for i in seal['outputs']]:
        raw=Path(item['path']).read_bytes();assert sha(raw)==item['sha256'] and len(raw)==item['bytes'],item
    assert seal['engine']['sha256']==sha(Path(engine_path).read_bytes())
    assert seal['engine']['path']==str(Path(engine_path).resolve())
    assert seal['identity_or_independence_authenticated_by_hash'] is False and seal['seal_self_included'] is False
    return {'input_files':len(got),'output_files':len(seal['outputs']),'engine_sha256':seal['engine']['sha256']}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--engine',type=Path,default=SOURCE/'stability_engine.py');ap.add_argument('--stage',choices=['original','repair'],default='original');args=ap.parse_args()
    engine=load_engine(args.engine); baseline=BASE/'inputs'/'independent-eleven'
    r=report(engine,baseline)
    ids=[f'AUDIT-{j:03d}' for j in range(1,12)]

    def cells_and_direction():
        # Hard-coded hand cells for all fixed pairs, including reversal W/R1,H/R1.
        tables={'R1/R2':([2,1,2,1],[F(39,2),2,14,5]),
                'R1/R3':([2,1,1,2],[F(39,2),2,3,16]),
                'R2/R3':([4,1,1,2],[F(71,2),11,7,7]),
                'W/R1':([2,2,1,1],[F(39,2),14,2,5]),
                'H/R1':([2,2,1,1],[F(39,2),14,2,5])}
        for pair,(raw,weighted) in tables.items():
            p=r['paired_comparisons'][pair]['dimensions']['S']
            for mode,c in [('raw',raw),('weighted',weighted)]:
                assert list(p[mode]['cells'].values())==c
                # Independent probability form from marginal positivity, not candidate four-cell formula.
                den=sum(c);px=F(c[2]+c[3],den);py=F(c[1]+c[3],den)
                pe=px*py+(1-px)*(1-py);po=1-F(c[1]+c[2],den)
                close(p[mode]['Po'],po);close(p[mode]['Pe'],pe);close(p[mode]['kappa'],(po-pe)/(1-pe))
                assert p[mode]['positive_counts']['change_second_minus_first']==c[1]-c[2]
                assert p[mode]['label_change_mass']==c[1]+c[2]
            for change in p['label_changes']:
                assert change['first_label']!=change['second_label']
                assert change['first_raw_response']['sha256'] and change['second_raw_response']['sha256']
        s=r['paired_comparisons']['R1/R2']['dimensions']['S']['weighted'];close(s['kappa'],F(139,787))
        return {'pairs':list(tables),'weighted_R1_R2_S_kappa':'139/787','R1_R2_positive_change_raw':-1,'weighted':-12}
    check('hand_all_fixed_pair_cells_direction_marginals_and_positive_changes',cells_and_direction)

    def triples():
        t=r['three_main_runs']['five_dimension_vector']
        assert t['domain']['joint_comparable_assignedIDs']==ids[:4]
        assert t['agreement_assignedIDs']==ids[:1]
        assert t['denominator_n']==4 and t['weighted_denominator']==10.5
        close(t['complete_agreement_rate'],F(1,4));close(t['weighted_complete_agreement_rate'],F(1,21))
        assert t['domain']['scheduled_n']==11 and t['domain']['scheduled_weight_sum']==129.5
        return {'raw':'1/4','weighted':'(1/2)/(21/2)=1/21','scheduled_weight':129.5,'denominator_weight':10.5}
    check('hand_three_way_vector_uses_finite_joint_C5_not_assigned_N_or_weight',triples)

    def qs():
        q=r['three_main_runs']['q'];assert q['domain']['joint_comparable_assignedIDs']==ids[:4]
        hand={'R1':([2,2,2,2,1],9,[8,7,8,7,5],35),'R2':([2,1,1,1,0],5,[7,2,3,2,0],14),'R3':([2,2,1,1,1],7,[7,8,3,2,3],23)}
        for run,(u,ud,w,wd) in hand.items():
            x=q['by_run'][run];assert list(x['unweighted_T'].values())==u and x['unweighted_sum5T']==ud
            assert list(x['weighted_T'].values())==w and x['weighted_sum5T']==wd
            for d,v,wv in zip(DIMS,u,w):close(x['unweighted_q'][d],F(v,ud));close(x['weighted_q'][d],F(wv,wd))
            close(sum(x['weighted_q'].values()),1)
        close(q['q_ranges']['weighted_q']['S']['range'],F(19,70))
        for pair in r['paired_comparisons'].values():
            assert pair['q']['domain']['joint_comparable_assignedIDs']==pair['five_dimension_vector']['domain']['joint_comparable_assignedIDs']
        return {'raw_denominators':[9,5,7],'weighted_denominators':[35,14,23],'weighted_S_range':'19/70'}
    check('hand_multilabel_q_own_run_sum5T_denominators_unequal_weights',qs)

    def states():
        s=r['per_record_diagnostic_states'];assert s[ids[4]]['R1']['state']=='valid_semantic_null'
        assert s[ids[6]]['R1']['state']=='technical_failure';assert s[ids[6]]['R1']['remaining_retry_slots_if_unresolved']==2
        assert s[ids[10]]['R3']['failure_exhausted_three_attempts'] is True
        assert s[ids[8]]['R1']['material_state']=='pending'
        assert r['three_main_runs']['five_dimension_vector']['domain']['material_pending_n']==1
        assert r['three_main_runs']['semantic_null_patterns']['is_binary_stability'] is False
        for run,index,kind in [('R1',7,'not_called'),('R1',10,'material_blocked'),('R2',9,'creation_empty'),('R3',9,'precheck_blocked')]:
            assert s[ids[index]][run]['not_called']['state']==kind
        raw_audit=engine.analyze_registry(baseline/'registry.json',baseline/'ledger.json')[2]
        assert raw_audit['runs']['R1'][9]['attempts'][0]['raw_response']['sha256']==sha(b'{"constructed_partial":')
        assert s[ids[6]]['R1']['labels'] is None # four superficially usable dimensions cannot survive whole-response failure.
        return {'zero_attempt_kinds_preserved':['not_called','material_blocked','creation_empty','precheck_blocked'],'failure_and_null_separate':True,'partial_transport_bytes_retained':True}
    check('null_failure_notcalled_subtypes_pending_overlap_and_partial_raw_separate',states)

    def firsts():
        p=r['production_firsts'];assert p[ids[2]]['attempt_number']==2
        assert p[ids[1]]['attempt_number']==1 and p[ids[1]]['labels']['E'] is None
        assert p[ids[3]] is None and r['per_record_diagnostic_states'][ids[3]]['R1']['first'] is not None
        assert p[ids[0]]['labels']==dict.fromkeys(DIMS,0)
        assert list(r['paired_comparisons'])==['R1/R2','R1/R3','R2/R3','W/R1','H/R1']
        for v in ['W/R1','H/R1']:assert r['paired_comparisons'][v]['dimensions']['S']['raw']['label_change_mass']==3
        return {'first_valid_at_attempt':2,'null_stops_at_attempt':1,'production_failure_not_filled':True,'variant_baseline':'R1'}
    check('first_valid_whole_response_and_fixed_variant_baseline',firsts)

    # Existing fixture names get stage suffix; originals remain reviewable after repair.
    prefix=args.stage+'-'
    def special(mode,fn):
        folder=BASE/'inputs'/(prefix+mode);build(folder,mode);return fn(report(engine,folder))
    def zero_check(x):
        for d in DIMS:
            m=x['paired_comparisons']['R1/R2']['dimensions'][d]['raw'];assert m['Po']==1 and m['Pe']==1 and m['kappa'] is None
        q=x['three_main_runs']['q'];assert q['by_run']['R1']['unweighted_sum5T']==0
        assert q['q_ranges']['weighted_q']['S']['na_runs']==['R1','R2','R3']
        return {'Po':1,'Pe':1,'kappa':None,'q':None}
    check('all_zero_marginal_kappa_and_q_NA',lambda:special('zero',zero_check))
    check('all_one_marginal_kappa_NA',lambda:special('one',lambda x:zero_check_one(x)))
    def no_check(x):
        for pair in x['paired_comparisons'].values():
            for d in DIMS:
                y=pair['dimensions'][d]['raw'];assert y['denominator']==0 and y['Po'] is None and y['Pe'] is None and y['kappa'] is None
        assert x['three_main_runs']['five_dimension_vector']['weighted_complete_agreement_rate'] is None
        assert x['limits']['binary_input_complete_for_all_registered_runs'] is False
        return {'N':0,'Po':None,'Pe':None,'kappa':None,'completion_claim':False}
    check('no_common_records_all_metrics_NA',lambda:special('no-common',no_check))
    def no_r3(x):
        assert x['three_main_runs']['five_dimension_vector']['denominator_n']==0
        assert x['limits']['all_registered_records_have_technical_firsts'] is False
        assert x['not_a_project_completion_or_validation_decision'] is True
        return {'R3_notcalled_n':11,'three_way_binary_denominator':0,'project_complete':False}
    check('unfinished_third_run_does_not_appear_complete',lambda:special('missing-R3',no_r3))

    def lone_zero_q():
        folder,reg,led=clone(prefix+'one-q-NA')
        for row in led['runs']['R3']['records']:
            for a in row['attempts']:
                if a['transport_status']!='ok':continue
                obj=json.loads((folder/a['raw_response']['path']).read_text())
                if set(obj['labels'])!=set(DIMS) or any(v is None for v in obj['labels'].values()):continue
                obj['labels']=dict.fromkeys(DIMS,0);update_raw(folder,reg,row,a,obj)
        seal_inputs(folder,reg,led);x=report(engine,folder)
        q=x['three_main_runs']['q'];assert q['q_ranges']['weighted_q']['S']['na_runs']==['R3']
        assert q['q_ranges']['weighted_q']['S']['range'] is None
        assert q['by_run']['R1']['weighted_sum5T']==35 and q['by_run']['R2']['weighted_sum5T']==14
        return {'NA_run':'R3','full_group_range':None,'defined_runs_retained':True}
    check('one_zero_sum5T_run_not_deleted_to_fabricate_complete_q_range',lone_zero_q)

    mutations=[
      ('config-drift',lambda g,l,b:l['runs']['R2']['records'][0]['attempts'][0]['executed_configuration']['request_settings'].update(audit_setting=True),'model/settings drift'),
      ('manual-version-drift',lambda g,l,b:g['common_artifacts']['manual'].update(version='unregistered-v2'),'version/manual/prompt drift'),
      ('prompt-byte-drift',lambda g,l,b:(b/g['common_artifacts']['prompt']['artifact']['path']).write_bytes(b'changed prompt'),'SHA mismatch'),
      ('material-byte-drift',lambda g,l,b:(b/g['sample']['assigned_records'][0]['material']['source_packet']['path']).write_bytes(b'{}'),'SHA mismatch'),
      ('ctx-bind-drift',lambda g,l,b:g['sample']['assigned_records'][0]['material']['ctx_binding'][0].update(CTXID='FOREIGN'),'CTX binding SHA mismatch'),
      ('order-drift',lambda g,l,b:l['runs']['R2']['records'][0].update(order_index=2),'order or batch drift'),
      ('batch-drift',lambda g,l,b:l['runs']['R2']['records'][0].update(batch_id='AUDIT-B2'),'order or batch drift'),
      ('contextunit-drift',lambda g,l,b:l['runs']['R2']['records'][0]['attempts'][0]['context'].update(context_unit='batch'),'context plan drift'),
      ('request-hash-drift',lambda g,l,b:l['runs']['P']['records'][2]['attempts'][1]['request_binding']['exact_request'].update(sha256='0'*64),'retry exact request/material drift'),
      ('later-first',lambda g,l,b:l['runs']['P']['records'][2].update(first=copy.deepcopy(l['runs']['R1']['records'][2]['first'])),'no diagnostic substitution'),
      ('null-retry',lambda g,l,b:append_retry(l['runs']['P']['records'][1]),'semantic null cannot trigger retry'),
      ('more-than-three',lambda g,l,b:append_retry(l['runs']['P']['records'][3]),'max 3 actual attempts'),
      ('missing-row',lambda g,l,b:l['runs']['R3']['records'].pop(),'complete ordered record ledger'),
      ('missing-run',lambda g,l,b:l['runs'].pop('R3'),'all six registered conditions'),
      ('best-baseline',lambda g,l,b:g['comparison_plan'].update(perturbation_baseline='R2'),'comparison plan must retain fixed'),
      ('threshold',lambda g,l,b:g.update(stability_pass_threshold=0.8),'no stability pass threshold'),
      ('CI-gate',lambda g,l,b:g.update(confidence_interval_gate=0.8),'no stability pass threshold'),
      ('missing-contextunit',lambda g,l,b:g.pop('context_unit'),'registry top-level fields'),
      ('false-local-validator',lambda g,l,b:falsify_local_check(g,l,b),'contradicts locally checked'),
      ('unbound-quote-validator',lambda g,l,b:falsify_validator_binding(g,l,b),'validator report binding mismatch')]
    for name,fn,pattern in mutations:
        check('reject_'+name,lambda name=name,fn=fn,pattern=pattern:mutate_case(engine,prefix+name,fn,pattern))

    def batch_check():
        folder=BASE/'inputs'/(prefix+'batch');build(folder,context='batch');x=report(engine,folder)
        i=x['identity_and_independence'];assert i['per_record_context_protocol_shape'] is False and i['independent_contexts_verified'] is False
        assert i['batch_context_warning'] and x['limits']['classification_correctness_measured'] is False
        return {'batch_shape_matches_record_protocol':False,'independence_verified':False,'complete_native_batch_adapter_available':False}
    check('explicit_batch_context_cannot_be_auto_certified_record_context',batch_check)

    if args.stage=='original':
        check('candidate_preparation_manifest_exact_651_and_source_hashes',verify_preparation)
        for name in ['mixed','all-zero','rare','batch-context']:
            check('candidate_existing_cli_seal_'+name,lambda name=name:verify_analysis_seal(SOURCE/'constructed-controls/results'/name,SOURCE/'constructed-controls/inputs'/name,SOURCE/'stability_engine.py'))
        def replay():
            folder=SOURCE/'constructed-controls/inputs/mixed';proc,out=cli(args.engine,folder,'original-candidate-mixed-replay')
            assert proc.returncode==0,proc.stderr
            x=verify_analysis_seal(out,folder,args.engine)
            for name in ['report.json','firsts.json','audit-ledger.json','report.md','seal.json']:
                assert (out/name).read_bytes()==(SOURCE/'constructed-controls/results/mixed'/name).read_bytes(),name
            return {**x,'five_files_byte_equal_to_sealed_cli_outputs':True}
        check('actual_candidate_CLI_replay_full_chain_without_writing_sealed_dir',replay)
        check('audit_original_baseline_CLI_seal',lambda:verify_analysis_seal(BASE/'original-baseline-cli',baseline,args.engine))
        prepare_type_counterexamples(args.engine)
        prepare_boundaries(args.engine)
    else:
        for name,pattern in [('census-boolean-pi','boolean is not a weight'),('retry-policy-json-type','fixed first-valid retry policy')]:
            def regression(name=name,pattern=pattern):
                folder=BASE/'inputs'/name
                try:report(engine,folder)
                except engine.ContractError as exc:
                    assert pattern in str(exc);return {'rejected_reason':str(exc)}
                raise AssertionError('Repair failed to reject '+name)
            check('regression_reject_original_bug_'+name,regression)
        proc,out=cli(args.engine,baseline,'repair-baseline-cli')
        check('repaired_CLI_baseline_and_seal',lambda:verify_analysis_seal(out,baseline,args.engine) if proc.returncode==0 else (_ for _ in ()).throw(AssertionError(proc.stderr)))
    summary={'stage':args.stage,'engine_path':str(args.engine.resolve()),'engine_sha256':sha(args.engine.read_bytes()),
             'independent_controls_run':len(RESULTS),'passed':sum(x['status']=='passed' for x in RESULTS),'failed':sum(x['status']=='failed' for x in RESULTS),
             'controls':RESULTS,'real_labels_or_gold_read':False,'model_dispatch_count':0,'scope':'constructed mathematical and engineering controls only; no reality stability validation'}
    (BASE/('controls-'+args.stage+'.json')).write_bytes(encoded(summary))
    print(json.dumps({k:v for k,v in summary.items() if k!='controls'},ensure_ascii=False))
    return bool(summary['failed'])

def zero_check_one(x):
    for d in DIMS:
        y=x['paired_comparisons']['R1/R2']['dimensions'][d]['raw'];assert y['Po']==1 and y['Pe']==1 and y['kappa'] is None
    return {'Po':1,'Pe':1,'kappa':None,'positive_count_each_run':11}

def append_retry(row):
    a=copy.deepcopy(row['attempts'][-1]);a['attempt_number']=len(row['attempts'])+1
    a['started_at']=f'2026-10-09T01:00:{2*a["attempt_number"]:02d}+00:00';a['ended_at']=f'2026-10-09T01:00:{2*a["attempt_number"]+1:02d}+00:00'
    row['attempts'].append(a)

def update_raw(folder,reg,row,a,obj):
    ref=a['raw_response'];a['raw_response']=write_ref(folder,ref['path'],encoded(obj,True))
    v=json.loads((folder/a['validator_report']['path']).read_text());v['raw_response_sha256']=a['raw_response']['sha256']
    a['validator_report']=write_ref(folder,a['validator_report']['path'],encoded(v))
    if row['first'] and row['first']['attempt_number']==a['attempt_number']:
        row['first']['raw_response']=copy.deepcopy(a['raw_response']);row['first']['parsed_response_sha256']=objsha(obj)

def falsify_local_check(g,l,b):
    a=l['runs']['R1']['records'][0]['attempts'][0];p=a['validator_report']['path'];v=json.loads((b/p).read_text());v['checks']['response_schema']=False
    a['validator_report']=write_ref(b,p,encoded(v))

def falsify_validator_binding(g,l,b):
    a=l['runs']['R1']['records'][0]['attempts'][0];p=a['validator_report']['path'];v=json.loads((b/p).read_text());v['exact_request_sha256']='0'*64
    a['validator_report']=write_ref(b,p,encoded(v))

def verify_preparation():
    seal=json.loads((SOURCE/'preparation-seal.json').read_text());items=seal['files'];assert len(items)==651
    paths={x['path'] for x in items};assert len(paths)==651
    current={p.relative_to(SOURCE).as_posix() for p in SOURCE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='preparation-seal.json' and not p.name.startswith('.')}
    assert current==paths
    for x in items:
        raw=(SOURCE/x['path']).read_bytes();assert sha(raw)==x['sha256'] and len(raw)==x['bytes'],x['path']
    sources=seal['read_only_method_sources'];assert len(sources)==2
    allowed=[SOURCE.parent.parent/'06-coding/llm-protocol-sol/稳定性与运行封存预设.md',SOURCE.parent.parent/'02-methods/prospective-statistical-contract-v2/validation-design-v2.json']
    assert {x['path'] for x in sources}=={str(x.resolve()) for x in allowed}
    for x in sources:
        raw=Path(x['path']).read_bytes();assert sha(raw)==x['sha256'] and len(raw)==x['bytes']
    tree=ast.parse((SOURCE/'test_stability_engine.py').read_text());tests=[n.name for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]
    assert len(tests)==22
    return {'prepared_files_hashed':651,'method_sources_hashed':2,'candidate_test_methods_count':22,'candidate_seal_self_excluded':True,'ignored_scope':seal['ignored']}

def prepare_type_counterexamples(engine_path):
    for name in ['census-boolean-pi','retry-policy-json-type']:
        folder,reg,led=clone(name)
        if name=='census-boolean-pi':
            reg['sample'].update(selection_mode='census',weight_kind='equal')
            for rec in reg['sample']['assigned_records']:rec['weight']=1;rec['inclusion_probability']=True
            complete_rebind(reg,led)
        else:
            reg['retry_policy'].update(max_actual_attempts=3.0,semantic_null_stops_retry=1,same_exact_request_only=1)
        seal_inputs(folder,reg,led)
        proc,out=cli(engine_path,folder,'originalbugoutput/'+name)
        assert proc.returncode==0,proc.stderr
        verify_analysis_seal(out,folder,engine_path)

def prepare_boundaries(engine_path):
    folder,reg,led=clone('bound-external-quote-assertion')
    row=led['runs']['R1']['records'][0];a=row['attempts'][0];obj=json.loads((folder/a['raw_response']['path']).read_text())
    obj['evidence']['S']=[{'CTXID':'NONEXISTENT-CONSTRUCTED-CTX','quote':'This invented string is absent from every source.'}]
    update_raw(folder,reg,row,a,obj);seal_inputs(folder,reg,led)
    proc,out=cli(engine_path,folder,'boundary-originaloutput/external-quote-not-rechecked');assert proc.returncode==0,proc.stderr
    verify_analysis_seal(out,folder,engine_path)
    folder,reg,led=clone('source-first-closure-not-implemented')
    rec=reg['sample']['assigned_records'][0];ref=rec['material']['source_packet'];packet=json.loads((folder/ref['path']).read_text())
    packet['assignedID']='FOREIGN-CONSTRUCTED-ID';packet['prior_model_labels']=dict.fromkeys(DIMS,0)
    rec['material']['source_packet']=write_ref(folder,ref['path'],encoded(packet));rec['material']['source_semantic_sha256']=objsha(packet)
    prompt=json.loads((folder/reg['common_artifacts']['prompt']['artifact']['path']).read_text());manual=(folder/reg['common_artifacts']['manual']['artifact']['path']).read_bytes()
    for run in RUNS:
        binding=reg['conditions'][run]['requests'][rec['assignedID']]
        binding['source_semantic_sha256']=objsha(packet)
        binding['exact_request']=write_ref(folder,binding['exact_request']['path'],make_request(reg,prompt,manual,packet,run))
        for a in led['runs'][run]['records'][0]['attempts']:
            if a['validator_report']:
                v=json.loads((folder/a['validator_report']['path']).read_text());v['exact_request_sha256']=binding['exact_request']['sha256']
                a['validator_report']=write_ref(folder,a['validator_report']['path'],encoded(v))
    complete_rebind(reg,led);seal_inputs(folder,reg,led)
    proc,out=cli(engine_path,folder,'boundary-originaloutput/source-first-not-certified');assert proc.returncode==0,proc.stderr
    verify_analysis_seal(out,folder,engine_path)
    facts={'external_quote_counterexample':'Bound assertions accepted; engine does not independently verify the invented nonexistent quote/CTX. This matches its disclosed trust boundary.',
           'source_first_counterexample':'Opaque resealed source JSON can contain a foreign source assignedID and invented prior-model-label metadata. No frozen recursive pure-source adapter/prevalidation report is implemented by this statistics contract.',
           'native_batch_contract':'Not implemented; per-record request/response bindings do not bind the complete batch response bytes, extraction path or delivery history.',
           'formal_stability_or_production_eligibility_proven':False,'true_model_dispatches':0}
    (BASE/'acceptance-boundaries.json').write_bytes(encoded(facts))

if __name__=='__main__':
    raise SystemExit(main())
