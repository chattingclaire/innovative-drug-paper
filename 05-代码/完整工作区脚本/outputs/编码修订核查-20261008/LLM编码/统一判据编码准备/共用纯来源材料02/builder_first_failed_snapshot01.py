from pathlib import Path
import json,hashlib,copy,collections,re
O=Path(__file__).resolve().parent;B=O.parent;P=B/'纯来源候选投影01'
A=B.parents[1]/'自动规则编码/共同定义候选/candidate11/full-shadow01'
F={'raw':B/'共同材料修订01/effective_blind_inputs_material_revision01.jsonl','old_view':P/'source_only_candidates01.jsonl','old_sidecar':P/'provenance_sidecars01.jsonl','issues':P/'issues01.jsonl','supplements':A/'material_supplement_all11.jsonl','memberships':A/'shared_component_scope_membership11.jsonl'}
def sh(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def hs(x):return hashlib.sha256(x.encode()).hexdigest()
def read(p):return [json.loads(x) for x in p.open()]
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def jsonl(p,rr):
    with p.open('w') as f:
        for r in rr:f.write(json.dumps(r,ensure_ascii=False)+'\n')
def get(o,p):
    for a in p.lstrip('/').split('/'):
        a=a.replace('~1','/').replace('~0','~');o=o[int(a)] if isinstance(o,list) else o[a]
    return o
def opaque(prefix,*values):return prefix+hs(json.dumps(values,ensure_ascii=False,sort_keys=True))[:20]
def keep(o,keys):return {k:copy.deepcopy(o[k]) for k in keys if k in o and o[k] is not None}
def pair(o):
    assert isinstance(o,dict) and isinstance(o.get('path'),str) and re.fullmatch('[0-9a-f]{64}',o.get('sha256',''))
    return {'path':o['path'],'sha256':o['sha256']}
def occ(row):
    out=[(None,'text',row['text'])]
    for z in row['contexts']:
        for k in ['text','title','caption']:
            if k in z:out.append((z['context_id'],k,z[k]))
        for k in ['headers','row_cells']:
            for j,t in enumerate(z.get(k,[])):out.append((z['context_id'],f'{k}/{j}',t))
    return out
def literal_coverage(row,text):
    found=[]
    for cid,field,t in occ(row):
        start=t.find(text)
        while start>=0:
            found.append({'context_id':cid,'output_field':field,'start':start,'end':start+len(text),'coverage':'exact' if t==text else 'subspan'})
            start=t.find(text,start+1)
    return found

before={k:sh(p) for k,p in F.items()};D={k:read(p) for k,p in F.items()}
R,V,S=D['raw'],D['old_view'],D['old_sidecar'];assert len(R)==len(V)==len(S)==4924
assert [x['id'] for x in R]==[x['id'] for x in V]==[x['id'] for x in S]
ix={x['id']:i for i,x in enumerate(R)};Q=collections.defaultdict(list)
for x in D['issues']:
    if x['code']!='unbound_policy_leaf':Q[x['id']].append(x)
BASE=[];SIDE=[];counts=collections.Counter();base_QA=[];old_total=0
for i,(raw,old,oldside) in enumerate(zip(R,V,S)):
    row=copy.deepcopy(old)
    sid={'id':raw['id'],'current_source':keep(oldside['current_source_priority'],['source_path','source_sha256','source_pair_fields','candidate_path','candidate_sha256','source_image','source_image_sha256']),'generic_source':copy.deepcopy(oldside['generic_source_identity']),'unit_source':copy.deepcopy(oldside['unit_source_identity']),'policy_leaves':[],'source_identity_links':[],'neutral_relations':[],'omitted_optional_pointers':[],'nonpolicy_boundary_pointers':[],'pending_root_freeze':True}
    issues=Q[raw['id']];links={};leafmap={z['raw_pointer']:z for z in oldside['policy_leaves']}
    for a in issues:
        if a['code']!='incomplete_or_invalid_explicit_source_pair':continue
        p=a['raw_pointer'];v=get(raw,p);sha=v['source_sha256'];pairs=set();roots=[]
        for z in oldside['policy_leaves']:
            b=z['source_binding']
            if b.get('source_sha256')==sha and b.get('source_path'):pairs.add((b['source_path'],sha))
        for n,k in [('current_source_priority','source_path'),('generic_source_identity','source'),('unit_source_identity','unit_source')]:
            b=oldside.get(n,{}) or {};h=b.get('source_sha256',b.get('unit_source_sha256'))
            if h==sha and b.get(k):pairs.add((b[k],sha));roots.append(n)
        assert len(pairs)==1
        path,sha=next(iter(pairs));ref=opaque('SL-',raw['id'],p)
        e={'relation_id':ref,'raw_container_pointer':p,'original_container_source_sha256':v['source_sha256'],'source_path':path,'source_sha256':sha,'existing_complete_root_identities':roots,'association_method':'same_record_existing_complete_pair_same_SHA'}
        links[p]=e;sid['source_identity_links'].append(e);counts['source_identity_links']+=1
        if roots==['generic_source_identity']:counts['generic_only_links']+=1
    for z in oldside['policy_leaves']:
        p=z['raw_pointer'];tx=get(raw,p);assert isinstance(tx,str) and hs(tx)==z['text_sha256']
        b=keep(z['source_binding'],['source_path','source_sha256','source_pair_fields','candidate_path','candidate_sha256','source_image','source_image_sha256','table_source_structured_sha256'])
        if z['source_binding'].get('identity_issues'):
            candidates=[(len(k),k,e) for k,e in links.items() if p==k or p.startswith(k+'/')];assert candidates
            _,k,e=max(candidates);b.update(source_path=e['source_path'],source_sha256=e['source_sha256'],source_identity_link_ref=e['relation_id']);counts['legacy_identity_leaf_kept_and_linked']+=1
        assert b.get('source_path') and b.get('source_sha256')
        sid['policy_leaves'].append({'raw_pointer':p,'context_id':z['context_id'],'output_field':z['output_field'],'text_sha256':z['text_sha256'],'character_n':z['character_n'],'source_binding':b})
    def refs_under(prefix):
        return list(dict.fromkeys(z['context_id'] for p,z in leafmap.items() if (p==prefix or p.startswith(prefix+'/')) and z['context_id'] is not None))
    def relation(kind,p,refs,**fields):
        rid=opaque('NR-',raw['id'],p);sid['neutral_relations'].append({'relation_id':rid,'kind':kind,'raw_pointer':p,'related_context_ids':refs,**fields})
        st={'relation_id':rid,'related_context_ids':refs}
        for k in ['unit_id','related_unit_ids','paragraph_ids']:
            if k in fields:st[k]=fields[k]
        if kind=='image_source_metadata':st['image_evidence_ref']=rid
        row['contexts'].append({'context_id':opaque('CTX-N2-',raw['id'],p),'kind':'structural_relation','structure':st})
    for a in issues:
        p=a['raw_pointer'];c=a['code']
        if c=='empty_or_invalid_declared_policy_leaf':
            assert get(raw,p) in (None,'');sid['omitted_optional_pointers'].append(p);counts['empty_optional_or_table_paragraph_omitted']+=1
        elif c=='invalid_declared_locator_shape':
            assert get(raw,p) is None;sid['omitted_optional_pointers'].append(p);counts['empty_optional_or_table_paragraph_omitted']+=1
        elif c=='unmapped_nested_context_container':
            val=get(raw,p);parent=p.rsplit('/',1)[0]
            if p.endswith('/unresolved_material_gaps'):
                assert val==[];sid['omitted_optional_pointers'].append(p);counts['empty_optional_or_table_paragraph_omitted']+=1
            elif p.endswith('/component_binding'):
                assert set(val)=={'unit_id','candidate_sha256'}
                relation('component_identity',p,refs_under(parent),unit_id=val['unit_id'],candidate_sha256=val['candidate_sha256']);counts['component_relations']+=1
            elif p.endswith('/source_bullets_without_analysis_units'):
                refs=[z['context_id'] for z in old['contexts'] if z.get('structure',{}).get('paragraph_id') in val and z.get('text')];assert refs
                relation('paragraph_member_identity',p,refs,paragraph_ids=val);counts['member_relations']+=1
            elif p.endswith('/separately_existing_unit_ids'):
                z=leafmap[parent+'/text'];relation('related_unit_identity',p,[z['context_id']],related_unit_ids=val);counts['member_relations']+=1
            else:
                assert p.endswith(('/source_page_images','/source_visual_evidence_v14','/source_image_evidence'))
                vv=val if isinstance(val,list) else [val];imgs=[keep(x,['path','sha256','page','actual_pdf_page','printed_page']) for x in vv]
                assert all(x.get('path') and x.get('sha256') for x in imgs)
                relation('image_source_metadata',p,refs_under(parent),image_sources=imgs);counts['image_relations']+=1
        elif c=='ambiguous_boundary_requires_literal_binding':
            val=get(raw,p)
            if p.endswith('verified_scope_context_v8/next_structure'):
                assert val=='二、工作流程';v=get(raw,p.rsplit('/',1)[0]);scope=[z for pp,z in leafmap.items() if pp.startswith('/contexts/verified_scope_context_v8/')];assert len(scope)==10
                cid=opaque('CTX-H2-',raw['id'],p)
                st={'position':'following_scope_component','scope_context_ids':[z['context_id'] for z in scope],'follows_context_id':scope[-1]['context_id'],'component_first_paragraph':v['first_paragraph'],'component_last_paragraph':v['last_paragraph']}
                row['contexts'].append({'context_id':cid,'kind':'following_heading','source_document':opaque('D2-',v['source_path'],v['source_sha256']),'text':val,'structure':st})
                sid['policy_leaves'].append({'raw_pointer':p,'context_id':cid,'output_field':'text','text_sha256':hs(val),'character_n':len(val),'source_binding':keep(v,['source_path','source_sha256','candidate_path','candidate_sha256']),'component_raw_pointer':p.rsplit('/',1)[0]});counts['following_headings_added']+=1
            elif val in ['end_of_original_word_attachment','Article 68 only, ending before Article 69']:
                sid['nonpolicy_boundary_pointers'].append({'raw_pointer':p,'kind':'declared_component_end' if val=='end_of_original_word_attachment' else 'declared_source_list_range','related_context_ids':refs_under(p.rsplit('/',1)[0])});counts['nonpolicy_boundaries_omitted_from_source_text']+=1
            else:raise AssertionError(('unknown boundary',p))
        elif c=='missing_table_row_index':
            obj=get(raw,p.rsplit('/',1)[0]);tr=[z for z in old['contexts'] if z['kind']=='table_row'];assert len(tr)==1
            tr=tr[0];assert obj['caption']==tr['caption'] and obj['headers']==tr['headers'] and obj['row_cells']==tr['row_cells'] and len(tr['headers'])==5 and ' | '.join(tr['row_cells'])==row['text']
            sid.setdefault('table_row_material',[]).append({'context_id':tr['context_id'],'raw_pointer':p.rsplit('/',1)[0],'paragraph_id':obj['paragraph_id'],'pages':obj['pages'],'physical_row_index_provided':False});counts['table_row_material_kept']+=1
    oldocc=occ(old);newocc=occ(row)
    assert row['id']==old['id'] and row['text']==old['text'] and row['pages']==old['pages'] and row['contexts'][:len(old['contexts'])]==old['contexts']
    assert newocc[:len(oldocc)]==oldocc and all(t=='二、工作流程' and k=='text' for cid,k,t in newocc[len(oldocc):])
    base_QA.append({'id':row['id'],'old_context_nodes_exact_and_ordered':True,'old_policy_occurrence_n':len(oldocc),'new_following_heading_n':len(newocc)-len(oldocc),'current_text_exact':True});old_total+=len(oldocc);BASE.append(row);SIDE.append(sid)
expected={'source_identity_links':1079,'generic_only_links':27,'legacy_identity_leaf_kept_and_linked':1180,'empty_optional_or_table_paragraph_omitted':928,'component_relations':59,'member_relations':28,'image_relations':47,'following_headings_added':51,'nonpolicy_boundaries_omitted_from_source_text':15,'table_row_material_kept':4}
assert counts==collections.Counter(expected),counts
jsonl(O/'source_only_base02.jsonl',BASE);jsonl(O/'provenance_base02.jsonl',SIDE);jsonl(O/'mechanical_base_QA02.jsonl',base_QA)
MERGED=copy.deepcopy(BASE);MSIDE=copy.deepcopy(SIDE);member_checks=[];new_fragment_checks=[];coverage_checks=[]
complete_roles={'published_title_and_notice','same_title_attachment_link','self_declared_scope','body_opening','body_last_paragraph','actual_reference_component_boundary'}
for sid in MSIDE:sid['added_component_fragments']=[];sid['package_fragment_coverage']=[]
def clean_fragment(f,package,pointer):
    assert isinstance(f['text'],str) and hs(f['text'])==f['text_sha256']
    return {'input_package':str(F[package]),'input_package_sha256':before[package],'fragment_raw_pointer':pointer,'role':f['role'],'text_sha256':f['text_sha256'],'source':pair(f['source']),'candidate':pair(f['candidate']),'candidate_locator':keep(f,['physical_pages','candidate_paragraph_id','candidate_paragraph_start','candidate_paragraph_end']),'actual_source_locations':[keep(x,['candidate_line_id','physical_page','raw_extracted_text_start','raw_extracted_text_end','raw_extracted_exact_span','extracted_text_sha256']) for x in f.get('actual_source_locations',[])],'existing_raw_matches':[keep(x,['raw_pointer','start','end']) for x in f.get('raw_matches',[])]}
for j,pkg in enumerate(D['memberships']):
    assert len(pkg['all_current_input_members'])==pkg['current_input_member_count']
    sourcefrags=[('scope_source_fragments',k,f) for k,f in enumerate(pkg['scope_source_fragments']) if f['role'] in complete_roles]+[('structural_boundary_fragments',k,f) for k,f in enumerate(pkg['structural_boundary_fragments'])]
    assert len(sourcefrags)==6 and {f['role'] for g,k,f in sourcefrags}==complete_roles
    omitted_anchors=[f for f in pkg['scope_source_fragments'] if f['role'] not in complete_roles]
    assert len(omitted_anchors)==2 and all(f['role']=='actual_title_or_scope_anchor' and any(f['text'] in z['text'] for g,k,z in sourcefrags) for f in omitted_anchors)
    for member in pkg['all_current_input_members']:
        i=ix[member['record_id']];assert member['current_unit_text_sha256']==hs(R[i]['text']) and member['input_line_1based']==i+1
        assoc=keep(member,['record_id','original_id','source_unit_id','candidate_paragraph_id','physical_pages','current_unit_text_sha256','input_line_1based','raw_pointer'])
        for sequence,(group,k,f) in enumerate(sourcefrags):
            pointer=f'/{j}/{group}/{k}';cid=opaque('CTX-F2-',R[i]['id'],pointer,pkg['component_id'])
            st={'source_role':f['role'],'sequence_index':sequence,'component_id':pkg['component_id'],**keep(f,['physical_pages','candidate_paragraph_id','candidate_paragraph_start','candidate_paragraph_end'])}
            source=pair(f['source']);MERGED[i]['contexts'].append({'context_id':cid,'kind':'source_fragment','source_document':opaque('D2-',source['path'],source['sha256']),'text':f['text'],'structure':st})
            e=clean_fragment(f,'memberships',pointer);e.update(context_id=cid,component_id=pkg['component_id'],current_association=assoc)
            MSIDE[i]['added_component_fragments'].append(e);new_fragment_checks.append({'record_id':R[i]['id'],'context_id':cid,'package_raw_pointer':pointer,'text_sha256':f['text_sha256'],'source_candidate_pair_exact':True,'role':f['role']})
        member_checks.append({'record_id':R[i]['id'],'component_id':pkg['component_id'],'current_text_sha256_exact':True,'complete_component_fragments_added':6})
# Every supplied fragment must be covered without appending machine-selected anchors.
covcounts=collections.Counter()
for j,pkg in enumerate(D['supplements']):
    assoc=pkg['association'];i=ix[assoc['record_id']];assert pkg['current_unit_text']==R[i]['text'] and assoc['current_unit_text_sha256']==hs(R[i]['text'])
    for k,f in enumerate(pkg['fragments']):
        e=clean_fragment(f,'supplements',f'/{j}/fragments/{k}');cov=literal_coverage(MERGED[i],f['text'])
        if cov:kind='exact_or_subspan_existing_complete_source_context'
        else:
            # The actual legacy table-certificate rendering is reversible caption+headers display,
            # not an omitted original policy sentence. Preserve native table fields separately.
            tables=[z for z in MERGED[i]['contexts'] if z['kind']=='table_row' and f['text']==z.get('caption','')+'；列名：'+' | '.join(z.get('headers',[]))]
            if tables:
                cov=[{'context_id':z['context_id'],'coverage':'caption_and_ordered_headers','output_fields':['caption','headers']} for z in tables];kind='existing_table_caption_and_headers_structure'
            else:
                # Two actually observed complete Article 8 representations only; not general normalization.
                # Compare full article, permit precisely source U+3000 space and four width punctuation variants.
                trans=str.maketrans({'\u3000':' ','，':',','（':'(', '）':')','：':':'})
                if f['text'].startswith('第八条\u3000') and len(f['text'])==82:
                    same=[(cid,field,t) for cid,field,t in occ(MERGED[i]) if t.startswith('第八条 ') and f['text'].translate(trans)==t]
                else:same=[]
                assert same,('uncovered_source_fragment',assoc['record_id'],j,k,f['role'])
                cov=[{'context_id':cid,'output_field':field,'coverage':'same_complete_article_source_glyph_representation','existing_text_sha256':hs(t),'explicit_source_to_existing_codepoints':{'U+3000':'U+0020','U+FF0C':'U+002C','U+FF08':'U+0028','U+FF09':'U+0029'}} for cid,field,t in same];kind='same_complete_article_source_representation'
        e.update(current_association=copy.deepcopy(assoc),covered_occurrences=cov,coverage_kind=kind);MSIDE[i]['package_fragment_coverage'].append(e)
        coverage_checks.append({'record_id':R[i]['id'],'package_raw_pointer':f'/{j}/fragments/{k}','coverage_kind':kind,'covered_occurrence_n':len(cov),'source_text_sha256':f['text_sha256']});covcounts[kind]+=1
jsonl(O/'source_only_with_scope02.jsonl',MERGED);jsonl(O/'provenance_with_scope02.jsonl',MSIDE);jsonl(O/'component_member_merge_QA02.jsonl',member_checks);jsonl(O/'new_component_fragment_QA02.jsonl',new_fragment_checks);jsonl(O/'existing_fragment_coverage_QA02.jsonl',coverage_checks)
# One actual full disk QA. Sidecar retains original raw pointers, but no old opinion/assertion fields.
rb=read(O/'source_only_base02.jsonl');rm=read(O/'source_only_with_scope02.jsonl');rs=read(O/'provenance_with_scope02.jsonl')
badkeys={'usage','normalization','verification','verified','runtime_source_authentication','label','labels','reason','rationale','confidence','source_title','statement','availability','runtime_used_additional_source_text','output_labels_used_to_select_members','annotations_or_AI_opinions_included','shared_with_other_methods_yet','binding_status','authentication_claim','match_method','literal_match'}
policykeys={'text','title','caption','headers','row_cells'};filename=re.compile(r'/Users/|/var/|\.(?:pdf|docx?|txt|html|png|jsonl?)\b',re.I);violations=[]
def scan(o,path='',model=False,policy=False):
    if isinstance(o,dict):
        for k,v in o.items():
            if k in badkeys:violations.append((path+'/'+k,'forbidden_key'))
            scan(v,path+'/'+k,model,k in policykeys)
    elif isinstance(o,list):
        for j,v in enumerate(o):scan(v,path+'/'+str(j),model,policy)
    elif isinstance(o,str) and model and not policy and filename.search(o):violations.append((path,'filename_or_absolute_path_in_model_metadata'))
for i,(a,b,sid) in enumerate(zip(rb,rm,rs)):
    assert a==BASE[i] and b==MERGED[i] and sid==MSIDE[i] and b['id']==V[i]['id'] and b['text']==V[i]['text']
    assert b['contexts'][:len(a['contexts'])]==a['contexts'];scan(b,f'/{i}',True);scan(sid,f'/{i}',False)
    new=b['contexts'][len(a['contexts']):];assert len(new)==len(sid['added_component_fragments'])
    for z,e in zip(new,sid['added_component_fragments']):assert z['context_id']==e['context_id'] and hs(z['text'])==e['text_sha256']
assert not violations,violations[:10]
after={k:sh(p) for k,p in F.items()};assert before==after
summary={'record_n':4924,'status':'assembled_pending_root_independent_QA_and_freeze','old_policy_occurrence_n':old_total,'base_following_heading_occurrences_added':51,'base_old_context_nodes_and_all_text_occurrences_exact_and_ordered':True,'base_metadata_counts':dict(counts),'supplement_association_n':len(D['supplements']),'selected_source_fragments_covered_without_anchor_addition':len(coverage_checks),'selected_fragment_coverage_kind_counts':dict(covcounts),'scope_component_n':len(D['memberships']),'scope_component_current_member_n':len(member_checks),'complete_uniform_component_fragments_added':len(new_fragment_checks),'local_title_scope_anchors_not_separately_added':4,'member_selection':'all supplied actual candidate component members; no rule output or dimension selection','source_fragment_text_SHA_source_candidate_role_associations_exact':True,'leakage_field_or_filename_violations':violations,'input_SHA_before':before,'input_SHA_after':after,'model_rule_coder_binder_calls':0,'formal_model_input_ready':False,'pending':'Root independent mechanical QA/freeze; assembly is not source authentication or coding validity'}
write(O/'mechanical_summary02.json',summary);print(json.dumps(summary,ensure_ascii=False,indent=2))
