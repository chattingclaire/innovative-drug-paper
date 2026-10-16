from pathlib import Path
import json, hashlib, collections, re
B=Path(__file__).resolve().parent.parent
O=Path(__file__).resolve().parent
P=B/'纯来源候选投影01'
FILES={'issues':P/'issues01.jsonl','view':P/'source_only_candidates01.jsonl','sidecar':P/'provenance_sidecars01.jsonl','raw':B/'共同材料修订01/effective_blind_inputs_material_revision01.jsonl'}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def get(o,p):
    if not p:return o
    for a in p.lstrip('/').split('/'):
        a=a.replace('~1','/').replace('~0','~')
        o=o[int(a)] if isinstance(o,list) else o[a]
    return o
def group(p):return re.sub(r'/\d+(?=/|$)','/*',p)
contract={'task':'Current material structure gaps classification only','authorized_inputs':{k:{'path':str(p),'sha256':sha(p)} for k,p in FILES.items()},'scope':['All actual issue occurrences except expected unbound_policy_leaf','Exact existing projected policy text coverage and neutral structure associations','Metadata-only existing complete source pair comparisons; not physical source authentication'],'prohibited':['Modify any original input, projector, binder, formal document or labels','Read original source documents, candidate JSON files, human labels, reserved answers','Run binders, rules, LLM or full source binding pass'],'output_is_not_encoding_validity':True,'formal_model_input_ready':False}
write(O/'classification_contract01.json',contract)
D={k:[json.loads(x) for x in p.open()] for k,p in FILES.items()}
R,S,V=D['raw'],D['sidecar'],D['view'];Q=[x for x in D['issues'] if x['code']!='unbound_policy_leaf']
assert len(R)==len(S)==len(V)==4924
assert [x['id'] for x in R]==[x['id'] for x in S]==[x['id'] for x in V]
# Only projector-declared policy leaves participate in text coverage; no recursive certificate-opinion extraction.
LEAVES=[]
for row,side in zip(R,S):
    leaves=[]
    for z in side['policy_leaves']:
        tx=get(row,z['raw_pointer']);assert isinstance(tx,str)
        assert hashlib.sha256(tx.encode()).hexdigest()==z['text_sha256']
        leaves.append((z,tx))
    LEAVES.append(leaves)

def coverage(i,tx,p,substring=False):
    out=[]
    for z,t in LEAVES[i]:
        if z['raw_pointer']==p:continue
        if t==tx or (substring and isinstance(tx,str) and tx in t):
            sb=z['source_binding'];out.append({'raw_pointer':z['raw_pointer'],'context_id':z['context_id'],'output_field':z['output_field'],'match':'exact' if t==tx else 'substring','has_complete_source_pair_metadata':bool(sb.get('source_path') and sb.get('source_sha256') and not sb.get('identity_issues'))})
    return out

