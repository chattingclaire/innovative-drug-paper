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
             e['physical_page'] in paragraph.get('pages',[]) and e['paragraph_text_sha256']==paragraph_sha]
    if not matches: return None
    if len(matches)!=1: raise ValueError('ambiguous visual source certificate')
    e=matches[0]
    for path_key,sha_key in [('transcription_path','transcription_sha256'),('rendered_page_path','rendered_page_sha256'),('provenance_record_path','provenance_record_sha256')]:
        if _sha_bytes(e[path_key])!=e[sha_key]: raise ValueError('visual certificate asset bytes changed')
    if norm(Path(e['transcription_path']).read_text())!=norm(paragraph['text']):
        raise ValueError('visual transcription does not reproduce bound paragraph')
    return dict(text=paragraph['text'],paragraph_id=paragraph['id'],source_path=source,
        source_sha256=actual,candidate_path=record['candidate_file'],candidate_sha256=record['candidate_sha256'],
        pages=paragraph.get('pages',[]),source_lines=paragraph.get('line_ids',[]),
        actual_bound_locator_reproduced=True,visual_transcription_certificate=e,
        authentication_v34=dict(method='source_sha_physical_page_paragraph_sha_visual_transcription',
            source_file_exists_and_sha_matches=True,candidate_file_exists_and_sha_matches=True,
            literal_reproduced_in_current_runtime=False,layout_reconstructed_literal_reproduced=False,
            visual_transcription_reproduced_in_current_runtime=True,prior_review_certificate_used=False,
            source_provenance=e['source_provenance'],review_type=e['review_type']))
