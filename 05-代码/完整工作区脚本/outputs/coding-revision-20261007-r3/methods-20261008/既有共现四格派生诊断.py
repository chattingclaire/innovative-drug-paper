from pathlib import Path
from fractions import Fraction
import json,hashlib,collections
R=Path('/PROJECT_ROOT/outputs/coding-revision-20261007-r3'); D=R/'methods-20261008'; I=R/'insights-20261008'
files=[I/'完整十对共现.json',I/'共现稳定性计算.json']
base=json.loads(files[0].read_text());stab=json.loads(files[1].read_text())
keys=['both_n','a_only_n','b_only_n','neither_n']
def calc(row):
 vals=[Fraction(row[k]) for k in keys];a,b,c,d=vals;n=sum(vals)
 den=b*c;num=a*d
 return {'dimension_a':row.get('dimension_a','F'),'dimension_b':row.get('dimension_b','Ec'),'four_cells':{k:float(v) for k,v in zip(keys,vals)},'four_cells_exact':{k:str(v) for k,v in zip(keys,vals)},'OR':float(num/den) if den else None,'OR_exact':str(num/den) if den else None,'NA_reason':None if den else 'a_only*b_only is zero; no correction or infinity substitution','P_B_given_A':float(a/(a+b)) if a+b else None,'P_B_given_nonA':float(c/(c+d)) if c+d else None,'B_base_rate':float((a+c)/n) if n else None}
allrows=[]
for r in base['results']:
 for pair in r['pairs']:
  allrows.append({**{k:r[k] for k in ['scope','method','department','unit_n']},**calc(pair)})
def difference(rows):
 a,b=rows['NHSA']['OR'],rows['NHC']['OR'];return {'NHSA_minus_NHC_OR':None if a is None or b is None else a-b,'direction': 'NA' if a is None or b is None else ('NHSA_higher' if a>b else 'NHC_higher' if a<b else 'equal')}
def balanced(clusters):
 G=len(clusters);cells={k:sum((Fraction(x[k],x['unit_n']) for x in clusters.values()),Fraction(0))/G for k in keys}
 return calc({'dimension_a':'F','dimension_b':'Ec',**cells})
cs=[]
for r in stab['composition56']:
 out={'scenario':r['scenario'],'omitted_policy_entry':r['omitted_policy_entry'],'methods':{}}
 for meth in ['rules','LLM']:
  deps={};cl={};kind='raw pooled four-cell OR'
  for dep,x in r['methods'][meth]['departments'].items():
   if 'cluster_counts' in x:
    kind='OR of equally averaged cluster-specific four-cell probabilities; all clusters retained, including zero-F. Not mean of ORs; not conditional/file-adjusted OR.'
    deps[dep]=balanced(x['cluster_counts']);cl[dep]={name:calc(y) for name,y in x['cluster_counts'].items()}
   else:deps[dep]=calc(x)
  out['methods'][meth]={'estimand':kind,'departments':deps,'cluster_OR_if_available':cl,**difference(deps)}
 cs.append(out)
ds=[]
for r in stab['definition6']:
 out={'scenario':r['scenario'],'explanation':r['explanation'],'methods':{}}
 for meth in ['rules','LLM']:
  out['methods'][meth]={}
  for scope in ['full4481','same180']:
   deps={dep:calc(x) for dep,x in r['methods'][meth][scope]['departments'].items()}
   out['methods'][meth][scope]={'departments':deps,**difference(deps)}
 ds.append(out)
summary={}
for meth in ['rules','LLM']:
 summary[meth]={}
 for label,rr in [('composition56', [x['methods'][meth] for x in cs]),('composition_raw54',[x['methods'][meth] for x in cs if x['scenario'] not in ['policy_file_equal','policy_series_equal']]),('definition6',[x['methods'][meth]['full4481'] for x in ds])]:
  cnt=dict(collections.Counter(x['direction'] for x in rr));vals=[x['NHSA_minus_NHC_OR'] for x in rr if x['NHSA_minus_NHC_OR'] is not None]
  summary[meth][label]={'scenario_n':len(rr),'direction_counts':cnt,'difference_range':[min(vals),max(vals)] if vals else None}
