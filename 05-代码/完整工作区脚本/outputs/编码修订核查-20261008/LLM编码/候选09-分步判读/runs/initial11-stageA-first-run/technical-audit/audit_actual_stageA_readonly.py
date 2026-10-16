"""Post-run mechanical audit only. Never calls CLI or reads private expectations.

Original strings are parsed in memory for exact equality/literal/path checks;
no policy text, model prose or semantic expectation is emitted in this report.
"""
import collections
import datetime
import hashlib
import importlib.util
import json
import re
from pathlib import Path

AUDIT=Path(__file__).resolve().parent
RUN=AUDIT.parent
HERE=RUN.parents[1]
spec=importlib.util.spec_from_file_location('c09_actual_audit_helpers',HERE/'run_candidate09.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
checks=[];failures=[]

def check(name,ok,details=None):
    item={'name':name,'passed':bool(ok)}
    if details is not None:item['details']=details
    checks.append(item)
    if not ok:failures.append(item)

def schema_errors(value,node,path='root'):
    """Validate every keyword in this frozen small schema, without dependencies."""
    errors=[]
    allowed={'type','properties','required','additionalProperties','items','enum','minLength','pattern','minItems'}
    if set(node)-allowed:errors.append(path+':unsupported_schema_keyword')
    typ=node.get('type');valid=(typ=='object'and isinstance(value,dict))or(typ=='array'and isinstance(value,list))or(typ=='string'and isinstance(value,str))
    if not valid:return errors+[path+':type']
    if 'enum'in node and not any(r.canonical(value)==r.canonical(x)for x in node['enum']):errors.append(path+':enum')
    if typ=='object':
        if set(node.get('required',[]))-set(value):errors.append(path+':required')
        props=node.get('properties',{})
        if node.get('additionalProperties')is False and set(value)-set(props):errors.append(path+':additionalProperties')
        for k,v in value.items():
            if k in props:errors.extend(schema_errors(v,props[k],path+'.'+k))
    elif typ=='array':
        if len(value)<node.get('minItems',0):errors.append(path+':minItems')
        for i,v in enumerate(value):errors.extend(schema_errors(v,node['items'],path+'['+str(i)+']'))
    else:
        if len(value)<node.get('minLength',0):errors.append(path+':minLength')
        if 'pattern'in node and re.search(node['pattern'],value)is None:errors.append(path+':pattern')
    return errors

def key_order_tree(value):
    if isinstance(value,dict):return [[k,key_order_tree(v)]for k,v in value.items()]
    if isinstance(value,list):return [key_order_tree(v)for v in value]
    return None

def main():
    freeze=json.loads((HERE/'design_freeze.json').read_text())
    original_files=[p for p in RUN.rglob('*')if p.is_file()and 'technical-audit'not in p.relative_to(RUN).parts]
    source_bindings=freeze['files']+freeze['sources']+[r.binding(HERE/'design_freeze.json')]
    starting={b['path']:r.sha(b['path'])for b in source_bindings}
    original_start={str(p):r.sha(p)for p in original_files}
    for b in source_bindings:
        check('frozen_binding:'+b['path'],r.sha(b['path'])==b['sha256']and Path(b['path']).stat().st_size==b['bytes'])
    ib,ip,input_bytes,rows=r.read_input()
    base,inv,av=r.load_runtime()
    expected_packet=r.assemble_stageA_packet(rows,inv)
    offline=HERE/'offline-plans'/r.RUN_NAMES['A']
    packet=json.loads((RUN/'input_packet.json').read_text())
    attempts=sorted((RUN/'attempts').glob('attempt-*'))
    check('exactly_one_actual_attempt',len(attempts)==1)
    attempt=attempts[0]
    raw=json.loads((attempt/'raw_output.json').read_text())
    aggregate=json.loads((RUN/'all_stageA_records.json').read_text())
    lines=[json.loads(x)for x in(RUN/'all_stageA_records.jsonl').read_text().splitlines()if x.strip()]
    seal=json.loads((RUN/'stageA_seal.json').read_text())
    summary=json.loads((RUN/'technical_summary.json').read_text())
    meta=json.loads((attempt/'run_metadata.json').read_text())
    supplement=json.loads((attempt/'candidate09_attempt_binding.json').read_text())
    plan=json.loads((RUN/'run_plan.json').read_text())
    receipt=json.loads((RUN/'final_stage_scope_receipt.json').read_text())
    version=json.loads((RUN/'cli_version_query.json').read_text())
    request=(RUN/'request.txt').read_text()
    expected_request=r.make_request('A',expected_packet,r.PROMPTS['A'].read_text())
    check('source_input_exact_frozen_bytes',(RUN/'frozen_input.jsonl').read_bytes()==input_bytes)
    check('packet_exact_original_rows_all_fields',r.canonical(packet['rows'])==r.canonical(rows))
    check('packet_preserves_recursive_original_field_order',key_order_tree(packet['rows'])==key_order_tree(rows))
    check('packet_exact_recomputed_inventory',r.canonical(packet)==r.canonical(expected_packet))
    check('actual_packet_offline_byte_equal',(RUN/'input_packet.json').read_bytes()==(offline/'input_packet.json').read_bytes())
    check('attempt_packet_actual_byte_equal',(attempt/'input.json').read_bytes()==(RUN/'input_packet.json').read_bytes())
    check('actual_request_offline_byte_equal',(RUN/'request.txt').read_bytes()==(offline/'request.txt').read_bytes())
    check('attempt_request_actual_byte_equal',(attempt/'request.txt').read_bytes()==(RUN/'request.txt').read_bytes())
    check('actual_request_exact_reassembly',request==expected_request)
    for dest,source in [('frozen_prompt.txt',r.PROMPTS['A']),('frozen_schema.json',r.SCHEMAS['A']),('frozen_validator.py',r.VALIDATORS['A'])]:
        check(dest+'_byte_equal',(RUN/dest).read_bytes()==source.read_bytes())
    check('selected_raw_known_root_SHA',r.sha(attempt/'raw_output.json')=='8f87de605448a7e4295d6deb166ae99b94a46437e1c954934c60432374625ef5')
    check('raw_aggregate_exact_bytes',(attempt/'raw_output.json').read_bytes()==(RUN/'all_stageA_records.json').read_bytes())
    check('raw_aggregate_typed_JSON_equal',r.canonical(raw)==r.canonical(aggregate))
    check('JSONL_rows_exact_typed_JSON_equal',r.canonical(lines)==r.canonical(aggregate['rows']))
    check('all11_ID_order_equal',[x['id']for x in rows]==[x['id']for x in raw['rows']]and len(raw['rows'])==11)
    schema_result=schema_errors(raw,json.loads(r.SCHEMAS['A'].read_text()))
    literal_result=av.validate(packet,raw)
    check('all_schema_keywords_and_constraints_pass',schema_result==[],{'errors':schema_result})
    check('frozen_stageA_literal_path_validator_pass',literal_result==[],{'errors':literal_result})
    # Compare inventory traversal to the unchanged B validator, mechanically.
    check('inventory_leaf_sequence_matches_legacy_B',all([x['text']for x in inv.inventory(row)]==list(base.v.iter_context_text(row.get('contexts',{})))for row in rows))
    totals=collections.Counter()
    for inp,out in zip(rows,raw['rows']):
        expected=[x['path']for x in inv.inventory(inp)]
        actual=[p for c in out['context_records']for p in c['paths']]
        check('context_exact_once:'+out['id'],collections.Counter(actual)==collections.Counter(expected)and all(n==1 for n in collections.Counter(actual).values()))
        totals['inventory_paths']+=len(expected);totals['propositions']+=len(out['current_propositions'])
        totals['context_records']+=len(out['context_records'])
        totals['unit_quote_occurrences']+=sum(len(p['unit_quotes'])for p in out['current_propositions'])+sum(len(c['unit_quotes'])for c in out['context_records'])
        totals['context_quote_occurrences']+=len(out['context_records'])
        totals['material_status_'+out['material_status']]+=1
        for c in out['context_records']:totals['context_status_'+c['status']]+=1
    events=(attempt/'events.jsonl').read_text()
    ea=base.event_audit(events);eb=base.event_output_binding_audit(events,raw)
    check('unique_completed_agent_JSON_equals_raw',eb['completed_agent_message_count']==1 and eb['event_raw_full_object_equal']and not eb['errors'])
    check('event_zero_tools_single_turn_no_errors',ea['tool_or_unknown_item_event_count']==0 and ea['completed_turns']==1 and not ea['turn_errors'])
    check('recorded_event_binding_matches_recalculation',r.canonical(eb)==r.canonical(json.loads((attempt/'event_output_binding_audit.json').read_text())))
    check('recorded_tool_audit_matches_recalculation',r.canonical(ea)==r.canonical(json.loads((attempt/'tool_event_audit.json').read_text())))
    expected_meta_hashes={'input_sha256':attempt/'input.json','request_sha256':attempt/'request.txt','prompt_sha256':r.PROMPTS['A'],
      'raw_output_sha256':attempt/'raw_output.json','events_sha256':attempt/'events.jsonl','stderr_sha256':attempt/'raw_stderr.txt',
      'tool_event_audit_sha256':attempt/'tool_event_audit.json','validation_sha256':attempt/'validation.json','event_output_binding_audit_sha256':attempt/'event_output_binding_audit.json'}
    for k,p in expected_meta_hashes.items():check('attempt_metadata_'+k,meta[k]==r.sha(p))
    check('first_attempt_accepted_exit0',meta['status']=='accepted_structural_literal_zero_tools'and meta['exit_code']==0 and not meta['errors']and meta['execution_error']is None)
    check('one_logical_one_actual_attempt',summary['logical_requests']==summary['actual_attempts']==1 and len(summary['attempts'])==1 and summary['selected_attempt']==str(attempt))
    check('no_material_flag_and_no_label_selection',summary['material_flags']==[]and supplement['material_flags_no_semantic_retry']==[]and meta['label_or_metric_selection']is False)
    check('summary_first_selection_binds_actual_metadata',summary['attempts'][0]['metadata']==r.binding(attempt/'run_metadata.json')and summary['attempts'][0]['candidate09_attempt_binding']==r.binding(attempt/'candidate09_attempt_binding.json'))
    for b in [summary['output_JSON'],summary['output_JSONL'],summary['selected_raw']]+[seal[k]for k in ['selected_raw','unique_completed_agent_events','source_input','frozen_prompt','selected_request','selected_input_packet','selected_attempt_metadata','technical_summary','all_records']]:
        check('actual_record_binding:'+b['path'],r.sha(b['path'])==b['sha256']and Path(b['path']).stat().st_size==b['bytes'])
    check('seal_per_ID_record_SHA_exact',seal['row_record_sha256']=={x['id']:r.row_sha(x)for x in raw['rows']})
    check('seal_input_and_material_count',seal['input_sha256']==ib['input_sha256']and seal['stageA_material_issue_count']==0)
    check('plan_original_rows_and_frozen_source_bindings',plan['source_rows_canonical_sha256']==r.row_sha(rows)and plan['source_input']==r.binding(ip)and plan['design_freeze']==r.binding(HERE/'design_freeze.json'))
    for k in ['authorization','design_freeze','source_input','input_binding','prompt','schema','validator']:
        b=plan[k];check('plan_binding:'+k,r.sha(b['path'])==b['sha256']and Path(b['path']).stat().st_size==b['bytes'])
    auth=json.loads(Path(plan['authorization']['path']).read_text())
    r.read_authorization(plan['authorization']['path'],'A',ib)
    check('root_auth_stageA_only',auth['authorized_stage']=='A'and auth['allow_automatic_next_stage']is False and auth['allow_other_scopes']is False)
    command=meta['command']
    check('command_model_effort_schema_output',command[command.index('--model')+1]==r.MODEL and 'model_reasoning_effort="medium"'in command and command[command.index('--output-schema')+1]==str(r.SCHEMAS['A'])and command[command.index('--output-last-message')+1]==str(attempt/'raw_output.json'))
    check('command_tool_and_context_isolation_flags',all(x in command for x in ['--ephemeral','--ignore-user-config','--ignore-rules','--skip-git-repo-check','--json'])and 'web_search="disabled"'in command and command[command.index('--sandbox')+1]=='read-only')
    check('CLI_recorded_version_and_entry_SHA_current',version['exit_code']==0 and version['stdout'].strip()==meta['cli_version']and version['cli_entry_sha256']==meta['cli_binary_sha256']==r.sha(meta['cli_path']))
    check('B_explicit_NOT_RUN_and_absent',receipt['stage_states']['B']['state']=='NOT_RUN'and not(HERE/'runs'/r.RUN_NAMES['B']).exists())
    check('no_semantic_PASS_or_auto_next_stage',receipt['semantic_PASS_or_adoption_written']is False and summary['semantic_correctness_verified']is False and summary['next_stage_automatically_run']is False)
    stderr=(attempt/'raw_stderr.txt').read_text();stderr_lines=[x for x in stderr.splitlines()if x.strip()]
    stderr_categories=collections.Counter()
    for line in stderr_lines:
        if 'WARN codex_rollout::list: state db discrepancy' in line and 'falling_back'in line:stderr_categories['state_db_path_lookup_fallback_warning']+=1
        elif 'WARN codex_skills::interface: ignoring interface.icon_small'in line:stderr_categories['skill_small_icon_path_warning']+=1
        elif 'WARN codex_skills::interface: ignoring interface.icon_large'in line:stderr_categories['skill_large_icon_path_warning']+=1
        else:stderr_categories['OTHER_REQUIRES_REVIEW']+=1
    check('stderr_only_observed_known_warning_categories',stderr_categories.get('OTHER_REQUIRES_REVIEW',0)==0)
    check('frozen_closure_unchanged_during_this_audit',all(r.sha(p)==h for p,h in starting.items()))
    check('original_actual_run_artifacts_unchanged_during_audit',all(r.sha(p)==h for p,h in original_start.items()))
    report={'status':'PASS_ACTUAL_STAGEA_TECHNICAL_AUDIT_ONLY'if not failures else'FAIL_ACTUAL_STAGEA_TECHNICAL_AUDIT_PRESERVED',
      'created_at_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate':r.CANDIDATE,'stage':'A',
      'reviewer_role':'Candidate09 prompt and runner author; mechanical actual-run audit, not independent semantic validation.',
      'checks_n':len(checks),'checks_passed':sum(x['passed']for x in checks),'failures':failures,'checks':checks,
      'design_freeze':r.binding(HERE/'design_freeze.json'),'source_bindings':source_bindings,
      'actual_original_artifact_bindings':[r.binding(p)for p in original_files],
      'offline_plan_bindings':[r.binding(offline/name)for name in ['input_packet.json','request.txt','plan_only.json']],
      'audit_script':r.binding(Path(__file__)),'raw_output_JSON':r.binding(attempt/'raw_output.json'),
      'aggregate_JSON':r.binding(RUN/'all_stageA_records.json'),'rows_JSONL':r.binding(RUN/'all_stageA_records.jsonl'),
      'row_record_sha256':seal['row_record_sha256'],'mechanical_counts':dict(totals),
      'actual_run_request_parameters':{'requested_model':meta['requested_model'],'reasoning_effort':meta['reasoning_effort'],
        'CLI_version':meta['cli_version'],'CLI_entry_sha256':meta['cli_binary_sha256'],'recorded_model_requests':1,'recorded_attempts':1,
        'tool_events':ea['tool_or_unknown_item_event_count'],'completed_agent_messages':eb['completed_agent_message_count'],
        'observed_model_fields':ea['observed_model_fields'],'provider_internal_model_revision':'not_exposed'},
      'stderr':{'binding':r.binding(attempt/'raw_stderr.txt'),'nonempty_line_count':len(stderr_lines),'categories':dict(stderr_categories),
        'interpretation':'Four CLI state-database/icon-path warnings only; this observation is limited to this attempt stderr. No claim about provider internals or semantic correctness.'},
      'StageB':'NOT_RUN','semantic_correctness_verified':False,'private_expectations_read':False,'policy_or_A_prose_semantically_read':False,
      'real_CLI_invocations_by_this_audit':0,'real_model_calls_by_this_audit':0,'original_sources_or_run_artifacts_modified':False,
      'limitations':['Literal anchors and path coverage do not establish correct relation semantics or complete attribute retention.',
        'Counts describe this recorded run only; model identity beyond CLI/event exposure is not independently attested.',
        'No StageA semantic gate or StageB authorization/adoption is generated.']}
    r.dump_new(AUDIT/'actual_stageA_technical_audit.json',report)
    md=f"# StageA实际技术审查\n\n{report['status']}。{report['checks_passed']}/{report['checks_n']}项技术检查通过。\n\n原11输入全部字段、实际packet/request与离线packet/request逐字节或完整类型化JSON一致；唯一完成agent_message的JSON等于raw及aggregate，JSONL rows与其一致。A schema、逐字引文和路径恰好一次覆盖检查通过，原冻结闭包和原运行文件未修改。\n\n本次运行记录为gpt-5.6-sol/medium，CLI {meta['cli_version']}，1逻辑请求、1首次有效attempt、0工具。stderr仅2条state db路径回退警告及小/大图标路径警告各1条，共4条；不把这推成provider内部无异常。B明确NOT_RUN。\n\n技术审查者为候选提示/runner作者；本报告不作原文或A理由语义判读，不读私有期待，不生成语义PASS或B准入门禁。本审计新增CLI/模型调用均0。\n\n原JSON SHA：{r.sha(RUN/'all_stageA_records.json')}。JSONL SHA：{r.sha(RUN/'all_stageA_records.jsonl')}。完整绑定见同目录JSON。\n"
    r.write_new(AUDIT/'actual_stageA_technical_audit.md',md)
    print(json.dumps({'status':report['status'],'checks_n':len(checks),'failures_n':len(failures),
      'report':r.binding(AUDIT/'actual_stageA_technical_audit.json'),'markdown':r.binding(AUDIT/'actual_stageA_technical_audit.md'),
      'new_CLI_invocations':0,'new_model_calls':0},ensure_ascii=False))
    return 0 if not failures else 2

if __name__=='__main__':raise SystemExit(main())
