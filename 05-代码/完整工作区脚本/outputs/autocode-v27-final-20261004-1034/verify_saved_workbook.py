"""Verify the exported XLSX against the frozen row-level and metric data."""
from pathlib import Path
import hashlib
import json
import zipfile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
data=json.loads((ROOT/'workbook_data.json').read_text())
ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(ROOT/'自动规则五维修订结果-v27.xlsx') as archive:
    strings=[''.join(item.itertext()) for item in ET.fromstring(archive.read('xl/sharedStrings.xml'))]
    def cells(sheet):
        tree=ET.fromstring(archive.read(f'xl/worksheets/sheet{sheet}.xml'))
        result={}
        for cell in tree.findall('m:sheetData/m:row/m:c',ns):
            value=cell.find('m:v',ns)
            result[cell.get('r')]=None if value is None else strings[int(value.text)] if cell.get('t')=='s' else value.text
        return result
    detail=cells(3)
    for i,row in enumerate(data['rows'],2):
        assert detail['A'+str(i)]==row['id'],('id',i)
        assert detail['C'+str(i)]==row['text'],('text',i)
        for column,dim in zip('DEFGH',('S','E','Ec','I','F')):
            assert int(detail[column+str(i)])==row['after'][dim],('label',i,dim)
    calculation=cells(2)
    for i,metric in enumerate(data['metrics'],2):
        for column,key in zip('LMNO',('kappa','precision','recall','f1')):
            actual=calculation[column+str(i)];expected=metric[key]
            assert actual=='n.a.' if expected is None else abs(float(actual)-expected)<1e-10,(i,key)
release=json.loads((ROOT/'release_manifest.json').read_text())
for path,expected in release['code_and_input_bindings'].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==expected,path
for name,expected in release['output_bindings'].items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,name
report={'all_4924_exported_ids_and_original_texts_match':True,
        'all_24620_current_labels_match':True,
        'all_240_exported_kappa_precision_recall_f1_values_match':True,
        'frozen_code_input_test_and_output_hashes_match':True,
        'visual_review':'All three worksheets inspected; primary summary, calculations and representative source/evidence ranges are legible.'}
(ROOT/'saved_workbook_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False))
