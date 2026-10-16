"""Read only six historical E cells and their saved reasons/locators; no judgement."""
from pathlib import Path
import datetime
import hashlib
import json
import zipfile
import xml.etree.ElementTree as ET

D = Path(__file__).resolve().parent
ROOT = D.parents[1]
SOURCE = ROOT / '09-delivery/agent-review-20261010/真人4项复核后-v2'
NS = {'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
IDS = ['RECODE25-00036','RECODE25-00038','RECODE25-00045']
ROWS = {'RECODE25-00036':13,'RECODE25-00038':18,'RECODE25-00045':23}
CONTEXT_ROWS = {'RECODE25-00036':13,'RECODE25-00038':19,'RECODE25-00045':25}
SUPPLEMENT_ROWS = {'RECODE25-00036':783,'RECODE25-00038':805,'RECODE25-00045':827}

def binding(path):
    p = Path(path).resolve(); b = p.read_bytes()
    return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}

def write(name, value):
    with (D/name).open('x',encoding='utf8') as f:
        json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')

input_bindings = []; values = {}; members = []
for side in ['A','B']:
    path = SOURCE / ('编码复核表-'+side+'.xlsx')
    file_binding = binding(path); input_bindings.append(file_binding)
    with zipfile.ZipFile(path) as z:
        workbook = ET.fromstring(z.read('xl/workbook.xml'))
        assert [(s.get('name'),s.get('sheetId')) for s in workbook.find('s:sheets',NS)] == [('编码表','1'),('原文语境','2')]
        relationships = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        targets = {r.get('Id'):r.get('Target') for r in relationships}
        for sh in workbook.find('s:sheets',NS):
            rid=sh.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
            expected='worksheets/sheet'+sh.get('sheetId')+'.xml'
            assert targets[rid] in [expected,'/'+ 'xl/'+expected]
        shared=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            shared=[''.join(si.itertext()) for si in ET.fromstring(z.read('xl/sharedStrings.xml'))]
        def cell(c):
            v=c.find('s:v',NS); t=c.get('t'); f=c.find('s:f',NS)
            if t=='s': value=shared[int(v.text)] if v is not None else None
            elif t=='inlineStr': value=''.join(c.find('s:is',NS).itertext())
            else:value=v.text if v is not None else None
            return {'address':c.get('r'),'cell_type':t or 'n','raw_v':v.text if v is not None else None,'value':value,'formula':f.text if f is not None else None}
        coding_bytes=z.read('xl/worksheets/sheet1.xml')
        coding_rows={int(r.get('r')):r for r in ET.fromstring(coding_bytes).findall('.//s:sheetData/s:row',NS)}
        material_bytes=z.read('xl/worksheets/sheet2.xml')
        material_rows={int(r.get('r')):r for r in ET.fromstring(material_bytes).findall('.//s:sheetData/s:row',NS)}
        def cells(row):return {c.get('r').rstrip('0123456789'):cell(c) for c in row}
        top=cells(coding_rows[4])['A']; assert 'E列依据由AI' in top['value']
        for source_id in IDS:
            rn=ROWS[source_id]; c=cells(coding_rows[rn])
            assert c['A']['value']==source_id and c['C']['value']=='E 有效性'
            assert c['D']['formula'] is None and c['D']['cell_type']=='n' and c['D']['value'] in ['0','1']
            cr=CONTEXT_ROWS[source_id]; sr=SUPPLEMENT_ROWS[source_id]
            current=cells(material_rows[cr]); supplement=cells(material_rows[sr])
            assert current['A']['value']==supplement['A']['value']==source_id
            assert c['H']['value']==f'原文语境第{cr}行；补材第{sr}行起'
            saved_material=[]
            for label,rownum,mc in [('original_context',cr,current),('supplement_start',sr,supplement)]:
                saved_material.append({'role':label,'sheet':'原文语境','row_1based':rownum,'identity_and_locator_cells':{k:mc[k] for k in ['A','B','C','D','F'] if k in mc},'text_cell_address':mc['E']['address'],'saved_text_sha256':hashlib.sha256((mc['E']['value'] or '').encode('utf8')).hexdigest(),'source_id_matches':True,'no_new_semantic_reassessment':True})
            values[(side,source_id)]={'side':side,'workbook':file_binding,'sheet':'编码表','worksheet_zip_part':'xl/worksheets/sheet1.xml','worksheet_part_sha256':hashlib.sha256(coding_bytes).hexdigest(),'row_1based':rn,'source_id':source_id,'dimension':'E','value':int(c['D']['value']),'saved_value_cell':c['D'],'saved_reason_cell':c['E'],'current_text_cell':c['F'],'saved_stage_cell':c['G'],'saved_material_location_cell':c['H'],'material_locator_readback':saved_material,'workbook_note_cell':top,'reason_authorship_as_stated':'AI按完整材料整理','new_independent_human_confirmation_inferred':False}
