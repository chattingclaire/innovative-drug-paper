"""Add actual document-body object declarations symmetrically, before r3 coding."""
from pathlib import Path
import copy, hashlib, json, unicodedata
from pypdf import PdfReader
HERE=Path(__file__).resolve().parent
PREV=HERE.parent/'agent-validation-20261007-r2'
def jl(p): return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def norm(s): return ''.join(c for c in unicodedata.normalize('NFKC',s) if not c.isspace() and not unicodedata.category(c).startswith('P'))
ll=jl(PREV/'effective_blind_inputs_v8.jsonl'); rr=jl(PREV/'rule_inputs_shared_v8.jsonl')
lb={r['id']:r for r in ll}; rb={r['id']:r for r in rr}
proposal_path=HERE/'rules-v33/source_bid_object_scope_proposal_v9.json'
proposal=json.loads(proposal_path.read_text());affected=[];certificates=[]
for g in proposal['groups']:
    container=Path(g['source_path']);candidate=Path(g['candidate_path'])
    assert sha(container)==g['source_sha256'] and sha(candidate)==g['candidate_sha256']
    cd=json.loads(candidate.read_text()); paras={p['id']:p for p in cd['paragraphs']}
    source=Path(g['verified_body_object_paragraphs'][0].get('source_file',container))
    source_text=norm('\n'.join(p.extract_text() for p in PdfReader(source).pages))
    parts=[]
    for p in g['verified_body_object_paragraphs']:
        assert paras[p['id']]['text']==p['text'] and norm(p['text']) in source_text
        assert '现制定非独家药品竞价规则如下' in p['text']
        parts.append({'paragraph_id':p['id'],'text':p['text'],'pages':p['pages'],
                      'source_path':str(source),'source_sha256':sha(source),
                      'candidate_path':str(candidate),'candidate_sha256':sha(candidate),
                      'role':'verified_document_body_object_only'})
    for rid in g['ids']:
        ri=rb[rid]['input']; assert ri['candidate_file']==str(candidate)
        assert Path(ri.get('unit_source',ri['source']))==source
        assert sha(source)==ri.get('unit_source_sha256',ri['source_sha256'])
        assert lb[rid]['text']==ri['unit_text']
        cert={'repair_version':'v9-source-object-declaration',
              'source_path':str(source),'source_sha256':sha(source),
              'container_source_path':str(container),'container_source_sha256':sha(container),
              'candidate_path':str(candidate),'candidate_sha256':sha(candidate),
              'current_unit_sha256':hashlib.sha256(lb[rid]['text'].encode()).hexdigest(),
              'current_unit_id':ri['unit_id'],'contexts':copy.deepcopy(parts),
              'component_first_paragraph':g['component_first_paragraph'],
              'component_last_paragraph':g['component_last_paragraph'],
              'next_component_boundary_text':g['next_component_boundary_text'],
              'source_normalized_substring_verified':True,
              'usage':'Resolve the medicine object of the current bidding-component proposition only. Do not copy reimbursement, economic or fairness labels from this declaration into routine procedures.'}
        c=lb[rid]['contexts']; c['verified_document_object_v9']=copy.deepcopy(parts)
        c['verified_context_certificates']['verified_document_object_v9']=copy.deepcopy(cert)
        ri['llm_v29_shared_context']=copy.deepcopy(c)
        ri['verified_document_object_v9']=copy.deepcopy(cert)
        affected.append(rid)
    certificates.append({'actual_source_path':str(source),'actual_source_sha256':sha(source),
                         'container_source_path':str(container),'container_source_sha256':sha(container),
                         'candidate_path':str(candidate),'candidate_sha256':sha(candidate),
                         'n':len(g['ids']),'contexts':parts})
assert len(affected)==len(set(affected))==152
for name,rows in [('effective_blind_inputs_v9.jsonl',ll),('rule_inputs_shared_v9.jsonl',rr)]:
    (HERE/name).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
old=jl(PREV/'effective_blind_inputs_v8.jsonl')
assert all(a['text']==b['text'] and a['id']==b['id'] for a,b in zip(ll,old))
assert sum(a!=b for a,b in zip(ll,old))==152
assert all(r['contexts']==s['input']['llm_v29_shared_context'] for r,s in zip(ll,rr))
manifest={'material_version':'v9','n':4924,'incremental_context_changed_n':152,
          'unit_text_changes':0,'unit_id_changes':0,'affected_ids':affected,
          'reason':'Actual document body establishes the medicine object; all four complete bidding components receive the same source-only declaration.',
          'not_derived_from_title_or_department':True,'source_object_only_not_label_propagation':True,
          'actual_source_certificates':certificates,
          'previous_v8_input_sha256':sha(PREV/'effective_blind_inputs_v8.jsonl'),
          'previous_v8_rule_input_sha256':sha(PREV/'rule_inputs_shared_v8.jsonl'),
          'proposal_sha256':sha(proposal_path),
          'new_llm_input_sha256':sha(HERE/'effective_blind_inputs_v9.jsonl'),
          'new_rule_input_sha256':sha(HERE/'rule_inputs_shared_v9.jsonl'),
          'two_methods_same_text_and_context':True,
          'coding_standard_unchanged':'CAL-5D-v1.3 + operational-v1.4',
          'frozen_before_new_agent_confirmation':True}
(HERE/'material_v9_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'n':4924,'context_added':152,'text_changes':0,'same_material':True},ensure_ascii=False))
