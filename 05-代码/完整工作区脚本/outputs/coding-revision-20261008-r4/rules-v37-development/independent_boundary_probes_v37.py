from pathlib import Path
from tempfile import TemporaryDirectory
import sys,hashlib,json,subprocess
R=Path('/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs')
NEW=R/'coding-revision-20261008-r4/rules-v37-development'
OLD=R/'coding-revision-20261007-r3/rules-v36.2-development'
assert hashlib.sha256((NEW/'candidate_freeze.json').read_bytes()).hexdigest()=='bddc8b3403539d3ead6f1488864d7f5498be2369464ba91e525ba0a7b465b47c'
cases=[
 ('drug_price_positive','药品按集采中选最高价计算。',False),
 ('price_other_subject','药品按程序申报，会议餐饮采用采购最低价。',False),
 ('price_other_lab_object','药品按程序申报，检验耗材采用采购最低价。',False),
 ('medication_prevention_positive','在药物给药过程中，应防止误用。',False),
 ('medication_wrong_money_object','在药品调配时，应防止误用科研经费。',False),
 ('purpose_only','为促进药品创新发展，完善药品试验数据保护制度，现予发布。',False),
 ('publication_explicit_right_scope','为促进药品创新发展，扩大药品试验数据保护制度的适用范围至改良型新药，现予发布。',False),
 ('publication_independent_right','为促进药品创新发展，完善药品试验数据保护制度，给予新药6年数据保护期，现予发布。',False),
 ('guidance_positive','药审中心安排审评人员进行沟通，基于已有研究资料，对下一步研究方案提出建议。',True),
 ('guidance_subject_switch','药审中心安排审评人员核对文件清单，申请人基于已有研究资料，对下一步研究方案提出意见或者建议。',True),
]
digest=lambda b:hashlib.sha256(b).hexdigest()
assert not (NEW/'independent_boundary_results_v37.json').exists()
with TemporaryDirectory(prefix='v37-independent-constructed-') as tmp:
 tmp=Path(tmp);records=[]
 scope='药物临床试验期间，用于防治严重疾病的创新药或者改良型新药，申请人可以申请适用突破性治疗药物程序。'
 for name,text,has_scope in cases:
  r={'unit_text':text}
  if has_scope:
   source=tmp/(name+'.txt');cand=tmp/(name+'.json');source.write_text(scope+'\n'+text+'\n');cand.write_text(json.dumps({'paragraphs':[{'id':'scope','text':scope,'pages':[]}],'unit_candidates':[{'id':'unit','text':text}]},ensure_ascii=False))
   sh=digest(source.read_bytes());ch=digest(cand.read_bytes())
   r.update(unit_source=str(source),unit_source_sha256=sh,candidate_file=str(cand),candidate_sha256=ch,unit_id='unit',verified_innovation_scope_v27={'text':scope,'text_sha256':digest(scope.encode()),'source_sha256':sh,'original_unit_sha256':digest(text.encode()),'component':'突破性治疗程序','verified':True,'locator':{'source_lines':[1],'paragraph_id':'scope'},'component_binding':{'unit_id':'unit','candidate_sha256':ch}})
  records.append({'name':name,'record':r})
 code='''import json,sys;sys.path.insert(0,sys.argv[1]);from policy_coding_v27 import code_unit;rows=json.load(sys.stdin);print(json.dumps([{'name':x['name'],'result':code_unit(x['record'])} for x in rows],ensure_ascii=False))'''
 output={}
 for ver,path in [('old',OLD),('new',NEW)]:
  p=subprocess.run([sys.executable,'-B','-c',code,str(path/'runtime')],input=json.dumps(records,ensure_ascii=False),text=True,capture_output=True,check=True)
  output[ver]=json.loads(p.stdout)
 rows=[]
 for a,b,case in zip(output['old'],output['new'],cases):
  row={'name':case[0],'constructed_text':case[1],'scope_fixture':case[2],'old_full_result':a['result'],'new_full_result':b['result'],'old_labels':a['result']['labels'],'new_labels':b['result']['labels'],'old_I_evidence':[e for e in a['result']['evidence'] if e['dimension']=='I'],'new_v37_evidence':[e for e in b['result']['evidence'] if e['rule'].startswith('V37')],'new_suppressions':[e for e in b['result']['suppressions'] if e['rule'].startswith('V37')]};rows.append(row)
  print(json.dumps({'name':row['name'],'old_labels':row['old_labels'],'new_labels':row['new_labels']},ensure_ascii=False))
 (NEW/'independent_boundary_results_v37.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
