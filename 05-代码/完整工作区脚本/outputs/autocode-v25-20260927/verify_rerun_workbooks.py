"""Read exported OOXML independently; no spreadsheet files are authored here."""
from pathlib import Path
import hashlib
import json
import zipfile
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
DEST=HERE.parent/'01a0dbb7-43f0-7a61-a367-7f0c814ee9d4/两方法重跑-20260927'
NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
    'r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}

def read_sheets(path):
    result={}
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        shared=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            root=ET.fromstring(z.read('xl/sharedStrings.xml'))
            shared=[''.join(si.itertext()) for si in root]
        rels=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        links={r.attrib['Id']:r.attrib['Target'] for r in rels}
        book=ET.fromstring(z.read('xl/workbook.xml'))
        for sheet in book.find('s:sheets',NS):
            target=links[sheet.attrib['{'+NS['r']+'}id']]
            target=target.lstrip('/') if target.startswith('/') else 'xl/'+target
            tree=ET.fromstring(z.read(target));cells={};formulas={}
            for c in tree.findall('.//s:sheetData/s:row/s:c',NS):
                key=c.attrib['r'];kind=c.attrib.get('t');v=c.find('s:v',NS)
                if kind=='s':value=shared[int(v.text)]
                elif kind=='inlineStr':value=''.join(c.find('s:is',NS).itertext())
                elif v is None:value=None
                elif kind in ('str','e'):value=v.text
                elif kind=='b':value=bool(int(v.text))
                else:value=float(v.text) if v.text is not None else None
                assert kind!='e',(path.name,sheet.attrib['name'],key,value)
                cells[key]=value
                f=c.find('s:f',NS)
                if f is not None:formulas[key]=f.text
            result[sheet.attrib['name']]={'cells':cells,'formulas':formulas}
    return result

def col(n):
    answer='';n+=1
    while n:
        n,r=divmod(n-1,26);answer=chr(65+r)+answer
    return answer

def compare_rows(cells,expected,start=1):
    for i,row in enumerate(expected,start):
        for j,value in enumerate(row):
            got=cells.get(col(j)+str(i))
            # The authoring layer prefixes an apostrophe only for formula-like
            # source strings. Excel may store that prefix or its quote flag.
            allowed=(value,"'"+value) if isinstance(value,str) and value.startswith('=') else (value,)
            if value=='':allowed=('',None)
            assert got in allowed,(i,j,'exported value does not match delivery payload')

def main():
    payload=json.loads((HERE/'rerun_delivery_payload.json').read_text())
    results=[]
    for book in payload['reference_books']:
        p=DEST/book['filename'];sheets=read_sheets(p)
        assert set(sheets)==({'编码记录','共用规范','长文本逐行'} if book['long_text_rows'] else {'编码记录','共用规范'})
        compare_rows(sheets['编码记录']['cells'],[book['header'],*book['rows']])
        assert len(book['rows'])==1695
        compare_rows(sheets['共用规范']['cells'],[book['manual_header'],[0,book['notice']],*book['manual_rows']])
        if book['long_text_rows']:compare_rows(sheets['长文本逐行']['cells'],[book['long_text_header'],*book['long_text_rows']])
        results.append({'file':p.name,'rows_checked':1695,'full_cells_match':True,
            'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    comp=payload['comparison_book'];p=DEST/comp['filename'];sheets=read_sheets(p)
    for s in comp['summaries']:
        cells=sheets[s['name']]['cells'];formulas=sheets[s['name']]['formulas']
        assert len(formulas)==90,(s['name'],'summary formula count')
        for i,row in enumerate(s['rows'],6):
            tp,fp,fn=row[11:14]
            denominators=(tp+fp,tp+fn,2*tp+fp+fn)
            numerators=(tp,tp,2*tp)
            for column,a,b in zip('DEF',numerators,denominators):
                got=cells.get(column+str(i))
                if b:assert isinstance(got,(int,float)) and abs(got-a/b)<1e-10
                else:assert got=='n.a.'
            for j in [0,1,2,6,7,8,9,11,12,13,14]:assert cells.get(col(j)+str(i))==row[j]
    for sheet,headers,rows in [('逐条对照',comp['detail_header'],comp['detail_rows']),
        ('LLM全量',comp['llm_header'],comp['llm_rows']),
        ('LLM证据',comp['evidence_header'],comp['evidence_rows']),
        ('方法说明',['序号','说明'],[[i+1,x] for i,x in enumerate(comp['method_notes'])])]:
        compare_rows(sheets[sheet]['cells'],[headers,*rows])
    results.append({'file':p.name,'LLM_rows_checked':4924,'comparison_rows_checked':1695,
        'cached_formulas_checked':180,'full_cells_match':True,
        'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    if comp['long_text_rows']:compare_rows(sheets['长文本逐行']['cells'],[comp['long_text_header'],*comp['long_text_rows']])
    out=HERE/'workbook_independent_verification.json';assert not out.exists()
    out.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(results,ensure_ascii=False))

if __name__=='__main__':main()
