from pathlib import Path
import json,hashlib
from datetime import datetime
from zoneinfo import ZoneInfo

root=Path(__file__).resolve().parent
archive=Path('/Users/rainbow/Desktop/战略院/创新药论文-完整归档-20260914')
work=archive/'12-投稿定稿工作区'
paths={'mapping':work/'校准材料-候选边界/研究者编号映射-不提供编码员.json','dictionary':archive/'03-编码数据与脚本/coding_v3_dict.json','llm':archive/'03-编码数据与脚本/coding_v3_llm.json','truncation_audit':archive/'11-编码检验复核-20260925/llm_input_truncation.json','A':root/'agent-A/result-A.json','C':root/'agent-C/result-C.json'}
loaded={k:json.loads(p.read_text()) for k,p in paths.items()}
old_dict={r['id']:r for r in loaded['dictionary']}
old_llm={r['id']:r for r in loaded['llm']}
a={r['id']:r for r in loaded['A']['records']}
c={r['id']:r for r in loaded['C']['records']}
raw={r['id']:r['text'] for r in json.loads((root/'agent-A/待评材料.json').read_text())['rows']}
truncated={r['id']:r for r in loaded['truncation_audit']['truncated']}
dims=['S','E','Ec','I','F']
names=['安全性','有效性','经济性','创新性','公平性']
def labels(nameset):return {d:int(name in nameset) for d,name in zip(dims,names)}
records=[]
for item in loaded['mapping']:
    id_,oldid=item['task_id'],item['historical_id']
    dr,lr=old_dict[oldid],old_llm[oldid]
    assert raw[id_]==dr['sent']
    assert hashlib.sha256(raw[id_].encode()).hexdigest()==item['text_sha256']
    assert dr['junk'] is None
    assert dr['file']==lr['file'] and dr['dept']==lr['dept']
    consensus=a[id_]['labels']==c[id_]['labels'] and all(v in [0,1] for v in a[id_]['labels'].values())
    new=a[id_]['labels'] if consensus else None
    predictions={'dictionary':labels(dr['dims_v3']),'llm':labels(lr['dims'])}
    rec={'id':id_,'historical_id':oldid,'source_file':dr['file'],'source_dept':dr['dept'],'text':raw[id_],'text_sha256':item['text_sha256'],'text_hash_verified':True,'A':a[id_]['labels'],'C':c[id_]['labels'],'clear_agreement':consensus,'reference_for_diagnostic_only':new,'historical':predictions,'llm_truncation_record':truncated.get(oldid),'differences':{}}
    if new:
        for method,pred in predictions.items():
            rec['differences'][method]=[{'dimension':d,'historical':pred[d],'new_review':new[d],'direction':'historical_extra_positive' if pred[d]==1 else 'historical_missed_positive'} for d in dims if pred[d]!=new[d]]
    records.append(rec)

def stats(rows,method):
    mismatches=[r for r in rows if r['differences'][method]]
    extras=sum(x['direction']=='historical_extra_positive' for r in rows for x in r['differences'][method])
    misses=sum(x['direction']=='historical_missed_positive' for r in rows for x in r['differences'][method])
    return {'rows':len(rows),'exact_vector_agreement':len(rows)-len(mismatches),'different_rows':[r['id'] for r in mismatches],'dimension_pairs':5*len(rows),'matching_dimensions':5*len(rows)-extras-misses,'historical_extra_positive':extras,'historical_missed_positive':misses}
