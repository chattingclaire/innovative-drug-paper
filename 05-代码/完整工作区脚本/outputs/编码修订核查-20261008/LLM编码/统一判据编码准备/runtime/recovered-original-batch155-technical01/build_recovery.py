from pathlib import Path
import collections, hashlib, json, sys

sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent
RUNTIME=OUT.parent
RUN=RUNTIME/'full-common-source02'
BATCH=RUN/'batches/batch-0155'
ATTEMPT=BATCH/'attempts/attempt-01'
W=RUNTIME.parents[2]
sha=lambda b:hashlib.sha256(b).hexdigest()
canonical=lambda obj:json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
dump=lambda p,obj:p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
protected_files={p:sha(p.read_bytes()) for p in BATCH.rglob('*') if p.is_file()}
for p in [RUN/'frozen_schema.json',RUN/'frozen_validator.py',RUN/'frozen_runner.py']:
    protected_files[p]=sha(p.read_bytes())
raw_bytes=(ATTEMPT/'raw_output.json').read_bytes()
input_bytes=(ATTEMPT/'input.json').read_bytes()
event_bytes=(ATTEMPT/'events.jsonl').read_bytes()
metadata_bytes=(ATTEMPT/'run_metadata.json').read_bytes()
raw=json.loads(raw_bytes);packet=json.loads(input_bytes);metadata=json.loads(metadata_bytes)
assert input_bytes==(BATCH/'input.json').read_bytes()
assert sha(input_bytes)==metadata['input_sha256'] and sha(raw_bytes)==metadata['raw_output_sha256']
assert sha(event_bytes)==metadata['events_sha256']
schema_bytes=(RUN/'frozen_schema.json').read_bytes();schema=json.loads(schema_bytes)
# The bundled Python has no jsonschema package. This frozen schema uses only
# the bounded keywords below; unsupported assertions cause an error rather
# than being skipped. The frozen validator is executed separately unchanged.
SUPPORTED={'$schema','title','description','type','properties','required','additionalProperties','const','enum','items','minLength'}
def schema_check(value,contract,pointer=''):
    assert set(contract)<=SUPPORTED, sorted(set(contract)-SUPPORTED)
    errors=[];kind=contract.get('type')
    type_ok={'object':isinstance(value,dict),'array':isinstance(value,list),
             'string':isinstance(value,str),'integer':type(value) is int,
             'boolean':type(value) is bool}.get(kind,False)
    if not type_ok:return [{'path':pointer or '/', 'message':'type:'+str(kind)}]
    if 'const' in contract and (type(value)!=type(contract['const']) or value!=contract['const']):
        errors.append({'path':pointer or '/','message':'const'})
    if 'enum' in contract and not any(type(value)==type(item) and value==item for item in contract['enum']):
        errors.append({'path':pointer or '/','message':'enum'})
    if kind=='string' and len(value)<contract.get('minLength',0):errors.append({'path':pointer or '/','message':'minLength'})
    if kind=='object':
        for required in contract.get('required',[]):
            if required not in value:errors.append({'path':pointer or '/','message':'required:'+required})
        properties=contract.get('properties',{})
        if contract.get('additionalProperties') is False:
            for extra in set(value)-set(properties):errors.append({'path':pointer or '/','message':'additionalProperties:'+extra})
        for key,item in value.items():
            if key in properties:errors.extend(schema_check(item,properties[key],pointer+'/'+key))
    elif kind=='array':
        for index,item in enumerate(value):errors.extend(schema_check(item,contract['items'],pointer+'/'+str(index)))
    return errors
schema_errors=schema_check(raw,schema)
namespace={'__name__':'recovery_frozen_validator'}
validator_bytes=(RUN/'frozen_validator.py').read_bytes()
exec(compile(validator_bytes,str(RUN/'frozen_validator.py'),'exec'),namespace)
validator_errors=namespace['validate'](packet,raw)
assert schema_errors==[] and validator_errors==[]
assert len(packet['rows'])==len(raw['rows'])==25
assert [r['id'] for r in packet['rows']]==[r['id'] for r in raw['rows']]

events=[json.loads(line) for line in event_bytes.decode().splitlines()]
messages=[];transport_errors=[];actual_tools=[];unknown=[];turns=0
for line,event in enumerate(events,1):
    item=event.get('item',{})
    if event['type']=='item.completed' and item.get('type')=='agent_message':
        parsed=json.loads(item['text'])
        messages.append({'line_1based':line,'item_id':item['id'],'text_sha256':sha(item['text'].encode()),
            'canonical_sha256':sha(canonical(parsed)),'raw_bytes_equal':item['text'].encode()==raw_bytes})
    elif event['type']=='error' or item.get('type')=='error':
        message=event.get('message',item.get('message',''))
        assert 'request timed out' in message
        transport_errors.append({'line_1based':line,'event':event,'classification':'network_transport_error_non_tool'})
    elif event['type']=='turn.completed':turns+=1
    elif event['type'] in ['thread.started','turn.started']:pass
    elif item.get('type') in ['command_execution','mcp_tool_call','web_search','tool_call','function_call']:
        actual_tools.append({'line_1based':line,'event':event})
    else:unknown.append({'line_1based':line,'event':event})
