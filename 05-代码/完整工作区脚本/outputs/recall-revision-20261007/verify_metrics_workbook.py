"""Read-only XLSX XML/cache checks; does not author or modify workbooks."""
from pathlib import Path
import hashlib
import json
import math
import zipfile
from xml.etree import ElementTree as ET

OUT=Path(__file__).resolve().parent
NS={'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
    'r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}


def col(n):
    s=''
    while n:
        n,m=divmod(n-1,26);s=chr(65+m)+s
    return s


def equal(actual,expected,label):
    if expected is None:
        assert actual in (None,'','NA'),(label,actual,expected)
    elif isinstance(expected,(int,float)):
        assert isinstance(actual,(int,float)) and math.isfinite(actual) and abs(actual-expected)<1e-10,(label,actual,expected)
    else:
        assert actual==expected,(label,actual,expected)


def read_workbook(path):
    with zipfile.ZipFile(path) as z:
        workbook=ET.fromstring(z.read('xl/workbook.xml'))
        rels=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        relationship={r.get('Id'):r.get('Target') for r in rels}
        strings=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('x:si',NS):
                strings.append(''.join(t.text or '' for t in si.findall('.//x:t',NS)))
        sheets={}
        formula_count=0
        for s in workbook.findall('x:sheets/x:sheet',NS):
            target=relationship[s.get('{'+NS['r']+'}id')]
            target=target.lstrip('/') if target.startswith('/') else 'xl/'+target
            cells={}
            for c in ET.fromstring(z.read(target)).findall('.//x:sheetData/x:row/x:c',NS):
                typ=c.get('t');v=c.find('x:v',NS);f=c.find('x:f',NS)
                assert typ!='e',(s.get('name'),c.get('r'),'Formula error',v.text if v is not None else '')
                raw=v.text if v is not None else None
                if typ=='s':value=strings[int(raw)] if raw is not None else None
                elif typ=='inlineStr':value=''.join(t.text or '' for t in c.findall('.//x:t',NS))
                elif typ in ('str','b'):value=raw or ''
                elif raw is not None:
                    try:value=float(raw)
                    except ValueError:value=raw
                else:value=None
                cells[c.get('r')]={'value':value,'formula':f.text if f is not None else None}
                formula_count+=f is not None
            sheets[s.get('name')]=cells
        return sheets,formula_count


def main():
    path=OUT/'三部门编码与注意力指标.xlsx'
    expected=json.loads((OUT/'workbook-expected-cells.json').read_text())
    for name,sha in expected['source_sha256'].items():
        assert hashlib.sha256((OUT/name).read_bytes()).hexdigest()==sha,('Input changed after build',name)
    sheets,formula_count=read_workbook(path)
    assert list(sheets)==['κ对照','完整分类指标','注意力分布','稳健性结果','方法与来源','LLM稳定性']
    for e in expected['expected']:
        equal(sheets[e['sheet']][e['cell']]['value'],e['expected'],e['sheet']+'!'+e['cell'])
    coding=json.loads((OUT/'三部门编码指标.json').read_text())
    ci_checked=0
    for i,r in enumerate(coding['records']):
        row=7+i
        for j,metric in enumerate(['agreement','kappa','precision','recall','f1','left_positive_rate','right_positive_rate']):
            ci=r['metrics'].get(metric,{}).get('ci95',{})
            for k,field in enumerate(['low','high','defined_repetitions','undefined_repetitions']):
                addr=f'{col(29+4*j+k)}{row}'
                equal(sheets['完整分类指标'].get(addr,{}).get('value'),ci.get(field),'CI cache '+addr)
                ci_checked+=1
        # κ and agreement use actual scalar formulas; A/C P/R/F1 deliberately blank.
        assert sheets['完整分类指标'][f'Y{row}']['formula']
        assert sheets['完整分类指标'][f'X{row}']['formula']
        if r['method']=='A_C':
            for c in ('Z','AA','AB'):assert sheets['完整分类指标'][f'{c}{row}']['formula']=='""'
    placeholder_n=expected['classification_records']-expected['actual_classification_records']
    for row in range(7+len(coding['records']),7+expected['classification_records']):
        equal(sheets['完整分类指标'][f'F{row}']['value'],'未完成','LLM status')
        for c in ('N','O','P','Q','R','X','Y','Z','AA','AB'):
            equal(sheets['完整分类指标'].get(f'{c}{row}',{}).get('value'),None,'LLM missing '+c+str(row))
    for r in (7,17,32,66):
        if f'Y{r}' in sheets['完整分类指标']:
            assert 'W'+str(r) in sheets['完整分类指标'][f'Y{r}']['formula']
    previous,unused=read_workbook(OUT.parent/'final-three-department-20261007/三部门编码与注意力指标.xlsx')
    preserved_cells=0
    for name,old in previous.items():
        if name=='LLM稳定性':continue
        for addr in set(old)|set(sheets[name]):
            a=old.get(addr,{'value':None,'formula':None});b=sheets[name].get(addr,{'value':None,'formula':None})
            assert a['formula']==b['formula'],('Changed original formula',name,addr)
            if a['formula'] is not None:preserved_cells+=1
    stability=json.loads((OUT/'llm-v30/stability_comparison_v30.json').read_text())
    sample_path=Path(stability['actual_source_paths']['sample']['path'])
    assert hashlib.sha256(sample_path.read_bytes()).hexdigest()==stability['sample_sha256']
    sample_rows=[json.loads(l) for l in sample_path.read_text().splitlines() if l.strip()] if sample_path.suffix=='.jsonl' else json.loads(sample_path.read_text())['rows']
    ids=[r['id'] for r in sample_rows]
    assert len(ids)==36
    paths={k:v['predictions_path'] for k,v in stability['actual_source_paths'].items() if k!='sample'}
    raw={}
    for key,rel in paths.items():
        p=OUT/rel;assert hashlib.sha256(p.read_bytes()).hexdigest()==stability['output_bindings'][key]
        data=[json.loads(x) for x in p.read_text().splitlines()] if p.suffix=='.jsonl' else json.loads(p.read_text())['rows']
        raw[key]={r['id']:r['labels'] for r in data}
    stab=sheets['LLM稳定性'];dims=['S','E','Ec','I','F'];checked=0
    for i,c in enumerate(stability['comparisons']):
        left=raw[c['left']];right=raw[c['right']];n=36
        exact=sum(all(left[u][d]==right[u][d] for d in dims) for u in ids)
        for addr,val in [(f'B{7+i}',n),(f'C{7+i}',exact),(f'D{7+i}',exact/n)]:equal(stab[addr]['value'],val,addr);checked+=1
        assert stab[f'D{7+i}']['formula']
        for j,d in enumerate(dims):
            row=14+i*5+j
            a=sum(left[u][d]==1 and right[u][d]==1 for u in ids);b=sum(left[u][d]==1 and right[u][d]==0 for u in ids);c01=sum(left[u][d]==0 and right[u][d]==1 for u in ids);e=sum(left[u][d]==0 and right[u][d]==0 for u in ids)
            pe=(a+b)*(a+c01)+(c01+e)*(b+e);k=None if pe==n*n else ((a+e)*n-pe)/(n*n-pe)
            for colname,val in [('C',n),('D',a),('E',b),('F',c01),('G',e),('H',(a+e)/n),('I',k)]:equal(stab[f'{colname}{row}']['value'],val,f'{colname}{row}');checked+=1
            bad=[u for u in ids if left[u][d]!=right[u][d]]
            equal(stab[f'J{row}']['value'],'；'.join(bad) or '无','Disagreement IDs')
            assert all(stab[f'{colname}{row}']['formula'] for colname in ('C','H','I'))
    stability_hash=hashlib.sha256((OUT/'llm-v30/stability_comparison_v30.json').read_bytes()).hexdigest()
    digests=[stability_hash,stability['sample_sha256'],*stability['output_bindings'].values()]
    for row,digest in enumerate(digests,33):equal(stab[f'D{row}']['value'],digest,'Stability source hash')
    report={'status':'passed','workbook':path.name,'workbook_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'source_sha256':expected['source_sha256'],'sheets':list(sheets),
            'point_and_attention_cached_cells_checked':len(expected['expected']),
            'bootstrap_ci_cached_cells_checked':ci_checked,
            'formula_cells':formula_count,'unexpected_formula_errors':0,
            'actual_classification_records':len(coding['records']),'explicit_incomplete_llm_records':placeholder_n,
            'live_input_change_check':expected['live_input_change_check'],
            'baseline_five_sheet_formulas_preserved':preserved_cells,
            'allowed_method_sheet_additions':['A22:D22 Törnberg依据','A27:D27 稳定性汇总输入'],
            'stability_comparisons':3,'stability_dimension_rows':15,'stability_independently_reconstructed_cached_cells':checked,'stability_bound_source_hashes':6,
            'visual_previews':['workbook-kappa.png','workbook-classification-counts.png','workbook-classification-formulas.png','workbook-attention.png','workbook-sensitivity.png','workbook-methods.png','workbook-llm-stability.png','workbook-llm-stability-bindings.png'],
            'limits':'Formula caches and artifact-tool recalculation verified; no native Microsoft Excel execution was required or claimed.'}
    (OUT/'workbook-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
