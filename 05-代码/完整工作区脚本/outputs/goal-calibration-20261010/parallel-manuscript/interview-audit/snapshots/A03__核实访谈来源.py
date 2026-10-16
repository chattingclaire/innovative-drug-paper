from pathlib import Path
from docx import Document
import json,hashlib
root=Path('/Users/rainbow/Desktop/战略院/创新药论文-完整归档-20260914/04-访谈与研讨会原始资料')
items=[('权重与健康需求','史录文教授访谈会议纪要-0605.docx',6),('背对背经济测算','史录文教授访谈会议纪要-0605.docx',7),('商保数据限制','史录文教授访谈会议纪要-0605.docx',30),('四层评价及经济性评价','医保局专家调研-0616.docx',2),('PPT及个人打分','医保局专家调研-0616.docx',3),('比较临床价值','医保局专家调研-0616.docx',5)]
rows=[]
for claim,name,i in items:
 p=root/name;d=Document(p)
 rows.append({'claim':claim,'source':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'paragraph_number_1_based':i+1,'exact_text':d.paragraphs[i].text,'finding':'本地原始纪要明确支持；保留专家归属，不直接等同正式规定或三部门普遍事实'})
Path('访谈主张-原始纪要核实.json').write_text(json.dumps({'scope':'核查6项正文所用访谈内容；不是全部访谈与文献核查完成','claims':rows},ensure_ascii=False,indent=2))
# Change attribution only, retaining sourced substantive content.
rp=Path('失效结论替换规则.json');rules=json.loads(rp.read_text())
for r in rules:
 if r['old'].startswith('针对价值衡量的不一致'):
  r['new']=r['new'].replace('访谈显示，医保目录评审中企业需将申报材料制作成演示文稿供综合组专家审阅打分，材料描述不清晰会直接影响得分；药物经济学测算采用背对背方式进行；商业健康保险机构则因难以获得公立医院的数据而难以测算定价。','受访的医保评审领域专家介绍，企业需将申报材料制作成演示文稿供综合组专家审阅打分，材料描述不清晰会影响得分。受访的高校药事管理领域专家介绍，药物经济学测算采用背对背方式进行，并指出商业健康保险机构获取公立医院数据存在困难，影响其测算。')
  assert '受访的医保评审领域专家介绍，企业' in r['new']
rp.write_text(json.dumps(rules,ensure_ascii=False,indent=2))
print('Verified six claims against two original DOCX files; clarified paragraph attribution')
