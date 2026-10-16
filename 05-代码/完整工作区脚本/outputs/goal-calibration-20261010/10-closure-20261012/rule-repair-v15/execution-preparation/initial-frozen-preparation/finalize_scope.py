"""Bind an existing ROOT release; never create a release or run a coder."""
import argparse,json
from pathlib import Path
from merge_common import bind,save
from scope_contract import build_scope,require

def finalize(release_path,expected_sha,scope_output):
    b=bind(release_path);require(b['sha256']==expected_sha,'Explicit ROOT release SHA differs')
    require(Path(scope_output).resolve()!=Path(release_path).resolve(),'scope cannot replace release')
    scope=build_scope(b);save(scope_output,scope);return bind(scope_output)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--release',required=True);p.add_argument('--release-sha256',required=True);p.add_argument('--scope-out',required=True);a=p.parse_args()
    print(json.dumps(finalize(a.release,a.release_sha256,a.scope_out),ensure_ascii=False))
