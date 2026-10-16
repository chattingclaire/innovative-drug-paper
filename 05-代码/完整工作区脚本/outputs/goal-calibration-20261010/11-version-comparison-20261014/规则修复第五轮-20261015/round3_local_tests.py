"""Synthetic paired boundaries plus four unchanged source-input replays."""
import json,pathlib,sys,copy,hashlib
sys.dont_write_bytecode=True
HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE/'code'))
from relations import RelationView
from dimensions import judge
from evidence import validate_decisions
results=[]
def check(name,u,expected):
 v=RelationView(u);d=judge(v);validate_decisions(v.unit,d)
 actual={k:d[k]['value'] for k in expected}
 results.append({'name':name,'text':u['text'],'expected':expected,'actual':actual,'passed':actual==expected})
def sample(text,prefix='',kind='paragraph',sha='a'*64,component='A'):
 return {'text':text,'source_ref':{'sha256':'a'*64,'locator':{'paragraph_ids':['p1']}},'structure':{'component_id':'A'},'contexts':[{'context_id':'SYNTH-context','kind':kind,'text':prefix+text if kind=='paragraph' else prefix,'source_ref':{'sha256':sha,'locator':{'paragraph_id':'p1'}},'structure':{'component_id':component,'paragraph_id':'p1'}}]}
base='药品审评中心根据申报品种、工艺、设施等因素，基于风险决定是否启动药品注册生产现场核查。'
for name,text,scope,expect in [
 ('category_obligation','对于创新药、改良型新药以及生物制品等，应当进行药品注册生产现场核查。',base,1),
 ('cosmetic_requirement','对于创新药，应当在材料首页签字盖章。',base,0),
 ('common_risk_obligation','该创新药应按普遍要求报告不良事件。',base,0),
 ('common_inspection','所有药品应当进行药品注册生产现场核查。',base,0),
 ('no_differential_baseline','对于创新药，应当进行药品注册生产现场核查。','药品材料按顺序归档。',0),
 ('name_only_inspection','对于创新药，系统新增“应当进行药品注册生产现场核查”栏目。',base,0)]:check(name,sample(text,scope,'preceding_paragraph'),{'I':expect})
route='45日通道是审评机构将现有审评审批资源向符合条件的创新药临床试验申请倾斜的改革举措。'
for name,text,prefix,expect in [
 ('rnd_choice','申请人应当根据品种研发的实际需求，合理选择45日通道或者60日默示许可。',route,1),
 ('different_route','申请人应当根据品种研发的实际需求，合理选择60日通道。',route,0),
 ('form_choice','申请人应当根据品种研发的实际需求，在申报表选择45日通道栏目名称。',route,0),
 ('route_no_innovation','申请人应当根据品种研发的实际需求，合理选择45日通道。','45日通道是企业办公场所审批通道。',0),
 ('route_state','申请人已经通过45日通道。',route,0),
 ('route_only_registration','申请人登记45日通道的使用情况。',route,0)]:check(name,sample(text,prefix),{'I':expect})
safety='加强医疗机构药品安全管理。建立覆盖药品采购、贮存、调配、使用全过程的监测系统。'
for name,text,prefix,expect in [
 ('expiration_prevention','遵循近效期先出的原则，避免出现过期药品。',safety,1),
 ('inventory_months','统计库存药品有效期月份用于财务盘点。',safety,0),
 ('inventory_numbers','对药品使用数量进行预估。',safety,0),
 ('inventory_loss_only','遵循近效期先出的原则，避免出现过期药品。','为减少库存报损，应优化库存成本核算。',0),
 ('safety_form','系统增设“避免出现过期药品”栏目，并登记近效期先出字段。',safety,0)]:check(name,sample(text,prefix),{'S':expect})
ftext='因此，原则上，单臂试验适用于治疗严重危及生命且缺乏有效标准治疗手段的难治疾病，并在早期研究中初步显示突出疗效的单药治疗。'
fpre='晚期无药可治的肿瘤患者存在急迫的治疗需求；一旦早期数据提示突出疗效，则希望入组的受试者均能接受试验治疗，得到潜在的治疗机会，因此不再要求采用安慰剂对照，可以采用单臂试验设计。'
for name,prefix,expected in [
 ('need_opportunity_chain',fpre,1),('no_chain','单臂试验采用开放设计。',0),
 ('missing_treatment_need',fpre.replace('无药可治','尚可治疗'),0),
 ('missing_all_participants',fpre.replace('均能接受','可能接受'),0),
 ('contradicted_opportunity',fpre.replace('则希望','并非希望'),0),
 ('retained_control',fpre.replace('不再要求采用','仍然要求采用'),0)]:check(name,sample(ftext,prefix),{'F':expected})
for name,text,prefix,expected in [('crosssource_route','申请人应当根据品种研发的实际需求，合理选择45日通道。',route,{'I':0}),('crosssource_safety','遵循近效期先出的原则，避免出现过期药品。',safety,{'S':0}),('crosssource_fairness',ftext,fpre,{'F':0})]:
 check(name,sample(text,prefix,sha='b'*64),expected)
for rid,dim in [('RECODE25-04550','I'),('RECODE25-02232','I'),('RECODE25-02375','S'),('RECODE25-00275','F')]:
 for r in map(json.loads,(ROOT/'06-coding/rule-full4481-v2-root/run4481-first/effective-semantic-units.jsonl').open()):
  if r['id']==rid:check(rid,r['semantic_unit'],{dim:1});break
failed=[r for r in results if not r['passed']]
(HERE/'round3-local-tests.json').write_text(json.dumps({'purpose':'development regression, not independent validation','code_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (HERE/'code').glob('*.py')},'cases':results},ensure_ascii=False,indent=2))
print(json.dumps({'passed':len(results)-len(failed),'total':len(results),'failed':failed},ensure_ascii=False))
if failed:raise SystemExit(1)
