"""Read-only request-order checks and full-input KEY metadata counts; no model call.

Full policy strings are consumed mechanically and are never emitted. Only the
already exposed synthetic 015/016 key order is inspected. No labels/references
are loaded from full input. The source and frozen runtime are not modified.
"""
import collections
import hashlib
import json
from pathlib import Path

PROJECT = Path('/Users/rainbow/Desktop/战略院/药企项目-创新药')
HERE = PROJECT/'outputs/编码修订核查-20261008/LLM编码/候选08-命题与证据判定'
OUT = HERE/'failure-mechanism-audit'
SOURCE = PROJECT/'outputs/coding-revision-20261007-r3/effective_blind_inputs_v14.jsonl'
RUN = HERE/'runtime-unchanged-v2/inherited62-candidate08-first-run'
PROMPT = HERE/'candidate08_prompt_PROPOSED.txt'
MARKER = '\n\n--- 本批冻结盲法输入 ---\n'
TRAILER = '\n\n只根据上述给定材料直接返回规定JSON。禁止外部检索、读取文件、调用任何工具、运行命令或代码。不从ID推断答案。'

def binding(p):
    b=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}

def keys_only(obj, path='$'):
    found=[]
    if isinstance(obj,dict):
        found.append({'path':path,'ordered_keys':list(obj)})
        for k,v in obj.items():found.extend(keys_only(v,path+'.'+k))
    elif isinstance(obj,list):
        for i,v in enumerate(obj):found.extend(keys_only(v,path+f'[{i}]'))
    return found

def main():
    assert binding(SOURCE)['sha256']=='6829d554cf5514e49565c7c58c4ffdb6f7768f9999b0eea49f114db023c03763'
    rows=[json.loads(line) for line in SOURCE.read_text().splitlines() if line.strip()]
    assert len(rows)==4924
    occurrences=collections.Counter(); row_count=collections.Counter()
    by_path=collections.Counter(); follow_occurrences=collections.Counter();follow_row_count=collections.Counter()
    shapes=collections.Counter();counts=collections.Counter();roles=collections.Counter()
    def visit(obj,path,occ,paths):
        if isinstance(obj,dict):
            for k,v in obj.items():
                occ[k]+=1;paths[path+'.'+k]+=1
                visit(v,path+'.'+k,occ,paths)
        elif isinstance(obj,list):
            for v in obj:visit(v,path+'[]',occ,paths)
    for row in rows:
        context=row.get('contexts',{})
        local=collections.Counter();paths=collections.Counter()
        visit(context,'contexts',local,paths)
        occurrences.update(local);row_count.update(local.keys());by_path.update(paths)
        if 'context_usage' in row:counts['top_level_context_usage_present']+=1
        follows=context.get('structured_following_units',[]) if isinstance(context,dict) else []
        if follows:
            counts['structured_following_nonempty_rows']+=1
            loc=collections.Counter();dummy=collections.Counter()
            visit(follows,'contexts.structured_following_units',loc,dummy)
            follow_occurrences.update(loc);follow_row_count.update(loc.keys())
            for item in follows:
                if isinstance(item,dict):shapes['|'.join(sorted(item))]+=1
            stat=context.get('following_list_material_status_v11',{})
            roles[stat.get('role','NO_TYPED_STATUS') if isinstance(stat,dict) else 'NO_TYPED_STATUS']+=1
            counts['nonempty_following_with_complete_v11_certificate']+=int('complete_following_list_v11' in context)
            counts['nonempty_following_with_legacy_verified_v27_certificate']+=int('verified_following_list_v27' in context)
            counts['nonempty_following_with_colon_ended_current_unit']+=int(row.get('text','').rstrip().endswith(('：',':')))
    prompt=PROMPT.read_text()
    traces=[]
    for uid,batch in [('C05-NEW-015',1),('C05-NEW-016',2)]:
        base=RUN/'batches'/f'batch-{batch:04d}'
        inp=json.loads((base/'input.json').read_text())
        row=next(x for x in inp['rows'] if x['id']==uid)
        request=(base/'attempts/attempt-01/request.txt').read_text()
        assert request==prompt+MARKER+json.dumps(inp,ensure_ascii=False)+TRAILER
        parsed=json.loads(request[len(prompt+MARKER):-len(TRAILER)])
        target=next(x for x in parsed['rows'] if x['id']==uid)
        assert keys_only(row)==keys_only(target)
        stderr=(base/'attempts/attempt-01/raw_stderr.txt').read_text()
        traces.append({
            'id':uid,'batch':batch,'request_binding':binding(base/'attempts/attempt-01/request.txt'),
            'ordered_row_and_nested_keys':keys_only(row),
            'request_parsed_order_equals_input_order':True,
            'actual_request_uses_sort_keys':False,
            'full_packet_default_dump_differs_from_sorted_key_dump':json.dumps(inp,ensure_ascii=False)!=json.dumps(inp,ensure_ascii=False,sort_keys=True),
            'stderr_binding':binding(base/'attempts/attempt-01/raw_stderr.txt'),
            'stderr_truncation_related_token_counts':{s:stderr.casefold().count(s) for s in ['truncat','context window','token limit','too long','overflow']},
            'stderr_values_not_displayed':True,
        })
    report={
        'status':'READ_ONLY_METADATA_AND_SERIALIZATION_CHECK_COMPLETE',
        'source_binding':binding(SOURCE),'runner_binding':binding(HERE/'runtime-unchanged-v2/run_production_v32.py'),
        'runner_line_evidence':{'input_parse_retains_JSON_object_order':[124,124],'batch_preserves_row_order':[129,129],
          'packet_insertion_rows_only':[149,149],'request_default_json_dumps_no_sort_keys':[150,150],
          'sort_keys_is_only_canonical_event_raw_comparison':[59,64]},
        'full4924_context_key_frequencies':{
            'n_rows':4924,'recursive_key_occurrences':dict(sorted(occurrences.items())),
            'rows_containing_each_recursive_key':dict(sorted(row_count.items())),
            'recursive_key_path_occurrences_arrays_collapsed':dict(sorted(by_path.items())),
            'structured_following_item_recursive_key_occurrences':dict(sorted(follow_occurrences.items())),
            'structured_following_rows_containing_each_recursive_item_key':dict(sorted(follow_row_count.items())),
            'following_item_key_shapes':dict(sorted(shapes.items())),
            'counts':dict(sorted(counts.items())),'following_material_role_counts':dict(sorted(roles.items())),
        },'synthetic_request_order_checks':traces,
        'limitations':['Counts are structural metadata, not semantic judgments of 4924 rows.',
          'No provider-side prompt echo or hidden context-window behavior is exposed by this check.',
          'Changing JSON insertion order changes the actual local request under this runner; JSON semantic object equality alone would not show that change.'],
        'real_model_calls':0,'protected_or_new_policy_strings_emitted':False,
    }
    path=OUT/'input_metadata_and_serialization_order.json'
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'report':binding(path),'counts':report['full4924_context_key_frequencies']['counts'],
      'following_material_role_counts':dict(roles),
      'request_order_checks':[{k:v for k,v in t.items() if k in ['id','ordered_row_and_nested_keys','request_parsed_order_equals_input_order','actual_request_uses_sort_keys','stderr_truncation_related_token_counts']} for t in traces]},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
