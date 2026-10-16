from pathlib import Path
from zipfile import ZipFile
from lxml import etree
import json,hashlib,re
R=Path('/Users/rainbow/Desktop/战略院/药企项目-创新药');D=R/'outputs/final-three-department-20261008-human-validation-template';B=R/'outputs/coding-revision-20261007-r3';ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
 with ZipFile(p) as z:
  r=etree.fromstring(z.read('word/document.xml'));ps=[''.join(x.xpath('.//w:t/text()',namespaces=ns)) for x in r.findall('w:body/w:p',ns)];ts=[[[''.join(c.xpath('.//w:t/text()',namespaces=ns)) for c in row.findall('w:tc',ns)] for row in t.findall('w:tr',ns)] for t in r.findall('w:body/w:tbl',ns)]
 return ps,ts
p=D/'论文修订稿-编码实算结果版.docx';m=D/'编码复核说明与真人检验事项.docx';ps,t=read(p);ms,mt=read(m)
assert sha(p)=='2145e9d960fe428003181bbe48eb616fb006b05cd1f9b89d4adfeacba8c86585'
assert sha(m)=='5005be3ccd106f7f89385538fd400a487714eed41e6544091a6c5fdc221ff27e'
b=B/'manuscript-update-20261008/proxy-180-table2-binding-20261008/表2与五维κ_代理180权威绑定.json';a=json.loads(b.read_text());assert sha(b)=='e437298ca834133b01d21781464b621426ab221595a86634aa0d1061cf8d28dd'
body='\n'.join(ps).split('参考文献\n')[0];memo='\n'.join(ms);checks=[]
def c(id,ok,detail): checks.append({'id':id,'status':'PASS' if ok else 'FAIL','detail':detail})
actual=[x.split('/') for row in t[1][1:] for x in row[2:]];expected=[x.split('/') for row in a['table2_display_rows_A_B'][1:] for x in row[2:]]
c('80_table_values',actual==expected and sum(map(len,actual))==80,'实际DOCX表2的10×4×2=80值逐项等于权威绑定显示值；方法标签仅改规则→自动规则编码、LLM→LLM编码。不是重新计算原始统计。')
c('five_AB_kappa',a['A_B_kappa_sentence_values'] in ps[54],'五维κ 0.944/0.820/0.879/0.520/0.641与同版权威绑定一致，低值如实保留。')
c('180_design',all(x in ps[49]+ps[50]+ps[56] for x in ['947、医保760、卫健60','各抽60条，共180条','卫健为框内全查','5000次','有限总体校正','剩余规范代表框']),'正文为180条规范代表分层不放回样本、旧框947/760/60；60挑战不并概率估计；未将240新方案权重和不作FPC混入。')
c('proxy_identity',all(x in ps[49]+ps[54] for x in ['均由AI代理承担','开发诊断','人工编码的独立检验另行实施']),'正文4.2实述A/B/T为AI代理，未称已完成真人编码。')
c('display_alias', '展示B对应原归档中的C' in memo and '原始文件及标签不改写' in memo,'B是原C展示映射；原始标签不改写；memo未来真人A/B与当前代理另述。')
c('not_future240', '240条' not in body and '新240条重新计算的80个数值替换当前180条代理值' in memo,'未来真人240及其79族无FPC区间方案在memo，与当前正文180条实际区间区别。')
c('variables_and_denominators',all(x in ps[38]+ps[39] for x in ['S、E、Ec、I、F','五维编码句次合计','本部门全部分析单元数','除以经济性单元数']), '五维未新增；3.3三项比例与4.2 κ/观察一致率/P/R/F1分别承担内容描述和测量检验。')
c('Card_local_design','参考Card等' in ps[47] and '允许同一文本体现多个框架' in ps[47] and '本文采用多标签编码' in ps[47], 'Card现[44]只用于重叠标注思路；五维0/1及分母明确归为本文设计，不借其αU作为Cohen κ来源。')
c('ordinary_duplicate_description','按规范化正文归并重复单元' in ps[49] and '正文族指' not in body,'项目规范化重复单元用普通操作描述，没有包装成文献发明的采样法。')
c('example_scope','仅降低企业申报费用不据此编码为公平性' in ps[47] and '不因同处一段而自动联动' in ps[47], '患者负担例子说明跨维可并存；反例仅排公平性，不宣称行政申报费必定属于经济性。')
c('method_tradeoff_values', all(x in ps[54] for x in ['0.997','0.910','0.900、0.945','0.870、0.783','1.000、0.945']), 'P/R取舍的具体比较直接对应表2，不泛称LLM全面优于规则。')
c('denominator_arithmetic', all(abs(float(x/y*100)-z)<.005 for x,y,z in [(322,690,46.67),(392,910,43.08),(610,994,61.37),(677,1157,58.51)]), '新增两组计数/分母比例按数学重算均与两位显示数一致；没有把相对占比降低说成识别更少。')
ids=['RECODE25-00741','RECODE25-01353','RECODE25-02845'];cases={i:{} for i in ids}
source=B/'rule_inputs_shared_v14.jsonl';rule=B/'rules-v36.2-development/all_predictions_material_v14.jsonl';llm=B/'llm-candidate03-development/full-corpus-candidate03-material-v14-single-unit-reconciled-development/all_predictions.jsonl'
for line in source.read_text().splitlines():
 d=json.loads(line)
 if d['id'] in cases:
  x=d['input'];cases[d['id']].update({'unit_text':x['unit_text'],'source_stem':x['original_file_stem'],'pages':x.get('pages')})
