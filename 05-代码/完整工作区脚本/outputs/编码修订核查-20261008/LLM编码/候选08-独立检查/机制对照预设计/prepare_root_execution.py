"""Offline preparation only. Does not invoke CLI, model, or modify prior freezes."""
import ast, hashlib, importlib.util, json, shutil
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
DEST = BASE / 'root_execution_preparation'
OLD = BASE.parents[1] / '候选08-命题与证据判定'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def bind(p): return {'path':str(p.resolve()),'sha256':sha(p),'bytes':p.stat().st_size}
def write(p, obj): p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')

def main():
    assert not DEST.exists(), 'preparation immutable; inspect existing result instead of rerunning'
    manifest = json.loads((BASE/'mechanism_design_manifest_PROPOSED.json').read_text())
    plan = json.loads((BASE/'mechanism_contrast_plan_PROPOSED_PRIVATE.json').read_text())
    assert sha(BASE/'mechanism_design_manifest_PROPOSED.json') == 'be8252943ca9dc0e01a9e2dc87310b1aa15444048ef50b55efc284f02977e00e'
    for b in [manifest['plan'],manifest['private_expected_controls'],*manifest['input_files'],*manifest['source_bindings']]:
        assert sha(Path(b['path'])) == b['sha256'], b['path']
    promptp = OLD/'candidate08_prompt_PROPOSED.txt'
    prompt = promptp.read_text()
    assert sha(promptp) == 'd79c097443fa249051c5264da1ff532ddf7d984225ac3e776807de95f7f21803'
    runnerp = OLD/'runtime-unchanged-v2/run_production_v32.py'
    tree = ast.parse(runnerp.read_text())
    request_exprs = [n.value for n in ast.walk(tree) if isinstance(n,ast.Assign)
                     and any(isinstance(t,ast.Name) and t.id=='request' for t in n.targets)]
    assert len(request_exprs)==1
    request_code = compile(ast.Expression(request_exprs[0]),str(runnerp),'eval')
    DEST.mkdir()
    runtime = DEST/'runtime';runtime.mkdir()
    for name in ['run_production_v32.py','validate_binary_output.py','output_schema_codex_compatible.json']:
        shutil.copyfile(OLD/'runtime-unchanged-v2'/name,runtime/name)
        assert (runtime/name).read_bytes()==(OLD/'runtime-unchanged-v2'/name).read_bytes()
    spec=importlib.util.spec_from_file_location('frozen_runner_offline',runtime/'run_production_v32.py')
    runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
    all_normalized=[];arms=[]
    for arm in plan['proposed_arms']:
        ap=Path(arm['input_binding']['path']);packet=json.loads(ap.read_text())
        rows=packet['rows'];runner.no_reference_fields(rows)
        assert [r['id'] for r in rows]==plan['design']['same_ids_and_same_base_order_in_every_request']
        normalized=[]
        for r in rows:
            assert list(r)==(['id','contexts','text'] if arm['requested_row_serialization']=='before_text' else ['id','text','contexts'])
            assert set(r['contexts'])=={arm['field_key']}
            context=r['contexts'][arm['field_key']]
            assert len(context)==1 and context[0]['source_position']=='following_adjacent'
            assert set(context[0])=={'source_position','text'}
            normalized.append({'id':r['id'],'text':r['text'],'context':context})
        all_normalized.append(normalized)
        ad=DEST/'offline_requests'/arm['arm'];ad.mkdir(parents=True)
        write(ad/'input_packet.json',packet)
        request=eval(request_code,{'prompt':prompt,'packet':packet,'json':json})
        assert request.startswith(prompt+'\n\n--- 本批冻结盲法输入 ---\n')
        (ad/'request.txt').write_text(request)
        args=['--input',str(ap),'--expected-input-sha256',sha(ap),'--prompt',str(promptp),
              '--expected-n','5','--run-name',arm['arm'],'--batch-size','25','--workers','1',
              '--max-attempts','3','--timeout-seconds','1800','--purpose',
              'Predeclared representation diagnostic; no candidate selection or external-validity claim']
        arms.append({'arm':arm['arm'],'field_key':arm['field_key'],
                     'requested_row_serialization':arm['requested_row_serialization'],
                     'input':bind(ap),'offline_packet':bind(ad/'input_packet.json'),
                     'offline_request':bind(ad/'request.txt'),'runner_arguments':args})
    assert all(x==all_normalized[0] for x in all_normalized)
    for i,j in [(0,1),(2,3)]:
        a=Path(arms[i]['offline_request']['path']).read_text()
        b=Path(arms[j]['offline_request']['path']).read_text()
        prefix=len(prompt)
        assert a[:prefix]==b[:prefix]
        assert a[prefix:].replace('"structured_following_units"','"provided_context_units"')==b[prefix:]
    final={'status':'FINAL_DIAGNOSTIC_DESIGN_FROZEN_NOT_YET_AUTHORIZED',
           'created_at_UTC':datetime.now(timezone.utc).isoformat(),
           'purpose':'Resolve an untested input-representation hypothesis after faithful local request/output trace; not a new coding candidate',
           'root_semantic_review_before_output':'Root read all five bases, four hard label vectors and one unscored boundary after original08 prompt freeze; concurs with four hard-case definitions. Prompt author has not received new originals or expectations.',
           'original08_status':'FAIL_CONFIRMED_SEMANTIC_ERROR',
           'model':'gpt-5.6-sol','reasoning_effort':'medium',
           'arms':arms,'logical_requests':4,'maximum_identical_technical_attempts':12,
           'execution_order':[a['arm'] for a in arms],
           'retry_policy':'Only frozen-runner execution/structure/literal/tool failures; first valid; no semantic retries, winner choice, or label edits',
           'stop_policy':'Only technical exhaustion stops unstarted arms; semantic errors are diagnostic outcomes and all four arms are retained',
           'all_original_text_and_context_equal_after_only_field_normalization':True,
           'exact_request_formula_compiled_from_verified_frozen_runner':True,
           'analysis_and_limits_source':bind(BASE/'mechanism_contrast_plan_PROPOSED_PRIVATE.json'),
           'expectations_private_binding':manifest['private_expected_controls'],
           'no_test_of_production_typed_branches':True,
           'not_external_human_validation':True,'no_new_kappa_or_distribution_estimation':True,
           'no_adoption_or_original08_continuation_authorized':True}
    write(DEST/'final_execution_plan.json',final)
    files=[p for p in DEST.rglob('*') if p.is_file() and '__pycache__' not in str(p)]
    files += [Path(__file__),BASE/'execute_root_diagnostic.py',promptp,
              BASE/'mechanism_design_manifest_PROPOSED.json',
              BASE/'mechanism_contrast_plan_PROPOSED_PRIVATE.json',
              BASE/'five_new_bases_FULL5_EXPECTATIONS_PRIVATE_FROZEN.json']
    write(DEST/'preparation_freeze.json',{'status':'OFFLINE_PREPARATION_COMPLETE_ZERO_MODEL_CALLS',
          'files':[bind(p) for p in sorted(set(files))],'model_calls':0,
          'authorization_required':'root_execution_authorization.json separate after independent preflight'})
    print(json.dumps({'status':'prepared_offline_zero_calls','freeze':bind(DEST/'preparation_freeze.json'),
                      'plan':bind(DEST/'final_execution_plan.json'),'arms':4,'rows':20},ensure_ascii=False))

if __name__=='__main__':main()
