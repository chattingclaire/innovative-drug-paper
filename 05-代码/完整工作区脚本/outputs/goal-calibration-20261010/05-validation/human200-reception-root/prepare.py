"""Bind the existing XLSX parser and prepare the actual200 sampling metadata."""
import ast
import hashlib
import importlib.util
import json
import zipfile
from collections import Counter
from fractions import Fraction
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
DELIVERY=ROOT/'09-delivery/human200-independent-preparation-root'
OLD=ROOT/'05-validation/formal800-xlsx-lawful-null-reception-supplement-sol'
BRIDGE=ROOT/'07-statistics/formal800-v15-statistics-input-bridge-sol/bridge.py'
ENGINE=ROOT/'07-statistics/prospective-engine-domain-sol/metrics_engine.py'


def binding(p):
    raw=p.read_bytes()
    return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def write(p,d):
    with p.open('x') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')


def extract(p,names):
    text=p.read_text()
    tree=ast.parse(text)
    functions={n.name:ast.get_source_segment(text,n) for n in tree.body if isinstance(n,ast.FunctionDef)}
    return {name:functions[name] for name in names}


def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def main():
    old_bind=json.loads((OLD/'bindings.json').read_text())
    dependencies=old_bind['dependencies']
    for entry in dependencies.values():
        if binding(Path(entry['path']))!=entry:raise ValueError('Existing helper binding changed')
    helper_names=['text_value','read_xlsx','cell','blank','comparable','_normalize_binary','normalize','inspect']
    functions=extract(OLD/'adapter.py',helper_names)
    require=extract(Path(dependencies['interface_common']['path']),['require'])['require']
    nonempty=extract(Path(dependencies['human_receiver']['path']),['nonempty'])['nonempty']
    original_inspect=functions['inspect']
    functions['inspect']=original_inspect.replace('4002','1002').replace('4001','1001').replace('4000','1000').replace('800','200')
    if '4000' in functions['inspect'] or '800' in functions['inspect']:raise ValueError('Unadapted shape constant')
    header='''"""Existing reader/normalizer unchanged; inspect shape adapted800 to200 only."""
import io,re,zipfile
from collections import Counter
from decimal import Decimal,InvalidOperation
from types import SimpleNamespace
import xml.etree.ElementTree as ET
DIMS=('S','E','Ec','I','F')
NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
RNS='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
'''
    text=header+'\n'+require+'\n\n'+nonempty+'\n\nOLD=SimpleNamespace(nonempty=nonempty)\n\n'+'\n\n'.join(functions[n] for n in helper_names)+'\n'
    vendor=HERE/'bound_xlsx_reader.py'
    with vendor.open('x') as f:f.write(text)
    draw_path=DELIVERY/'coordinator-private/draw-and-mapping.json'
    draw=json.loads(draw_path.read_text())
    rows=draw['records']
    if len(rows)!=200 or len({x['source_id'] for x in rows})!=200:raise ValueError('Expected actual200 unique draw')
    strata={}
    for r in rows:
        h={'id':r['stratum'],'N':r['N_h'],'n':r['n_h'],'department':r['department'],'domain':r['domain']}
        if r['stratum'] in strata and strata[r['stratum']]!=h:raise ValueError('Inconsistent stratum metadata')
        strata[r['stratum']]=h
        if Fraction(r['pi_exact'])!=Fraction(h['n'],h['N']) or Fraction(r['weight_exact'])!=Fraction(h['N'],h['n']):raise ValueError('New exact weight mismatch')
    counts=Counter(x['stratum'] for x in rows)
    if len(strata)!=41 or any(counts[h['id']]!=h['n'] or (h['n']==1 and h['N']>1) for h in strata.values()):raise ValueError('Invalid new stratum count')
    domain_N={d:sum(h['N'] for h in strata.values() if h['domain']==d) for d in ['remaining','exposed']}
    weighted={d:sum((Fraction(r['weight_exact']) for r in rows if r['domain']==d),Fraction()) for d in domain_N}
    if domain_N!={'remaining':1444,'exposed':3037} or weighted!={d:Fraction(N) for d,N in domain_N.items()}:raise ValueError('Weights do not recover domain populations')
    ids=sorted(r['source_id'] for r in rows)
    canonical=hashlib.sha256(json.dumps(ids,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    design={'kind':'stratified_srswor','sampling_unit':'source_unit','strata':sorted(strata.values(),key=lambda x:x['id']),
        'assigned_ids_sha256':canonical,'domain_partition':'remaining_exposed','domain_population_N':domain_N}
    bridge=module(BRIDGE,'_bound_preparation_only_bridge')
    metadata=bridge.metadata_template(design)
    records=[{'unit_id':r['source_id'],'stratum_id':r['stratum'],'department':r['department'],
              'outputs':{m:None for m in ['A','B','reference','rule','LLM']}} for r in rows]
    write(HERE/'statistics-input.UNFILLED.template.json',{'data_role':None,'bridge_status':'unfilled200_preparation_not_a_real_execution','metadata':metadata,'records':records})
    write(HERE/'assigned-design-metadata.json',{'actual_sample_N':200,'sampling_seed':2026101001,'seed_is_not_model_seed':True,
        'design':design,'records':rows,'exact_domain_weights':{d:str(w) for d,w in weighted.items()},'actual_labels_read':0})
    manifest=json.loads((DELIVERY/'workbook-manifest.json').read_text())
    packages=json.loads((DELIVERY/'distribution-package-manifest.json').read_text())
    templates={}
    (HERE/'templates').mkdir(exist_ok=False)
    for w in manifest['workbooks']:
        side=w['side']
        package=next(x['file'] for x in packages['packages'] if x['side']==side)
        if binding(Path(package['path']))!=package:raise ValueError('Original distribution package binding changed')
        with zipfile.ZipFile(package['path']) as z:
            raw=z.read('coder-'+side+'/独立编码表-'+side+'-200条.xlsx')
        if hashlib.sha256(raw).hexdigest()!=w['file']['sha256'] or len(raw)!=w['file']['bytes']:raise ValueError('Archived blank template differs')
        destination=HERE/'templates'/('original-blank-'+side+'.xlsx')
        with destination.open('xb') as f:f.write(raw)
        templates[side]=binding(destination)
    bindings={'vendor':binding(vendor),'code':binding(HERE/'receive.py'),'draw':binding(draw_path),
        'workbook_manifest':binding(DELIVERY/'workbook-manifest.json'),'materials':binding(DELIVERY/'material-pages-index.json'),
        'template_inputs':templates,
        'source_helpers':[binding(OLD/'adapter.py'),*dependencies.values(),binding(BRIDGE),binding(ENGINE)],
        'original_inspect_function_sha256':hashlib.sha256(original_inspect.encode()).hexdigest(),
        'changed_reader_function':'inspect only;4002/4001/4000/800 changed to1002/1001/1000/200',
        'normalization_unchanged':True,'formal_numeric_results_produced':0}
    write(HERE/'bindings.json',bindings)
    print(json.dumps({'status':'actual200_reader_and_sampling_metadata_prepared','strata_N':41,'record_N':200,
        'judgment_rows_per_coder':1000,'exact_weighted_domain_totals':{d:str(w) for d,w in weighted.items()},'actual_human_results':0},ensure_ascii=False))


if __name__=='__main__':main()
