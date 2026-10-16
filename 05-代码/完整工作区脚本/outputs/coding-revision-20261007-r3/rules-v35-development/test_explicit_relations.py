"""Constructed positive/negative semantic controls, not validation data."""
import sys,json
from pathlib import Path
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'runtime'))
from rules_semantic_v35 import revise
from rule_support import rebuild
CASES=[
 ('error-prevention','加强用药交代，避免老年人用错药。',{'S'}),
 ('database-error','避免药品数据录入错误。',set()),
 ('drug-name','文件名为“用药差错资料提交规范”。',set()),
 ('long-effect','基于随访研究评价该药物的长期效果。',{'E'}),
 ('administrative-effect','评价药品审批系统的长期运行效果。',set()),
 ('data-reliability','研究药物数据的有效性和完整性。',set()),
 ('economic-effect','分析测算药品的成本、效果、效用和效益。',{'E'}),
 ('cost-only','分析测算药品的成本以及申报资料质量。',set()),
 ('device-cost','测算设备的成本、效果和效益。',set()),
 ('reference-price','若参照药为其他药品，原则上取其全国加权平均价。',{'Ec'}),
 ('price-file','公开参考药价格文件名。',set()),
 ('reference-method','参考药品评价方法，记录研究质量。',set()),
 ('unmet','应关注患者未满足的临床需求。',{'F'}),
 ('general-need','本办法旨在满足患者的临床需求。',set()),
 ('research-need','研究人群的统计需求尚未满足。',set()),
 ('formulary','遴选儿童用药时，可不受一品两规和药品总品种数限制。',{'F'}),
 ('general-formulary','统计一品两规和药品总品种数管理工作。',set()),
 ('filing-only','药品申报平台不受文件名长度限制。',set()),
]
rows=[]
for name,text,expected in CASES:
 result={'evidence':[],'suppressions':[],'judgement_status':'determined'}
 result=rebuild(revise({'unit_text':text},result))
 actual={d for d,v in result['labels'].items() if v}
 assert actual==expected,(name,actual,expected)
 for e in result['evidence']:assert text[e['start']:e['end']]==e['text']
 rows.append({'name':name,'constructed_text':text,'expected':sorted(expected),'actual':sorted(actual),'pass':True})
(R/'constructed_semantic_controls.json').write_text(json.dumps({'all_checks_pass':True,'n':len(rows),'rows':rows},ensure_ascii=False,indent=2)+'\n')
print(len(rows),'semantic controls passed')
