"""Generic finite visual source certificates; no corpus ID or filename gate."""
import hashlib,json
from pathlib import Path
from source_context_adapter_v33 import norm

def _sha_bytes(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def authenticate_visual_paragraph(record,paragraph):
    source=record.get('unit_source') or record.get('source')
    expected=record.get('unit_source_sha256') or record.get('source_sha256')
    actual=_sha_bytes(source)
    if actual!=expected: raise ValueError('visual source bytes SHA changed')
    paragraph_sha=hashlib.sha256(paragraph['text'].encode()).hexdigest()
    entries=json.loads(Path(__file__).with_name('visual_transcriptions.json').read_text())['entries']
    matches=[e for e in entries if e['source_sha256']==actual and
             (e.get('physical_pages') or [e['physical_page']])==paragraph.get('pages',[]) and
             e['paragraph_text_sha256']==paragraph_sha]
    if not matches: return None
    if len(matches)!=1: raise ValueError('ambiguous visual source certificate')
    return verify_visual_entry(record,paragraph,matches[0])

def verify_visual_entry(record,paragraph,e):
    source=record.get('unit_source') or record.get('source')
    actual=_sha_bytes(source)
    pages=e.get('physical_pages') or [e['physical_page']]
    if (actual!=(record.get('unit_source_sha256') or record.get('source_sha256')) or
        e['source_sha256']!=actual or pages!=paragraph.get('pages',[]) or
        pages!=sorted(set(pages)) or
        e['paragraph_text_sha256']!=hashlib.sha256(paragraph['text'].encode()).hexdigest()):
        raise ValueError('visual source/page/paragraph binding differs')
    if _sha_bytes(record['candidate_file'])!=record['candidate_sha256']:
        raise ValueError('visual target candidate bytes changed')
    if e.get('candidate_path') and (e['candidate_path']!=record['candidate_file'] or
                                  e.get('candidate_sha256')!=record['candidate_sha256']):
        raise ValueError('visual registered candidate binding differs')
    for path_key,sha_key in [('transcription_path','transcription_sha256'),('provenance_record_path','provenance_record_sha256')]:
        if _sha_bytes(e[path_key])!=e[sha_key]: raise ValueError('visual certificate asset bytes changed')
    rendered=e.get('rendered_pages') or [dict(physical_page=e['physical_page'],
        path=e['rendered_page_path'],sha256=e['rendered_page_sha256'])]
    if [p['physical_page'] for p in rendered]!=pages:
        raise ValueError('visual certificate rendered page set differs')
    for page in rendered:
        if _sha_bytes(page['path'])!=page['sha256']:
            raise ValueError('visual certificate rendered page bytes changed')
    if norm(Path(e['transcription_path']).read_text())!=norm(paragraph['text']):
        raise ValueError('visual transcription does not reproduce bound paragraph')
    return dict(text=paragraph['text'],paragraph_id=paragraph['id'],source_path=source,
        source_sha256=actual,candidate_path=record['candidate_file'],candidate_sha256=record['candidate_sha256'],
        pages=paragraph.get('pages',[]),source_lines=[],
        actual_bound_locator_reproduced=True,visual_transcription_certificate=e,
        authentication_v34=dict(method='source_sha_physical_page_paragraph_sha_visual_transcription',
            source_file_exists_and_sha_matches=True,candidate_file_exists_and_sha_matches=True,
            literal_reproduced_in_current_runtime=False,layout_reconstructed_literal_reproduced=False,
            visual_transcription_reproduced_in_current_runtime=True,prior_review_certificate_used=False,
            source_provenance=e['source_provenance'],review_type=e['review_type'],
            normalizations=e.get('normalizations'),text_layer_contiguous_extraction_claimed=False,
            all_rendered_pages_sha_verified=True))
