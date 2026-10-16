from pathlib import Path
from zipfile import ZipFile
from copy import deepcopy
from lxml import etree as E
from collections import Counter
import json,re,hashlib

WORK=Path(__file__).resolve().parent
OUT=WORK.parent
SRC=OUT/'创新药评价的注意力配置差异与协调路径-交稿版-表述修订.docx'
DST=OUT/'创新药评价的注意力配置差异与协调路径-署名修订版.docx'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
def W(s):return '{'+NS['w']+'}'+s
def text(e):return ''.join(e.xpath('.//w:t/text()',namespaces=NS))
def norm(s):return s.replace('\u2060','')
def get(e,n):
    x=e.find('w:'+n,NS)
    if x is None:x=E.SubElement(e,W(n))
    owners={'pPr':'p','rPr':'r','tblPr':'tbl','trPr':'tr','tcPr':'tc'}
    if n in owners and e.tag==W(owners[n]) and len(e) and e[0] is not x:
        e.remove(x);e.insert(0,x)
    return x
def val(e,n,v):get(e,n).set(W('val'),str(v))
def fonts(rp,ea='宋体',sz=None,bold=None):
    f=get(rp,'rFonts');f.attrib.clear()
    for k,v in [('ascii','Times New Roman'),('hAnsi','Times New Roman'),('eastAsia',ea),('cs','Times New Roman')]:f.set(W(k),v)
    get(rp,'color').attrib.clear();get(rp,'color').set(W('val'),'000000')
    if sz is not None:val(rp,'sz',sz);val(rp,'szCs',sz)
    if bold is not None:val(rp,'b',int(bold));val(rp,'bCs',int(bold))
def set_text(p,value,cites=True):
    rp=E.Element(W('rPr'))
    for r in p.findall('w:r',NS):
        t=r.find('w:rPr',NS)
        if t is not None and t.find('w:vertAlign',NS) is None:
            rp=deepcopy(t);break
    for x in list(p):
        if x.tag!=W('pPr'):p.remove(x)
    for s in re.split(r'(\[\d+(?:[-,]\d+)*\])',norm(value)) if cites else [value]:
        if not s:continue
        r=E.SubElement(p,W('r'));rpr=deepcopy(rp);r.append(rpr)
        citation=cites and bool(re.fullmatch(r'\[\d+(?:[-,]\d+)*\]',s))
        if citation:val(rpr,'vertAlign','superscript')
        t=E.SubElement(r,W('t'));t.text=('\u2060'+s) if citation else s
        t.set('{http://www.w3.org/XML/1998/namespace}space','preserve')
def paragraph(value,ea='宋体',sz=21,align='center',keep=True):
    p=E.Element(W('p'));pr=get(p,'pPr')
    val(pr,'jc',align);val(pr,'keepNext',int(keep));val(pr,'snapToGrid',0)
    get(pr,'ind').attrib.update({W('firstLine'):'0',W('firstLineChars'):'0',W('left'):'0',W('right'):'0'})
    get(pr,'spacing').attrib.update({W('before'):'0',W('after'):'40',W('line'):'280',W('lineRule'):'auto'})
    r=E.SubElement(p,W('r'));fonts(get(r,'rPr'),ea,sz,False)
    E.SubElement(r,W('t')).text=value
    return p

assert hashlib.sha256(SRC.read_bytes()).hexdigest()=='494fe4856a837e5289b96f2fb84eb2443d5211313bbb4bf7c17a4f9db95050a2'
with ZipFile(SRC) as z:
    infos=z.infolist();pkg={i.filename:z.read(i.filename) for i in infos}
root=E.fromstring(pkg['word/document.xml']);body=root.find('w:body',NS)
ps=body.findall('w:p',NS);tables=body.findall('w:tbl',NS)
original=[text(p) for p in ps];original_tables=[[[text(c) for c in r.findall('w:tc',NS)] for r in t.findall('w:tr',NS)] for t in tables]
entries=[]
for filename in ['chinese-polish-front.json','chinese-polish-methods.json','chinese-polish-discussion.json']:
    entries+=json.loads((WORK/filename).read_text())['entries']
assert len({x['index'] for x in entries})==len(entries)
for x in entries:
    i=x['index'];assert norm(text(ps[i]))==norm(x['before']),(i,'source mismatch')
    if i not in [94,101]:
        assert re.findall(r'\[\d+(?:[-,]\d+)*\]',norm(x['before']))==re.findall(r'\[\d+(?:[-,]\d+)*\]',x['after']),(i,'citations')
    set_text(ps[i],x['after'])

