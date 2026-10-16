"""Local OOXML revision; never relabel agent observations as human data."""
from pathlib import Path
from zipfile import ZipFile
from copy import deepcopy
from lxml import etree as E
import re, json, hashlib

OUT=Path(__file__).resolve().parent
BASE=OUT.parent/'final-three-department-20261008-adopted-results'
MAIN=BASE/'论文修订稿-三部门实测结果版.docx'
MEMO=BASE/'校核与待确认事项.docx'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
def W(s):return '{'+NS['w']+'}'+s
def plain(x):return ''.join(x.xpath('.//w:t/text()',namespaces=NS)).replace('\u2060','')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def replace(p,text,citations=True):
    pr=p.find('w:pPr',NS); rp=None
    for r in p.findall('w:r',NS):
        q=r.find('w:rPr',NS)
        if q is not None and q.find('w:vertAlign',NS) is None:rp=deepcopy(q);break
    for c in list(p):
        if c is not pr:p.remove(c)
    chunks=re.split(r'(\[\d+(?:[,–—-]\d+)*\])',text) if citations else [text]
    for chunk in chunks:
        if not chunk:continue
        r=E.SubElement(p,W('r'))
        if rp is not None:r.append(deepcopy(rp))
        is_cite=citations and bool(re.fullmatch(r'\[\d+(?:[,–—-]\d+)*\]',chunk))
        if is_cite:
            q=r.find('w:rPr',NS)
            if q is None:q=E.SubElement(r,W('rPr'))
            for old in q.findall('w:vertAlign',NS):q.remove(old)
            E.SubElement(q,W('vertAlign')).set(W('val'),'superscript')
        for j,line in enumerate(chunk.split('\n')):
            if j:E.SubElement(r,W('br'))
            t=E.SubElement(r,W('t'));t.set('{http://www.w3.org/XML/1998/namespace}space','preserve')
            t.text=('\u2060' if is_cite else '')+line
def cellset(c,text):
    ps=c.findall('w:p',NS)
    replace(ps[0],str(text),False)
    for p in ps[1:]:c.remove(p)
def load_doc(p):
    with ZipFile(p) as z:parts={i.filename:z.read(i.filename) for i in z.infolist()}
    return parts,E.fromstring(parts['word/document.xml'])
def save_doc(src,dst,parts,root):
    parts['word/document.xml']=E.tostring(root,encoding='UTF-8',xml_declaration=True,standalone=True)
    with ZipFile(src) as z,ZipFile(dst,'w') as out:
        for i in z.infolist():out.writestr(i,parts[i.filename])
def cite_ids(s):
    out=[]
    for seg in s[1:-1].split(','):
        ends=re.split('[–—-]',seg);out.extend(range(int(ends[0]),int(ends[-1])+1))
    return out
