"""Audit candidate: authenticate new source fields without propagating labels.

The typed interface carries text and its current-unit relation. It is not a
dimension classifier. IDs/paths are used only as exact structural locators.
"""
import copy
import json
import re
import subprocess
from functools import lru_cache
from pathlib import Path
from source_context_adapter_v33 import prepare as prepare_v33
from source_context_adapter_v33 import digest, norm, file_sha, candidate, source_text, require
from context_validation import payload_digest
from pdf_layout_reconstruction_v34 import reconstruct_pdf

VERSION = 'v34-architecture-audit-candidate-not-released'


@lru_cache(maxsize=256)
def alternative_pdf_text(path):
    if Path(path).suffix.lower() != '.pdf':
        return ''
    try:
        return subprocess.run(['pdftotext','-layout','-enc','UTF-8',path,'-'],
                              check=True,capture_output=True,text=True).stdout
    except (FileNotFoundError, subprocess.CalledProcessError):
        return ''


@lru_cache(maxsize=256)
def authenticated_source_text(path):
    if Path(path).suffix.lower() in {'.doc','.docx'}:
        return subprocess.run(['textutil','-convert','txt','-stdout',path],
                              check=True,capture_output=True,text=True).stdout
    if Path(path).suffix.lower() == '.json':
        doc=json.loads(Path(path).read_text())
        if isinstance(doc,dict) and isinstance(doc.get('normative_paragraphs'),list):
            text=[p for p in doc['normative_paragraphs'] if isinstance(p,str)]
            for table in doc.get('tables',[]):
                for row in table.get('rows',[]):
                    if isinstance(row,list):text.extend(c for c in row if isinstance(c,str))
            return '\n'.join(text)
        raise ValueError('source adapter: unsupported authenticated JSON source schema')
    return source_text(path)


def authenticate_target(record):
    source = record.get('unit_source') or record.get('source')
    sha = record.get('unit_source_sha256') or record.get('source_sha256')
    cp = record.get('candidate_file')
    require(source and cp and file_sha(source) == sha, 'v34 target source binding invalid')
    require(file_sha(cp) == record.get('candidate_sha256'), 'v34 target candidate binding invalid')
    units = [u for u in candidate(cp).get('unit_candidates', [])
             if u.get('id') == record.get('unit_id')]
    require(len(units) == 1 and units[0].get('text') == record['unit_text'],
            'v34 target unit binding invalid')


def authenticate_context(c):
    require(isinstance(c, dict) and c.get('text'), 'v34 context text absent')
    require(c.get('source_path') and file_sha(c['source_path']) == c.get('source_sha256'),
            'v34 context source hash invalid')
    require(c.get('candidate_path') and file_sha(c['candidate_path']) == c.get('candidate_sha256'),
            'v34 context candidate hash invalid')
    require(c.get('pages') or c.get('source_lines'), 'v34 context locator absent')
    try:
        literal = (norm(c['text']) in norm(authenticated_source_text(c['source_path'])) or
                   norm(c['text']) in norm(alternative_pdf_text(c['source_path'])))
    except ValueError:
        literal = False
    layout=None
    if not literal and Path(c['source_path']).suffix.lower()=='.pdf':
        try:
            result=reconstruct_pdf(c['source_path'])
            if result and norm(c['text']) in norm(result['text']):layout=result
        except (FileNotFoundError,subprocess.CalledProcessError):
            pass
    review = c.get('verification', {})
    prior_review_bound = (review.get('verified') is True and bool(review.get('method')) and
                          any(p.get('id') == c.get('paragraph_id') and p.get('text') == c['text']
                              for p in candidate(c['candidate_path']).get('paragraphs', [])))
    require(literal or layout or prior_review_bound,
            'v34 literal extraction unavailable and no source-review certificate bound to candidate paragraph')
    out = copy.deepcopy(c)
    out['authentication_v34'] = {
        'method': ('actual_source_literal_reproduced' if literal else
                   'layout_reconstructed_source_literal_reproduced' if layout else
                   'prior_source_review_certificate_bound_to_actual_files_and_candidate_paragraph'),
        'literal_reproduced_in_current_runtime': literal,
        'layout_reconstructed_literal_reproduced':bool(layout),
        'supplied_source_suffix':Path(c['source_path']).suffix.lower(),
        'prior_source_review_method':review.get('method') if not literal and not layout else None}
    if layout:
        out['authentication_v34']['layout_reconstruction']={k:v for k,v in layout.items() if k!='text'}
    return out


