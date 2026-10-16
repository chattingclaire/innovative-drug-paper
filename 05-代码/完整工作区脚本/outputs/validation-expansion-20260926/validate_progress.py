"""Administrative progress QA only; emits no labels, disagreements or performance."""
from pathlib import Path
import argparse,hashlib,json,re
from datetime import datetime
from holdout_results import read_json,validate_result
OUT=Path(__file__).parent
parser=argparse.ArgumentParser()
parser.add_argument('--phase',choices=('H600','R200'),default='H600')
args=parser.parse_args()
phase_root=OUT/args.phase
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
freeze=read_json((OUT/'最终冻结清单.json').read_bytes(),'freeze')
assert sha(OUT/'holdout_results.py')==freeze['files']['holdout_results']['sha256']
seal=read_json((phase_root/'封存信息.json').read_bytes(),'seal')
assert seal['release_status']=='ready_for_blind_review'
assert seal['freeze_manifest_sha256']==sha(OUT/'最终冻结清单.json')
prior_path=phase_root/'独立提交接收登记.json'
prior=read_json(prior_path.read_bytes(),'prior') if prior_path.exists() else {'submissions':{}}
records=dict(prior['submissions']);summary={};errors=[]
for coder in 'AC':
    directory=phase_root/f'agent-{coder}';count=0;batches=[]
    assert sha(directory/'五维共用编码协议.md')==freeze['files']['protocol']['sha256']
    for p in sorted(directory.glob('结果-*.json')):
        try:
            m=re.fullmatch(r'结果-(\d{2})\.json',p.name)
            if not m:raise ValueError('Unexpected result filename')
            batch=int(m.group(1));material=directory/f'材料-{batch:02d}.json'
            assert sha(material)==seal['output_files'][str(material.relative_to(phase_root))]
            result=read_json(p.read_bytes(),str(p));packet=read_json(material.read_bytes(),str(material))
            validate_result(result,coder,freeze['protocol_version'],packet,sha(material),str(p))
            relative=str(p.relative_to(phase_root));digest=sha(p)
            if relative in records and records[relative]['sha256']!=digest:raise ValueError('Previously received raw submission changed')
            records[relative]={'sha256':digest,'rows':len(result['rows']),'completed_at':result['completed_at'],'input_packet_sha256':sha(material)}
            count+=len(result['rows']);batches.append(batch)
        except Exception as exc:errors.append({'coder':coder,'file':p.name,'issue':str(exc)})
    summary[coder]={'validated_batches':batches,'validated_rows':count}
if not errors:
    prior_path.write_text(json.dumps({'status':'administrative_progress_only_no_performance_evaluated','checked_at':datetime.now().astimezone().isoformat(),'submissions':records,'summary':summary},ensure_ascii=False,indent=2))
print(json.dumps({'phase':args.phase,'summary':summary,'structural_errors':errors,'performance_computed':False},ensure_ascii=False))
