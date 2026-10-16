from pathlib import Path
import json,csv,hashlib,importlib.util,collections,itertools
ROOT=Path('outputs/goal-calibration-20261010').resolve()
OUT=ROOT/'11-version-comparison-20261014/后台统计图表-20261014'
PREP=ROOT/'07-statistics/full4481-attention-robustness-preparation-sol'
spec=importlib.util.spec_from_file_location('engine',PREP/'full4481_attention_robustness.py'); eng=importlib.util.module_from_spec(spec);spec.loader.exec_module(eng)
D=['S','E','Ec','I','F']; Z=dict(zip(D,['安全性','有效性','经济性','创新性','公平性'])); DEPS=['NMPA','NHSA','NHC']; ZDEP=dict(zip(DEPS,['药监局','医保局','卫健委']))
FILES={'LLM':ROOT/'07-statistics/original-whole-batch-native-full4481-cap13-root/selected-records.jsonl','rule':ROOT/'06-coding/rule-full4481-v2-root/run4481-first/predictions.jsonl'}
meta=[json.loads(x) for x in (PREP/'unit-metadata.jsonl').read_text().splitlines()]; entries=json.loads((PREP/'source-entry-metadata.json').read_text()); em={x['source_entry_id']:x for x in entries}
def save(name,data): (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def bind(p):return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def agg(rows,w):
 a=eng.aggregate(rows,w);a.pop('fractional_hit_share_r');return a
def cond(rows,w,a,b):
 complete=[r for r in rows if r['labels'][a] is not None and r['labels'][b] is not None]
 numerator=sum(w[r['unit_id']] for r in complete if r['labels'][a]==r['labels'][b]==1)
 denominator=sum(w[r['unit_id']] for r in complete if r['labels'][b]==1)
 required=[];optional=[]
 for r in rows:
  av,bv=r['labels'][a],r['labels'][b];v=(0 if av is None else av,1 if av is None else av,w[r['unit_id']])
  if bv==1:required.append(v)
  elif bv is None:optional.append(v)
 return {'positive_pair':numerator,'complete_condition_positive':denominator,'observed':eng.div(numerator,denominator),'both_binary_N':len(complete),'pair_unresolved_N':len(rows)-len(complete),'bounds':eng.mean_bounds(required,optional)}
def summarize(rows,w):
 s=agg(rows,w);s['conditionals']={f'{a}_given_{b}':cond(rows,w,a,b) for a,b in [('E','S'),('F','Ec')]};return s
def mean_summary(rows,key):
 s=eng.means(rows,key);groups=collections.defaultdict(list)
 for r in rows:groups[key(r)].append(r)
 s['conditionals']={}
 for a,b in [('E','S'),('F','Ec')]:
  vals=[cond(g,eng.weights(g,'clause_equal','policy_year'),a,b) for g in groups.values()]
  defined=[v['observed'] for v in vals if v['observed'] is not None]
  required=[(v['bounds']['lower'],v['bounds']['upper'],1) for v in vals if not v['bounds']['undefined_possible']]
  optional=[(v['bounds']['lower'],v['bounds']['upper'],1) for v in vals if v['bounds']['undefined_possible'] and v['bounds']['lower'] is not None]
  s['conditionals'][f'{a}_given_{b}']={'observed':eng.div(sum(defined),len(defined)),'defined_member_N':len(defined),'member_N':len(vals),'bounds':eng.mean_bounds(required,optional)}
 return s
def q(s,d):return s['dimensions'][d].get('q_observed',s['dimensions'][d].get('q_mean_among_observed_positive_members'))
def p(s,d):return s['dimensions'][d].get('p_conditional_lower',s['dimensions'][d].get('p_mean_conditional_lower'))
def top(s):return [d for d in D if q(s,d)==max(q(s,x) for x in D)]
allresults={}
for method,path in FILES.items():
 preds=[json.loads(x) for x in path.read_text().splitlines()]; byid={x['id']:x for x in preds};assert len(byid)==len(meta)==4481
 rows=[dict(m,labels=byid[m['unit_id']]['labels']) for m in meta]
 for r in rows:assert all(v in (0,1,None) for v in r['labels'].values())
 scenario_specs={
 '条款等权':(rows,'clause_equal'),
 '来源内同年精确重复降权':(rows,'text_repeat_same_source'),
 '部门年度内精确重复降权':(rows,'text_repeat_department_year'),
 '剔除联合来源':([r for r in rows if not em[r['source_entry_id']]['joint_publication']],'clause_equal'),
 '剔除年度系列来源':([r for r in rows if not em[r['source_entry_id']]['annual_series']],'clause_equal'),
 '剔除多组件来源':([r for r in rows if em[r['source_entry_id']]['listed_component_n']==1],'clause_equal'),
 '限定2018至2025年':([r for r in rows if 2018<=r['policy_year']<=2025],'clause_equal')}
 scenarios={}
 for name,(selected,mode) in scenario_specs.items():
  w=eng.weights(selected,mode,'policy_year');scenarios[name]={dep:summarize([r for r in selected if r['department']==dep],w) for dep in DEPS}
 for name,key in [('来源等权均值',lambda r:r['source_entry_id']),('系列年度成员均值',lambda r:(r['department'],r['policy_year'],em[r['source_entry_id']]['policy_series']))]:
  scenarios[name]={dep:mean_summary([r for r in rows if r['department']==dep],key) for dep in DEPS}
 leave=[]
 for e in entries:
  selected=[r for r in rows if r['source_entry_id']!=e['source_entry_id']];w=eng.weights(selected,'clause_equal','policy_year')
  leave.append({'removed_source':e['source_entry_id'],'department':e['department'],'statistics':{dep:summarize([r for r in selected if r['department']==dep],w) for dep in DEPS}})
 allresults[method]={'whole':summarize(rows,eng.weights(rows,'clause_equal','policy_year')),'scenarios':scenarios,'leave_one_source_out':leave}
save('统计及稳健性完整结果.json',{'inputs':{k:bind(v) for k,v in FILES.items()},'metadata':{p.name:bind(p) for p in [PREP/'unit-metadata.jsonl',PREP/'source-entry-metadata.json']},'engine':bind(PREP/'full4481_attention_robustness.py'),'script':bind(Path(__file__).resolve()),'model_calls':0,'results':allresults,'notes':['未修改任何标签；描述性统计不设0.8合格线。','条款占比为已知正例/全部条款，待定另列；五维构成为已知正例/五维已知正例总数。','条件比例为两维均有二元判断时，条件维度=1的条款中目标维度=1的比例。','NULL界限是各待定维度可分别取0/1的敏感性范围，不是置信区间。','来源/系列均值对分母大于0的成员取均值，零分母不记为0。','来源条目51个，不等同于56个独立组件；未臆造组件归属。']})
base=allresults['LLM']['scenarios']['条款等权'];table=[]
for dep in DEPS:
 s=base[dep]
 for d in D:
  a=s['dimensions'][d];table.append({'部门':ZDEP[dep],'维度':Z[d],'条款数':s['clause_N'],'正标签数':int(a['positive_weight']),'负标签数':int(a['negative_weight']),'待定数':int(a['unresolved_weight']),'五维正标签累计数':int(s['positive_assignment_weight']),'条款占比':p(s,d),'五维构成比例':q(s,d),'条款占比上界':a['p_conditional_upper'],'五维构成下界':a['q_conditional_lower'],'五维构成上界':a['q_conditional_upper']})
save('LLM三部门双口径表.json',table)
with (OUT/'LLM三部门双口径表.csv').open('w',encoding='utf-8-sig',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=table[0]);writer.writeheader();writer.writerows(table)
lines=['# 77条校准对应旧版LLM：4481条全量统计','', '|部门|条款数|安全性|有效性|经济性|创新性|公平性|正标签累计数|待定判断数|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
for dep,s in base.items():lines.append('|'+ '|'.join([ZDEP[dep],str(s['clause_N'])]+[str(int(s['dimensions'][d]['positive_weight'])) for d in D]+[str(int(s['positive_assignment_weight'])),str(int(s['unresolved_assignment_weight']))])+'|')
for title,key in [('条款占比：维度正标签数÷本部门全部条款数','p'),('五维构成：维度正标签数÷本部门五维正标签累计数','q')]:
 lines+=['','## '+title,'','|部门|安全性|有效性|经济性|创新性|公平性|','|---|---:|---:|---:|---:|---:|']
 for dep,s in base.items():lines.append('|'+ '|'.join([ZDEP[dep]]+[f'{(p if key=="p" else q)(s,d)*100:.2f}%' for d in D])+'|')
lines+=['','同一条款可以涉及多个维度，每维至多计一次。条款占比的五维合计不要求为100%；五维构成合计100%。待定未作为负标签，亦不计入已识别正标签。全量60项待定的上下界保存在配套JSON中。','']
(OUT/'全量双口径统计表.md').write_text('\n'.join(lines))
# Audit claims with exact exceptions, rather than importing later-version claims.
claims={}
checks={
 '医保局经济性构成高于卫健委':lambda s:q(s['NHSA'],'Ec')>q(s['NHC'],'Ec'),
 '药监局安全性居首':lambda s:top(s['NMPA'])==['S'],
 '医保局经济性居首':lambda s:top(s['NHSA'])==['Ec'],
 '卫健委安全性居首':lambda s:top(s['NHC'])==['S'],
 '医保局E给定S高于药监局':lambda s:s['NHSA']['conditionals']['E_given_S']['observed']>s['NMPA']['conditionals']['E_given_S']['observed'],
 '医保局E给定S高于卫健委':lambda s:s['NHSA']['conditionals']['E_given_S']['observed']>s['NHC']['conditionals']['E_given_S']['observed'],
 '卫健委F给定Ec高于医保局':lambda s:s['NHC']['conditionals']['F_given_Ec']['observed']>s['NHSA']['conditionals']['F_given_Ec']['observed']}
for method,result in allresults.items():
 claims[method]={name:{'nine_scenarios_pass_N':sum(check(s) for s in result['scenarios'].values()),'scenario_exceptions':[name2 for name2,s in result['scenarios'].items() if not check(s)],'leave_one_pass_N':sum(check(x['statistics']) for x in result['leave_one_source_out']),'leave_one_exceptions':[x['removed_source'] for x in result['leave_one_source_out'] if not check(x['statistics'])]} for name,check in checks.items()}
comparisons=[]
for a,b in itertools.combinations(DEPS,2):
 for d in D:
  values={method:q(r['scenarios']['条款等权'][a],d)-q(r['scenarios']['条款等权'][b],d) for method,r in allresults.items()}
  signs={m:(v>0)-(v<0) for m,v in values.items()};comparisons.append({'部门配对':[ZDEP[a],ZDEP[b]],'维度':Z[d],'差值':values,'同向':len(set(signs.values()))==1})
claims['两机15项五维构成比较']={'same_direction_N':sum(x['同向'] for x in comparisons),'comparisons':comparisons}
save('旧稿主张核查.json',claims)
print(json.dumps(claims,ensure_ascii=False,indent=2))