clear=[r for r in records if r['clear_agreement']]
strict=[r for r in clear if not r['llm_truncation_record']]
summary={'blind_review_clear_agreement_rows':len(clear),'excluded_for_unresolved':[r['id'] for r in records if not r['clear_agreement']],'llm_truncated_among_clear':[r['id'] for r in clear if r['llm_truncation_record']],'historical_comparison_all_clear':{m:stats(clear,m) for m in ['dictionary','llm']},'same_subset_excluding_known_truncation':{m:stats(strict,m) for m in ['dictionary','llm']},'limits':['定向选出的边界校准材料，不代表总体准确率','两名AI agent的共同判断不是人工金标准','历史口径与本轮候选定义不同，差异不能全解释为旧算法错误','未截断只按现有审计记录判断，不证明历史提示、上下文和独立性完全一致','不据18条推断正文全量部门排序或占比是否成立']}
output={'generated_at':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'sources':{k:{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for k,p in paths.items()},'new_protocol':'CAL-5D-20260926-v1.1','summary':summary,'records':records}
(root/'与正文历史编码逐条对照.json').write_text(json.dumps(output,ensure_ascii=False,indent=2))
def labeltext(v):
    if any(x=='待定' for x in v.values()):return '待定'
    return '、'.join(n for d,n in zip(dims,names) if v[d]) or '全0'
lines=['# 本轮盲评与正文历史两种编码对照','',
'本次只做冻结后的事后对照，没有向两位评审回传机器答案，也没有修改任何原始标签。正文当前工作稿表2明确保留原2965句版本的词典与LLM一致性记录，并注明待验证重算。本次使用保存的coding_v3_dict.json与coding_v3_llm.json，与18条校准材料的历史ID及原文SHA-256逐项核对，18条均对应。',
'','本轮16条获得两位AI评审相同且明确的五维判断。CAL-014因孤立数字的完整性判断有分歧，CAL-018双方均待定，不作为确定标签参照。','',
'| 诊断范围 | 历史词典五维完全一致 | 历史LLM五维完全一致 |','|---|---:|---:|',
f"| 16条明确一致材料的历史标签对照 | {stats(clear,'dictionary')['exact_vector_agreement']}/16 | {stats(clear,'llm')['exact_vector_agreement']}/16 |",
f"| 另排除CAL-008已知LLM截断后的共同15条 | {stats(strict,'dictionary')['exact_vector_agreement']}/15 | {stats(strict,'llm')['exact_vector_agreement']}/15 |",'',
'这些是边界材料上的新旧口径差异计数，不是算法总体准确率。旧LLM对CAL-008只展示前120字的记录已在历史输入审计中登记，即使标签恰好相同，也不能把该条算作相同完整输入的验证。其余条目仅表示该审计未记录截断，不证明提示词和完整语境一致。','',
'在共同15条中，词典有3个历史多标维度、4个历史漏标维度；LLM有3个历史多标维度、1个历史漏标维度。“多标/漏标”均相对于本轮候选定义下的AI共同判断，不代表旧定义下已有真人裁定。','',
'| 编号 | 本轮A | 本轮C | 历史词典 | 历史LLM | 对照说明 |','|---|---|---|---|---|---|']
for r in records:
    status='不作确定标签比较' if not r['clear_agreement'] else 'LLM输入曾截断，排除共同15条对照' if r['llm_truncation_record'] else '存在差异' if any(r['differences'][m] for m in ['dictionary','llm']) else '相同'
    lines.append(f"| {r['id']} | {labeltext(r['A'])} | {labeltext(r['C'])} | {labeltext(r['historical']['dictionary'])} | {labeltext(r['historical']['llm'])} | {status} |")
lines += ['', '## 差异对应的修订方向','',
'| 编号 | 具体问题 | 应检查的规则 |','|---|---|---|',
'| CAL-002 | 机构已有创新药试验经验，历史词典记I，本轮均不记I | 创新药作为对象名称与创新属性/支持措施分开，属于收紧误触发 |',
'| CAL-006 | 本轮仅S；历史词典全0，LLM记S+E | “安 全性”的版式分词可能使词典漏检，须核实并统一规范化；代表性没有明确关联效果判断时不自动E |',
'| CAL-009 | 扩大商业健康保险的创新药支付范围；本轮Ec+F，历史词典I，LLM仅Ec | 识别实质支付覆盖及药品保障获取，同时排除创新药名称对I的误触发 |',
'| CAL-010 | 用药不受一品两规限定；本轮及LLM均F，历史词典全0 | 补充解除用药获取限制的语义表达，不能只找可及或公平字样 |',
'| CAL-013 | 特殊储存药品的机构资质要求；历史LLM记F，本轮均全0 | 一般储运任务与实质临床管理难度分开，不能因特殊储存自动F |',
'| CAL-015 | 宏观医保改革目标；历史LLM记Ec，本轮均全0 | 医保筹资支付领域名称不直接等于药品治疗经济性 |',
'| CAL-017 | 公示资料不含经济性信息；历史词典记Ec，本轮均全0 | 纯信息披露元数据与经济性评价内容分开 |','',
'## 是否需要增加编码内容','',
'需要补充的是同一维度下未覆盖的实质表达、必要的父条款/表头，以及用来检验边界的正反对照材料；同时必须收紧造成多标的触发条件。不能只加词，不加排除规则；不能因为两种方法不一致就扩张维度定义，也不能为了维持正文排序选取更多有利样本。','',
'先核源CAL-014和CAL-018。随后以共同定义修改实际词典实现和实际LLM调用提示，所有方法使用相同完整单元与核实语境、保留待定；用本批及另设教学对照检查开发缺陷。完成后冻结规则，在未参与开发、覆盖各部门和不同文本类型的新样本上独立验证。经济性和创新性在本轮明确16条中各仅1个正例，安全性/有效性各3个、公平性4个，需要补充覆盖；稀有正例的定向补样须单列，不能直接混入代表性总体准确率。','',
'最后重跑全量语料，并重算正文的方法一致性、部门命中数、占比及敏感性结果。18条不能证明或推翻正文全量部门排序；不以正文旧结论作为改标目标。','',
'正文附录A2还有一处须明确版本归属：历史LLM维度说明将“目录外药品的价格费用”列入公平性，而本轮手册按内容把纯价格归经济性，仅在有患者负担或保障获取依据时再记公平性。这段作为历史方法记录可以保留，但不能直接称与本轮新词典/手册同口径；新版运行及论文方法说明须同步。','',
'## 来源','']
for k,p in paths.items():lines.append(f'- {k}：[{p.name}]({p})')
lines += ['','正文核查对象：'+f'[当前稿7]({work/"0925稿7-论证修订工作稿-统计待重算.docx"})。表2及方法正文已经将旧一致性标为历史结果、待验证重算。']
(root/'与正文历史编码对照说明.md').write_text('\n'.join(lines)+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2))
