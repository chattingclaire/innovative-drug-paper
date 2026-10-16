from pathlib import Path
from zipfile import ZipFile
from copy import deepcopy
from lxml import etree as E
import hashlib, json
WOR=Path(__file__).resolve().parent
SRC=WOR.parent/'创新药评价的注意力配置差异与协调路径-署名修订版.docx'
DST=WOR.parent/'创新药评价的注意力配置差异与协调路径-署名信息补全版.docx'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
def W(n):return '{'+NS['w']+'}'+n
def tx(e):return ''.join(e.xpath('.//w:t/text()',namespaces=NS))
def get(e,n):
    c=e.find('w:'+n,NS)
    if c is None:
        c=E.Element(W(n));e.insert(0,c) if n in ['pPr','rPr'] else e.append(c)
    return c
def val(e,n,v):get(e,n).set(W('val'),str(v))
def run(p,s,sup=False,ea='宋体'):
    r=E.SubElement(p,W('r'));rp=E.SubElement(r,W('rPr'));f=E.SubElement(rp,W('rFonts'))
    for k,v in [('ascii','Times New Roman'),('hAnsi','Times New Roman'),('eastAsia',ea),('cs','Times New Roman')]:f.set(W(k),v)
    for n,v in [('b','0'),('bCs','0'),('color','000000'),('sz','21'),('szCs','21')]:val(rp,n,v)
    if sup:val(rp,'vertAlign','superscript')
    t=E.SubElement(r,W('t'));t.text=s;t.set('{http://www.w3.org/XML/1998/namespace}space','preserve')
    return r

def para(s='',align='center',keep=True,line=280):
    p=E.Element(W('p'));pp=E.SubElement(p,W('pPr'))
    val(pp,'jc',align);val(pp,'keepNext',int(keep));val(pp,'keepLines',1);val(pp,'snapToGrid',0)
    E.SubElement(pp,W('ind')).attrib.update({W('firstLine'):'0',W('firstLineChars'):'0',W('left'):'0',W('right'):'0'})
    E.SubElement(pp,W('spacing')).attrib.update({W('before'):'0',W('after'):'40',W('line'):str(line),W('lineRule'):'exact'})
    if s:run(p,s)
    return p

assert hashlib.sha256(SRC.read_bytes()).hexdigest()=='e71006d4343fda7c2b3ceb7c34c55f26e0a934a7a984dfdb538d046430873a36'
with ZipFile(SRC) as z:infos=z.infolist();pkg={i.filename:z.read(i.filename) for i in infos}
doc=E.fromstring(pkg['word/document.xml']);body=doc.find('w:body',NS);ps=body.findall('w:p',NS)
body_start=next(p for p in ps if tx(p)=='1\u3000引言')
original_tail=[E.tostring(e) for e in list(body)[list(body).index(body_start):]]
assert tx(ps[2]).startswith('（1. 中国科学院科技战略咨询研究院')
assert tx(ps[8])=='WANG Xiaojiong, CHEN Haiting, LIU Zhongquan'
zh=[
'（1. 中国科学院科技战略咨询研究院，北京 100190；',
'2. 中国科学院大学公共政策与管理学院，北京 100049；',
'3. 国家发展和改革委员会创新驱动发展中心，北京 100038）']
idx=list(body).index(ps[2]);body.remove(ps[2]);body.remove(ps[3])
for i,s in enumerate(zh):body.insert(idx+i,para(s))
en=para()
for i,(name,units) in enumerate([('WANG Xiaojiong','1'),('CHEN Haiting','1,2'),('LIU Zhongquan','3')]):
    if i:run(en,', ')
    run(en,name);run(en,units,True)
enidx=list(body).index(ps[8]);body.remove(ps[8]);body.insert(enidx,en)
aff=[
'(1. Institutes of Science and Development, Chinese Academy of Sciences, Beijing 100190, China;',
'2. School of Public Policy and Management, University of Chinese Academy of Sciences, Beijing 100049, China;',
'3. Center for Innovation-Driven Development, National Development and Reform Commission, Beijing 100038, China)']
for i,s in enumerate(aff):body.insert(enidx+1+i,para(s))

froot=E.fromstring(pkg['word/footnotes.xml']);foot=froot.find('w:footnote[@w:id="1"]',NS)
for c in list(foot):foot.remove(c)
f=para('基金项目：国家自然科学基金项目（72074204）。','left',False)
foot.append(f)
bios=[
'作者简介：王孝炯（1982—），男，安徽合肥人，中国科学院科技战略咨询研究院研究员。主要研究方向：创新发展政策。',
'陈海婷（2002—），女，福建建瓯人，中国科学院科技战略咨询研究院、中国科学院大学公共政策与管理学院硕士研究生。主要研究方向：科技创新管理与政策。',
'刘中全（1988—），男，河南周口人，国家发展和改革委员会创新驱动发展中心副研究员。主要研究方向：科技政策、生物经济。']
for s in bios:foot.append(para(s,'left',False))
# The user explicitly requested leaving the corresponding author unspecified.
assert '本文通信作者' not in tx(foot)
assert original_tail==[E.tostring(e) for e in list(body)[list(body).index(body_start):]]
for name,tree in [('word/document.xml',doc),('word/footnotes.xml',froot)]:pkg[name]=E.tostring(tree,xml_declaration=True,encoding='UTF-8',standalone=True)
with ZipFile(DST,'w') as z:
    for info in infos:z.writestr(info,pkg[info.filename])
with ZipFile(SRC) as a,ZipFile(DST) as b:
    changes=[n for n in a.namelist() if a.read(n)!=b.read(n)]
assert changes==['word/document.xml','word/footnotes.xml'],changes
record={
'source':str(SRC),'output':str(DST),'output_sha256':hashlib.sha256(DST.read_bytes()).hexdigest(),
'changed_parts':changes,'main_text_tables_figures_references_unchanged':True,
'corresponding_author':'用户于2026-10-13要求先留空，不指定、不添加通信作者标记',
'changes':['中文单位补城市和邮编','英文姓名补单位上标','补英文单位、城市、邮编、国名','基金改为名称及编号，依模板删项目题目','三位作者简介分段列出，保留全部已有个人信息'],
'affiliation_evidence':[
'https://www.casisd.cn/',
'https://english.casisd.cn/',
'https://sppm.ucas.ac.cn/index.php/en/lxwm-en',
'https://www.mdpi.com/2227-7390/13/19/3224',
'https://www.kygl.net.cn/CN/abstract/abstract23153.shtml',
'https://pubmed.ncbi.nlm.nih.gov/39319718/'],
'visual_review':'pending'}
(WOR/'author-metadata-completion-record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2))
print(json.dumps(record,ensure_ascii=False,indent=2))
