"""One sealed development cohort execution; no labels/audits as inference input.

The production adapter's unchanged protocol/receipt helpers are used only for
finite source-consumption checks. This driver has no production/acceptance role.
"""
import argparse,copy,datetime,hashlib,json,os,sys,traceback,types
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
NAMES=('source_packet','source_receipts','evidence','relations','dimensions')
def cj(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def bind(p):
    p=Path(p).resolve();raw=p.read_bytes()
    return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def verify(b):
    if bind(b['path'])!=b:raise ValueError('sealed file changed: '+b['path'])
def save(path,v):
    with Path(path).open('x',encoding='utf8')as f:f.write(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def jsonl(path,v):
    with Path(path).open('x',encoding='utf8')as f:
        for row in v:f.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+'\n')
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def main(scope_path,output_path):
    scope_path=Path(scope_path).resolve();scope=json.loads(scope_path.read_bytes());out=Path(output_path).resolve()
    if scope['execution_purpose']!='disclosed_AI_development_only' or scope['expected_record_N'] not in (77,800):
        raise ValueError('not the explicitly authorized development scope')
    if scope['maximum_actual_cohort_runs']!=1 or out.exists():raise ValueError('one-run directory already exists or wrong scope')
    for bound in scope['code_bindings']+[scope['manual'],scope['source_packet'],scope['source_package_seal']]:verify(bound)
    bundles=[json.loads(line)for line in Path(scope['source_packet']['path']).read_text().splitlines()if line]
    ids=[b['source_record']['id']for b in bundles]
    if ids!=scope['approved_record_ids'] or len(set(ids))!=len(ids) or len(ids)!=scope['expected_record_N']:
        raise ValueError('development record scope differs')
    out.mkdir(exist_ok=False)
    save(out/'launch-committed.json',{'status':'one_development_execution_committed','started_at_utc':now(),
       'scope_binding':bind(scope_path),'driver_binding':bind(__file__),'formal_execution':False,
       'human_reference_N':0,'independent_validation':False,'maximum_actual_cohort_runs':1})
    modules={};expected={Path(b['path']).stem:b for b in scope['code_bindings']}
    for name in NAMES:
        bound=expected[name];module=types.ModuleType(name);module.__file__=bound['path'];sys.modules[name]=module
        exec(compile(Path(bound['path']).read_bytes(),bound['path'],'exec'),module.__dict__);modules[name]=module
    import rule_driver as receipt_helpers
    receipt_helpers.VERSION='rule-v20-disclosed-AI-development-only'
    protocol=receipt_helpers.finite_protocol(modules['source_packet'],bundles,scope['material_bindings'],scope)
    predictions=[];consumption=[];units=[];errors=[]
    # The runtime cannot read audit decisions, calibration judgments, LLM
    # outputs, workbooks, or the new projection candidate. IDs are administrative.
    allowed={str(Path(b['path']).resolve())for b in scope['code_bindings']+scope['material_bindings']+[scope['source_packet'],scope['manual'],scope['source_package_seal']]}
    allowed.add(str(scope_path));allowed.add(str(Path(receipt_helpers.__file__).resolve()))
    allowed.add(str((HERE/'interface_common.py').resolve()))
    actual_reads=set();actual_writes=set()
    def audit(event,args):
        if event!='open' or not args or not isinstance(args[0],(str,bytes,os.PathLike)):return
        p=Path(args[0]).resolve();mode=args[1]if len(args)>1 else None;flags=args[2]if len(args)>2 else 0
        writing=(isinstance(mode,str)and any(x in mode for x in 'wax+'))or(isinstance(flags,int)and bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)))
        if writing:
            if not p.is_relative_to(out):raise PermissionError('development write outside new run directory: '+str(p))
            actual_writes.add(str(p));return
        if str(p) not in allowed and not p.is_relative_to(out) and not p.is_relative_to(Path(sys.base_prefix).resolve()):
            raise PermissionError('development read outside sealed source/code: '+str(p))
        actual_reads.add(str(p))
    sys.addaudithook(audit)
    for bundle in bundles:
        rid=bundle['source_record']['id'];view=None;source_log=None;source_check=None
        row={'id':rid,'labels':None,'decisions':None,'implementation_errors':[],
             'bundle_canonical_sha256':hashlib.sha256(cj(bundle).encode()).hexdigest(),
             'identity':'AI rule candidate; disclosed development; not human or independent truth'}
        try:
            unit=modules['source_packet'].semantic_unit(bundle);view=modules['relations'].RelationView(unit)
            decisions=modules['dimensions'].judge(view);modules['evidence'].validate_decisions(unit,decisions)
            row['candidate_decisions_diagnostic_only']=copy.deepcopy(decisions)
            source_log,source_check=receipt_helpers.actual_reading_log(protocol,bundle,view,out.name)
            if source_check['errors']:raise ValueError('source protocol errors: '+cj(source_check['errors']))
            if any(x in source_check['dependency_stop_reasons']for x in ('required_view_not_read','scope_boundary_unknown','read_delivery_incomplete')):
                raise ValueError('incomplete necessary source consumption: '+cj(source_check['dependency_stop_reasons']))
            row.update(labels={d:decisions[d]['value']for d in modules['dimensions'].DIMENSIONS},decisions=decisions,
                relation_traces=view.traces(),material_requests=view.material_requests,source_requests=view.source_requests,
                source_dependency_stop_reasons=source_check['dependency_stop_reasons'])
            units.append({'id':rid,'semantic_unit':unit})
            consumption.append({'id':rid,'actual_source_view_events':view.source_view_events,
                'source_relation_traces':view.traces(),'uniform_source_reading_log':source_log,
                'uniform_source_protocol_check':source_check,'image_pixel_reads':0,
                'new_projection_candidate_used':False})
        except Exception as error:
            issue={'id':rid,'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()};errors.append(issue)
            row['implementation_errors'].append(issue)
            consumption.append({'id':rid,'technical_failure':issue,
                'source_view_events':getattr(view,'source_view_events',[]),
                'source_relation_traces':view.traces()if view else [],'source_requests':getattr(view,'source_requests',[]),
                'material_requests':getattr(view,'material_requests',[]),'source_log':source_log,'source_check':source_check})
        predictions.append(row)
    jsonl(out/'predictions.jsonl',predictions);jsonl(out/'delivered-complete-source-bundles.jsonl',bundles)
    jsonl(out/'actual-source-consumption.jsonl',consumption);jsonl(out/'effective-semantic-units.jsonl',units)
    save(out/'technical-failures.json',errors)
    save(out/'runtime-file-access.json',{'actual_read_paths':sorted(actual_reads),'actual_write_paths':sorted(actual_writes),
         'reference_or_LLM_inputs_permitted':False,'new_projection_candidate_permitted':False})
    summary={'status':'completed_with_preserved_failures'if errors else 'completed',
       'finished_at_utc':now(),'record_N':len(predictions),'dimension_N':5*len(predictions),
       'technical_failure_record_N':len(errors),'null_dimension_N':sum(p['labels'][d]is None for p in predictions if p['labels']is not None for d in p['labels']),
       'source_input_unchanged':True,'new_material_projection_consumed':False,
       'actual_cohort_runs':1,'retry_attempted':False,'formal_accuracy_or_independent_validation':False,
       'scope_binding':bind(scope_path),'code_bindings':scope['code_bindings'],'manual_binding':scope['manual']}
    save(out/'execution.json',summary)
    save(out/'output-bindings.json',[bind(out/n)for n in ['predictions.jsonl','delivered-complete-source-bundles.jsonl','actual-source-consumption.jsonl','effective-semantic-units.jsonl','technical-failures.json','runtime-file-access.json','execution.json','launch-committed.json']])
    print(json.dumps({k:v for k,v in summary.items()if k not in {'code_bindings','scope_binding','manual_binding'}},ensure_ascii=False))
    return bool(errors)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--scope',required=True);parser.add_argument('--out',required=True);args=parser.parse_args()
    raise SystemExit(main(args.scope,args.out))
