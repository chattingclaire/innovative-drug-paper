"""One finite source-reader check. No dimension labels or LLM results used."""
import ast, copy, hashlib, json, re, subprocess, sys, traceback
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RT=ROOT/'runtime'
sys.path.insert(0,str(RT))
import common_innovation_relations14 as innovation
import common_guideline_scope11 as guideline
from source_context_adapter_v33 import norm,digest

INPUT=Path(__file__).with_name('规则待核输入21.jsonl')
records={row['id'][-5:]:row['input'] for row in map(json.loads,INPUT.read_text().splitlines())}
results=[]
fixtures=Path(__file__).with_name('source_controls');fixtures.mkdir(exist_ok=True)

def file_sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def add(name,function,expected_reject=False,predicate=None):
    try:
        actual=function()
        ok=not expected_reject and (predicate(actual) if predicate else True)
        results.append(dict(name=name,passed=bool(ok),expected='source_relation_rejected' if expected_reject else 'source_relation_reproduced',actual_type=type(actual).__name__,summary=actual if isinstance(actual,(bool,str,int)) else None))
    except Exception as error:
        results.append(dict(name=name,passed=expected_reject,expected='source_relation_rejected' if expected_reject else 'source_relation_reproduced',error_type=type(error).__name__,reason=getattr(error,'reason',str(error)),details=getattr(error,'details',{})))

def paragraph(record):
    doc,paras,index=innovation._document(record)
    return doc,paras[index]
def authenticate(record):
    doc,p=paragraph(record)
    return innovation._authenticate_paragraph(record,p,doc)
def changed_candidate(name,record,change):
    z=copy.deepcopy(record);doc=json.loads(Path(z['candidate_file']).read_text());change(doc)
    path=fixtures/(name+'.json');path.write_text(json.dumps(doc,ensure_ascii=False)+'\n')
    z['candidate_file']=str(path);z['candidate_sha256']=file_sha(path)
    return z
def inline(name,text):
    path=fixtures/(name+'.txt');path.write_text(text+'\n')
    doc=dict(source=str(path),source_sha256=file_sha(path),paragraphs=[dict(id='paragraph',text=text,line_ids=['L1'],source_lines=[1])],lines=[dict(id='L1',text=text,line=1)],unit_candidates=[dict(id='unit',paragraph_id='paragraph',text=text)])
    cp=fixtures/(name+'.json');cp.write_text(json.dumps(doc,ensure_ascii=False)+'\n')
    return dict(unit_source=str(path),unit_source_sha256=file_sha(path),source=str(path),source_sha256=file_sha(path),candidate_file=str(cp),candidate_sha256=file_sha(cp),unit_id='unit',unit_text=text)

add('registered_actual_annex_and_paragraph',lambda:authenticate(records['00834']))
wrong_sha=copy.deepcopy(records['00834']);wrong_sha['unit_source_sha256']='0'*64
add('registered_annex_wrong_actual_sha',lambda:authenticate(wrong_sha),True)
wrong_component=copy.deepcopy(records['00834']);wrong_component['unit_source']=wrong_component['source'];wrong_component['unit_source_sha256']=wrong_component['source_sha256']
add('current_unit_cannot_bind_to_container_instead_of_annex',lambda:authenticate(wrong_component),True)
z=records['00834'];doc,p=paragraph(z);line=p['line_ids'][0]
wrong_line=changed_candidate('different_component_line',z,lambda d:next(x for x in d['lines'] if x['id']==line).update(source_file=records['02074']['unit_source']))
add('candidate_line_from_different_source_component',lambda:authenticate(wrong_line),True)
cert=copy.deepcopy(records['00834']);c=cert['complete_following_list_v11'];c['contexts'].pop(1);c['contexts_sha256']=digest(json.dumps(c['contexts'],ensure_ascii=False,sort_keys=True))
add('complete_list_omitted_middle_member',lambda:innovation.resolve_current_contents(cert),True)
cert=copy.deepcopy(records['00834']);c=cert['complete_following_list_v11'];removed=c['contexts'].pop();c['contexts_sha256']=digest(json.dumps(c['contexts'],ensure_ascii=False,sort_keys=True));b=c['structure_boundary'];b['last_paragraph']=c['contexts'][-1]['paragraph_id'];b['next_paragraph_id']=removed['paragraph_id'];b['next_paragraph_text']=removed['text']
add('complete_list_truncated_before_next_enumerated_member',lambda:innovation.resolve_current_contents(cert),True)
for suffix in ['00846','00889','02086','02124']:
    add('actual_v27_complete_interval_'+suffix,lambda suffix=suffix:innovation.resolve_current_contents(records[suffix]),predicate=lambda d:bool(d and len(d['members'])>0))
