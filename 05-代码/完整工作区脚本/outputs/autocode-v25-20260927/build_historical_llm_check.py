"""Summarize existing historical LLM comparisons without relabeling or sampling."""
import csv
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

ROOT=Path('/Users/rainbow/Desktop/战略院/药企项目-创新药')
ARCH=Path('/Users/rainbow/Desktop/战略院/创新药论文-完整归档-20260914')
OUT=ROOT/'outputs/autocode-v25-20260927'
CHECK=ARCH/'11-编码检验复核-20260925'
source=CHECK/'results.json'
r=json.loads(source.read_text())
rows=list(csv.DictReader((CHECK/'sentence_comparison.csv').open(encoding='utf-8-sig')))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
docs={
 'historical_v3':ARCH/'00-论文最新稿/0925论文修订稿6-创新药评价的注意力配置差异-清洁版.docx',
 'current_submission':ARCH/'12-投稿定稿工作区/投稿候选稿-匿名审稿版.docx',
}
doc_evidence={}
for name,path in docs.items():
 with ZipFile(path) as z: root=ET.fromstring(z.read('word/document.xml'))
 selected=[]
 for i,p in enumerate(root.findall('.//w:body/w:p',ns),1):
  txt=''.join(t.text or '' for t in p.findall('.//w:t',ns))
  if ('LLM' in txt or 'Claude' in txt) and (name=='current_submission' or i in [50,54,157]):
   selected.append({'top_level_body_paragraph':i,'text':txt})
 doc_evidence[name]={'path':str(path),'sha256':sha(path),'paragraphs':selected}

comparisons=[]
verified=0
for block,version,exclude in [('matched_text_pairs_338','LLMv2',{'0'}),('cross_version_diagnostic_only','LLMv3',set())]:
 for ref in ['A','C']:
  key=(ref if version=='LLMv2' else '旧'+ref)+' vs '+version
  metrics=[]
  for d in r['dims']:
   use=[x for x in rows if x['维度']==d and x['句子编号'] not in exclude and x[ref] in ('0','1') and x[version] in ('0','1')]
   counts={k:sum(x[ref]==a and x[version]==b for x in use) for k,a,b in [('tp','1','1'),('fn','1','0'),('fp','0','1'),('tn','0','0')]}
   stored=r[block][key][d]
   assert stored['n']==len(use) and all(stored[k]==v for k,v in counts.items())
   assert stored['recall']==counts['tp']/(counts['tp']+counts['fn'])
   verified+=1
   metrics.append({'dimension':d,'paired_valid_n':stored['n'],'reference_positive_n':stored['tp']+stored['fn'],
                   'recall':stored['recall'],'precision':stored['precision'],'f1':stored['f1'],**counts})
  comparisons.append({'method_version':version,'reference':'historical_author_'+ref,
                      'source_json_pointer':'/'+block+'/'+key,
                      'purpose':'historical_exploratory_comparison' if version=='LLMv2' else 'cross_definition_diagnostic_only',
                      'metrics':metrics,'macro_f1':r[block][key]['macro_f1']})

