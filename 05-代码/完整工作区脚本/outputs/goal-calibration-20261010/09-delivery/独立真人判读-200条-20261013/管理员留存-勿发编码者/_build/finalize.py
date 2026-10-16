from pathlib import Path
import hashlib, html, importlib.util, json, posixpath, re, sys, zipfile
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import unquote, urlparse
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
ADMIN=HERE.parent
OUT=ADMIN.parent
ROOT=OUT.parent.parent
sys.dont_write_bytecode=True
MAIN='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
REL='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PKG='http://schemas.openxmlformats.org/package/2006/relationships'
ET.register_namespace('',MAIN); ET.register_namespace('r',REL)
def load(p):return json.loads(p.read_text())
def bind(p):
    raw=p.read_bytes();return {'path':str(p.resolve()),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def put(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
mapping=load(ADMIN/'blind-assignment.json')
frozen=load(ADMIN/'sampling-freeze.json')
assert not (ADMIN/'ISSUED.json').exists(),'Issued release is immutable'

spec=importlib.util.spec_from_file_location('reader',ROOT/'05-validation/human200-reception-root/bound_xlsx_reader.py')
reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader);reader.posixpath=posixpath
proof=[]
for side in ('A','B'):
    folder=OUT/('发给编码者'+side)
    target=folder/f'独立判读-{side}-200条.xlsx'
    before=reader.read_xlsx(target.read_bytes())
    with zipfile.ZipFile(target) as z:members={n:z.read(n) for n in z.namelist()}
    sn='xl/worksheets/sheet1.xml';rn='xl/worksheets/_rels/sheet1.xml.rels'
    sheet=ET.fromstring(members[sn]);rels=ET.fromstring(members[rn]) if rn in members else ET.Element('{'+PKG+'}Relationships')
    previous=sheet.find('{'+MAIN+'}hyperlinks')
    if previous is not None:
        assert len(previous)==1000
        sheet.remove(previous)
        for e in list(rels):
            if e.attrib['Id'].startswith('rIdMaterial'):rels.remove(e)
    links=ET.Element('{'+MAIN+'}hyperlinks')
    for i,r in enumerate(mapping['methods'][side]):
        rid=f'rIdMaterial{i+1}'
        assert all(x.attrib['Id']!=rid for x in rels)
        assert (folder/r['material_locator']).is_file()
        ET.SubElement(rels,'{'+PKG+'}Relationship',{'Id':rid,'Type':REL+'/hyperlink','Target':r['material_locator'],'TargetMode':'External'})
        for d in range(5):ET.SubElement(links,'{'+MAIN+'}hyperlink',{'ref':f'B{2+i*5+d}','{'+REL+'}id':rid})
    after={'printOptions','pageMargins','pageSetup','headerFooter','rowBreaks','colBreaks','customProperties','cellWatches','ignoredErrors','smartTags','drawing','legacyDrawing','legacyDrawingHF','picture','oleObjects','controls','webPublishItems','tableParts','extLst'}
    ix=next((i for i,e in enumerate(sheet) if e.tag.rsplit('}',1)[-1] in after),len(sheet));sheet.insert(ix,links)
    dvs=sheet.find('{'+MAIN+'}dataValidations');assert len(dvs)==1
    dv=dvs[0];assert dv.attrib['sqref']=='D2:D1001'
    for k,v in {'allowBlank':'1','showErrorMessage':'1','errorStyle':'stop','errorTitle':'请填0或1','error':'确有材料缺失请留空，并在理由栏写明待定原因。'}.items():dv.set(k,v)
    members[sn]=ET.tostring(sheet,encoding='utf-8',xml_declaration=True)
    members[rn]=ET.tostring(rels,encoding='utf-8',xml_declaration=True)
    tmp=target.with_suffix('.tmp')
    with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as z:
        for n,raw in members.items():z.writestr(n,raw)
    tmp.replace(target)
    actual=reader.read_xlsx(target.read_bytes());assert actual==before,'Cell data changed during hyperlink addition'
    assert set(actual)=={'独立初判'}
    sc=actual['独立初判'];assert not sc['duplicates'] and not sc['merged']
    for i,r in enumerate(mapping['methods'][side]):
        for d,dimension in enumerate(('S','E','Ec','I','F')):
            n=2+i*5+d
            for col,val in [('A',r['original_blind_id']),('B',r['material_locator']),('C',dimension)]:
                cell=reader.cell(sc['cells'],f'{col}{n}');assert cell['formula'] is None and cell['resolved_value']==val
            assert all(reader.blank(reader.cell(sc['cells'],f'{c}{n}')) for c in 'DE')
    assert bind(folder/'共同编码手册.txt')['sha256']==frozen['manual']['sha256']
    inspection=target.with_name(target.name+'.inspect.ndjson')
    if inspection.exists():inspection.rename(HERE/(side+'-export-inspection.ndjson'))
    guide=html.escape((folder/'填写说明.txt').read_text())
    entry=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>编码者{side} 独立判读材料</title><style>body{{font:17px/1.8 Arial,"PingFang SC",sans-serif;max-width:860px;margin:40px auto;padding:0 24px;color:#263749}}h1{{font-size:28px}}a{{color:#185f9b}}.links{{padding:18px 22px;background:#edf3f8;border-radius:8px}}pre{{white-space:pre-wrap;font:16px/1.8 inherit}}li{{margin:8px 0}}</style><h1>编码者{side} 独立判读材料</h1><p>200条材料，每条分别填写五个维度。</p><div class="links"><ul><li><a href="独立判读-{side}-200条.xlsx">打开填写表</a></li><li><a href="材料目录.html">查看200条原文材料</a></li><li><a href="共同编码手册.txt">阅读共同编码手册</a></li><li><a href="提交说明.txt">填写提交说明</a></li></ul></div><h2>填写方法</h2><pre>{guide}</pre></html>'''
    (folder/'开始阅读.html').write_text(entry)
    files=[p for p in folder.rglob('*') if p.is_file()]
    class Links(HTMLParser):
        def __init__(self):super().__init__();self.links=[]
        def handle_starttag(self,t,attrs):
            self.links += [v for k,v in attrs if k in ('href','src')]
    link_count=0
    for p in files:
        if p.suffix=='.html' and p.parent.name!='附件':
            parser=Links();parser.feed(p.read_text())
            for link in parser.links:
                u=urlparse(link)
                if u.scheme or not u.path:continue
                dest=(p.parent/unquote(u.path)).resolve()
                assert dest.is_relative_to(folder.resolve()) and dest.is_file(),str(dest)
                link_count+=1
    proof.append({'side':side,'template_binding':bind(target),'units':200,'slots':1000,'blank_answer_and_reason_cells':2000,'native_relative_material_links':1000,'generated_page_local_links_resolved':link_count,'original_website_snapshots_retained_byte_exact':True,'manual_sha256':bind(folder/'共同编码手册.txt')['sha256'],'initial_answers_present':False,'files':[{'relative_path':str(p.relative_to(folder)),**bind(p)} for p in sorted(files)]})
put(ADMIN/'issued-workbooks-and-files.json',{'created_at_utc':datetime.now(timezone.utc).isoformat(),'packages':proof,'native_hyperlinks_added_without_cell_changes':True})
archives=[]
for side in ('A','B'):
    folder=OUT/('发给编码者'+side);zpath=OUT/f'编码者{side}材料.zip'
    assert not zpath.exists()
    with zipfile.ZipFile(zpath,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(folder.rglob('*')):
            if p.is_file():z.write(p,str(p.relative_to(OUT)))
    with zipfile.ZipFile(zpath) as z:
        assert z.testzip() is None
        assert all(n.startswith(folder.name+'/') for n in z.namelist())
        assert not any('管理员' in n or '_build' in n or 'inspect' in n for n in z.namelist())
        for p in folder.rglob('*'):
            if p.is_file():assert z.read(str(p.relative_to(OUT)))==p.read_bytes()
    archives.append(bind(zpath))
put(ADMIN/'ISSUED.json',{'schema':'human200-issued-release-v1','issued_at_utc':datetime.now(timezone.utc).isoformat(),'status':'materials_ready_to_distribute','draw':bind(ADMIN/'draw.json'),'sampling_freeze':bind(ADMIN/'sampling-freeze.json'),'blind_assignment':bind(ADMIN/'blind-assignment.json'),'common_materials':bind(ADMIN/'common-materials.json'),'file_manifest':bind(ADMIN/'issued-workbooks-and-files.json'),'archives':archives,'human_initials_received':False,'human_independence_confirmed':False,'independent_validation_completed':False,'formal_statistical_admission_claimed':False,'model_runs':0,'full_machine_rerun':False,'scope_population_N':1151,'sample_N':200,'old200_overwritten':False})
print(json.dumps({'status':'ready_to_distribute','archives':archives,'blank_workbooks':2,'units_per_reviewer':200},ensure_ascii=False))
