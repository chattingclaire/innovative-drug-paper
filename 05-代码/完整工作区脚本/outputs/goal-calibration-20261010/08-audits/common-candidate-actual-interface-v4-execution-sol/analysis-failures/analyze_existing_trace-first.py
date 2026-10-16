"""Read already generated traces and exact quote bytes; no classifier imports."""
import hashlib
import json
from pathlib import Path

D=Path(__file__).resolve().parent
BASE=D.parents[1]
CODE=BASE/'06-coding/rule-five-dimension-joint-root/versions/joint-v4-structure-normalization-sol'

def bind(p):
    b=p.read_bytes()
    return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}

def write(name,value):
    p=D/name
    if p.exists(): raise RuntimeError('Preserve prior trace analysis: '+str(p))
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def main():
    results=json.loads((D/'execution-results.json').read_bytes())
    reports=[];allchecks=[]
    for row in results:
        rid=row['record_id']
        unit=json.loads((D/'semantic-units'/(rid+'.json')).read_bytes())
        byid={c['context_id']:c for c in unit['contexts']}
        standard=[r for r in row['trace']['relations'] if r['kind']=='cited_standard'
            and r['details'].get('resolution_path')=='primary_literal_complete_operative_standard']
        assert len(standard)==1
        relation=standard[0]
        details=relation['details']
        assert details.get('SE_scope_verified') is None
        request=[r for r in row['trace']['source_requests'] if r.get('resolution_path')=='primary_literal_complete_operative_standard']
        assert len(request)==1 and request[0]['dependency_status']=='resolved'
        assert row['trace']['material_requests']==[]
        quotechecks=[]
        for source,path in [(relation['context_evidence'],'relation/context_evidence'),(request[0]['evidence'],'request/evidence')]:
            for i,q in enumerate(source):
                c=byid[q['context_id']]
                assert c['kind']=='source_textleaf' and q['text']==c['text'][q['start']:q['end']]
                locator=q['source_ref']['locator']
                p=Path(locator['snapshot_absolute_path'])
                raw=p.read_bytes();text=raw.decode('utf8',errors='strict')
                assert bind(p)['sha256']==locator['snapshot_sha256']==q['source_ref']['sha256']
                l0,l1=locator['unicode_code_point_interval_half_open']
                assert text[l0:l1]==c['text']
                start,end=l0+q['start'],l0+q['end']
                assert text[start:end]==q['text']
                item={'record_id':rid,'path':path+'/'+str(i),'context_id':q['context_id'],
                    'text':q['text'],'original_source':bind(p),'actual_unicode_interval_half_open':[start,end],
                    'actual_utf8_interval_half_open':[len(text[:start].encode()),len(text[:end].encode())],
                    'actual_line_range_1based':[text[:start].count('\n')+1,text[:end].count('\n')+(0 if text[:end].endswith('\n') else 1)],
                    'literal_text_and_identity_verified':True}
                quotechecks.append(item);allchecks.append(item)
        rawpath=Path(relation['context_evidence'][0]['source_ref']['locator']['snapshot_absolute_path'])
        rawtext=rawpath.read_bytes().decode('utf8')
        lines=rawtext.splitlines(keepends=True)
        safety_line=15 if rid!='RECODE25-00045' else 33
        next_boundary_line=18 if rid!='RECODE25-00045' else 36
        next_paragraph_line=None if rid!='RECODE25-00045' else 35
        group_end=details['selected_group_snapshot_span'][1]
        heading=rawtext[group_end:].splitlines()[0]
        assert heading==lines[next_boundary_line-1].rstrip('\r\n')
        safety=lines[safety_line-1]
        assert safety in details['standard_text']
        boundary={'source':bind(rawpath),'actual_next_section_line':next_boundary_line,
            'actual_next_section_text':lines[next_boundary_line-1],
            'parser_group_end_snapshot_codepoint':group_end,
            'next_section_original_text_starts_at_parser_group_end':True,
            'boundary_quote_supplied_in_relation':False}
        if next_paragraph_line:
            boundary.update(actual_next_paragraph_after_numbered_members_line=next_paragraph_line,
                actual_next_paragraph_text=lines[next_paragraph_line-1],
                'parser_group_includes_following_status_list_paragraph':lines[next_paragraph_line-1] in details['standard_text'])
        reports.append({'record_id':rid,'actual_S':row['actual_S'],'historical_expected_S':1,
            'assessment':'规则遗漏依据','not_missing_original_material':True,'not_NULL':True,
            'current':unit['text'],'current_standard_family':details['standard_family'],
            'safety_original_source_line':safety_line,'safety_original_quote':safety,
            'safety_quote_present_in_actual_generated_cited_standard':True,
            'actual_standard_relation_details':{k:v for k,v in details.items() if k not in ['content','standard_text']},
            'actual_resolved_request_path':'primary_literal_complete_operative_standard',
            'actual_next_original_boundary':boundary,
            'direct_execution_gap':{
                'producer':str(CODE/'relations.py')+':659 _operative_references -> _primary_standard_group',
                'producer_generates_relation':True,
                'not_supplied':['SE_scope_verified','closure_proof','explicit boundary quote'],
                'consumer_gate':str(CODE/'dimensions.py')+':857 _se_allowed: cited_standard requires SE_scope_verified',
                'exclusion_path':str(CODE/'dimensions.py')+':425 _safety_effect calls acc.exclude after gate rejection',
                'final_basis_path':row['decisions']['S']['basis_path'],
                'classification_unchanged':True},
            'scope_only_repair_proposal':'Enrich the already existing neutral literal-group parser with same-version/component/current-action and exact next-boundary receipts, separate consumed members from boundary-only text, then publish the proof through existing SE_scope_verified/closure_proof consumer protocol. Do not bypass the gate for arbitrary cited_standard, assign labels from programme names, inject inputs, or reuse sibling paragraphs as content.',
            'proposal_executed':False})
    write('trace-original-quote-readback.json',allchecks)
    write('actual-S3-consumer-gap.json',reports)
    print(json.dumps({'existing_traces_analyzed':3,'original_relation_and_request_quotes_checked':len(allchecks),
        'new_judge_calls':0,'confirmed_missing_consumer_proof_wiring':3},ensure_ascii=False))

if __name__=='__main__':main()
