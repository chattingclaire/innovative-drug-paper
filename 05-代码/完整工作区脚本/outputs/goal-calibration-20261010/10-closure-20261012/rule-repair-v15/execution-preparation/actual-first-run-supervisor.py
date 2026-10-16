"""Reuse actual Popen.wait once; requires a real externally released scope."""
import argparse,importlib.util,json,os,sys
from pathlib import Path
sys.dont_write_bytecode=True
from merge_common import bind,exact,load
from scope_contract import contract,driver_argv,require,validate_full_scope

def main():
    p=argparse.ArgumentParser();p.add_argument('--scope',required=True);p.add_argument('--scope-sha256',required=True);a=p.parse_args()
    sb=bind(a.scope);require(sb['sha256']==a.scope_sha256,'actual scope SHA differs')
    scope=load(a.scope);validate_full_scope(scope);c=contract()
    require(os.getsid(0)==os.getpid(),'Start supervisor in a detached session')
    require(Path(sys.executable).resolve()==Path(c['python_executable']).resolve(),'Use frozen Python launcher')
    require(not Path(scope['output_directory']).exists() and not Path(scope['wait_directory']).exists(),'actual first attempt already exists; no restart/reset')
    hb=c['wait_helper'];exact(hb)
    spec=importlib.util.spec_from_file_location('bound_actual_wait',hb['path']);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    result=m.wait_and_seal(driver_argv(a.scope,scope),scope['wait_directory'],{
      'purpose':'single_actual_rule_full4481_v17_execution','ROOT_release':scope['release'],
      'frozen_scope':sb,'helper':hb,'supervisor':bind(__file__),'no_automatic_restart':True})
    if not result['actual_wait_returned'] or result['launch_or_supervision_error'] is not None:return 1
    return result['returncode'] if result['returncode']>=0 else 128-result['returncode']

if __name__=='__main__':raise SystemExit(main())
