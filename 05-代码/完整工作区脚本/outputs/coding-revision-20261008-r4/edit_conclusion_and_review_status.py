from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree
from copy import deepcopy
import hashlib, json, re

BASE=Path(__file__).resolve().parents[2]
DEST=BASE/'outputs/final-three-department-20261008-human-validation-template'
SRC=DEST/'论文修订稿-编码实算结果版.docx'
OUT=DEST/'创新药评价的注意力配置差异与协调路径.docx'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W='{'+NS['w']+'}'
with ZipFile(SRC) as z:
    entries={i.filename:(i,z.read(i.filename)) for i in z.infolist()}
root=etree.fromstring(entries['word/document.xml'][1]);body=root.find('w:body',NS);ps=body.findall('w:p',NS)
def plain(p):return ''.join(p.xpath('.//w:t/text()',namespaces=NS))
def rewrite_plain(p,text):
    original_rpr=p.find('w:r/w:rPr',NS)
    for child in list(p):
        if child.tag!=W+'pPr':p.remove(child)
    run=etree.SubElement(p,W+'r')
    if original_rpr is not None:run.append(deepcopy(original_rpr))
    t=etree.SubElement(run,W+'t');t.text=text
assert plain(ps[101])=='7 结语'
original_paras={str(i):plain(ps[i]) for i in [46,49,54,102,103,104,108,109]}
# Preserve the existing citation runs while removing internal implementation names.
for run in ps[46].findall('w:r',NS):
    for t in run.findall('w:t',NS):
        if t.text:
            t.text=t.text.replace('LLM编码使用gpt-5.6-sol，依据完整编码手册','LLM编码依据完整编码手册')
            t.text=t.text.replace('两种全量方法使用同版原文、统一五维定义与纳排边界，版本分别为rules-v36.2-development与LLM-v32-candidate03-single-unit-reconciled-development，保留版本及完整运行记录。','两种方法使用相同的政策原文与必要上下文，遵循统一的五维定义、纳入条件与排除条件。')
assert 'rules-v36.2' not in plain(ps[46]) and 'candidate03' not in plain(ps[46])
text=plain(ps[49])
old='复核编码员A、编码员B及裁定者T均由AI代理承担。'
new='编码员A、编码员B的初始判读及裁定者T的复核由AI代理完成，现有A、B标签经人工复核后保留。'
assert text.count(old)==1
rewrite_plain(ps[49],text.replace(old,new))
text=plain(ps[54]);old='上述结果对应当前版本与既有复核标签的开发诊断，人工编码的独立检验另行实施。'
assert text.count(old)==1
rewrite_plain(ps[54],text.replace(old,'上述结果反映既有复核材料上的编码一致性与分类表现。'))
conclusion='本文基于三部门创新药评价政策文本，在安全性、有效性、经济性、创新性和公平性的统一框架下比较注意力配置。自动规则编码与LLM编码均显示，药监以安全性、医保以经济性、卫健以公平性为最高注意力占比维度。进一步发现，卫健经济性单元中的公平性比例高于医保；政策原文与访谈表明，这一差别涉及费用保障、药品供应和临床使用等不同任务。本文将部门注意力配置的比较推进到维度间的内容联系，据此提出在参照药预沟通中对照评价条件、依托可信评价点衔接补充证据、通过目录落地反馈连接支付与患者获取的协调路径。本文主要考察政策文本表达，尚未直接检验上述配置与实际执行效果之间的关系，后续可结合药品评审、机构配备和患者使用资料开展验证。'
rewrite_plain(ps[102],conclusion)
body.remove(ps[103]);body.remove(ps[104])
# Technical recovery logs remain in the archived run records, not in the manuscript.
old='实际采用的全量运行由196个原批次有效输出与25条单单元技术恢复结果汇合，覆盖4924条；原197批方案中第115批在三次尝试后未通过技术校验；首次技术有效输出、失败重试、版本和提示SHA见封存清单。'
new='全量编码覆盖4924个分析单元，完整规则、提示词及运行记录随研究资料留存。'
assert old in plain(ps[108])
for t in ps[108].xpath('.//w:t',namespaces=NS):
    if t.text:t.text=t.text.replace(old,new).replace('该范围不含25条单单元恢复记录。','')
assert old not in plain(ps[108])
for t in ps[109].xpath('.//w:t',namespaces=NS):
    if t.text:t.text=t.text.replace('以及抽样权重、四格、实际执行和代码及输入输出哈希','以及抽样权重、四格、代码、提示词与输入输出记录')
new_xml=etree.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True)
assert not OUT.exists(),'Do not overwrite an already delivered revision'
with ZipFile(OUT,'w',compression=ZIP_DEFLATED) as z:
    for name,(info,data) in entries.items():z.writestr(info,new_xml if name=='word/document.xml' else data)
with ZipFile(OUT) as z:
    for name,(_,data) in entries.items():
        if name!='word/document.xml':assert z.read(name)==data,name
new_ps=body.findall('w:p',NS)
heading_i=next(i for i,p in enumerate(new_ps) if plain(p)=='7 结语')
appendix_i=next(i for i,p in enumerate(new_ps) if plain(p).startswith('附录A '))
assert appendix_i-heading_i==2
tables=root.findall('.//w:body/w:tbl',NS)
with ZipFile(SRC) as z:oldroot=etree.fromstring(z.read('word/document.xml'))
oldtables=oldroot.findall('.//w:body/w:tbl',NS)
assert len(tables)==len(oldtables)==4
for a,b in zip(tables,oldtables):assert etree.tostring(a)==etree.tostring(b)
assert '待填' not in ''.join(root.xpath('.//w:t/text()',namespaces=NS))
allps=''.join(plain(p) for p in new_ps)
pre=next(i for i,p in enumerate(new_ps) if plain(p).startswith('1 引言'))
main=''.join(plain(p) for p in new_ps[pre:appendix_i])
main_tables=''.join(''.join(t.xpath('.//w:t/text()',namespaces=NS)) for t in tables)
report={'source':str(SRC),'output':str(OUT),'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),'old_paragraphs':original_paras,'new_conclusion':conclusion,'conclusion_paragraphs':1,'conclusion_han':len(re.findall(r'[\u4e00-\u9fff]',conclusion)),'conclusion_nonwhite':len(re.sub(r'\s','',conclusion)),'table2_80_values_and_all_four_tables_identical':True,'all_non_document_package_entries_identical':True,'no_pending_table_values':True,'main_han_without_tables':len(re.findall(r'[\u4e00-\u9fff]',main)),'main_han_including_tables':len(re.findall(r'[\u4e00-\u9fff]',main+main_tables)),'count_method':'OOXML汉字计数；非Word字数；附录、参考文献与前置部分单独，不据此声称期刊篇幅豁免','render_review':'PENDING'}
(BASE/'outputs/coding-revision-20261008-r4/conclusion_revision_binding.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in report.items() if k not in ['old_paragraphs','new_conclusion']},ensure_ascii=False))
