"""Authenticate page-bounded PDF regions for a differently structured carrier.

The registry selects physical source/paragraph bindings, never labels or IDs.
Every call re-reads actual PDF bytes and compares the full bounded region.
"""
import hashlib,json,re,subprocess,unicodedata
from pathlib import Path

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(text):return hashlib.sha256(text.encode()).hexdigest()
def normalized(text):
    return ''.join(c for c in unicodedata.normalize('NFKC',text) if not c.isspace()).translate(
        str.maketrans({'，':',','。':'.','；':';','：':':'}))
def require(value,message):
    if not value:raise ValueError('cross-carrier source: '+message)

def authenticate_cross_carrier_paragraph(record,paragraph,doc):
    source=record.get('unit_source') or record.get('source')
    source_sha=record.get('unit_source_sha256') or record.get('source_sha256')
    entries=json.loads(Path(__file__).with_name('cross_carrier_certificates.json').read_text())['certificates']
    matched=[e for e in entries if e['pdf_source']['path']==source and
             e['pdf_source']['sha256']==source_sha and
             [e['pdf_source']['physical_page']]==paragraph.get('pages',[]) and
             e['candidate_carrier']['candidate_json_sha256']==record['candidate_sha256']]
    if not matched:return None
    require(len(matched)==1,'ambiguous page-bounded region')
    return verify_cross_carrier_entry(record,paragraph,doc,matched[0])

def verify_cross_carrier_entry(record,paragraph,doc,entry):
    pdf=entry['pdf_source'];carrier=entry['candidate_carrier'];region=entry['page_bounded_region']
    source=record.get('unit_source') or record.get('source')
    require(source==pdf['path'] and sha(source)==pdf['sha256']==
            (record.get('unit_source_sha256') or record.get('source_sha256')),'actual PDF SHA/path differs')
    require(record['candidate_file']==carrier['candidate_json_path'] and
            sha(record['candidate_file'])==record['candidate_sha256']==carrier['candidate_json_sha256'],
            'actual candidate SHA/path differs')
    require(sha(carrier['txt_path'])==carrier['txt_sha256'] and
            doc['source']==carrier['txt_path'] and doc['source_sha256']==carrier['txt_sha256'],
            'actual carrier TXT binding differs')
    page=pdf['physical_page'];require(type(page) is int and page>0 and paragraph.get('pages')==[page],
                                    'physical page binding differs')
    raw=subprocess.run(['pdftotext','-raw','-f',str(page),'-l',str(page),source,'-'],
                       check=True,capture_output=True,text=True).stdout
    text=normalized(raw);start=normalized(region['start_anchor']);end=normalized(region['end_boundary_exclusive'])
    require(start and end and text.count(start)==text.count(end)==1,'page anchors are not unique')
    begin=text.index(start);stop=text.index(end);require(stop>begin,'page boundaries are reversed')
    bounded=text[begin:stop]
    require(digest(bounded)==region['cross_carrier_normalized_paragraph_sha256'],
            'actual full PDF region hash differs')
    paragraphs=doc.get('paragraphs',[]);ids=[p['id'] for p in paragraphs]
    if carrier.get('paragraph_interval'):
        first,last=carrier['paragraph_interval'];require(ids.count(first)==ids.count(last)==1,
                                                       'candidate interval endpoints are not unique')
        interval=paragraphs[ids.index(first):ids.index(last)+1]
    else:
        interval=[p for p in paragraphs if p['id']==carrier.get('paragraph_id')]
        require(len(interval)==1,'candidate full paragraph is not unique')
    require(interval and any(p==paragraph for p in interval),'current paragraph outside the bounded carrier interval')
    whole=''.join(p['text'] for p in interval)
    require(normalized(whole)==bounded,'complete candidate region differs from actual PDF region')
    current=normalized(record['unit_text']);part=normalized(paragraph['text'])
    require(current and text.count(current)==bounded.count(current)==1 and
            part and bounded.count(part)==1,'current unit/paragraph not unique in the actual region')
    if entry.get('complete_members'):
        members=entry['complete_members'];require(len(interval)==len(members)+1,'complete member count differs')
        require(all(p['text']==m['text'] and digest(m['text'])==m['text_sha256']
                    for p,m in zip(interval[1:],members)),'complete actual member texts differ')
        require(digest(whole)==entry['list_closure']['full_article_candidate_text_sha256'],
                'full candidate article hash differs')
        order=[normalized(marker) for marker in entry['list_closure']['expected_order']]
        require(all(bounded.count(marker)==1 for marker in order) and
                [bounded.index(marker) for marker in order]==sorted(bounded.index(marker) for marker in order),
                'complete member markers are not unique and ordered')
        actual_markers=re.findall(r'\(([一二三四五六七八九十]+)\)',bounded)
        require(['('+m+')' for m in actual_markers]==order,'additional or omitted list marker')
    return dict(text=paragraph['text'],paragraph_id=paragraph['id'],source_path=source,
        source_sha256=pdf['sha256'],candidate_path=record['candidate_file'],candidate_sha256=record['candidate_sha256'],
        pages=[page],source_lines=[],actual_bound_locator_reproduced=True,
        cross_carrier_locator=dict(physical_page=page,start_anchor=region['start_anchor'],
            end_boundary_exclusive=region['end_boundary_exclusive'],bounded_normalized_sha256=digest(bounded),
            normalization='NFKC_no_whitespace_CJK_comma_period_semicolon_colon_to_ASCII',
            paragraph_normalized_sha256=digest(part),candidate_paragraph_ids=[p['id'] for p in interval],
            source_extractor='pdftotext -raw physical page only',txt_lines_are_pdf_locators=False),
        authentication_v34=dict(method='actual_pdf_page_unique_anchors_and_full_region_reproduced',
            literal_reproduced_in_current_runtime=False,layout_reconstructed_literal_reproduced=True,
            prior_review_fallback_accepted=False,dimension_assignment=False,actual_physical_page_sha256=digest(raw)))
