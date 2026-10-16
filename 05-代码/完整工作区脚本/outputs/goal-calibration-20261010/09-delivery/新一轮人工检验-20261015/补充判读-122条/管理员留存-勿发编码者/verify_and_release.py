from pathlib import Path
import json, hashlib, zipfile, shutil, re
from datetime import datetime, timezone
from urllib.parse import urlsplit, unquote
from lxml import etree, html
HERE=Path(__file__).resolve().parent; OUT=HERE.parent
UP=OUT.parent/'管理员留存-勿发编码者'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def binding(p):return dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size)
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
assert not (HERE/'READY.json').exists()
mapping=json.loads((HERE/'blind-assignment.json').read_text())
inputs=[json.loads(l) for l in (HERE/'common-inputs.jsonl').read_text().splitlines()]
units={r['id']:r for r in inputs}; assert len(units)==122
sources=json.loads((HERE/'sources.json').read_text())
protocol=json.loads((HERE/'protocol.json').read_text())
assert protocol['common_inputs_sha256']==sha(HERE/'common-inputs.jsonl')
checks={}; files=[]
ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
for side in ['A','B']:
    folder=OUT/('编码者'+side)
    for artifact in folder.glob('*.inspect.ndjson'):
        shutil.move(str(artifact),str(HERE/'_build'/artifact.name))
    assert sha(folder/'共同编码手册.txt')==protocol['common_manual_sha256']
    assert len(mapping[side])==122 and {m['id'] for m in mapping[side]}==set(units)
    linked=0
    for p in folder.rglob('*.html'):
        if '原件' in p.parts:continue
        dom=html.fromstring(p.read_text())
        for ref in dom.xpath('//@href | //@src'):
            u=urlsplit(ref)
            if u.scheme:continue
            target=(p.parent/unquote(u.path)).resolve();assert target.exists(),(p,ref)
            assert folder.resolve() in target.parents
            if u.fragment:
                assert html.fromstring(target.read_text()).xpath('//*[@id=$id]',id=unquote(u.fragment)),ref
            linked+=1
    for m in mapping[side]:
        dom=html.fromstring((folder/m['material_locator']).read_text())
        current=dom.xpath('//div[@class="current"]')[0].text_content()
        assert current==units[m['id']]['source_bundle']['source_record']['text']
        assert hashlib.sha256(current.encode()).hexdigest()==m['text_sha256']
        para=units[m['id']]['source_bundle']['source_record']['contexts'][0]['text']
        assert para in dom.text_content()
    for d in sources:
        dom=html.fromstring((folder/'来源'/f'{d["code"]}.html').read_text())
        for i,t in enumerate(d['paragraphs']):
            assert dom.xpath(f'//div[@id="p{i}"]/p')[0].text_content()==t
        r=next(r for r in inputs if r['id'].startswith('SUP-'+d['code']))
        resources=r['source_bundle']['source_full_text_resources']
        assert [p['text'] for p in resources[0]['paragraphs']]==d['paragraphs']
        if len(resources)>1:assert dom.xpath('//pre')[0].text_content()==resources[1]['paragraphs'][0]['text']
        for name in [d['source_file']]+d['attachments']:
            assert sha(folder/'原件'/name)==sha(UP/'候选来源下载'/name)
    book=folder/f'补充判读-{side}-122条.xlsx'
    with zipfile.ZipFile(book) as z:
        ss=etree.fromstring(z.read('xl/sharedStrings.xml')) if 'xl/sharedStrings.xml' in z.namelist() else None
        strings=[''.join(e.itertext()) for e in ss] if ss is not None else []
        root=etree.fromstring(z.read('xl/worksheets/sheet1.xml'))
        cells={c.get('r'):c for c in root.findall('.//s:c',ns)}
        def value(ref):
            c=cells.get(ref)
            if c is None:return None
            assert c.find('s:f',ns) is None,'Unexpected formula'
            v=c.find('s:v',ns)
            if c.get('t')=='s':return strings[int(v.text)]
            if c.get('t')=='inlineStr':return ''.join(c.find('s:is',ns).itertext())
            return v.text if v is not None else None
        for i,m in enumerate(mapping[side]):
            for j,dim in enumerate(['安全性 S','有效性 E','经济性 Ec','创新性 I','公平性 F']):
                row=5+i*5+j
                assert [value(f'{c}{row}') for c in 'ABC']==[m['blind_id'],m['material_locator'],dim]
                assert value(f'D{row}') in [None,''] and value(f'E{row}') in [None,'']
        assert root.find('.//s:pane',ns).get('ySplit')=='4'
        assert root.find('.//s:dataValidation',ns).get('sqref')=='D5:D614'
        assert value('A615') is None
    allowed={'.html','.txt','.xlsx','.json','.doc','.jpg'}
    for p in folder.rglob('*'):
        if p.is_file():assert p.suffix in allowed,p;files.append(binding(p))
    zip_path=OUT/f'编码者{side}-补充判读122条.zip'
    with zipfile.ZipFile(zip_path,'x',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(folder.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(OUT))
    with zipfile.ZipFile(zip_path) as z:
        assert z.testzip() is None
        assert all(n.startswith('编码者'+side+'/') for n in z.namelist())
    checks[side]={'items':122,'decision_rows':610,'response_cells_blank':1220,'local_links_checked':linked,'zip':binding(zip_path),'human_files':sum(1 for p in folder.rglob('*') if p.is_file())}
assert [m['id'] for m in mapping['A']] != [m['id'] for m in mapping['B']]
guide=OUT/'给研究者的说明.md'
guide.write_text(guide.read_text().replace('目前这是已准备的材料包，只有在READY.json生成并完成打包检查后才可发放。当前没有新人工检验成绩。','两份材料包已通过编号、空白填写区、全文和附件一致性、全部本地链接及压缩包检查，可以分别发放。Excel原文位置栏是文件位置文字，请通过“开始阅读.html”按编号打开原文。当前没有新人工检验成绩。'))
save(HERE/'READY.json',{'status':'ready_for_independent_human_coding','created_at_utc':datetime.now(timezone.utc).isoformat(),'checks':checks,'human_files':files,'common_inputs':binding(HERE/'common-inputs.jsonl'),'protocol':binding(HERE/'protocol.json'),'method_freeze':binding(UP/'方法与标准冻结.json'),'visual_review':'A/B first three item groups reviewed; readable headers, explicit group borders, blank answer fields. No spreadsheet hyperlink behavior claimed; HTML index links verified.','independent_validation_completed':False,'new_human_answers_received':False})
print(json.dumps(checks,ensure_ascii=False,indent=2))
