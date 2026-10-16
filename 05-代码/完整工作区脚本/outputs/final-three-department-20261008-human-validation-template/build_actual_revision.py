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
    payload=json.loads((OUT/'revision_payload_actual.json').read_text())
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
    # Actual sentence evidence complements the aggregate distributions.
    for text in reversed(payload.get('method_difference_paragraphs',[])):
        p=deepcopy(ps[69]);replace(p,text);body.insert(body.index(ps[69])+1,p)
    # Only method names change in existing numerical tables. No observations change.
    for table in tables:
        for c in table.findall('.//w:tc',NS):
            t=plain(c)
            if t=='规则':cellset(c,'自动规则编码')
            elif t=='LLM':cellset(c,'LLM编码')
    # Fill all eighty review metrics from the independently verified actual180.
    actual_rows=payload['actual_table2_rows']
    review_rows=tables[1].findall('w:tr',NS)
    assert len(review_rows)==len(actual_rows)==11
    for row,values in zip(review_rows,actual_rows):
        for c,value in zip(row.findall('w:tc',NS),values):
            value={'规则':'自动规则编码','LLM':'LLM编码','方法':'编码方法'}.get(value,value)
            cellset(c,value)
    # Full canonical method names need enough room to remain intact. Preserve
    # total table widths and numerical content; do not shrink the existing font.
    for table,widths in [(tables[1],[1000,1700,1900,1800,1800,1800]),
                         (tables[2],[1000,1700,1440,1440,1440,1440,1440])]:
        for col,width in zip(table.find('w:tblGrid',NS),widths):col.set(W('w'),str(width))
        for row in table.findall('w:tr',NS):
            for cell,width in zip(row.findall('w:tc',NS),widths):
                cell.find('w:tcPr/w:tcW',NS).set(W('w'),str(width))
    # Remove the inherited forced page break that left most of a page blank
    # before Table 3 in the freshly rendered, longer review section.
    for paragraph in body.findall('w:p',NS):
        if plain(paragraph).startswith('表3 全语料'):
            pr=paragraph.find('w:pPr',NS)
            for br in pr.findall('w:pageBreakBefore',NS):pr.remove(br)
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
    dst=OUT/'论文修订稿-编码实算结果版.docx'
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
    mdst=OUT/'编码复核说明与真人检验事项.docx';save_doc(MEMO,mdst,mparts,mr)
    # Authoring audit records scope, not a claim of human/statistical validation.
    report={'status':'AUTHORED_PENDING_FRESH_RENDER_AND_REVIEW','main':str(dst),'main_sha256':sha(dst),
            'memo':str(mdst),'memo_sha256':sha(mdst),'source_main_sha256':sha(MAIN),'source_memo_sha256':sha(MEMO),
            'changed_source_paragraph_indices':sorted(changed),'references_count':len(order),
            'old_to_new_reference_numbers':mapping,'human_metrics_state':'PENDING_ACTUAL_LABELS',
            'actual_machine_numeric_tables_state':'PRESERVED','proxy_review_values_state':'ALL80_PLUS_FIVE_KAPPA_FILLED','table2_binding':payload['actual_table2_binding'],'comparison_frames':'full4481 and actual proxy180; future human240 memo only'}
    (OUT/'authoring_audit_actual.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
