"""Prepare four source-only synthetic controls before final v5 code.

No candidate import or execution; controls are hidden from the code owner.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT=Path('/PROJECT_ROOT')
BASE=ROOT/'outputs/goal-calibration-20261010'
D=Path(__file__).resolve().parent
MANUAL=BASE/'03-manual/full4481-common-release-20261010-root/manual.txt'
STANDARD_NAME='分层审评程序'
CURRENT_OPERATIVE='申请人应当核验分层审评程序的纳入条件；不符合纳入条件的，应当及时终止该药物的程序资格。'
CURRENT_PAPERWORK='已纳入分层审评程序的申请人，应将申报资料压缩包按程序名称命名后上传。'

def canonical(v):
    return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'))

def sha(b): return hashlib.sha256(b).hexdigest()
def bind(p):
    b=p.read_bytes()
    return {'path':str(p),'bytes':len(b),'sha256':sha(b)}
def write(name,v):
    p=D/name
    if p.exists(): raise RuntimeError('Preparation is immutable once written: '+str(p))
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def fixture(case_number,current,complete_boundary):
    cid='SYNTH-FINITE-'+str(case_number).zfill(2)
    lines=['分层审评程序（试行）\n',
        '本程序用于药物临床试验申请的审评安排。\n',
        '一、工作程序\n',current+'\n',
        '二、适用范围和适用条件\n',
        '（一）适用范围\n',
        '药物临床试验期间，申请人可以申请适用分层审评程序。\n',
        '（二）适用条件\n',
        '申请适用分层审评程序的药物，应当同时满足以下条件：\n',
        '1.申请人应当提供该药物治疗效果的比较证据。\n',
        '2.申请人应当评估该药物重大不良反应的风险，并提出风险控制措施。\n']
    if complete_boundary:
        lines+=['三、其他事项\n','申请材料的上传时间另行告知。\n']
    text=''.join(lines);raw=text.encode('utf8');source_sha=sha(raw)
    path=D/'source-texts'/(cid+'.txt');path.parent.mkdir(parents=True,exist_ok=True)
    assert not path.exists();path.write_bytes(raw)
    offsets=[0]
    for line in lines:offsets.append(offsets[-1]+len(line))
    def ref(line):
        start,end=offsets[line-1],offsets[line]
        return {'sha256':source_sha,'source_resource_id':'SOURCE-'+source_sha,
            'locator':{'source_lines':[line],'paragraph_id':'synp'+str(line).zfill(4),
                'component_id':'synthetic-programme-1','unicode_code_point_interval_half_open':[start,end]}}
    scopeid='CTX-'+cid+'-SCOPE'
    currentref=ref(4)
    contexts=[{'context_id':'CTX-'+cid+'-CURRENT','kind':'paragraph','text':current,
        'source_document':'SOURCE-'+source_sha,'source_ref':currentref,
        'structure':{'paragraph_id':'synp0004','component_id':'synthetic-programme-1','source_lines':[4]}},
        {'context_id':'CTX-'+cid+'-HEADING','kind':'heading','text':'一、工作程序',
         'source_document':'SOURCE-'+source_sha,'source_ref':ref(3),
         'structure':{'paragraph_id':'synp0003','component_id':'synthetic-programme-1','source_lines':[3]}},
        {'context_id':scopeid,'kind':'source_paragraph','text':lines[6].rstrip('\n'),
         'source_document':'SOURCE-'+source_sha,'source_ref':ref(7),
         'structure':{'paragraph_id':'synp0007','component_id':'synthetic-programme-1','source_lines':[7]}}]
    neutral_relation={'relation_id':'NR-'+cid+'-COMPONENT','kind':'component_identity',
        'unit_id':cid,'related_context_ids':[scopeid]}
    contexts.append({'context_id':'CTX-'+cid+'-STRUCTURE','kind':'structural_relation',
        'source_ref':{'sha256':source_sha,'source_resource_id':'SOURCE-'+source_sha,
            'locator':{'unit_id':cid,'related_context_ids':[scopeid]}},
        'structure':{'unit_id':cid,'related_context_ids':[scopeid]}})
    leaves=[]
    for first,last in [(1,10),(11,len(lines))]:
        a,b=offsets[first-1],offsets[last]
        quote=text[a:b];rid='SOURCE-TEXT-'+source_sha+'-L'+str(first).zfill(4)+'-L'+str(last).zfill(4)
        locator={'coordinate_basis':'raw strict UTF8 synthetic frozen fragment; no normalization',
            'snapshot_absolute_path':str(path),'original_archive_absolute_path':str(path),
            'snapshot_sha256':source_sha,'physical_line_range_1based_inclusive':[first,last],
            'unicode_code_point_interval_half_open':[a,b],
            'utf8_byte_interval_half_open':[len(text[:a].encode()),len(text[:b].encode())],
            'physical_pages':None,'PDF_page_or_pixel_locator_available':False}
        leaves.append({'kind':'verbatim_UTF8_snapshot_text','source_resource_id':rid,
            'source_sha256':source_sha,'source_version_id':'SOURCEVERSION-'+source_sha,
            'text':quote,'text_unicode_code_points':len(quote),'text_utf8_bytes':len(quote.encode()),
            'text_utf8_sha256':sha(quote.encode()),'locator':locator})
    bundle={'common_source_bundle_version':{'version':'synthetic-natural-source-only-v1',
                'status':'synthetic_fragment_not_actual_policy_or_original_EOF_completeness_attestation'},
        'source_record':{'id':cid,'text':current,'source_ref':currentref,'pages':[],
            'contexts':contexts,'source_relations':[neutral_relation]},
        'source_documents':[{'source_resource_id':'SOURCE-'+source_sha,'source_sha256':source_sha,
            'snapshot':str(path),'document_title':'Synthetic controlled source fragment',
            'representation':'Frozen synthetic UTF8 fragment; file end alone does not certify normative document end'}],
        'explicit_or_primary_source_resources':[],
        'preserved_historical_neutral_source_supplements':[],
        'source_full_text_resources':leaves,'source_asset_locations':[],
        'source_locator_bases':[],'source_reference_index':[],
        'source_provenance_addenda':[{'identity':'New synthetic source authored for independent finite-source control',
            'not_actual_policy':True,'no_candidate_relation_or_closure_status_injected':True}]}
    packet={'output_id':cid,'source_id':cid,'packet_version':'synthetic-source-only-control',
        'source_bundle':bundle,'source_bundle_sha256':sha(canonical(bundle).encode()),'verified_asset_files':[]}
    write('source-packets/'+cid+'.json',packet)
    # Mechanical source-binding checks only; not a source adapter or rule run.
    validation=[]
    for i,leaf in enumerate(leaves):
        loc=leaf['locator'];a,b=loc['unicode_code_point_interval_half_open'];u,v=loc['utf8_byte_interval_half_open']
        first,last=loc['physical_line_range_1based_inclusive']
        assert leaf['text']==text[a:b]==''.join(lines[first-1:last])
        assert leaf['text'].encode()==raw[u:v] and sha(raw[u:v])==leaf['text_utf8_sha256']
        validation.append({'pointer':'/source_full_text_resources/'+str(i),
            'literal_text_bytes_line_and_codepoint_ranges_verified':True,'resource_id':leaf['source_resource_id']})
    assert ''.join(x['text'] for x in leaves)==text
    for ctx in contexts[:3]:
        loc=ctx['source_ref']['locator'];a,b=loc['unicode_code_point_interval_half_open']
        assert text[a:b].rstrip('\n')==ctx['text']
    return {'case_id':cid,'packet_binding':bind(D/'source-packets'/(cid+'.json')),
        'source_text_binding':bind(path),'current_text':current,
        'source_bundle_sha256':packet['source_bundle_sha256'],'mechanical_source_checks':validation}

def main():
    if (D/'preparation-seal.json').exists(): raise RuntimeError('Already sealed')
    mb=bind(MANUAL)
    assert mb['sha256']=='5ea7ab74d30fb79c4cbd1d7d6b2ae40c4f52a52360075f3552199de949f9cc7b'
    # Two independent policy-semantic pairs; no candidate implementation or
    # owner controls read, no generated relation/resolution/units injected.
    configs=[(1,CURRENT_OPERATIVE,True,1,'P1','Actual operative qualification norm with complete same-version safety condition and next actual section'),
        (2,CURRENT_OPERATIVE,False,None,'P1','Same operative qualification norm and supplied conditions, but fragment ends before the actual next normative boundary; preserve missing closure as NULL'),
        (3,CURRENT_OPERATIVE,True,1,'P2','Actual criterion verification and qualification consequence justify finite standard consumption'),
        (4,CURRENT_PAPERWORK,True,0,'P2','Existing programme identity and naming/upload obligation do not operate the substantive qualification standard; no safety inheritance from adjacent conditions')]
    fixed=[];source_checks=[]
    for number,current,complete,value,pair,basis in configs:
        case=fixture(number,current,complete);source_checks.append(case)
        fixed.append({'case_id':case['case_id'],'pair':pair,'dimension':'S','expected_value':value,
            'expected_basis':basis,'manual_sha256':mb['sha256'],
            'manual_lines':[9,29,31,40,41,44],
            'source_packet':case['packet_binding'],'source_text':case['source_text_binding'],
            'other_dimension_expectations':None,'fixture_identity':'new synthetic controlled text, not a real policy ID or human label',
            'candidate_read_before_preparation':False,'candidate_execution_before_final_binding':False})
    write('coordinator-private/fixed-controls-before-final-code.json',fixed)
    write('source-byte-verification.json',source_checks)
    mlines=MANUAL.read_text().splitlines(keepends=True)
    write('coordinator-private/manual-basis-quotes.json',[{'source':mb,'line_1based':i,'quote':mlines[i-1]} for i in [9,29,31,40,41,44]])
    write('execution-contract.json',{'status':'PREPARED_WAIT_ROOT_FINAL_V5_BINDING',
        'case_count':4,'synthetic_only':True,'actual_policy_IDs_read_or_added':0,
        'dimensions_with_fixed_expectations':['S'],'each_case_max_calls':{'semantic_unit':1,'RelationView':1,'judge':1},
        'candidate_algorithm_final_binding':None,'ROOT_future_execution_authorization':None,
        'current_adapter_RelationView_judge_calls':0,'owner_development_controls_read':0,'v5_unfrozen_code_read':0,
        'source_only_rule_input_fields':'exact source_bundle from frozen packet; expected labels remain separate',
        'forbidden_injections':['resolved dependency status','SE_scope_verified','closure_proof','generated units'],
        'NULLs_failures_and_first_outputs_must_remain':True,'retry_or_input_repair_allowed':False,
        'formal_statistics_or_new_real_human_results':0,
        'disclosure':'Only preparation case count and seal SHA are reported to ROOT/code owner before final code freeze'})
    write('input-bindings.json',[mb])
    members=[bind(p) for p in sorted(D.rglob('*')) if p.is_file() and p.name!='preparation-seal.json']
    value={'status':'fixed_independent_source_only_controls_before_final_v5_code',
        'case_count':4,'pair_count':2,'identity':'nonhuman independent synthetic preparation',
        'members':members,'inputs':[mb],'candidate_calls':0,'actual_policy_IDs_added':0,
        'new_real_human_results':0,'self_excluded':True}
    write('preparation-seal.json',value)
    for item in members+[mb]: assert bind(Path(item['path']))==item
    print(json.dumps({'case_count':4,'preparation_seal':bind(D/'preparation-seal.json'),
        'member_count':len(members),'readback':'all_equal','candidate_calls':0},ensure_ascii=False))

if __name__=='__main__':main()