def main():
    assert sha(MAIN)=='dd23f6e6e426d0a914eb206fb85ee152bdb0400700e769d8c28390efecb7226f'
    assert sha(MEMO)=='c73c4c9ef4e9f80421d2650609e1c5fb6d030403ac9a576ac0e2105276578a57'
    payload=json.loads((OUT/'revision_payload.json').read_text())
    parts,r=load_doc(MAIN);body=r.find('w:body',NS);ps=body.findall('w:p',NS)
    original=[plain(p) for p in ps]
    assert len(ps)==172
    tables=body.findall('w:tbl',NS)
    assert len(tables)==4
    kept_tables={str(i):E.tostring(tables[i]) for i in [0,2,3]}
    refs={int(re.match(r'\[(\d+)\]',plain(p))[1]):plain(p) for p in ps[111:]}
    for key,value in payload['new_references'].items():refs[int(key)]='['+str(key)+'] '+value
    for key,value in payload.get('replace_references',{}).items():refs[int(key)]='['+str(key)+'] '+value
    changed=[]
    for i,text in payload['paragraph_updates'].items():
        i=int(i);replace(ps[i],text);changed.append(i)
    # A visible theory location defines the variables before the methods/results.
    heading=deepcopy(ps[28]);replace(heading,'3.3 变量与指标定义')
    body.insert(body.index(ps[37]),heading)
    for extra in payload['definition_extra_paragraphs']:
        p=deepcopy(ps[37]);replace(p,extra);body.insert(body.index(ps[37])+1,p)
    # Only method names change in existing numerical tables. No observations change.
    for table in tables:
        for c in table.findall('.//w:tc',NS):
            t=plain(c)
            if t=='规则':cellset(c,'自动规则编码')
            elif t=='LLM':cellset(c,'LLM编码')
    # Table 2 is reserved for actual human results, not for old proxy metrics.
    pending=tables[1].findall('w:tr',NS)
    assert len(pending)==11
    for row in pending[1:]:
        cells=row.findall('w:tc',NS)
        for c in cells[2:]:cellset(c,'待填/待填')
    for c,text in zip(pending[0].findall('w:tc',NS),['维度','编码方法','κ（A/C）','P（A/C）','R（A/C）','F1（A/C）']):cellset(c,text)
    # Full canonical method names need enough room to remain intact. Preserve
    # total table widths and numerical content; do not shrink the existing font.
    for table,widths in [(tables[1],[1000,1700,1900,1800,1800,1800]),
                         (tables[2],[1000,1700,1440,1440,1440,1440,1440])]:
        for col,width in zip(table.find('w:tblGrid',NS),widths):col.set(W('w'),str(width))
        for row in table.findall('w:tr',NS):
            for cell,width in zip(row.findall('w:tc',NS),widths):
                cell.find('w:tcPr/w:tcW',NS).set(W('w'),str(width))
    # Renumber by actual first appearance, including newly checked official sources.
    for p in ps[111:]:body.remove(p)
    mapping={};order=[]
    for p in body.iter(W('p')):
        for match in re.finditer(r'\[\d+(?:[,–—-]\d+)*\]',plain(p)):
            for old in cite_ids(match[0]):
                assert old in refs,old
                if old not in mapping:mapping[old]=len(mapping)+1;order.append(old)
    # Keep inherited references only when cited; no orphan citations or phantom works.
    for p in list(body.iter(W('p'))):
        t=plain(p)
        def sub(m):return '['+','.join(str(mapping[x]) for x in sorted(cite_ids(m[0]),key=lambda n:mapping[n]))+']'
        nt=re.sub(r'\[\d+(?:[,–—-]\d+)*\]',sub,t)
        if nt!=t:replace(p,nt)
    template=ps[111]
    sect=body.find('w:sectPr',NS)
    for old in order:
        p=deepcopy(template)
        replace(p,re.sub(r'^\[\d+\]','['+str(mapping[old])+']',refs[old]),False)
        body.insert(body.index(sect),p)
    dst=OUT/'论文修订稿-人工复核待填版.docx'
    save_doc(MAIN,dst,parts,r)
    # Separate implementation memo, using the existing document's actual components.
    mparts,mr=load_doc(MEMO);mb=mr.find('w:body',NS);mps=mb.findall('w:p',NS)
    components={'title':deepcopy(mps[0]),'heading':deepcopy(mps[2]),'body':deepcopy(mps[1])}
    msect=mb.find('w:sectPr',NS)
    for child in list(mb):
        if child is not msect:mb.remove(child)
    for item in payload['memo_blocks']:
        if item['kind']=='kappa_table':
            # Existing journal table provides readable sizing, then use the memo's
            # explicit gray grid and light header for this implementation matrix.
            t=deepcopy(tables[1]);rows=t.findall('w:tr',NS);row_template=deepcopy(rows[1]);head_template=deepcopy(rows[0])
            for row in rows:t.remove(row)
            values=payload['old_proxy_kappa_table']
            widths=[1100,1120,1900,1900,1800,1800]
            grid=t.find('w:tblGrid',NS)
            for c in list(grid):grid.remove(c)
            for width in widths:E.SubElement(grid,W('gridCol')).set(W('w'),str(width))
            for ri,vals in enumerate(values):
                row=deepcopy(head_template if ri==0 else row_template)
                for ci,(c,value) in enumerate(zip(row.findall('w:tc',NS),vals)):
                    cellset(c,value);cp=c.find('w:tcPr',NS)
                    cw=cp.find('w:tcW',NS);cw.set(W('w'),str(widths[ci]))
                    for old in cp.findall('w:tcBorders',NS)+cp.findall('w:shd',NS):cp.remove(old)
                    borders=E.SubElement(cp,W('tcBorders'))
                    for edge in ['top','bottom','left','right']:
                        q=E.SubElement(borders,W(edge));q.set(W('val'),'single');q.set(W('sz'),'4');q.set(W('color'),'D9D9D9')
                    if ri==0:E.SubElement(cp,W('shd')).set(W('fill'),'E7E6E6')
                t.append(row)
            mb.insert(mb.index(msect),t)
        else:
            p=deepcopy(components[item['kind']]);replace(p,item['text'],False)
            mb.insert(mb.index(msect),p)
    mdst=OUT/'真人复核实施与待补事项.docx';save_doc(MEMO,mdst,mparts,mr)
    # Authoring audit records scope, not a claim of human/statistical validation.
    report={'status':'AUTHORED_PENDING_FRESH_RENDER_AND_REVIEW','main':str(dst),'main_sha256':sha(dst),
            'memo':str(mdst),'memo_sha256':sha(mdst),'source_main_sha256':sha(MAIN),'source_memo_sha256':sha(MEMO),
            'changed_source_paragraph_indices':sorted(changed),'references_count':len(order),
            'old_to_new_reference_numbers':mapping,'human_metrics_state':'PENDING_ACTUAL_LABELS',
            'actual_machine_numeric_tables_state':'PRESERVED','comparison_frames':'full4481 vs future240; not old180 as human'}
    (OUT/'authoring_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
