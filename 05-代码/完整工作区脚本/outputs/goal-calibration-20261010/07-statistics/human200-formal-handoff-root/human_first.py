"""Reviewed real200 A/B originals -> human_first statistics, no automatic reference.

The review must come from actual user execution evidence. This program checks
its binding and scope; JSON flags and SHA256 cannot authenticate people.
"""
import argparse
import hashlib
import importlib.util
import json
from datetime import datetime,timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
RECEIVER=ROOT/'05-validation/human200-reception-root'
ENGINE=ROOT/'07-statistics/prospective-engine-domain-sol/metrics_engine.py'
DIMS=('S','E','Ec','I','F')


def require(ok,message):
    if not ok:raise ValueError(message)


def binding(path):
    path=path.resolve();raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def verify(b):
    path=Path(b['path']).resolve()
    require(binding(path)==b,'Frozen binding mismatch: '+str(path))
    return path


def read_json(p):return json.loads(p.read_text())


def reviewed_receive(directory,review_path):
    # Read the actual review first, before opening any human label ledger.
    review=read_json(review_path)
    require(review.get('status')=='ROOT_reviewed_actual_human200_initial_submissions','Missing actual200 human execution review')
    require(review.get('control_or_synthetic') is False,'Controls cannot become human execution')
    require(review.get('independent_initial_before_discussion') is True,'Initial independent execution has not been established')
    require(review.get('machine_answers_used') is False and review.get('AI_substitution_used') is False,'Actual human independence is not established')
    require(review.get('sample_records_per_coder')==200,'Review is for a different sample size')
    identities=review.get('human_identity_codes',{})
    require(all(isinstance(identities.get(s),str) and identities[s].strip() for s in ['A','B']) and identities['A']!=identities['B'],'Two distinct actual human identity codes required')
    evidence=review.get('actual_user_confirmation',{})
    require(evidence.get('source_kind')=='direct_user_confirmation' and isinstance(evidence.get('statement'),str) and evidence['statement'].strip(),'Actual user confirmation must be cited; do not invent it')
    directory=directory.resolve()
    require(directory.is_relative_to(RECEIVER) and directory!=RECEIVER,'Use an actual reception directory under the200 receiver')
    seal_path=directory/'seal.json'
    require(review.get('receive_seal_binding')==binding(seal_path),'Review does not bind this actual receive seal')
    seal=read_json(seal_path)
    require(seal.get('mode')=='receive','A dry-run cannot enter real statistics')
    require(seal.get('receiver_bindings')==binding(RECEIVER/'bindings.json'),'Reception used different receiver bindings')
    inventory={}
    for item in seal['output_members']:
        path=verify(item)
        require(path.is_relative_to(directory),'Reception member outside its archived directory')
        relative=str(path.relative_to(directory))
        require(relative not in inventory,'Duplicate reception member')
        inventory[relative]=item
    current={str(p.relative_to(directory)) for p in directory.rglob('*') if p.is_file() and p!=seal_path}
    require(current==set(inventory),'Reception seal does not cover its full stored output')
    report=read_json(directory/'report.json')
    require(report.get('mode')=='receive' and report.get('alignment_withheld_due_to_content_errors') is False,'Invalid content cannot enter formal statistics')
    for side in ['A','B']:
        sr=report['sides'][side]
        require(sr.get('content_valid') is True and sr.get('fully_completed') is True and sr.get('issues')==[],'Independent judgment content remains incomplete: '+side)
        require(sr.get('expected_rows')==1000 and sr.get('expected_blind_ids')==200,'Wrong issued row/ID shape')
        require(sum(sr['counts'].get(s,0) for s in ['filled','lawful_null'])==1000,'Finished judgments do not cover all assigned slots')
        archived=verify(sr['archived_original'])
        require(archived==directory/('original-'+side+'.xlsx'),'Unexpected archived original path')
        require(review.get('original_submission_bindings',{}).get(side)==binding(archived),'Execution review does not bind actual original bytes')
        require(sr['input']['sha256']==sr['archived_original']['sha256'],'Original reception copy differs')
    return review,report,seal


