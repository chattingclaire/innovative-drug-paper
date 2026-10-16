from pathlib import Path
from zipfile import ZipFile
from copy import deepcopy
from collections import Counter
from lxml import etree as E
import json, hashlib, re

OUT=Path(__file__).resolve().parent.parent
SOURCE=OUT/'创新药评价的注意力配置差异与协调路径-交稿版.docx'
TARGET=OUT/'创新药评价的注意力配置差异与协调路径-交稿版-表述修订.docx'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()=='d4a4a56c9ba176dbbd4cf9b68c10fd985ac60a22385a63accd227e99427a53f3'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
def W(s):return '{'+NS['w']+'}'+s
def txt(e):return ''.join(e.xpath('.//w:t/text()',namespaces=NS))
def norm(s):return s.replace('\u2060','')
with ZipFile(SOURCE) as z:
    infos=z.infolist();pkg={i.filename:z.read(i.filename) for i in infos}
root=E.fromstring(pkg['word/document.xml']);body=root.find('w:body',NS);ps=body.findall('w:p',NS)
before=[txt(p) for p in ps];before_xml=[E.tostring(p) for p in ps]
replacements={}
def replace_span(i,old,new):
    s=replacements.get(i,norm(before[i-1]));assert s.count(old)==1,(i,old)
    replacements[i]=s.replace(old,new)

replace_span(2,'自动规则编码中，药监局安全性注意力占比为38.12%，医保局经济性注意力占比为78.20%；两种方法均显示，医保局安全性单元中的有效性比例较高，分别为65.31%和81.01%，药监局为37.79%和42.60%，卫健委为24.32%和26.00%。','自动规则编码中，药监局对安全性的注意力占比为38.12%，医保局对经济性的注意力占比为78.20%。两种方法均显示，在涉及药品安全的政策句段中，同时讨论疗效的句段占比以医保局最高。')
replace_span(6,'Under rule-based and large language model coding, respectively, the proportions of safety units that also address efficacy are 65.31% and 81.01% in medical insurance, compared with 37.79% and 42.60% in drug regulation and 24.32% and 26.00% in health administration.','Both coding methods show that, among policy passages concerning drug safety, the share also addressing therapeutic efficacy is highest in medical insurance policy.')
replace_span(38,'本文将安全性、有效性、经济性、创新性、公平性分别记为S、E、Ec、I、F，','本文将安全性、有效性（疗效与临床获益）、经济性、创新性、公平性分别记为S、E、Ec、I、F，')
replacements[39]='本文区分三类比例。注意力占比反映五维关注的相对分配：以本部门某维被编码为1的句段数，除以五维被编码为1的句段数之和。一个句段涉及多个维度时，分别计入各维，因此五维占比合计为100%。内容覆盖比例反映某类内容出现的范围：以涉及该维的句段数除以本部门全部分析单元数，各维比例可以交叉，合计不必为100%。条件比例考察两类内容在同一句段中出现的情况。例如，“涉及安全性的句段中，同时涉及有效性的比例”，以同时涉及安全性和有效性的句段数为分子，以涉及安全性的句段数为分母；只纳入两维均可判定的句段。交换分母则回答另一问题，即涉及有效性的句段中，有多少同时涉及安全性。两类内容在同一句段中出现的具体含义，结合政策原文及访谈解释。来源构成、汇总方式和待定信息的变化用于检验比较的适用范围。'
replace_span(76,'注意力占比之外，经济性单元中的公平性比例进一步呈现部门差异。在两维均可作二元比较的记录中，','在涉及经济性的句段中，同时涉及公平性的句段占比也呈现部门差异。仅纳入相关两维均可判定的句段，')
replace_span(76,'该比例呈现经济性内容中公平性的共同表达，具体用途结合条文判断（表4）。','这一比较说明，涉及价格、费用或支付的内容，有多少同时涉及患者获取药品的机会与负担；具体用途结合条文判断（表4）。')
replace_span(77,'从公平性内容看，公平性单元中的经济性比例在两种方法中呈现不同的部门方向：','以公平性句段为分母时，比较的是其中有多少同时涉及经济性。两种编码方法呈现不同的部门方向：')
replace_span(83,'医保局的安全性注意力占比较低，但安全性单元中的有效性比例在两种方法中均高于药监局和卫健委。在两维均可作二元比较的记录中，自动规则编码的医保局为32/49（65.31%），药监局为99/262（37.79%），卫健委为9/37（24.32%）；LLM编码中分别为64/79（81.01%）、187/439（42.60%）和13/50（26.00%）。','在涉及安全性的句段中，同时讨论疗效的句段占比，医保局高于药监局和卫健委，两种编码方法均呈现这一差异。以自动规则编码为例，医保局49条涉及安全性且两维均可判定的句段中，有32条同时涉及有效性，占65.31%；药监局和卫健委的对应比例分别为99/262（37.79%）和9/37（24.32%）。LLM编码中，医保局、药监局、卫健委的对应比例分别为64/79（81.01%）、187/439（42.60%）和13/50（26.00%）。')
replace_span(83,'较低的安全性注意力占比与较高的上述条件比例共同呈现其文本关注方式，具体条款将安全有效用于准入及价值比较。','这说明，医保局五维关注中安全性的相对份额较小，而在讨论安全性时更常一并涉及疗效；具体条款将安全有效用于准入及价值比较。')
replace_span(90,'安全性单元中的有效性比例、经济性单元中的公平性比例，以及相关准入、支付和供应条文，','安全性与有效性、经济性与公平性在同一句段中的出现情况，以及相关准入、支付和供应条文，')
replace_span(94,'五维注意力占比，以及安全性与有效性、经济性与公平性的共同表达，','五维注意力占比，以及安全与疗效、费用与保障在同一句段中的出现情况，')
replace_span(103,'在全量主口径中，医保局经济性注意力占比高于卫健委，卫健委经济性单元中的公平性比例则高于医保局；相关条文分别涉及费用保障和机构供应、临床使用。','在全量主口径中，医保局的经济性注意力占比高于卫健委；在涉及经济性的句段中，卫健委同时涉及公平性的句段占比高于医保局。相关条文分别涉及费用保障和机构供应、临床使用。')
replace_span(106,'维度间的条件比例进一步显示，医保局安全性单元中的有效性比例较高；经济性与公平性的共同表达还需结合编码方法及来源构成解释。','进一步比较发现，在涉及药品安全的句段中，医保局同时讨论疗效的句段占比更高；经济性与公平性在同一句段中的出现情况，则随编码方法和来源构成而变化。')
replace_span(106,'本文将部门注意力配置的比较推进到给定维度内容中的共同表达，','本文在比较部门关注重心的基础上，进一步考察不同评价内容在同一句段中如何出现，')

