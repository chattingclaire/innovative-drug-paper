import pathlib,json,sys,copy,hashlib
sys.dont_write_bytecode=True
HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(HERE/'code'))
from relations import RelationView
from dimensions import judge
from evidence import validate_decisions
text='(三)申办者应当记录已识别的风险和相应的缓解措施，并与参与采取措施或者受此类活动影响的人员沟通。'
prev='(二)风险控制应当与风险对试验参与者权益和安全，以及试验结果可靠性影响的重要性相称。申办者应当预先设定风险控制可接受范围。'
scope='第二条 本规范适用于经药品监督管理部门批准，为研制药品而进行的药物临床试验。'
base={'text':text,'source_ref':{'sha256':'a'*64},'structure':{'component_id':'A'},'contexts':[{'context_id':'scope','kind':'source_paragraph','text':scope,'source_ref':{'sha256':'a'*64},'structure':{'component_id':'A'}},{'context_id':'risk','kind':'preceding_paragraph','text':prev,'source_ref':{'sha256':'a'*64},'structure':{'component_id':'A'}}]}
results=[]
def check(name,u,expected=None,path_expected=None):
 v=RelationView(u);d=judge(v);validate_decisions(v.unit,d)
 actual=d['S']['value'];paths=[d['S']['basis_path']]+[x['basis_path'] for x in d['S'].get('details',{}).get('additional_evidence',[])]
 has='same_source_identified_participant_risk_control' in paths
 ok=(expected is None or actual==expected) and (path_expected is None or has==path_expected)
 results.append({'name':name,'expected_value':expected,'expected_new_path':path_expected,'value':actual,'has_new_path':has,'passed':ok})
check('explicit_risk_chain',base,1,True)
for name,kind,value in [('data_only','risk',prev.replace('试验参与者权益和安全，以及','')),('other_source','sha','b'*64),('other_component','component','B'),('no_scope','delete_scope',None),('no_risk_definition','delete_risk',None),('scope_excludes_drug_trial','scope',scope.replace('本规范适用于','本规范不适用于')),('ordinary_record','text','(三)申办者应当记录临床试验文件的页码和签字。'),('quoted_record','text','(三)上传写有“申办者应当记录已识别的风险和相应的缓解措施”的文件。'),('title_record','text','(三)将“申办者应当记录已识别的风险和相应的缓解措施”作为栏目标题。')]:
 u=copy.deepcopy(base)
 if kind=='risk':u['contexts'][1]['text']=value
 elif kind=='sha':u['contexts'][1]['source_ref']['sha256']=value
 elif kind=='component':u['contexts'][1]['structure']['component_id']=value
 elif kind=='delete_scope':u['contexts']=u['contexts'][1:]
 elif kind=='delete_risk':u['contexts']=u['contexts'][:1]
 elif kind=='scope':u['contexts'][0]['text']=value
 elif kind=='text':u['text']=value
 check(name,u,0 if kind in ['risk','text'] else None,False)
u=copy.deepcopy(base);u['text']='(三)上传写有“申办者应当记录已识别的风险和相应的缓解措施”的文件；申办者应当记录已识别的风险和相应的缓解措施，并沟通风险控制情况。';check('mixed_form_and_actual',u,1,True)
for r in map(json.loads,(ROOT/'06-coding/rule-full4481-v2-root/run4481-first/effective-semantic-units.jsonl').open()):
 if r['id']=='RECODE25-04071':check('original_saved_input',r['semantic_unit'],1,True);break
failed=[x for x in results if not x['passed']]
(HERE/'round4-safety-tests.json').write_text(json.dumps({'role':'development boundary checks, not independent validation','code_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (HERE/'code').glob('*.py')},'cases':results},ensure_ascii=False,indent=2))
print(json.dumps({'passed':len(results)-len(failed),'total':len(results),'failed':failed},ensure_ascii=False))
if failed:raise SystemExit(1)
