"""Zero-model mechanical risk-scope estimate. Never emits original text/labels.

Trigger specification is frozen before counts. Predictions describe aggregate
strata only and never influence a trigger. No reference/expectation file read.
"""
import collections
import hashlib
import importlib.util
import itertools
import json
import re
from pathlib import Path

OUT=Path(__file__).resolve().parent
C09=OUT.parents[1]
PROJECT=C09.parents[3]
SPEC=OUT/'scope_spec_PREDECLARED.json'
spec=json.loads(SPEC.read_text())
lock=json.loads((OUT/'scope_spec_lock.json').read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def object_sha(x):return hashlib.sha256(canonical(x).encode()).hexdigest()
def binding(p):
    p=Path(p).resolve();return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
def write_new(p,x):
    with Path(p).open('x')as f:f.write(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
assert sha(SPEC)==lock['scope_spec']['sha256']=='ed421419dc712b26d8af45714f6d60e736bdd79b3894a4bf7f84a06ca3847db7'
for name in ['input','retained_original_LLM03']:assert sha(spec[name]['path'])==spec[name]['sha256']
inventory_path=C09/'runtime/stageA_context_inventory.py'
ispec=importlib.util.spec_from_file_location('c09_partial_inventory',inventory_path)
inventory=importlib.util.module_from_spec(ispec);ispec.loader.exec_module(inventory)
patterns={k:re.compile(v)for k,v in spec['patterns'].items()}

def hit(category,text,path):
    m=patterns[category].search(text)
    if not m:return None
    return {'pattern':category,'path':path,'start':m.start(),'end':m.end(),
      'matched_UTF8_sha256':hashlib.sha256(m.group().encode()).hexdigest()}
def following_paths(value,path=''):
    found=[]
    if isinstance(value,dict):
        for k,v in value.items():
            p=path+'/'+str(k).replace('~','~0').replace('/','~1')
            if k=='structured_following_units'and isinstance(v,(list,dict))and v:found.append(p)
            found.extend(following_paths(v,p))
    elif isinstance(value,list):
        for i,v in enumerate(value):found.extend(following_paths(v,path+'/'+str(i)))
    return found
def triggers(row):
    text=row['text'];leaves=inventory.inventory(row)
    def unit(cat):return hit(cat,text,'/text')
    def context(cat):
        for leaf in leaves:
            m=hit(cat,leaf['text'],leaf['path'])
            if m:return m
        return None
    result={}
    a,b=unit('attribute'),unit('change')
    if a and b:result['T1_CURRENT_ATTRIBUTE_CHANGE']=[a,b]
    a,b=unit('safety'),unit('duty_or_action')
    if a and b:result['T2_CURRENT_SAFETY_DUTY_OR_ACTION']=[a,b]
    a,b=unit('support_or_administration'),unit('research')or context('research')
    if a and b:result['T3_CURRENT_SUPPORT_OR_ADMIN_IN_RESEARCH_CONTEXT']=[a,b]
    a=unit('coverage_or_access')
    if a:result['T4_COVERAGE_ACCESS_OR_LINKED_CONDITION']=[a]
    else:
        a,b=unit('condition_or_procedure'),context('coverage_or_access')
        if a and b:result['T4_COVERAGE_ACCESS_OR_LINKED_CONDITION']=[a,b]
    paths=following_paths(row)
    if paths:result['T5_NONEMPTY_STRUCTURED_FOLLOWING']=[{'path':p,'nonempty_container':True}for p in paths]
    return result

def main():
    # Only the material/department provenance portion is used. No reference
    # labels, submissions, score tables or private expectations are opened.
    manifest_path=PROJECT/'outputs/coding-revision-20261007-r3/statistics/final_bindings_v14_CONFIRMED_r3.json'
    assert sha(manifest_path)=='46582af989d0473655b71ba38f174c2043794b8da9833bca9940aa0cf62c71cd'
    mf=json.loads(manifest_path.read_text())
    for b in [mf['material']['rule_inputs'],mf['metadata']]:assert sha(b['path'])==b['sha256']
    rule_rows=[json.loads(s)for s in Path(mf['material']['rule_inputs']['path']).read_text().splitlines()if s.strip()]
    meta=json.loads(Path(mf['metadata']['path']).read_text())
    file_groups={Path(x['original_file']).stem:x['analysis_group']for x in meta['rows']}
    material={x['id']:x['input']for x in rule_rows}
    ip=Path(spec['input']['path']);lp=Path(spec['retained_original_LLM03']['path'])
    rows=[json.loads(s)for s in ip.read_text().splitlines()if s.strip()]
    preds=[json.loads(s)for s in lp.read_text().splitlines()if s.strip()]
    pred_map={x['id']:(i+1,x)for i,x in enumerate(preds)}
    assert len(rows)==len(preds)==len(pred_map)==4924 and set(pred_map)=={x['id']for x in rows}==set(material)
    ex=PROJECT/'outputs/coding-revision-20261008-r4/validation-state-audit/future_human_v5_development_exclusion_metadata.json'
    assert sha(ex)=='a3ea2e0aaabbf9d00fafb4f3511b3a8910b182111d1cff803c0bb5f03040d135'
    protected=set(json.loads(ex.read_text())['all_registered_members_of_reserved_families_unit_ids'])
    assert len(protected)==267
    ib=json.loads((C09/'initial11_input_binding.json').read_text())
    assert sha(ib['input_path'])==ib['input_sha256']
    initial=[json.loads(s)for s in Path(ib['input_path']).read_text().splitlines()if s.strip()]
    real9=[x for x in initial if x['id'].startswith('RECODE25-')]
    assert len(initial)==11 and len(real9)==9
    sources=[binding(SPEC),binding(OUT/'scope_spec_lock.json'),binding(inventory_path),binding(ip),binding(lp),binding(manifest_path),binding(mf['material']['rule_inputs']['path']),binding(mf['metadata']['path']),binding(ex),binding(C09/'initial11_input_binding.json'),binding(ib['input_path'])]
    start={x['path']:x['sha256']for x in sources}
    tc=collections.Counter();unique=collections.Counter();overlap=collections.Counter();groups={};strata={}
    ids={};perrow=[];label_summaries={k:collections.Counter()for k in ['all4924','selected','outside']}
    masks={};reserved_counts=collections.Counter();root_keys=collections.Counter();context_keys=collections.Counter()
    for i,row in enumerate(rows,1):
        rid=row['id'];old_line,pred=pred_map[rid];origin=material[rid]
        assert row['text']==origin['unit_text']and row['contexts']==origin['llm_v29_shared_context']
        group=file_groups[origin['original_file_stem']]
        g=groups.setdefault(group,{'all_n':0,'selected_n':0,'outside_n':0,'triggers':collections.Counter(),'nonprotected_outside_n':0})
        found=triggers(row);selected=bool(found);ids[rid]=found;masks[rid]=selected
        tc.update(found.keys());overlap.update(['+'.join(found)if found else'NONE'])
        if len(found)==1:unique.update(found.keys())
        g['all_n']+=1;g['selected_n']+=selected;g['outside_n']+=not selected;g['triggers'].update(found.keys())
        g['nonprotected_outside_n']+=not selected and rid not in protected
        old=pred['labels'];assert set(old)=={'S','E','Ec','I','F'}and all(type(v)is int and v in [0,1]for v in old.values())
        label_pattern=''.join(str(old[d])for d in ['S','E','Ec','I','F'])
        stratum=('I'+str(old['I'])+'F'+str(old['F']))if old['I']or old['F']else('I0F0_allfive0'if label_pattern=='00000'else'I0F0_other_dimensions_positive')
        for key in ['all4924','selected'if selected else'outside']:
            label_summaries[key].update({'n':1,'pattern_'+label_pattern:1,**{d+'_positive':old[d]for d in old}})
        sc=strata.setdefault(group+'|'+stratum,{'all_n':0,'selected_n':0,'outside_n':0,'nonprotected_outside_n':0,'outside_source_file_hashes':set()})
        sc['all_n']+=1;sc['selected_n']+=selected;sc['outside_n']+=not selected;sc['nonprotected_outside_n']+=not selected and rid not in protected
        file_hash=hashlib.sha256(origin['original_file_stem'].encode()).hexdigest()
        if not selected:sc['outside_source_file_hashes'].add(file_hash)
        reserved_counts['all_reserved_n']+=rid in protected;reserved_counts['selected_reserved_n']+=selected and rid in protected;reserved_counts['outside_reserved_n']+=not selected and rid in protected
        root_keys.update(row.keys());context_keys.update(row.get('contexts',{}).keys())
        perrow.append({'id':rid,'original_input_line_1based':i,'source_group':group,'source_file_stem_UTF8_sha256':file_hash,
          'original_input_row_canonical_sha256':object_sha(row),'original_input_source_sha256':spec['input']['sha256'],
          'original_LLM03_line_1based':old_line,'original_LLM03_row_canonical_sha256':object_sha(pred),
          'original_LLM03_source_sha256':spec['retained_original_LLM03']['sha256'],'reserved_family_member':rid in protected,
          'selected_for_proposed_review':selected,'trigger_ids':list(found),'mechanical_trigger_evidence_METADATA_ONLY':found})
    for st in strata.values():st['outside_source_file_n']=len(st.pop('outside_source_file_hashes'))
    for g in groups.values():g['triggers']=dict(g['triggers'])
    coverage=[]
    original_byid={x['id']:x for x in rows}
    for row in real9:
        assert canonical(row)==canonical(original_byid[row['id']]),'pilot real input does not equal original full input'
        coverage.append({'id':row['id'],'selected':masks[row['id']],'trigger_ids':list(ids[row['id']]),'original_full_input_exact':True,'private_expectations_or_B_result_used':False})
    selected_n=sum(masks.values());outside_n=4924-selected_n
    for d in label_summaries.values():
        n=d['n'];d['I_positive_fraction']=d['I_positive']/n if n else None;d['F_positive_fraction']=d['F_positive']/n if n else None
    pair_overlaps={a+' & '+b:sum(a in x and b in x for x in ids.values())for a,b in itertools.combinations([t['id']for t in spec['triggers']],2)}
    assert all(sha(p)==h for p,h in start.items()),'source changed during mechanical scope estimate'
    pp=OUT/'all4924_scope_provenance_METADATA_ONLY_PRIVATE.jsonl'
    with pp.open('x')as f:
        for x in perrow:f.write(json.dumps(x,ensure_ascii=False)+'\n')
    report={'status':'COMPLETED_MECHANICAL_FEASIBILITY_ESTIMATE_NOT_EXECUTION_OR_ADOPTION','scope_spec_sha256':sha(SPEC),
      'script':binding(Path(__file__)),'sources':sources,'original_n':4924,'trigger_counts':dict(tc),
      'exclusive_one_trigger_counts':dict(unique),'pair_overlap_counts':pair_overlaps,'exact_trigger_combination_counts':dict(overlap),
      'union_selected_n':selected_n,'union_selected_fraction':selected_n/4924,'outside_n':outside_n,'groups':groups,
      'three_department4481':{'all_n':sum(g['all_n']for k,g in groups.items()if k!='GOV'),'selected_n':sum(g['selected_n']for k,g in groups.items()if k!='GOV')},
      'reserved_current_unit_metadata_counts_only':dict(reserved_counts),'original_LLM03_aggregate_label_strata_only':{k:dict(v)for k,v in label_summaries.items()},
      'outside_strata_for_future_independent_audit':strata,'current9_real_control_coverage':coverage,
      'current9_covered_n':sum(x['selected']for x in coverage),'field_counts_only':{'root':dict(root_keys),'contexts_top_level':dict(context_keys)},
      'all4924_row_provenance':binding(pp),'predicted_labels_used_by_triggers':False,'AB_or_other_references_read':False,
      'private_expectations_or_B_actual_output_read':False,'original_text_semantically_read_or_displayed':False,
      'protected_text_or_predictions_individually_displayed':False,'source_files_modified':False,
      'new_model_calls':0,'new_CLI_invocations':0,
      'limitations':['Keyword co-occurrence is a risk detector, not a semantic classifier or proven error-recall bound.',
        'Coverage of nine previously exposed development controls is not external validation or proof of B repair.',
        'Legacy quotable-leaf inventory ignores bare strings inside lists; original contexts are never removed.',
        '4924 includes GOV443; it differs from the three-department4481 analysis frame and the1767 probability sampling frame.',
        'Future partial review would create an explicitly selective-review version, not a single complete09 run.']}
    write_new(OUT/'partial_scope_feasibility_METADATA_ONLY.json',report)
    print(json.dumps({'status':report['status'],'trigger_counts':dict(tc),'selected_union_n':selected_n,'outside_n':outside_n,
      'current9_covered_n':report['current9_covered_n'],'groups':groups,'protected_metadata_counts_only':dict(reserved_counts),
      'report':binding(OUT/'partial_scope_feasibility_METADATA_ONLY.json'),'provenance':binding(pp),'new_model_calls':0,'new_CLI_invocations':0},ensure_ascii=False))

if __name__=='__main__':main()
