"""Execute four presealed hidden synthetic cases once after ROOT final binding."""
import hashlib
import json
import os
import sys
import traceback
from pathlib import Path

D=Path(__file__).resolve().parent
PREP=D.parent
ROOT=Path('/Users/rainbow/Desktop/战略院/药企项目-创新药')
BASE=ROOT/'outputs/goal-calibration-20261010'
CODE=BASE/'06-coding/rule-five-dimension-joint-root/versions/joint-v5-primary-standard-bridge-sol'
PREPSHA='74491ccf70822fc36b8426d0fb13c5f2b337cc9d7dd2bc36ef86435b128a941d'
PRESHA='4f8ae9d0a3eb116dd3cd6b44bd8355683b08a54921ee1a6739aff0b609dc3cae'
ALGSHA='5f9d780b4a72779f69e91082881109f65aa8adc6395ebf94b061bd207e0d14bf'

def canonical(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def sha(b):return hashlib.sha256(b).hexdigest()
def bind(p):
    b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':sha(b)}
def write(name,value):
    p=D/name
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf8') as f:
        f.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n');f.flush();os.fsync(f.fileno())
def append_result(value):
    with (D/'execution-results.jsonl').open('a',encoding='utf8') as f:
        f.write(json.dumps(value,ensure_ascii=False)+'\n');f.flush();os.fsync(f.fileno())

def main():
    if (D/'execution-started.json').exists():raise RuntimeError('Once-only execution already started; do not retry')
    assert bind(PREP/'preparation-seal.json')['sha256']==PREPSHA
    assert bind(CODE/'pre-execution-seal.json')['sha256']==PRESHA
    assert bind(CODE/'algorithm-bindings.json')['sha256']==ALGSHA
    prep=json.loads((PREP/'preparation-seal.json').read_bytes())
    for item in prep['members']+prep['inputs']:assert bind(Path(item['path']))==item
    pre=json.loads((CODE/'pre-execution-seal.json').read_bytes())
    alg=json.loads((CODE/'algorithm-bindings.json').read_bytes())
    assert pre['five_modules']==alg['five_modules']
    assert pre['post_independent_algorithm_edit_allowed'] is False
    assert alg['code_will_not_change_after_new_results'] is True
    inputs=[bind(PREP/'preparation-seal.json'),bind(CODE/'pre-execution-seal.json'),bind(CODE/'algorithm-bindings.json')]
    for item in pre['five_modules']+[pre['manual']]+pre['common_frozen_input_bindings']:
        assert bind(Path(item['path']))==item;inputs.append(item)
    fixed=json.loads((PREP/'coordinator-private/fixed-controls-before-final-code.json').read_bytes())
    assert len(fixed)==4 and len({x['case_id'] for x in fixed})==4
    for item in fixed:
        assert item['dimension']=='S' and item['other_dimension_expectations'] is None
        assert bind(Path(item['source_packet']['path']))==item['source_packet']
        assert bind(Path(item['source_text']['path']))==item['source_text']
        inputs.extend([item['source_packet'],item['source_text']])
    write('execution-started.json',{'authority':'ROOT explicitly authorized four hidden presealed controls each once with final v5',
        'preparation_sha256':PREPSHA,'pre_execution_sha256':PRESHA,'algorithm_bindings_sha256':ALGSHA,
        'synthetic_only':True,'case_count':4,'retries_allowed':False,
        'input_expectations_or_closure_flags_injected':False,'new_real_human_results':0})
    sys.dont_write_bytecode=True;sys.path.insert(0,str(CODE))
    import source_packet,relations,dimensions,evidence,source_receipts
    results=[]
    for control in fixed:
        cid=control['case_id'];calls={'semantic_unit':0,'RelationView':0,'judge':0}
        unit=view=decisions=None
        result={'case_id':cid,'fixed_control':control,'calls':calls,'stage':'not_started',
            'execution_error':None,'mechanical_error':None,'synthetic_only':True,'new_human_result':False,
            'other_dimension_expectations':None,'retry_count':0}
        write('attempts/'+cid+'.json',{'case_id':cid,'status':'single_attempt_started','no_retry':True})
        packet=json.loads(Path(control['source_packet']['path']).read_bytes());bundle=packet['source_bundle']
        assert packet['source_bundle_sha256']==sha(canonical(bundle).encode())
        original=canonical(bundle)
        try:
            result['stage']='semantic_unit';calls['semantic_unit']+=1
            unit=source_packet.semantic_unit(bundle)
            assert canonical(bundle)==original
            write('semantic-units/'+cid+'.json',unit)
            result['stage']='RelationView';calls['RelationView']+=1
            view=relations.RelationView(unit)
            result['stage']='judge';calls['judge']+=1
            decisions=dimensions.judge(view)
            result.update(stage='completed_once',decisions=decisions,
                observed_values_only={d:x['value'] for d,x in decisions.items()},
                actual_S=decisions['S']['value'],expected_S=control['expected_value'],
                matches_fixed_S_expectation=decisions['S']['value']==control['expected_value'])
        except Exception as exc:
            result['execution_error']={'type':type(exc).__name__,'message':str(exc),
                'stage':result['stage'],'traceback':traceback.format_exc()}
        if view is not None:
            result['trace']={'relations':view.traces(),'material_requests':view.material_requests,
                'source_requests':view.source_requests,'source_view_events':view.source_view_events,
                'source_relation_traces':view.source_relation_traces,'structural_address_issues':view.structural_address_issues,
                'source_scope_review':view.source_scope_review}
        if decisions is not None:
            try:
                evidence.validate_decisions(unit,decisions)
                result['evidence_validate_decisions']='passed_without_label_mutation'
                inventory=source_packet.source_inventory(bundle)
                resolved,deltas=source_receipts.resolve_inventory(bundle,inventory,[],D)
                assert not deltas and resolved==inventory
                result.update(producer_inventory=inventory,resolved_inventory=resolved,identity_deltas=deltas)
                byid={x['context_id']:x for x in unit['contexts']};checks=[]
                def check_quote(q,path):
                    c=byid[q['context_id']]
                    assert q['text']==c['text'][q['start']:q['end']] and q['source_ref']==c['source_ref']
                    check={'path':path,'context_id':q['context_id'],'literal_quote_and_source_ref_verified':True}
                    loc=c['source_ref'].get('locator',{})
                    if c['kind']=='source_textleaf':
                        p=Path(loc['snapshot_absolute_path']);raw=p.read_bytes();text=raw.decode('utf8')
                        assert sha(raw)==c['source_ref']['sha256']==loc['snapshot_sha256']
                        a,b=loc['unicode_code_point_interval_half_open']
                        assert text[a:b]==c['text']
                        start,end=a+q['start'],a+q['end'];assert text[start:end]==q['text']
                        check.update(original_file=bind(p),actual_codepoint_interval=[start,end],
                            actual_utf8_interval=[len(text[:start].encode()),len(text[:end].encode())],
                            actual_start_line_1based=text[:start].count('\n')+1,
                            original_literal_bytes_verified=True)
                    checks.append(check)
                for dim,decision in decisions.items():
                    for key in ['current_anchor','current_proposition']:
                        q=decision[key]
                        if q is not None:
                            assert q['text']==unit['text'][q['start']:q['end']]
                            checks.append({'path':'decisions/'+dim+'/'+key,'literal_current_verified':True})
                    for i,q in enumerate(decision['context_evidence']):check_quote(q,'decisions/'+dim+'/context_evidence/'+str(i))
                for i,r in enumerate(view.traces()):
                    for j,q in enumerate(r['context_evidence']):check_quote(q,'relations/'+str(i)+'/context_evidence/'+str(j))
                    for j,q in enumerate(r.get('details',{}).get('closure_proof',{}).get('boundary_quotes',[])):
                        check_quote(q,'relations/'+str(i)+'/closure_proof/boundary_quotes/'+str(j))
                inv={x['resource_id']:x for x in resolved}
                for i,event in enumerate(view.source_view_events):
                    r=inv[event['resource_id']]
                    assert r['source_sha256']==event['source_sha256'] and r['available_views'][event['view']]==event['view_sha256']
                    checks.append({'path':'source_view_events/'+str(i),'resource_id':event['resource_id'],
                        'actual_source_and_view_sha_verified':True})
                result['readback_checks']=checks
            except Exception as exc:
                result['mechanical_error']={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
        write('results/'+cid+'.json',result);append_result(result);results.append(result)
        print(json.dumps({'case_id':cid,'actual_S':result.get('actual_S'),'expected_S':control['expected_value'],
            'match':result.get('matches_fixed_S_expectation'),'execution_error':result['execution_error'] is not None,
            'mechanical_error':result['mechanical_error'] is not None},ensure_ascii=False),flush=True)
    for item in inputs+prep['members']+prep['inputs']:assert bind(Path(item['path']))==item
    write('input-bindings.json',inputs)
    write('execution-results.json',results)
    summary={'identity':'four hidden synthetic source-only independent development controls; not formal accuracy',
        'case_count':4,'first_results_only':True,
        'actual_S':[r.get('actual_S') for r in results],'fixed_expected_S':[r['fixed_control']['expected_value'] for r in results],
        'matches':sum(bool(r.get('matches_fixed_S_expectation')) for r in results),
        'execution_errors':sum(r['execution_error'] is not None for r in results),
        'mechanical_errors':sum(r['mechanical_error'] is not None for r in results),
        'calls':{name:sum(r['calls'][name] for r in results) for name in ['semantic_unit','RelationView','judge']},
        'fixture_coverage_note':'Two paired contrasts share the same complete operative baseline; four frozen packet identities, three distinct current/source-text combinations. Do not interpret duplicate baseline as independent empirical accuracy.',
        'actual_policy_IDs_read_or_added':0,'new_real_human_results':0,'formal_metrics':0,
        'preparation_and_code_bindings_unchanged':True,'retry_count':0}
    write('execution-summary.json',summary);print(json.dumps(summary,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
