"""Restore one source-defined list and its explicit anaphoric continuation.

The frozen v2 inputs/runtime and all labels are untouched.  Membership is
identified from source paragraphs, never from predictions or reference labels.
"""
from pathlib import Path
from hashlib import sha256
from copy import deepcopy
import json
import unicodedata
import pypdfium2 as pdfium

HERE=Path(__file__).resolve().parent
def sha(path):return sha256(Path(path).read_bytes()).hexdigest()
def digest(text):return sha256(text.encode()).hexdigest()
def compact(text):return ''.join(c for c in unicodedata.normalize('NFKC',text) if c.isalnum())
def read_rows(path):return [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]

def main():
    old_rule=HERE/'rule_inputs_v31_shared_v2.jsonl'
    old_llm=HERE/'effective_blind_inputs_v30_v2.jsonl'
    assert sha(old_rule)=='0d4e6358807c5ed38311b9a306dd539de7278e2c57de94b7a0f7730b2e06258a'
    assert sha(old_llm)=='0c05b1dbd43a74943bb1deafd26b1dbb1963bef0505dda501d83cdf1bfed9955'
    frozen=[old_rule,old_llm,HERE/'rules-v31/all_predictions_completed_material_v2.jsonl',
            HERE/'rules-v31/all_predictions_completed_material_v2.run.json',
            HERE/'rules-v31/release_completed_material_v2.json']
    frozen.extend(sorted((HERE/'rules-v31/completed-material-runtime-v2').glob('*.py')))
    previous={str(p.resolve()):sha(p) for p in frozen}
    rules=read_rows(old_rule);models=read_rows(old_llm)
    assert len(rules)==len(models)==4924
    candidates={r['input']['candidate_file'] for r in rules
                if r['input']['original_file_stem']=='CDE-抗肿瘤创新药上市申请安全性总结资料指导原则-2020'}
    assert len(candidates)==1
    candidate_path=Path(candidates.pop());candidate=json.loads(candidate_path.read_text())
    source=Path(candidate['source']);source_sha=sha(source);candidate_sha=sha(candidate_path)
    assert source_sha=='d003d23a67bd150f7fcebb6e1268b437129cee4cee645cb00586cb8f482291b2'
    assert candidate_sha=='2c661d2fbb6b40e17838d35e3dd81f1027997cd4d056e95a9fefc2f2ad7522fe'
    paragraphs={p['id']:p for p in candidate['paragraphs']}
    assert paragraphs['p0007']['text']=='建议基于以上数据来源,撰写申报资料的安全性内容,为产品说明书的撰写提供参考。'
    assert paragraphs['p0008']['text']=='总结报告的人群定义有如下建议:'
    assert [paragraphs[p]['text'].split('、')[0] for p in ('p0009','p0010','p0011')]==['A','B','C']
    assert paragraphs['p0012']['text'].startswith('在上述人群定义原则下,')
    assert paragraphs['p0013']['text'].startswith('考虑部分抗肿瘤创新药需要联合用药,')
    assert paragraphs['p0014']['type']=='heading_candidate'
    document=pdfium.PdfDocument(source)
    page_text=document[5].get_textpage().get_text_range()
    positions=[]
    for pid in [f'p{x:04d}' for x in range(7,15)]:
        parent=paragraphs[pid]
        assert parent['pages']==[6]
        assert compact(parent['text']) in compact(page_text),pid
        positions.append(compact(page_text).index(compact(parent['text'])))
    assert positions==sorted(positions)
    units={u['id']:u for u in candidate['unit_candidates']}
    # A/B/C share the list predicate and its local report-object antecedent.
    # The following paragraph explicitly points back to the complete list.
    memberships={}
    for unit in units.values():
        pid=unit.get('paragraph_id')
        if pid in {'p0009','p0010','p0011'}:
            memberships[unit['id']]=['p0007','p0008']
        elif pid=='p0012':
            memberships[unit['id']]=[f'p{x:04d}' for x in range(7,12)]
    assert len(memberships)==5
    changes=[]
    for rule,model in zip(rules,models):
        rec=rule['input']
        assert rule['id']==model['id'] and rec['unit_text']==model['text']
        assert rec['llm_v29_shared_context']==model['contexts']
        if rec['candidate_file']==str(candidate_path) and rec['unit_id'] in memberships:
            unit=units[rec['unit_id']]
            assert unit['text']==rec['unit_text']
            assert (rec.get('unit_source') or rec['source'])==str(source)
            new=[]
            for pid in memberships[rec['unit_id']]:
                parent=paragraphs[pid]
                usage=('Only restore the safety-report object and the governing population-definition predicate; '
                       'do not turn sibling content into this unit or transfer labels.'
                       if unit['paragraph_id']!='p0012' else
                       'Only resolve the explicit phrase 上述人群定义原则 and the report object using the complete preceding A/B/C list; '
                       'do not impose one sibling population on all other populations or transfer labels.')
                cert={'paragraph_id':pid,'text':parent['text'],'pages':parent['pages'],
                      'source_lines':parent['line_ids'],'text_sha256':digest(parent['text']),
                      'source_path':str(source),'source_sha256':source_sha,
                      'candidate_path':str(candidate_path),'candidate_sha256':candidate_sha,
                      'original_unit_sha256':digest(rec['unit_text']),'unit_id':rec['unit_id'],
                      'repair_version':'v31-source-list-predicate',
                      'verification':{'verified':True,'method':'literal_source_list_membership_and_explicit_anaphora'},
                      'target_paragraph_id':unit['paragraph_id'],'material_revision':'v3-source-safety-population-list',
                      'usage':usage}
                rec.setdefault('verified_parent_context',[]).append(cert)
                model['contexts'].setdefault('verified_parent_context',[]).append(deepcopy(cert))
                new.append(pid)
            model['contexts'].setdefault('verified_context_certificates',{})['verified_parent_context']=deepcopy(model['contexts']['verified_parent_context'])
            rec['llm_v29_shared_context']=deepcopy(model['contexts'])
            changes.append({'id':rule['id'],'unit_id':rec['unit_id'],'target_paragraph':unit['paragraph_id'],
                            'added_parent_paragraphs':new,'source_physical_pages':[6]})
    assert len(changes)==5
    assert all(r['input']['llm_v29_shared_context']==m['contexts'] for r,m in zip(rules,models))
    rule_path=HERE/'rule_inputs_v31_shared_v3.jsonl'
    model_path=HERE/'effective_blind_inputs_v30_v3.jsonl'
    for path,data in [(rule_path,rules),(model_path,models)]:
        assert not path.exists(),('Preserve existing frozen v3 material',path)
        path.write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in data))
    assert previous=={p:sha(p) for p in previous}
    out={'status':'source_list_and_anaphora_context_completion_v3','n':4924,
         'rule_input_path':str(rule_path.resolve()),'rule_input_sha256':sha(rule_path),
         'llm_input_path':str(model_path.resolve()),'llm_input_sha256':sha(model_path),
         'ids_and_unit_texts_unchanged':4924,'rules_and_llm_contexts_identical':4924,
         'additional_context_units':len(changes),'certificates_added':sum(len(c['added_parent_paragraphs']) for c in changes),
         'changes':changes,'source':str(source),'source_sha256':source_sha,
         'candidate':str(candidate_path),'candidate_sha256':candidate_sha,
         'source_paragraphs':[paragraphs[f'p{x:04d}'] for x in range(7,15)],
         'boundary':'p0008 governs A/B/C p0009–p0011; p0012 explicitly refers back to the full list. p0013 introduces separate single/combined-drug safety-data guidance; p0014 starts a new section. No extension beyond p0012.',
         'source_literal_check_normalization':'NFKC and alphanumeric comparison permits extraction punctuation/whitespace differences; candidate text and all certificate text hashes are exact',
         'classification_labels_or_reference_data_loaded':False,'construct_or_runtime_changed':False,
         'frozen_previous_artifacts_sha256':previous,'builder_sha256':sha(__file__)}
    (HERE/'safety_population_context_v3_manifest.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ['status','additional_context_units','certificates_added','rule_input_sha256','llm_input_sha256']},ensure_ascii=False))

if __name__=='__main__':main()