add('actual_nested_outer_item_and_circled_conditions',lambda:innovation.resolve_current_contents(records['00103']),predicate=lambda d:len(d['members'])==2)
bad_inline=inline('non_contiguous_inline','新品种应当满足以下条件:1具有充分创新性;3具有明确治疗优势;')
add('inline_missing_number_not_accepted',lambda:innovation.resolve_current_contents(bad_inline),True)
good_inline=inline('parenthesized_inline','新品种应当满足以下条件:(1)具有充分创新性;(2)具有明确治疗优势;')
add('other_inline_parenthesized_format',lambda:innovation.resolve_current_contents(good_inline),predicate=lambda d:len(d['members'])==2)
add('actual_announcement_source_locator',lambda:authenticate(records['01380']))
add('actual_abbreviation_is_not_list_pointer',lambda:innovation.current_pointer(records['01380']['unit_text']),predicate=lambda value:value is False)
add('abbreviation_does_not_hide_separate_actual_list_pointer',lambda:innovation.current_pointer('本办法(以下简称办法)要求新品种满足以下条件:'),predicate=lambda value:value is True)
add('decorated_numeric_page_edge',lambda:guideline._layout_gap_only('—— 18 —'),predicate=bool)
add('page_edge_with_substantive_text_rejected',lambda:guideline._layout_gap_only('疗效证据遗漏\n—— 18 —'),predicate=lambda value:value is False)
add('actual_cross_page_paragraph',lambda:authenticate(records['03072']))
add('unrelated_figure_is_boundary_only',lambda:innovation.resolve_current_contents(records['03864']),predicate=lambda d:len(d['members'])==4 and d['actual_next_boundary']['content_adopted'] is False)
add('actual_same_sha_pdf_fallback',lambda:authenticate(records['04190']),predicate=lambda d:d['authentication_v34'].get('extraction_method')=='pypdf_same_sha_ordered_physical_page_lines')
doc,p=paragraph(records['04190']);wrong_page=copy.deepcopy(p);wrong_page['pages']=[5];lm={x['id']:copy.deepcopy(x) for x in doc['lines']}
for key in wrong_page['line_ids']:lm[key]['page']=5
raw=subprocess.run(['pdftotext','-layout',records['04190']['unit_source'],'-'],check=True,capture_output=True,text=True).stdout.split('\f')
add('pdf_fallback_cannot_move_current_paragraph_to_another_page',lambda:guideline._paragraph_context(records['04190'],wrong_page,lm,raw),True)
add('actual_explicit_purpose_scope_word_order',lambda:guideline.resolve_guideline_scope(records['02826']))
def scope_has_object(text):
    return any(guideline._INNOVATION_OBJECT.search(m.group()) and guideline._RESEARCH_OBJECT.search(m.group()) for m in guideline._self_scope_matches(text))
add('scope_object_only_inside_quoted_title_rejected',lambda:scope_has_object('为落实《支持创新药研发指南》,制定本指导原则。'),predicate=lambda value:value is False)
add('scope_declaration_cannot_cross_sentence',lambda:scope_has_object('指导创新药研发。制定本指导原则。'),predicate=lambda value:value is False)
add('negated_scope_support_declaration_rejected',lambda:scope_has_object('不支持创新药研发,制定本指导原则。'),predicate=lambda value:value is False)
add('unbound_scanned_page_stays_unresolved',lambda:authenticate(records['01459']),True)

report=dict(kind='source_reading_function_checks_only_not_validity',input_sha256=file_sha(INPUT),runtime_sha256={p.name:file_sha(p) for p in RT.iterdir() if p.is_file()},n_checks=len(results),n_passed=sum(r['passed'] for r in results),all_checks_pass=all(r['passed'] for r in results),checks=results)
Path(__file__).with_name('source_mechanism_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['kind','n_checks','n_passed','all_checks_pass']},ensure_ascii=False))
for row in results:
    if not row['passed']:print(json.dumps(row,ensure_ascii=False))
