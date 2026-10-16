"""One preserved development replay per explicit cohort, never formal inference."""
import argparse, copy, datetime, hashlib, json, sys, traceback
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
from source_packet import semantic_unit, source_inventory
from relations import RelationView
from dimensions import judge
from evidence import validate_decisions


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def cj(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def binding(path):
    p=Path(path).resolve();return {'path':str(p),'sha256':digest(p),'bytes':p.stat().st_size}
def verify(b):
    p=Path(b['path']);raw=p.read_bytes()
    if len(raw)!=b['bytes'] or hashlib.sha256(raw).hexdigest()!=b['sha256']:raise ValueError('binding changed '+str(p))
    return raw
def write(path,x):
    with Path(path).open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--scope',required=True);ap.add_argument('--scope-sha256',required=True)
    args=ap.parse_args();scopefile=Path(args.scope).resolve()
    if digest(scopefile)!=args.scope_sha256:raise ValueError('declared scope changed')
    s=json.loads(scopefile.read_text());out=Path(s['output_directory'])
    if s['purpose']!='disclosed_development_regression_only' or s['max_runs']!=1 or s['formal_validation_complete'] or s['human_reference']:raise ValueError('development scope contract')
    out.mkdir(exist_ok=False)
    write(out/'execution-start.json',{'scope':binding(scopefile),'code':s['code'],'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'real_cohort_attempt_N':1,'formal_validation':False,'human_reference':False})
    for b in s['code']+[s['manual']]:verify(b)
    if s['manual']['sha256']!='5ea7ab74d30fb79c4cbd1d7d6b2ae40c4f52a52360075f3552199de949f9cc7b':raise ValueError('frozen common manual required')
    if 'source_packet' in s:
        bundles=[json.loads(line) for line in verify(s['source_packet']).decode('utf8').splitlines() if line.strip()]
    else:bundles=[json.loads(verify(b)) for b in s['material_files']]
    ids=[b['source_record']['id'] for b in bundles]
    if ids!=s['approved_record_ids'] or len(ids)!=s['expected_N'] or len(set(ids))!=len(ids):raise ValueError('exact finite cohort order/coverage')
    write(out/'input-bindings.json',{'scope':binding(scopefile),'manual':s['manual'],'source_packet':s.get('source_packet'),
        'material_files':s.get('material_files'),'source_bundle_canonical_sha256':hashlib.sha256(cj(bundles).encode()).hexdigest(),
        'ID_is_administrative_scope_only':True,'review_labels_read_by_inference':False})
    rows=[];failed=[];source_checks=[]
    with (out/'predictions.jsonl').open('x',encoding='utf8') as stream:
        for ordinal,bundle in enumerate(bundles,1):
            rid=bundle['source_record']['id'];unit=None;view=None
            row={'id':rid,'ordinal':ordinal,'source_bundle_sha256':hashlib.sha256(cj(bundle).encode()).hexdigest(),
                'candidate_only':True,'not_formal_or_human_validation':True,'labels':None,'decisions':None}
            try:
                unit=semantic_unit(bundle);view=RelationView(unit);decisions=judge(view);validate_decisions(unit,decisions)
                inventory=source_inventory(bundle);indexed={(x['resource_id'],k):(x['source_sha256'],v) for x in inventory for k,v in x['available_views'].items()}
                event_checks=[]
                for event in view.source_view_events:
                    expected=indexed.get((event['resource_id'],event['view']))
                    actual=(event['source_sha256'],event['view_sha256'])
                    event_checks.append({'resource_id':event['resource_id'],'view':event['view'],'exact_original_view_binding':expected==actual,
                        'delivery_inventory_expected':expected,'actual_runtime_event':actual})
                mismatches=[x for x in event_checks if not x['exact_original_view_binding']]
                if mismatches:raise ValueError('runtime source view does not match delivered inventory: '+repr(mismatches))
                row.update(labels={d:x['value'] for d,x in decisions.items()},decisions=decisions,
                    status='candidate_executed',source_view_events=view.source_view_events,
                    source_relation_traces=view.traces(),source_requests=view.source_requests,
                    source_view_binding_checks=event_checks,source_current_full_text_consumed=unit['text'],
                    source_current_exact_binding=unit['text']==bundle['source_record']['text'],
                    evidence_validation='all five dimensions exact current/quote/source_ref passed',
                    protocol_validation_claimed=False,source_protocol_note='runtime events and exact delivered inventory checked; not a renewed pixel read or independent human full-source review')
                source_checks.append({'id':rid,'current_verified':True,'event_N':len(event_checks),'all_view_bindings_passed':True})
            except Exception as exc:
                row.update(status='technical_failure',error_type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc(),
                    source_view_events=copy.deepcopy(getattr(view,'source_view_events',[])),
                    source_relation_traces=copy.deepcopy(view.traces()) if view else [],
                    source_requests=copy.deepcopy(getattr(view,'source_requests',[])))
                failed.append({'id':rid,'error':row['error']})
            stream.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+'\n');stream.flush();rows.append(row)
    for b in s['code']+[s['manual']]+s.get('material_files',[])+([s['source_packet']] if 'source_packet' in s else []):verify(b)
    summary={'cohort_N':len(rows),'unique_N':len({x['id'] for x in rows}),'technical_failure_N':len(failed),'technical_failures':failed,
        'null_dimensions':[{'id':x['id'],'dimension':d,'needed_material':x['decisions'][d]['needed_material']} for x in rows if x['decisions'] for d,v in x['labels'].items() if v is None],
        'source_check_N':len(source_checks),'runtime_source_view_event_N':sum(x['event_N'] for x in source_checks),
        'input_code_manual_unchanged_after_run':True,'formal_validation':False,'is_human_reference':False,
        'scope_completed_once':True,'all_attempts_preserved':True,'source_protocol_validation_claimed':False}
    write(out/'run-summary.json',summary);write(out/'source-checks.json',source_checks)
    print(json.dumps({key:summary[key] for key in ('cohort_N','technical_failure_N','input_code_manual_unchanged_after_run')},ensure_ascii=False))


if __name__=='__main__':main()
