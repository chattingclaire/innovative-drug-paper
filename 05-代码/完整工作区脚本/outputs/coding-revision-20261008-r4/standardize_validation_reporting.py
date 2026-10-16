from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from copy import deepcopy
from lxml import etree
import json, csv, hashlib

BASE=Path(__file__).resolve().parents[2]
OUT=BASE/'outputs/final-three-department-20261008-human-validation-template/创新药评价的注意力配置差异与协调路径.docx'
SUP=OUT.parent/'编码检验补充统计表.csv'
R4=Path(__file__).resolve().parent
STAT=BASE/'outputs/coding-revision-20261007-r3/methods-20261008/rules-v36.2-plus-LLM03-reconciled-development-complete-statistics-v3'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(OUT)=='110c3592814211121d35c2295598a922388acb6a30ed305cfba1d2bc8d9508af'
assert sha(STAT/'machine_reference_classification.json')=='3fd95118b034b9ffd1510dd04ce592558f5bfc0f5e5d2a4ae249ab5b5245ca29'
assert sha(STAT/'A_C_before_third_agreement.json')=='724745a210e9ca5ed667e7a61fe55a8abce4ef2b7d89adc42f51159f447204e3'
assert not SUP.exists()
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W='{'+NS['w']+'}'
with ZipFile(OUT) as z: entries={i.filename:(i,z.read(i.filename)) for i in z.infolist()}
root=etree.fromstring(entries['word/document.xml'][1]); body=root.find('w:body',NS); ps=body.findall('w:p',NS)
plain=lambda p:''.join(p.xpath('.//w:t/text()',namespaces=NS))
old_paras={i:plain(p) for i,p in enumerate(ps)}
old_tables=[etree.tostring(t) for t in body.findall('w:tbl',NS)]
old_refs=[plain(p) for p in ps if plain(p).startswith('[')]
old_cites=[etree.tostring(r) for r in root.xpath('.//w:r[w:rPr/w:vertAlign[@w:val="superscript"]]',namespaces=NS)]
def rewrite(i,text):
 p=ps[i]; rpr=p.find('w:r/w:rPr',NS)
 for c in list(p):
  if c.tag!=W+'pPr':p.remove(c)
 r=etree.SubElement(p,W+'r')
 if rpr is not None:r.append(deepcopy(rpr))
 etree.SubElement(r,W+'t').text=text
def replace_run_text(i,old,new):
 n=0
 for t in ps[i].xpath('.//w:t',namespaces=NS):
  if t.text and old in t.text:t.text=t.text.replace(old,new);n+=1
 assert n==1,(i,old,n)

# Method definitions remain next to their existing primary references.
replace_run_text(50,'及观察一致率报告','（扣除机会一致后的名义二元编码一致性）及观察一致率报告')
replace_run_text(50,'，以精确率（P）、召回率（R）及F1检验分类表现，分别表示识别内容与参照相符的比例、参照内容被识别的比例及二者的调和均值。总体和各部门按维度报告四格及上述指标。概率样本按部门框规模/60加权四格；这是采样设计加权，κ针对名义二元类别。',
 '，以精确率（P）、召回率（R）及F1评价相对于所列参照的分类表现。以各维标签1为正类，P为机器判为1的单元中参照同为1的比例，R为参照判为1的单元中机器同为1的比例，F1为二者的调和均值。总体和各部门按维度报告四格、参照正类比例及上述指标。概率样本按部门抽样框规模/60加权四格。')