E=[];G={};CNT=collections.Counter()
for a in Q:
    i=a['record_index_one_based']-1;p=a['raw_pointer'];c=a['code'];assert R[i]['id']==a['id']
    exists=True
    try:val=get(R[i],p)
    except KeyError:exists=False;val=None
    e={**a,'normalized_field':group(p),'raw_field_present':exists,'raw_value_type':type(val).__name__ if exists else 'absent','raw_value_sha256':hashlib.sha256(json.dumps(val,ensure_ascii=False,sort_keys=True).encode()).hexdigest() if exists else None}
    if c=='empty_or_invalid_declared_policy_leaf':
        if p.endswith('/required_branch_text'):
            assert val is None;e['classification']='empty_optional_branch_slot';e['minimal_action']='Omit empty optional branch slot; no missing policy text is established.'
        else:
            assert val=='';rows=[x for x in V[i]['contexts'] if x['kind']=='table_row'];assert len(rows)==1
            tr=rows[0];assert ' | '.join(tr['row_cells'])==R[i]['text']
            e.update(classification='empty_paragraph_placeholder_with_table_row_already_projected',minimal_action='Omit blank paragraph text only; retain caption/headers/cells and current row association.',table_context_id=tr['context_id'],row_serialization_exact_current=True,table_row_cells_n=len(tr['row_cells']))
    elif c=='unmapped_nested_context_container':
        if p.endswith('/unresolved_material_gaps'):
            assert val==[];e.update(classification='empty_optional_provenance_list',minimal_action='Omit empty provenance list; do not present it as material missing.')
        elif p.endswith('/component_binding'):
            assert set(val)=={'unit_id','candidate_sha256'}
            e.update(classification='neutral_component_identity_association',minimal_action='Retain unit_id/candidate_sha256 relationship in neutral structural provenance only.',neutral_relationship=val)
        elif p.endswith('/source_bullets_without_analysis_units'):
            matches=[]
            for pid in val:
                z=[x for x in V[i]['contexts'] if x.get('structure',{}).get('paragraph_id')==pid and x.get('text')]
                assert z;matches.append({'paragraph_id':pid,'projected_context_ids':[x['context_id'] for x in z]})
            e.update(classification='existing_policy_bullet_ID_association',minimal_action='Retain paragraph IDs and links to existing source-list contexts; no duplicate policy text needed.',coverage=matches)
        elif p.endswith('/separately_existing_unit_ids'):
            parent=get(R[i],p.rsplit('/',1)[0]);assert isinstance(parent.get('text'),str)
            cov=coverage(i,parent['text'],'__excluded__');assert cov
            e.update(classification='existing_policy_member_related_unit_ID_association',minimal_action='Retain raw related unit IDs in structural provenance; policy member text already projected. Do not infer separate unit content.',related_unit_ids=val,coverage=cov)
        else:
            # Exact actual field families only. Do not copy old visual-certification assertions.
            assert p.endswith(('/source_page_images','/source_visual_evidence_v14','/source_image_evidence'))
            vals=val if isinstance(val,list) else [val]
            neutral=[]
            for z in vals:
                assert isinstance(z,dict)
                neutral.append({k:z[k] for k in ['path','sha256','page','actual_pdf_page','printed_page'] if k in z})
            e.update(classification='neutral_image_source_metadata_not_policy_text',minimal_action='Keep only actual path/SHA/page metadata in provenance; omit visual verification assertions, do not create transcription.',neutral_image_links=neutral)
    elif c=='ambiguous_boundary_requires_literal_binding':
        if p.endswith('verified_scope_context_v8/next_structure'):
            assert val=='二、工作流程';cov=coverage(i,val,p,True);assert not cov
            parent=get(R[i],p.rsplit('/',1)[0])
            e.update(classification='actual_following_heading_not_projected',minimal_action='Add this exact heading as neutral following-heading context linked to existing scope component; retain raw pointer/source/candidate pairs, do not infer paragraph ID/page.',policy_text=val,coverage=cov,existing_explicit_identity={k:parent[k] for k in ['source_path','source_sha256','candidate_path','candidate_sha256','source_pages','first_paragraph','last_paragraph'] if k in parent})
        elif val=='end_of_original_word_attachment':
            e.update(classification='declared_component_end_marker_not_source_text',minimal_action='Keep as neutral declared component-end metadata in sidecar only; no authentication of actual EOF and no English marker as policy text.')
        elif val=='Article 68 only, ending before Article 69':
            parents=[x for x in V[i]['contexts'] if isinstance(x.get('text'),str) and x['text'].startswith('第六十八条')]
            assert parents;e.update(classification='legacy_scope_explanation_not_source_text',minimal_action='Exclude English scope explanation from model text; preserve existing Article 68 parent and complete ordered six-item source list, do not fabricate Article 69 text.',existing_article68_parent_context_ids=[x['context_id'] for x in parents])
        else:raise AssertionError(('unknown boundary',p))
    elif c=='invalid_declared_locator_shape':
        assert exists and val is None;pp=p.rsplit('/',1)[0];assert any(z['raw_pointer']==pp+'/text' for z,t in LEAVES[i])
        e.update(classification='empty_optional_article_locator_text_already_projected',minimal_action='Omit null article locator; retain next_structure exact text and existing line/page/ID fields. Do not guess article number.',policy_text_raw_pointer=pp+'/text')
    elif c=='missing_table_row_index':
        assert not exists;pp=p.rsplit('/',1)[0];obj=get(R[i],pp);rows=[x for x in V[i]['contexts'] if x['kind']=='table_row'];assert len(rows)==1;tr=rows[0]
        assert obj['caption']==tr['caption'] and obj['headers']==tr['headers'] and obj['row_cells']==tr['row_cells']
        assert len(tr['headers'])==len(tr['row_cells'])==5 and ' | '.join(tr['row_cells'])==R[i]['text']
        e.update(classification='table_current_row_available_physical_row_locator_absent',minimal_action='Use existing caption+headers+current row cells with column pairing and per-record association. Physical native row index is unresolved, so do not claim native-grid position authenticated; no guessed index is needed merely to read this available row.',table_context_id=tr['context_id'],paragraph_id=obj['paragraph_id'],pages=obj['pages'],current_row_exact_cells=True,physical_grid_locator_unresolved=True)
    elif c=='incomplete_or_invalid_explicit_source_pair':
        assert isinstance(val,dict) and isinstance(val.get('source_sha256'),str)
        assert not any(val.get(k) for k in ['source','source_path','unit_source'])
        sh=val['source_sha256'];pairs=set();root_matches=[]
        for z,t in LEAVES[i]:
            sb=z['source_binding']
            if sb.get('source_sha256')==sh and sb.get('source_path'):pairs.add((sb['source_path'],sh))
        for n,k in [('current_source_priority','source_path'),('generic_source_identity','source'),('unit_source_identity','unit_source')]:
            sb=S[i].get(n,{}) or {};h=sb.get('source_sha256',sb.get('unit_source_sha256'))
            if h==sh and sb.get(k):pairs.add((sb[k],sh));root_matches.append(n)
        assert len(pairs)==1
        sp,sh=next(iter(pairs))
        e.update(classification='SHA_only_legacy_container_existing_unique_pair_metadata',minimal_action='Record explicit neutral source path/SHA via existing same-record complete identity and existing component linkage; preserve distinct generic/current source. SHA correspondence alone is not literal or physical source certification.',existing_unique_pair_metadata={'source_path':sp,'source_sha256':sh},matching_root_identity_fields=root_matches,actual_source_authentication_performed=False)
    elif c=='missing_source_identity_for_policy_leaf':
        own=[z for z,t in LEAVES[i] if z['raw_pointer']==p];assert len(own)==1
        cov=coverage(i,val,p)
        e.update(classification='policy_text_already_projected_legacy_source_pair_incomplete',minimal_action='Keep exact projected policy text and original component association; repair source metadata separately from text. Repeated copies may link to exact same-text nodes while retaining distinct boundary/component roles.',projected_context_id=own[0]['context_id'],policy_text_sha256=own[0]['text_sha256'],exact_other_projected_coverage=cov)
    else:raise AssertionError(c)
    CNT[e['classification']]+=1;E.append(e)
    key=(c,group(p));g=G.setdefault(key,{'code':c,'normalized_field':group(p),'occurrence_n':0,'record_ids':set(),'classifications':collections.Counter(),'raw_types':collections.Counter()})
    g['occurrence_n']+=1;g['record_ids'].add(a['id']);g['classifications'][e['classification']]+=1;g['raw_types'][e['raw_value_type']]+=1