def following_list(record, shared, typed, log):
    cert = record.get('complete_following_list_v11')
    other = shared.get('complete_following_list_v11')
    if cert is None and other is None:
        return False
    require(cert == other, 'v34 following list differs across methods')
    require(isinstance(cert, dict), 'v34 following list must be an object')
    require(cert.get('original_unit_sha256') == digest(record['unit_text']), 'v34 stale following list')
    source_sha = record.get('unit_source_sha256') or record.get('source_sha256')
    require(cert.get('source_sha256') == source_sha, 'v34 following source differs')
    contexts = cert.get('contexts', [])
    require(contexts and cert.get('contexts_sha256') == payload_digest(contexts),
            'v34 following list content hash differs')
    require(cert.get('repair_status') == 'supplemented' and cert.get('unresolved_material_gaps') == [],
            'v34 unresolved following list')
    boundary = cert.get('structure_boundary', {})
    require(boundary.get('all_paragraphs_in_interval_included') is True and
            boundary.get('first_paragraph') == contexts[0].get('paragraph_id') and
            boundary.get('last_paragraph') == contexts[-1].get('paragraph_id'),
            'v34 following interval not complete')
    authenticated = [authenticate_context(c) for c in contexts]
    require(all(c['source_sha256'] == source_sha for c in contexts), 'v34 following list mixed sources')
    cp = record['candidate_file']
    paragraphs = candidate(cp).get('paragraphs', [])
    indexes = [i for i,p in enumerate(paragraphs) if p.get('id') == boundary['first_paragraph']]
    require(len(indexes) == 1, 'v34 following first paragraph not unique')
    start = indexes[0]
    actual = paragraphs[start:start+len(contexts)]
    require(len(actual) == len(contexts) and
            all(p.get('id') == c.get('paragraph_id') and p.get('text') == c['text']
                for p,c in zip(actual,contexts)), 'v34 following candidate interval differs')
    next_p = paragraphs[start+len(contexts)] if start+len(contexts) < len(paragraphs) else None
    require(next_p is not None and next_p.get('id') == boundary.get('next_paragraph_id') and
            next_p.get('text') == boundary.get('next_paragraph_text'), 'v34 following next boundary differs')
    positions = [i for i,c in enumerate(contexts) if norm(record['unit_text']) in norm(c['text'])]
    require(len(positions) == 1 and positions[0] == 0 and len(contexts) > 1,
            'v34 current item must uniquely introduce its following interval')
    typed.append({'field': 'complete_following_list_v11', 'role': 'current_following_conditions_only',
                  'contexts': authenticated, 'current_unit_sha256': digest(record['unit_text']),
                  'labels_may_be_copied': False})
    log.append({'field': 'complete_following_list_v11', 'authenticated': True,
                'usage': 'completeness_gate_only', 'dimension_assignment': False})
    return True


def reference_role(text):
    # Navigation is kept visible but cannot license positive dimensions.
    if re.search(r'参见|详见|见附件|参阅|下载|查阅|网址|链接', text) and not re.search(r'须|必须|应当|符合|满足|按照.*执行',text):
        return 'navigation_preview_only'
    substantive = re.search(r'评价|评估|比较|审查|(?:应当|应|将|予以|决定|确定)(?:调出|退出|纳入)|实际给付|持续供应', text)
    if re.search(r'申报|申请|填报|报送|上传|选择|提交',text) and not substantive:
        return 'current_administrative_eligibility_reference'
    if substantive and re.search(r'符合|满足|须|必须|应当|按照|按|依据',text):
        return 'current_substantive_condition_reference'
    return 'unclassified_explicit_reference_needs_relation_review'


