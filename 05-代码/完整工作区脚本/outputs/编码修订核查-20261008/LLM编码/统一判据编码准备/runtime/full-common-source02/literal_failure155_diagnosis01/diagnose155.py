from pathlib import Path
import collections, hashlib, json

OUT=Path(__file__).resolve().parent
BATCH=OUT.parent/'batches/batch-0155'
sha=lambda b:hashlib.sha256(b).hexdigest()
canon=lambda obj:json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
inp=json.loads((BATCH/'input.json').read_text())
rows=inp['rows'];by={r['id']:r for r in rows}
inputs_expected=[r['id'] for r in rows]
source_hashes={str(p):sha(p.read_bytes()) for p in BATCH.rglob('*') if p.is_file()}
facts=[]
for attempt in sorted((BATCH/'attempts').iterdir()):
    metadata=json.loads((attempt/'run_metadata.json').read_text())
    output_bytes=(attempt/'raw_output.json').read_bytes()
    output=json.loads(output_bytes)
    events=[json.loads(s) for s in (attempt/'events.jsonl').read_text().splitlines()]
    bindings=[];texts=[];event_errors=[];actual_tool_items=[]
    for line,event in enumerate(events,1):
        item=event.get('item',{})
        if event['type']=='item.completed' and item.get('type')=='agent_message':
            text=item['text'];texts.append(text)
            parsed=json.loads(text)
            bindings.append({'event_line_1based':line,'item_id':item['id'],'text_sha256':sha(text.encode()),
                'raw_output_bytes_equal':text.encode()==output_bytes,'canonical_object_equal':parsed==output,
                'row_n':len(parsed['rows']),'input_id_order_exact': [r['id'] for r in parsed['rows']]==inputs_expected})
        elif event['type']=='error' or item.get('type')=='error':
            event_errors.append({'event_line_1based':line,'event':event,
                'classification':'network_transport_error' if ('timed out' in event.get('message',item.get('message','')) or 'transport' in event.get('message',item.get('message',''))) else 'other_error'})
        elif item and item.get('type')!='agent_message':
            actual_tool_items.append({'event_line_1based':line,'event':event})
    nonliteral=[];evidence_n=0
    for index,r in enumerate(output['rows']):
        own=by[r['id']]
        own_contexts=[(n['context_id'],n.get('text','')) for n in own['contexts']]
        for evidence_index,evidence in enumerate(r['evidence']):
            evidence_n+=1;quote=evidence['quote']
            own_unit=quote in own['text']
            context_matches=[cid for cid,text in own_contexts if quote in text]
            literal=own_unit if evidence['source']=='unit' else bool(context_matches)
            if not literal:
                nonliteral.append({'record_id':r['id'],'json_pointer':f'/rows/{index}/evidence/{evidence_index}/quote',
                    'evidence':evidence,'literal_in_own_unit':own_unit,'literal_own_context_ids':context_matches,
                    'exact_quote_in_other_units_of_same_batch':[x['id'] for x in rows if x['id']!=r['id'] and quote in x['text']]})
    semantics=[{k:v for k,v in r.items() if k!='evidence'} for r in output['rows']]
    facts.append({'attempt':attempt.name,'metadata_status':metadata['status'],'exit_code':metadata['exit_code'],
        'thread_id':next(e['thread_id'] for e in events if e['type']=='thread.started'),
        'input_sha256':sha((attempt/'input.json').read_bytes()),
        'input_equal_batch_input':(attempt/'input.json').read_bytes()==(BATCH/'input.json').read_bytes(),
        'input_hash_matches_metadata':sha((attempt/'input.json').read_bytes())==metadata['input_sha256'],
        'raw_output_sha256':sha(output_bytes),'raw_output_hash_matches_metadata':sha(output_bytes)==metadata['raw_output_sha256'],
        'events_sha256':sha((attempt/'events.jsonl').read_bytes()),
        'events_hash_matches_metadata':sha((attempt/'events.jsonl').read_bytes())==metadata['events_sha256'],
        'metadata_sha256':sha((attempt/'run_metadata.json').read_bytes()),
        'completed_message_event_n':len(bindings),'distinct_completed_message_text_n':len(set(texts)),
        'distinct_completed_message_canonical_object_n':len({sha(canon(json.loads(t))) for t in texts}),
        'bindings':bindings,'network_or_error_events':event_errors,'actual_tool_or_unknown_items':actual_tool_items,
        'record_n':len(output['rows']),'output_id_order_exact':[r['id'] for r in output['rows']]==inputs_expected,
        'evidence_n':evidence_n,'nonliteral_quotes':nonliteral,
        'all_non_evidence_record_fields_sha256':sha(canon(semantics)),
        'original_record_03874':next(r for r in output['rows'] if r['id']=='RECODE25-03874'),
        'stored_validation_errors':json.loads((attempt/'validation.json').read_text())['errors']})

first=facts[0]
assert first['attempt']=='attempt-01' and first['record_n']==25 and first['output_id_order_exact']
assert first['distinct_completed_message_text_n']==1 and all(x['raw_output_bytes_equal'] for x in first['bindings'])
assert first['nonliteral_quotes']==[] and first['actual_tool_or_unknown_items']==[]
shared_source=by['RECODE25-03875']['text']
start=shared_source.index('续约分支三，重新谈判：')
shared_quote=shared_source[start:]
assert shared_source.count(shared_quote)==1 and '独家药品，需满足任一条件：' in shared_quote
parallel={'record_id':'RECODE25-03875','source':'unit','quote':shared_quote,
    'start_char_0based':start,'end_char_exclusive_0based':len(shared_source),'character_n':len(shared_quote),
    'whole_span_occurrence_n':shared_source.count(shared_quote),
    'common_modifier_quote':'独家药品，需满足任一条件：',
    'first_boundary':'续约分支三，重新谈判：','last_boundary':'不同意按照《续约规则》中的（二）调整支付标准。',
    'use_limit':'本段在03875的输入unit中；不在03874的unit或其context中。只能用于定位来源错配，不能移入03874作引文修复。'}
