import json, hashlib, argparse
from pathlib import Path
from score_blind import DIMS, validate
BASE=Path('/Users/rainbow/Desktop/战略院/创新药论文-完整归档-20260914/12-投稿定稿工作区')
OUT=Path(__file__).parent
parser=argparse.ArgumentParser();parser.add_argument('--versions',nargs='+',default=['18','20']);parser.add_argument('--output',default='开发60-词典版本逐条对照.json');args=parser.parse_args()
target=OUT/args.output
if target.exists():raise RuntimeError('Preserve issued comparison; choose a new output file')
load=lambda p:json.loads(p.read_text())
packet=load(OUT/'开发60-共同无答案材料.json'); q={r['id']:r for r in packet['rows']}
mapping={r['blind_id']:r for r in load(OUT/'开发60-研究者映射.json')['rows']}
_,a=validate(OUT/'agent-A/result-A.json',q); _,c=validate(OUT/'agent-C/result-C.json',q)
ids=[k for k in q if all(a[k]['labels'][d] in (0,1) and c[k]['labels'][d] in (0,1) for d in DIMS)]
results={}
for version in args.versions:
    p=BASE/f'全量开发诊断-v4-development-{version}/逐单元开发编码.json'
    data=load(p); pred={r['id']:r for r in data['rows']}
    for k,m in mapping.items():
        assert pred[m['review_id']]['unit_text_sha256']==m['text_sha256'],k
    rows=[]
    for k in q:
        r=pred[mapping[k]['review_id']]
        rows.append({'id':k,'review_id':mapping[k]['review_id'],'text':q[k]['text'],'labels_A':a[k]['labels'],'labels_C':c[k]['labels'],
                     'labels_dictionary':r['labels'],'input_assessment_status':r.get('input_assessment_status'),
                     'dictionary_evidence':r['evidence'],'A_reasons':a[k]['dimension_reasons'],'C_reasons':c[k]['dimension_reasons'],
                     'both_fully_definite':k in ids,'differing_dimensions_vs_A':[d for d in DIMS if r['labels'][d]!=a[k]['labels'][d]],
                     'differing_dimensions_vs_C':[d for d in DIMS if r['labels'][d]!=c[k]['labels'][d]]})
    metrics={}
    for name,review in [('A',a),('C',c)]:
        metrics[name]={'n_both_fully_definite':len(ids),'matching_vectors':sum(pred[mapping[k]['review_id']]['labels']==review[k]['labels'] for k in ids),
          'matching_cells':sum(pred[mapping[k]['review_id']]['labels'][d]==review[k]['labels'][d] for k in ids for d in DIMS),
          'dimension_counts':{d:{'n':len(ids),'matches':sum(pred[mapping[k]['review_id']]['labels'][d]==review[k]['labels'][d] for k in ids),
            'dictionary_extra_positive':sum(pred[mapping[k]['review_id']]['labels'][d]==1 and review[k]['labels'][d]==0 for k in ids),
            'dictionary_missing_positive':sum(pred[mapping[k]['review_id']]['labels'][d]==0 and review[k]['labels'][d]==1 for k in ids)} for d in DIMS}}
    results['v'+version]={'source':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'metadata':{k:v for k,v in data.items() if k!='rows'},'comparison':metrics,'rows':rows}
output={'purpose':'development_diagnostics_not_accuracy','unresolved_rows':[k for k in q if k not in ids],
    'scope':'相同55条双方全部可判的开发单元，分别对照A与C；不把AI共识当真值，不含历史LLM重跑。五条未完全可判另列，不补0。',
    'versions':results}
target.write_text(json.dumps(output,ensure_ascii=False,indent=2))
for v,o in results.items():print(v,json.dumps(o['comparison'],ensure_ascii=False))
