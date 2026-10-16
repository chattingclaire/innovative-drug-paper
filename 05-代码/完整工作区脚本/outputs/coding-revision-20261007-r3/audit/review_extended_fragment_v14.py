"""Independently authenticate the 20 proposed source families before packaging.

Only original sources, their candidate parses, and frozen source inputs are read.
The image-only page was visually read in this review; its exact render is bound.
"""
from pathlib import Path
from functools import lru_cache
import hashlib
import json
import subprocess
import unicodedata
from pypdf import PdfReader

B = Path(__file__).resolve().parents[1]
P = B / 'audit/extended_fragment_source_proposal_v14.json'
DEST = B / 'audit/extended_fragment_source_review_v14.json'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
digest = lambda s: hashlib.sha256(s.encode()).hexdigest()
norm = lambda s: ''.join(c for c in unicodedata.normalize('NFKC', s) if c.isalnum())

@lru_cache(None)
def pdf(path):
    return PdfReader(path)

def source_check(c, source):
    if source.suffix == '.pdf':
        raw = '\n'.join(pdf(str(source)).pages[n - 1].extract_text() for n in c['pages'])
        if not raw.strip():
            assert source.name == 'CDE-关爱延伸-正式计划镜像.pdf' and c['pages'] == [17]
            return 'original_pdf_p17_fresh_render_visually_verified'
        assert norm(c['text']) in norm(raw), c['paragraph_id']
        return 'original_pdf_stated_pages_normalized_literal_match'
    lines = source.read_text().splitlines()
    assert c['source_lines'] and all(x.startswith('L') for x in c['source_lines'])
    raw = '\n'.join(lines[int(x[1:]) - 1] for x in c['source_lines'])
    assert norm(c['text']) == norm(raw), (c['paragraph_id'], c['text'], raw)
    return 'original_text_exact_stated_lines_normalized_match'