# A concise abstract, with explicit subjects and unchanged findings.
abstract='摘要：创新药评价涉及上市、医保准入和临床使用等环节，跨部门协调需要明确各环节的评价重点及结论适用范围。本文以药监局、医保局和卫健委2017—2026年的51项政策资料为研究对象，采用自动规则编码和大语言模型编码，从安全性、有效性、经济性、创新性、公平性五个维度比较注意力配置，并结合政策条文与专家访谈解释部门差异。自动规则编码显示，药监局对安全性的注意力占比为38.12%，医保局对经济性的注意力占比为78.20%。两种方法均发现，在涉及药品安全的表述中，医保局同时讨论疗效的比例最高。政策条文和访谈表明，部门评价差异与费用保障、药品供应和临床使用等任务有关。跨部门协调应针对同一适应症和目标人群对照评价结论，统筹补充研究，并共享支付、配备和使用信息。'
set_text(ps[1],abstract)

table_entries=json.loads((WORK/'chinese-polish-tables.json').read_text())['entries']
for x in table_entries:
    cell=tables[x['table']].findall('w:tr',NS)[x['row']].findall('w:tc',NS)[x['col']]
    assert text(cell)==x['before']
    pp=cell.find('w:p',NS);set_text(pp,x['after'],False)
    for p in cell.findall('w:p',NS)[1:]:cell.remove(p)

# Make inherited defaults explicit to prevent Latin/CJK font drift.
styles=E.fromstring(pkg['word/styles.xml'])
defaults=get(get(styles,'docDefaults'),'rPrDefault');fonts(get(defaults,'rPr'),'宋体',24)
for sid in ['3','28']:
    st=styles.find(f'w:style[@w:styleId="{sid}"]',NS)
    if st is not None:
        fonts(get(st,'rPr'),'宋体',24)
        get(get(st,'pPr'),'spacing').attrib.update({W('before'):'0',W('after'):'0',W('line'):'360',W('lineRule'):'auto'})
for sid,sz in [('4',21),('62',21)]:
    st=styles.find(f'w:style[@w:styleId="{sid}"]',NS)
    if st is not None:fonts(get(st,'rPr'),'黑体' if sid=='4' else '宋体',sz)

format_changes=[]
for i,p in enumerate(ps):
    s=text(p);pp=get(p,'pPr');st=pp.find('w:pStyle',NS);sid=st.get(W('val')) if st is not None else ''
    # Titles and captions are based on the retained journal template.
    heading=bool(re.match(r'^\d+(?:\.\d+)*\s+',s)) or s.startswith('附录') or s=='参考文献'
    if heading:
        s=re.sub(r'^(\d+(?:\.\d+)*|附录[A-Z])\s+',lambda m:m[1]+'\u3000',s)
        set_text(p,s,False);val(pp,'keepNext',1)
        get(pp,'ind').attrib.update({W('firstLine'):'0',W('firstLineChars'):'0',W('left'):'240'})
        ea='黑体';sz=21 if re.match(r'^\d+\.\d+',s) else 24
        for r in p.findall('w:r',NS):fonts(get(r,'rPr'),ea,sz)
    elif i in [1,2,3,5,6]:
        val(pp,'jc','left');val(pp,'snapToGrid',0)
        get(pp,'ind').attrib.update({W('firstLine'):'0',W('firstLineChars'):'0',W('left'):'0',W('right'):'0'})
        for r in p.findall('w:r',NS):fonts(get(r,'rPr'),'宋体',21)
    elif sid=='62':
        for r in p.findall('w:r',NS):fonts(get(r,'rPr'),'宋体',21,False)
        val(pp,'jc','left');val(pp,'keepLines',1);val(pp,'keepNext',0)
        get(pp,'spacing').attrib.update({W('line'):'276',W('lineRule'):'auto',W('before'):'40',W('after'):'60'})
    elif re.match(r'^[图表]\s*[0-9C]',s):
        for r in p.findall('w:r',NS):fonts(get(r,'rPr'),'宋体',21,False)
    # Keep normal text black; preserve superscript citation position.
    for r in p.findall('w:r',NS):
        rp=get(r,'rPr');f=rp.find('w:rFonts',NS)
        if f is not None:
            ea=f.get(W('eastAsia'),'宋体');fonts(rp,ea)
    if re.match(r'^(?:[图表]\s*[0-9C]|Figure |Table )',s):val(pp,'keepNext',1)
    if p.find('.//w:drawing',NS) is not None or p.find('.//w:pict',NS) is not None:val(pp,'keepNext',1)

