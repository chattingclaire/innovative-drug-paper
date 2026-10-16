#!/usr/bin/env python3
"""Exact arithmetic on frozen aggregate figure2_data; no unit-level data are opened."""
from pathlib import Path
from fractions import Fraction as F
import json,hashlib
O=Path(__file__).resolve().parent;ROOT=O.parents[2]
M=ROOT/'outputs/coding-revision-20261007-r3/manuscript-update-20261008'
AUTH=M/'proxy-180-table2-binding-20261008/表2与五维κ_代理180权威绑定.json'
P=M/'measurement-adapter-v4/actual-payload-ready-v6-report-v5/manuscript_measurement_payload.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def b(p):return {'path':str(p),'sha256':sha(p)}
assert sha(AUTH)=='e437298ca834133b01d21781464b621426ab221595a86634aa0d1061cf8d28dd'
a=json.loads(AUTH.read_text());expected=next(x for x in a['input_bindings']if x['path']==str(P));assert b(P)==expected
p=json.loads(P.read_text());assert p['status']=='ready_for_authoring'
x={(r['group'],r['method_role']):r for r in p['figure2_data']};assert len(x)==6
checks=[]
def check(name,value):
 checks.append({'name':name,'pass':bool(value)});assert value,name
G=['NMPA','NHSA','NHC'];D=['S','E','Ec','I','F'];gn={'NMPA':'药监','NHSA':'医保','NHC':'卫健'};dn={'S':'安全性','E':'有效性','Ec':'经济性','I':'创新性','F':'公平性'}
def val(t):return {'exact_fraction':str(t),'value':float(t)}
rows=[];groups=[]
for g in G:
 r=x[g,'rules'];l=x[g,'LLM'];nr=r['unit_n'];nl=l['unit_n'];tr=r['denominator'];tl=l['denominator']
 check(g+' common unit denominator',nr==nl)
 for role,z in [('rules',r),('LLM',l)]:
  check(g+role+' 5 counts sum to q denominator',sum(z['dimensions'][d]['count']for d in D)==z['denominator'])
  check(g+role+' q exact sum1',sum((F(z['dimensions'][d]['exact_fraction'])for d in D),F())==1)
  for d in D:
   n=z['dimensions'][d]['count'];check(g+role+d+' q fraction',F(n,z['denominator'])==F(z['dimensions'][d]['exact_fraction']));check(g+role+d+' coverage fraction',F(n,z['unit_n'])==F(z['dimensions'][d]['coverage_exact_fraction']))
 groups.append({'group':g,'department':gn[g],'common_unit_denominator':nr,'rules_five_dimension_label_occurrence_denominator':tr,'LLM_five_dimension_label_occurrence_denominator':tl,'label_occurrence_denominator_change':tl-tr})
 for d in D:
  c0=r['dimensions'][d]['count'];c1=l['dimensions'][d]['count'];q0=F(c0,tr);q1=F(c1,tl);v0=F(c0,nr);v1=F(c1,nr)
  rows.append({'group':g,'department':gn[g],'dimension':d,'dimension_name':dn[d],'rules_count':c0,'LLM_count':c1,'net_count_change_LLM_minus_rules':c1-c0,'common_unit_denominator':nr,'rules_coverage_percent':val(100*v0),'LLM_coverage_percent':val(100*v1),'coverage_difference_percentage_points_LLM_minus_rules':val(100*(v1-v0)),'rules_q_denominator':tr,'LLM_q_denominator':tl,'rules_attention_percent':val(100*q0),'LLM_attention_percent':val(100*q1),'attention_difference_percentage_points_LLM_minus_rules':val(100*(q1-q0)),'count_increases_but_attention_falls':c1>c0 and q1<q0})
check('all15 comparisons retained',len(rows)==15)
for g in G:check(g+' attention differences exact sum0',sum((F(r['attention_difference_percentage_points_LLM_minus_rules']['exact_fraction'])for r in rows if r['group']==g),F())==0)
examples=[]
for g,d in [('NMPA','S'),('NHSA','Ec')]:
 z=next(y for y in rows if y['group']==g and y['dimension']==d)
 examples.append({**z,'count_relative_increase_percent':val(F(100*(z['LLM_count']-z['rules_count']),z['rules_count'])),'all_labels_relative_increase_percent':val(F(100*(z['LLM_q_denominator']-z['rules_q_denominator']),z['rules_q_denominator']))})
