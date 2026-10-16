"""Independently verify source object scope v2; reads no reference labels."""
from pathlib import Path
from collections import Counter
from copy import deepcopy
import datetime
import hashlib
import json
import unicodedata
import pypdfium2 as pdfium

OUT=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def normalized(text):
    # Preserve punctuation and every character; only compatibility forms and
    # extraction whitespace differ from the original candidate paragraph.
    return ''.join(unicodedata.normalize('NFKC',text).split())


def read_rows(path):
    data=[json.loads(s) for s in Path(path).read_text().splitlines() if s.strip()]
    result={r['id']:r for r in data}
    assert len(data)==len(result)==4924
    return data,result


def main():
    paths={
        'rule_v1':OUT/'rule_inputs_v31_shared.jsonl',
        'llm_v1':OUT/'effective_blind_inputs_v30.jsonl',
        'rule_v2':OUT/'rule_inputs_v31_shared_v2.jsonl',
        'llm_v2':OUT/'effective_blind_inputs_v30_v2.jsonl',
        'manifest':OUT/'renewal_object_scope_v2_manifest.json',
        'builder':OUT/'extend_renewal_object_scope_v2.py',
        'verifier':Path(__file__),
    }
    expected={'rule_v1':'40346a9b15020e866cf86474d560ff40bb6bcb6cfa855b1357d8ec3a44b2b400',
              'llm_v1':'6fa91f237c8762fb117cb6c920d6a689dd65ee35f3b938db2f0a569bf9b965b8',
              'rule_v2':'0d4e6358807c5ed38311b9a306dd539de7278e2c57de94b7a0f7730b2e06258a',
              'llm_v2':'0c05b1dbd43a74943bb1deafd26b1dbb1963bef0505dda501d83cdf1bfed9955'}
    before={str(p):sha(p) for p in paths.values()}
    for key,value in expected.items():assert sha(paths[key])==value
    rule_rows,r1=read_rows(paths['rule_v1']);_,l1=read_rows(paths['llm_v1'])
    rule_v2,r2=read_rows(paths['rule_v2']);_,l2=read_rows(paths['llm_v2'])
    assert [r['id'] for r in rule_rows]==[r['id'] for r in rule_v2]
    assert set(r1)==set(l1)==set(r2)==set(l2)
    manifest=json.loads(paths['manifest'].read_text())
    assert manifest['builder_sha256']==sha(paths['builder'])
    assert len(manifest['source_checks'])==5
    scopes={};source_checks=[]
    for entry in manifest['source_checks']:
        source,candidate_path=Path(entry['source']),Path(entry['candidate'])
        assert sha(source)==entry['source_sha256'] and sha(candidate_path)==entry['candidate_sha256']
        before[str(source)],before[str(candidate_path)]=sha(source),sha(candidate_path)
        candidate=json.loads(candidate_path.read_text())
        parent=entry['parent']
        p=[p for p in candidate['paragraphs'] if p['id']==parent['id']]
        assert len(p)==1 and p[0]==parent
        assert str(source)==(parent.get('source_file') or candidate['source'])
        assert parent['pages']==[1]
        assert '现分类制定' in parent['text'] and '谈判药品' in parent['text']
        pdf=pdfium.PdfDocument(source)
        page=pdf[0].get_textpage().get_text_range()
        assert normalized(parent['text']) in normalized(page), ('Character/punctuation difference',source)
        unit_candidates={u['id']:u for u in candidate['unit_candidates']}
        assert len(unit_candidates)==len(candidate['unit_candidates'])
        eligible_units={uid:u for uid,u in unit_candidates.items() if (u.get('source_file') or candidate['source'])==str(source)}
        year=next(y for y in (2022,2023,2024,2025,2026) if str(y) in str(source))
        image_path=OUT/f'source-object-scope-v2-visual/{year}-source-page1-top.png'
        assert image_path.is_file()
        before[str(image_path)]=sha(image_path)
        assert str(source) not in scopes
        scopes[str(source)]={'parent':parent,'candidate_path':str(candidate_path),'candidate_units':eligible_units}
        source_checks.append({'source':str(source),'source_sha256':sha(source),
            'candidate':str(candidate_path),'candidate_sha256':sha(candidate_path),
            'intro_paragraph_id':parent['id'],'intro_text':parent['text'],'pages':[1],
            'punctuation_retained_NFKC_whitespace_only_literal_match':True,
            'page1_title_and_intro_visually_reviewed':True,
            'visual_evidence':str(image_path),'visual_evidence_sha256':sha(image_path),
            'component_membership_rule':'Each frozen unit must map to a candidate unit from this exact component PDF; shared parent candidate alone is insufficient.',
            'candidate_component_unit_count':len(eligible_units)})
    changed=[];unchanged=[];member_counts=Counter();addition_counts=Counter()
    for rid in r1:
        old,new=r1[rid],r2[rid]
        inp,inp2=old['input'],new['input']
        assert old['original_id']==new['original_id']
        assert inp['unit_text']==inp2['unit_text']==l1[rid]['text']==l2[rid]['text']
        assert inp['llm_v29_shared_context']==l1[rid]['contexts']
        assert inp2['llm_v29_shared_context']==l2[rid]['contexts']
        assert not {'labels','prediction','A','C'} & (set(inp2)|set(l2[rid]))
        source=inp.get('unit_source') or inp['source']
        should_add=False
        if source in scopes:
            member_counts[source]+=1
            scope=scopes[source];parent=scope['parent']
            assert inp['candidate_file']==scope['candidate_path']
            unit=scope['candidate_units'][inp['unit_id']]
            assert unit['text']==inp['unit_text']
            assert inp.get('unit_source_sha256',inp['source_sha256'])==sha(Path(source))
            should_add=(normalized(parent['text']) not in normalized(inp['unit_text'])
                        and not any(normalized(p['text'])==normalized(parent['text']) for p in inp.get('verified_parent_context',[])))
        if not should_add:
            assert old==new and l1[rid]==l2[rid], ('Unexpected nonmember modification',rid)
            unchanged.append(rid)
            continue
        old_parents=inp.get('verified_parent_context',[])
        new_parents=inp2['verified_parent_context']
        assert len(new_parents)==len(old_parents)+1 and new_parents[:-1]==old_parents
        cert=new_parents[-1]
        parent=scopes[source]['parent']
        assert cert['paragraph_id']==parent['id'] and cert['text']==parent['text'] and cert['pages']==parent['pages']
        assert cert['source_path']==source and cert['source_sha256']==sha(Path(source))
        assert cert['candidate_path']==inp['candidate_file'] and cert['candidate_sha256']==sha(Path(inp['candidate_file']))
        assert cert['original_unit_sha256']==digest(inp['unit_text']) and cert['unit_id']==inp['unit_id']
        assert cert['text_sha256']==digest(parent['text'])
        assert cert['source_lines']==parent.get('line_ids',[])
        assert cert['repair_version']=='v31-source-object-scope'
        assert cert['verification']=={'verified':True,'method':'literal_source_scope_and_exact_component_membership'}
        assert cert['usage']=='Resolve only the explicitly stated negotiated-medicine object. Do not copy dimension labels or specific eligibility/timing conditions; local exceptions retain their own scope.'
        expected_rule,expected_llm=deepcopy(old),deepcopy(l1[rid])
        expected_rule['input'].setdefault('verified_parent_context',[]).append(deepcopy(cert))
        expected_llm['contexts'].setdefault('verified_parent_context',[]).append(deepcopy(cert))
        expected_llm['contexts'].setdefault('verified_context_certificates',{})['verified_parent_context']=deepcopy(expected_llm['contexts']['verified_parent_context'])
        expected_rule['input']['llm_v29_shared_context']=deepcopy(expected_llm['contexts'])
        assert expected_rule==new and expected_llm==l2[rid], ('Additional changes beyond object context',rid)
        addition_counts[source]+=1
        changed.append({'id':rid,'unit_id':inp['unit_id'],'source':source,'parent_id':parent['id'],
                        'original_unit_sha256':digest(inp['unit_text']),'certificate_sha256':digest(json.dumps(cert,ensure_ascii=False,sort_keys=True))})
    assert len(changed)==434 and len(unchanged)==4490
    assert {r['id'] for r in manifest['changes']}=={r['id'] for r in changed}
    assert len(manifest['changes'])==len(changed)
    for entry in source_checks:
        source=entry['source'];entry['frozen_component_members']=member_counts[source];entry['certificates_added']=addition_counts[source]
        entry['intro_or_preexisting_context_not_duplicated']=member_counts[source]-addition_counts[source]
    assert before=={p:sha(Path(p)) for p in before}, 'Read-only source changed during QA'
    report={'status':'passed','created_at':datetime.datetime.now().astimezone().isoformat(),
        'independence':'Separate verification script did not import the builder, classifier, statistics code or reference labels; rebuilt exact deltas and component membership from the actual candidate JSON and original PDFs.',
        'scope_source_count':5,'total_ids_checked':4924,'original_ids_and_unit_texts_unchanged':4924,
        'rule_and_llm_contexts_identical':4924,'certificates_added_and_bound':434,'entire_other_records_unchanged':4490,
        'normalization':'NFKC plus extraction whitespace removal only; punctuation and all language characters retained.',
        'source_checks':source_checks,'changed_units':changed,
        'usage_scope':'The verified intro resolves the negotiated-medicine object of the component. It is not a new counted unit, dimension label, inherited success claim or permission to propagate subsection timing/eligibility conditions.',
        'previous_v1_files_unchanged':True,'reference_labels_loaded':False,'source_sha256':before}
    target=OUT/'source_object_scope_v2_independent_QA.json'
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'ids_checked':4924,'certificates_added':434,'source_counts':source_checks,'output':str(target)},ensure_ascii=False))


if __name__=='__main__':main()
