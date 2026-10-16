"""Bound original protocol and audit only; no RelationView, judge or receipts."""
import ast,hashlib,json,os,sys,types
from pathlib import Path
sys.dont_write_bytecode=True
import rule_driver
from merge_common import load,bind

H=Path(__file__).resolve().parent
c=load(H/'execution-contract.json')
manifest=load(H/'algorithm-bindings.json')
source_binding=next(x for x in manifest['modules'] if x['module']=='source_packet')
source=types.ModuleType('probe_source_packet')
source.__file__=source_binding['path']
raw=Path(source.__file__).read_bytes()
assert hashlib.sha256(raw).hexdigest()==source_binding['sha256']
exec(compile(raw,source.__file__,'exec'),source.__dict__)
with open(c['source_input']['path'],'rb') as f:bundle=json.loads(next(f))
materials=load(c['source_material_bindings']['path'])['materials']+[c[k] for k in ('source_reading_protocol_code','source_input','manual')]
omitted='--omit-configuration' in sys.argv
config=c['source_protocol_configuration']
if omitted:materials=[b for b in materials if b['path']!=config['path']]
scope={'v12_source_base':c['v12_source_base'],
       'complete_bundles_canonical_sha256':c['source_input']['sha256'],
       'source_manifest_sha256':c['source_manifest']['sha256'],
       'source_packet':c['source_input'],'source_package_seal':c['source_package_seal'],
       'manual':c['manual']}
allowed={Path(b['path']).resolve() for b in materials}
allowed|={Path(x['path']).resolve() for x in manifest['modules']}
allowed|={x.resolve() for x in H.iterdir() if x.is_file()}
stdlib=Path(os.__file__).resolve().parent
out=H/'NOT_AN_EXECUTION_OUTPUT';reads=[]
driver_ast=ast.parse(Path(rule_driver.__file__).read_text())
audit_ast=next(x for x in ast.walk(driver_ast) if isinstance(x,ast.FunctionDef) and x.name=='audit')
exec(compile(ast.Module(body=[audit_ast],type_ignores=[]),rule_driver.__file__,'exec'),globals())
sys.addaudithook(audit)
try:
    protocol=rule_driver.finite_protocol(source,[bundle],materials,scope)
    log=protocol.prepare(bundle['source_record']['id'],'protocol-dependency-check-only','rule')
    check=protocol.check(log)
    assert not omitted
    assert log['protocol_sha256']==config['sha256'] and not check['errors']
    assert not log['read_receipts'] and not log['use_receipts']
    assert config['path'] in reads
    result={'status':'PASS_ORIGINAL_PROTOCOL_WITH_EXACT_AUDIT','configuration_reads':reads.count(config['path']),
            'errors':check['errors'],'expected_unread_dependency_stops':check['dependency_stop_reasons'],
            'READ_N':0,'USE_N':0,'configuration':config}
except PermissionError as error:
    assert omitted and str(error)=='unapproved read '+config['path'],str(error)
    result={'status':'PASS_REPRODUCED_ORIGINAL_MISSING_DEPENDENCY','error':str(error),'configuration':config}
result.update(classifier_calls=0,model_calls=0,actual_run_created=False,read_paths=sorted(set(reads)))
print(json.dumps(result,ensure_ascii=False))