def references(record, shared, typed, log):
    for field in ('explicitly_cited_articles_v10', 'explicitly_cited_qualifications_v12'):
        value = record.get(field, shared.get(field))
        if value is None:
            continue
        if field in record and field in shared:
            require(record[field] == shared[field], 'v34 explicit references differ across methods')
        if isinstance(value, dict):
            require(value.get('current_unit_sha256', digest(record['unit_text'])) == digest(record['unit_text']),
                    'v34 stale explicit reference')
            groups = value.get('references', [])
            if field.endswith('_v12'):
                require(value.get('references_sha256') == payload_digest(groups),
                        'v34 explicit reference payload hash differs')
                for key, expected in (
                    ('current_unit_id',record.get('unit_id')),
                    ('current_unit_source_path',record.get('unit_source') or record.get('source')),
                    ('current_unit_source_sha256',record.get('unit_source_sha256') or record.get('source_sha256')),
                    ('current_unit_candidate_path',record.get('candidate_file')),
                    ('current_unit_candidate_sha256',record.get('candidate_sha256'))):
                    require(value.get(key) == expected, 'v34 explicit reference target version differs')
        else:
            groups = value
        require(isinstance(groups, list) and groups, 'v34 explicit references missing')
        if all(isinstance(c,dict) and c.get('text') for c in groups):
            groups = [{'contexts': groups}]
        n = 0
        for group in groups:
            contexts = group.get('contexts', [])
            require(contexts, 'v34 empty explicit reference group')
            authenticated = [authenticate_context(c) for c in contexts]
            boundary = group.get('structure_boundary')
            complete = False
            if boundary is not None:
                require(boundary.get('all_paragraphs_in_interval_included') is True,
                        'v34 reference interval incomplete')
                require(len({c['candidate_path'] for c in contexts}) == 1,
                        'v34 reference interval mixed candidates')
                paragraphs = candidate(contexts[0]['candidate_path']).get('paragraphs', [])
                first = boundary.get('first_paragraph_id')
                indexes = [i for i,p in enumerate(paragraphs) if p.get('id') == first]
                require(len(indexes) == 1, 'v34 reference first paragraph not unique')
                start = indexes[0]
                actual = paragraphs[start:start+len(contexts)]
                require(len(actual) == len(contexts) and
                        all(p.get('id') == c.get('paragraph_id') and p.get('text') == c['text']
                            for p,c in zip(actual,contexts)) and
                        actual[-1].get('id') == boundary.get('last_paragraph_id'),
                        'v34 reference candidate interval differs')
                following = paragraphs[start+len(contexts)] if start+len(contexts) < len(paragraphs) else None
                require(following is not None and
                        following.get('id') == boundary.get('next_candidate_paragraph_id') and
                        following.get('text') == boundary.get('next_candidate_paragraph_text'),
                        'v34 reference next boundary differs')
                complete = True
            typed.append({'field': field, 'role': reference_role(record['unit_text']),
                          'reference_address': group.get('reference_address'),
                          'contexts': authenticated, 'current_unit_sha256': digest(record['unit_text']),
                          'complete_interval_authenticated': complete,
                          'labels_may_be_copied': False})
            n += len(contexts)
        log.append({'field':field,'authenticated':True,'context_n':n,
                    'usage':'typed_reference_resolution_only','dimension_assignment':False})


