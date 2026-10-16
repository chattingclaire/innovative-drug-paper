"""Identity-only reception of first replay; only failed 15 need semantic replay."""
import copy, hashlib,json,sys,traceback
from pathlib import Path
sys.dont_write_bytecode=True
from development_driver import binding,verify,cj,write
from source_packet import semantic_unit,source_inventory
from source_receipts import resolve_inventory
from relations import RelationView
from dimensions import judge
from evidence import validate_decisions
HERE=Path(__file__).resolve().parent


def main():
    scope=HERE/'technical15-scope.json';s=json.loads(scope.read_text());out=Path(s['output_directory']);out.mkdir(exist_ok=False)
    for b in s['code']+s['identity_material_bindings']+[s['original_predictions'],s['original_scope'],s['manual']]:verify(b)
    oldscope=json.loads(verify(s['original_scope']));oldrows=[json.loads(x) for x in verify(s['original_predictions']).decode().splitlines()]
    by_id={x['id']:x for x in oldrows}
    failed=[x['id'] for x in oldrows if x['status']=='technical_failure']
    if failed!=s['failed_ID_order'] or len(failed)!=15:raise ValueError('not the original exact 15 technical failures')
    bundles={}
    for material in oldscope['material_files']:
        b=json.loads(verify(material));bundles[b['source_record']['id']]=b
    evidence=[];success=[];errors=[];semantics_unchanged=[]
    with (out/'predictions.jsonl').open('x',encoding='utf8') as stream:
        for ordinal,old in enumerate(oldrows,1):
            rid=old['id'];b=bundles[rid];row=copy.deepcopy(old)
            try:
                raw=source_inventory(b)
                resolved,delta=resolve_inventory(b,raw,s['identity_material_bindings'],s['source_base'])
                edited=copy.deepcopy(raw)
                for item in delta:
                    if item['field']!='source_sha256' or item['producer_value'] is not None or not item['producer_inventory_retained_unchanged'] or item['read_use_status_changed']:
                        raise ValueError('bridge changes exceed identity-only repair')
                    target=next(x for x in edited if x['resource_id']==item['resource_id']);target['source_sha256']=item['resolved_value']
                if edited!=resolved or raw!=source_inventory(b):raise ValueError('producer inventory or other field changed')
                u=semantic_unit(b)
                if rid in failed:
                    v=RelationView(u);d=judge(v);validate_decisions(u,d)
                    row.update(labels={key:x['value'] for key,x in d.items()},decisions=d,
                        status='candidate_executed_after_identity_only_technical_replay',source_view_events=v.source_view_events,
                        source_relation_traces=v.traces(),source_requests=v.source_requests,
                        source_current_full_text_consumed=u['text'],source_current_exact_binding=u['text']==b['source_record']['text'],
                        original_failure_preserved_in_first_run=old['error'],semantic_replay_ordinal=failed.index(rid)+1)
                    row.pop('error',None);row.pop('traceback',None);row.pop('error_type',None)
                else:
                    # No semantic function is called for these 785 predictions.
                    validate_decisions(u,row['decisions'])
                    semantics_unchanged.append({'id':rid,'original_decisions_sha256':hashlib.sha256(cj(old['decisions']).encode()).hexdigest(),
                        'reception_decisions_sha256':hashlib.sha256(cj(row['decisions']).encode()).hexdigest(),'no_semantic_replay':True})
                indexed={(x['resource_id'],k):(x['source_sha256'],v) for x in resolved for k,v in x['available_views'].items()}
                checks=[]
                for event in row['source_view_events']:
                    expected=indexed.get((event['resource_id'],event['view']));actual=(event['source_sha256'],event['view_sha256'])
                    checks.append({'resource_id':event['resource_id'],'view':event['view'],'exact_original_view_binding_after_identity_bridge':expected==actual,
                        'expected':expected,'actual':actual})
                if any(not x['exact_original_view_binding_after_identity_bridge'] for x in checks):raise ValueError('other runtime view mismatch retained as failure')
                row['identity_only_reception']={'original_producer_inventory_unchanged':True,'deltas':delta,'checks':checks,
                    'labels_read_as_target':False,'semantic_modules_unchanged':True,'not_formal_acceptance':True}
                success.append(rid);evidence.append({'id':rid,'semantic_replay':rid in failed,'identity_deltas':delta,'check_N':len(checks)})
            except Exception as exc:
                row.update(status='technical_failure',error=str(exc),error_type=type(exc).__name__,traceback=traceback.format_exc())
                errors.append({'id':rid,'error':str(exc)})
            stream.write(json.dumps(row,ensure_ascii=False)+'\n');stream.flush()
    for b in s['code']+s['identity_material_bindings']+[s['original_predictions'],s['original_scope'],s['manual']]+oldscope['material_files']:verify(b)
    write(out/'identity-reception.json',evidence);write(out/'785-no-semantic-replay-proof.json',semantics_unchanged)
    summary={'covered_N':len(oldrows),'identity_checks_passed_N':len(success),'remaining_technical_failures':errors,
        'semantic_replay_N':15,'original_success_N_not_replayed':len(semantics_unchanged),
        'source_manual_five_modules_unchanged':True,'repair_scope':'frozen source_receipts.resolve_inventory only; existing source_pdf_sha256 identity mapping',
        'formal_validation_complete':False,'human_reference':False,'original_first_run_unchanged':True,'all_attempts_preserved':True}
    write(out/'reception-summary.json',summary);print(json.dumps(summary,ensure_ascii=False))


if __name__=='__main__':main()
