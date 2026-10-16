"""Replace only the superseded external terminal prerequisite; inner actors stay frozen."""
import argparse, datetime, json, sys, types
from pathlib import Path
sys.dont_write_bytecode=True
import terminal_common as c

def go_outer(path, fresh):
    go=c.load(path)
    assert go.get('template_only') is False and go.get('fixture_only') is not True,'Template/fixture cannot authorize execution'
    assert go['authorized_successor_outer_entrypoint']==c.bind(__file__)
    assert go['successor_compatibility_seal']==c.bind(c.HERE/'seal.json')
    terminal=c.verify_certificate(go['production_terminal_certificate'],fresh)
    assert datetime.datetime.fromisoformat(go['at_utc'])>=datetime.datetime.fromisoformat(terminal['at_utc'])
    return go,terminal
def run_native(go_path):
    go,terminal=go_outer(go_path,True)
    assert go.get('author')=='ROOT' and go.get('execution_authorized') is True
    core=types.ModuleType('unchanged_native0216_core');core.__file__=str(c.N/'runner.py')
    exec(compile((c.N/'runner.py').read_bytes(),core.__file__,'exec'),core.__dict__)
    def revised_check(path,m):
        actual,cert=go_outer(path,True)
        assert actual['author']=='ROOT' and actual['execution_authorized'] is True
        assert actual['run_id']==m['run_id'] and actual['authorized_entrypoint']==c.bind(__file__)
        assert actual['preparation_seal']==c.bind(c.N/'preparation-seal.json')
        assert actual['native_v15_full_collection_seal']==cert['native_full_collection_seal']
        assert actual.get('single_transport_owner') is True and actual.get('live_cli_pids')==[]
        return actual
    core.check_go=revised_check
    sys.argv=[core.__file__,'--mode','run','--go',str(go_path)];core.main()
def run_stability(go_path):
    go,_=go_outer(go_path,True)
    sys.path.insert(0,str(c.ST));import capacity13_common as common
    old_validate=common.validate_GO
    def revised_validate(run,d,path):
        go_outer(path,False) # Own future parallel stability children are not old production children.
        return old_validate(run,d,path)
    common.validate_GO=revised_validate
    import bootstrap
    controller,_,_=bootstrap.runtime();doc=common.profile()
    print(json.dumps(controller.execute(Path(doc['base_campaign_manifest']['path']).parent,go_path),ensure_ascii=False))
def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['preflight','certificate','run'],required=True);p.add_argument('--target',choices=['native0216','stability13']);p.add_argument('--go');p.add_argument('--request');p.add_argument('--output');x=p.parse_args()
    c.assert_preparation()
    if x.mode=='preflight':
        print(json.dumps({'state':'prepared_not_executed','model_calls':0,'classifier_calls':0,'signals_sent_N':0,'old_v4_complete_replaced_only_in_outer_terminal_prerequisite':True,'actual_full_collector_and_new13_terminal_and_ROOT_GO_still_required':True}));return
    if x.mode=='certificate':
        assert x.request and x.output;print(json.dumps(c.create_certificate(x.request,x.output),ensure_ascii=False));return
    assert x.go and x.target,'No actual ROOT GO: no dispatch'
    if x.target=='native0216':run_native(x.go)
    else:run_stability(x.go)
if __name__=='__main__':main()
