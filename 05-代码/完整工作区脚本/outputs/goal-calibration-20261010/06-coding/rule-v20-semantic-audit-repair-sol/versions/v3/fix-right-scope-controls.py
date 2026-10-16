from pathlib import Path
import json,hashlib,copy,sys
p=Path(__file__).resolve().parent;sys.dont_write_bytecode=True
sha='a'*64;ref={'sha256':sha,'source_resource_id':'SOURCE-'+sha,'locator':{}}
def c(cid,k,t,article=None):
 r=copy.deepcopy(ref)
 if article:r['locator']['article_id']=article
 return {'context_id':cid,'kind':k,'text':t,'source_ref':r,'structure':{}}
def u(text,paragraph,definition,article,otherarticle):
 r=copy.deepcopy(ref);r['locator']['article_id']=article
 return {'text':text,'source_ref':r,'contexts':[c('current','paragraph',paragraph,article),c('definition','source_paragraph',definition,otherarticle)]}
cases=[]
def add(n,x,i,f,reason):cases.append({'name':n,'synthetic_input':x,'expected':{'I':i,'F':f},'manual_reason':reason,'control_group':'additional right-closure control fixed before terminal scope patch'})
t='药审中心终止本条药品的数据保护。'
add('right_known_own_ordinary_brother_innovative',u(t,'本条普通药品按一般资料保密条件登记数据保护。'+t,'创新药具有新作用机制，给予该药品六年数据保护期。','article-current','article-brother'),0,0,'原定位明确兄弟条款创新资格属于不同药品；当前同条已明确普通保密对象，不继承。')
add('right_unknown_anaphor_brother_scope_missing',u(t,t,'创新药具有新作用机制，给予该药品六年数据保护期。','article-current','article-brother'),None,0,'当前药品数据保护确指对象未核明，唯一创新定义属于兄弟条款；需I资格补材。')
add('right_same_article_qualified_object',u(t,t,'本条创新药具有新作用机制，给予该药品六年数据保护期。','article-current','article-current'),1,0,'原定位同条、同一保护类型及药品对象，实质创新资格决定当前权利终止。')
t='药审中心终止本条普通药品的数据保护。'
add('right_different_protection_type_same_available_paragraph',u(t,t,'创新药给予市场独占待遇。普通药品实行一般资料保密的数据保护。','article-current','article-current'),0,0,'同段不同保护类型分别判断，市场独占的创新资格不能赋给一般数据保护。')
file=p/'right-scope-controls-fixed-before-terminal-patch.json'
file.write_text(json.dumps({'identity':'nonhuman AI development; supplement after original phase, not new independent validation','cases':cases,'case_N':4,'expected_changed':False,'stage':'after run005, fixed before further right-scope code edits'},ensure_ascii=False,indent=2)+'\n')
def bind(q):
 x=q.read_bytes();return {'path':str(q),'sha256':hashlib.sha256(x).hexdigest(),'bytes':len(x)}
(p/'right-scope-preterminal-seal.json').write_text(json.dumps({'controls':bind(file),'preterminal_modules':[bind(p/(n+'.py'))for n in ['relations','dimensions']],'input_changed':False,'timing':'additional controls fixed after original32 run005, before terminal scope patch'},ensure_ascii=False,indent=2)+'\n')
# V2 actual before making any patch for these newly fixed controls.
for version in [p.parent/'v2',p]:
 for n in ['source_packet','source_receipts','evidence','relations','dimensions']:sys.modules.pop(n,None)
 sys.path.insert(0,str(version));import relations,dimensions,evidence
 results=[]
 for x in cases:
  v=relations.RelationView(copy.deepcopy(x['synthetic_input']));d=dimensions.judge(v);evidence.validate_decisions(x['synthetic_input'],d)
  actual={k:d[k]['value']for k in ['I','F']};results.append({'name':x['name'],'expected':x['expected'],'observed':actual,'passed':actual==x['expected'],'decisions':d,'source_requests':v.source_requests,'relation_traces':v.traces()})
 out=p/('right-scope-baseline-'+version.name+'.json');out.write_text(json.dumps({'modules':[bind(version/(n+'.py'))for n in ['source_packet','source_receipts','evidence','relations','dimensions']],'controls':bind(file),'results':results},ensure_ascii=False,indent=2)+'\n');print(version.name,[(x['name'],x['observed'])for x in results]);sys.path.pop(0)
