from pathlib import Path
import sys,json,copy,hashlib
sys.dont_write_bytecode=True
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p));import relations,dimensions,evidence
cs=json.loads((p/'right-scope-controls-fixed-before-terminal-patch.json').read_bytes())['cases'];out=[]
for c in cs:
 v=relations.RelationView(copy.deepcopy(c['synthetic_input']));d=dimensions.judge(v);evidence.validate_decisions(c['synthetic_input'],d);actual={k:d[k]['value']for k in ['I','F']};out.append({'name':c['name'],'expected':c['expected'],'observed':actual,'passed':actual==c['expected'],'decisions':d,'source_requests':v.source_requests,'relation_traces':v.traces(),'evidence_validation_passed':True})
result={'results':out,'controls_sha256':hashlib.sha256((p/'right-scope-controls-fixed-before-terminal-patch.json').read_bytes()).hexdigest(),'modules':[{'path':str(p/(n+'.py')),'sha256':hashlib.sha256((p/(n+'.py')).read_bytes()).hexdigest()}for n in ['source_packet','source_receipts','evidence','relations','dimensions']]}
with Path(sys.argv[1]).open('x',encoding='utf-8')as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'case_N':len(out),'pass_N':sum(r['passed']for r in out),'failure_N':sum(not r['passed']for r in out)},ensure_ascii=False))
