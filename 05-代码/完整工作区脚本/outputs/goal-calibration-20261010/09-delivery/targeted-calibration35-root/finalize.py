from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlsplit, unquote
import hashlib
import io
import json
import zipfile
import xml.etree.ElementTree as ET
from openpyxl import load_workbook

HERE=Path(__file__).resolve().parent
MAIN='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
REL='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PKG='http://schemas.openxmlformats.org/package/2006/relationships'
ET.register_namespace('',MAIN);ET.register_namespace('r',REL)
def bind(p):
    raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
assert not (HERE/'saved-readback.json').exists()
source=json.loads((HERE/'workbook-input.json').read_text());target=HERE/'需要定向核定-34条35项.xlsx';before=bind(target)
with zipfile.ZipFile(target) as z:
    assert z.testzip() is None
    original={n:z.read(n) for n in z.namelist()};infos={i.filename:i for i in z.infolist()}
parts=dict(original);sheet_name='xl/worksheets/sheet1.xml';rel_name='xl/worksheets/_rels/sheet1.xml.rels'
sheet=ET.fromstring(parts[sheet_name]);assert sheet.find(f'{{{MAIN}}}hyperlinks') is None
rels=ET.fromstring(parts[rel_name]) if rel_name in parts else ET.Element(f'{{{PKG}}}Relationships')
existing={x.attrib['Id'] for x in rels};links=ET.Element(f'{{{MAIN}}}hyperlinks')
for i,row in enumerate(source['rows'],6):
    uri=row['material_url'];parsed=urlsplit(uri);assert parsed.scheme=='file' and Path(unquote(parsed.path)).is_file()
    rid=f'rIdMaterial{i}';assert rid not in existing
    ET.SubElement(rels,f'{{{PKG}}}Relationship',{'Id':rid,'Type':REL+'/hyperlink','Target':uri,'TargetMode':'External'})
    ET.SubElement(links,f'{{{MAIN}}}hyperlink',{'ref':f'A{i}',f'{{{REL}}}id':rid})
following={'printOptions','pageMargins','pageSetup','headerFooter','rowBreaks','colBreaks','customProperties','cellWatches','ignoredErrors','smartTags','drawing','legacyDrawing','legacyDrawingHF','picture','oleObjects','controls','webPublishItems','tableParts','extLst'}
index=next((i for i,x in enumerate(sheet) if x.tag.rsplit('}',1)[-1] in following),len(sheet));sheet.insert(index,links)
parts[sheet_name]=ET.tostring(sheet,encoding='utf-8',xml_declaration=True);parts[rel_name]=ET.tostring(rels,encoding='utf-8',xml_declaration=True)
temp=target.with_suffix('.native-links.tmp')
with zipfile.ZipFile(temp,'x',compression=zipfile.ZIP_DEFLATED) as z:
    for n,raw in parts.items():z.writestr(infos.get(n,n),raw)
with zipfile.ZipFile(temp) as z:
    assert z.testzip() is None
    for n,raw in original.items():
        if n not in {sheet_name,rel_name}:assert z.read(n)==raw
w=load_workbook(io.BytesIO(temp.read_bytes()),read_only=False,data_only=False);assert w.sheetnames==[source['sheet']]
s=w[source['sheet']];assert s.max_row==40 and s.max_column==8 and s.freeze_panes=='C6'
assert [s.cell(5,c).value for c in range(1,9)]==source['headers']
for i,row in enumerate(source['rows'],6):
    cells=[s.cell(i,c) for c in range(1,9)]
    assert [c.value for c in cells]==row['values'],i
    assert cells[0].data_type=='s' and cells[0].number_format=='@'
    assert all(c.data_type!='f' for c in cells)
    assert cells[0].hyperlink.target==row['material_url']
    assert Path(unquote(urlsplit(cells[0].hyperlink.target).path)).is_file()
    assert not cells[3].protection.locked or not s.protection.sheet
assert sum(s.cell(i,4).value is None for i in range(6,41))==22
w.close();temp.replace(target)
report={'at_utc':datetime.now(timezone.utc).isoformat(),'workbook':bind(target),'artifact_export_before_native_links':before,'source_matrix':bind(HERE/'workbook-input.json'),'rows':35,'unique_current_records':34,'original_identifier_strings_and_leading_zero_format_verified':True,'all_values_and_numeric_types_verified':True,'blank_D_preserved':22,'material_native_links_verified':35,'all_link_targets_exist':True,'freeze_panes':'C6','D_E_directly_editable':True,'extra_human_result_column_added':False,'ZIP_CRC_and_unchanged_unrelated_parts_verified':True,'native_links_change_displayed_values_or_styles':False,'visual_review_opening_and_longest_pending_final_check':True,'actual_human_result_N':0,'identity':'AI suggestions for targeted development calibration; not a new independent blind test','original_coding_files_modified':False}
(HERE/'saved-readback.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'rows_verified':35,'links_verified':35,'blank_D':22,'saved':str(target)},ensure_ascii=False))