# Reference punctuation is half-width. English title spaces and URLs are retained.
references=[]
for i,p in enumerate(ps):
    if re.match(r'^\[\d+\]',text(p)):
        old=text(p);new=old.translate(str.maketrans({'（':'(', '）':')','：':':','，':',','；':';'}))
        new=re.sub(r'\]\s+\(','](',new)
        # No space after bibliographic field delimiters in Chinese entries.
        if re.match(r'^\[\d+\]\s*[\u4e00-\u9fff]',new):
            new=re.sub(r'([.,:;])\s+(?=[\u4e00-\u9fff(\[]|https?://)',r'\1',new)
        if old!=new:set_text(p,new,False);format_changes.append({'paragraph':i,'before':old,'after':new})
        val(get(p,'pPr'),'jc','left');val(get(p,'pPr'),'keepLines',1)
        for r in p.findall('w:r',NS):fonts(get(r,'rPr'),'宋体',21,False)
        references.append(new)
assert len(references)==66

# Reflow tables within the text block. Narrative cells must never use justification.
widths=[
 [1700,1100,2500,2900,2266],
 [1100,1800,1892,1892,1891,1891],
 [1100,1800,1514,1513,1513,1513,1513],
 [1000,3156,3155,3155],
 [1100,850,850,800,3350,1758,1758],
 [1100,950,2104,2104,2104,2104],
 [1100,1561,1561,1561,1561,1561,1561],
 [2466,1600,1600,1600,1600,1600]
]
for ti,t in enumerate(tables):
    assert sum(widths[ti])==10466,(ti,sum(widths[ti]))
    pr=get(t,'tblPr');get(pr,'tblW').attrib.update({W('w'):'10466',W('type'):'dxa'})
    val(pr,'jc','center');get(pr,'tblLayout').set(W('type'),'fixed')
    mar=get(pr,'tblCellMar')
    for edge,n in [('top',110 if ti in [0,3] else 65),('bottom',110 if ti in [0,3] else 65),('left',100),('right',100)]:
        get(mar,edge).attrib.update({W('w'):str(n),W('type'):'dxa'})
    grid=get(t,'tblGrid')
    for x in list(grid):grid.remove(x)
    for n in widths[ti]:E.SubElement(grid,W('gridCol')).set(W('w'),str(n))
    rows=t.findall('w:tr',NS)
    for ri,row in enumerate(rows):
        rpr=get(row,'trPr');val(rpr,'cantSplit',1)
        for h in rpr.findall('w:trHeight',NS):rpr.remove(h)
        if ti not in [0,3]:get(rpr,'trHeight').attrib.update({W('val'):'400',W('hRule'):'atLeast'})
        if ri==0:val(rpr,'tblHeader',1)
        for ci,cell in enumerate(row.findall('w:tc',NS)):
            cp=get(cell,'tcPr');get(cp,'tcW').attrib.update({W('w'):str(widths[ti][ci]),W('type'):'dxa'})
            val(cp,'vAlign','center')
            for cm in cp.findall('w:tcMar',NS):cp.remove(cm)
            for p in cell.findall('w:p',NS):
                pp=get(p,'pPr');val(pp,'jc','left' if ti in [0,3] else 'center');val(pp,'snapToGrid',0)
                # All tables fit on a page; keep rows together to prevent an isolated final row.
                val(pp,'keepNext',1);val(pp,'keepLines',1)
                get(pp,'ind').attrib.update({W('firstLine'):'0',W('firstLineChars'):'0',W('left'):'0',W('right'):'0'})
                get(pp,'spacing').attrib.update({W('before'):'0',W('after'):'0',W('line'):'276',W('lineRule'):'auto'})
                for r in p.findall('w:r',NS):fonts(get(r,'rPr'),'宋体',21,ri==0)

# Restore actual authors from a verified historic named manuscript.
auth=json.loads((WORK/'author-source.json').read_text())
assert hashlib.sha256(Path(auth['primary_source']['path']).read_bytes()).hexdigest()==auth['primary_source']['sha256']
a=auth['recovered']
az=paragraph('','仿宋',24)
for oldrun in list(az.findall('w:r',NS)):az.remove(oldrun)
for i,name in enumerate(a['author_order_zh']):
    r=E.SubElement(az,W('r'));fonts(get(r,'rPr'),'仿宋',24,False);E.SubElement(r,W('t')).text=('，' if i else '')+name
    r=E.SubElement(az,W('r'));fonts(get(r,'rPr'),'仿宋',24,False);val(get(r,'rPr'),'vertAlign','superscript');E.SubElement(r,W('t')).text=['1','1,2','3'][i]
ps[0].addnext(az)
aff=paragraph('（1. 中国科学院科技战略咨询研究院；2. 中国科学院大学公共政策与管理学院；')
az.addnext(aff)
aff2=paragraph('3. 国家发展和改革委员会创新驱动发展中心）')
aff.addnext(aff2)
ae=paragraph(', '.join(a['author_order_en']),'宋体',21)
ps[4].addnext(ae)

