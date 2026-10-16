"""Additional geometry controls fixed after attempt01 and before refinement."""
import copy,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
old=json.loads((P/'geometry-controls-fixed-before-edit.json').read_text())['cases']
fixed={c['name']:c for c in old};cases=[]
def clone(source,name,expected,reason):
    c=copy.deepcopy(fixed[source]);c.update(name=name,expected=expected,manual_reason=reason);cases.append(c);return c
def ctx(c,id):return next(z for z in c['synthetic_bundle']['source_record']['contexts'] if z['context_id']==id)
def geo(c,id,**kw):
    z=ctx(c,id);z['structure'].update(kw);z['source_ref']['locator'].update(kw)
def split(name,remote=False):
    c=clone('near_closed_group',name,dict.fromkeys(['S','E','Ec']) if remote else {'S':1,'E':1,'Ec':1},'末成员由同一印刷原段拆分，下一原段证闭合；远段仍不闭合。')
    for i,id in enumerate(['MEMBER-1','MEMBER-2','MEMBER-3'],1):geo(c,id,paragraph_id=f'p0001_item0{i}')
    geo(c,'NEXT',paragraph_id='p0099' if remote else 'p0002')
    b=ctx(c,'BOUNDARY')['structure'];b.update(last_paragraph='p0001_item03',next_paragraph_id='p0099' if remote else 'p0002')
split('split_printed_paragraph_next_original');split('split_printed_paragraph_remote_original',True)
def preceding(name,current,parent,remote,expect):
    # Literal synthetic document has actual parent first, then current. Metadata
    # and intervals agree; no original source/material is edited or substituted.
    doc=parent+'\n'+current+'\n';sha=hashlib.sha256(doc.encode()).hexdigest()
    def ref(pid,seq,a,b):return {'sha256':sha,'source_resource_id':'SOURCE-SYNTHETIC-'+sha,'locator':{'paragraph_id':pid,'sequence_index':seq,'component_id':'C-LOCAL','unicode_code_point_interval_half_open':[a,b]}}
    cs=[{'context_id':'PRE','kind':'preceding_paragraph','text':parent,'structure':{'paragraph_id':'p0001','sequence_index':1,'component_id':'C-LOCAL'},'source_ref':ref('p0001',1,0,len(parent))},{'context_id':'CUR','kind':'paragraph','text':current,'structure':{'paragraph_id':'p0050' if remote else 'p0002','sequence_index':50 if remote else 2,'component_id':'C-LOCAL'},'source_ref':ref('p0050' if remote else 'p0002',50 if remote else 2,len(parent)+1,len(doc)-1)}]
    bundle={'source_record':{'text':current,'source_ref':cs[-1]['source_ref'],'contexts':cs},'source_documents':[],'source_full_text_resources':[],'explicit_or_primary_source_resources':[],'preserved_historical_neutral_source_supplements':[],'source_reference_index':[]}
    cases.append({'name':name,'synthetic_bundle':bundle,'synthetic_documents':[{'sha256':sha,'text':doc,'is_synthetic':True}],'expected':expect,'manual_reason':'明确例如/同一思路的局部前置定义可以补足；已供远段定位矛盾不能只据preceding角色继承。','manual_lines':[22,39,42,84,94,104],'is_human_reference':False})
price='本段开展测算评估，采用基金测算和药物经济学测算并提出医保支付标准评估意见。'
dose='基于给药剂量建立剂量—暴露量—效应（安全性/疗效）关系以确定方案。'
for remote in [False,True]:
    preceding('price_method_'+('remote' if remote else 'near'),'专家就药品测算评估的思路进行交流。',price,remote,{'S':0,'E':0,'Ec':0 if remote else 1})
    preceding('dose_definition_'+('remote' if remote else 'near'),'例如，采用药物模型确定合理的用法用量。',dose,remote,{'S':0 if remote else 1,'E':0 if remote else 1,'Ec':0})
out={'status':'fixed_after_attempt01_before_refinement','cases':cases,'case_N':len(cases),'earlier_expectations_unchanged':True,'synthetic_not_new_original_source_exposure':True}
with (P/'refinement-controls-fixed.json').open('x',encoding='utf8') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
print('fixed',len(cases),'additional cases before refinement')