def set_text(p,value):
    rp=None
    for r in p.findall('w:r',NS):
        pr=r.find('w:rPr',NS)
        if pr is not None and pr.find('w:vertAlign',NS) is None:rp=deepcopy(pr);break
    if rp is None:rp=E.Element(W('rPr'))
    for x in list(p):
        if x.tag!=W('pPr'):p.remove(x)
    for s in re.split(r'(\[\d+(?:[-,]\d+)*\])',value):
        if not s:continue
        r=E.SubElement(p,W('r'));pr=deepcopy(rp);r.append(pr)
        cite=bool(re.fullmatch(r'\[\d+(?:[-,]\d+)*\]',s))
        if cite:E.SubElement(pr,W('vertAlign')).set(W('val'),'superscript')
        t=E.SubElement(r,W('t'));t.text=('\u2060'+s) if cite else s
        if s.startswith(' ') or s.endswith(' '):t.set('{http://www.w3.org/XML/1998/namespace}space','preserve')

changes=[]
for i,value in replacements.items():
    set_text(ps[i-1],value);changes.append({'paragraph_before_revision':i,'before':before[i-1],'after':txt(ps[i-1])})
for i,p in enumerate(ps,1):
    if i not in replacements:assert E.tostring(p)==before_xml[i-1],i
full=txt(body)
for term in ['安全性单元中的有效性比例','经济性单元中的公平性比例','公平性单元中的经济性比例','safety units']:
    assert term not in full,term
ref_start=before.index('参考文献');assert [txt(p) for p in ps[ref_start:]]==before[ref_start:]
# Every table, figure, data value outside the simplified abstracts and explanatory definition is retained.
for i in replacements:
    if i not in [2,6,39]:assert Counter(re.findall(r'\d+(?:\.\d+)?',before[i-1]))==Counter(re.findall(r'\d+(?:\.\d+)?',txt(ps[i-1]))),i
pkg['word/document.xml']=E.tostring(root,encoding='UTF-8',xml_declaration=True,standalone=True)
with ZipFile(TARGET,'w') as z:
    for info in infos:z.writestr(info,pkg[info.filename])
with ZipFile(SOURCE) as z:
    changed_parts=[name for name in z.namelist() if z.read(name)!=pkg[name]]
assert changed_parts==['word/document.xml']
record={'source':str(SOURCE),'output':str(TARGET),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(TARGET.read_bytes()).hexdigest(),'changes':changes,'tables_figures_and_66_references_preserved':True,'no_statistics_recomputed':True,'abstract_removed_conditional_percentages_only':True,'visual_review':'pending'}
(OUT/'_work/clarity-edit-record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
(OUT/'_work/clarity-submission-text.txt').write_text('\n'.join(txt(e) for e in body)+'\n')
print(json.dumps({'output':str(TARGET),'modified_paragraphs':list(replacements),'changed_parts':changed_parts},ensure_ascii=False))
