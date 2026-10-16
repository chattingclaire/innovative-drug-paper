from pathlib import Path
from collections import Counter
import json,csv,hashlib,datetime

B=Path(__file__).resolve().parent
GOAL=B.parents[1]
AI=GOAL.parent/'ai-audit800-20261010'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,x):
 with (B/name).open('x',encoding='utf-8') as f:f.write(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
inputs=[B/'innovation-first22-sol/reviews.json',B/'innovation-last22-sol/reviews.json',B/'fairness-root-review.json']
rows=[]
for p in inputs:
 x=json.loads(p.read_text()); rr=x['rows'] if isinstance(x,dict) else x
 for r in rr:
  d=r.get('dimension',r.get('dim'))
  rows.append({'blind_id':r['blind_id'],'source_id':r['source_id'],'dimension':d,
   'ai':r.get('ai',r.get('AI')),'rule':r['rule'],'review_value':None if r['review_value']=='未定' else r['review_value'],
   'assessment':r['assessment'],'reason':r.get('reason',r.get('explanation')),
   'current_text':r.get('current_original',r.get('current_quote',r.get('current_text'))),
   'needs_human_review':r.get('needs_human_review',False) or r['assessment']=='AI不符合现手册',
   'detailed_review_file':str(p),'review_identity':'AI source-based semantic review, not human reference'})
assert len(rows)==66
assert len({(r['source_id'],r['dimension']) for r in rows})==66
actual={(r['原记录号'],r['维度']) for r in csv.DictReader((AI/'与规则法分歧清单.csv').open(encoding='utf-8-sig')) if r['维度'] in ('I','F')}
disagreements=[r for r in rows if r['ai']!=r['rule']]
assert {(r['source_id'],r['dimension']) for r in disagreements}==actual and len(actual)==53
counter={d:dict(Counter(r['assessment'] for r in disagreements if r['dimension']==d)) for d in ('I','F')}
assert counter['I']=={'手册边界待核':5,'规则遗漏依据':34,'AI不符合现手册':5}
assert counter['F']=={'规则遗漏依据':7,'手册边界待核':2}
need=[r for r in disagreements if r['needs_human_review']]
assert len(need)==13
write('joined-review.json',{'identity':'ROOT integrated AI semantic audit, seen prior outputs; not a new blind run',
 'scope':'all 44 I and 9 F disagreements, plus all 5 I and 8 F common positives',
 'input_bindings':[{'path':str(p),'sha256':sha(p)} for p in inputs],
 'assessment_counts':counter,'label_slots_reviewed':66,'disagreement_slots_reviewed':53,
 'original_labels_modified':False,'formal_acceptance_claimed':False,'rows':rows})
write('human-review-candidates.json',{'identity':'AI recommendations for targeted calibration; not human submissions',
 'count':13,'unresolved_boundaries':7,'AI_zero_recommendations_for_confirmation':5,
 'supported_one_with_additional_management_boundary_check':1,'rows':need})
lines=['需要核定的13项（7项未定、5项建议AI由1改0、1项建议维持1但需核管理服务边界）',
       '本清单是AI复审建议，不是已收到的真人结果。原800条AI初判及机器生产值均未修改。',
       '这些集中讨论/修改若用于调手册、规则或提示词，属于校准；不能再称本批材料未参与调试。正式检验需保留对应冻结版本与未参与调试的材料。','']
for i,r in enumerate(need,1):
 lines.extend([f"{i}. {r['blind_id']} / {r['source_id']} / {r['dimension']}",
  f"原AI={r['ai']}，原规则={r['rule']}；AI复审建议={r['review_value'] if r['review_value'] is not None else '未定'}；{r['assessment']}",
  '当前完整命题：'+r['current_text'],'待核依据：'+r['reason'],
  '完整材料：'+str(AI/'source-A/coder-A/materials'/f"{r['blind_id']}.html"),
  '逐条原文及同版证据：'+r['detailed_review_file'],''])
(B/'需核定的13项.txt').write_text('\n'.join(lines),encoding='utf-8')
metrics=json.loads((B/'descriptive-metrics.json').read_text())
report=['本轮不能凭93%一致率宣布编码正确。800条AI辅助抽检和规则法不是独立真人参照；下列指标只衡量双方一致程度。',
 '','800份完整材料bundle逐条canonical相同，手册、prompt和protocol均同SHA；输入版本差异已经排除。AI4000项均为二元值，规则有25项NULL，分维度各5项，未记成0或纳入二元一致率。',
 '','|维度|共同二元条数|AI=1|规则=1|双方=1|一致率|κ|阳性一致率|',
 '|---|---:|---:|---:|---:|---:|---:|---:|']
for r in metrics['by_dimension']:
 report.append(f"|{r['dimension']}|{r['joint_binary_N']}|{r['AI_positive_N_joint']}|{r['rule_positive_N_joint']}|{r['AI1_rule1']}|{r['agreement']:.2%}|{r['kappa']:.3f}|{r['positive_agreement']:.2%}|")
report+=['','阳性一致率=2×双方都判1的条数÷（AI判1数+规则判1数）。创新性为2×5/(49+5)=18.52%；分母并非真人核定的正确阳性数，因此不是准确率或对真人参照的F1。',
 '','逐条复审44项I分歧：34项有规则遗漏依据，5项AI不符合现手册，5项手册边界待核；9项F分歧：7项有规则遗漏依据，2项边界待核。13项共同阳性也已查核，均有现手册依据。这是AI核源意见，未经真人最终裁定，不据此声称AI正确率。其余S/E/Ec的225项分歧尚未做本次逐条语义复审。',
 '','规则遗漏主要涉及：创新对象与当前可用支持安排的关系、具名程序纳入后的优先服务和撤回、同版完整资格援引、数据保护表格基础分支与创新分类的待遇使用。只读代码/消费日志显示规则并非单纯只扫描当前句，已有CTX及完整来源叶文本扫描；部分遗漏发生在关系桥或短语覆盖。',
 '','AI放宽建议的5项均在I：A-000186（笼统特征调整）、375（原研身份与创新资格）、393（反馈识别泛称改进）、410（一般设计目标）、661（剂型局限/风险未明确具体改变）。建议值均0，保留原初判1；不能只因适老化、产品优化或原研身份就自动进入I。',
 '','待核7项：I的A-000018、019、165、242、717；F的A-000432、738。另A-000756建议维持I=1，但项目管理服务与一般行政义务边界也建议核定。与5项建议改0合计13项，完整材料、争点和证据路径在《需核定的13项.txt》。',
 '','当前保留抽样，不因阳性一致率低直接重抽。先统一边界并修正执行；若正式真人参照的某维阳性稀少且估计不确定性过大，再前瞻决定增加样本或对稀少候选层提高抽取量。预测0所在层也必须能抽到，以检查共同漏判；抽取概率和分析权重需要相应记录，不能把专项校准材料无权混入总体估计。200条只是已准备的较小工作量方案，尚未证明足以完成每维验证。',
 '','如后续使用本轮条目修订算法或提示词，应另存候选版本和校准曝光记录；当前冻结规则/正式LLM主运行不回写，当前未完整运行的LLM不与本轮结果混称。这些方法调整完成后，重新检验应使用未用于调整的材料，不能反复在同一批调到指标达标。',
 '','方法依据只保留两项：',
 '- [Cicchetti & Feinstein（1990），High agreement but low kappa: II](https://pubmed.ncbi.nlm.nih.gov/2189948/)：分别报告阳性和阴性一致性，避免只看总体一致率。',
 '- [Statistics Canada，Probability sampling](https://www150.statcan.gc.ca/n1/edu/power-pouvoir/ch13/prob/5214899-eng.htm)：分层概率抽样以已知抽取概率为基础；本项目是否增样，仍需按实际验证目标、费用和不确定性评估。']
(B/'核查报告.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
receipt={'at_utc':now,'kind':'new semantic and input-identity evidence; meaningful goal progress',
 'source_bundle_matches':800,'I_F_disagreements_reviewed':53,'common_positive_slots_reviewed':13,
 'AI_only_assessments':counter,'targeted_human_candidates':13,'source_versions_changed':False,
 'primary_predictions_changed':False,'formal_validation_complete':False,'sample_design_changed':False,
 'next_actions':['核定7个未定边界及建议改值，保留真人实际回覆身份','按完整关系修正候选规则/提示执行，另存冻结与校准曝光','补核S/E/Ec225项分歧和阴性抽检以检查共同遗漏','正式参照检验和样本精度评估完成后再进入论文写作'],
 'report':str(B/'核查报告.md')}
log=GOAL/'logs/root-ai800-disagreement-semantic-audit-reception-20261010.json'
with log.open('x',encoding='utf-8') as f:f.write(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
p=GOAL/'progress.json';progress=json.loads(p.read_text());progress['ai800_disagreement_semantic_audit_actual']=receipt
campaign=GOAL/'06-coding/native-full4481-v1-sol';selected=list(campaign.glob('batch-*/root-selection.json'))
n=sum(len(json.loads((s.parent/'first.json').read_text())['records']) for s in selected)
progress['current_fixed_full4481_execution_observation']={'at_utc':now,'scope':'native-full4481-v1-sol',
 'selected_batches':len(selected),'selected_records':n,'total_records':4481,'remaining_records':4481-n,
 'total_batches':504,'remaining_batches':504-len(selected),'controller_session_id':62929,
 'max_parallel':3,'all_primary_terminal':False,'only_terminal_selection_counted':True}
progress['updated_at_utc']=now;p.write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'reviewed_slots':66,'disagreements':53,'counts':counter,'targeted_human':len(need),'primary_selected_records':n},ensure_ascii=False))