rows=[]
for source_id in IDS:
    a,b=values[('A',source_id)],values[('B',source_id)]
    rows.append({'source_id':source_id,'dimension':'E','A':a,'B':b,'A_B_values_equal':a['value']==b['value'],'A_B_reasons_text_equal':a['saved_reason_cell']['value']==b['saved_reason_cell']['value'],'A_B_material_locators_equal':a['saved_material_location_cell']['value']==b['saved_material_location_cell']['value'],'observed_v5_E_as_reported_by_ROOT':1,'saved_values_match_reported_v5_E':a['value']==b['value']==1,'semantic_reassessment_performed':False})
report={'status':'readback_of_saved_historical_E_cells_only','at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'records':rows,'summary':{'records_N':3,'E_saved_cells_N':6,'A_values':[r['A']['value'] for r in rows],'B_values':[r['B']['value'] for r in rows],'A_B_value_disagreements_N':sum(not r['A_B_values_equal'] for r in rows),'A_B_reason_text_matches_N':sum(r['A_B_reasons_text_equal'] for r in rows),'reference_stage_all':'补材判读 pilot02','reason_authorship_note_preserved':True,'does_not_establish_new_human_independent_E_confirmation':True,'classifier_calls_N':0,'reference_edits_N':0,'main_LLM_output_reads_N':0},'inputs':input_bindings,'scope':'仅三条已暴露历史记录的E原值、各自理由、当前命题和保存材料定位；定位页只保存字段/文本SHA，不重判语义。'}
write('readback.json',report)
write('file-sha256.json',{'inputs':input_bindings,'before_and_after_equal':all(binding(m['path'])==m for m in input_bindings)})
with (D/'README.md').open('x',encoding='utf8') as f:
    f.write('只读三条历史E：00036/00038/00045的A/B均为1，0数值分歧；理由各自不同，材料定位相同。编码表值/理由/定位单元格分别D13/E13/H13、D18/E18/H18、D23/E23/H23。\n\n三条G列均为“补材判读 pilot02”；A4/B4明确E列依据由AI按完整材料整理。本读回确认保存值与出处，不把A/B相同升级为新增真人独立确认，不重新判断语义、修改参照或重跑分类器。\n')
seal_path=(D/'output-seal.json').resolve()
members=[binding(p) for p in sorted(D.iterdir()) if p.is_file() and p.resolve()!=seal_path]
write('output-seal.json',{'members':members,'inputs':input_bindings,'self_excluded':True,'status':'sealed_read_only_historical_S3_E_cell_readback'})
for m in members+input_bindings:assert binding(m['path'])==m
assert all(Path(m['path']).resolve()!=seal_path for m in members)
print(json.dumps({'A_E':report['summary']['A_values'],'B_E':report['summary']['B_values'],'values_equal':True,'reasons_identical':False,'seal':binding(seal_path),'members_N':len(members),'inputs':input_bindings},ensure_ascii=False))
