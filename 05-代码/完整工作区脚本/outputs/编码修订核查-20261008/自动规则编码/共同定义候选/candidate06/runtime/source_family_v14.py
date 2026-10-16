"""Authenticate local predicates and independent components; never assign labels."""
import subprocess


def bind_common(record, shared, field, require, digest, file_sha, candidate):
    cert = record.get(field)
    require(cert == shared.get(field), 'v14 source certificate differs across methods')
    if cert is None:
        return None
    for key, value in (
        ('current_unit_id', record.get('unit_id')),
        ('current_unit_sha256', digest(record['unit_text'])),
        ('source_path', record.get('unit_source') or record.get('source')),
        ('source_sha256', record.get('unit_source_sha256') or record.get('source_sha256')),
        ('candidate_path', record.get('candidate_file')),
        ('candidate_sha256', record.get('candidate_sha256')),
    ):
        require(cert.get(key) == value, 'v14 current target/source binding differs')
    require(file_sha(cert['source_path']) == cert['source_sha256'] and
            file_sha(cert['candidate_path']) == cert['candidate_sha256'],
            'v14 actual file digest differs')
    review = cert.get('verification', {})
    require(review.get('verified') is True and
            file_sha(review.get('review_path', '')) == review.get('review_sha256'),
            'v14 original-source review binding differs')
    doc = candidate(cert['candidate_path'])
    targets = [u for u in doc['unit_candidates'] if u.get('id') == record['unit_id']]
    require(len(targets) == 1 and targets[0]['text'] == record['unit_text'],
            'v14 target unit differs')
    return cert, doc, targets[0]


def local_family(record, shared, typed, log, api):
    require, digest, file_sha, candidate, norm, payload_digest, authenticate = api
    field = 'source_local_list_family_v14'
    bound = bind_common(record, shared, field, require, digest, file_sha, candidate)
    parents = [p for p in record.get('verified_parent_context', [])
               if p.get('repair_version') == 'v14-source-local-list-predicate']
    if bound is None:
        require(not parents, 'v14 parent requires full local source family')
        return
    cert, doc, target = bound
    require(record.get('verified_parent_context') == shared.get('verified_parent_context'),
            'v14 parent arrays differ across methods')
    contexts = cert.get('contexts', [])
    require(len(contexts) > 1 and cert.get('contexts_sha256') == payload_digest(contexts),
            'v14 family context digest differs')
    require(all(c.get('source_path') == cert['source_path'] and
                c.get('source_sha256') == cert['source_sha256'] and
                c.get('candidate_path') == cert['candidate_path'] and
                c.get('candidate_sha256') == cert['candidate_sha256'] for c in contexts),
            'v14 mixed source family')
    boundary = cert['structure_boundary']
    paragraphs = doc['paragraphs']
    positions = [i for i,p in enumerate(paragraphs) if p.get('id') == boundary['first_paragraph']]
    require(len(positions) == 1 and boundary.get('all_paragraphs_in_interval_included') is True,
            'v14 family start/completeness invalid')
    start = positions[0]
    actual = paragraphs[start:start+len(contexts)]
    require(len(actual) == len(contexts) and all(
        p['id'] == c['paragraph_id'] and p['text'] == c['text'] for p,c in zip(actual, contexts))
        and actual[-1]['id'] == boundary['last_paragraph'], 'v14 contiguous interval differs')
    following = paragraphs[start+len(contexts)] if start+len(contexts) < len(paragraphs) else None
    next_boundary = boundary['next_boundary']
    require(following is not None and following['id'] == next_boundary['paragraph_id'] and
            following['text'] == next_boundary['text'], 'v14 next boundary differs')
    predicate = cert['actual_parent_predicate']
    require(len(parents) == 1 and parents[0] == predicate and
            predicate['paragraph_id'] == contexts[0]['paragraph_id'] and
            predicate['text'] == contexts[0]['text'], 'v14 local predicate differs')
    require(predicate.get('unit_id') == record['unit_id'] and
            predicate.get('original_unit_sha256') == digest(record['unit_text']) and
            predicate.get('text_sha256') == digest(predicate['text']), 'v14 parent target differs')
    auth = [authenticate(c) for c in contexts]
    member = next((c for c in auth[1:] if c['paragraph_id'] == target.get('paragraph_id')
                   and norm(record['unit_text']) in norm(c['text'])), None)
    require(member is not None, 'v14 current target is not a member of actual local list')
    typed.append({'field': field, 'role': 'current_local_list_predicate',
                  'contexts': auth, 'parent_predicate': auth[0],
                  'target_is_list_child': True, 'current_list_member': member,
                  'current_unit_sha256': digest(record['unit_text']), 'labels_may_be_copied': False})
    log.append({'field': field, 'authenticated': True,
                'usage': 'actual_local_predicate_and_list_membership_only', 'dimension_assignment': False})


def component(record, shared, typed, log, api):
    require, digest, file_sha, candidate, norm, payload_digest, authenticate = api
    field = 'source_component_boundary_v14'
    bound = bind_common(record, shared, field, require, digest, file_sha, candidate)
    if bound is None:
        return
    cert, doc, target = bound
    heading = cert['actual_component_heading']
    require(heading.get('source_path') == cert['source_path'] and
            heading.get('source_sha256') == cert['source_sha256'] and
            heading.get('candidate_path') == cert['candidate_path'] and
            heading.get('candidate_sha256') == cert['candidate_sha256'] and
            heading.get('text_sha256') == digest(heading['text']), 'v14 component heading differs')
    require({'text': heading['text'], 'pages': heading.get('pages', [])} ==
            shared.get('nearest_preceding_heading') == record.get('nearest_preceding_heading'),
            'v14 component heading not the actual shared heading')
    source = subprocess.run(['textutil','-convert','txt','-stdout',cert['source_path']],
                            check=True,capture_output=True,text=True).stdout
    contexts = cert['contexts']
    require(contexts and cert.get('contexts_sha256') == payload_digest(contexts),
            'v14 component contexts digest differs')
    flat = norm(source)
    require(norm(heading['text']) in flat, 'v14 heading absent from original Word source')
    position = flat.index(norm(heading['text'])) + len(norm(heading['text']))
    for c in contexts:
        require(c['source_path'] == cert['source_path'] and c['source_sha256'] == cert['source_sha256'],
                'v14 component source differs')
        matches = [p for p in doc['paragraphs'] if p.get('id') == c['paragraph_id']]
        require(len(matches) == 1 and matches[0]['text'] == c['text'], 'v14 component paragraph differs')
        text = norm(c['text'])
        found = flat.find(text, position)
        require(found >= position, 'v14 component item absent/out of order')
        require(not flat[position:found], 'v14 unaccounted text between original attachment items')
        position = found + len(text)
    require(not flat[position:], 'v14 attachment end not reached')
    boundary = cert['structure_boundary']
    require(boundary['first_paragraph'] == contexts[0]['paragraph_id'] and
            boundary['last_paragraph'] == contexts[-1]['paragraph_id'] and
            boundary['next_boundary'] == 'end_of_original_word_attachment', 'v14 component boundary differs')
    members = [c for c in contexts if c['paragraph_id'] == target.get('paragraph_id') and
               norm(record['unit_text']) in norm(c['text'])]
    require(len(members) == 1, 'v14 current unit not in independent attachment')
    typed.append({'field': field, 'role': 'independent_attachment_heading_only',
                  'heading': heading, 'current_list_member': members[0], 'labels_may_be_copied': False})
    log.append({'field': field, 'authenticated': True,
                'usage': 'original_component_heading_and_boundary_only', 'dimension_assignment': False})
