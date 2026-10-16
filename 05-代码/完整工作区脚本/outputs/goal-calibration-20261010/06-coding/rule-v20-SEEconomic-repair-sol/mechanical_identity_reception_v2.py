"""No judge call: receive original785 and already saved identity-replayed15."""
import copy,hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
from development_driver import verify,cj,write,binding
from source_packet import semantic_unit,source_inventory
from source_receipts import resolve_inventory
from evidence import validate_decisions
HERE=Path(__file__).resolve().parent


def main():
    s=json.loads((HERE/'technical15-scope.json').read_text())
    oldscope=json.loads(verify(s['original_scope']))
    original=[json.loads(x) for x in verify(s['original_predictions']).decode().splitlines()]
    replay_path=HERE/'development800-identity-reception/predictions.jsonl'
    replay_binding=binding(replay_path);replay={x['id']:x for x in map(json.loads,verify(replay_binding).decode().splitlines())}
    failed=s['failed_ID_order'];out=HERE/'development800-identity-reception-v2';out.mkdir(exist_ok=False)
    for b in s['code']+s['identity_material_bindings']+[s['manual']]:verify(b)
    bundles={}
    for material in oldscope['material_files']:
        b=json.loads(verify(material));bundles[b['source_record']['id']]=b
    checks=[];accepted=[]
    with (out/'predictions.jsonl').open('x',encoding='utf8') as stream:
        for old in original:
            rid=old['id'];row=copy.deepcopy(replay[rid] if rid in failed else old);bundle=bundles[rid]
            if row['decisions'] is None or row['labels'] is None:raise ValueError('no complete existing saved prediction '+rid)
            validate_decisions(semantic_unit(bundle),row['decisions'])
            raw=source_inventory(bundle);inventory=raw;deltas=[]
            if rid in failed:
                if not any(x.get('source_sha256') is None and x['resource_id'].startswith('FULLSOURCE-') for x in raw):
                    raise ValueError('technical repair not an original missingSHA')
                inventory,deltas=resolve_inventory(bundle,raw,s['identity_material_bindings'],s['source_base'])
                expected=copy.deepcopy(raw)
                for delta in deltas:
                    if delta['field']!='source_sha256' or delta['producer_value'] is not None or delta['read_use_status_changed']:
                        raise ValueError('nonidentity delta')
                    next(x for x in expected if x['resource_id']==delta['resource_id'])['source_sha256']=delta['resolved_value']
                if expected!=inventory:raise ValueError('bridge modifies otherfields')
            indexed={(x['resource_id'],k):(x['source_sha256'],v) for x in inventory for k,v in x['available_views'].items()}
            events=row['source_view_events']
            for event in events:
                if indexed.get((event['resource_id'],event['view']))!=(event['source_sha256'],event['view_sha256']):raise ValueError('source event mismatch '+rid)
            predecessor=replay[rid] if rid in failed else old
            if row['decisions']!=predecessor['decisions'] or row['labels']!=predecessor['labels']:raise ValueError('prediction semantics changed')
            row['mechanical_reception_v2']={'no_judge_called':True,'original785_retained':rid not in failed,
                'saved_15_technical_prediction_reused':rid in failed,'identity_only_deltas':deltas,
                'original_producer_inventory_unchanged':raw==source_inventory(bundle),'all_runtime_view_bindings_passed':True,
                'predecessor_decisions_sha256':hashlib.sha256(cj(predecessor['decisions']).encode()).hexdigest(),
                'accepted_decisions_sha256':hashlib.sha256(cj(row['decisions']).encode()).hexdigest()}
            stream.write(json.dumps(row,ensure_ascii=False)+'\n');stream.flush();accepted.append(row)
            checks.append({'id':rid,**row['mechanical_reception_v2'],'event_N':len(events)})
    for b in s['code']+s['identity_material_bindings']+[s['manual'],s['original_predictions'],s['original_scope'],replay_binding]+oldscope['material_files']:verify(b)
    write(out/'acceptance-checks.json',checks)
    write(out/'reception-summary.json',{'covered_N':800,'original785_no_semantic_replay':785,'saved15_reused_no_extra_semantic_replay':15,
        'remaining_technical_failure_N':0,'semantic_calls_in_this_receiver':0,'original_source_and_five_modules_unchanged':True,
        'declared_predecessor_bindings':[s['original_predictions'],replay_binding],'is_formal_validation':False,'is_human_reference':False,
        'prior785plus15_and_failed_reception_preserved':True,'repair_scope':'only original missing source_pdf_sha256 bridge'} )
    print('800 accepted mechanically; 785 original retained; saved15 reused; no judge called.')


if __name__=='__main__':main()
