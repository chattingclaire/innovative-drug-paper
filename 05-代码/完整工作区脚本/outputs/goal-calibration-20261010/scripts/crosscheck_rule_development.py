"""Independent integer/Fraction recomputation after a rule prediction seal."""
import argparse
import hashlib
import importlib.util
import json
from fractions import Fraction
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('independent_math',ROOT/'scripts/audit_pilot.py')
math=importlib.util.module_from_spec(spec);spec.loader.exec_module(math)
DIMS=('S','E','Ec','I','F')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):
    rows=[json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]
    assert len(rows)==len({r['id'] for r in rows})
    return {r['id']:r for r in rows}
def ratio(a,b):return None if not b else float(Fraction(a,b))
def main():
    parser=argparse.ArgumentParser();parser.add_argument('run',type=Path);parser.add_argument('destination',type=Path)
    parser.add_argument('--evaluation',type=Path)
    parser.add_argument('--reference',type=Path,default=ROOT/'06-coding/development-reference41-v11/reference.jsonl')
    parser.add_argument('--expected-n',type=int,default=41)
    args=parser.parse_args()
    run=args.run.resolve();seal=json.loads((run/'seal.json').read_text());dest=args.destination.resolve()
    assert seal['complete'] is True and seal['prediction_sha256']==sha(run/'predictions.jsonl')
    for entry in seal['implementation_files']:
        assert sha(entry['path'])==entry['sha256'],entry['path']
    for name in ('source','manual','fixture_manifest'):
        assert sha(seal[name+'_path'])==seal[name+'_sha256']
    assert sha(run/'freeze.json')==seal['freeze_sha256']
    assert sha(run/'execution.json')==seal['execution_sha256']
    ref_path=args.reference.resolve()
    pred=load(run/'predictions.jsonl');ref=load(ref_path)
    assert set(pred)==set(ref) and len(pred)==seal['prediction_n']==args.expected_n
    evaluation=args.evaluation.resolve() if args.evaluation else run/'evaluation'
    official=json.loads((evaluation/'metrics.json').read_text())['per_dimension']
    report={}
    for dim in DIMS:
        cells=[0,0,0,0];unknown=[]
        for ident in sorted(pred):
            a=pred[ident]['labels'][dim];b=ref[ident]['labels'][dim]
            assert a is None or type(a) is int and a in (0,1)
            assert b is None or type(b) is int and b in (0,1)
            if a is None or b is None:unknown.append({'id':ident,'prediction':a,'reference':b})
            else:cells[2*a+b]+=1
        tn,fn,fp,tp=cells
        symmetric=math.statistics(*cells)
        metric={'cohens_kappa':symmetric['kappa'],'precision':ratio(tp,tp+fp),
                'recall':ratio(tp,tp+fn),'F1':ratio(2*tp,2*tp+fp+fn),
                'specificity':ratio(tn,tn+fp),'determined_accuracy':ratio(tp+tn,sum(cells))}
        expected={'TP':tp,'FP':fp,'FN':fn,'TN':tn}
        assert expected==official[dim]['confusion_determined']
        for key,value in metric.items():
            old=official[dim][key]
            assert (value is None and old is None) or (value is not None and old is not None and abs(value-old)<1e-12),(dim,key,value,old)
        report[dim]={'four_cells':expected,'metrics':metric,'all_n':args.expected_n,'comparable_n':sum(cells),
                     'unknown':unknown,'goal_main_points':{k:metric[k] is not None and metric[k]>=.8 for k in ('cohens_kappa','precision','recall','F1')}}
    result={'identity':'automatic_rule_vs_AI_consensus_development','n':args.expected_n,'status':'independent_arithmetic_crosscheck_passed',
            'run_path':str(run),'prediction_sha256':sha(run/'predictions.jsonl'),'reference_sha256':sha(ref_path),
            'all_runtime_source_manual_and_seal_bindings_verified':True,'per_dimension':report,
            'population_CI':None,'CI_reason':'Nonprobability development fixture','human_validation':False,
            'final_acceptance':False,'no_predictions_or_reference_modified':True}
    dest.mkdir(parents=True,exist_ok=True)
    with (dest/'arithmetic-crosscheck.json').open('x') as stream:
        stream.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({d:report[d]['metrics'] for d in DIMS},ensure_ascii=False))
if __name__=='__main__':main()
