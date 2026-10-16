"""Fixed supplied-metadata contradictions, before final consistency refinement."""
import copy,json
from pathlib import Path
P=Path(__file__).resolve().parent
cases=[]
base={c['name']:c for c in json.loads((P/'geometry-controls-fixed-before-edit.json').read_text())['cases']}
def clone(name,new,expected):
    c=copy.deepcopy(base[name]);c.update(name=new,expected=expected,manual_reason='已供同字段矛盾或另一组件重复当前字面不能建立有限范围；不默选有利一方。');cases.append(c);return c
c=clone('near_closed_group','member_component_structure_locator_conflict',dict.fromkeys(['S','E','Ec']))
next(x for x in c['synthetic_bundle']['source_record']['contexts'] if x['context_id']=='MEMBER-2')['source_ref']['locator']['component_id']='C-OTHER'
c=clone('near_payment_parent','parent_target_structure_locator_conflict',{'S':0,'E':0,'Ec':0})
next(x for x in c['synthetic_bundle']['source_record']['contexts'] if x['context_id']=='PARENT')['source_ref']['locator']['target_paragraph_id']='p0999'
c=copy.deepcopy(next(c for c in json.loads((P/'refinement-controls-interface-complete.json').read_text())['cases'] if c['name']=='price_method_near'))
c.update(name='preceding_other_component_duplicated_current',expected={'S':0,'E':0,'Ec':0},manual_reason='当前位置在C-LOCAL，另一组件的同字面段不能替代当前建立前置定义。')
r=c['synthetic_bundle']['source_record'];pre=r['contexts'][0];pre['structure']['component_id']='C-OTHER';pre['source_ref']['locator']['component_id']='C-OTHER'
dup=copy.deepcopy(r['contexts'][-1]);dup['context_id']='DUP';dup['structure']['component_id']='C-OTHER';dup['source_ref']['locator']['component_id']='C-OTHER';r['contexts'].append(dup);cases.append(c)
with (P/'consistency-controls-fixed.json').open('x',encoding='utf8') as f:json.dump({'status':'fixed_after_attempt03_before_consistency_edit','cases':cases,'case_N':len(cases),'pure_synthetic_no_original_source_exposure':True},f,ensure_ascii=False,indent=2);f.write('\n')