rewrite(51,'表2 自动规则编码与LLM编码的逐维一致性与分类表现')
rewrite(52,'Table 2 Dimension-Specific Agreement and Classification Performance of Rule-Based and LLM Coding')
rewrite(53,'注：表内为180条概率样本的设计加权点估计，均保留3位小数；斜线前后分别以编码员A、编码员B为参照。各维标签1为正类，P、R、F1取值为0—1；分母为零或指标未定义时记NA。A、B及复核参照的形成过程见第4.2节。四格、参照正类比例、观察一致率与近似95%区间见配套《编码检验补充统计表》；60条挑战材料在其中单列，不并入概率估计。')
rewrite(54,'编码员A与编码员B在安全性、有效性、经济性、创新性、公平性上的κ依次为0.944、0.820、0.879、0.520、0.641。两种机器方法在安全性、有效性、经济性上与A、B的κ点估计为0.820—1.000。经济性方面，LLM编码对A、B的召回率均为1.000，高于自动规则编码的0.900、0.945，但精确率为0.870、0.783，低于自动规则编码的1.000、0.945。创新性方面，两种方法的召回率同为1.000/0.714；LLM编码的精确率为0.200/0.400，低于自动规则编码的0.500/1.000，F1相应为0.333/0.513和0.667/0.833，差异主要体现为LLM编码纳入了更多与参照不符的单元。公平性方面，以A为参照时LLM编码的F1点估计高于自动规则编码（0.836对0.732），以B为参照时则较低（0.744对0.952），方法排序随参照变化。')
rewrite(59,'注：两种方法均覆盖三部门4481个分析单元，药监、医保、卫健分别为1848、2100、533个。注意力占比单位为%，分母为各方法在本部门识别的五维编码句次合计。同一单元可跨维计数，同维至多一次；未舍入的五维占比合计100%，表中保留2位小数，独立舍入可能使显示值合计偏离100%。')
rewrite(69,'注：两种方法分别对同一政策语料编码；注意力占比以各方法在同部门识别的五维编码句次合计为分母。同一单元可跨维计数，同维至多一次，未舍入的五维占比合计100%。图中保留1位小数，完整数值见表3。')
# Comparative coding results are parallel measurements, not a time series.
rewrite(71,'两种方法的注意力占比差异与编码句次总量有关。药监安全性在自动规则编码与LLM编码中分别为322次和392次，五维句次合计分别为690次和910次，对应占比为46.67%和43.08%；医保经济性分别为610次和677次，五维合计为994次和1157次，对应占比为61.37%和58.51%。LLM编码识别的上述维度句次更多，但因五维句次合计也更多，其相对占比较低。全量56种文件构成口径中，两种方法均保留医保经济性注意力占比高于卫健的方向；自动规则编码的公平性占比在系列等权时转为医保高于卫健。全量分布与概率样本估计分别对应所收集文本及剩余规范代表框。')

# Export existing statistics only; do not recompute any labels or intervals.
groups={'ALL':'总体','NMPA':'药监','NHSA':'医保','NHC':'卫健'}
dims={'S':'安全性','E':'有效性','Ec':'经济性','I':'创新性','F':'公平性'}
methods={'rules-v36.2':'自动规则编码','LLM-candidate03-single-unit-reconciled':'LLM编码','A_C':'编码员A—编码员B'}
refs={'A':'编码员A','C':'编码员B','candidate':'复核参照（含AI复核者T判读）','symmetric A/C':'编码员A与编码员B的对称比较'}
metric_names={'kappa':'κ','agreement':'观察一致率','precision':'精确率P','recall':'召回率R','f1':'F1','left_positive_rate':'左侧编码1比例','right_positive_rate':'右侧编码1比例'}
header=['材料','部门','权重','比较方法','参照','维度','有效配对数','左侧编码1单元数','右侧编码1单元数']
for kind in ['未加权','设计加权']:
 header += [kind+x for x in ['左1右1','左1右0','左0右1','左0右0']]
for m in metric_names.values():header += [m,m+'近似95%区间下限',m+'近似95%区间上限',m+'区间有效重复数',m+'区间未定义重复数']
rows=[]
for name in ['machine_reference_classification.json','A_C_before_third_agreement.json']:
 data=json.loads((STAT/name).read_text())
 for r in data['comparisons']:
  o={'材料':{'probability_canonical':'概率样本','enriched_challenge':'挑战材料'}[r['component']], '部门':groups[r['group']], '权重':{'unweighted':'等额样本描述','eligible_design_weighted':'部门抽样设计加权'}[r['weighting']], '比较方法':methods[r['method']], '参照':refs[r['reference']], '维度':dims[r['dimension']], '有效配对数':r['paired_n'],'左侧编码1单元数':r['left_positive_n'],'右侧编码1单元数':r['reference_positive_n']}
  for kind,key in [('未加权','raw_confusion'),('设计加权','weighted_confusion')]:
   if r['method']=='A_C':
    cells=r['symmetric_raw_cells' if kind=='未加权' else 'symmetric_weighted_cells']; keys=['A1_C1','A1_C0','A0_C1','A0_C0']
   else:cells=r[key];keys=['TP','FP','FN','TN']
   for label,k in zip(['左1右1','左1右0','左0右1','左0右0'],keys):o[kind+label]=cells[k]
  for k,label in metric_names.items():
   if k not in r['metrics']:
    for suffix in ['', '近似95%区间下限','近似95%区间上限','区间有效重复数','区间未定义重复数']:o[label+suffix]='不适用'
    continue
   m=r['metrics'][k]; ci=m['ci95_primary']
   o[label]='NA' if m['estimate'] is None else m['estimate']
   for suffix,key in [('近似95%区间下限','low'),('近似95%区间上限','high'),('区间有效重复数','defined_repetitions'),('区间未定义重复数','undefined_repetitions')]:o[label+suffix]='NA' if ci[key] is None else ci[key]
  rows.append(o)
