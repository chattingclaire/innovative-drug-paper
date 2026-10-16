"""ROOT-authorized once-only historical S3 source-only development execution."""
from __future__ import annotations
import hashlib
import json
import sys
import traceback
from pathlib import Path

ROOT=Path('/Users/rainbow/Desktop/战略院/药企项目-创新药')
BASE=ROOT/'outputs/goal-calibration-20261010'
CODE=BASE/'06-coding/rule-five-dimension-joint-root/versions/joint-v4-structure-normalization-sol'
PLAN=BASE/'08-audits/common-candidate-actual-interface-sol/historical-human-S3-development-plan'
D=Path(__file__).resolve().parent
IDS=['RECODE25-00036','RECODE25-00038','RECODE25-00045']
PRESHA='d3eb4a895f1154173488eac32366f86a47687c9935716eb50876f3ba9a5670e0'
ALGSHA='45c33b4eb89e3a263a36560515617f1884f91c13e988777881675b7119e8a54b'
PLANSHA='e791c3183117c5d2c427788b818febf6df0faa2c6c99d3d2f73206690f4b185b'

def bind(p):
    b=p.read_bytes()
    return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}

def write(name,value):
    p=D/name
    if p.exists(): raise RuntimeError('Once-only output already exists: '+str(p))
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def canonical(v):
    return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'))