distinct=collections.Counter(m['canonical_sha256'] for m in messages)
assert len(distinct)==1 and len(messages)==2 and all(m['raw_bytes_equal'] for m in messages)
assert actual_tools==[] and unknown==[] and turns==1 and metadata['exit_code']==0

# Source bindings use only the same input row, without concatenating distinct fields.
TEXT_KEYS={'text','headers','row_cells','caption','definition','title','note'}
def context_literals(value,pointer='',context_id=None):
    if isinstance(value,list):
        for n,item in enumerate(value):yield from context_literals(item,f'{pointer}/{n}',context_id)
    elif isinstance(value,dict):
        context_id=value.get('context_id',context_id)
        for key,item in value.items():
            child=f'{pointer}/{key}'
            if key in TEXT_KEYS and isinstance(item,str):yield child,context_id,item
            elif isinstance(item,(list,dict)):yield from context_literals(item,child,context_id)
def spans(text,quote):
    start=0;found=[]
    while True:
        position=text.find(quote,start)
        if position<0:return found
        found.append({'start_char_0based':position,'end_char_exclusive_0based':position+len(quote)})
        start=position+1

prediction_lines=[];lineages=[]
for index,(source,row) in enumerate(zip(packet['rows'],raw['rows'])):
    prediction_line=json.dumps(row,ensure_ascii=False,separators=(',',':'))+'\n'
    prediction_lines.append(prediction_line)
    evidence_bindings=[]
    for evidence_index,evidence in enumerate(row['evidence']):
        quote=evidence['quote']
        haystacks=[(f'/rows/{index}/text',None,source['text'])] if evidence['source']=='unit' else list(context_literals(source['contexts'],f'/rows/{index}/contexts'))
        matches=[{'input_json_pointer':pointer,'context_id':context_id,'source_text_sha256':sha(text.encode()),
                  'continuous_literal_spans':spans(text,quote)}
                 for pointer,context_id,text in haystacks if quote in text]
        assert matches
        evidence_bindings.append({'evidence_index_0based':evidence_index,'dimension':evidence['dimension'],
            'declared_source':evidence['source'],'original_quote_sha256':sha(quote.encode()),
            'matches_in_own_input_row':matches})
    row_canonical=sha(canonical(row))
    lineages.append({'id':row['id'],'prediction_line_1based':index+1,
        'original_attempt':str(ATTEMPT),'original_output_json_pointer':f'/rows/{index}',
        'original_input_json_pointer':f'/rows/{index}',
        'original_input_file_sha256':sha(input_bytes),'original_input_row_canonical_sha256':sha(canonical(source)),
        'original_unit_text_sha256':sha(source['text'].encode()),
        'original_contexts_canonical_sha256':sha(canonical(source['contexts'])),
        'original_raw_output_file_sha256':sha(raw_bytes),'original_output_row_canonical_sha256':row_canonical,
        'prediction_jsonl_line_sha256_including_newline':sha(prediction_line.encode()),
        'prediction_row_canonical_sha256':row_canonical,'all_row_fields_unchanged':json.loads(prediction_line)==row,
        'bound_original_events_sha256':sha(event_bytes),'bound_original_metadata_sha256':sha(metadata_bytes),
        'bound_completed_message_canonical_sha256':messages[0]['canonical_sha256'],
        'literal_evidence_bindings':evidence_bindings})

copies={'original_raw_output.json':raw_bytes,'same_batch_input.json':input_bytes,
    'original_events.jsonl':event_bytes,'original_run_metadata.json':metadata_bytes,
    'frozen_schema.json':schema_bytes,'frozen_validator.py':validator_bytes}
for filename,data in copies.items():(OUT/filename).write_bytes(data)
(OUT/'predictions.jsonl').write_text(''.join(prediction_lines))
(OUT/'prediction_lineage.jsonl').write_text(''.join(json.dumps(row,ensure_ascii=False,separators=(',',':'))+'\n' for row in lineages))
recovered=json.loads((OUT/'original_raw_output.json').read_text())
jsonl_rows=[json.loads(s) for s in (OUT/'predictions.jsonl').read_text().splitlines()]
assert recovered==raw and jsonl_rows==raw['rows']
copy_proof={name:{'original_sha256':sha(data),'recovered_sha256':sha((OUT/name).read_bytes()),
                  'byte_for_byte_equal':(OUT/name).read_bytes()==data} for name,data in copies.items()}
binding={'status':'corrected_technical_event_binding','original_status':metadata['status'],
    'original_status_unchanged':True,'completed_agent_message_event_n':len(messages),
    'unique_different_completed_output_n':len(distinct),'message_bindings':messages,
    'network_transport_errors_non_tools':transport_errors,'actual_tool_event_n':len(actual_tools),
    'unknown_event_n':len(unknown),'turn_completed_n':turns,
    'correction':'只把原第3/9行相同completed JSON的重复发生合并为一个不同输出，并把第4–8行实际网络错误分类为非tool；不删改原events，不改原严格audit。',
    'reject_multiple_different_completed_outputs':True,'output_full_object_canonical_sha256':sha(canonical(raw)),
    'semantic_correctness_verified':False,'human_validation':False}
