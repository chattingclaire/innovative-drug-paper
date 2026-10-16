"""Apply source-defined context branches uniformly, without reading any labels."""
import copy
import json
from pathlib import Path
from pypdf import PdfReader
from context_validation import compact, digest, validate_added_parents
from run_release import sha, rows, save

ROOT = Path(__file__).resolve().parent
PREV = ROOT.parent / 'autocode-v27-final-20261004-1034'


def groups():
    result = json.loads((ROOT/'context_proposals_se.json').read_text())['groups']
    other = json.loads((ROOT/'context_proposals_ec_if.json').read_text())['proposals']
    for proposal in other:
        if 'direct_parent' in proposal:
            parent = proposal['direct_parent']
            targets = proposal['proposed_relation']['child_paragraph_ids']
        else:
            parent = proposal['substantive_scope']
            targets = [u['paragraph_id'] for u in proposal['all_branch_units']]
        result.append({
            'id':proposal['proposed_relation']['type']+'_'+parent['paragraph_id'],
            'source_path':proposal['source']['path'], 'source_sha256':proposal['source']['sha256'],
            'candidate_path':proposal['candidate']['path'], 'candidate_sha256':proposal['candidate']['sha256'],
            'parents':[{'paragraph_id':parent['paragraph_id'], 'text':parent['candidate_text'],
                        'text_sha256':digest(parent['candidate_text']), 'pages':parent['pages'],
                        'line_ids':parent['line_ids'], 'source_lines':[],
                        'verification':{'verified':True,'method':'normalized_substring_in_pdf_page_text'}}],
            'target_paragraph_ids':targets, 'usage':proposal['proposed_relation']['scope_meaning'],
            'labels_inherited':False, 'apply_to_all_same_branch':True})
    return result


def main():
    baseline = PREV/'rule_inputs_v27.jsonl'
    frozen = json.loads((PREV/'release_manifest.json').read_text())
    assert frozen['code_and_input_bindings'][str(baseline)] == sha(baseline)
    output = rows(baseline)
    logs=[]; checked={}; candidate_cache={}; pdf_cache={}
    for group in groups():
        assert group['labels_inherited'] is False and group['apply_to_all_same_branch'] is True
        for pathkey,hashkey in [('source_path','source_sha256'),('candidate_path','candidate_sha256')]:
            path=group[pathkey]; checked[path]=sha(path); assert checked[path]==group[hashkey]
        candidate = candidate_cache.setdefault(group['candidate_path'], json.loads(Path(group['candidate_path']).read_text()))
        paragraphs={p['id']:p for p in candidate['paragraphs']}
        units={u['id']:u for u in candidate['unit_candidates']}
        for parent in group['parents'] + group.get('scope_qualifications', []):
            assert parent['text']==paragraphs[parent['paragraph_id']]['text']
            assert parent['text_sha256']==digest(parent['text'])
            assert parent['verification']['verified'] is True
            source=Path(group['source_path'])
            if source.suffix.lower()=='.pdf':
                reader=pdf_cache.setdefault(str(source),PdfReader(source))
                actual='\n'.join(reader.pages[n-1].extract_text() for n in parent['pages'])
            else:
                lines=source.read_text().splitlines()
                actual='\n'.join(lines[n-1] for n in parent['source_lines'])
            if compact(parent['text']) not in compact(actual):
                assert parent['verification']['method']=='full_page_visual_comparison_scanned_pdf_page_14'
                assert parent['pages']==[14]
        targets=set(group['target_paragraph_ids']); applied=[]
        for row in output:
            rec=row['input']
            if (rec.get('unit_source_sha256') or rec.get('source_sha256')) != group['source_sha256']:
                continue
            if rec['candidate_sha256'] != group['candidate_sha256']: continue
            unit=units[rec['unit_id']]
            if unit.get('paragraph_id') not in targets: continue
            assert compact(unit['text'])==compact(rec['unit_text'])
            for parent in group['parents'] + group.get('scope_qualifications', []):
                cert=copy.deepcopy(parent)
                cert.update({k:group[k] for k in ('source_path','source_sha256','candidate_path','candidate_sha256','usage')})
                cert.update({'repair_version':'v28','original_unit_sha256':digest(rec['unit_text']),
                             'unit_id':rec['unit_id'],'branch_group':group['id']})
                field='verified_parent_context'
                if group['id']=='rare_patient_experience_mixed_treatment_list' and parent['paragraph_id']!='p0059':
                    field='verified_scope_qualifications_v28'
                    cert['usage']='Full mixed-treatment sibling list for scope qualification only; not a drug-object anchor or dimension evidence.'
                existing=rec.setdefault(field,[])
                if not any(c.get('paragraph_id')==cert['paragraph_id'] and c.get('text')==cert['text'] for c in existing):
                    existing.append(cert)
            validate_added_parents(rec)
            applied.append({'id':row['id'],'unit_id':rec['unit_id'],'paragraph_id':unit['paragraph_id']})
        assert applied,group['id']
        logs.append({'group':group['id'],'applied_units':applied,'usage':group['usage']})
    before={r['id']:r for r in rows(baseline)}
    assert len(output)==len(before)==4924
    for row in output:
        assert row['original_id']==before[row['id']]['original_id']
        assert row['input']['unit_text']==before[row['id']]['input']['unit_text']
    (ROOT/'rule_inputs_v27.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in output))
    byid={r['id']:r for r in output}
    for group in ('se','ec','if'):
        packet=rows(ROOT/f'audit_packet_{group}.jsonl')
        (ROOT/f'audit_packet_{group}_context_updated.jsonl').write_text(''.join(json.dumps(byid[r['id']],ensure_ascii=False)+'\n' for r in packet))
    save(ROOT/'parent_context_patch_v28.json',{'baseline_input_sha256':sha(baseline),
        'prepared_input_sha256':sha(ROOT/'rule_inputs_v27.jsonl'),'source_bindings':checked,
        'groups':logs,'distinct_units_supplemented':len({r['id'] for g in logs for r in g['applied_units']}),
        'unit_texts_unchanged':True,'reference_labels_used':False,
        'historical_AC_and_LLM_inputs_not_rewritten':True})
    print(json.dumps({'groups':len(logs),'distinct_units_supplemented':len({r['id'] for g in logs for r in g['applied_units']})}))


if __name__=='__main__':main()
