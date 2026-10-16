"""Check v3 source material and frozen certificate rejection, without labels."""
from pathlib import Path
from hashlib import sha256
from copy import deepcopy
import json,sys,unicodedata
import pypdfium2 as pdfium

HERE=Path(__file__).resolve().parent
def sha(path):return sha256(Path(path).read_bytes()).hexdigest()
def digest(text):return sha256(text.encode()).hexdigest()
def compact(text):return ''.join(c for c in unicodedata.normalize('NFKC',text) if c.isalnum())
def read_rows(name):return [json.loads(l) for l in (HERE/name).read_text().splitlines() if l.strip()]

def main():
    plan=json.loads((HERE/'safety_population_context_v3_manifest.json').read_text())
    before=plan['frozen_previous_artifacts_sha256']
    assert before=={p:sha(p) for p in before}
    rule2=read_rows('rule_inputs_v31_shared_v2.jsonl');rule3=read_rows('rule_inputs_v31_shared_v3.jsonl')
    model2=read_rows('effective_blind_inputs_v30_v2.jsonl');model3=read_rows('effective_blind_inputs_v30_v3.jsonl')
    assert len(rule2)==len(rule3)==len(model2)==len(model3)==4924
    assert sha(plan['source'])==plan['source_sha256'] and sha(plan['candidate'])==plan['candidate_sha256']
    candidate=json.loads(Path(plan['candidate']).read_text());paragraphs={p['id']:p for p in candidate['paragraphs']}
    units={u['id']:u for u in candidate['unit_candidates']}
    text=pdfium.PdfDocument(plan['source'])[5].get_textpage().get_text_range()
    page_positions=[compact(text).index(compact(paragraphs[f'p{x:04d}']['text'])) for x in range(7,15)]
    assert page_positions==sorted(page_positions)
    changes=[];certificates=0
    sys.path.insert(0,str(HERE/'rules-v31/completed-material-runtime-v2'))
    import context_validation as validator
    assert Path(validator.__file__).parent==HERE/'rules-v31/completed-material-runtime-v2'
    for old,new,lold,lnew in zip(rule2,rule3,model2,model3):
        assert old['id']==new['id']==lold['id']==lnew['id']
        assert old['original_id']==new['original_id']
        assert old['input']['unit_text']==new['input']['unit_text']==lold['text']==lnew['text']
        assert new['input']['llm_v29_shared_context']==lnew['contexts']
        validator.validate_added_parents(new['input'])
        if old==new:
            assert lold==lnew
            continue
        rec=new['input'];unit=units[rec['unit_id']]
        expected=(['p0007','p0008'] if unit['paragraph_id'] in {'p0009','p0010','p0011'}
                  else ['p0007','p0008','p0009','p0010','p0011'] if unit['paragraph_id']=='p0012' else None)
        assert expected is not None
        additions=[c for c in rec['verified_parent_context'] if c.get('material_revision')=='v3-source-safety-population-list']
        assert [c['paragraph_id'] for c in additions]==expected
        for cert in additions:
            p=paragraphs[cert['paragraph_id']]
            assert cert['text']==p['text'] and cert['pages']==p['pages']==[6] and cert['source_lines']==p['line_ids']
            assert cert['text_sha256']==digest(p['text']) and cert['original_unit_sha256']==digest(rec['unit_text'])
            assert cert['source_path']==plan['source'] and cert['source_sha256']==plan['source_sha256']
            assert cert['candidate_path']==plan['candidate'] and cert['candidate_sha256']==plan['candidate_sha256']
            assert cert['unit_id']==rec['unit_id'] and cert['target_paragraph_id']==unit['paragraph_id']
            assert compact(cert['text']) in compact(text)
        # No field except the documented paired contexts may change.
        rr=deepcopy(new);ll=deepcopy(lnew)
        rr['input']['verified_parent_context']=deepcopy(old['input'].get('verified_parent_context',[]))
        if 'verified_parent_context' not in old['input']:del rr['input']['verified_parent_context']
        rr['input']['llm_v29_shared_context']=deepcopy(old['input']['llm_v29_shared_context'])
        ll['contexts']=deepcopy(lold['contexts'])
        assert rr==old and ll==lold
        changes.append(new['id']);certificates+=len(additions)
    expected_ids=[f'RECODE25-{i:05d}' for i in range(1774,1779)]
    assert changes==expected_ids and certificates==16
    target=deepcopy(next(r['input'] for r in rule3 if r['id']=='RECODE25-01775'))
    normal=deepcopy(target);validator.validate_added_parents(normal)
    tests=[]
    corruptions=[
      ('unit_text',lambda r:r.update(unit_text=r['unit_text']+'伪造')),
      ('parent_text',lambda r:r['verified_parent_context'][-1].update(text='伪造父谓词')),
      ('parent_pages',lambda r:r['verified_parent_context'][-1].update(pages=[7])),
      ('parent_source_lines',lambda r:r['verified_parent_context'][-1].update(source_lines=['6:999'])),
      ('parent_source_hash',lambda r:r['verified_parent_context'][-1].update(source_sha256='0'*64)),
      ('parent_candidate_hash',lambda r:r['verified_parent_context'][-1].update(candidate_sha256='0'*64)),
      ('parent_unit_id',lambda r:r['verified_parent_context'][-1].update(unit_id='u99999')),
      ('parent_id',lambda r:r['verified_parent_context'][-1].update(paragraph_id='p0013')),
      ('unverified',lambda r:r['verified_parent_context'][-1]['verification'].update(verified=False)),
      ('wrong_source_path',lambda r:r['verified_parent_context'][-1].update(source_path=str(HERE/'rule_inputs_v31_shared_v2.jsonl'))),
    ]
    for name,corrupt in corruptions:
        r=deepcopy(target);corrupt(r)
        try:validator.validate_added_parents(r)
        except ValueError:tests.append({'name':name,'rejected':True})
        else:raise AssertionError(('Corrupted context accepted',name))
    assert before=={p:sha(p) for p in before}
    image=HERE/'source-list-v3-visual/CDE-safety-summary-2020-physical-page6.png'
    result={'status':'passed_source_material_and_frozen_certificate_QA','scope':'Preparation QA independent of labels/metrics; separate root/statistician source review remains separately recorded.',
       'n':4924,'rules_and_llm_contexts_identical':4924,'unit_ids_and_original_texts_unchanged':4924,
       'changed_ids':changes,'added_certificates':certificates,'source_physical_page':6,'source_printed_page':3,
       'source_pdf_sha256':sha(plan['source']),'candidate_sha256':sha(plan['candidate']),
       'source_paragraph_order_and_page_text_passed':True,'all_original_v2_and_runtime_hashes_preserved':True,
       'all_new_and_existing_parent_certificates_validated':True,'negative_tamper_tests':tests,
       'classification_or_label_data_used':False,'classification_runtime_changed':False,
       'material_manifest_path':str((HERE/'safety_population_context_v3_manifest.json').resolve()),
       'material_manifest_sha256':sha(HERE/'safety_population_context_v3_manifest.json'),
       'rule_input_sha256':sha(HERE/'rule_inputs_v31_shared_v3.jsonl'),
       'llm_input_sha256':sha(HERE/'effective_blind_inputs_v30_v3.jsonl'),
       'source_render':{'path':str(image.resolve()),'sha256':sha(image),'actually_opened_and_viewed_by_preparing_agent':True},
       'parent_agent_independent_visual_review':{'confirmed_in_parent_message':True,
          'actual_scope':'Only the rendered original PDF physical page 6 / printed page 3: p0007 report object, p0008 parent, A/B/C, p0012 anaphora, p0013 separate paragraph, p0014 new-section boundary.',
          'not_human_or_semantic_accuracy_validation':True},
       'verification_script_sha256':sha(__file__)}
    (HERE/'source_safety_population_v3_QA.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['status','changed_ids','added_certificates','rule_input_sha256','llm_input_sha256']},ensure_ascii=False))

if __name__=='__main__':main()