def local_source_family(record,shared,typed,log,out):
    cert=record.get('source_local_list_family_v13')
    parents=[p for p in record.get('verified_parent_context',[])
             if str(p.get('repair_version','')).startswith('v13')]
    if cert is None:
        require(not parents,'v34 v13 parent requires its actual local source-family certificate')
        return
    require(cert==shared.get('source_local_list_family_v13'),'v34 local family differs across methods')
    require(record.get('verified_parent_context')==shared.get('verified_parent_context'),
            'v34 local family parents differ across methods')
    for key,expected in (('current_unit_id',record.get('unit_id')),
                         ('current_unit_sha256',digest(record['unit_text'])),
                         ('source_path',record.get('unit_source') or record.get('source')),
                         ('source_sha256',record.get('unit_source_sha256') or record.get('source_sha256')),
                         ('candidate_path',record.get('candidate_file')),
                         ('candidate_sha256',record.get('candidate_sha256'))):
        require(cert.get(key)==expected,'v34 local family target/source binding differs')
    contexts=cert.get('contexts',[])
    require(contexts and cert.get('contexts_sha256')==payload_digest(contexts),
            'v34 local family payload hash differs')
    heading=cert.get('actual_heading');predicate=cert.get('actual_parent_predicate')
    siblings=cert.get('actual_list_siblings',[])
    require(contexts==[heading,predicate,*siblings] and siblings,'v34 local family structure differs')
    actual=[authenticate_context(c) for c in contexts]
    paragraphs=candidate(record['candidate_file']).get('paragraphs',[])
    boundary=cert.get('structure_boundary',{})
    indexes=[i for i,p in enumerate(paragraphs) if p.get('id')==boundary.get('first_paragraph')]
    require(len(indexes)==1 and boundary.get('all_paragraphs_in_interval_included') is True,
            'v34 local family interval unavailable')
    start=indexes[0];interval=paragraphs[start:start+len(contexts)]
    require(len(interval)==len(contexts) and all(p.get('id')==c.get('paragraph_id') and p.get('text')==c['text']
            for p,c in zip(interval,contexts)) and interval[-1]['id']==boundary.get('last_paragraph'),
            'v34 local family exact candidate interval differs')
    following=paragraphs[start+len(contexts)] if start+len(contexts)<len(paragraphs) else None
    next_boundary=boundary.get('next_boundary',{})
    require(following is not None and following.get('id')==next_boundary.get('paragraph_id') and
            following.get('text')==next_boundary.get('text') and
            boundary.get('actual_source_bullet_count')==len(siblings),'v34 local family end/bullet count differs')
    for p in parents:
        require(p.get('unit_id')==record.get('unit_id') and p.get('original_unit_sha256')==digest(record['unit_text']) and
                p.get('text_sha256')==digest(p.get('text','')) and p.get('text')==predicate['text'] and
                p.get('paragraph_id')==predicate['paragraph_id'],'v34 v13 local parent certificate differs')
        authenticate_context(p)
    require(parents,'v34 local family lacks its current predicate parent')
    image=cert.get('source_image_evidence')
    if image:
        require(file_sha(image.get('path',''))==image.get('sha256') and
                image.get('actual_pdf_page') in heading.get('pages',[]),'v34 local visual evidence binding differs')
    target=next(u for u in candidate(record['candidate_file'])['unit_candidates'] if u.get('id')==record.get('unit_id'))
    member=next((c for c in actual[2:] if c.get('paragraph_id')==target.get('paragraph_id') and
                 norm(record['unit_text']) in norm(c['text'])),None)
    typed.append({'field':'source_local_list_family_v13','role':'current_local_list_predicate',
                  'contexts':actual,'parent_predicate':actual[1],'target_is_list_child':member is not None,
                  'current_list_member':member,'current_unit_sha256':digest(record['unit_text']),
                  'labels_may_be_copied':False})
    log.append({'field':'source_local_list_family_v13','authenticated':True,
                'usage':'actual_local_predicate_and_list_membership_only','dimension_assignment':False})


def _v14_api():
    return require,digest,file_sha,candidate,norm,payload_digest,authenticate_context


def local_family_v14(record,shared,typed,log):
    from source_family_v14 import local_family
    return local_family(record,shared,typed,log,_v14_api())


def component_v14(record,shared,typed,log):
    from source_family_v14 import component
    return component(record,shared,typed,log,_v14_api())


def prepare(record):
    out = prepare_v33(record)
    shared = record.get('llm_v29_shared_context', {})
    fields = ('complete_following_list_v11', 'explicitly_cited_articles_v10',
              'explicitly_cited_qualifications_v12','source_local_list_family_v13',
              'source_local_list_family_v14','source_component_boundary_v14')
    new_local_parents=any(str(p.get('repair_version','')).startswith('v13') for p in record.get('verified_parent_context',[]))
    if not any(k in record or k in shared for k in fields) and not shared.get('structured_following_units') and not new_local_parents:
        return out
    authenticate_target(record)
    typed, log = [], []
    local_source_family(record,shared,typed,log,out)
    local_family_v14(record,shared,typed,log)
    component_v14(record,shared,typed,log)
    out['verified_complete_following_list_v34'] = following_list(record, shared, typed, log)
    references(record, shared, typed, log)
    previews = shared.get('structured_following_units', [])
    if previews:
        typed.append({'field':'structured_following_units','role':'navigation_preview_only',
                      'contexts':copy.deepcopy(previews),'authenticated':False,
                      'labels_may_be_copied':False})
        log.append({'field':'structured_following_units','authenticated':False,
                    'usage':'preview_only_not_a_completeness_certificate','dimension_assignment':False})
    out['typed_contexts_v34'] = typed
    out['source_field_consumption_v34'] = log
    return out
