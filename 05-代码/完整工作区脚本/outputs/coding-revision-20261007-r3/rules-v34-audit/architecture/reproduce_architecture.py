"""Small end-to-end semantic representation controls; no reference labels."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
FROZEN = HERE.parents[1] / 'rules-v33' / 'runtime'


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def payload(value):
    return sha(json.dumps(value, ensure_ascii=False, sort_keys=True))


def fixture(name, current, children):
    folder = HERE / 'constructed_source_controls' / name
    folder.mkdir(parents=True, exist_ok=True)
    source, cp = folder/'source.txt', folder/'candidate.json'
    paragraphs = [{'id':f'p{i}', 'text':t, 'source_lines':[f'L{i+1}']}
                  for i,t in enumerate([current,*children,'下一节：其他事务'])]
    source.write_text('\n'.join(p['text'] for p in paragraphs))
    cp.write_text(json.dumps({'paragraphs':paragraphs,
                              'unit_candidates':[{'id':'unit','text':current,'paragraph_id':'p0'}]},ensure_ascii=False))
    sh, ch = sha(source.read_text()), sha(cp.read_text())
    contexts = [{'paragraph_id':p['id'],'text':p['text'],'pages':[],
                 'source_lines':p['source_lines'],'source_path':str(source),
                 'source_sha256':sh,'candidate_path':str(cp),'candidate_sha256':ch,
                 'verification':{'verified':True,'method':'constructed_literal_control'}}
                for p in paragraphs[:-1]]
    record = {'unit_text':current,'source':str(source),'source_sha256':sh,
              'unit_source':str(source),'unit_source_sha256':sh,
              'candidate_file':str(cp),'candidate_sha256':ch,'unit_id':'unit',
              'paragraph_context':[], 'llm_v29_shared_context':{}}
    cert = {'original_unit_sha256':sha(current),'source_sha256':sh,'contexts':contexts,
            'contexts_sha256':payload(contexts),'repair_status':'supplemented',
            'unresolved_material_gaps':[],'source_files_hash_verified':True,
            'structure_boundary':{'first_paragraph':contexts[0]['paragraph_id'],
                                  'last_paragraph':contexts[-1]['paragraph_id'],
                                  'all_paragraphs_in_interval_included':True,
                                  'next_paragraph_id':paragraphs[-1]['id'],
                                  'next_paragraph_text':paragraphs[-1]['text']}}
    return record, cert


def engine(record, version):
    module_path = FROZEN if version == 'v33' else HERE/'runtime'
    code = "import sys,json;sys.path.insert(0,sys.argv[1]);import policy_coding_v27 as c\ntry:\n r=c.code_unit(json.load(sys.stdin)); print(json.dumps({'judgement_status':r['judgement_status'],'labels':r['labels'],'typed_roles':[x['role'] for x in r.get('typed_contexts_v34',[])],'consumed':r.get('source_field_consumption_v34',[])},ensure_ascii=False))\nexcept Exception as e: print(json.dumps({'error':str(e)},ensure_ascii=False))"
    p = subprocess.run([sys.executable,'-B','-c',code,str(module_path)],
                       input=json.dumps(record,ensure_ascii=False),text=True,capture_output=True,check=True)
    return json.loads(p.stdout)


def main():
    outputs = []
    missing_following = []
    for text in ('药品的临床评价应当包括以下内容：', '申请人应当提交以下药物评价资料：'):
        result = engine({'unit_text':text,'paragraph_context':[],
                         'source_sha256':'constructed-control'},'v33')
        assert result['judgement_status'] != 'undetermined' and not any(result['labels'].values())
        fixed = engine({'unit_text':text,'paragraph_context':[],
                        'source_sha256':'constructed-control'},'v34')
        assert fixed['judgement_status'] == 'undetermined'
        missing_following.append({'text':text,'v33':result,
                                  'candidate':fixed,
                                  'manual_required_status':'undetermined',
                                  'candidate_repair_implemented':True})
    for text in ('药品评价委员会的职责如下：', '药品评价资料下载地址如下：',
                 '本院药品评价工作有关事项通知如下：',
                 '现就开展药品使用监测和临床综合评价有关事项通知如下：'):
        result = engine({'unit_text':text,'paragraph_context':[],
                         'source_sha256':'constructed-control'},'v34')
        assert result['judgement_status'] != 'undetermined'
        outputs.append({'control':'self_sufficient_organization_or_navigation_lead','text':text,'candidate':result})
    r,c=fixture('evaluation_complete','药品的临床评价应当包括以下内容：',['一是评价该药物疗效。'])
    r['complete_following_list_v11']=c;r['llm_v29_shared_context']['complete_following_list_v11']=copy.deepcopy(c)
    fixed=engine(r,'v34');assert fixed['judgement_status'] != 'undetermined'
    outputs.append({'control':'evaluation_lead_with_authenticated_complete_material_not_pending','candidate':fixed})
    r,c = fixture('numeric', '药品必须符合以下条件：', ['1.用于治疗严重疾病。'])
    old = copy.deepcopy(r);old['verified_following_list_v27']=c
    new = copy.deepcopy(r);new['complete_following_list_v11']=c
    new['llm_v29_shared_context']['complete_following_list_v11']=copy.deepcopy(c)
    a,b,d = engine(old,'v33'),engine(new,'v33'),engine(new,'v34')
    assert a['judgement_status'] != 'undetermined' and b['judgement_status'] == 'undetermined'
    assert d['judgement_status'] != 'undetermined'
    outputs.append({'control':'equivalent_certificate_field_representation','v33_legacy':a,'v33_v11':b,'candidate_v11':d})
    r,c = fixture('non_numeric', '药品必须符合以下条件：', ['一是用于治疗严重疾病。'])
    r['complete_following_list_v11']=c;r['llm_v29_shared_context']['complete_following_list_v11']=copy.deepcopy(c)
    a,b = engine(r,'v33'),engine(r,'v34')
    assert a['judgement_status'] == 'undetermined' and b['judgement_status'] != 'undetermined'
    outputs.append({'control':'complete_following_non_v27_marker','v33':a,'candidate':b})
    bad = copy.deepcopy(r);bad['complete_following_list_v11']['structure_boundary']['next_paragraph_text']='伪造边界'
    bad['llm_v29_shared_context']['complete_following_list_v11']=copy.deepcopy(bad['complete_following_list_v11'])
    err = engine(bad,'v34');assert 'error' in err
    outputs.append({'control':'tampered_following_boundary_rejected','candidate':err})
    for name,text,role in [
        ('administrative','符合第二条申报条件的药品，应通过平台提交申请。','current_administrative_eligibility_reference'),
        ('substantive','应按照第二条评价该药物的临床优势。','current_substantive_condition_reference'),
        ('actual_exit','符合第二条退出条件的药品应予以调出目录。','current_substantive_condition_reference'),
        ('exit_application_route','符合第二条退出条件的药品可以通过平台提交申请。','current_administrative_eligibility_reference'),
        ('preview','药品申报指南可参见第二条。','navigation_preview_only')]:
        r,c=fixture(name,text,['第二条 评价药物疗效并报告药物不良反应。'])
        refs=[{'reference_address':'第二条','contexts':[c['contexts'][1]],'selection':'complete_exact_cited_interval_only'}]
        value={'repair_version':'v12-source-explicit-qualification-reference','current_unit_sha256':sha(text),
               'current_unit_id':r['unit_id'],'current_unit_source_path':r['unit_source'],
               'current_unit_source_sha256':r['unit_source_sha256'],
               'current_unit_candidate_path':r['candidate_file'],'current_unit_candidate_sha256':r['candidate_sha256'],
               'references':refs,'references_sha256':payload(refs)}
        r['llm_v29_shared_context']['explicitly_cited_qualifications_v12']=value
        a,b=engine(r,'v33'),engine(r,'v34')
        assert role in b['typed_roles']
        if role!='current_substantive_condition_reference':assert a['labels']==b['labels']
        outputs.append({'control':name+'_reference_role_no_label_copy','v33':a,'candidate':b})
        if name=='administrative':
            bad=copy.deepcopy(r);bad['llm_v29_shared_context']['explicitly_cited_qualifications_v12']['references'][0]['contexts'][0]['text']='第二条 伪造要求。'
            err=engine(bad,'v34');assert 'error' in err
            outputs.append({'control':'tampered_reference_payload_rejected','candidate':err})
    report={'scope':'constructed interface controls only, not corpus accuracy or reliability',
            'controls':outputs,'all_controls_passed':True,
            'additional_confirmed_missing_material_gate_bug':missing_following}
    (HERE/'reproduction_results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'controls':len(outputs),'all_passed':True},ensure_ascii=False))


if __name__=='__main__':main()
