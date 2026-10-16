"""Apply only source-verified, label-free repairs to the eight rule gaps."""
import copy
import hashlib
import json
from pathlib import Path
from context_validation import digest, payload_digest, verified_following_list, compact

ROOT = Path(__file__).resolve().parent
OLD = ROOT.parent/'autocode-v25-20260927'
PREV = ROOT.parent/'coding-v26-20260930'


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    source_inputs = OLD/'current_rule_inputs.jsonl'
    patch_path = PREV/'context_repair/label_free_context_patch53_v26.json'
    prior_path = PREV/'title_scope_verification/all_predictions.jsonl'
    rows = [json.loads(line) for line in source_inputs.read_text().splitlines()]
    pending = {r['id'] for r in map(json.loads, prior_path.read_text().splitlines())
               if r['prediction']['judgement_status'] == 'undetermined'}
    patches = {r['id']:r for r in json.loads(patch_path.read_text())['records']}
    log = []
    scope_log = []
    checked = {}
    for row in rows:
        if row['id'] not in pending:
            continue
        repair = patches[row['id']]
        rec = row['input']
        assert repair['unit_text_sha256'] == digest(rec['unit_text'])
        assert repair['repair_status'] == 'supplemented'
        assert repair['unresolved_material_gaps'] == []
        contexts = copy.deepcopy(repair['verified_context_v26']['contexts'])
        for c in contexts:
            for path_key, hash_key in [('source_path','source_sha256'), ('candidate_path','candidate_sha256')]:
                path = c[path_key]
                if path not in checked:
                    checked[path] = file_hash(path)
                assert checked[path] == c[hash_key], (row['id'], path_key)
            for im in c.get('source_page_images', []):
                assert file_hash(im['path']) == im['sha256']
        paragraphs = json.loads(Path(contexts[-1]['candidate_path']).read_text())['paragraphs']
        positions = [next(i for i,p in enumerate(paragraphs)
                          if p.get('id',p.get('paragraph_id')) == c['paragraph_id']) for c in contexts]
        assert positions == list(range(positions[0],positions[-1]+1)), row['id']
        following = paragraphs[positions[-1]+1] if positions[-1]+1<len(paragraphs) else None
        boundary = {'all_paragraphs_in_interval_included':True,
                    'first_paragraph':contexts[0]['paragraph_id'],
                    'last_paragraph':contexts[-1]['paragraph_id'],
                    'next_structure':following,
                    'review':'Complete section ends immediately before the next numbered heading/article.'}
        cert = {
            'original_unit_sha256': repair['unit_text_sha256'],
            'source_sha256': rec.get('unit_source_sha256') or rec.get('source_sha256'),
            'contexts':contexts, 'contexts_sha256':payload_digest(contexts),
            'repair_status':repair['repair_status'], 'unresolved_material_gaps':[],
            'source_files_hash_verified':True,
            'structure_boundary':boundary,
            'provenance_patch_sha256':file_hash(patch_path),
            'usage':'Completeness only. Context does not become current-unit dimension evidence.',
        }
        rec['verified_following_list_v27'] = cert
        assert verified_following_list(rec), row['id']
        log.append({'id':row['id'], 'original_id':row['original_id'],
                    'unit_text_sha256':repair['unit_text_sha256'],
                    'paragraphs':[c['paragraph_id'] for c in contexts],
                    'source_sha256':cert['source_sha256'],
                    'structure_boundary':boundary,
                    'unit_text_unchanged':True, 'label_free_repair':True})
    assert len(log) == len(pending) == 8
    # Source-defined program scope is added consistently to the whole verified
    # component, never selected by reference labels or desired predictions.
    source_root = Path('/Users/rainbow/Desktop/战略院/创新药论文-完整归档-20260914/12-投稿定稿工作区/原文补全')
    source_path = source_root/'NMPA-突破性治疗等三程序-2020-附件正文.txt'
    candidate_path = source_root/'PDF段落与句子候选/NMPA-突破性治疗等三程序-2020.json'
    source_sha, candidate_sha = file_hash(source_path), file_hash(candidate_path)
    source_line = source_path.read_text().splitlines()[5]
    candidate = json.loads(candidate_path.read_text())
    scope_para = next(p for p in candidate['paragraphs'] if p.get('id')=='p0004')
    assert compact(scope_para['text']) == compact(source_line)
    unit_map = {u['id']:u for u in candidate['unit_candidates']}
    for row in rows:
        rec = row['input']
        if (rec.get('unit_source_sha256') or rec.get('source_sha256')) != source_sha:
            continue
        assert rec['candidate_sha256'] == candidate_sha
        unit = unit_map[rec['unit_id']]
        if unit.get('component') != '突破性治疗程序':
            continue
        # Current-unit and scope source bindings are checked again by the rule.
        scope = {'text':scope_para['text'], 'text_sha256':digest(scope_para['text']),
                 'source_sha256':source_sha, 'original_unit_sha256':digest(rec['unit_text']),
                 'component':'突破性治疗程序', 'verified':True,
                 'locator':{'source_lines':[6],'paragraph_id':scope_para['id']},
                 'component_binding':{'unit_id':rec['unit_id'], 'candidate_sha256':candidate_sha},
                 'usage':'Resolve innovation-qualified program object only; current-unit comparison and parent eligibility anchors remain mandatory.'}
        rec['verified_innovation_scope_v27'] = scope
        scope_log.append({'id':row['id'],'unit_text_sha256':digest(rec['unit_text']),
                          'source_sha256':source_sha,'scope_text_sha256':scope['text_sha256']})
    output = ROOT/'rule_inputs_v27.jsonl'
    output.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
    audit = {'input_count':len(rows), 'repaired_count':len(log),
             'source_inputs_sha256':file_hash(source_inputs),
             'repair_patch_sha256':file_hash(patch_path),
             'prepared_inputs_sha256':file_hash(output),
             'all_unit_texts_and_ids_unchanged':True,
             'checked_files':checked, 'repairs':log,
             'innovation_scope_source_line':source_line,
             'innovation_scope_component_count':len(scope_log),
             'innovation_scope_repairs':scope_log}
    (ROOT/'context_repair_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
    print(json.dumps({'rows':len(rows),'repaired':len(log),'scope_component_rows':len(scope_log),'prepared_inputs_sha256':file_hash(output)}))


if __name__ == '__main__':
    main()