def main():
    assert not DEST.exists(), 'Never overwrite the source review'
    prop = json.loads(P.read_text())
    ll = {x['id']: x for x in map(json.loads, (B / 'effective_blind_inputs_v13.jsonl').read_text().splitlines())}
    rr = {x['id']: x['input'] for x in map(json.loads, (B / 'rule_inputs_shared_v13.jsonl').read_text().splitlines())}
    assert sha(B / 'effective_blind_inputs_v13.jsonl') == prop['v13_llm_sha256']
    assert sha(B / 'rule_inputs_shared_v13.jsonl') == prop['v13_rule_sha256']
    reviewed = []
    for f in prop['families']:
        source, candidate = Path(f['source_path']), Path(f['candidate_path'])
        assert sha(source) == f['source_sha256'] and sha(candidate) == f['candidate_sha256']
        cd = json.loads(candidate.read_text()); ps = cd['paragraphs']; ix = {p['id']: i for i, p in enumerate(ps)}
        record = {'family': f.get('source_list_head_unit', f.get('family')), 'affected_ids': f['affected_ids'], 'affected_n': len(f['affected_ids']), 'source_path': str(source), 'source_sha256': sha(source), 'candidate_path': str(candidate), 'candidate_sha256': sha(candidate), 'decision': 'source_repair_needed', 'label_inheritance_allowed': False}
        if 'complete_contiguous_interval' in f:
            cs = f['complete_contiguous_interval']; boundary = f['next_boundary']
            assert [c['paragraph_id'] for c in cs] == [p['id'] for p in ps[ix[cs[0]['paragraph_id']]:ix[cs[-1]['paragraph_id']] + 1]]
            assert ps[ix[cs[-1]['paragraph_id']] + 1]['id'] == boundary['paragraph_id']
            details = []
            for c in cs + [boundary]:
                cp = ps[ix[c['paragraph_id']]]
                assert c['text'] == cp['text'] and c['pages'] == cp.get('pages', [])
                assert c['source_lines'] == cp.get('line_ids', [])
                assert Path(cp.get('source_file') or cd['source']).resolve() == source.resolve()
                details.append({'paragraph_id': c['paragraph_id'], 'text_sha256': digest(c['text']), 'method': source_check(c, source), 'is_excluded_next_boundary': c is boundary})
            assert cs[0]['text'] == f['actual_parent_text']
            record.update(reason=f['reason'], actual_parent_text=f['actual_parent_text'], actual_parent_paragraph_id=f['actual_parent_paragraph_id'], complete_interval_paragraph_ids=[c['paragraph_id'] for c in cs], next_boundary=boundary, checks=details, existing_first_or_other_items_no_change=f['existing_first_or_other_items_with_actual_head_available_no_change_needed'])
            if source.suffix == '.pdf':
                image = B / ('audit/v14-source-' + str(cs[0]['pages'][0]) + '.png')
                record['fresh_visual_evidence'] = {'path': str(image), 'sha256': sha(image), 'page': cs[0]['pages'][0], 'full_relevant_page_read': True, 'parent_all_siblings_and_next_boundary_visually_verified': True}
        else:
            raw = subprocess.run(['textutil', '-convert', 'txt', '-stdout', str(source)], check=True, capture_output=True, text=True).stdout
            assert norm(f['actual_component_heading']) in norm(raw)
            aps = [p for p in ps if p.get('origin') == 'verified_local_attachment' and p.get('attachment_title') == '试点工作申报资料要求']
            assert [p['id'] for p in aps] == f['source_paragraph_ids'] and len(aps) == 9
            pos = -1
            for rid, cp in zip(f['affected_ids'], aps):
                row = ll[rid]; r = rr[rid]
                assert row['text'] == cp['text'] and norm(row['text']) in norm(raw)
                at = norm(raw).index(norm(row['text'])); assert at > pos; pos = at
                assert Path(r['unit_source']).resolve() == source.resolve() and r['unit_source_sha256'] == sha(source)
                assert row['contexts']['nearest_preceding_heading']['text'] == '五、保障措施'
            assert norm(raw).endswith(norm(aps[-1]['text']))
            assert not any(norm(p['text']) == norm(f['actual_component_heading']) for p in ps)
            record.update(reason='独立原始Word附件包含自己的资料要求标题和连续9项；主方案第五节及其前段不能作为附件标题与首项前文。', actual_component_heading=f['actual_component_heading'], source_paragraph_ids=f['source_paragraph_ids'], attachment_extracted_text_sha256=digest(raw), original_title_and_all_nine_items_verified=True, end_of_actual_attachment_verified=True, no_candidate_heading_paragraph_fabricated=True, first_item_wrong_cross_component_previous=f['first_item_cross_component_immediate_previous_replaced'])
        reviewed.append(record)
    ids = sorted(rid for f in reviewed for rid in f['affected_ids'])
    assert ids == prop['affected_ids'] and len(ids) == len(set(ids)) == 78 and len(reviewed) == 20
    for x in prop['proposals']:
        row = ll[x['id']]
        assert row['text'] == x['current_unit'] and digest(row['text']) == x['current_unit_sha256']
        assert digest(json.dumps(row['contexts'], ensure_ascii=False, sort_keys=True)) == x['old_context_sha256']
        if x['repair_type'] == 'actual_local_list_parent_predicate':
            assert x['actual_parent_context'] == x['complete_local_family_contexts'][0]
            assert {c['paragraph_id'] for c in row['contexts']['paragraph_context']} <= {c['paragraph_id'] for c in x['complete_local_family_contexts'][1:]}
    result = {'review_version': 'v14-source-family-review', 'status': 'PASS', 'source_only': True, 'proposal_path': str(P), 'proposal_sha256': sha(P), 'source_family_n': 20, 'affected_unit_n': 78, 'parent_repair_unit_n': 69, 'attachment_heading_unit_n': 9, 'attachment_cross_component_previous_n': 1, 'affected_ids': ids, 'families': reviewed, 'all_original_sources_and_candidates_sha_rechecked': True, 'no_new_analysis_units_or_original_text_changes': True, 'no_labels_references_confirmation_or_predictions_read': True, 'no_label_inheritance': True}
    DEST.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ['status', 'source_family_n', 'affected_unit_n', 'parent_repair_unit_n', 'attachment_heading_unit_n']}, ensure_ascii=False))

if __name__ == '__main__':
    main()