dump(OUT/'corrected_event_binding.json',binding)
validation={'status':'corrected_technical_event_binding','schema_path':str(RUN/'frozen_schema.json'),
    'schema_sha256':sha(schema_bytes),'validator_path':str(RUN/'frozen_validator.py'),
    'schema_check_engine':'Python stdlib bounded interpreter of all assertion keywords in this frozen schema; jsonschema package unavailable',
    'validator_sha256':sha(validator_bytes),'schema_errors':schema_errors,'frozen_validator_errors':validator_errors,
    'schema_and_literal_validator_pass':True,'input_record_n':25,'output_record_n':25,
    'evidence_n':sum(len(r['evidence']) for r in raw['rows']),
    'all_fields_unchanged':recovered==raw and jsonl_rows==raw['rows'],
    'all_25_original_and_prediction_row_fields_equal':[{'id':old['id'],'equal':old==new} for old,new in zip(raw['rows'],jsonl_rows)],
    'quote_changed_n':0,'model_called':False,'semantic_correctness_verified':False,'human_validation':False,
    'copy_sha_and_bytes_proof':copy_proof}
dump(OUT/'technical_validation_and_preservation.json',validation)

mapping_path=W/'人工参照复核/新定义概率180复核同步02/admin/PRIVATE_mapping_and_design.json'
mapping=json.loads(mapping_path.read_text());sample={r['design_id'] for r in mapping['coders']['A']}
assert len(sample)==180 and sample=={r['design_id'] for r in mapping['coders']['B']}
source03_path=W/'LLM编码/统一判据编码准备/共用纯来源材料03/source_only_with_scope03.jsonl'
targets={'RECODE25-00929','RECODE25-01956','RECODE25-02286','RECODE25-03894'}
present=set()
with source03_path.open() as stream:
    for line in stream:
        row=json.loads(line)
        if row['id'] in targets:present.add(row['id'])
assert present==targets
intersection={'scope':'仅交集核查，不修改人工表',
    'source03_changed_three_intersection_with_probability180':sorted(sample&{'RECODE25-00929','RECODE25-01956','RECODE25-02286'}),
    'record03894_intersection_with_probability180':sorted(sample&{'RECODE25-03894'}),
    'sample_n':180,'sample_mapping_path':str(mapping_path),'sample_mapping_sha256':sha(mapping_path.read_bytes())}
dump(OUT/'sample_intersection_only.json',intersection)
unchanged={str(p):sha(p.read_bytes())==digest for p,digest in protected_files.items()}
assert all(unchanged.values())
dump(OUT/'original_run_unchanged_proof.json',{'all_original_batch_and_frozen_files_byte_unchanged':True,'files':unchanged})
manifest={'status':'corrected_technical_event_binding','original_attempt':str(ATTEMPT),
    'original_raw_output_sha256':sha(raw_bytes),'recovered_raw_output_sha256':sha((OUT/'original_raw_output.json').read_bytes()),
    'predictions_jsonl_sha256':sha((OUT/'predictions.jsonl').read_bytes()),
    'prediction_lineage_jsonl_sha256':sha((OUT/'prediction_lineage.jsonl').read_bytes()),
    'output_n':25,'quote_changed_n':0,'all_fields_unchanged':True,
    'old_failed_status_preserved':True,'selection_basis':'最早实际完整输出及事件绑定；未按标签或指标挑选。',
    'schema_and_literal_checks_pass':True,'semantic_correctness_verified':False,'human_validation':False,'model_called':False,
    'sample_intersections':intersection,
    'files':{p.name:sha(p.read_bytes()) for p in OUT.iterdir() if p.is_file()}}
dump(OUT/'recovery_manifest.json',manifest)
(OUT/'恢复说明.txt').write_text('batch-0155原实际输出技术恢复\n\n状态：corrected_technical_event_binding。\n原attempt-01完整raw按字节保存；25行predictions逐行完整保存原rows字段。引文、labels、dimension_reasons、subtypes、质量标记及所有其他字段均未更改。\n已实际运行冻结JSON schema及frozen_validator，25条结构与自身来源字面证据检查均通过。\n原events第3/9行是字节相同的完整JSON重复发生，唯一不同completed输出数为1；第4–8行是网络超时/传输回退错误，无tool事件。更正分类与绑定依据另存，旧failed状态和原运行文件保持。\n本包只作技术恢复，不宣称语义有效或真人验证；未调用模型。\n\n180样本交集：00929/01956/02286为空；03894为空。未改人工表。\n')
print(json.dumps({'directory':str(OUT),'status':manifest['status'],'rows':25,'schema_errors':schema_errors,
    'validator_errors':validator_errors,'original_recovered_raw_sha_equal':manifest['original_raw_output_sha256']==manifest['recovered_raw_output_sha256'],
    'predictions_jsonl_sha256':manifest['predictions_jsonl_sha256'],'intersection_three':intersection['source03_changed_three_intersection_with_probability180'],
    'intersection03894':intersection['record03894_intersection_with_probability180']},ensure_ascii=False))
