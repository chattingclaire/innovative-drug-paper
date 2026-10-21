from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
import re, json, hashlib, difflib

ROOT = Path('/PROJECT_ROOT')
SRC = ROOT/'outputs/goal-calibration-20261010/08-manuscript/submission-20261013/创新药评价的注意力配置差异与协调路径-署名阅读版-最终结果.docx'
OUT = Path(__file__).resolve().parent.parent
DST = OUT/'创新药评价的注意力配置差异与协调路径-格式校正版-方法待定.docx'
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS = {'w': W}
def tag(n): return '{'+W+'}'+n
def child(e,n):
    v=e.find(tag(n))
    if v is None: v=E.SubElement(e,tag(n))
    return v
def pt(p): return ''.join(p.xpath('.//w:t/text()',namespaces=NS))
def plain(t): return re.sub(r'\s+','',t)
def sha(b): return hashlib.sha256(b).hexdigest()
def rewrite(p, after):
    nodes=p.xpath('.//w:t',namespaces=NS)
    before=''.join(n.text or '' for n in nodes)
    starts=[]; x=0
    for n in nodes: starts.append(x); x+=len(n.text or '')
    for op,a,b,c,d in reversed(difflib.SequenceMatcher(a=before,b=after,autojunk=False).get_opcodes()):
        if op=='equal': continue
        # All edits are spaces; assign inserted spaces to the text node at the boundary.
        if a==b:
            k=max(i for i,s in enumerate(starts) if s<=a)
            t=nodes[k].text or ''; off=a-starts[k]
            nodes[k].text=t[:off]+after[c:d]+t[off:]
        else:
            ks=[i for i,s in enumerate(starts) if s<b and s+len(nodes[i].text or '')>a]
            for k in reversed(ks):
                t=nodes[k].text or ''; lo=max(a-starts[k],0); hi=min(b-starts[k],len(t))
                nodes[k].text=t[:lo]+(after[c:d] if k==ks[0] else '')+t[hi:]
    for n in nodes:
        if n.text and (n.text[0].isspace() or n.text[-1].isspace()):n.set('{http://www.w3.org/XML/1998/namespace}space','preserve')
    assert pt(p)==after

with ZipFile(SRC) as z: parts={n:z.read(n) for n in z.namelist()}; infos=z.infolist()
assert sha(SRC.read_bytes())=='ec0e35657665255569a609a4890d4e5ddb22cef0c7085cf2dc6810860de7b136'
doc=E.fromstring(parts['word/document.xml']); styles=E.fromstring(parts['word/styles.xml'])
ps=doc.xpath('//w:body/w:p',namespaces=NS)
assert len(ps)==200
old_ps=[pt(p) for p in ps]
edits=[]
headings=[21,25,28,31,35,44,48,55,68,72,81,90,95,101,104,108]
for i in headings:
    assert ps[i].find('w:pPr/w:pStyle',NS).get(tag('val'))=='4'
    for r in ps[i].xpath('.//w:r',namespaces=NS):
        rp=child(r,'rPr')
        for n in ['sz','szCs']:child(rp,n).set(tag('val'),'24')
    edits.append({'type':'heading_size','paragraph':i,'text':pt(ps[i]),'before_pt':10.5,'after_pt':12})
style=styles.xpath('//w:style[@w:styleId="4"]',namespaces=NS)[0]
for n in ['sz','szCs']:child(child(style,'rPr'),n).set(tag('val'),'24')

number_map={54:['4481','1848','2100'],56:['1151','1112','1000'],57:['1151','5000'],61:['1151'],64:['1151','4481'],67:['4481','1848','2100'],79:['1088','1148'],116:['4481'],119:['4481','1848','2100'],120:['4481'],128:['5000','0.935680','0.935712'],132:['1151','4481']}
sep='\u202f'
def grouped(n):
    a,*b=n.split('.')
    a=re.sub(r'(?<=\d)(?=(?:\d{3})+$)',sep,a)
    return a+('.'+sep.join(b[0][k:k+3] for k in range(0,len(b[0]),3)) if b else '')
for i,vals in number_map.items():
    before=pt(ps[i]);after=before
    for val in vals:
        after,n=re.subn(r'(?<![\d.])'+re.escape(val)+r'(?![\d.])',grouped(val),after)
        assert n>0,(i,val)
    assert plain(before)==plain(after)
    rewrite(ps[i],after)
    edits.append({'type':'number_grouping','paragraph':i,'before':before,'after':after})