res={'status':'PASS_EXACT_AGGREGATE_DENOMINATOR_AUDIT','source_payload':b(P),'prior_source_binding':b(AUTH),'source_selector':'/figure2_data','script':b(Path(__file__)),'method_ids':{'rules':p['resolved_fields39']['FINAL_RULES_ID'],'LLM':p['resolved_fields39']['FINAL_LLM_ID']},'scope':'Frozen adopted full-corpus aggregate counts for4481 three-department units; no sample weights, human validation or new uncertainty estimate.','definitions':{'count':'Number of units coded1 for this dimension; binary per dimension, multiple dimensions may be1 on the same unit.','coverage_percent':'100*dimension_count/common_department_unit_n','attention_percent_q':'100*dimension_count/sum_of_five_dimension_counts_for_that_department_and_method','method_difference':'LLM minus automatic rules','denominator_identity':'q_L-q_R=[(c_L-c_R)*T_R-c_R*(T_L-T_R)]/(T_R*T_L)','identity_use':'Arithmetic explanation only, not a new substantive metric.'},'department_denominators':groups,'comparisons':rows,'examples':examples,'checks':checks,'check_count':len(checks),'limits':['A larger machine count is a net difference, not an identification of exclusively added units or proof the added labels are correct.','Aggregate counts do not reveal the overlap or individual false positives/false negatives.','Attention uses each method’s own sum of five label occurrences, not distinct positive units and not the department unit count.','Coverage shares use the same unit denominator and are not the sum-normalized attention composition.','No reserved future-human text or labels opened; no source labels, manuscript or statistics changed.']}
(O/'分母与占比核查.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n')
lines=['# 两种编码方法的分母与占比核查','',f'从已冻结figure2_data按有理数核算15项差异，{len(checks)}项检查全部通过。范围为三部门全量4481个句段；方法为自动规则v36.2与完整LLM03。所有差值均为“LLM−自动规则”，未重新编码、抽样或计算显著性。','','每个句段可对应多个维度。同一维度的识别数，是被该方法编码为1的句段数；**覆盖比例**以本部门全部句段为共同分母；**注意力占比q**以该部门、该方法的五维标签次数之和为分母。后者不是去重后的阳性句段数。','','|部门|共同句段分母|规则五维次数分母|LLM五维次数分母|分母净增|','|---|---:|---:|---:|---:|']
for z in groups:lines.append(f"|{z['department']}|{z['common_unit_denominator']}|{z['rules_five_dimension_label_occurrence_denominator']}|{z['LLM_five_dimension_label_occurrence_denominator']}|+{z['label_occurrence_denominator_change']}|")
lines+=['','|部门|维度|规则→LLM计数|计数净差|覆盖率：规则→LLM（%）|覆盖率差（百分点）|q：规则→LLM（%）|q差（百分点）|','|---|---|---:|---:|---:|---:|---:|---:|']
for z in rows:
 lines.append(f"|{z['department']}|{z['dimension_name']}|{z['rules_count']}→{z['LLM_count']}|{z['net_count_change_LLM_minus_rules']:+d}|{z['rules_coverage_percent']['value']:.2f}→{z['LLM_coverage_percent']['value']:.2f}|{z['coverage_difference_percentage_points_LLM_minus_rules']['value']:+.2f}|{z['rules_attention_percent']['value']:.2f}→{z['LLM_attention_percent']['value']:.2f}|{z['attention_difference_percentage_points_LLM_minus_rules']['value']:+.2f}|")
lines+=['','两个例子：','']
for z in examples:
 lines.append(f"- **{z['department']}{z['dimension_name']}**：识别数{z['rules_count']}→{z['LLM_count']}（净增{z['net_count_change_LLM_minus_rules']}），覆盖率{z['rules_coverage_percent']['value']:.2f}%→{z['LLM_coverage_percent']['value']:.2f}%（+{z['coverage_difference_percentage_points_LLM_minus_rules']['value']:.2f}个百分点）；但五维次数分母{z['rules_q_denominator']}→{z['LLM_q_denominator']}，使q从{z['rules_attention_percent']['value']:.2f}%降至{z['LLM_attention_percent']['value']:.2f}%（{z['attention_difference_percentage_points_LLM_minus_rules']['value']:.2f}个百分点）。该维计数增加{z['count_relative_increase_percent']['value']:.2f}%，低于分母增加的{z['all_labels_relative_increase_percent']['value']:.2f}%。")
lines+=['','因此，q下降只表示该维在该方法全部五维标签次数中的份额下降，不能据此说该方法识别了更少的相关句段。反之，较高计数也不证明额外识别均正确：这里是两种方法的净计数差，并未识别仅LLM阳性的新增单元，更未判定这些单元的真实性。个体误差仍须依据原句及独立参照核验。','','审计恒等式（不增设论文指标）：令c为该维次数、T为五维次数总和，则q_L−q_R=[(c_L−c_R)T_R−c_R(T_L−T_R)]/(T_RT_L)。每个部门五维q差精确相加为0，反映构成分母约束。','','全部精确分数、源payload路径/SHA与方法ID见同名JSON。未读取未来真人样本，未修改文稿或原始统计。']
(O/'分母与占比核查.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'status':res['status'],'checks':len(checks),'outputs':[b(O/'分母与占比核查.json'),b(O/'分母与占比核查.md')],'examples':[{'department':z['department'],'dimension':z['dimension_name'],'count_delta':z['net_count_change_LLM_minus_rules'],'coverage_pp':z['coverage_difference_percentage_points_LLM_minus_rules']['value'],'q_pp':z['attention_difference_percentage_points_LLM_minus_rules']['value']}for z in examples]},ensure_ascii=False,indent=2))
