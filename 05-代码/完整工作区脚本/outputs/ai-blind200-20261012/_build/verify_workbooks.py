from pathlib import Path
import hashlib
import json
import re
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / 'goal-calibration-20261010/09-delivery/human200-independent-preparation-root'
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
      'r': 'http://schemas.openxmlformats.org/package/2006/relationships'}
OFFICE_R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def context_text(value):
    if isinstance(value,str):
        return value or '当前条款'
    if isinstance(value,dict) and (value.get('current_source') or value.get('current_locator')):
        labels={'paragraph_ids':'段落','paragraph_id':'段落','physical_pages':'页','pages':'页','source_unit_id':'原文单元','sequence_index':'顺序'}
        location='；'.join(labels.get(key,key)+'：'+('、'.join(map(str,val)) if isinstance(val,list) else str(val))
                          for key,val in (value.get('current_source',{}).get('locator') or value.get('current_locator',{})).items())
        count=len(value.get('used_contexts',[]))
        suffix=(f'实际使用补充语境{count}处，完整定位及片段见同目录《完整依据.md》对应盲号、维度。' if count else '未使用补充语境。')
        return f'当前原文定位：{location}。'+suffix
    return '完整语境定位见同目录《完整依据.md》对应盲号、维度。'


def inspect(path):
    with zipfile.ZipFile(path) as archive:
        sheet = ET.fromstring(archive.read('xl/worksheets/sheet1.xml'))
        strings = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            root = ET.fromstring(archive.read('xl/sharedStrings.xml'))
            strings = [''.join(si.itertext()) for si in root]
        values = {}
        formulas = {}
        for cell in sheet.findall('s:sheetData/s:row/s:c', NS):
            address = cell.get('r')
            value = cell.find('s:v', NS)
            if cell.get('t') == 's':
                value = strings[int(value.text)] if value is not None else None
            elif cell.get('t') == 'inlineStr':
                value = ''.join(cell.find('s:is', NS).itertext())
            elif value is not None and value.text is not None:
                value = value.text
                if cell.get('t') not in ('str', 'e', 'b'):
                    value = float(value)
                    if value.is_integer():
                        value = int(value)
            else:
                value = None
            values[address] = value
            formula = cell.find('s:f', NS)
            if formula is not None:
                formulas[address] = formula.text
        relationships = {}
        relpath = 'xl/worksheets/_rels/sheet1.xml.rels'
        if relpath in archive.namelist():
            relationships = {x.get('Id'): x.get('Target') for x in ET.fromstring(archive.read(relpath))}
        links = {x.get('ref'): relationships.get(x.get(OFFICE_R), x.get('location'))
                 for x in sheet.findall('s:hyperlinks/s:hyperlink', NS)}
        validations = []
        for validation in sheet.findall('s:dataValidations/s:dataValidation', NS):
            attributes = dict(validation.attrib)
            for key in ('allowBlank','showDropDown','showInputMessage','showErrorMessage'):
                attributes[key] = attributes.get(key,'0') in ('true','1')
            attributes.setdefault('errorStyle','stop')
            attributes.setdefault('operator','between')
            attributes.setdefault('imeMode','noControl')
            validations.append({'attributes':attributes,
                'children':[(child.tag,dict(child.attrib),child.text) for child in validation]})
        pane = sheet.find('s:sheetViews/s:sheetView/s:pane', NS)
        return {'values':values, 'formulas':formulas, 'links':links,
                'validations':validations, 'pane':pane.attrib if pane is not None else None}


def main():
    baselines = json.loads((ROOT/'_build/original-input-hashes.json').read_text())
    unchanged = all(digest(Path(path)) == expected for path,expected in baselines.items())
    frozen = json.loads((ROOT/'_build/frozen-sources.json').read_text())
    for item in frozen.values():
        assert digest(Path(item['zip']))==item['zip_sha256'], 'Original ZIP changed'
        assert digest(Path(item['local_copy']))==item['workbook_sha256'], 'Frozen blank workbook changed'
    results = []
    for side in 'AB':
        original = Path(frozen[side]['local_copy'])
        output = ROOT/f'评审{side}'/f'AI独立盲评-{side}-200条.xlsx'
        before, after = inspect(original), inspect(output)
        submission=json.loads((output.parent/'submission.json').read_text())
        assert submission['status']=='sealed' and submission['identity']=='AI评审'+side
        assert submission['independent'] is True and submission['human_judgments'] is False
        assert digest(output.parent/'judgments.jsonl')==submission['judgments_sha256'], 'Sealed judgment hash mismatch'
        entries = [json.loads(line) for line in (output.parent/'judgments.jsonl').read_text().splitlines() if line.strip()]
        by_id = {entry['blind_id']:entry['judgments'] for entry in entries}
        assert len(entries)==len(by_id)==200
        for row in range(1,1002):
            for col in 'ABC':
                assert before['values'].get(f'{col}{row}')==after['values'].get(f'{col}{row}'), f'Source mismatch {side}/{col}{row}'
        for col in 'DE':
            assert before['values'].get(f'{col}1')==after['values'].get(f'{col}1')
        for row in range(2,1002):
            key,dimension=after['values'][f'A{row}'],after['values'][f'C{row}']
            judgment=by_id[key][dimension]
            expected=(('待定：' if judgment['value'] is None else '')+judgment['reason']+
                '\n原文依据：'+(judgment['evidence'] or '见具体待补项')+
                '\n语境定位：'+context_text(judgment['context']))
            assert after['values'].get(f'D{row}')==judgment['value'], f'Value mismatch {side}/D{row}'
            assert after['values'].get(f'E{row}')==expected, f'Reason mismatch {side}/E{row}'
        assert before['links']==after['links'], f'Native hyperlink mismatch {side}'
        assert len(after['links'])==1000
        broken=[]
        for target in set(after['links'].values()):
            if not (output.parent/target).exists():
                broken.append(target)
        assert not broken, f'Broken links {side}: {broken}'
        assert before['validations']==after['validations'], f'Validation mismatch {side}'
        assert before['pane']==after['pane'], f'Freeze-pane mismatch {side}'
        assert before['formulas']==after['formulas'], f'Unexpected formula changes {side}'
        results.append({'side':side,'records':200,'judgments':1000,'all_values_and_reasons_match_sealed_judgments':True,
                        'source_columns_preserved':True,'native_hyperlinks':1000,'unique_material_pages':len(set(after['links'].values())),
                        'all_workbook_targets_resolve':True,'validation_preserved':True,'freeze_pane_preserved':True,
                        'workbook_sha256':digest(output),'human_judgments':False})
    report={'status':'passed','original_input_observation':'unchanged' if unchanged else 'changed_since_start_outside_this_export',
            'original_inputs_unchanged_at_readback':unchanged,'original_zips_unchanged':True,'checks':results,
            'scope':'Mechanical XLSX fidelity and coverage; semantic accuracy awaits human judge.'}
    (ROOT/'_build/workbook-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