out={'scope':'Post-hoc baseline interpretation diagnosis only; no significance tests, CI, model changes or novelty screening. OR=(both*neither)/(a_only*b_only); zero denominator NA, no 0.5 correction. All existing 10 pairs reported without selection. Formal machine methods rules v33 and LLM; development and AI reference rows only separately identified inherited supplemental data.','source_bindings':[{'path':str(f),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in files],'all10_pairs_all_existing_scopes':allrows,'F_Ec_composition56':cs,'F_Ec_definition6':ds,'summary':summary,'boundaries':['Higher P(Ec|F) does not imply higher OR. OR is unadjusted, descriptive and noncausal.','Equal-cluster mixture OR does not adjust within-file confounding and is not comparable as the same estimand to mean P(Ec|F).','54 raw composition cases plus 2 equal-cluster mixture cases are separately summarized; 56 scenarios are dependent sensitivity cases, not replications.','A/C/candidate are AI reference, sample180 not equivalent to corpus4481; zero/sparse cells limit comparisons.']}
(D/'基率解释诊断_OR.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
md=['# 基率解释诊断：条件比例与关联强度不能混写','', '本补充只从已经保存的完整四格复算，未读取或改变标签。两正式方法、三部门、全部10对均保留，不做显著性筛选；另保留既有AI参考与开发方法的同口径行，均注明作用域。OR=共同阳性×共同阴性/(仅A阳性×仅B阳性)，分母为零留NA，不加0.5。','', '主发现能说“医保F条款中Ec表达的绝对比例更高”；不能说“医保F与Ec的关联强度更大”。全量四格的OR恰是卫健更大。这个逆向结果只用于防止误读，不再包装为另一项创新发现。','', '|方法|部门|F∩Ec / 仅F / 仅Ec / 均无|P(Ec\|F)|P(Ec\|非F)|全部Ec基率|OR|','|---|---|---|---:|---:|---:|---:|']
for meth in ['rules','LLM']:
 for dep in ['NHSA','NHC']:
  x=cs[0]['methods'][meth]['departments'][dep];a=x['four_cells'];md.append('|'+ '|'.join([meth,dep,' / '.join(str(int(a[k])) for k in keys),f"{x['P_B_given_A']*100:.2f}%",f"{x['P_B_given_nonA']*100:.2f}%",f"{x['B_base_rate']*100:.2f}%",f"{x['OR']:.4f}"])+ '|')
md+=['','这里OR比较的是各部门内部F与非F条款的Ec优势比，再比较两部门数值。它没有控制文件类型、系列重复、时期或部门职责；不能据此推断因果、经过控制的独立关联，亦不能只凭OR刻画更公平。','', '|方法|情景组|卫健OR较高|医保OR较高|相等|NA|医保−卫健OR范围|','|---|---|---:|---:|---:|---:|---:|']
for meth,sm in summary.items():
 for label,x in sm.items():
  c=x['direction_counts'];rr=x['difference_range'];md.append('|'+ '|'.join([meth,label,str(c.get('NHC_higher',0)),str(c.get('NHSA_higher',0)),str(c.get('equal',0)),str(c.get('NA',0)), 'NA' if rr is None else f'{rr[0]:.4f} 至 {rr[1]:.4f}'])+'|')
md+=['','54个原始条目构成情景直接复用保存的四格。文件等权、系列等权两情景不能用“平均条件比例”反推出OR，因此另以每簇四格占比等权混合后算OR，保留所有簇包括F=0簇；完整JSON也保留每簇原始OR和NA。这只是另一构成口径，既不是OR的算术均值，也不是文件固定效应或分层调整OR。56情景不是56次独立复制；没有新增bootstrap、检验或区间。','', '六个定义情景均复用旧情景。去除clinical-management-only F与dimension-information-only F只是既有标签的敏感性口径，不重写公平性构念。其完整四格和OR见JSON；同180的结果另列，不能与全量描述混合。','', '所有10对既有四格均已计算（包括S/E/Ec/I/F），不根据最大OR选择新故事。稀有I、药监Ec以及小样本大量零格意味着部分OR无定义；NA就是缺少可比较信息，不能填成0或“无关联”。','', '与既有P(Ec|F)稳定性并不冲突：医保的Ec总体基率和非F条款Ec率也高。分母与问题不同，绝对条件比例方向与相对优势比方向完全可以相反。原文和访谈可解释支付/使用路径，但不能把同句共现直接当机制已经检验。']
(D/'基率解释诊断_OR.md').write_text('\n'.join(md)+'\n')
print(json.dumps(summary,ensure_ascii=False));print('all pairs',len(allrows))
# Additional interpretation checks requested after the initial OR output.
def extra(x):
 a,b,c,d=[Fraction(x[k]) for k in keys]
 p=a/(a+b) if a+b else None;q=c/(c+d) if c+d else None
 return {'F_Ec_raw_cells':{k:float(v) for k,v in zip(keys,[a,b,c,d])},'P_Ec_given_F':float(p) if p is not None else None,'P_Ec_given_nonF':float(q) if q is not None else None,'additive_difference':float(p-q) if p is not None and q is not None else None,'P_F_given_Ec':float(a/(a+c)) if a+c else None}
def revrows(r):
 result={'scenario':r['scenario'],'omitted_policy_entry':r.get('omitted_policy_entry'),'methods':{}}
 for meth in ['rules','LLM']:
  deps={}
  for dep,x in r['methods'][meth]['departments'].items():
   if 'cluster_counts' not in x:deps[dep]=extra(x)
   else:
    pairs=[(name,extra(v)) for name,v in x['cluster_counts'].items()];good=[y['P_F_given_Ec'] for _,y in pairs if y['P_F_given_Ec'] is not None]
    deps[dep]={'P_F_given_Ec':sum(good)/len(good) if good else None,'estimand':'Equal mean of cluster-specific P(F|Ec), excluding explicitly NA zero-Ec clusters. Not same as equal-cluster cell-mixture conditional ratio.','defined_Ec_cluster_n':len(good),'all_cluster_n':len(pairs),'zero_Ec_clusters_excluded':[name for name,y in pairs if y['P_F_given_Ec'] is None],'cluster_results':dict(pairs)}
  a,b=deps['NHSA']['P_F_given_Ec'],deps['NHC']['P_F_given_Ec'];result['methods'][meth]={'departments':deps,'NHSA_minus_NHC_P_F_given_Ec_pp':(a-b)*100 if a is not None and b is not None else None,'direction':'NA' if a is None or b is None else 'NHSA_higher' if a>b else 'NHC_higher' if a<b else 'equal'}
 return result
revcomp=[revrows(r) for r in stab['composition56']]
revdef=[revrows({'scenario':r['scenario'],'methods':{m:r['methods'][m]['full4481'] for m in ['rules','LLM']}}) for r in stab['definition6']]
revs={}
for meth in ['rules','LLM']:
 revs[meth]={}
 for name,rs in [('composition56',revcomp),('definition6',revdef)]:
  xs=[x['methods'][meth] for x in rs];vv=[x['NHSA_minus_NHC_P_F_given_Ec_pp'] for x in xs if x['NHSA_minus_NHC_P_F_given_Ec_pp'] is not None]
  revs[meth][name]={'directions':dict(collections.Counter(x['direction'] for x in xs)),'NHSA_minus_NHC_range_pp':[min(vv),max(vv)] if vv else None}
out['additive_and_reverse_conditional_diagnostic']={'primary':revcomp[0],'composition56':revcomp,'definition6':revdef,'summary':revs,'interpretation':'Additive conditional-probability contrasts and odds-ratio contrasts can rank departments differently. Reverse conditioning answers another denominator-specific description; it is not independent confirmation of mechanism or adjusted association.'}
(D/'基率解释诊断_OR.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
add=['','## 同一四格的加法差与反向条件（补充）','', '|方法|医保 P(Ec给定F)−P(Ec给定非F)|卫健对应差|部门比较|医保 P(F给定Ec)|卫健 P(F给定Ec)|','|---|---:|---:|---|---:|---:|']
for meth in ['rules','LLM']:
 x=revcomp[0]['methods'][meth]['departments'];a=x['NHSA'];b=x['NHC'];add.append(f"|{meth}|{a['additive_difference']*100:.4f} 个百分点|{b['additive_difference']*100:.4f} 个百分点|{'医保较高' if a['additive_difference']>b['additive_difference'] else '卫健较高'}|{a['P_F_given_Ec']*100:.2f}%|{b['P_F_given_Ec']*100:.2f}%|")
add+=['','加法比例差的部门排序在两方法间不一致；粗OR则两方法均为卫健更高。两者衡量不同尺度，不存在不注明指标就能概括的“关联更强”。此处不选择更有利的尺度作新故事。','', '|方法|反向条件情景组|卫健较高|医保较高|NA|医保−卫健范围（百分点）|','|---|---|---:|---:|---:|---:|']
for meth,ss in revs.items():
 for name,x in ss.items():
  c=x['directions'];rr=x['NHSA_minus_NHC_range_pp'];add.append(f"|{meth}|{name}|{c.get('NHC_higher',0)}|{c.get('NHSA_higher',0)}|{c.get('NA',0)}|{rr[0]:.4f} 至 {rr[1]:.4f}|")
add+=['','全量反向分母是Ec条款：规则卫健14/31、医保101/609；LLM卫健13/31、医保145/682。文件/系列等权的反向条件采用“簇内P(F|Ec)的等权平均”，仅排除Ec=0导致NA的簇，全部排除名单和分母保留在JSON；54个其他情景仍用原始四格。它和前述等权混合四格OR是不同目标量，不能混为控制后的结果。','', '反向条件即使方向稳定，也受F/Ec边际率、条款功能和文件构成影响；没有增加独立实证资料或机制识别。原条件比例、反向条件、加法差和OR在此全部列出，目的只是防止单一方向被过度解读。']
with (D/'基率解释诊断_OR.md').open('a') as f:f.write('\n'.join(add)+'\n')
print('reverse',json.dumps(revs,ensure_ascii=False))
