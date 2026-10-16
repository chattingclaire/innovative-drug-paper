"""Add traceable r2 delivery tables; never rewrite sealed coding or source results."""
from pathlib import Path
from collections import Counter
import csv,datetime,hashlib,json

P=Path(__file__).resolve().parent;RUN=P.parent
DIMS=('S','E','Ec','I','F');NAMES={'S':'安全性','E':'有效性','Ec':'经济性','I':'创新性','F':'公平性'}
METRICS=('kappa','precision','recall','f1');GROUPS=('NMPA','NHSA','NHC')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
def jl(p):return {r['id']:r for r in map(json.loads,Path(p).read_text().splitlines())}
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def value(r,m):return r['metrics'][m]['estimate']
def fmt(v,n=4):return 'NA'if v is None else f'{v:.{n}f}'
def csvfile(path,rows,fields):
 with path.open('w',encoding='utf-8-sig',newline='')as f:
  w=csv.DictWriter(f,fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
def main():
 cpath=P/'最终机器参照比较.json';apath=P/'最终五维注意力与配对差值.json';acpath=P/'A_C协商前信度-v8.json';dpath=P/'正文重复剔除-v8-最终机器与参照.json'
 data=read(cpath);attention=read(apath);ac=read(acpath);deleted=read(dpath)
 qpaths=[P/'最终统计独立数值QA.json',P/'A_C协商前信度-v8独立QA.json',P/'正文重复剔除-v8独立数值QA.json']
 for p in qpaths:assert read(p)['status']=='passed'
 sources={str(p):sha(p)for p in[cpath,apath,acpath,dpath,*qpaths,Path(__file__)]}
 # Frozen source result hashes must still match their independently verified snapshots.
 for p in qpaths:
  for source,s in read(p)['source_sha256'].items():assert sha(source)==s,(p,source)
 current=[m for m in data['method_bindings']if not m.startswith('old_')];assert set(current)=={'rules_v32_1_material_v8','llm_v31_IF_v30_SEEc_material_v8'}
 rule=next(m for m in current if m.startswith('rules_'));llm=next(m for m in current if m.startswith('llm_'));family={rule:'old_rules_v31_v3',llm:'old_llm_v30_v3'}
 refs={c:jl(RUN/f'reference/agent_{c}_final_v8.jsonl')for c in('A','C')};refs['third_agent_candidate']=jl(P/'adjudicated_agent_reference_candidate_v8.jsonl')
 machines={m:jl(b['path'])for m,b in data['method_bindings'].items()}
 label=lambda row,d:row.get('prediction',row)['labels'][d]
 records=data['records'];lookup={(r['method'],r['reference'],r['component'],r['group'],r['weighting'],r['dimension']):r for r in records}
 flat=[];diffs=[]
 for r in records:
  for metric in METRICS:
   m=r['metrics'][metric];ci=m['ci95_primary'];sf=m['ci95_source_file_conditional_sensitivity']
   flat.append({**{k:r[k]for k in('component','group','weighting','method','reference','dimension','paired_n','left_positive_n','reference_positive_n')},
    'comparison_role':r['comparison_role'],'metric':metric,'estimate':m['estimate'],'CI95_low':ci['low'],'CI95_high':ci['high'],
    'conditional_source_file_CI95_low':sf['low'],'conditional_source_file_CI95_high':sf['high'],'diagnostic_0_80':r['point_0_80_diagnostics'][metric],
    **r['raw_confusion']})
  fp=[];fn=[]
  for rid in r['paired_ids']:
   pair=label(machines[r['method']][rid],r['dimension']),label(refs[r['reference']][rid],r['dimension'])
   if pair==(1,0):fp.append(rid)
   elif pair==(0,1):fn.append(rid)
  assert len(fp)==r['raw_confusion']['FP']and len(fn)==r['raw_confusion']['FN']
  diffs.append({**{k:r[k]for k in('component','group','weighting','method','reference','dimension','paired_n')},'relative_FP_IDs':fp,'relative_FN_IDs':fn,
   'interpretation':'Relative to named agent reference; not a proven semantic error or real-human ground truth.'})
 for r in ac['records']:
  if r['reference_version']!='final_v8':continue
  m=r['metrics']['kappa'];ci=m['ci95_primary'];sf=m['ci95_source_file_conditional_sensitivity']
  flat.append({**{k:r[k]for k in('component','group','weighting','method','reference','dimension','paired_n','left_positive_n','reference_positive_n')},
   'comparison_role':'before_adjudication_current_agent_A_C','metric':'kappa','estimate':m['estimate'],'CI95_low':ci['low'],'CI95_high':ci['high'],
   'conditional_source_file_CI95_low':sf['low'],'conditional_source_file_CI95_high':sf['high'],'diagnostic_0_80':r['point_0_80_diagnostics']['kappa'],**r['raw_confusion']})
 assert len(flat)==2205 and len(diffs)==540
 low=[r for r in flat if r['diagnostic_0_80']!='at_least_0_80']
 fields=['component','group','weighting','comparison_role','method','reference','dimension','metric','paired_n','left_positive_n','reference_positive_n','TP','FP','FN','TN','estimate','CI95_low','CI95_high','conditional_source_file_CI95_low','conditional_source_file_CI95_high','diagnostic_0_80']
 diagnostic={'target_role':'0.80 work-target diagnostic on point estimates; neither a universal publication criterion nor an equivalence margin; CI lower bounds are not required>=.80.',
  'human_validation_completed':False,'all_points_n':len(flat),'current_machine_points_n':1080,'historical_machine_points_n':1080,'current_A_C_kappa_points_n':45,
  'all_points':flat,'below_or_undefined_points':low,'counts_by_role':{},'source_sha256':sources}
 for role in sorted({r['comparison_role']for r in flat}):diagnostic['counts_by_role'][role]=dict(Counter(r['diagnostic_0_80']for r in flat if r['comparison_role']==role))
 write(P/'最终逐项指标诊断-v8.json',diagnostic);csvfile(P/'最终全部点指标-v8.csv',flat,fields);csvfile(P/'最终低值与未定义逐项清单-v8.csv',low,fields)
 write(P/'最终机器与参照分歧编号-v8.json',{'scope':'Classification comparison diagnostic IDs only. FP/FN are relative to agent reference, not final semantic truth.','records':diffs,'source_sha256':sources})
 contrasts=[]
 for method,oldmethod in family.items():
  for r in records:
   if r['method']!=method:continue
   old=lookup[(oldmethod,r['reference'],r['component'],r['group'],r['weighting'],r['dimension'])]
   for metric in METRICS:
    before=value(old,metric);after=value(r,metric);delta=None if before is None or after is None else after-before
    contrasts.append({**{k:r[k]for k in('component','group','weighting','reference','dimension','paired_n','reference_positive_n')},'old_method':oldmethod,'new_method':method,'metric':metric,
     'old_value':before,'new_value':after,'new_minus_old':delta,'point_change':'undefined'if delta is None else'increased'if delta>1e-12 else'decreased'if delta< -1e-12 else'unchanged',
     'old_TP':old['raw_confusion']['TP'],'old_FP':old['raw_confusion']['FP'],'old_FN':old['raw_confusion']['FN'],'new_TP':r['raw_confusion']['TP'],'new_FP':r['raw_confusion']['FP'],'new_FN':r['raw_confusion']['FN']})
 assert len(contrasts)==1080
 write(P/'最终旧新方法变化-v8.json',{'interpretation':'Historical methods use v3 material and current methods v8; method+material descriptive contrast, not pure prompt/code causal effects or a paired statistical significance claim.','point_change_counts':dict(Counter(r['point_change']for r in contrasts)),'records':contrasts,'source_sha256':sources})
 csvfile(P/'最终旧新方法变化-v8.csv',contrasts,list(contrasts[0]))
 core=[r for r in records if r['method']in current and r['component']=='probability_base'and r['group']=='ALL'and r['weighting']=='unweighted']
 rows=[]
 for r in core:
  out={k:r[k]for k in('method','reference','dimension','paired_n','reference_positive_n')};out.update(r['raw_confusion'])
  for m in METRICS:out[m]=value(r,m);out[m+'_CI95_low']=r['metrics'][m]['ci95_primary']['low'];out[m+'_CI95_high']=r['metrics'][m]['ci95_primary']['high']
  rows.append(out)
 csvfile(P/'核心指标表-概率240-v8.csv',rows,list(rows[0]))
 select=lambda m,c,d,g='ALL',w='unweighted',ref='third_agent_candidate':lookup[(m,ref,c,g,w,d)]
 acmain={r['dimension']:r for r in ac['records']if r['reference_version']=='final_v8'and r['component']=='probability_base'and r['group']=='ALL'and r['weighting']=='unweighted'}
 lines=['# 第二轮v8实际统计结果','',
 '本轮300条是专家agent预验证：240条部门分层概率样本与60条富集挑战分别分析，A/C在协商前独立提交，第三agent审查46个不同单元。全部执行者为agent，未完成真人验证。现因用于第三轮方法修订，300条登记为开发/培训材料，不能再确认第三轮方法。原始提交、v6结果及本轮v8机器输出保持不变。','',
 '概率样本的未加权总体结果如下；κ、精确率P、召回率R及F1分别报告，不以0.80作为统一发表条件。完整A/C各自对照、分部门、可用框加权总体、挑战结果及区间见对应CSV/JSON。','',
 '|维度|A—C κ|规则—候选 κ|规则P|规则R|规则F1|LLM—候选 κ|LLM P|LLM R|LLM F1|候选正类n|',
 '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
 for d in DIMS:
  r=select(rule,'probability_base',d);l=select(llm,'probability_base',d)
  lines.append('|'+ '|'.join([NAMES[d],fmt(value(acmain[d],'kappa')),*[fmt(value(r,m))for m in METRICS],*[fmt(value(l,m))for m in METRICS],str(r['reference_positive_n'])])+'|')
 lines+=['','规则公平性相对候选参照为16个TP、1个FP、20个FN，召回率44.44%，κ=0.5616。该结果表现为漏识别偏多。LLM创新性为10个TP、3个FP、0个FN，精确率76.92%，κ=0.8631；其扩大识别的同时仍有相对多判。相对候选的FP/FN不能直接当成已由真人证实的错误，全部分歧编号已另存。','',
 '在概率样本上，旧LLM→新LLM的创新性κ由0.9452降至0.8631，P由1降至0.7692，R由0.9升至1；公平性κ由0.7747升至0.8039，P由0.8710降至0.8333，R由0.75升至0.8333。旧规则→新规则的概率样本创新性点值不变；公平性κ由0.5763降至0.5616，R仍为0.4444，新增1个相对FP。旧方法使用v3材料、新方法使用v8材料，这些是方法与材料合并变化的描述，不能解释为纯提示词或代码的因果效果。','',
 '挑战60条对候选参照：','',
 '|维度|规则κ|规则P|规则R|规则F1|LLMκ|LLM P|LLM R|LLM F1|候选正类n|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
 for d in DIMS:
  r=select(rule,'enriched_challenge',d);l=select(llm,'enriched_challenge',d)
  lines.append('|'+ '|'.join([NAMES[d],*[fmt(value(r,m))for m in METRICS],*[fmt(value(l,m))for m in METRICS],str(r['reference_positive_n'])])+'|')
 lines+=['','挑战创新性：规则κ由0.4146升至0.5909，LLM由0.6863升至0.9149；挑战公平性：规则κ仍为0.4970，LLM由0.4886升至0.7000。不能把挑战改善概括为所有分布或所有样本均改善。','',
 '全4481条三部门文本的五维注意力占比如下，分母为各方法、各部门的五维编码句次总数：','',
 '|方法|部门|安全性%|有效性%|经济性%|创新性%|公平性%|','|---|---|---:|---:|---:|---:|---:|']
 for m in current:
  for g,r in attention['full_4481_attention'][m].items():lines.append('|'+ '|'.join(['自动规则'if m==rule else'LLM',g,*[fmt(100*r['shares'][d],2)for d in DIMS]])+'|')
 lines+=['','主口径中，两条机器方法均为药监安全性第一、有效性第二，医保经济性第一、公平性第二；卫健部门规则为安全性与公平性并列，LLM为公平性第一、安全性第二。主口径15项同维度部门间大小方向一致，不表示每个部门全部五维排序相同。','',
 '54个主口径、政策文本等权、政策系列等权及逐一删文口径中，药监安全性第一和医保经济性第一均保留；LLM药监有效性第二保留51/54，其余3个口径位次变化。15项部门方向全部一致的口径为44/54，其余7个有1项差异、3个有2项差异。卫健第一位在安全性与公平性之间变动，不能强行写成固定单维排序。','',
 '|全量差值：LLM−规则|点值/百分点|配对来源文件bootstrap 95%区间/百分点|','|---|---:|---|']
 for g,d in(('NMPA','I'),('NHSA','F')):
  r=next(r for r in attention['paired_full_corpus_rule_minus_LLM_difference_CIs']if(r['group'],r['dimension'])==(g,d));ci=r['ci95_paired_difference_percentage_points']
  lines.append(f'|{g} {NAMES[d]}|{fmt(-r["rule_minus_LLM_percentage_points"],4)}|[{fmt(-ci["high"],4)}, {fmt(-ci["low"],4)}]|')
 lines+=['','相较旧v3机器结果的6.1877及6.2135个百分点，两处差距现为6.4177及8.9855个百分点，均未收敛。该区间使用同一部门同一套来源文件重抽次数，同时重算两种方法各自的五维分母；它描述已观测文件组成的条件敏感性，不是语义真值或完整设计型测量误差区间。未预设等效界值，不据区间声称等效、可互换或存在统一可接受差值。','',
 '独立正文审计发现20条样本与已知开发材料的其他编号存在规范化正文重复，含概率18条、挑战2条。保留原240/60样本和设计权重，另列剔除后的222/58描述性敏感性；该子集不继承原固定设计的代表性或有限总体修正。概率主估计仅对应开发编号排除后的2962条可用框，不是全部4481条的真人估计，也不是保证正文未见的外部验证。','',
 '独立数值QA通过：540个机器比较、7560个分类区间、47个五维占比向量、220个占比/配对差值区间、324个稳健性部门向量；去重复敏感性520个比较、7040个区间、28个占比向量。无分母指标保持NA，完美一致的退化区间不外推为未见文本保证。主区间为非线性指标的有限总体重标度百分位近似，另报告按部门来源文件重抽的条件区间。','',
 '结果支持明确报告部门的主导关注及方法差异，但规则公平性漏识别和LLM创新性相对多判仍需在原文层面修订与另批确认，不能把本轮分数改写为全部合格。正文继续暂停；第三轮须与本轮分开报告。','']
 (P/'第二轮核心结果说明-v8.md').write_text('\n'.join(lines))
 # A compact failure taxonomy is a diagnostic interpretation, not a relabelling.
 taxonomy={'status':'reference_relative_diagnostic_not_semantic_ground_truth','classes':[
  {'type':'rule_F_underidentification','probability_reference':'third_agent_candidate','TP':16,'FP':1,'FN':20,'precision':16/17,'recall':16/36,'implication':'Prioritize actual clause scope/qualifying-object/availability and burden predicates in original text; counts alone do not locate a code bug.'},
  {'type':'LLM_I_overinclusive_tradeoff','probability_reference':'third_agent_candidate','TP':10,'FP':3,'FN':0,'precision':10/13,'recall':1,'implication':'Check innovation property vs ordinary procedure and specific supported object qualification; preserve contrary reference reasons.'},
  {'type':'LLM_F_recall_precision_tradeoff','old_probability_TP_FP_FN':[27,4,9],'new_probability_TP_FP_FN':[30,6,6],'implication':'Recall increased while precision decreased; challenge remains weaker. Do not label all apparent positives as confirmed mistakes.'},
  {'type':'rare_support_and_undefined','implication':'Department strata with no positive reference or no predicted positives produce NA precision/recall/kappa; no replacement with1.'},
  {'type':'material_scope_separate_from_classification','implication':'v8 added84 source contexts with0unit text edits, both methods same material. Context repair and semantic boundary refinement are distinct; no pure prompt/code effect claim.'}],
  'no_rules_or_labels_modified':True,'r2_300_now_development_training_for_r3':True,'source_sha256':sources}
 write(P/'第二轮故障归类参考-v8.json',taxonomy)
 # Verify exported dimensions/counts/changes and freeze all newly added delivery hashes.
 added=[P/name for name in('最终逐项指标诊断-v8.json','最终全部点指标-v8.csv','最终低值与未定义逐项清单-v8.csv','最终机器与参照分歧编号-v8.json','最终旧新方法变化-v8.json','最终旧新方法变化-v8.csv','核心指标表-概率240-v8.csv','第二轮核心结果说明-v8.md','第二轮故障归类参考-v8.json')]
 assert len(rows)==30 and len(contrasts)==1080 and all(r['dimension']in DIMS for r in flat)
 for path in sources:assert sha(path)==sources[path]
 qa={'status':'passed_added_delivery_tables_and_existing_numerical_QAs_bound','checked_at':datetime.datetime.now().astimezone().isoformat(),'all_point_indicators':len(flat),'low_or_undefined_points':len(low),'diagnostic_counts_by_role':diagnostic['counts_by_role'],'old_new_point_contrasts':len(contrasts),'comparison_diff_ID_sets':len(diffs),'core_probability_rows':len(rows),'source_sha256':sources,'added_output_sha256':{str(p):sha(p)for p in added},'no_existing_coding_or_statistic_files_modified':True}
 write(P/'第二轮报告与诊断表QA-v8.json',qa)
 print(json.dumps({k:v for k,v in qa.items()if k not in('source_sha256','added_output_sha256')},ensure_ascii=False))
if __name__=='__main__':main()
