"""Only source schema loading and strict contract boundary; never calls judge."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import types

HERE = Path(__file__).resolve().parent
EXPECTED_READER = 'dee2733f551797ec1485eb5316e00ffc71f9ad539c276b023dfd18d5dc08276e'
EXPECTED_DESIGN = 'ff022f5a9d803ed28befedd5a1218011ed06dfab4493c9ac2a04c4ce9f44482b'
RESULTS = []


def record(name, passed, detail=None):
    RESULTS.append({'name':name,'passed':bool(passed),'detail':detail})


def main():
    auth = json.loads((HERE.parent/'initial-authorization-and-semantic-binding.json').read_text())
    design_path = Path(auth['design_path'])
    payload = design_path.read_bytes()
    assert hashlib.sha256(payload).hexdigest() == EXPECTED_DESIGN
    design = json.loads(payload)
    raw_payload = Path(design['source']['path']).read_bytes()
    assert hashlib.sha256(raw_payload).hexdigest() == design['source']['sha256']
    originals = [json.loads(line) for line in raw_payload.splitlines() if line.strip()]
    candidate = HERE.parent/'source_packet.py'
    code = candidate.read_bytes()
    assert hashlib.sha256(code).hexdigest() == EXPECTED_READER
    assert not any(name in sys.modules for name in ('evidence','relations','dimensions'))
    reader = types.ModuleType('independent_reader_source_only')
    reader.__file__ = str(candidate)
    exec(compile(code,str(candidate),'exec'),reader.__dict__)
    assert not any(name in sys.modules for name in ('evidence','relations','dimensions'))
    loaded = reader.load_fixture(design['source']['path'], design_path)
    canonical = lambda rows: json.dumps(rows,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
    record('raw_load_returns_exact_original_rows', loaded == originals and canonical(loaded) == canonical(originals) and sum(len(row['contexts']) for row in loaded)==106 and sum(len(row['source_attachments']) for row in loaded)==18)
    record('source_field_literal_preserved', all(row['source_references'][0]['source_field']=='source_context' and 'contexts' in row and 'source_context' not in row for row in loaded))
    refused = []
    for row in loaded:
        before = copy.deepcopy(row)
        try:
            reader.semantic_unit(row)
            refused.append({'id':row['id'],'refused':False})
        except reader.UnsupportedSourceGraph as error:
            refused.append({'id':row['id'],'refused':True,'exception_type':type(error).__name__,'message':str(error),'raw_unchanged':row==before})
    record('actual_unsupported_contract_refusal', all(item.get('refused') and item.get('raw_unchanged') for item in refused) and len(refused)==2, refused)
    synthetic = {'id':'SYNTHETIC-OLD-CONTRACT','text':'人工结构控件文本','pages':[1],'contexts':[],
                 'source_ref':{'sha256':'a'*64,'source_resource_id':'SOURCE-artificial','locator':{'pages':[1]}},
                 'source_attachments':[],'source_references':[]}
    unit = reader.semantic_unit(synthetic)
    passed = all(unit[key]==synthetic[key] and unit[key] is not synthetic[key] for key in ('pages','contexts','source_ref','source_attachments','source_references')) and 'id' not in unit
    unit['source_ref']['source_resource_id']='changed-in-copy'
    record('supported_original_contract_deepcopy', passed and synthetic['source_ref']['source_resource_id']=='SOURCE-artificial')
    names = ['unknown_raw_field','unknown_context_field','unknown_structure_field','unknown_region_field','unknown_attachment_field','unknown_reference_field','nested_result_field','boolean_page','dangling_context_graph']
    for name in names:
        row = copy.deepcopy(originals[0])
        if name == 'unknown_raw_field':row['unreviewed_raw_field']=True
        elif name == 'unknown_context_field':row['contexts'][0]['unreviewed_context_field']=True
        elif name == 'unknown_structure_field':row['contexts'][0]['structure']['unreviewed_structure_field']=True
        elif name == 'unknown_region_field':
            context = next(ctx for ctx in row['contexts'] if ctx['kind']=='same_snapshot_referenced_source_paragraph')
            context['source_ref']['locator']['regions'][0]['unreviewed_region_field']=True
        elif name == 'unknown_attachment_field':row['source_attachments'][0]['unreviewed_attachment_field']=True
        elif name == 'unknown_reference_field':row['source_references'][0]['unreviewed_reference_field']=True
        elif name == 'nested_result_field':row['contexts'][0]['structure']['labels']={'S':0}
        elif name == 'boolean_page':row['pages']=[True]
        elif name == 'dangling_context_graph':
            context=next(ctx for ctx in row['contexts'] if ctx['kind']=='same_snapshot_referenced_source_paragraph')
            context['structure']['related_context_ids'].append('CTX-DANGLING-SYNTHETIC')
        try:
            reader._row(row,'independent-artificial-structure-control')
            record(name,False,'unexpected acceptance')
        except reader.PacketInterfaceError as error:
            record(name,True,{'exception_type':type(error).__name__,'message':str(error)})
    assert hashlib.sha256(candidate.read_bytes()).hexdigest() == EXPECTED_READER
    assert Path(design['source']['path']).read_bytes()==raw_payload and design_path.read_bytes()==payload
    assert not any(name in sys.modules for name in ('evidence','relations','dimensions'))
    report={'status':'independent_source_only_reader_identity_and_contract_controls','reader_sha256':EXPECTED_READER,'design_sha256':EXPECTED_DESIGN,'source_sha256':design['source']['sha256'],
            'test_n':len(RESULTS),'pass_n':sum(item['passed'] for item in RESULTS),'fail_n':sum(not item['passed'] for item in RESULTS),'cases':RESULTS,
            'semantic_coder_modules_loaded':[],'actual_prediction_or_evaluation':False,'reference_or_AB_native_opened':False,
            'test_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'predeclared_sha256':hashlib.sha256((HERE/'reader-controls-predeclared-run02.json').read_bytes()).hexdigest()}
    with (HERE/'reader-controls-result-run02.json').open('x',encoding='utf-8') as stream:
        json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print(json.dumps({key:report[key] for key in ('reader_sha256','test_n','pass_n','fail_n')}))


if __name__=='__main__':main()