quote_ranges=[]
unit=by['RECODE25-03874']['text']
for evidence in first['original_record_03874']['evidence']:
    quote=evidence['quote'];pos=unit.index(quote)
    quote_ranges.append({'quote':quote,'source':'RECODE25-03874/text','start_char_0based':pos,
                         'end_char_exclusive_0based':pos+len(quote),'occurrence_n':unit.count(quote)})
result={'scope':'只读batch-0155实际输入、三次attempt原输出、run metadata和events；技术来源绑定与字面性诊断。',
    'semantic_correctness_adjudicated':False,'model_called':False,'original_files_modified':False,
    'attempt_facts':facts,
    'first_complete_actual_output':{'attempt':'attempt-01','event_lines_1based':[3,9],
       'different_completed_output_n':1,'raw_output_sha256':first['raw_output_sha256'],
       'explanation':'第3行item_0和第9行item_2均为同一完整25条JSON的字节相同重复发生。两条completed不是两个不同答案。第4–7行重连超时及第8行WebSockets转HTTPS fallback是网络传输事件，不是tool调用。原严格audit把error item计为potential_tool并按消息发生数2拒绝，尚未改动该原记录。',
       'source_binding_recovery_possible':True,
       'quote_changes_required_n':0,
       'preserve_all_25_labels_reasons_subtypes_and_other_non_evidence_fields':True,
       'explanation_of_preservation':'本诊断不写修复输出。attempt-01全部26条引用在指定的自己unit或自己contexts中均为连续字面子串；03874的两条Ec引文已有精确首尾范围，无需替换任何引文。若后续更正事件分类/重复发生绑定，只应绑定原始attempt-01字节，全部25条输出内容原样保留。',
       'formal_technical_pass_claimed':False},
    'record_03874_actual_input':by['RECODE25-03874'],
    'attempt01_record03874_literal_ranges':quote_ranges,
    'later_attempt_recovery_assessment':{'attempt02_nonliteral_n':len(facts[1]['nonliteral_quotes']),
       'attempt03_nonliteral_n':len(facts[2]['nonliteral_quotes']),
       'quote_only_recovery_while_preserving_reasons_possible':False,
       'reason':'后两次03874的禁忌/不良反应、1类药重新谈判引文，以及第三次3亿元降价引文，均在03874自身unit及唯一paragraph context中缺席，却逐字存在于同批03875。原理由明确声称这些要求属于03874流程图。任意改引03874已有流程或经济文字不能保持该理由的具体来源命题；移入03875文字也不是修复03874的自己来源。'},
    'complete_parallel_common_modifier_source':parallel,
    'selection_basis':'按attempt发生顺序和完整原输出/事件字节绑定定位最早完整结果，不按label取值或指标选择。',
    'files_before_after_unchanged':all(p.is_file() and sha(p.read_bytes())==digest for name,digest in source_hashes.items() for p in [Path(name)])}
assert result['files_before_after_unchanged']
(OUT/'literal_failure155_diagnosis01.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
lines=['batch-0155有限技术诊断','',result['scope'],'未调用模型；未修改原输入、输出、metadata、events或validation；不裁定语义有效。','',
    '最早完整实际输出：attempt-01。',result['first_complete_actual_output']['explanation'],
    '原输出SHA256：'+first['raw_output_sha256'],
    'events SHA256：'+first['events_sha256'],
    'metadata SHA256：'+first['metadata_sha256'],
    'thread_id：'+first['thread_id'],'',
    'attempt-01完整25条、26条证据均有自己来源的连续字面匹配。03874不存在非字面quote。',
    result['first_complete_actual_output']['explanation_of_preservation'],
    '原运行状态仍为failed_attempt_preserved；本报告不把字面和绑定诊断写成正式技术通过或语义正确。','',
    '后两次03874的来源错配：',result['later_attempt_recovery_assessment']['reason']]
for fact in facts[1:]:
    lines.append(fact['attempt'])
    for issue in fact['nonliteral_quotes']:
        lines.extend([issue['json_pointer'],issue['evidence']['quote'],'自己unit/contexts均无；同批精确来源：'+','.join(issue['exact_quote_in_other_units_of_same_batch'])])
lines.extend(['','真实并列共用修饰段：',parallel['quote'],
    f'来源03875/text，0-based范围 [{start}, {len(shared_source)})，共{len(shared_quote)}字符，仅1处完整发生。',
    '共用修饰：“独家药品，需满足任一条件：”；该段含三个并列条件。',parallel['use_limit'],'',
    'attempt-01的03874已有连续引文：'])
for span in quote_ranges:lines.extend([span['quote'],f'03874/text [{span["start_char_0based"]}, {span["end_char_exclusive_0based"]})'])
(OUT/'literal_failure155_diagnosis01.txt').write_text('\n'.join(lines)+'\n')
print(json.dumps({'directory':str(OUT),'first_complete_attempt':'attempt-01','different_message_n':1,
                  'first_attempt_nonliteral_n':0,'later_nonliteral_n':[len(f['nonliteral_quotes']) for f in facts[1:]],
                  'source_files_unchanged':result['files_before_after_unchanged']},ensure_ascii=False))
