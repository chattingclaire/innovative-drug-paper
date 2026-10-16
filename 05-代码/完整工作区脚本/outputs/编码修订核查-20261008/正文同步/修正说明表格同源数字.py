"""Repair a delivery-review finding without changing coding/statistical sources."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from copy import deepcopy
import json, hashlib, shutil
from lxml import etree as E

HERE=Path(__file__).resolve().parent
WORK=HERE.parent
OUT=WORK/'本轮结果'
STAT=WORK/'统计复算/完整39与LLM03-同步复算01'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W='{'+NS['w']+'}'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def binding(p):return {'path':str(p.resolve()),'sha256':sha(p)}
def text(p):return ''.join(p.xpath('.//w:t/text()',namespaces=NS))

memo=OUT/'编码复核说明与真人检验事项.docx'
main=OUT/'创新药评价的注意力配置差异与协调路径.docx'
assert sha(memo)=='1d4a787965db122570160347ec6318c77cc645d23f4411b992386654fd779cde'
assert sha(main)=='042cf1f7154fa8b2ad915b6cbdb6948e8583a8f164fccff0f5e168868d151705'
numeric=WORK/'统计复算/独立数值审查/complete39_LLM03_independent_numeric_QA_FINAL.json'
assert sha(numeric)=='838520092cafb6ca64f613e6167983ffa0a4f9821ecd5494b805f78e1339b2da'
assert read(numeric)['status']=='PASS_INDEPENDENT_NUMERIC_QA_COMPLETE'
archive=HERE/'说明同源核对未通过记录'
archive.mkdir(exist_ok=False)
oldmemo=archive/memo.name
shutil.copy2(memo,oldmemo)
oldrender=archive/'实际审读的4页渲染'
shutil.move(str(HERE/'渲染说明'),str(oldrender))
failed={'status':'FAIL_MEMO_RULE_KAPPA_TABLE_NOT_SYNCHRONIZED',
        'actual_original_image_pages_read':[binding(oldrender/f'page-{i}.png') for i in range(1,5)],
        'memo':binding(oldmemo),'main_unchanged':binding(main),
        'finding':'说明表格仍为旧规则κ，正文及本次独立数值QA未变。仅修说明表格25个展示值。',
        'statistical_sources_changed':False,'labels_changed':False}
(archive/'实际视觉与数值发现.json').write_text(json.dumps(failed,ensure_ascii=False,indent=2)+'\n')
with ZipFile(memo)as z:parts={i.filename:(i,z.read(i.filename))for i in z.infolist()}
tree=E.fromstring(parts['word/document.xml'][1])
tables=tree.findall('w:body/w:tbl',NS);assert len(tables)==1
rows=tables[0].findall('w:tr',NS);assert len(rows)==6
classification=read(STAT/'machine_reference_classification.json')['comparisons']
agreement=read(STAT/'A_C_before_third_agreement.json')['comparisons']
def point(method,ref,d):
    source=agreement if method=='A_C' else classification
    found=[r for r in source if (r['method'],r['reference'],r['dimension'],r['component'],r['group'],r['weighting'])==
           (method,ref,d,'probability_canonical','ALL','eligible_design_weighted')]
    assert len(found)==1
    return found[0]['metrics']['kappa']['estimate']
ab_ref=next(r['reference']for r in agreement)
changes=[]
for row,d in zip(rows[1:],('S','E','Ec','I','F')):
    cells=row.findall('w:tc',NS);assert len(cells)==6
    values=[point('A_C',ab_ref,d)]+[point(m,r,d)for m in ('rules-v39','LLM-candidate03-single-unit-reconciled')for r in ('A','C')]
    for cell,v in zip(cells[1:],values):
        old=text(cell);new=f'{v:.3f}'
        p=cell.find('w:p',NS);pr=deepcopy(p.find('w:r/w:rPr',NS))
        for child in list(p):
            if child.tag!=W+'pPr':p.remove(child)
        r=E.SubElement(p,W+'r')
        if pr is not None:r.append(pr)
        E.SubElement(r,W+'t').text=new
        changes.append({'dimension':d,'old':old,'new':new,'estimate':v})
xml=E.tostring(tree,xml_declaration=True,encoding='UTF-8',standalone=True)
temp=OUT/'说明同源修正临时文件.docx'
assert not temp.exists()
with ZipFile(temp,'x',compression=ZIP_DEFLATED)as z:
    for name,(info,data)in parts.items():z.writestr(info,xml if name=='word/document.xml'else data)
temp.replace(memo)
assert sha(main)=='042cf1f7154fa8b2ad915b6cbdb6948e8583a8f164fccff0f5e168868d151705'
record={'status':'MEMO25_KAPPA_VALUES_SYNCHRONIZED_NEW_RENDER_PENDING','changes':changes,
        'new_memo':binding(memo),'preserved_old_memo':binding(oldmemo),
        'source_bindings':[binding(p)for p in [numeric,STAT/'machine_reference_classification.json',STAT/'A_C_before_third_agreement.json',Path(__file__)]],
        'main_and_statistics_unchanged':True}
(HERE/'说明表格同源修正.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(record['new_memo'],ensure_ascii=False))
