"""Read exactly three historical S cells and seal a plan; never classify."""
import hashlib
import json
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path('/PROJECT_ROOT')
BASE=ROOT/'outputs/goal-calibration-20261010'
D=Path(__file__).resolve().parent
PARENT=D.parent
PAIRS=[('RECODE25-00036',12),('RECODE25-00038',17),('RECODE25-00045',22)]
MANUAL=BASE/'03-manual/full4481-common-release-20261010-root/manual.txt'
NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
RN='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'

def bind(p):
    raw=p.read_bytes()
    return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

def write(name,v):
    p=D/name
    if p.exists(): raise RuntimeError('Preserve previous file: '+str(p))
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def cells(path):
    wanted={col+str(row) for _,row in PAIRS for col in ['A','C','D','E','F']}
    with zipfile.ZipFile(path) as z:
        strings=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            strings=[''.join(x.itertext()) for x in ET.fromstring(z.read('xl/sharedStrings.xml'))]
        wb=ET.fromstring(z.read('xl/workbook.xml'))
        rels={x.get('Id'):x.get('Target') for x in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
        ss=[x for x in wb.find('m:sheets',NS) if x.get('name')=='编码表']
        assert len(ss)==1
        target=rels[ss[0].get(RN)]
        part=target.lstrip('/') if target.startswith('/') else 'xl/'+target
        raw=z.read(part)
        found={}
        for c in ET.fromstring(raw).findall('.//m:c',NS):
            address=c.get('r')
            if address not in wanted: continue
            v=c.find('m:v',NS)
            text=v.text if v is not None else None
            kind=c.get('t')
            value=text
            if kind=='s': value=strings[int(text)]
            elif kind=='inlineStr': value=''.join(c.find('m:is',NS).itertext())
            elif kind=='n' and text is not None:
                assert text in ['0','1'] if address.startswith('D') else True
                value=int(text) if text in ['0','1'] else float(text)
            found[address]={'address':address,'raw_cell_type':kind,'raw_value':text,'value':value,
                'formula':c.findtext('m:f',namespaces=NS)}
        assert set(found)==wanted
        return {'file':bind(path),'sheet':'编码表','worksheet_zip_part':part,
            'worksheet_part_sha256':hashlib.sha256(raw).hexdigest(),'cells':found,
            'selected_range_only':True,'other_worksheet_cells_admitted':0}

def main():
    parentseal=PARENT/'output-seal.json'
    assert bind(parentseal)['sha256']=='0e4d70ac1bc0d78e54b302e87a3123ade68edef888000df6446cf1232ce9f156'
    report=json.loads((PARENT/'interface-findings.json').read_text())
    assert [x['record_id'] for x in report]==[rid for rid,_ in PAIRS]
    paths={'before_targeted_human_followup':BASE/'00-baseline/20261010-pre-targeted-human-followup-edits',
           'after_user_confirmed_four_item_followup':BASE/'09-delivery/agent-review-20261010/真人4项复核后-v2'}
    archives=[]
    for stage,directory in paths.items():
        for coder in ['A','B']:
            p=directory/('编码复核表-'+coder+'.xlsx')
            data=cells(p)
            data.update({'historical_stage':stage,'coder':coder,
                'identity':'Existing archive; not a new independently submitted human result'})
            for rid,row in PAIRS:
                assert data['cells']['A'+str(row)]['value']==rid
                assert data['cells']['C'+str(row)]['value']=='S 安全性'
                assert data['cells']['D'+str(row)]['formula'] is None
                expected_text=next(x['current']['current_canonical_text'] for x in report if x['record_id']==rid)
                assert data['cells']['F'+str(row)]['value']==expected_text
                if stage=='after_user_confirmed_four_item_followup':
                    assert data['cells']['D'+str(row)]['value']==1
            archives.append(data)
    doc=BASE/'09-delivery/agent-review-20261010/局部补充核验四项.txt'
    doclines=doc.read_text().splitlines(keepends=True)
    excerpt=[]
    for rid,row,a,b in [('RECODE25-00036',12,9,11),('RECODE25-00038',17,13,15),('RECODE25-00045',22,17,19)]:
        q=''.join(doclines[a-1:b])
        assert rid in q and 'D'+str(row) in q
        excerpt.append({'record_id':rid,'source':bind(doc),'line_range_1based_inclusive':[a,b],
            'quote':q,'quote_sha256':hashlib.sha256(q.encode()).hexdigest()})
    manual=bind(MANUAL)
    assert manual['sha256'].startswith('5ea7ab74')
    mlines=MANUAL.read_text().splitlines(keepends=True)
    mquotes=[{'source':manual,'line_1based':i,'quote':mlines[i-1],
        'quote_sha256':hashlib.sha256(mlines[i-1].encode()).hexdigest()} for i in [9,29,31,40,41,44,46]]
    fixed=[]
    inputbindings=[bind(parentseal),bind(PARENT/'adapter-execution-receipts.json'),
        bind(PARENT/'source-quotes-verified.json'),bind(PARENT/'interface-findings.json'),manual,bind(doc)]
    inputbindings.extend(x['file'] for x in archives)
    for rid,row in PAIRS:
        packet=BASE/'03-manual/common-material-projection-candidate-root/packets'/(rid+'.json')
        raw=packet.read_bytes()
        target=D/'frozen-source-packets'/(rid+'.json')
        target.parent.mkdir(parents=True,exist_ok=True)
        assert not target.exists()
        target.write_bytes(raw)
        assert target.read_bytes()==raw
        inputbindings.append(bind(packet))
        sourcefind=next(x for x in report if x['record_id']==rid)
        decisions=[]
        for archive in archives:
            decisions.append({'archive':archive['file'],'sheet':archive['sheet'],'coder':archive['coder'],
                'historical_stage':archive['historical_stage'],'id_cell':'A'+str(row),
                'dimension_cell':'C'+str(row),'value_cell':'D'+str(row),'reason_cell':'E'+str(row),
                'current_cell':'F'+str(row),'value':archive['cells']['D'+str(row)]['value'],
                'reason':archive['cells']['E'+str(row)]['value']})
        fixed.append({'case_id':rid+'-historical-S-development','record_id':rid,'dimension':'S',
            'expected_value':1,'expected_value_identity':'historical user-confirmed development adjudication',
            'expectation_basis':'ROOT explicitly relayed the human user confirmation; selected post-confirmation A/B archive values and written acceptance record independently located. A/B agreement alone does not define reference.',
            'historical_pre_followup_and_followup_archive_cells':decisions,
            'acceptance_document_quote':next(x for x in excerpt if x['record_id']==rid),
            'frozen_source_packet_copy':bind(target),'exact_upstream_source_packet':bind(packet),
            'source_bundle_sha256':sourcefind['raw_source_bundle_canonical_sha256'],
            'current_and_original_binding':sourcefind['current'],
            'source_interface_observation':{
                'six_old_new_adapter_identities_retained':True,'actual_pure_adapter_calls_before_plan':7,
                'old_new_bundle_equal':True,'complete_literal_standard_and_next_boundary_visible':True,
                'structured_reference_and_member_closure_not_supplied':True},
            'other_dimension_expectations':None,'formal_gold_standard':False,
            'new_real_human_result':False,'executed':False,'actual_rule_value':None})
    write('historical-human-archive-cells.json',archives)
    write('manual-basis-quotes.json',mquotes)
    write('fixed-S3-before-execution.json',fixed)
    write('input-bindings.json',inputbindings)
    write('execution-plan.json',{'status':'WAIT_ROOT_V4_FINAL_BINDING_NO_CLASSIFICATION_EXECUTION',
        'owner_identity':'GPT-6.1 Sol nonhuman source-only historical development check',
        'case_ids':[x['case_id'] for x in fixed],'dimensions_with_fixed_expectations':['S'],
        'expected_cases':3,'per_case_future_execution_limit':1,
        'required_final_rule_algorithm_binding':None,
        'required_ROOT_explicit_execution_authorization':None,
        'known_v3_status':'Do not execute: ROOT reported integer article metadata construction failure and prepares separate v4 repair',
        'future_sequence':[
            'ROOT supplies final v4 exact seal and code binding after independent controls',
            'Verify that binding, this plan seal, manual and exact three source-only packet bytes',
            'Execute each of the three packets once; keep expectations separate from consumer input',
            'Save all decisions/receipts/full trace/errors without changing the fixed S expectations',
            'Compare only S as historical development checks; preserve NULL, failures and disagreements; no other-dimensional expected labels',
            'Write any future execution outside sealed plan members; no formal accuracy/statistics or human-result claims'],
        'judge_calls_now':0,'RelationView_calls_now':0,'machine_output_reads_now':0,
        'new_human_results':0,'new_actual_policy_ids':0,
        'archive_locator_probe_caveat':'First read-only exploratory worksheet probe checked the same row addresses on both sheets and displayed non-target RECODE25-00005 structural metadata on the context sheet. No non-target current policy prose, dimension decision or expectation was admitted. The durable extraction selects only 编码表 and exact three rows.'})
    for item in inputbindings:
        assert bind(Path(item['path']))==item
    print(json.dumps({'fixed_S_expectations':3,'archive_workbooks':4,'selected_historical_cells':60,
        'new_human_results':0,'judge_calls':0,'ROOT_v4_binding':None},ensure_ascii=False))

if __name__=='__main__': main()