def main():
    if (D/'execution-started.json').exists():
        raise RuntimeError('This authorized execution has already started; no retry permitted')
    assert bind(CODE/'pre-execution-seal.json')['sha256']==PRESHA
    assert bind(CODE/'algorithm-bindings.json')['sha256']==ALGSHA
    assert bind(PLAN/'output-seal.json')['sha256']==PLANSHA
    pre=json.loads((CODE/'pre-execution-seal.json').read_bytes())
    algorithm=json.loads((CODE/'algorithm-bindings.json').read_bytes())
    assert pre['five_modules']==algorithm['five_modules']
    inputs=[bind(CODE/'pre-execution-seal.json'),bind(CODE/'algorithm-bindings.json'),bind(PLAN/'output-seal.json')]
    for item in pre['five_modules']+[pre['manual']]+pre['common_frozen_input_bindings']:
        assert bind(Path(item['path']))==item
        inputs.append(item)
    planseal=json.loads((PLAN/'output-seal.json').read_bytes())
    for item in planseal['members']+planseal['inputs']:
        assert bind(Path(item['path']))==item
    assert pre['post_independent_result_mutation_allowed'] is False
    fixed=json.loads((PLAN/'fixed-S3-before-execution.json').read_bytes())
    assert [(x['record_id'],x['dimension'],x['expected_value']) for x in fixed]==[(rid,'S',1) for rid in IDS]
    sourcebindings=[]
    for item in fixed:
        p=Path(item['frozen_source_packet_copy']['path'])
        assert bind(p)==item['frozen_source_packet_copy']
        sourcebindings.append(bind(p))
    # Classification modules receive the exact source bundle only. The fixed
    # expectations and historical workbook values do not enter consumer input.
    write('execution-started.json',{'authority':'Explicit ROOT message authorizes sealed v4 and exactly three once-only historical S cases',
        'algorithm_preseal_sha256':PRESHA,'algorithm_bindings_sha256':ALGSHA,'plan_seal_sha256':PLANSHA,
        'case_ids':IDS,'source_bindings':sourcebindings,'per_case_limits':{'semantic_unit':1,'RelationView':1,'judge':1},
        'real_new_human_results':0,'formal_evaluation':False,'new_policy_ids':0,'retry_allowed':False})
    sys.dont_write_bytecode=True
    sys.path.insert(0,str(CODE))
    import source_packet
    import relations
    import dimensions
    import evidence
    import source_receipts
    results=[]
    for expected in fixed:
        rid=expected['record_id']
        counts={'semantic_unit':0,'RelationView':0,'judge':0}
        unit=view=decisions=None
        result={'record_id':rid,'dimension_with_fixed_expectation':'S','expected_S':1,
            'identity':'nonhuman rule output; comparison to existing historical human development adjudication',
            'source_packet':expected['frozen_source_packet_copy'],'source_bundle_sha256':expected['source_bundle_sha256'],
            'stage':'not_started','calls':counts,'execution_error':None,'mechanical_validation_error':None,
            'formal_accuracy_claim':False,'new_real_human_result':False}
        raw=json.loads(Path(expected['frozen_source_packet_copy']['path']).read_bytes())
        bundle=raw['source_bundle']
        assert hashlib.sha256(canonical(bundle).encode()).hexdigest()==expected['source_bundle_sha256']
        assert bundle['source_record']['id']==rid
        write('attempts/'+rid+'.json',{'record_id':rid,'status':'single_attempt_started','retry_allowed':False})
        try:
            result['stage']='semantic_unit';counts['semantic_unit']+=1
            unit=source_packet.semantic_unit(bundle)
            write('semantic-units/'+rid+'.json',unit)
            result['stage']='RelationView';counts['RelationView']+=1
            view=relations.RelationView(unit)
            result['stage']='judge';counts['judge']+=1
            decisions=dimensions.judge(view)
            result['decisions']=decisions
            result['observed_values_only']={dim:decision['value'] for dim,decision in decisions.items()}
            result['actual_S']=decisions['S']['value']
            result['matches_historical_S_expectation']=decisions['S']['value']==1
            result['stage']='completed_once'
        except Exception as exc:
            result['execution_error']={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc(),
                'stage':result['stage']}
        if view is not None:
            result['trace']={'relations':view.traces(),'material_requests':view.material_requests,
                'source_requests':view.source_requests,'source_view_events':view.source_view_events,
                'source_relation_traces':view.source_relation_traces,
                'structural_address_issues':view.structural_address_issues,
                'source_scope_review':view.source_scope_review}
        if decisions is not None:
            try:
                evidence.validate_decisions(unit,decisions)
                result['evidence_validate_decisions']='passed_without_modifying_decisions'
                inventory=source_packet.source_inventory(bundle)
                # All three original payloads are literal text leaves. The
                # frozen resolver must retain their identities unchanged.
                resolved,deltas=source_receipts.resolve_inventory(bundle,inventory,[],BASE/'00-baseline')
                result['producer_inventory']=inventory
                result['resolved_inventory']=resolved
                result['source_identity_deltas']=deltas
                checks=[]
                for dim,decision in decisions.items():
                    for label in ['current_anchor','current_proposition']:
                        anchor=decision[label]
                        if anchor is not None:
                            assert anchor['text']==unit['text'][anchor['start']:anchor['end']]
                            checks.append({'path':'decisions/'+dim+'/'+label,'literal_original_current_verified':True})
                    for i,q in enumerate(decision['context_evidence']):
                        matches=[c for c in unit['contexts'] if c['context_id']==q['context_id']]
                        assert len(matches)==1
                        c=matches[0]
                        assert q['text']==c['text'][q['start']:q['end']] and q['source_ref']==c['source_ref']
                        checks.append({'path':'decisions/'+dim+'/context_evidence/'+str(i),
                            'context_id':q['context_id'],'literal_context_verified':True,'source_ref_verified':True})
                for ri,r in enumerate(view.traces()):
                    for qi,q in enumerate(r['context_evidence']):
                        matches=[c for c in unit['contexts'] if c['context_id']==q['context_id']]
                        assert len(matches)==1
                        c=matches[0]
                        assert q['text']==c['text'][q['start']:q['end']] and q['source_ref']==c['source_ref']
                        checks.append({'path':'relations/'+str(ri)+'/context_evidence/'+str(qi),
                            'context_id':q['context_id'],'literal_context_verified':True,'source_ref_verified':True})
                byid={x['resource_id']:x for x in resolved}
                for ei,event in enumerate(view.source_view_events):
                    entry=byid[event['resource_id']]
                    assert entry['source_sha256']==event['source_sha256']
                    assert entry['available_views'][event['view']]==event['view_sha256']
                    checks.append({'path':'source_view_events/'+str(ei),'resource_id':event['resource_id'],
                        'view':event['view'],'source_and_view_sha_verified_against_original_inventory':True})
                result['mechanical_readback_checks']=checks
            except Exception as exc:
                result['mechanical_validation_error']={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
        write('execution-results/'+rid+'.json',result)
        results.append(result)
    for item in inputs+sourcebindings:
        assert bind(Path(item['path']))==item
    for item in planseal['members']+planseal['inputs']:
        assert bind(Path(item['path']))==item
    write('input-bindings.json',inputs+sourcebindings)
    write('execution-results.json',results)
    write('execution-summary.json',{'identity':'Three once-only historical development checks, not formal performance',
        'case_ids':IDS,'actual_S':[x.get('actual_S') for x in results],
        'S_expectations':[1,1,1],'S_expectation_matches':sum(x.get('matches_historical_S_expectation',False) for x in results),
        'S_NULL_count':sum('actual_S' in x and x['actual_S'] is None for x in results),
        'execution_errors':sum(x['execution_error'] is not None for x in results),
        'mechanical_validation_errors':sum(x['mechanical_validation_error'] is not None for x in results),
        'calls':{k:sum(x['calls'][k] for x in results) for k in ['semantic_unit','RelationView','judge']},
        'other_dimension_expectations_added':0,'new_real_human_results':0,'formal_metrics_created':0,
        'original_packets_plan_algorithm_manual_unchanged':True,'retry_attempts':0})
    print(json.dumps(json.loads((D/'execution-summary.json').read_text()),ensure_ascii=False))

if __name__=='__main__': main()