# Insert deliberate line breaks at phrase boundaries in the narrative table.
for ri,ci,parts in [
    (1,2,['保证安全、有效','和质量可控']),
    (1,3,['以临床价值为导向；','提供相应证据']),
    (1,4,['证据如何支持','上市决策']),
    (2,3,['临床必需、安全有效、','价格合理']),
    (2,4,['评价结论如何用于','准入和支付']),
    (3,2,['保障供应、规范使用，','满足用药需求']),
    (3,3,['安全性、有效性、经济性、','创新性、适宜性、可及性']),
    (3,4,['综合评价如何','指导临床使用'])
]:
    p=tables[0].findall('w:tr',NS)[ri].findall('w:tc',NS)[ci].find('w:p',NS)
    assert ''.join(parts)==text(p)
    set_text(p,'',False)
    for j,s in enumerate(parts):
        r=E.SubElement(p,W('r'));fonts(get(r,'rPr'),'宋体',21,False)
        if j:E.SubElement(r,W('br'))
        E.SubElement(r,W('t')).text=s

# Place funding and biographies in a genuine first-page footnote, not the body/footer.
fn=E.fromstring(pkg['word/footnotes.xml'])
for x in list(fn):
    if int(x.get(W('id'),'0'))>=0 and x.get(W('type')) not in ['separator','continuationSeparator']:fn.remove(x)
note=E.SubElement(fn,W('footnote'));note.set(W('id'),'1')
fund=a['funding_raw']
bio='作者简介：王孝炯（1982—），男，安徽合肥人，中国科学院科技战略咨询研究院研究员，研究方向为创新发展政策；陈海婷（2002—），女，福建建瓯人，中国科学院科技战略咨询研究院、中国科学院大学公共政策与管理学院硕士研究生，研究方向为科技创新管理与政策；刘中全（1988—），男，河南周口人，国家发展和改革委员会创新驱动发展中心副研究员，研究方向为科技政策、生物经济。'
for s in [fund,bio]:
    p=paragraph(s,sz=21,align='left',keep=False)
    sp=get(get(p,'pPr'),'spacing');sp.set(W('line'),'240');sp.set(W('after'),'0')
    note.append(p)
marker=E.SubElement(ps[0],W('r'));rp=get(marker,'rPr');fonts(rp,'宋体',16);val(rp,'vertAlign','superscript')
ref=E.SubElement(marker,W('footnoteReference'));ref.set(W('id'),'1');ref.set(W('customMarkFollows'),'1')
E.SubElement(marker,W('t')).text='*'

# Verify no table statistics or embedded artwork changed.
for ti in range(1,len(tables)):
    if ti==3:continue
    now=[[text(c) for c in row.findall('w:tc',NS)] for row in tables[ti].findall('w:tr',NS)]
    assert now==original_tables[ti],ti
all_text=text(body)
assert not any(x in all_text for x in ['［作者姓名','英文署名待补','{{'])
for r in root.xpath('.//w:r',namespaces=NS):
    if re.fullmatch(r'\[\d+(?:[-,]\d+)*\]',norm(text(r))) and r.getparent() in ps[:131]:
        assert r.find('w:rPr/w:vertAlign',NS).get(W('val'))=='superscript'
pkg['word/document.xml']=E.tostring(root,encoding='UTF-8',xml_declaration=True,standalone=True)
pkg['word/styles.xml']=E.tostring(styles,encoding='UTF-8',xml_declaration=True,standalone=True)
pkg['word/footnotes.xml']=E.tostring(fn,encoding='UTF-8',xml_declaration=True,standalone=True)
with ZipFile(DST,'w') as z:
    for info in infos:z.writestr(info,pkg[info.filename])
record={'source':str(SRC),'output':str(DST),'sha256':hashlib.sha256(DST.read_bytes()).hexdigest(),'language_paragraphs':len(entries),'language_changes':entries,'table_text_changes':table_entries,'reference_punctuation_changes':format_changes,'numeric_tables_unchanged':True,'references_count':66,'authors':a['author_order_zh'],'author_source':auth['primary_source'],'unconfirmed_author_details':['城市邮编','英文单位名称','通信作者'],'formatting':['字体显式指定','标题字号及间距','中文摘要左对齐','表注五号','叙述表格固定列宽左对齐与行距','表格不拆行且整体同页','首面作者简介基金脚注'],'visual_review':'pending'}
(WORK/'named-polish-record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
(WORK/'named-polish-text.txt').write_text('\n'.join(text(x) for x in body)+'\n')
print(json.dumps({k:record[k] for k in ['output','language_paragraphs','numeric_tables_unchanged','references_count','authors']},ensure_ascii=False))
