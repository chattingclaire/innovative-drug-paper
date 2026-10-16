"""Read-only OOXML audit; writes JSON observations, never edits DOCX."""
from pathlib import Path
from zipfile import ZipFile
from collections import Counter
import json,re,hashlib
from lxml import etree as E

BASE=Path(__file__).resolve().parents[1]
SOURCE=BASE/'创新药评价的注意力配置差异与协调路径-交稿版-表述修订.docx'
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS={'w':W}
def attrs(e):return {} if e is None else {E.QName(k).localname:v for k,v in e.attrib.items()}
def prop(e):
    if e is None:return {}
    return {E.QName(c).localname:attrs(c) for c in e}
def txt(e):return ''.join(e.xpath('.//w:t/text()',namespaces=NS))
def merge(a,b):
    out={k:dict(v) for k,v in a.items()}
    for k,v in b.items():out.setdefault(k,{}).update(v)
    return out
def val(e,k):return e.get('{'+W+'}'+k) if e is not None else None

with ZipFile(SOURCE) as z:
    doc=E.fromstring(z.read('word/document.xml'))
    styles=E.fromstring(z.read('word/styles.xml'))
    sd={val(x,'styleId'):x for x in styles.findall('w:style',NS)}
    dr=prop(styles.find('w:docDefaults/w:rPrDefault/w:rPr',NS))
    dp=prop(styles.find('w:docDefaults/w:pPrDefault/w:pPr',NS))
    def style(sid,kind,seen=None):
        if sid not in sd:return {}
        seen=set() if seen is None else seen
        if sid in seen:return {}
        seen.add(sid);s=sd[sid]
        return merge(style(val(s.find('w:basedOn',NS),'val'),kind,seen),prop(s.find('w:'+kind,NS)))
    paras=[];fontcounts=Counter();sizecounts=Counter();colors=Counter();badcites=[];allcites=[]
    in_refs=False
    for i,p in enumerate(doc.xpath('.//w:body/w:p',namespaces=NS),1):
        t=txt(p);sid=val(p.find('w:pPr/w:pStyle',NS),'val') or 'Normal'
        if t.strip()=='参考文献':in_refs=True
        pp=merge(merge(dp,style(sid,'pPr')),prop(p.find('w:pPr',NS)))
        runs=[];offset=0
        for r in p.findall('.//w:r',NS):
            rt=txt(r)
            if not rt:continue
            rid=val(r.find('w:rPr/w:rStyle',NS),'val')
            rp=merge(merge(merge(dr,style(sid,'rPr')),style(rid,'rPr')),prop(r.find('w:rPr',NS)))
            rec={'text':rt,'start':offset,'end':offset+len(rt),'effective':rp,'direct':prop(r.find('w:rPr',NS))}
            offset+=len(rt);runs.append(rec)
            fontcounts[json.dumps(rp.get('rFonts',{}),ensure_ascii=False,sort_keys=True)]+=len(rt)
            sizecounts[rp.get('sz',{}).get('val','unset')]+=len(rt)
            colors[json.dumps(rp.get('color',{}),sort_keys=True)]+=len(rt)
        if not in_refs:
            for m in re.finditer(r'\[[0-9]+(?:[—–,，\-][0-9]+)*\]',t):
                affected=[r for r in runs if r['start']<m.end() and r['end']>m.start()]
                ok=all(r['effective'].get('vertAlign',{}).get('val')=='superscript' for r in affected)
                rec={'paragraph':i,'text':m.group(),'superscript':ok,'nearby':t[max(0,m.start()-15):m.end()+15]}
                allcites.append(rec)
                if not ok:badcites.append(rec)
        paras.append({'p':i,'style':sid,'text':t,'pPr':pp,'direct_pPr':prop(p.find('w:pPr',NS)),'runs':runs})
    tables=[]
    for ti,t in enumerate(doc.xpath('.//w:body/w:tbl',namespaces=NS),1):
        tpr=t.find('w:tblPr',NS);trs=t.findall('w:tr',NS)
        rows=[]
        for ri,tr in enumerate(trs,1):
            cells=[]
            for ci,tc in enumerate(tr.findall('w:tc',NS),1):
                fonts=Counter();sizes=Counter();borders=[]
                for r in tc.findall('.//w:r',NS):
                    if txt(r):
                        p=r.getparent()
                        while p is not None and p.tag!='{'+W+'}p':p=p.getparent()
                        sid=val(p.find('w:pPr/w:pStyle',NS),'val') or 'Normal'
                        rp=merge(merge(dr,style(sid,'rPr')),prop(r.find('w:rPr',NS)))
                        fonts[json.dumps(rp.get('rFonts',{}),ensure_ascii=False,sort_keys=True)]+=len(txt(r))
                        sizes[rp.get('sz',{}).get('val','unset')]+=len(txt(r))
                bp=tc.find('w:tcPr/w:tcBorders',NS)
                borders={} if bp is None else {E.QName(c).localname:attrs(c) for c in bp}
                cells.append({'column':ci,'text':txt(tc),'fonts':dict(fonts),'sizes':dict(sizes),'borders':borders,'tcPr':prop(tc.find('w:tcPr',NS))})
            rows.append({'row':ri,'trPr':prop(tr.find('w:trPr',NS)),'cells':cells})
        bp=tpr.find('w:tblBorders',NS) if tpr is not None else None
        tables.append({'table':ti,'rows_N':len(trs),'tblPr':prop(tpr),'borders':{} if bp is None else {E.QName(c).localname:attrs(c) for c in bp},'rows':rows})
    section=[prop(s) for s in doc.findall('.//w:sectPr',NS)]
    authors=[]
    for name in z.namelist():
        if name.endswith('.xml') and name.startswith(('word/footnotes','word/endnotes','word/header','word/footer','docProps/')):
            x=E.fromstring(z.read(name));authors.append({'part':name,'text':txt(x),'xml':E.tostring(x,encoding='unicode')[:10000]})
    report={'source':str(SOURCE),'sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
      'paragraph_count':len(paras),'table_count':len(tables),'defaults':{'rPr':dr,'pPr':dp},
      'body_char_fonts':dict(fontcounts),'body_char_sizes_halfpoints':dict(sizecounts),'body_char_colors':dict(colors),
      'paragraphs':paras,'tables':tables,'sections':section,'citations':allcites,'bad_citations':badcites,'ancillary_parts':authors,
      'used_styles':{s:E.tostring(sd[s],encoding='unicode') for s in {p['style'] for p in paras} if s in sd}}
(BASE/'_work/format-author-audit-evidence.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('paragraphs','tables','used_styles','ancillary_parts','citations')},ensure_ascii=False,indent=2))
print('PARAGRAPHS')
for p in paras:
    if len(p['text'])<100 or p['p']<8 or p['text'].startswith('['):
        print(p['p'],p['style'],p['text'][:65],p['pPr'],[(r['text'][:20],r['effective']) for r in p['runs'][:2]])
