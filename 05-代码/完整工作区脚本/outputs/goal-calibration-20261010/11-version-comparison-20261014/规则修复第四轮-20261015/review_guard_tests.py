import json,sys,pathlib,hashlib
sys.dont_write_bytecode=True
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'code'))
from relations import RelationView
from dimensions import judge
from evidence import validate_decisions
cases=json.loads((HERE/'round2-dimensions-review-probes.json').read_text())[-1]['cases']
cases.extend([
 {'name':'actual_payment_plus_receipt','unit':{'text':'应按期结算医保药品费用，并上传结算医保费用的凭证。','contexts':[]},'expected':{'Ec':1}},
 {'name':'actual_effect_plus_field','unit':{'text':'优化给药方案，减少患者的无效药物暴露，同时更新相关字段名称。','contexts':[]},'expected':{'E':1}},
 {'name':'risk_content_plus_late_analysis','unit':{'text':'未提交药物安全性报告的，应分析迟交原因，并评价药物风险。','contexts':[]},'expected':{'S':1}},
])
results=[]
for c in cases:
 v=RelationView(c['unit']);d=judge(v);validate_decisions(v.unit,d)
 actual={k:d[k]['value'] for k in c['expected']}
 results.append({'name':c['name'],'text':c['unit']['text'],'expected':c['expected'],'actual':actual,'passed':actual==c['expected']})
failed=[r for r in results if not r['passed']]
(HERE/'review-guard-tests.json').write_text(json.dumps({'scope':'synthetic counterexamples and paired controls, not independent validation','code_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (HERE/'code').glob('*.py')},'cases':results},ensure_ascii=False,indent=2))
print(json.dumps({'passed':len(results)-len(failed),'total':len(results),'failed':failed},ensure_ascii=False))
if failed:raise SystemExit(1)
