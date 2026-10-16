"""Preserve returned200 A/B originals and inspect content; never compute scores."""
import argparse
import hashlib
import importlib.util
import json
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent


def binding(path):
    raw=path.read_bytes()
    return {'path':str(path.resolve()),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def verify(b):
    p=Path(b['path'])
    if binding(p)!=b:raise ValueError('Frozen input binding mismatch: '+str(p))
    return p


def put_json(path,data):
    with path.open('x') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--A',type=Path);parser.add_argument('--B',type=Path)
    parser.add_argument('--mode',choices=['dry-run','receive'],required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    b=json.loads((HERE/'bindings.json').read_text())
    for key in ['vendor','code','draw','workbook_manifest','materials']:verify(b[key])
    for entry in b['template_inputs'].values():verify(entry)
    for entry in b['source_helpers']:verify(entry)
    spec=importlib.util.spec_from_file_location('_bound200_xlsx_reader',verify(b['vendor']))
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    manifest=json.loads(verify(b['workbook_manifest']).read_text())
    pages=json.loads(verify(b['materials']).read_text())['pages']
    draw=json.loads(verify(b['draw']).read_text())['records']
    output=args.output_dir.resolve()
    if not output.is_relative_to(HERE) or output==HERE:raise ValueError('Use a new output child of this200 receiver')
    output.mkdir(parents=True,exist_ok=False)
    reports={};normalized={};inputs={}
    for side in ['A','B']:
        provided=getattr(args,side)
        if provided is None:
            reports[side]={'side':side,'status':'not_submitted','expected_rows':1000,'expected_blind_ids':200,
                'fully_completed':False,'content_valid':False,'actual_human_execution_verified':False}
            normalized[side]=[];continue
        raw=provided.read_bytes()
        archived=output/('original-'+side+'.xlsx')
        with archived.open('xb') as f:f.write(raw)
        actual=binding(provided.resolve());saved=binding(archived)
        if actual['sha256']!=saved['sha256'] or actual['bytes']!=saved['bytes']:raise ValueError('Original copy mismatch')
        inputs[side]={'input':actual,'archived_original':saved}
        issued=next(w for w in manifest['workbooks'] if w['side']==side)
        template=helper.read_xlsx(verify(b['template_inputs'][side]).read_bytes())['独立初判']['cells']
        bundle={p['blind_id']:p['source_bundle_sha256'] for p in pages if p['side']==side}
        data={'spec':{'worksheet':'独立初判'},'cells':template,'source':set(bundle),'bundle':bundle,'bids':set(bundle)}
        report,rows=helper.inspect(side,raw,data)
        report.setdefault('fully_completed',False)
        report.setdefault('fully_filled',False)
        report.update(inputs[side])
        report.update(actual_human_execution_verified=False,human_independence_not_inferred_from_xlsx=True,
            qualification_status='actual_user_execution_evidence_pending',actual_mode=args.mode)
        reports[side]=report;normalized[side]=rows
        with (output/('derived-'+side+'.jsonl')).open('x') as f:
            for row in rows:f.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+'\n')
    valid=all(reports[s].get('content_valid') is True for s in ['A','B'])
    alignment=[]
    if valid:
        sides={s:{(x['blind_id'],x['dimension']):x for x in normalized[s]} for s in ['A','B']}
        for record in draw:
            for dim in helper.DIMS:
                pair={s:sides[s][record[s+'_blind_id'],dim] for s in ['A','B']}
                pending=any(x['completion_status'] not in ['filled','lawful_null'] for x in pair.values())
                has_null=any(x['completion_status']=='lawful_null' for x in pair.values())
                status='pending' if pending else 'lawful_null' if has_null else 'agreement' if pair['A']['value']==pair['B']['value'] else 'disagreement'
                alignment.append({'source_id':record['source_id'],'dimension':dim,'status':status,
                    'values':{s:pair[s]['value'] for s in ['A','B']},'source_rows':{s:pair[s]['row'] for s in ['A','B']},
                    'pairwise_binary_agreement':status=='agreement','is_adjudicated_reference':False})
        with (output/'alignment.jsonl').open('x') as f:
            for row in alignment:f.write(json.dumps(row,ensure_ascii=False)+'\n')
    report={'status':'originals_preserved_content_inspected','at_utc':datetime.now(timezone.utc).isoformat(),
        'mode':args.mode,'sides':reports,'alignment_withheld_due_to_content_errors':not valid,
        'alignment_counts':dict(Counter(x['status'] for x in alignment)),
        'human_identity_or_independence_authenticated':False,'formal_analysis_admitted':False,
        'actual_human_execution_evidence_review_required':True,'formal_numeric_results_generated':0,
        'A_B_agreement_automatically_used_as_reference':False,'dry_run_is_not_actual_human_submission':args.mode=='dry-run'}
    put_json(output/'report.json',report)
    put_json(output/'seal.json',{'inputs':inputs,'receiver_bindings':binding(HERE/'bindings.json'),
        'output_members':[binding(p) for p in sorted(output.iterdir()) if p.is_file()],
        'mode':args.mode,'original_byte_copies_verified':True,'formal_numeric_results_generated':0})
    print(json.dumps({'mode':args.mode,'counts':{s:reports[s].get('counts',{}) for s in ['A','B']},
        'fully_completed':{s:reports[s]['fully_completed'] for s in ['A','B']},
        'alignment_counts':report['alignment_counts'],'formal_analysis_admitted':False},ensure_ascii=False))


if __name__=='__main__':main()
