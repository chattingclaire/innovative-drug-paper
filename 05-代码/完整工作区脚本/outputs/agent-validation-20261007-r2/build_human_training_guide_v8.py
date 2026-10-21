"""Publish traceable candidate learning cases, never substitute agents for humans."""
from pathlib import Path
import json,hashlib,csv,collections
HERE=Path(__file__).resolve().parent;DIMS=['S','E','Ec','I','F'];NAMES={'S':'安全性','E':'有效性','Ec':'经济性','I':'创新性','F':'公平性'}
def jl(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def main():
 A={r['id']:r for r in jl(HERE/'reference/agent_A_final_v8.jsonl')};C={r['id']:r for r in jl(HERE/'reference/agent_C_final_v8.jsonl')};raw={r['id']:r for r in jl(HERE/'effective_blind_inputs_v8.jsonl')}
 mapping=json.loads((HERE/'admin/adjudication_mapping_PRIVATE.json').read_text());lookup={r['blind_id']:r for r in mapping};adj={};sources={}
 for p in sorted((HERE/'adjudication').glob('结果-*.json')):
  d=json.loads(p.read_text());sources[str(p.resolve())]=sha(p)
  for r in d['rows']:
   rid=lookup[r['id']]['original_id'];assert rid not in adj;adj[rid]=r
 newmap={m['blind_id']:m for m in json.loads((HERE/'admin/adjudication_v8_mapping_PRIVATE.json').read_text())}
 for p in sorted((HERE/'adjudication-v8').glob('结果-*.json')):
  d=json.loads(p.read_text());sources[str(p.resolve())]=sha(p)
  for r in d['rows']:adj[newmap[r['id']]['original_id']]=r
 assert len(adj)==46
 sample={r['original_id']:r for r in json.loads((HERE/'admin/sampling_design.json').read_text())['sample']}
 candidate=[];joint_overruled=[];needs_human=[]
 for rid in sorted(A):
  if rid in adj:
   r=adj[rid];source='third_agent_disagreement_adjudication' if A[rid]['labels']!=C[rid]['labels'] else 'third_agent_agreement_audit'
  else:assert A[rid]['labels']==C[rid]['labels'];r=A[rid];source='A_C_agreement_not_third_audited'
  assert set(r['labels'])==set(DIMS) and all(type(x)is int and x in (0,1) for x in r['labels'].values())
  if A[rid]['labels']==C[rid]['labels'] and r['labels']!=A[rid]['labels']:joint_overruled.append(rid)
  if 'needs_human_review' in json.dumps(r.get('issues',[]),ensure_ascii=False):needs_human.append(rid)
  candidate.append({'id':rid,'labels':r['labels'],'dimension_reasons':r['dimension_reasons'],'evidence':r['evidence'],'innovation_subtypes':r['innovation_subtypes'],'fairness_subtypes':r['fairness_subtypes'],'safety_quality_basis':r['safety_quality_basis'],'reference_origin':source,'adjudication_reason':r.get('adjudication_reason','两位agent在同版完整材料上独立给出相同五维判断；尚未经第三位逐条审计。'),'issues':r.get('issues',[]),'component':sample[rid]['component'],'group':sample[rid]['group'],'human_gold_standard':False})
 out=HERE/'reference/adjudicated_candidate_reference_v8.jsonl';out.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in candidate));final={r['id']:r for r in candidate}
 csvpath=HERE/'真人培训候选判例-300条-v8.csv'
 with csvpath.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.writer(f);w.writerow(['原单元编号','样本用途','部门','政策原文','来源标题','页码','完整语境JSON','S安全性','E有效性','Ec经济性','I创新性','F公平性','S理由','E理由','Ec理由','I理由','F理由','逐字证据JSON','I子类','F子类','A首次同材五维','C首次同材五维','裁决来源','裁决理由','待真人复审问题'])
  for r in candidate:
   rid=r['id'];s=raw[rid];w.writerow([rid,r['component'],r['group'],s['text'],s['source_title'],json.dumps(s['pages'],ensure_ascii=False),json.dumps(s['contexts'],ensure_ascii=False)]+[r['labels'][d] for d in DIMS]+[r['dimension_reasons'][d] for d in DIMS]+[json.dumps(r['evidence'],ensure_ascii=False),'|'.join(r['innovation_subtypes']),'|'.join(r['fairness_subtypes']),json.dumps(A[rid]['labels'],ensure_ascii=False),json.dumps(C[rid]['labels'],ensure_ascii=False),r['reference_origin'],r['adjudication_reason'],json.dumps(r['issues'],ensure_ascii=False)])
 selected=[]
 for dim in DIMS:
  options=[rid for rid in A if A[rid]['labels']==C[rid]['labels'] and final[rid]['labels'][dim]==1 and rid not in selected]
  if options:selected.append(min(options,key=lambda rid:len(raw[rid]['text'])))
 selected+=sorted(rid for rid in A if A[rid]['labels']!=C[rid]['labels'] and rid not in selected)
 selected+=sorted(rid for rid in joint_overruled if rid not in selected)
 selected+=sorted(m['original_id'] for m in json.loads((HERE/'admin/adjudication_v8_mapping_PRIVATE.json').read_text()) if m['original_id'] not in selected)
 lines=['# 真人五维编码培训依据（agent预验证版）','','本材料用于真人学习编码规范和审阅候选判例。两位专家agent各自完成300条独立判读，第三位agent复核19条初始分歧及24条随机一致记录，并在源语境补齐后另审查4条受影响记录（其中1条与原抽查重合），共46条。所有执行者均为agent；这不是已完成的真人验证，也不是不可修订的人工金标准。','','## 先理解测量对象','','本研究测量政策文本对药品安全性、有效性、经济性、创新性、公平性的关注。每条分别判五个0/1，可多维同时为1，也可全部为0。标签1表示实质讨论该维度，包括评价要求、否定或条件性规定，不表示药品已经具有相应优点。不存在第六个“无关维度”。','','完整规范：[五维手册v1.3](/PROJECT_ROOT/outputs/agent-validation-20261007-r2/protocol/完整五维手册-v1.3.md)及[共用操作说明v1.4](/PROJECT_ROOT/outputs/agent-validation-20261007-r2/共用操作说明-v1.4.md)。实际政策引文与教学构造例须明确区分。','','## 每条的判断步骤','','1. 读完整单元与同版语境，确认材料完整、当前对象及完整谓词。','2. 分别判五维。标题、部门、药名或程序名称不能直接代替实质命题。','3. 每个1标出当前单元的连续原文；依赖上下文时再引对象、父谓词或列头。','4. 每维写本条理由，创新性与公平性写清纳入或排除边界，保留来源子类。','5. 实质缺料先回查，不猜0；材料已完整但有边界争议，保留个人判断和理由，独立提交后再讨论。','','## 最容易混淆的边界','','|维度|应据什么判定|不能自动纳入的内容|','|---|---|---|','|安全性|药物损害、风险及相应证据；明确质量安全另留痕|数据安全、单纯质量二字、人员专业背景|','|有效性|药物效果、临床获益、疗效比较及证据要求|数据有效、一般研究设计、推荐身份本身|','|经济性|药价、药费、支付标准、药物费用责任|科研经费、行政收费、仅程序名称|','|创新性|创新属性、具体改良、创新研发实体支持、专有权利及有依据的创新资格|普通设计、一般手续、创新药名称或单纯宗旨|','|公平性|实际药物保障获取、未满足治疗需求、患者负担及具体临床管理难度|一般申报资格、常规试验供药、机构行政管理|','','源文列表须按真实共同父谓词合读；表行须附实际表题、列名及行映射。不能把所有子项的标签复制给引导句，也不能因子项没有重复保障动词就忽略它实际承接的条件关系。','','## 有原文依据的候选判例','','下列判例展示实际分歧及边界；完整300条、双方原判断、逐字证据、完整语境和裁决理由见同目录真人培训候选判例-300条-v8.csv。补料源复读判例一并列入。学习后不得再把这批材料作为本人的未接触正式验证样本。','']
 for i,rid in enumerate(selected,1):
  r=final[rid];s=raw[rid];lines += [f'### 判例{i}：{rid}', '',f'来源：{s["source_title"]}；页码：{s["pages"] or "见源文件定位"}。', '',f'> {s["text"]}', '', '候选五维：'+ '；'.join(f'{NAMES[d]}={r["labels"][d]}' for d in DIMS)+'。', '', 'A：'+str(A[rid]['labels'])+'；C：'+str(C[rid]['labels'])+'。', '', '裁决或共识依据：'+r['adjudication_reason'], '', '逐维理由：'+'；'.join(f'{NAMES[d]}：{r["dimension_reasons"][d]}' for d in DIMS)+'。', '']
  if r['evidence']:lines+=['关键逐字证据：'+'；'.join(f"{NAMES[e['dimension']]}/{('原句' if e['source']=='unit' else '已给语境')}：{e['quote']}" for e in r['evidence']),'']
  if r['issues']:lines+=['真人复审事项：'+json.dumps(r['issues'],ensure_ascii=False),'']
 lines+=['## 真人正式验证如何使用','','真人先学习完整手册、共用说明和上述候选判例，再在另外封存的240条无答案材料上独立填写。使用future-human-validation-v2中两份材料：原文相同、顺序及编号不同；已按NFKC并去标点/空白的正文族排除培训及已知开发内容，240条包内亦无相同正文。每部门抽80个正文族，再族内抽1条，抽样概率和权重另存，不等于普通单元简单随机抽样。旧无答案包停止使用。编码员姓名、专业经历和实施日期由真实执行者填写，不能预填。','','先封存双方原始提交并计算协商前信度，再人工裁决分歧形成参照，最后检验两条机器方法。真人可以修正agent候选标准，但应说明原文和定义依据。任何据正式验证结果进行的调试须留版本，并另设后续确认样本。','','不要求三种方法的注意力占比逐项完全相同。需要检验机器能否忠实执行五维定义，以及误差是否系统性改变部门注意力结论。占比分母统一为同部门五维编码句次之和。','','工作目标与指标用途见[评价方案与使用范围](/PROJECT_ROOT/outputs/agent-validation-20261007-r2/评价方案与使用范围.md)。正式指标由statistics目录的实际计算提供，本指南不先填尚未完成的机器分数。当前300条中20条与已知开发材料正文规范化相同，原结果保留并另作敏感性分析；不能把本轮称为正文完全未接触的外部验证。']
 (HERE/'真人五维编码培训依据-v8.md').write_text('\n'.join(lines)+'\n')
 dump(HERE/'reference/training_guide_binding_v8.json',{'reference_sha256':sha(out),'training_csv_sha256':sha(csvpath),'guide_sha256':sha(HERE/'真人五维编码培训依据-v8.md'),'n':300,'adjudicated_or_audited_n':46,'third_auditor_overruled_joint_agreement':joint_overruled,'explicit_needs_human_review':needs_human,'source_sha256':sources,'human_validation_completed':False})
 print(json.dumps({'candidate_reference_n':300,'guide_cases_n':len(selected),'joint_agreement_overruled_n':len(joint_overruled),'needs_human_review_n':len(needs_human)},ensure_ascii=False))
if __name__=='__main__':main()