source_hash_checks=[{'path':m['path'],'expected_sha256':m['sha256'],'actual_sha256':sha(Path(m['path'])),'matches':sha(Path(m['path']))==m['sha256']} for m in r['manifest']]
assert all(x['matches'] for x in source_hash_checks)
trunc=json.loads((CHECK/'llm_input_truncation.json').read_text())
assert len(trunc['truncated'])==139
report={
 'title':'历史LLM验证对照核查','date':'2026-09-27',
 'archive_status':'仅历史，不用于当前比较',
 'latest_user_correction':'标准已改变；词典自动编码与LLM编码均应使用新v1.3完整输入重新运行，并分别对照本轮已完成的1268条A/C首次AI标签。旧作者A/C历史指标不回答当前方法表现。',
 'scope_correction':'按用户纠正：问题是原论文词典自动编码与LLM语义编码两条方法；不是两个模型，也不是本轮A/C两个AI评审。',
 'main_conclusion':'历史LLM存在相对旧作者A/C的召回指标，维度和参照差异显著；没有本轮V600同输入同口径的LLM召回，不能把候选词典I/F低召回推到LLM。',
 'methods':[
   {'name':'词典自动编码','meaning':'规则/关键词词典实现；本轮V600统计比较的是词典v23与candidate17，不是历史LLM。'},
   {'name':'LLM语义编码','meaning':'原论文与词典并列的对照方法；v2与v3是不同历史编码口径/数据版本，不是用户所说两方法之外的“两套模型验证”。',
    'v2':{'output':str(ARCH/'03-编码数据与脚本/llm_all_results.json'),'rows':3387,
          'script':str(ARCH/'03-编码数据与脚本/LLM编码脚本-llm_code_all.py'),
          'configured_model':'claude-sonnet-4-20250514',
          'provenance_limit':'脚本模型字段可核实；输出文件只有id/dims，不含逐请求模型或提示词哈希，不能由脚本单独证明每条历史调用身份。'},
    'v3':{'output':str(ARCH/'03-编码数据与脚本/coding_v3_llm.json'),'rows':2965,
          'manuscript_reported_model':'Claude Opus 5',
          'provenance_limit':'这是稿6正文与附录自述；标签文件没有运行模型元数据，核查不将稿件自述升级为逐请求可验证事实。',
          'definition':'医保目录申报指南口径；与v2及现v1.3手册/共同澄清均不可直接视为相同。',
          'input_truncation_affected_n':139,'input_truncation_denominator':2965,
          'input_truncation_detail':'存档命令导出经去空白、部分行号处理后的前120字符；不能证明长句全部以完整输入编码。'}}],
 'references':{'historical_A_C':'据2026-09-25作者最终更正记录作为旧人工盲编码；C文件名仍含机器编码-Claude，不据文件名改写作者确认。与2026-09-26 V600/D668的AI A/C不是同一身份/同一轮标签。',
               'not_gold_standard':'旧A/C尚未裁决为统一金标准；分别报告，不能挑更接近LLM的一位作真值。'},
 'comparisons':comparisons,
 'sample_boundaries':{
  'old_author_sample_n':339,'v2_main_textmatched_n':338,'v2_excluded_id':0,
  'v2_exclusion_reason':'作者表ID0文本900字符，旧自动语料1080字符；两方法输入展示不一致，主比较排除。',
  'v2_A_fairness_valid_n':336,'v2_A_invalid_fairness_cells':['H135','H136'],
  'v3_retained_old_n':299,'v3_new_blank_sample_n':296,'old_new_overlap_n':33,
  'v3_gold_reference_absent':'原296条新A/B盲表未完成标签；299条是旧A/C在清洗后保留的跨定义诊断，不能称v3同版独立验证。',
  'context_and_definition':'同ID或原句同文不保证源位置、上下文、实际送入LLM的完整输入或操作定义一致。'},
 'current_round':{'V600_LLM_same_input_rerun':False,'V600_LLM_recall':'not_available',
  'reason':'现有统一提示词准备包含v1.3手册但未含后续共同澄清全文，历史外部LLM未按本轮同输入重跑。',
  'A_C_kappa_is_not_LLM_recall':True,
  'development18':'旧18条校准材料曾有历史LLM标签事后对照；共同可判16条五维全一致12/16，排除已知截断后11/15。是边界诊断计数，不是总体召回。'},
 'manuscript_evidence':doc_evidence,
 'verification':{'confusion_tables_recomputed_from_existing_comparison_csv':verified,
                 'source_hash_checks':source_hash_checks,
                 'original_labels_or_manuscript_modified':False,
                 'new_v25_validation_candidate_files_opened':False,
                 'incidental_historical_policy_text_display':True,
                 'incidental_exposure_register':str(OUT/'历史LLM核查新增暴露登记.json'),
                 'incidental_exposure_note':'直接cat旧截断审计时有部分政策preview/hidden显示，输出被截断；保守登记全部139个审计ID及2个非法格ID，不以未打开新候选文件证明新验证框未暴露。',
                 'no_new_recall_experiment':'仅独立核对已有混淆计数和召回算术；未执行新LLM、抽样或产生新标签。'},
 'evidence_files':[{'path':str(p),'sha256':sha(p)} for p in [source,CHECK/'sentence_comparison.csv',CHECK/'analyze.py',CHECK/'论文背景与编码检验复核.md',CHECK/'llm_input_truncation.json',ARCH/'03-编码数据与脚本/LLM编码脚本-llm_code_all.py',ROOT/'outputs/validation-expansion-20260926/维度口径与正文衔接-完成阶段核对.md',ROOT/'outputs/01a0dbb7-blind-review/与正文历史编码对照说明.md']],
}
(OUT/'历史LLM验证对照核查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')

