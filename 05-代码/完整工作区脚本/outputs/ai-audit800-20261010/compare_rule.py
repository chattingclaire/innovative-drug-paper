from pathlib import Path
from collections import Counter,defaultdict
import json,csv,hashlib
BASE=Path(__file__).resolve().parent; ROOT=BASE.parent.parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
initial=BASE/'AI原始判读-800条.jsonl'
summary=json.loads((BASE/'抽检汇总.json').read_text())
assert sha(initial)==summary['initial_jsonl_sha256']
reviews={r['source_id']:r for r in map(json.loads,initial.read_text().splitlines())}
assert len(reviews)==800
metadata=json.loads((BASE/'checks/sample-metadata.json').read_text())['records']
production=ROOT/'outputs/goal-calibration-20261010/06-coding/rule-full4481-v2-root'
release=json.loads((production/'rule-production-release.json').read_text())
for k,fn in [('manual','manual.txt'),('prompt','execution-prompt.txt'),('protocol','common-execution-protocol.txt')]:
    assert sha(BASE/'source-A/coder-A'/fn)==release[k]['sha256'],k+' mismatch'
predpath=production/'run4481-first/predictions.jsonl'
rule={}
with predpath.open() as f:
    for line in f:
        p=json.loads(line)
        if p['id'] in reviews:rule[p['id']]=p
assert set(rule)==set(reviews)
dims=['S','E','Ec','I','F'];stats=defaultdict(Counter);differences=[];missing=[]
for sid,r in sorted(reviews.items(),key=lambda z:z[1]['blind_id']):
    domain=metadata[r['blind_id']]['domain']
    sr=json.loads((BASE/'source-A/coder-A/materials'/f"{r['blind_id']}.json").read_text())['source_record']
    for dim in dims:
        a=r['judgments'][dim];v=a['value'];rv=rule[sid]['labels'][dim]
        assert rv in [0,1,None]
        c=stats[(domain,dim)];c['slots']+=1
        if rv is None or v is None:
            c['not_joint_binary']+=1;missing.append([r['blind_id'],sid,domain,dim,rv,v]);continue
        c['joint_binary']+=1;c['agree' if rv==v else 'disagree']+=1
        if rv!=v:
            differences.append([r['blind_id'],sid,domain,metadata[r['blind_id']]['department'],dim,rv,v,sr['text'],a['evidence'],a['locator'],a['reason'],rule[sid]['decisions'][dim].get('reason','')])
with (BASE/'与规则法分歧清单.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(['A盲号','原记录号','原样本分组','部门','维度','规则法值','本轮AI值','当前完整命题','AI依据','AI定位','AI理由','规则法理由']);w.writerows(differences)
out={'comparison_kind':'固定AI初判后的描述性对照；差异不是经裁定的错误，不代表真人效度或总体正确率','ai_initial_sha256':sha(initial),'rule_predictions_path':str(predpath),'rule_predictions_sha256':sha(predpath),'same_manual_prompt_protocol':True,'records':800,'slots':4000,'disagreement_slots':len(differences),'disagreement_records':len({r[0] for r in differences}),'not_joint_binary':missing,'by_domain_dimension':[{'domain':a,'dimension':b,**c} for (a,b),c in sorted(stats.items())]}
(BASE/'与规则法对照汇总.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps(out,ensure_ascii=False))
