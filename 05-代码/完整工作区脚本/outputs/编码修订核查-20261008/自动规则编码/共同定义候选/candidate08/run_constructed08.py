"""Predeclared candidate08 constructions and bounded07/06 regressions only."""
import argparse
import ast
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNTIME = HERE / "runtime"
sys.dont_write_bytecode = True
sys.path.insert(0, str(RUNTIME))
import policy_coding_v27 as coder

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

# Reuse only already reviewed synthetic source writer / offset checks. Do not
# execute its imports or main (which would select the older runtime).
fixture_path = HERE.parent / "candidate07/independent_review07/run_independent07.py"
tree = ast.parse(fixture_path.read_text(encoding="utf-8"))
defs = [node for node in tree.body if isinstance(node, ast.FunctionDef)
        and node.name in {"prose", "verify_offsets"}]
exec(compile(ast.fix_missing_locations(ast.Module(body=defs, type_ignores=[])), str(fixture_path), "exec"))

def run(phase):
    design_path = HERE/"constructed_design08.json"
    design = json.loads(design_path.read_text(encoding="utf-8"))
    extra = json.loads((HERE/"constructed_design08_addendum01.json").read_text(encoding="utf-8"))
    polarity = json.loads((HERE/"constructed_design08_addendum02.json").read_text(encoding="utf-8")) if (HERE/"constructed_design08_addendum02.json").exists() else {"checks":[]}
    if phase == "before-polarity":new_cases=polarity["checks"]
    elif phase == "delivery":new_cases=design["checks"]+extra["checks"]+polarity["checks"]
    else:new_cases = extra["checks"] if phase == "before-addendum" else design["checks"] + (extra["checks"] if phase == "after" else [])
    old_design = json.loads(Path(design["regressions"][0]["path"]).read_text(encoding="utf-8"))
    code_before = {str(p):sha(p) for p in sorted(RUNTIME.glob("*.py"))}
    checks = []
    with tempfile.TemporaryDirectory(prefix="candidate08-invented-real-source-") as tmp:
        groups = [("new08",new_cases)]
        if phase not in ("before-addendum","before-polarity"):groups.append(("independent07",old_design["cases"]))
        for group, cases in groups:
            for i, case in enumerate(cases):
                record = prose(Path(tmp)/f"{group}-{i}", case["text"], case["prefix"])
                if case.get("expected_source_error"):
                    Path(record["source"]).write_text(case["text"],encoding="utf-8")
                    record["source_sha256"]=record["unit_source_sha256"]=sha(record["source"])
                original=copy.deepcopy(record)
                result,error=None,None
                try:result=coder.code_unit(record)
                except Exception as exc:error={"type":type(exc).__name__,"message":str(exc)}
                technical=verify_offsets(record,result) if result else None
                if case.get("expected_source_error"):
                    passed=bool(error and error["type"]=="ValueError" and result is None and record==original)
                else:
                    passed=bool(not error and record==original and technical["passed"] and all(
                        result["labels"][d]==v for d,v in case["expected"].items()))
                checks.append({"group":group,"name":case["name"],"expected":case["expected"],
                    "expected_source_error":case.get("expected_source_error",False),"passed":passed,
                    "actual_labels":result["labels"] if result else None,"error":error,
                    "technical":technical,"input_unchanged":record==original,
                    "source_sha256":sha(record["source"]),"candidate_sha256":sha(record["candidate_file"]),"prediction":result})
    regressions=[]
    if phase in ("after","delivery"):
        for filename in ("selftest_common_scope07.py","selftest_common_final06.py"):
            result=subprocess.run([sys.executable,"-B",str(RUNTIME/filename)],cwd=HERE,capture_output=True,text=True)
            payload=json.loads(result.stdout) if result.returncode==0 else None
            record={"suite":filename,"exit_code":result.returncode,"stderr":result.stderr,"stdout":payload,
                    "stdout_sha256":hashlib.sha256(result.stdout.encode()).hexdigest(),
                    "purpose":"Bounded mechanical author-suite regression; not independent validity."}
            suffix="_delivery" if phase=="delivery" else ""
            target=HERE/(filename.removesuffix('.py')+"_regression08"+suffix+".json")
            with target.open('x',encoding='utf-8') as f:json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n')
            regressions.append({"suite":filename,"path":str(target),"sha256":sha(target),"exit_code":result.returncode,
                "passed":payload.get('passed') if payload else False,
                "case_n":payload.get('case_n',payload.get('check_n')) if payload else None})
    code_after={str(p):sha(p) for p in sorted(RUNTIME.glob('*.py'))}
    preserve=json.loads((HERE/'candidate07_preserved_before08.json').read_text())['files']
    unchanged={p:sha(p)==h for p,h in preserve.items()}
    return {'schema_version':'constructed08-actual-v1','phase':phase,'at_utc':datetime.now(timezone.utc).isoformat(),
        'design_sha256':sha(design_path),'fixture_code_sha256':sha(fixture_path),'runner_sha256':sha(__file__),
        'runtime_version':coder.VERSION,'checks':checks,'failures':[{'group':c['group'],'name':c['name']} for c in checks if not c['passed']],
        'new_case_n':len(new_cases),'new_pass_n':sum(c['passed'] for c in checks if c['group']=='new08'),
        'independent07_case_n':sum(c['group']=='independent07' for c in checks),'independent07_pass_n':sum(c['passed'] for c in checks if c['group']=='independent07'),
        'author_regressions':regressions,'code_sha256_before':code_before,'code_sha256_after':code_after,
        'code_unchanged_during_execution':code_before==code_after,'candidate07_file_n':len(unchanged),
        'candidate07_existing_files_all_unchanged':all(unchanged.values()),
        'all_passed':all(c['passed'] for c in checks) and all(c['passed'] for c in regressions),
        'scope':{'actual_temporary_txt_json':True,'authenticator_mocked':False,'real21_33_full':False,
                 'real_policy_or_reference_labels_read':False,'model_called':False}}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=('before','before-addendum','after','before-polarity','delivery'),required=True)
    phase=parser.parse_args().phase
    result=run(phase);path=HERE/f'constructed_execution08_{phase}.json'
    with path.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({k:result[k] for k in ('phase','new_case_n','new_pass_n','independent07_case_n','independent07_pass_n','failures','author_regressions','code_unchanged_during_execution','candidate07_existing_files_all_unchanged')},ensure_ascii=False))
    print(json.dumps({'path':str(path),'sha256':sha(path)},ensure_ascii=False))