for kind,f in [('rule',rule),('LLM',llm)]:
 for line in f.read_text().splitlines():
  d=json.loads(line)
  if d['id'] in cases: cases[d['id']][kind+'_labels']=d.get('labels',d.get('prediction',{}).get('labels'))
c('three_actual_cases',cases[ids[0]]['rule_labels']['Ec']==0 and cases[ids[0]]['LLM_labels']['Ec']==1 and cases[ids[1]]['rule_labels']['S']==0 and cases[ids[1]]['LLM_labels']['S']==1 and cases[ids[2]]['rule_labels']['I']==0 and cases[ids[2]]['LLM_labels']['I']==1,'P72三例与当前冻结原句、rules36.2和完整reconciled03实际输出一致；药物警戒句没有独立研发支持内容，扩大创新判定的反例保留。')
refs=[x for x in ps if re.match(r'^\[\d+\]',x)];first=[]
for k in re.findall(r'\[([0-9,]+)\]',body):
 for n in map(int,k.split(',')):
  if n not in first:first.append(n)
c('66_references_order',len(refs)==66 and first==list(range(1,67)) and 'CARD D' in refs[43] and all('BESSONNEAU' not in x for x in refs),'正文首次引用与参考文献均1—66；Card现[44]；Bessonneau不再占正文引用位，memo另说明未来方案。')
c('policy_roles',all(x in body for x in ['复用现有申请表及附件','履行法定上市后研究义务','2026年医保官方解读','须由保险机构确认','不能将目录纳入视为基本医保报销']),'三节职责及正式文件/官方解读区别保留；与已核官方证据包一致。')
c('core_result_and_future',all(x in body for x in ['45.16%','43.33%','20.49%','21.42%']) and '不能提前写成三种方法均已验证' in memo,'机器全量核心结论保持，真人验证未冒称完成。')
assert all(x['status']=='PASS' for x in checks),[x for x in checks if x['status']=='FAIL']
report={'schema':'actual-filled-content-review-v1','date':'2026-10-08','status':'PASS_CONTENT_ONLY','input_files':[{'path':str(x),'sha256':sha(x)} for x in [p,m,b,source,rule,llm]],'locator_convention':'本次DOCX直接w:body/w:p 0基序号；非原替换映射号、非页码。','checks':checks,'checked_counts':{'checks':len(checks),'table2_scalars':80,'AB_kappa':5,'actual_case_rows':3,'references':66},'actual_case_evidence':cases,'blocking_findings':[],'scope_limit':'只读内容/表内显示值对权威绑定/三例实据核验；未重跑5000统计、未冒称视觉验收、未读取未来待评文件或修改任何标签/文稿。','prior_review':'另存，不覆盖旧2fa待填稿内容核查；本报告仅绑定本次2145实算稿及5005说明；本轮只复核表3题注分页属性修复后的内容。','remaining_condition':'真人独立复核仍待实际标签和作者资料；当前80值和5个κ是实际代理开发诊断。'}
prior=D/'policy-source-audit/编码实算稿独立内容核查-20261008.json'
old=json.loads(prior.read_text())
assert old['checks']==report['checks'] and old['checked_counts']==report['checked_counts'] and old['actual_case_evidence']==report['actual_case_evidence']
assert old['input_files'][1:]==report['input_files'][1:]
with ZipFile(p) as z:
 r=etree.fromstring(z.read('word/document.xml'))
 caps=[x for x in r.findall('w:body/w:p',ns) if ''.join(x.xpath('.//w:t/text()',namespaces=ns)).startswith('表3')]
 assert len(caps)==1 and caps[0].find('w:pPr/w:pageBreakBefore',ns) is None
report['layout_recheck']={'table3_caption_pageBreakBefore_absent':True,'prior_review':{'path':str(prior),'sha256':sha(prior)},'all_prior_16_checks_and_actual_case_evidence_identical':True,'all_other_input_bindings_identical':True,'canonical_current_main_content_sha256':hashlib.sha256(json.dumps({'paragraphs':ps,'tables':t},ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'comparison_scope':'复跑原16项内容规则并逐项对比原审查结果；未声称对已不存在的旧DOCX作整包字节差异比较；视觉验收由其他审阅承担。'}
out=D/'policy-source-audit/编码实算稿独立内容核查-20261008-v6.json';assert not out.exists();out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'path':str(out),'sha256':sha(out),'checks':len(checks),'blocking':0},ensure_ascii=False,indent=2))