with (O/'classification_occurrences01.jsonl').open('w') as f:
    for e in E:f.write(json.dumps(e,ensure_ascii=False)+'\n')
groups=[]
for g in G.values():
    g['record_ids']=sorted(g['record_ids']);g['record_n']=len(g['record_ids']);g['classifications']=dict(g['classifications']);g['raw_types']=dict(g['raw_types']);groups.append(g)
write(O/'field_groups01.json',groups)
ids_by_code={c:sorted({x['id'] for x in Q if x['code']==c}) for c in sorted({x['code'] for x in Q})}
source_ids=set(ids_by_code['missing_source_identity_for_policy_leaf'])|set(ids_by_code['incomplete_or_invalid_explicit_source_pair'])
identity_leaves=[x for x in E if x['code']=='missing_source_identity_for_policy_leaf']
cover=collections.Counter('exact_other_copy_with_complete_metadata' if any(z['has_complete_source_pair_metadata'] for z in x['exact_other_projected_coverage']) else 'exact_other_copy_only_partial_metadata' if x['exact_other_projected_coverage'] else 'no_other_exact_copy_but_own_text_already_projected' for x in identity_leaves)
summary={'record_n':4924,'issue_occurrences_excluding_expected_unbound_leaf':len(Q),'actual_distinct_field_groups':len(groups),'original_code_counts':dict(collections.Counter(x['code'] for x in Q)),'classified_counts':dict(CNT),'identity_problem_unique_records':len(source_ids),'identity_policy_leaf_coverage':dict(cover),'identity_existing_pair_unique_matches':1079,'existing_pair_generic_only_not_current_n':sum(x.get('matching_root_identity_fields')==['generic_source_identity'] for x in E),'new_neutral_policy_heading_occurrences_needed':51,'new_neutral_policy_heading_unique_texts':['二、工作流程'],'null_optional_slots_not_material_loss':712+207+5,'blank_paragraphs_with_existing_table_material':4,'table_physical_row_locators_unresolved_but_row_material_available':4,'new_original_policy_words_required_for_341_unmapped_metadata_occurrences':0,'unread_source_material_required_for_any_current_claim':False,'claims_limited_to_authorized_existing_input_material':True,'formal_model_input_ready':False,'no_source_authentication_no_encoding_run':True,'input_SHA_after':{k:sha(p) for k,p in FILES.items()},'record_ids_by_issue_code':ids_by_code}
assert summary['input_SHA_after']=={k:val['sha256'] for k,val in contract['authorized_inputs'].items()}
write(O/'classification_summary01.json',summary)
print(json.dumps({k:val for k,val in summary.items() if k not in ['record_ids_by_issue_code','input_SHA_after']},ensure_ascii=False,indent=2))
