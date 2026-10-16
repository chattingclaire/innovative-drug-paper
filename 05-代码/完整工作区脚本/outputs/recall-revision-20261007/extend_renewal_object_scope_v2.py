"""Preserve frozen material v1; add the five explicit renewal object scopes."""
from pathlib import Path
from hashlib import sha256
import json,re,unicodedata
import pypdfium2 as pdfium

HERE=Path(__file__).resolve().parent
def sha(p):return sha256(Path(p).read_bytes()).hexdigest()
def digest(t):return sha256(t.encode()).hexdigest()
def compact(t):return ''.join(c for c in unicodedata.normalize('NFKC',t) if c.isalnum())
def rows(p):return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
rules=rows(HERE/'rule_inputs_v31_shared.jsonl');llm=rows(HERE/'effective_blind_inputs_v30.jsonl')
assert sha(HERE/'rule_inputs_v31_shared.jsonl')=='40346a9b15020e866cf86474d560ff40bb6bcb6cfa855b1357d8ec3a44b2b400'
assert sha(HERE/'effective_blind_inputs_v30.jsonl')=='6fa91f237c8762fb117cb6c920d6a689dd65ee35f3b938db2f0a569bf9b965b8'
proposals=json.loads((HERE/'parent_list_context_proposals.json').read_text())
scope={};checks=[]
for proposal in proposals:
    file=Path(proposal['candidate_file']);candidate=json.loads(file.read_text())
    for parent in candidate['paragraphs']:
        if not re.search(r'现分类制定.*谈判药品.*(?:续约规则|处理规则)如下',parent['text']):continue
        source=Path(parent.get('source_file') or candidate['source'])
        if str(source) in scope:continue
        pdf=pdfium.PdfDocument(source);page_text='\n'.join(pdf[n-1].get_textpage().get_text_range() for n in parent['pages'])
        assert compact(parent['text']) in compact(page_text)
        scope[str(source)]=(file,parent)
        checks.append({'source':str(source),'source_sha256':sha(source),'candidate':str(file),
            'candidate_sha256':sha(file),'parent':parent,'literal_source_match':True,
            'scope':'the component defines rules for agreement-period/expiring negotiated medicines; only object is restored, local timing/eligibility exceptions remain local'})
assert len(scope)==5
changes=[];cert_count=0
for r,l in zip(rules,llm):
    rec=r['input'];source=rec.get('unit_source') or rec['source']
    assert r['id']==l['id'] and rec['unit_text']==l['text']
    if source in scope:
        file,parent=scope[source]
        assert str(file)==rec['candidate_file']
        if compact(parent['text']) not in compact(rec['unit_text']) and not any(compact(c['text'])==compact(parent['text']) for c in rec.get('verified_parent_context',[])):
            cert={'paragraph_id':parent['id'],'text':parent['text'],'pages':parent['pages'],'source_lines':parent.get('line_ids',[]),
                'text_sha256':digest(parent['text']),'source_path':source,'source_sha256':sha(source),
                'candidate_path':str(file),'candidate_sha256':sha(file),'original_unit_sha256':digest(rec['unit_text']),
                'unit_id':rec['unit_id'],'repair_version':'v31-source-object-scope',
                'verification':{'verified':True,'method':'literal_source_scope_and_exact_component_membership'},
                'usage':'Resolve only the explicitly stated negotiated-medicine object. Do not copy dimension labels or specific eligibility/timing conditions; local exceptions retain their own scope.'}
            assert cert['source_sha256']==(rec.get('unit_source_sha256') or rec['source_sha256'])
            rec.setdefault('verified_parent_context',[]).append(cert)
            l['contexts'].setdefault('verified_parent_context',[]).append(json.loads(json.dumps(cert)))
            l['contexts'].setdefault('verified_context_certificates',{})['verified_parent_context']=json.loads(json.dumps(l['contexts']['verified_parent_context']))
            changes.append({'id':r['id'],'source':source,'parent_id':parent['id']});cert_count+=1
    rec['llm_v29_shared_context']=json.loads(json.dumps(l['contexts']))
    assert rec['llm_v29_shared_context']==l['contexts']
rp=HERE/'rule_inputs_v31_shared_v2.jsonl';lp=HERE/'effective_blind_inputs_v30_v2.jsonl'
for path,data in [(rp,rules),(lp,llm)]:path.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in data))
out={'status':'source_object_scope_completion_v2','n':4924,'previous_frozen_materials_unchanged':True,
    'ids_and_unit_texts_unchanged':4924,'rules_and_llm_contexts_identical':4924,'scope_source_count':5,
    'additional_context_units':len(changes),'certificates_added':cert_count,'source_checks':checks,'changes':changes,
    'rule_input_sha256':sha(rp),'llm_input_sha256':sha(lp),'classification_labels_added':False,
    'builder_sha256':sha(Path(__file__))}
(HERE/'renewal_object_scope_v2_manifest.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:out[k] for k in ['status','additional_context_units','rule_input_sha256','llm_input_sha256']},ensure_ascii=False))
