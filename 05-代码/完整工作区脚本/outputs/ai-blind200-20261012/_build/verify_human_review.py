from pathlib import Path
import collections
import csv
import hashlib
import importlib.util
import json
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'真人复核'
PATH=OUT/'真人标注汇总-200条.xlsx'
SHEET_NS='http://schemas.openxmlformats.org/spreadsheetml/2006/main'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    # Artifact Tool authored all cell content. Apply only the worksheet title in
    # OOXML, because that metadata operation is absent from its public help.
    with zipfile.ZipFile(PATH) as archive:
        infos=archive.infolist()
        parts={info.filename:archive.read(info.filename) for info in infos}
    workbook=ET.fromstring(parts['xl/workbook.xml'])
    sheets=workbook.findall(f'{{{SHEET_NS}}}sheets/{{{SHEET_NS}}}sheet')
    assert len(sheets)==1
    assert sheets[0].get('name') in ('独立初判','真人标注汇总')
    sheets[0].set('name','真人标注汇总')
    for node in workbook.findall(f'{{{SHEET_NS}}}definedNames/{{{SHEET_NS}}}definedName'):
        if node.text:
            node.text=node.text.replace("'独立初判'!","'真人标注汇总'!").replace('独立初判!','真人标注汇总!')
    parts['xl/workbook.xml']=ET.tostring(workbook,encoding='utf-8',xml_declaration=True)
    if 'docProps/app.xml' in parts:
        app=ET.fromstring(parts['docProps/app.xml'])
        for node in app.iter():
            if node.text=='独立初判':node.text='真人标注汇总'
        parts['docProps/app.xml']=ET.tostring(app,encoding='utf-8',xml_declaration=True)
    temporary=PATH.with_suffix('.tmp.xlsx')
    with zipfile.ZipFile(temporary,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for info in infos:archive.writestr(info,parts[info.filename])
    temporary.replace(PATH)

    spec=importlib.util.spec_from_file_location('workbook_verifier',ROOT/'_build/verify_workbooks.py')
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    source=helper.inspect(ROOT/'_build/frozen-coder-A.xlsx')
    output=helper.inspect(PATH)
    manifest=json.loads((OUT/'录入记录.json').read_text())
    expected={row['sheet_row']:row for row in manifest['rows']}
    assert len(expected)==1000
    dimensions=collections.defaultdict(collections.Counter)
    provenance=collections.Counter()
    for row in range(2,1002):
        item=expected[row]
        for col in 'ABC':assert source['values'].get(f'{col}{row}')==output['values'].get(f'{col}{row}')
        assert output['values'][f'A{row}']==item['A_blind_id']
        assert output['values'][f'C{row}']==item['dimension']
        assert output['values'].get(f'D{row}')==item['human_value']
        assert output['values'][f'E{row}']==item['recorded_reason']
        if item['human_value'] is None:assert item['recorded_reason'].startswith('待定：')
        dimensions[item['dimension']]['null' if item['human_value'] is None else str(item['human_value'])]+=1
        provenance[item['recording_source']]+=1
    assert provenance=={'user_bulk_confirmation_of_AI_consensus':987,'user_item_specific_confirmation':9,'user_pending_discussion':4}
    assert all(sum(c.values())==200 for c in dimensions.values())
    assert sum(c['1'] for c in dimensions.values())==114
    assert sum(c['0'] for c in dimensions.values())==882
    assert sum(c['null'] for c in dimensions.values())==4
    for feature in ('links','validations','pane','formulas'):assert source[feature]==output[feature],feature
    assert len(output['links'])==1000
    assert all((OUT/target).exists() for target in set(output['links'].values()))
    original_verification=json.loads((ROOT/'_build/workbook-verification.json').read_text())
    for result in original_verification['checks']:
        ai_path=ROOT/f'评审{result["side"]}'/f'AI独立盲评-{result["side"]}-200条.xlsx'
        assert sha(ai_path)==result['workbook_sha256']
    with PATH.open('rb') as stream:
        assert stream.read(2)==b'PK'
    manifest['output_sha256']=sha(PATH)
    manifest['sheet_name']='真人标注汇总'
    (OUT/'录入记录.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    fields=['source_id','dimension','A_blind_id','B_blind_id','human_value','recording_source','sheet_row','recorded_reason']
    with (OUT/'真人标注汇总-逐维记录.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(manifest['rows'])
    report={'status':'passed','source_columns_preserved':True,'all_1000_values_and_provenance_verified':True,
            'native_material_links_preserved':1000,'all_link_targets_exist':True,'AI_sealed_workbooks_unchanged':True,
            'dimensions':dict(dimensions),'provenance':dict(provenance),'numeric_values':996,'pending_values':4,
            'independent_execution_verified':False,'formal_adjudication':False,'output_sha256':sha(PATH)}
    (OUT/'录入核查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