def fmt(m):return f'{100*m["recall"]:.1f}%（{m["tp"]}/{m["reference_positive_n"]}）'
def table(version):
 a=next(x for x in comparisons if x['method_version']==version and x['reference'].endswith('_A'))
 c=next(x for x in comparisons if x['method_version']==version and x['reference'].endswith('_C'))
 lines=['| 维度 | 以旧作者A为参照：召回率（TP/参照阳性） | 以旧作者C为参照：召回率（TP/参照阳性） | 有效配对数 A/C |','|---|---:|---:|---:|']
 for ma,mc in zip(a['metrics'],c['metrics']):lines.append(f'| {ma["dimension"]} | {fmt(ma)} | {fmt(mc)} | {ma["paired_valid_n"]}/{mc["paired_valid_n"]} |')
 return '\n'.join(lines)

text=f'''# 历史LLM验证对照核查

> **封存状态：仅历史，不用于当前比较。** 用户最新明确：标准已变，词典自动编码与LLM编码两条都应重跑，参照为本轮已完成的1268条A/C首次AI编码。下文旧作者A/C指标仅留档，不回答当前方法召回率，也不写入当前投稿结果。已停止扩展历史分析。

日期：2026-09-27。范围按用户纠正：核查原论文的“词典自动编码”和“LLM语义编码”两条方法，**不是两个模型，也不是本轮A/C两位AI评审。** 原作者A/C只在此独立说明中讨论；未写入或修改投稿文件。

**有历史LLM与原作者编码的召回率，但不能统称也像本轮词典一样低。原稿6所用LLMv3相对旧A的创新性/公平性为46.2%/17.5%，相对旧C为68.8%/56.1%；这只是跨口径诊断。当前V600同输入、同手册的LLM召回率尚未测得。**

## 1. 原文中的两条编码方法

原稿6方法段50、表2和附录A2明确：LLM语义编码作为词典编码的对照。稿6的LLM数据是清洗后2965句；表2总体κ=0.654是**词典—LLM方法间一致性**，不是LLM相对作者的召回率。方法段54的296条新人工验证写“结果待补”，现存新A/B表也没有完成标签。

- [原稿6清洁版]({docs['historical_v3']})：顶层正文段50、54、157；具体段落原文和文档哈希见配套JSON。段号按`word/document.xml`顶层正文段计，不是页码。
- [历史v3 LLM输出]({ARCH/'03-编码数据与脚本/coding_v3_llm.json'})：2965条，字段为id/dept/file/dims。
- [更早v2 LLM输出]({ARCH/'03-编码数据与脚本/llm_all_results.json'})：3387条，字段为id/dims。

模型身份仅作来源核对：v2脚本配置`claude-sonnet-4-20250514`；稿6对v3自述“Claude Opus 5”。二者是历史执行/口径版本信息，不把用户问题改成“两个模型验证”。标签文件不含逐请求模型、提示词或运行哈希，稿件自述与脚本配置的证据强度须区分。

## 2. 原稿6的LLMv3：已有299条跨口径诊断

旧339条作者样本中299条被v3清洗保留。下表直接来自存档统计`cross_version_diagnostic_only`，本次用逐句对照CSV独立核对了分子、分母与混淆计数。**v3采用申报指南新定义，参照仍是旧A/C；旧样本还参与过规则开发，因此不是新方法的同版独立验证。**

{table('LLMv3')}

因此，相对旧A，有效性和公平性漏识别较多，创新性也不高；相对旧C，有效性较高，公平性仍有缺口。不能只挑某一位作为真值。更不能据这些历史数字断言LLM在当前手册下也是创新性6%—7%的召回。

另有实际输入局限：历史导出步骤将归一化文本截到前120字符，139/2965句超过该长度。存档有命令及受影响ID；这证明输入完整性存在问题，不证明每条后续调用均经过完整修复。稿6的新296条作者标签未完成，无法用它们补出同版召回。

## 3. 更早LLMv2：338条同原文展示的历史比较

旧作者A/C共有339句；ID0在作者表显示900字符，旧自动语料为1080字符，人工—自动主比较排除后为338句。A公平性另有H135、H136两个“标题行”非法格，因此该维有效配对数336；这些格未填0。召回率的分母是**该参照判1的数量**，不是338。

{table('LLMv2')}

这些是相对各自旧作者标签的探索性符合程度；作者尚未裁定统一参考。旧C归档文件名仍含“机器编码-Claude”，但9月25日核查记录按作者最终更正将A/C记为人工盲编码；此处保留这项历史身份说明，不将旧C混同本轮AI-C。

同一338条比较上，LLMv2公平性召回高于词典v2（对A：20.7%对12.6%；对C：57.8%对40.0%），但有效性召回低于词典v2（对A：22.6%对40.5%；对C：57.1%对65.7%）。这进一步说明，LLM与词典各维表现不能互相替代。

## 4. 与当前V600的关系

当前V600比较的是词典v23与candidate17，相对于两位本轮AI评审各自的结果。**历史外部LLM未在本轮相同600条、相同完整输入与共同澄清下重跑，因此没有当前LLM召回率可报告。** 两位AI的κ衡量评审间一致性，不是原论文LLM的召回。

此前18条校准材料有一次历史标签事后对照：共同明确的16条，历史LLM五维完全一致12/16；排除已知截断后为11/15。这是少量边界材料上的完整标签差异计数，不能换算成总体准确率或逐维召回，更不能冒充V600检验。

旧版与当前版的样本、单元边界、定义、实际上下文和参照身份均不同；不能把历史LLM的数字与V600词典数字并列作算法优劣排名。当前可确认的是历史LLM也曾有识别不足和输入问题，尚未确认其按现行口径的表现。

## 5. 证据和本次核验

- [原历史完整统计]({source})：`matched_text_pairs_338`与`cross_version_diagnostic_only`两个区块，逐维n、TP、FP、FN、TN、precision、recall、F1均在。
- [逐句历史对照CSV]({CHECK/'sentence_comparison.csv'})：本次据此独立复核20个LLM混淆表；结果与存档JSON完全一致。没有重新编码。
- [历史背景复核报告]({CHECK/'论文背景与编码检验复核.md'})：作者身份、339/338/299/296分母、非法格及历史方法边界。
- [LLM输入截断审计]({CHECK/'llm_input_truncation.json'})：历史导出命令及139条受影响ID。未在本文重印政策正文。
- [当前完成阶段口径核对]({ROOT/'outputs/validation-expansion-20260926/维度口径与正文衔接-完成阶段核对.md'})、[当前投稿候选稿]({docs['current_submission']})段109：明确历史外部LLM未按同输入重跑。
- [18条校准事后对照]({ROOT/'outputs/01a0dbb7-blind-review/与正文历史编码对照说明.md'})：12/16、11/15及其限制。
- [本核查结构化记录]({OUT/'历史LLM验证对照核查.json'})：分子分母、precision/F1、原稿段落、全部来源哈希及核验信息。

本次复核六份历史源数据的SHA256均与9月25日统计绑定一致。未打开v25新验证候选文件、未抽样或调用LLM产生新结果，未修改原作者标签、历史报告或投稿文件。区间未移用：旧存档bootstrap对应339条范围，不能直接贴到338条主比较或299条跨版本诊断上。

### 本轮附带原文暴露登记

核查过程中有一次直接读取旧`llm_input_truncation.json`，工具虽截断输出，仍展示了头尾部分政策`preview`/`hidden`原文；此外，`results.json`结构摘要显示了非法格ID2687、1009的原文。不能把“未打开新候选文件”说成“没有与候选重叠的正文暴露”。为避免遗漏，已将截断审计全部139个旧ID、加上述2个非法格共141条保守登记；其中能从可见输出明确识别的24条标为确认展示，其余117条标为可能展示、保守排除。

详见[本轮历史LLM核查新增暴露登记]({OUT/'历史LLM核查新增暴露登记.json'})，含历史ID、原语料JSON指针、原文与归一化文字哈希、展示来源及字段。后续验证框须程序映射这些片段并排除重叠；本报告不宣称该框仍完全未暴露。未向模型展示全部2965/3387句，其他全量文件仅程序处理标签、长度、字段和哈希；本次登记不隐瞒工具已产生的可见片段。
'''
(OUT/'历史LLM验证对照核查.md').write_text(text)
print(json.dumps({'outputs':['历史LLM验证对照核查.md','历史LLM验证对照核查.json'],'confusion_tables_verified':verified,'historical_source_hashes_verified':len(source_hash_checks)},ensure_ascii=False))