for i in range(134,200):
    p=ps[i];before=pt(p);after=re.sub(r'^(\[\d+\]) +',r'\1',before)
    # Authors are separated from the title by the first period-space boundary.
    m=re.match(r'^(\[\d+\])(.+?)\. +(.+)$',after)
    if m:
        after=m[1]+re.sub(r', +',',',m[2])+'.'+m[3]
    marker=re.search(r'\[(?:J|M|C|EB/OL|Z)\]',after)
    assert marker
    prefix,suffix=after[:marker.end()],after[marker.end():]
    ref=i-133
    if ref==31:
        suffix=suffix.replace('GREENWOOD R, OLIVER C, SAHLIN K, et al. ', 'GREENWOOD R,OLIVER C,SAHLIN K,et al.')
        suffix=suffix.replace('Institutionalism. London: SAGE, 2008: 99-129.', 'Institutionalism.London:SAGE,2008:99-129.')
    elif ref==44:
        suffix=suffix.replace('Papers). Beijing: Association for Computational Linguistics, 2015:438–444. DOI:', 'Papers).Beijing:Association for Computational Linguistics,2015:438–444.DOI:')
    else:
        suffix=re.sub(r'(?<=[.,:;\]]) +','',suffix)
    after=prefix+suffix
    assert plain(before)==plain(after)
    if after!=before:
        rewrite(p,after);edits.append({'type':'reference_structural_spaces','paragraph':i,'reference':ref,'before':before,'after':after})
    pp=child(p,'pPr');ind=child(pp,'ind')
    ind.attrib.clear()
    for key,val in [('left','420'),('right','0'),('hanging','420')]: ind.set(tag(key),val)
    # No tabs or manual newlines: every continuation inherits the same hanging indent.
    assert not p.xpath('.//w:br|.//w:tab',namespaces=NS)
refstyle=styles.xpath('//w:style[@w:styleId="63"]',namespaces=NS)[0]
for n in ['sz','szCs']:child(child(refstyle,'rPr'),n).set(tag('val'),'21')

new_ps=[pt(p) for p in ps]
assert all(plain(a)==plain(b) for a,b in zip(old_ps,new_ps))
newparts=dict(parts)
newparts['word/document.xml']=E.tostring(doc,xml_declaration=True,encoding='UTF-8',standalone=True)
newparts['word/styles.xml']=E.tostring(styles,xml_declaration=True,encoding='UTF-8',standalone=True)
with ZipFile(DST,'w') as z:
    for info in infos:z.writestr(info,newparts[info.filename])

oldroot=E.fromstring(parts['word/document.xml'])
def all_text(d):return ''.join(d.xpath('//w:t/text()',namespaces=NS))
def cites(d):return [pt(r) for r in d.xpath('//w:body/w:p/w:r[w:rPr/w:vertAlign[@w:val="superscript"]]',namespaces=NS) if re.search(r'\[\d',pt(r))]
validation={
 'status':'format_corrected_methods_pending', 'source':str(SRC),'output':str(DST),
 'source_sha256':sha(SRC.read_bytes()),'output_sha256':sha(DST.read_bytes()),
 'body_paragraphs':len(ps),'reference_count':66,'tables':len(doc.xpath('//w:tbl',namespaces=NS)),
 'full_text_equal_ignoring_whitespace':plain(all_text(oldroot))==plain(all_text(doc)),
 'digit_sequence_equal':re.findall(r'\d',all_text(oldroot))==re.findall(r'\d',all_text(doc)),
 'numeric_tokens_equal_after_removing_group_spaces':re.findall(r'\d+(?:\.\d+)?',all_text(oldroot))==re.findall(r'\d+(?:\.\d+)?',all_text(doc).replace(sep,'')),
 'all_citation_runs_unchanged':cites(oldroot)==cites(doc),'citation_run_count':len(cites(doc)),
 'reference_nonwhitespace_text_unchanged':all(plain(a)==plain(b) for a,b in zip(old_ps[134:],new_ps[134:])),
 'authors_and_affiliations_unchanged':all(old_ps[i]==new_ps[i] for i in [1,2,3,4,9,10,11,12]),
 'table_xml_unchanged':all(E.tostring(a)==E.tostring(b) for a,b in zip(oldroot.xpath('//w:tbl',namespaces=NS),doc.xpath('//w:tbl',namespaces=NS))),
 'drawings_unchanged':all(E.tostring(a)==E.tostring(b) for a,b in zip(oldroot.xpath('//w:drawing',namespaces=NS),doc.xpath('//w:drawing',namespaces=NS))),
 'package_parts_changed':[n for n in parts if parts[n]!=newparts[n]],
 'footnotes_unchanged':parts.get('word/footnotes.xml')==newparts.get('word/footnotes.xml'),
 'secondary_heading_indices':headings,'number_grouping_paragraphs':list(number_map),
 'number_group_separator':'U+202F NARROW NO-BREAK SPACE',
 'reference_direct_indents':{'left_twips':420,'hanging_twips':420,'right_twips':0},
 'changes':edits,
}
for key,value in validation.items():
    if key.endswith('unchanged') or key.endswith('_equal') or key=='full_text_equal_ignoring_whitespace': assert value,key
(OUT/'_work/format-change-validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in validation.items() if k!='changes'},ensure_ascii=False,indent=2))
