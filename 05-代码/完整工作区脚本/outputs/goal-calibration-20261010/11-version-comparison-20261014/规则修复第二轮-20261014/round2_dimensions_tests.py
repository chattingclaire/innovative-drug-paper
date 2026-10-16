"""Constructed semantic controls, not independent validation or replacement labels."""
import copy, json, pathlib, sys, hashlib
sys.dont_write_bytecode=True
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'code'))
from relations import RelationView
from dimensions import judge, _review_condition_units, _object, Unit
from evidence import validate_decisions
cases=[
('missing_report','未在规定时间提交安全性报告的，暂停药物临床试验。',{'S':0}),
('risk_report','安全性报告显示该药导致严重肝损伤，应暂停给药。',{'S':1}),
('risk_report_content','药物安全性报告应包括所有死亡病例和严重不良事件病例的分析。',{'S':1}),
('mixed_report_risk','未按时提交药物安全性报告，或者报告提示新的严重药物风险的，应暂停试验。',{'S':1}),
('drug_settlement','经办机构应及时结算定点机构发生的医保药品费用。',{'Ec':1}),
('drug_insurance_settlement','规范医保用药行为，按规定及时结算和支付医保费用。',{'Ec':1}),
('office_payment','药品研发机构应及时支付办公室租赁费用。',{'Ec':0}),
('fee_form','药品医保费用字段不能为空。',{'Ec':0}),
('payment_channel','为相关药品扩展商业保险等多元支付渠道。',{'Ec':1}),
('payment_space','为创新药拓展更多支付空间。',{'Ec':1}),
('office_space','为创新药企业拓展办公空间。',{'Ec':0,'I':0}),
('payment_interface','优化支付平台登录界面和药品信息报送流程。',{'Ec':0}),
('ineffective_exposure','优化给药方案，减少患者的无效药物暴露。',{'E':1}),
('kinetic_exposure','估计健康受试者的药代动力学暴露水平。',{'E':0}),
('invalid_data','在给药方案数据库中清除无效数据记录。',{'E':0}),
]
results=[]
for name,text,expected in cases:
 v=RelationView({'text':text,'contexts':[]});decisions=judge(v);validate_decisions(v.unit,decisions)
 actual={d:x['value'] for d,x in decisions.items()}
 results.append({'name':name,'text':text,'expected':expected,'actual':actual,'passed':all(actual[d]==x for d,x in expected.items())})
# Synthetic source identity, same adjacent review, and component boundaries.
current='综合审评结论通过的，批准药品上市。'
definition='对药品的安全性、有效性进行综合审评。'
base={'text':current,'source_ref':{'sha256':'a'*64},'structure':{'component_id':'A'},'contexts':[{'context_id':'TEST-review','kind':'preceding_paragraph','text':definition,'source_ref':{'sha256':'a'*64},'structure':{'component_id':'A'}}]}
for name,field,value,expected in [
 ('same_review',None,None,1),('other_source','sha','b'*64,0),('other_component','component','B',0),
 ('other_review','text','对药品的安全性、有效性进行技术审评。',0),
 ('format_definition','text','对药品申报材料的格式进行综合审评。',0),
 ('other_relation','kind','source_paragraph',0),
 ('status_only','current','本药品已通过综合审评。',0),
 ('filing_only','current','综合审评材料已收到，录入文件编号。',0)]:
 u=copy.deepcopy(base)
 if field=='sha':u['contexts'][0]['source_ref']['sha256']=value
 elif field=='component':u['contexts'][0]['structure']['component_id']=value
 elif field=='current':u['text']=value
 elif field:u['contexts'][0][field]=value
 v=RelationView(u);relations=_review_condition_units(v)
 decisions=judge(v);validate_decisions(v.unit,decisions)
 results.append({'name':name,'expected_relation_count':expected,'actual_relation_count':len(relations),'passed':len(relations)==expected and (not expected or all(decisions[d]['value']==1 for d in ['S','E']))})
# Explicit scope adds an object only to actual adverse-case content.
scope={'text':'死亡病例的安全性总结报告应包括相关研究病例。','source_ref':{'sha256':'a'*64},'structure':{'component_id':'A'},'contexts':[{'context_id':'TEST-scope','kind':'source_paragraph','text':'针对首次递交上市申请的抗肿瘤创新药产品，在安全性资料的整理分析方面提供建议。','source_ref':{'sha256':'a'*64},'structure':{'component_id':'A'}}]}
for name,field,value,expected in [('report_scope',None,None,True),('report_other_source','sha','b'*64,False),('report_other_component','component','B',False),('report_deadline_only','current','安全性总结报告须于六月上传。',False)]:
 u=copy.deepcopy(scope)
 if field=='sha':u['contexts'][0]['source_ref']['sha256']=value
 elif field=='component':u['contexts'][0]['structure']['component_id']=value
 elif field=='current':u['text']=value
 v=RelationView(u);obj=_object(v,Unit(v.norm,0,len(v.norm)))
 actual=bool(obj.get('established'))
 results.append({'name':name,'expected_object':expected,'actual_object':actual,'passed':actual==expected})
failed=[r for r in results if not r['passed']]
(HERE/'round2-dimensions-tests.json').write_text(json.dumps({'scope':'synthetic development tests, not held-out validation','code_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (HERE/'code').glob('*.py')},'cases':results},ensure_ascii=False,indent=2))
print(json.dumps({'passed':len(results)-len(failed),'total':len(results),'failed':failed},ensure_ascii=False))
if failed:raise SystemExit(1)
