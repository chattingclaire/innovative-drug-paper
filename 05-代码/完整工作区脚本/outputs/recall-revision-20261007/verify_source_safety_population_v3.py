"""Independently reconstruct v3 list/anaphora material deltas, without labels."""
from pathlib import Path
from copy import deepcopy
import datetime
import hashlib
import json
import unicodedata
import pypdfium2 as pdfium

OUT=Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(value):return hashlib.sha256(value.encode()).hexdigest()
def literal(value):return ''.join(unicodedata.normalize('NFKC',value).split())


def rows(path):
    values=[json.loads(s) for s in Path(path).read_text().splitlines() if s.strip()]
    result={v['id']:v for v in values}
    assert len(values)==len(result)==4924
    return values,result


def main():
    paths={'old_rules':OUT/'rule_inputs_v31_shared_v2.jsonl',
           'old_llm':OUT/'effective_blind_inputs_v30_v2.jsonl',
           'new_rules':OUT/'rule_inputs_v31_shared_v3.jsonl',
           'new_llm':OUT/'effective_blind_inputs_v30_v3.jsonl',
           'manifest':OUT/'safety_population_context_v3_manifest.json',
           'preparation_QA':OUT/'source_safety_population_v3_QA.json',
           'source_image':OUT/'source-list-v3-visual/CDE-safety-summary-2020-physical-page6.png',
           'verifier':Path(__file__)}
    expected={'old_rules':'0d4e6358807c5ed38311b9a306dd539de7278e2c57de94b7a0f7730b2e06258a',
              'old_llm':'0c05b1dbd43a74943bb1deafd26b1dbb1963bef0505dda501d83cdf1bfed9955',
              'new_rules':'ef21e0bd5d07007bc7494ce922987bf55527d64934464406c1b2ef300f86f792',
              'new_llm':'7592b73780f2f660c2285b83fe2952921cc4ae1972e31e67a5ecb3fa1e57b5f6'}
    before={str(p.resolve()):sha(p) for p in paths.values()}
    for key,value in expected.items():assert sha(paths[key])==value
    old_list,old=rows(paths['old_rules']);new_list,new=rows(paths['new_rules'])
    _,llm_old=rows(paths['old_llm']);_,llm_new=rows(paths['new_llm'])
    assert [r['id'] for r in old_list]==[r['id'] for r in new_list]
    assert set(old)==set(new)==set(llm_old)==set(llm_new)
    manifest=json.loads(paths['manifest'].read_text())
    source=Path(manifest['source']);candidate_path=Path(manifest['candidate'])
    assert sha(source)==manifest['source_sha256']=='d003d23a67bd150f7fcebb6e1268b437129cee4cee645cb00586cb8f482291b2'
    assert sha(candidate_path)==manifest['candidate_sha256']=='2c661d2fbb6b40e17838d35e3dd81f1027997cd4d056e95a9fefc2f2ad7522fe'
    before[str(source)],before[str(candidate_path)]=sha(source),sha(candidate_path)
    candidate=json.loads(candidate_path.read_text())
    assert candidate['source']==str(source)
    paragraphs={p['id']:p for p in candidate['paragraphs']}
    unit_candidates={u['id']:u for u in candidate['unit_candidates']}
    assert len(paragraphs)==len(candidate['paragraphs'])
    assert len(unit_candidates)==len(candidate['unit_candidates'])
    page=pdfium.PdfDocument(source)[5].get_textpage().get_text_range()
    normalized_page=literal(page);positions=[]
    source_paragraphs=[]
    for pid in [f'p{i:04d}' for i in range(7,15)]:
        paragraph=paragraphs[pid]
        assert paragraph['pages']==[6]
        assert literal(paragraph['text']) in normalized_page, ('Literal mismatch with punctuation retained',pid)
        position=normalized_page.index(literal(paragraph['text']));positions.append(position)
        source_paragraphs.append({'id':pid,'text':paragraph['text'],'pages':[6],
                                  'line_ids':paragraph['line_ids'],'literal_pdf_match':True})
    assert positions==sorted(positions)
    assert paragraphs['p0007']['text']=='建议基于以上数据来源,撰写申报资料的安全性内容,为产品说明书的撰写提供参考。'
    assert paragraphs['p0008']['text']=='总结报告的人群定义有如下建议:'
    assert [paragraphs[p]['text'].split('、')[0] for p in ('p0009','p0010','p0011')]==['A','B','C']
    assert paragraphs['p0012']['text'].startswith('在上述人群定义原则下,')
    assert paragraphs['p0013']['text'].startswith('考虑部分抗肿瘤创新药需要联合用药,')
    assert paragraphs['p0014']['type']=='heading_candidate'
    membership={}
    for uid,unit in unit_candidates.items():
        if unit.get('paragraph_id') in ('p0009','p0010','p0011'):
            membership[uid]=['p0007','p0008']
        elif unit.get('paragraph_id')=='p0012':
            membership[uid]=['p0007','p0008','p0009','p0010','p0011']
    assert len(membership)==5
    changes=[];unchanged=[];certificate_count=0
    for rid,row in old.items():
        current=new[rid];inp=row['input'];updated=current['input']
        assert row['original_id']==current['original_id']
        assert inp['unit_text']==updated['unit_text']==llm_old[rid]['text']==llm_new[rid]['text']
        assert inp['llm_v29_shared_context']==llm_old[rid]['contexts']
        assert updated['llm_v29_shared_context']==llm_new[rid]['contexts']
        assert not {'labels','prediction','A','C'} & (set(updated)|set(llm_new[rid]))
        eligible=inp['candidate_file']==str(candidate_path) and inp['unit_id'] in membership
        if not eligible:
            assert row==current and llm_old[rid]==llm_new[rid], ('Nonmember changed',rid)
            unchanged.append(rid);continue
        assert (inp.get('unit_source') or inp['source'])==str(source)
        unit=unit_candidates[inp['unit_id']]
        assert unit['text']==inp['unit_text']
        assert updated['verified_parent_context'][:len(inp.get('verified_parent_context',[]))]==inp.get('verified_parent_context',[])
        added=updated['verified_parent_context'][len(inp.get('verified_parent_context',[])):]
        assert [a['paragraph_id'] for a in added]==membership[inp['unit_id']]
        rebuilt_rule,rebuilt_llm=deepcopy(row),deepcopy(llm_old[rid])
        for cert in added:
            paragraph=paragraphs[cert['paragraph_id']]
            assert set(cert)=={'paragraph_id','text','pages','source_lines','text_sha256','source_path','source_sha256',
                              'candidate_path','candidate_sha256','original_unit_sha256','unit_id','repair_version',
                              'verification','target_paragraph_id','material_revision','usage'}
            assert cert['text']==paragraph['text'] and cert['pages']==[6] and cert['source_lines']==paragraph['line_ids']
            assert cert['text_sha256']==digest(paragraph['text'])
            assert cert['source_path']==str(source) and cert['source_sha256']==sha(source)
            assert cert['candidate_path']==str(candidate_path) and cert['candidate_sha256']==sha(candidate_path)
            assert cert['unit_id']==inp['unit_id'] and cert['original_unit_sha256']==digest(inp['unit_text'])
            assert cert['target_paragraph_id']==unit['paragraph_id']
            assert cert['repair_version']=='v31-source-list-predicate'
            assert cert['material_revision']=='v3-source-safety-population-list'
            assert cert['verification']=={'verified':True,'method':'literal_source_list_membership_and_explicit_anaphora'}
            assert 'do not' in cert['usage'] and 'transfer labels' in cert['usage']
            rebuilt_rule['input'].setdefault('verified_parent_context',[]).append(deepcopy(cert))
            rebuilt_llm['contexts'].setdefault('verified_parent_context',[]).append(deepcopy(cert))
        rebuilt_llm['contexts'].setdefault('verified_context_certificates',{})['verified_parent_context']=deepcopy(rebuilt_llm['contexts']['verified_parent_context'])
        rebuilt_rule['input']['llm_v29_shared_context']=deepcopy(rebuilt_llm['contexts'])
        assert rebuilt_rule==current and rebuilt_llm==llm_new[rid], ('Change beyond authenticated material',rid)
        certificate_count+=len(added)
        changes.append({'id':rid,'unit_id':inp['unit_id'],'paragraph_id':unit['paragraph_id'],
                        'parent_ids':[c['paragraph_id'] for c in added],
                        'original_unit_sha256':digest(inp['unit_text']),
                        'certificate_sha256':[digest(json.dumps(c,ensure_ascii=False,sort_keys=True)) for c in added]})
    assert len(changes)==5 and len(unchanged)==4919 and certificate_count==16
    assert {c['id'] for c in changes}=={f'RECODE25-{i:05d}' for i in range(1774,1779)}
    assert {c['id'] for c in changes}=={c['id'] for c in manifest['changes']}
    for path,value in manifest['frozen_previous_artifacts_sha256'].items():
        assert sha(path)==value;before[path]=value
    assert before=={p:sha(p) for p in before}, 'Source changed during read-only QA'
    report={'status':'passed','checked_at':datetime.datetime.now().astimezone().isoformat(),
        'independence':'Separate script imports no builder, classifier or statistics code and reads no A/C labels. Reconstructs the exact allowed delta from original PDF/candidate membership.',
        'total_ids_checked':4924,'original_ids_and_unit_texts_unchanged':4924,
        'rule_and_llm_contexts_identical':4924,'certificates_added_and_bound':16,
        'changed_units':changes,'entire_other_records_unchanged':4919,
        'source':str(source),'source_sha256':sha(source),'source_physical_page':6,'source_printed_page':3,
        'source_paragraphs':source_paragraphs,
        'normalization':'NFKC and extraction whitespace only; punctuation and every language character retained.',
        'boundary':'A/B/C inherit only the local safety-report object/population-definition predicate. Explicit 上述人群定义原则 resolves to the complete list; no extension into p0013 separate combined-drug guidance or p0014 next section.',
        'source_image':str(paths['source_image']),'source_image_sha256':sha(paths['source_image']),
        'source_page_actually_opened_and_viewed':True,'reference_labels_loaded':False,
        'frozen_v2_and_classifier_code_preserved':True,'source_sha256_bindings':before}
    target=OUT/'source_safety_population_v3_independent_QA.json'
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'same_materials':4924,'changes':len(changes),
                      'certificates':16,'other_records_unchanged':4919,'output':str(target),'sha256':sha(target)},ensure_ascii=False))


if __name__=='__main__':main()