def project_records(directory,review,report):
    b=read_json(RECEIVER/'bindings.json')
    for key in ['vendor','code','draw','workbook_manifest','materials']:verify(b[key])
    draw=read_json(verify(b['draw']))['records']
    manifest=read_json(verify(b['workbook_manifest']))
    materials=read_json(verify(b['materials']))['pages']
    spec=importlib.util.spec_from_file_location('_reviewed200_source_reader',verify(b['vendor']))
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    method_cells={}
    for side in ['A','B']:
        raw=(directory/('original-'+side+'.xlsx')).read_bytes()
        template=helper.read_xlsx(verify(b['template_inputs'][side]).read_bytes())['独立初判']['cells']
        bundle={p['blind_id']:p['source_bundle_sha256'] for p in materials if p['side']==side}
        control={'spec':{'worksheet':'独立初判'},'cells':template,'source':set(bundle),'bundle':bundle,'bids':set(bundle)}
        checked,derived=helper.inspect(side,raw,control)
        require(checked.get('content_valid') is True and checked.get('fully_completed') is True,'Re-read of original disagrees with admitted content')
        saved=[json.loads(line) for line in (directory/('derived-'+side+'.jsonl')).read_text().splitlines()]
        require(derived==saved,'Stored derivation differs from exact original re-read')
        method_cells[side]={(x['blind_id'],x['dimension']):x for x in derived}
        require(len(method_cells[side])==1000,'Duplicate normalized source/dimension')
    records=[]
    for row in draw:
        outputs={}
        for side in ['A','B']:
            labels={}
            for dim in DIMS:
                cell=method_cells[side][row[side+'_blind_id'],dim]
                status,value=cell['completion_status'],cell['value']
                require(status in ['filled','lawful_null'],'Unfinished state in complete handoff')
                require((status=='filled' and type(value) is int and value in [0,1]) or (status=='lawful_null' and value is None),'Normalized labels must be integer0/1 or explicit lawful NULL')
                labels[dim]=value
            outputs[side]={'status':'completed','labels':labels}
        records.append({'unit_id':row['source_id'],'stratum_id':row['stratum'],'department':row['department'],'outputs':outputs})
    require(len(records)==200 and len({x['unit_id'] for x in records})==200,'Assigned200 records not preserved')
    prepared=read_json(RECEIVER/'statistics-input.UNFILLED.template.json')['metadata']
    prepared['analysis_stage']='human_first'
    frame=read_json(ROOT/'06-coding/native-full4481-v1-sol/run-manifest.json')['ordered_source_ids']
    canonical=lambda value:hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    require(len(frame)==4481 and len(set(frame))==4481,'Current full source frame mismatch')
    prepared['scope']['frame_ids_sha256']=canonical(sorted(frame))
    prepared['identities']={s:{'kind':'human','verified':True,'independent_initial':True,'identity_code':review['human_identity_codes'][s]} for s in ['A','B']}
    prepared['identities']['reference']={}
    # These are actual user attestations, not cryptographic authentication.
    prepared['identity_and_source_evidence_reviewed']=True
    prepared['freeze_attestations']['common_manual']=True
    prepared['freeze_attestations']['common_materials']=True
    prepared['freeze_attestations']['design_before_answers']=True
    prepared['freeze_attestations']['initial_submissions_before_discussion']=True
    for side in ['A','B']:
        prepared['input_seals'][side]={'sealed':True,'sha256':binding(directory/('original-'+side+'.xlsx'))['sha256'],
            'joined_projection_sha256':canonical([{'unit_id':r['unit_id'],'output':r['outputs'][side]} for r in sorted(records,key=lambda x:x['unit_id'])])}
    # No reference/rule/LLM results or their completion are invented here.
    prepared['artifact_seals']['common_manual']={'sealed':True,'sha256':manifest['workbooks'][0]['manual']['sha256']}
    require(review.get('common_manual_sha256')==manifest['workbooks'][0]['manual']['sha256'],'User execution review refers to a different common manual')
    prepared['artifact_seals']['common_materials']={'sealed':True,'sha256':b['materials']['sha256']}
    prepared['artifact_seals']['design']={'sealed':True,'sha256':b['draw']['sha256']}
    return {'data_role':'sealed_project','metadata':prepared,'records':records}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--receive-dir',type=Path,required=True)
    p.add_argument('--review',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    args=p.parse_args()
    contract=read_json(HERE/'bindings.json')
    verify(contract['code']);verify(contract['engine']);verify(contract['receiver_bindings'])
    verify(contract['manual']);verify(contract['production_manifest'])
    verify(contract['statistics_template']);verify(contract['assigned_design_metadata'])
    output=args.output_dir.resolve()
    require(output.is_relative_to(HERE) and output!=HERE and not output.exists(),'Use a new output directory under this handoff')
    review,report,seal=reviewed_receive(args.receive_dir,args.review)
    payload=project_records(args.receive_dir,review,report)
    spec=importlib.util.spec_from_file_location('_registered200_human_first_engine',verify(contract['engine']))
    engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
    engine.prepare(payload)
    result=engine.analyze(payload,replicates=5000,seed=20261010,guard_mode='single_category')
    output.mkdir(parents=True,exist_ok=False)
    for name,value in [('bound-statistical-input.json',payload),('human-first-results.json',result)]:
        with (output/name).open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
    receipt={'at_utc':datetime.now(timezone.utc).isoformat(),'analysis_stage':'human_first','review':binding(args.review),
        'receive_seal':binding(args.receive_dir/'seal.json'),'engine':contract['engine'],'code':contract['code'],
        'A_B_identity_evidence_is_actual_user_attestation_not_crypto_authentication':True,
        'independent_human_adjudication_reference_created':False,'machine_accuracy_or_annual_conclusions_computed':False,
        'project_overall_acceptance_claimed':False,'members':[binding(x) for x in sorted(output.iterdir()) if x.is_file()]}
    with (output/'seal.json').open('x') as f:json.dump(receipt,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'status':'actual_reviewed200_human_first_calculated','rows':200,'replicates':5000,'project_overall_acceptance':False},ensure_ascii=False))


if __name__=='__main__':main()
