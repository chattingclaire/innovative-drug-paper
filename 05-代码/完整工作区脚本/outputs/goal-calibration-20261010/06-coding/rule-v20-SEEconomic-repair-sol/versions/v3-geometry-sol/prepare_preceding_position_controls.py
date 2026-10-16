"""Supplied preceding-span contradictions; classifier unchanged after attempt05."""
import copy,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
old=json.loads((P/'refinement-controls-interface-complete.json').read_text())['cases'];cases=[]
for name in ['price_method_near','dose_definition_near']:
    c=copy.deepcopy(next(x for x in old if x['name']==name));c.update(name=name+'_reversed_source_spans',expected={'S':0,'E':0,'Ec':0},manual_reason='即便preceding角色、段号与序号看似近邻，已供同源原文字跨度反向时，不能从后文借定义。')
    r=c['synthetic_bundle']['source_record'];pre,cur=r['contexts'];raw=cur['text']+'\n'+pre['text']+'\n';sha=hashlib.sha256(raw.encode()).hexdigest()
    cur['source_ref']['locator']['unicode_code_point_interval_half_open']=[0,len(cur['text'])]
    pre['source_ref']['locator']['unicode_code_point_interval_half_open']=[len(cur['text'])+1,len(raw)-1]
    r['source_ref']=copy.deepcopy(cur['source_ref'])
    for z in [r]+r['contexts']:z['source_ref']['sha256']=sha;z['source_ref']['source_resource_id']='SOURCE-SYNTHETIC-'+sha
    c['synthetic_documents']=[{'sha256':sha,'text':raw,'is_synthetic':True}];cases.append(c)
with (P/'preceding-position-controls-fixed.json').open('x',encoding='utf8') as f:json.dump({'status':'fixed_after_attempt05_without_classifier_change','cases':cases,'case_N':2,'pure_synthetic':True},f,ensure_ascii=False,indent=2);f.write('\n')
