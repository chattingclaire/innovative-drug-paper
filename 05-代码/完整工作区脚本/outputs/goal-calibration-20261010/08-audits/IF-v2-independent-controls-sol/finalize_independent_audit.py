"""Report one fixed-control execution and seal the read-only I/F v2 audit."""
from pathlib import Path
import ast
import difflib
import hashlib
import json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
V1=ROOT/'06-coding/rule-v20-semantic-audit-repair-sol'
V2=V1/'versions/v2'
MANUAL=ROOT/'03-manual/full4481-common-release-20261010-root/manual.txt'


def binding(path):
    data=Path(path).read_bytes()
    return {'path':str(path),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}


def write_new(name,data):
    with (HERE/name).open('x',encoding='utf-8') as f:
        json.dump(data,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')


def code_location(filename,token):
    raw=(V2/filename).read_text();at=raw.index(token)
    return {'path':str(V2/filename),'line':raw[:at].count('\n')+1,'literal':token}


def manual_quote(quote):
    raw=MANUAL.read_text();at=raw.index(quote)
    return {'path':str(MANUAL),'line':raw[:at].count('\n')+1,'quote':quote,
            'unicode_code_point_interval_half_open':[at,at+len(quote)],'exact_match':True}


def funcs(path):
    raw=path.read_text();lines=raw.splitlines();tree=ast.parse(raw);out={}
    def visit(nodes,prefix=''):
        for n in nodes:
            if isinstance(n,ast.FunctionDef):
                text='\n'.join(lines[n.lineno-1:n.end_lineno])
                out[prefix+n.name]={'ast_sha256':hashlib.sha256(ast.dump(n,include_attributes=False).encode()).hexdigest(),
                                    'line':n.lineno,'end_line':n.end_lineno,'body':text}
            elif isinstance(n,ast.ClassDef):visit(n.body,prefix+n.name+'.')
    visit(tree.body);return out


def main():
    pre=json.loads((HERE/'pre-execution-seal.json').read_text())
    for e in [pre['controls'],pre['authority_and_manual_basis'],pre['algorithm_bindings'],*pre['verified_modules_and_manual']]:
        a=binding(e['path'])
        if a['sha256']!=e['sha256'] or a['bytes']!=e['bytes']:raise ValueError('sealed input changed '+e['path'])
    controls=json.loads((HERE/'controls-fixed-before-execution.json').read_text())
    execution=json.loads((HERE/'execution-results.json').read_text())
    by_name={c['name']:c for c in execution['cases']}
    fixture_by_name={c['name']:c for c in controls['cases']}

    common_standard=manual_quote('当前直接要求核验、满足确指标准，或以该标准是否满足决定授予、维持、限制、终止实质待遇的一般规范，属于操作性标准援引：完整同版本标准核明后，按实际被援引内容逐维判断。')
    common_missing=manual_quote('须记录当前行动锚点、语境位置和实际补足的关系；所需片段缺失登记补材，不记0。')
    common_support=manual_quote('只使用同一版本、同一安排且与当前行动直接对应的有限片段；不把后续新版本条件倒灌此前文本，不继续沿一般“有关规定”递归查读。')
    support_three=manual_quote('I3须能填写三个证据项：支持对象是创新/实质改良研发；当前具体设置或实施一项可由该项目或对应研发群体使用的资源、技术服务、研究反馈、办理便利或申请机会；原文或合规必要语境直接连接对象与该安排。')
    denial=manual_quote('设立与撤回、肯定与否定使用同一门槛。')
    fairness_need=manual_quote('上游F是本研究明确采用的按需资源机会口径：须同时保存可辨认的目标治疗需要/缺口，以及以该缺口为条件的优先、申请、支持资源机会或其限制；不得从一般创新身份、普通申报或流程位置推出。')
    findings=[]
    def add(fid,name,category,title,reason,locations,bases, *, scope_note=''):
        c=by_name[name]
        findings.append({'finding_id':fid,'synthetic_case_name':name,'category':category,'title':title,
                         'current_text':c['current_text'],'expected':c['expected'],'observed':c['observed'],
                         'mismatches':c['mismatches'],'actual_value_preserved':True,
                         'reason':reason,'current_and_context_material':fixture_by_name[name]['synthetic_input'],
                         'relation_traces':c['relation_traces'],'material_requests':c['material_requests'],
                         'code_locations':locations,'manual_basis':bases,
                         'limited_interpretation':scope_note,'is_formal_error_rate':False})
    add('IFV2-OBS-01','named_postadmission_priority_service','supplied_same_edition_material_not_consumed',
        '当前明确具名服务与已供同版对象/缺口未接通',
        '当前直接规定对纳入同一程序的项目在临床试验关键阶段优先安排技术沟通并反馈研究方案。构造同版完整程序明确创新/改良研发对象，并将无有效治疗手段分支连接该程序的优先技术服务；这不是仅有完整对象或背景标题。实际未形成关系，I/F均0。',
        [code_location('relations.py','def _bounded_IF_semantic_support(self):'),
         code_location('relations.py',"operation = re.search(r'(?:可|可以|允许|可申请|自愿申报")],
        [support_three,common_support],scope_note='仅这份明确当前行动—同一程序—同阶段服务构造支持正判；不由对象范围对所有同名背景句或所有纳入品种推F。实际病例材料没有在本次执行。')
    add('IFV2-OBS-02','withdrawal_missing_same_edition_scope','required_substantive_standard_missing_decided_zero',
        '实质资格决定具体支持撤回却未登记标准缺失',
        '当前规范以不能满足具名程序条件为根据，终止该项目的优先研究方案反馈服务；实际支持后果已经表达，关键所指对象/资格标准未交付。固定预期是未定，候选无请求而I/F为0。缺失必要标准与仅名称、名单身份或历史状态应分开。',
        [code_location('relations.py','def _bounded_IF_missing_dependency(self):')],
        [common_standard,common_missing],scope_note='NULL预期基于当前具体条件—支持后果确指的关键实质标准缺失；不主张任何具名撤回句、标题缺失或可能有背景时都NULL。I/F未知内容仍待ROOT核查本完整命题与必要范围。')
    add('IFV2-OBS-03','negative_support_action_direct','current_specific_arrangement_missed',
        '直接限制缺口对应优先研发反馈机会漏F',
        '当前已写明无有效治疗手段疾病的创新研发对象及不再提供优先研究方案反馈机会，所需对象—缺口—限制后果自足。I=1已由I3成立，F0仍遗漏当前按需优先机会的限制议题；不把它解释成患者已失去全部治疗。',
        [code_location('dimensions.py','def _fairness(acc: Accumulator'),
         code_location('dimensions.py','opportunity = re.search(OPPORTUNITY, combined)')],
        [fairness_need,denial])
    add('IFV2-OBS-04','work_organization_innovation','over_inclusion_non_drug_novelty',
        '工作排班新颖被误用为药物技术新颖',
        '新颖修饰会议值班流程，创新修饰办公室排班组织方式；药品审评对象名不使该新颖属性属于药品技术。实际I1_technical_novelty阳性，缺属性与正确对象的关系。该路径为v2保留的既有逻辑，不归因于本轮新增支持关系。',
        [code_location('dimensions.py','if re.search(r"新作用机制|新靶点|新化合物|新分子实体|原创')],
        [manual_quote('仅新获批/上市/申报、泛称创新药作为管理或支付对象而没有具体创新条件的使用、一般管理创新')])
    add('IFV2-OBS-05','first_no_approved_option_opportunity','current_direct_parent_opportunity_missed',
        '首项获批治疗选项缺口与直接父申请机会漏F',
        '当前首项没有境内获批用于该疾病的药物，直接完整父句允许申请优先审评支持。关系bounded_IF_first_operative_member已形成，却F0；不同疾病/适应症表述没有消除治疗选项缺口，不能借兄弟创新条件加I。',
        [code_location('relations.py','def _bounded_IF_first_member(self):'),
         code_location('dimensions.py','GAPS =')],
        [fairness_need,manual_quote('必要语境可以补足明确承接的支持对象或条件')])
    add('IFV2-OBS-06','foreign_single_unlisted_not_no_options','manual_boundary_pending_actual_null',
        '单品未上市控制仍返回手册边界NULL',
        '固定预期0是依据本例明确境内已有其他获批治疗选项、供药充足，不能由单品未上市推无获批对应治疗选项。实际F=null、basis=manual_relation_boundary，未误赋1也非材料缺失。构造末句“本条未按治疗保障缺口分配机会”究竟否定整个推断关系，还是仍表达按需机会安排的否定议题，需结合手册L9/L29/L30及F限制/终止规则另解释；临床急需/罕见病与差别机会是否另有独立按需依据也待核。预期0和实际NULL均保留，不据此硬调规则0。',
        [code_location('dimensions.py',"acc.boundary(\"F\", unit, \"单品种未上市与按需优先机会\"")],
        [manual_quote('无有效防治手段、境内未获批目标适应症选项、现实供药不足分别留痕；三者不互相推定。'),
         manual_quote('急需、未上市或短缺词本身不足，须原文表达保障缺口与按需获取安排的关系。')],
        scope_note='这是预期与实际的未定边界差异，不算已观察到0/1语义误判，更不把AI预期当真人裁定。')
    add('IFV2-OBS-07','complete_same_edition_qualification','supplied_same_edition_material_consumer_shape_not_connected',
        '完整同版资格文字已供但结构种子消费者未接通',
        '构造单一同源全文含完整1/2资格成员、下一工作章节边界和当前核验—终止命题，并另供资格source_paragraph；可见文字已表达创新技术与创新研发用途而没有公平缺口。当前输入未供structural_relation.related_context_ids，_standards只把有关结构种子标明的source_paragraph列为candidate，因而报同版标准缺失并I/F均null。应区分已供文字但消费者形状不接通与实际原文没有交付。',
        [code_location('relations.py','def _standards(self):'),
         code_location('relations.py',"if shared and c['context_id'] in related")],
        [common_standard,common_support],scope_note='这是参数化合成结构控制，非实际800包验收。完整文本本身不准许跨程序继承；本例当前明确核验的正是同一完整组。保持真实null输出，不以AI补造结构回填。')

    risks=[
        {'risk_id':'IFV2-STATIC-01','title':'首项前置角色不足以证明真实相邻父句',
         'reason':'新_first_member只以（一）、唯一preceding_paragraph、同SHA、same_component和父句冒号判定直接父句，没有核对原始字节/字符/行区间、序号或实际邻接。当component缺失时same_component仍允许通过。上游角色可准确信息时有限，但对误标的同版远段或另清单第一项仍有越界风险。',
         'locations':[code_location('relations.py','def _bounded_IF_first_member(self):'),code_location('relations.py','def same_component(left, right):')],
         'executed_scope_note':'两个真正第一项及一个第二项控制已执行；并未另构造远段误标控制。'},
        {'risk_id':'IFV2-STATIC-02','title':'权利操作借同SHA任意定义存在兄弟条款风险',
         'reason':'新_right_operation扩大当前操作词和数据指代后，定义仅要求同SHA、source_resource_text/source_paragraph、同终端权利名、创新/改良和保护后果词；没有同条、当前主体、基础/例外分支或具体适用对象闭合。完整表行基础/例外控制通过与仿制药编号排除通过，不证明任意别的当前权利操作都可借该定义。',
         'locations':[code_location('relations.py','def _bounded_IF_right_operation(self):'),code_location('relations.py',"definitions.append(self._quote(c,'当前同一权利的创新/改良资格与实质权利后果定义'))")],
         'executed_scope_note':'此条列静态潜在范围风险，没有额外执行假权利/真人结果。'},
        {'risk_id':'IFV2-STATIC-03','title':'整程序可见角色不等于当前服务适用链',
         'reason':'新支持路径可按完整名称的>=6字符后缀选源程序，再调用_closed_primary_programme(require_current=False)；收集的objects、need、services、stages分别来自整个有界程序。原印程序标题边界限制了原文范围，但角色共现不能独立证明当前对象适用同阶段同一服务。need还从任意程序行收集，不局限实际资格分支；时限审评过滤只覆盖特定审评时限为数字日句式。',
         'locations':[code_location('relations.py',"closed = self._closed_primary_programme(name, require_current=False)"),
                      code_location('relations.py',"if objects and services and stages:"),
                      code_location('relations.py',"timed_review=bool(re.search(r'审评时限为")],
         'executed_scope_note':'本次有直接服务链、仅历史身份和下一程序三个范围控制，不能泛称所有同名/同程序句已受控。'},
        {'risk_id':'IFV2-STATIC-04','title':'个性化咨询补全仍需精确同一技术文档指代',
         'reason':'新增_individual_consultation已要求同SHA、同unit_id及sequence_index相邻，强于任意同段共现；但用ASCII别名在整容器出现来连接文档定义，引用整个parent_paragraph。混合父段另有别名或其他对象时，仍需确认当前未阐明问题实际指向同一创新临床试验文档。不能把任何一般指南未解决问题转成I3。',
         'locations':[code_location('relations.py','def _bounded_IF_individual_consultation(self):')],
         'executed_scope_note':'这一路未在本次20例中独立激活，仅静态审查，不算失败也不背书全部情形。'}]
    for risk in risks:risk['evidence_level']='read_only_code_inference_no_added_execution'
    report={'status':'sealed_v2_independent_semantic_review_with_failures_and_boundary',
            'summary':execution['summary'],'executed_findings':findings,'unexecuted_scope_risks':risks,
            'categories':{'current_specific_arrangement_or_direct_parent_missed':['negative_support_action_direct','first_no_approved_option_opportunity'],
                          'same_edition_material_supplied_not_connected':['named_postadmission_priority_service','complete_same_edition_qualification'],
                          'necessary_substantive_standard_missing':['withdrawal_missing_same_edition_scope'],
                          'wrong_novelty_object':['work_organization_innovation'],
                          'manual_boundary_with_actual_null':['foreign_single_unlisted_not_no_options']},
            'guards_observed':[
                '明确创新对象与直接可用研究方案反馈控制I1/F0；纯沟通形式和一般安全义务均I/F0。',
                '单纯历史身份没有倒借同程序支持；药物机制新颖性否定证据仍I1。',
                '第一项疾病严重程度不继承兄弟创新或缺口；第一项创新技术属性I1，第二项纯页码核对I/F0。',
                '明确无获批适应症选项与当前优先机会自足控制F1。',
                '整表行创新药基础保护待遇与儿科例外分别保留，I1/F0；仿制药编号形式控制没有借其他创新权利定义。',
                '缺同版资格控制真实返回null；下一含内部CJK空格的程序常规上市后义务没有继承前程序I/F。',
                'v2 judge将affected_dimensions与only_IF_consumers取交集；这是静态已核代码变化，不从样例通过泛称全输入兼容。'],
            'conclusion':'v2在有限独立对照中仍有对象误纳入、明确安排遗漏、已供同版材料消费者闭合失败、必要标准缺失处理和一个真实NULL边界差异。保持原代码和所有值；若ROOT核定后修复，应另存新版本，不以本预期作答案表，不复跑既有整批开发标签。',
            'is_human_reference':False,'is_formal_accuracy':False,'formal_records_used':0,
            'no_new_threshold_or_method':True,'owner_code_modified':False,'expected_changed_after_execution':False}
    write_new('findings.json',report)

    diffs=[]
    for filename in ['relations.py','dimensions.py']:
        old,new=funcs(V1/filename),funcs(V2/filename);changed=[]
        for symbol in sorted(old.keys()|new.keys()):
            if old.get(symbol,{}).get('ast_sha256')!=new.get(symbol,{}).get('ast_sha256'):
                changed.append({'symbol':symbol,'v1_location':{k:v for k,v in old.get(symbol,{}).items() if k!='body'},
                                'v2_location':{k:v for k,v in new.get(symbol,{}).items() if k!='body'},
                                'source_diff':'\n'.join(difflib.unified_diff(old.get(symbol,{}).get('body','').splitlines(),new.get(symbol,{}).get('body','').splitlines(),fromfile='sealed-v1',tofile='sealed-v2',lineterm=''))})
        diffs.append({'filename':filename,'v1_binding':binding(V1/filename),'v2_binding':binding(V2/filename),'changed_functions':changed})
    write_new('read-only-v1-to-v2-diff.json',{'comparison':diffs,'v1_or_v2_owner_regression_results_read':False,
                                            'v1_executed':False,'code_only':True})
    inputs=pre['verified_modules_and_manual']+[pre['algorithm_bindings'],binding(V2/'version-origin.json')]
    inputs.extend(binding(V1/f) for f in ['relations.py','dimensions.py'])
    authority=json.loads((HERE/'authority-and-manual-basis.json').read_text())
    inputs.extend(x['source'] for x in authority['authority_quotes'])
    delivery=V1/'delivery/delivery-seal.json'
    delivery_binding=binding(delivery)
    if delivery_binding['sha256']!='600956cfcc6bfb90a9da9c9aa54cf008e9b6633d5c4e5ce811793590cbd29a29':raise ValueError('owner delivery seal changed')
    inputs.append(delivery_binding)
    unique={x['path']:x for x in inputs}
    write_new('audited-input-bindings.json',{'inputs':list(unique.values()),
              'v2_five_modules_and_manual_verified_before_and_after':True,
              'owner_delivery_seal_sha_verified_only':'member list metadata seal SHA; owner result files not opened',
              'manual_sha256':pre['verified_modules_and_manual'][-1]['sha256'],
              'source_basis_ranges_are_not_formal_control_inputs':True})
    write_new('execution-and-readback-scope.json',{
        'actual_execution':{'twenty_controls_once':True,'pass_N':13,'fail_N':7,'dimension_mismatch_N':10,
                            'exception_N':0,'evidence_validation_pass_N':20,'all_null_and_failures_preserved':True},
        'actual_reading':{'v2_new_functions_and_v1_to_v2_code_diffs':'all changed function bodies and relevant full consumer methods read; whole files mechanically AST parsed and SHA checked',
                          'authority_originals':'NMPA three preserved UTF8 originals: exact continuous ranges in authority-and-manual-basis.json, SHA wholebytes; not semantic reading of entire files',
                          'manual':'whole shared threshold/finite relationship scope and I/F sections read',
                          'control_materials':'20 complete synthetic current records plus supplied contexts read/constructed before one execution'},
        'scope_not_read_or_run':['owner75 regressions result labels','owner800/77 replay predictions','mainLLM full or partial labels','neutral projection runtime','Codex CLI'],
        'static_not_executed_risks':['far preceding paragraph mislabeled first-parent','unrelated same-SHA right definition','all programme suffix or role combinations','individual consultation alias ambiguity'],
        'harness_notes':['One preliminary read-only AST discovery used relative Path dot for both directories and returned empty difference. It was discarded; corrected absolute v1/v2 comparison is saved. No conclusion or control result depended on that discovery.',
                         'One manual quote spelling was corrected before fixing inputs or executing; all stored basis quotes exactly match frozen manual. No semantic expectation changed.'],
        'preserved':['sealed v1/v2 code and version bindings','manual and frozen releases','raw source material','all prior results and statistics interfaces'],
        'expected_controls_are_new_development_exposure':True,'human_or_formal_results_created':False})
    readme='''# I/F v2 独立审查

20 个预先固定的独立合成对照仅执行一次：13 项符合预期，7 项不符，涉及 10 个维度差异；无技术异常，20 项原文/引文结构校验通过。预期、完整构造输入、实际五维决策、关系、请求、NULL和失败均原样保存，没有补0/1或改代码。

`findings.json` 分列当前具体支持/直接父机会遗漏、已供同版文字但消费者未接通、关键实质标准确指缺失被判0、组织工作新颖误I，以及单品未上市控制实际F=NULL的手册边界。完整对象不是当前适用关系；具名撤回也不自动要求NULL，报告写明每例当前行动锚点、实际链条及原手册依据。单品未上市NULL没有冒充0/1误判。

4项静态范围风险另列未执行推断：首项前置角色缺真实相邻坐标核验；权利操作借同SHA任意兄弟定义；整程序对象/服务/阶段共现不足以核定当前适用链；个性化咨询需精确同文档指代。这些不是额外运行失败，也不由有限通过例泛称全部安全。

输入见 `controls-fixed-before-execution.json`、`authority-and-manual-basis.json` 和运行前 `pre-execution-seal.json`；原始输出见 `execution-results.json` / `.jsonl`；版本差异与实际SHA见 `read-only-v1-to-v2-diff.json`、`audited-input-bindings.json`。读取范围见 `execution-and-readback-scope.json`。

v2 relations SHA 13f5eb351d39a8b8cf12bff8e6a4976570baf3719a4be85d216933f406e02bc2；dimensions SHA b4afd654f2b3be8730a1e91ae41d88de01b82fd8a283c65014a6c781d0fe2cd4。另三模块和共同手册5ea7运行前后不变。真实800/77包和主LLM部分标签未读，未调用投影或整批runner，未启动新Codex CLI。

13/20是本组开发对照的符合数，不是正式准确率，合成预期不是真人参照。ROOT可据完整命题核验后决定另存未来候选版本；本报告不反写旧冻结输入或标签。
'''
    with (HERE/'README.md').open('x',encoding='utf-8') as f:f.write(readme)
    members=[binding(p) for p in sorted(HERE.iterdir()) if p.is_file() and p.name!='output-seal.json']
    write_new('output-seal.json',{'status':'sealed_read_only_IF_v2_independent_controls_audit',
               'output_members':members,'self_excluded':True,'algorithm_bindings':pre['algorithm_bindings'],
               'manual_sha256':pre['verified_modules_and_manual'][-1]['sha256'],
               'synthetic_case_N':20,'pass_N':13,'fail_N':7,'dimension_mismatch_N':10,
               'formal_or_human_results_created':False,'v2_code_modified':False})
    print(json.dumps({'root':str(HERE),'output_member_N':len(members),'seal':binding(HERE/'output-seal.json')},ensure_ascii=False))


if __name__=='__main__':main()