with SUP.open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=header); w.writeheader(); w.writerows(rows)
with SUP.open(encoding='utf-8-sig',newline='') as f: back=list(csv.DictReader(f))
assert len(back)==len(rows)==420
for actual,expected in zip(back,rows):
 for k in header:assert actual[k]==str(expected[k]),(k,actual[k],expected[k])
binding=json.loads((BASE/'outputs/coding-revision-20261007-r3/manuscript-update-20261008/proxy-180-table2-binding-20261008/表2与五维κ_代理180权威绑定.json').read_text())
for row in binding['table2_values']:
 for ref,v in row['values'].items():
  hit=[x for x in back if x['材料']=='概率样本' and x['部门']=='总体' and x['权重']=='部门抽样设计加权' and x['比较方法']==('自动规则编码' if row['method_role']=='rules' else 'LLM编码') and x['参照']=='编码员'+ref and x['维度']==dims[row['dimension']]]
  assert len(hit)==1
  for k,m in v['metrics'].items():
   actual=float(hit[0][metric_names[k]])
   assert abs(actual-m['estimate'])<1e-12
   assert format(actual,'.3f')==m['display_3dp']
note='编码检验补充统计表\n\n本表导出与正文表2一致的固定统计结果，不新增判读或重新挑选结果。概率样本180条与富集挑战材料60条分别列示；部门抽样设计加权以剩余规范代表框为推断范围，等额样本描述不等于全语料总体。A、B初判来自AI代理，用户确认人工复核后标签未改；复核参照含AI复核者T的判读，不称独立人工裁定。B为原始编码员C的论文显示名称，原文件保持。\n\n机器方法为左侧、所列参照为右侧；A—B比较中A为左侧、B为右侧。四格列为左1右1、左1右0、左0右1、左0右0；机器比较分别对应TP、FP、FN、TN。编码1表示实质讨论该维度。A—B仅报告对称的一致性和两侧编码1比例，P、R、F1记不适用。NA表示分母为零或指标未定义，不替换为1。点估计与区间保留源统计精度，正文独立舍入至3位小数；区间采用既定部门层内重标bootstrap，固定卫健全查层，5000次，详见正文4.2。区间只反映固定材料与标签条件下的抽样变化。\n'
(SUP.parent/'编码检验补充统计表说明.txt').write_text(note,encoding='utf-8')
changed=[i for i,p in enumerate(ps) if plain(p)!=old_paras[i]]
assert changed==[50,51,52,53,54,59,69,71],changed
assert old_tables==[etree.tostring(t) for t in body.findall('w:tbl',NS)]
assert old_refs==[plain(p) for p in ps if plain(p).startswith('[')]
assert old_cites==[etree.tostring(r) for r in root.xpath('.//w:r[w:rPr/w:vertAlign[@w:val="superscript"]]',namespaces=NS)]
xml=etree.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True)
temp=OUT.with_suffix('.staging.docx')
with ZipFile(temp,'w',compression=ZIP_DEFLATED) as z:
 for name,(info,data) in entries.items():z.writestr(info,xml if name=='word/document.xml' else data)
temp.replace(OUT)
with ZipFile(OUT) as z:
 for name,(_,data) in entries.items():
  if name!='word/document.xml':assert z.read(name)==data
audit={'document':str(OUT),'before_sha256':'110c3592814211121d35c2295598a922388acb6a30ed305cfba1d2bc8d9508af','after_sha256':sha(OUT),'changed_paragraphs':{str(i):{'old':old_paras[i],'new':plain(ps[i])} for i in changed},'all_four_tables_unchanged':True,'all66_references_unchanged':True,'all_superscript_citation_runs_unchanged':True,'all_non_document_package_parts_unchanged':True,'supplement':{'path':str(SUP),'sha256':sha(SUP),'rows':420,'roundtrip_all_cells_exact_to_statistics_source':True,'table2_80_display_points_exact_against_binding':True,'float_vs_exact_fraction_estimate_tolerance':1e-12},'new_model_calls':0,'labels_changed':False,'new_metric_or_interval_computations':False,'render_status':'PENDING'}
(R4/'validation_reporting_revision_binding.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in audit.items() if k!='changed_paragraphs'},ensure_ascii=False))
