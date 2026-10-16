#!/usr/bin/env python3
"""Bind all43 finite inputs and preserve every result; do not call a judge."""
import copy
import datetime
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
V2=ROOT/'06-coding/rule-v20-SEEconomic-repair-sol/versions/v2'


def load(p):return json.loads(Path(p).read_bytes())


def canon(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()


def value_binding(v):
    raw=canon(v);return {'canonical_UTF8_bytes':len(raw),'canonical_sha256':hashlib.sha256(raw).hexdigest()}


def bind(p):
    p=Path(p).resolve();raw=p.read_bytes()
    return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def write(name,value):
    with (OUT/name).open('x',encoding='utf8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')


verification=load(OUT/'sealed-input-verification.json')
for item in verification['files']:
    assert bind(item['path'])==item,item['path']
preseal=load(OUT/'pre-execution-seal.json')
for item in preseal['inputs']:
    assert bind(item['path'])==item,item['path']
for snapshot in verification['code_snapshots']:
    assert bind(snapshot['independent_snapshot']['path'])==snapshot['independent_snapshot']
    assert bind(snapshot['owner_binding']['path'])==snapshot['owner_binding']

# Pure adapter readback reconstructs the received unit from the immutable
# presealed source. This is not a new relation/classification execution.
spec=importlib.util.spec_from_file_location('readback_source_packet',OUT/'code-snapshot/source_packet.py')
adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
execution=load(OUT/'execution-results.json')
by_result={(r['suite'],r['name']):r for r in execution['cases']}
specs={};input_rows=[]
for suite,filename in (('legacy20','legacy20-controls.json'),('new20','new20-fixed-before-execution.json'),
                        ('owner_closure3','owner-closure3-fixed-before-execution.json')):
    data=load(OUT/filename)
    for index,case in enumerate(data['cases']):
        mode='prebuilt_semantic_unit' if 'synthetic_input' in case else 'raw_bundle_adapted_by_sealed_SourcePacket'
        raw=case.get('synthetic_input',case.get('synthetic_bundle',case.get('bound_source_bundle')))
        unit=copy.deepcopy(raw) if 'synthetic_input' in case else adapter.semantic_unit(raw)
        key=(suite,case['name']);result=by_result[key]
        assert result['current_text']==unit['text']
        specs[key]={'case':case,'unit':unit}
        input_rows.append({'suite':suite,'name':case['name'],'source_file':bind(OUT/filename),
                           'case_JSON_pointer':f'/cases/{index}',
                           'source_input_kind':mode,'raw_input_object_binding':value_binding(raw),
                           'reconstructed_received_semantic_unit_binding':value_binding(unit),
                           'expected_binding':value_binding(case['expected']),
                           'code_algorithm_sha256':preseal['algorithm_sha256'],
                           'reconstructed_current_equals_executed_current':True,
                           'judge_attempted_once':result['judge_attempted'],
                           'no_additional_judge_call_for_this_readback':True})
assert len(input_rows)==43 and len({(r['suite'],r['name']) for r in input_rows})==43
write('executed43-input-bindings.json',input_rows)

failure_spec={
 'article_remote_next_boundary_unprovided_condition':{
   'category':'incomplete_scope_wrongly_accepted_as_closed',
   'path':'relations._se_group_proof → _se_article_proof → SE_closed_explicit_article_condition → dimensions._units/_safety_effect/_economics',
   'code_locations':[{'file':'relations.py','line':1751},{'file':'relations.py','line':1823}],
   'description':'末成员p0004之后尚有未供第四项条件；所谓next是p0099/sequence99。函数只核boundary字段指向的文本同源、同组件且非成员，未核该段真为紧接末成员的闭合边界；错误承认完整条件组。',
   'manual_lines':[22,23,25,39,40,41],
   'meaning':'期望NULL保留；实际1/1/1是缺闭合接口误接通，不能硬改期望为0或当正式FP/FN。'},
 'single_article_next_other_component':{
   'category':'incomplete_scope_cross_component_boundary_accepted',
   'path':'relations._se_article_proof single-paragraph fallback → SE_closed_explicit_article_condition',
   'code_locations':[{'file':'relations.py','line':1823}],
   'description':'当前第十条的成员在C-SCOPE，所谓相邻第十一条在C-OTHER。单段fallback仅同SHA和相邻段号，未核same_component，借另一组件证明当前末界。',
   'manual_lines':[22,23,25,40,41,42],
   'meaning':'缺当前组件真实末界，期望S/E/Ec皆NULL。实际S1、E0、Ec0都超出本控制的可判资格。'},
 'safety_parent_other_component_reused_pid':{
   'category':'actual_parent_relation_overreach',
   'path':'relations._se_direct_content_parents → SE_direct_safety_content_member → dimensions._safety_effect',
   'code_locations':[{'file':'relations.py','line':1723},{'file':'dimensions.py','line':959}],
   'description':'当前数据列示在C-CURRENT；安全内容父句在C-OTHER但重用target_paragraph_id=p0002。目标段号碰撞不能建立当前直接父关系，函数未拒绝跨组件。',
   'manual_lines':[9,22,42,58,90],
   'meaning':'材料中关系明确不相属，固定S0实际S1，是实质范围越界，不是待补原文。'},
 'effect_indicator_not_safety_sibling':{
   'category':'actual_sibling_content_overreach',
   'path':'relations._se_bounded_content explicit_indicator_definition → SE_explicit_indicator_definition(affected_dimensions S/E) → dimensions._safety_effect',
   'code_locations':[{'file':'relations.py','line':1676},{'file':'dimensions.py','line':959}],
   'description':'当前明确核验“上述疗效指标”；同段前文分别定义安全性观察指标和疗效观察指标。宽泛antecedent同时选两类，把并列安全指标作为当前疗效指代补足，错误新增S。',
   'manual_lines':[15,22,39,42,94,96],
   'meaning':'E1符合；S固定0实际1。确指类型应由当前关系限定，不能因同药同段就扩维。'},
 'payment_parent_other_component_reused_pid':{
   'category':'actual_payment_parent_relation_overreach',
   'path':'relations._parents + _se_direct_content_parents → generic/SE_direct_payment_condition_member → dimensions._economics',
   'code_locations':[{'file':'relations.py','line':466},{'file':'relations.py','line':1723},{'file':'dimensions.py','line':1028}],
   'description':'当前成人患者数据成员在C-CURRENT，费用—基金支付父句在C-OTHER且重用段号；旧generic父路径和新增SE支付路径都接通。只修其中一路仍可能保留错误经济继承。',
   'manual_lines':[22,42,58,106,110,114],
   'meaning':'固定Ec0实际1，实际关系越界；不要求调金额或修改手册定义。'}}

failures=[]
for row in execution['cases']:
    if row['passed']:continue
    key=(row['suite'],row['name']);case=specs[key]['case'];unit=specs[key]['unit']
    details=failure_spec.get(row['name'],{
        'category':'historical_fixture_missing_closure_not_new_semantic_rule_error',
        'path':'relations._se_operational_references → material_requests[cited_standard] → Accumulator.finish',
        'code_locations':[{'file':'relations.py','line':1858},{'file':'dimensions.py','line':401}],
        'description':'原独审完整条文控制实际只有heading和三个编号成员、末句句号，没有原件首末/下一段闭合。旧预期1/1/1原样保留，当前NULL是缺当前确指闭合接口。',
        'manual_lines':[23,25,39,40,41],
        'meaning':'这是旧控制输入不足；不是要求v2强行恢复1或在未知上填0。'})
    failures.append({'suite':row['suite'],'name':row['name'],**details,
                     'current_text':unit['text'],'source_ref':unit['source_ref'],
                     'complete_supplied_contexts':unit['contexts'],
                     'complete_received_unit':unit,'original_presealed_case':case,
                     'expected':row['expected'],'observed':row['observed'],'mismatches':row.get('mismatches'),
                     'actual_relation_traces':row.get('relation_traces'),
                     'actual_material_requests':row.get('material_requests'),
                     'actual_decisions':row.get('decisions'),
                     'input_binding':next(r for r in input_rows if (r['suite'],r['name'])==key),
                     'interpretation_is_not_formal_accuracy':True})
assert len(failures)==6 and len(failure_spec)==5
write('all-failures-full-inputs-and-paths.json',failures)

closures=[];pdf_bindings=[]
for suite,name in [('owner_closure3','complete_renewal_total'),
                   ('owner_closure3','complete_explicit_article_condition'),
                   ('owner_closure3','different_title_same_substance'),
                   ('legacy20','complete_explicit_article_three_dimensions')]:
    key=(suite,name);case=specs[key]['case'];unit=specs[key]['unit'];row=by_result[key]
    entry={'suite':suite,'name':name,'current_text':unit['text'],
           'complete_supplied_contexts':unit['contexts'],'historical_expected':case.get('historical_expected_unchanged',case['expected']),
           'actual_observed_all5':row['observed_all5'],'material_requests':row['material_requests'],
           'new_independent_closure_target':case['expected'] if suite=='owner_closure3' else None,
           'historical_expected_not_rewritten':True,'manual_lines':[23,25,39,40,41],
           'only_structural_interface_missing_not_a_claim_no_original_exists':True}
    if name=='complete_renewal_total':
        b=case['bound_source_bundle'];doc=b['source_documents'][0]
        original=bind(doc['snapshot']);assert original['sha256']==doc['source_sha256'] and original['bytes']==doc['bytes']
        pdf_bindings.append(original)
        entry.update({'actual_bound_PDF_exists_and_SHA_bytes_match':original,
                      'source_document_record':doc,
                      'source_text_resources_N':len(b['source_full_text_resources']),
                      'source_assets_N':len(b['source_asset_locations']),
                      'ordered_member_N':sum(c['kind']=='ordered_members' for c in unit['contexts']),
                      'missing_interface':'9有序成员无parent/list/boundary容器及末界；原PDF可用但本轮未渲染、逐页读图或生成新结构。',
                      'original_PDF_semantically_read':False})
    else:
        entry['missing_interface']='合成cited_article仅article/sequence_index，未提供容器首末或相邻下一段；连续编号、句号不等于完整性认证。'
    closures.append(entry)
write('owner-four-closure-reception.json',closures)

static=[
 {'status':'actual_failures_demonstrated','topic':'same-source is insufficient for component and finite current relation',
  'demonstrating_cases':['single_article_next_other_component','safety_parent_other_component_reused_pid','payment_parent_other_component_reused_pid'],
  'actual_code_scope':'_se_article_proof单段fallback缺same_component；直接父句两路径的目标号/同SHA不等于同组件关系。'},
 {'status':'actual_failure_demonstrated','topic':'boundary pointer does not prove no unprovided members between last and next',
  'demonstrating_cases':['article_remote_next_boundary_unprovided_condition'],
  'actual_code_scope':'_se_group_proof对nextid文本身份核验，但未证明其与last为原件实际紧邻边界。'},
 {'status':'actual_failure_demonstrated','topic':'current effect anaphor cannot consume a sibling safety definition',
  'demonstrating_cases':['effect_indicator_not_safety_sibling'],
  'actual_code_scope':'_se_bounded_content宽泛指标antecedent+同时S/E消费者扩大当前确指对象。'},
 {'status':'finite_controls_passed_not_global_proof','topic':'explicit clause, missing middle/last and literal duplicate roles',
  'cases':['explicit_clause2_only_safety','explicit_clause2_missing_next_boundary','explicit_clause2_next_other_component',
           'article_missing_middle_member','article_missing_last_member','boundary_literal_duplicated_elsewhere','two_member_positions_identical_literal'],
  'actual_code_scope':'显式款次只消费本款，boundary_quote不产生标签；两个同字面成员位置保留。'},
 {'status':'static_risk_not_actual_failure_in_this_execution','topic':'preceding dose-model and price-method bridges lack explicit positional closure',
  'code_locations':[{'file':'relations.py','line':1714},{'file':'relations.py','line':1742}],
  'actual_code_scope':'剂量模型分支只kind=preceding_paragraph且按词型，未核同源/组件；价格方法分支核同源但无组件/真实紧邻段坐标约束。',
  'executed_control_note':'remote_preceding_price_method_other_component实际返回0；其原句未满足代码的“开展测算评估”窄词型，不能由这一通过声称远段接口已被阻断。未再改例或补执行。'},
 {'status':'static_guard_observed_and_existing_tests_passed','topic':'consumer permissions remain intersection and source available is not automatic classification',
  'actual_code_scope':'judge对affected_dimensions与only_IF_consumers取交集；SE消费者拒绝only_IF及未SE_scope_verified的标准/清单。不能用关系存在代替范围有效性。'}]
write('static-scope-review.json',static)

summary=execution['summary']
report={'status':'independent_SEEc_v2_finite_review_complete_errors_preserved_not_formal_validation',
        'candidate_algorithm_sha256':preseal['algorithm_sha256'],
        'algorithm_manifest_file_binding':verification['algorithm_manifest_file_binding'],
        'candidate_seal':verification['candidate_seal_binding'],'delivery_seal':verification['delivery_seal_binding'],
        'manual':load(OUT/'manual-basis-quotes.json')['binding'],
        'controls_preseal':bind(OUT/'pre-execution-seal.json'),'execution_summary':summary,
        'all43_inputs_binding_file':bind(OUT/'executed43-input-bindings.json'),
        'failure_records':bind(OUT/'all-failures-full-inputs-and-paths.json'),
        'owner_four_closures':bind(OUT/'owner-four-closure-reception.json'),
        'conclusion':'旧20其中1项旧完整条文控制缺机器可消费闭合，原预期保留而实际NULL；另3旧缺闭合复核也NULL。新增20中5项/9维实际范围不符，与缺材分列；v2封存候选不修改，交ROOT未来联合版本修通用范围。',
        'actual_reading_scope':{'old20':'固定原句与全部供给语境，旧预期和源bytes未改；这些20已是owner开发暴露，不称独立留出验证。',
                                'new20':'本审计以手册先定预期、来源结构与合成文字后一次执行；均非实际政策记录/人类首判。',
                                'owner_four':'3合成条文原上下文；A450当前完整命题及原包9成员/来源声明。PDF仅核真实SHA/bytes，不称逐页读完。',
                                'code':'全5模块byte绑定与快照；SE新增谓词/关系/闭合函数、共享_units/_add/judge及请求路由有限代码审查。',
                                'owner_results':'交付74成员只机械hash读回；只提取被指明的3旧控制输入与历史预期，未采用owner整套期望表生成新语义目标。'},
        'readback_only_adapter_units_N':21,
        'scope_limits':{'main_LLM_partial_or_owner800_replay_labels_read':False,
                        'full77_or800_replay':False,'source_projection_or_manual_changed':False,
                        'candidate_modified':False,'new_Codex_CLI':False,'human_reference_created':False,
                        'expected_or_NULL_filled_after_execution':False,'formal_accuracy_or_release_acceptance':False},
        'exposure':'本次控制及失败将交ROOT/owner作开发暴露，不能作为后续修复的独立验收分母。',
        'future_scope':'可在ROOT新联合代码另存封存后设计少量新的近邻结构/语义对照；本次不根据未来实现先设例，不改本批预期，不重跑旧全量。'}
write('report.json',report)
write('final-readback.json',{'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'all_presealed_inputs_and_owner_bound_files_unchanged':True,
    'owner_delivery_N':74,'original_audit_preserved':True,
    'actual_judge_attempts':43,'judge_rerun_in_finalizer':False,
    'pure_SourcePacket_reconstructed_readback_N':21,'input43_exact_pointer_and_canonical_bindings':True,
    'A450_PDF_bindings_only':pdf_bindings,
    'all_failure_N':6,'new_semantic_scope_failure_N':5,'old_fixture_missing_closure_N':1,
    'exception_N':0,'evidence_validation_success_N':43,'literal_positive_quote_check_N':50})
text='''S/E/Ec v2独立有限审查完成，候选及旧20预期保持不变。

五模块算法聚合SHA88eead7588d2e8353a4de6768cedd42a95ba4cb75c3dc819f6dd05aec9f5ac32；algorithm-bindings.json文件自身SHA4f0adb314ffc0d554f307a24a482bf2ed0df46aa9aa4c6dc7f5513ff681db44b。candidate seal a630f5...，delivery seal39a876...。交付74成员及旧审计所有成员真实SHA/bytes匹配，五模块精确快照随本审计封存，手册保持5ea7。

先固定新20和闭合复核期望，再有限43输入各一次执行：旧20符合19，1项3维不符（原完整条文没有真实闭合，原预期1/1/1保留，实际NULL）；新20符合15，5项9维不符；owner另外3缺闭合复核均NULL。无异常，43次原引文验证成功，50次阳性语境精确字面/引用位置检查通过。这是控制计数，不是正式准确率或人类金标准。

五类实际误接：远段被当真实末界（缺材期望NULL，实际1/1/1）；单段援引借跨组件下一条闭合（缺材期望NULL，实际1/0/0）；安全父句跨组件重用段号（S0→1）；当前疗效指标借同段兄弟安全指标（S0→1）；支付父句跨组件（Ec0→1，旧generic和新增SE两路都有）。实际引文完全匹配并不能证明当前适用关系正确。

四处旧闭合差异与上述误接分开：A450续约9有序成员缺可消费容器/末界；两旧selfcheck合成条文和原独审完整条文仅有编号/句号，无实际首末/下一段证据。A450原PDF真实存在且155649B/SHA32846e...匹配；缺的是当前机器文字/结构接口闭合。本审计只核PDF绑定，未渲染逐页读图，不声称政策原件不存在或人类无法核读。旧期望和NULL均原样保存，不硬调0/1。

executed43-input-bindings.json给全部43输入的源文件SHA、JSON指针、原输入与纯适配语义单元canonical SHA；all-failures-full-inputs-and-paths.json保存6项不符的当前原文、完整供给上下文、原预期、输出、实际误接trace及手册行号。owner-four-closure-reception.json复核4旧缺闭合。new20-fixed-before-execution.json/legacy20-controls.json/pre-execution-seal.json保留执行前证据；execution-results.json和jsonl保留所有输出/NULL；literal-quote-validation.json保留精确引文；static-scope-review.json区分实际失败、通过控制与未执行静态风险。

明确款次仅消费本款、缺中段/末项、边界/同字面成员重复、纯结构、AE内容/AAE编码等有限对照通过，不是普遍正确性证明。preceding剂量模型与价格方法仍有未核真实位置的静态风险；本次远段价格控制因未满足窄词型返回0，不用它声称该接口已阻断，也未改例复跑。

只读所有者候选、原资料和旧审计，未跑全77/800、未看主LLM部分结果或所有者800回放标签、未接新投影、未生成真人结果。新20属于审查后开发暴露，修复后不能作独立验收分母。ROOT可在另存新联合版本修这5类通用范围；本批不改预期、不回填NULL，后续近邻对照留待新封存入口。
'''
with (OUT/'README.txt').open('x',encoding='utf8') as stream:stream.write(text)
members=[bind(p) for p in sorted(OUT.rglob('*')) if p.is_file()]
write('output-seal.json',{'status':'sealed_independent_controls_and_scope_audit_not_formal_validation',
                       'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                       'output_members':members,'self_excluded':True,
                       'algorithm_sha256':preseal['algorithm_sha256'],
                       'manual':load(OUT/'manual-basis-quotes.json')['binding']})
for member in members:assert bind(member['path'])==member
print(json.dumps({'seal':bind(OUT/'output-seal.json'),'members_N':len(members),
                  'all43_inputs_bound':True,'all_outputs_exact':True,
                  'new_actual_scope_failure_N':5,'legacy_material_mismatch_N':1},ensure_ascii=False))
