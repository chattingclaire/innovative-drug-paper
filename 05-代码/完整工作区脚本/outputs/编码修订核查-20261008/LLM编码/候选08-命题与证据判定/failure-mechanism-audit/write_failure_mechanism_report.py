"""Seal a read-only evidence report; never calls CLI/model or edits frozen sources."""
import datetime
import hashlib
import json
from pathlib import Path

P=Path('/PROJECT_ROOT')
H=P/'outputs/编码修订核查-20261008/LLM编码/候选08-命题与证据判定'
O=H/'failure-mechanism-audit'
R=H/'runtime-unchanged-v2'
M=P/'outputs/coding-revision-20261007-r3'

def binding(p):
    p=Path(p); b=p.read_bytes()
    return {'path':str(p.resolve()),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}

def anchor(p,first,last,claim):
    return {'file':str(p),'line_start':first,'line_end':last,'claim':claim}

def main():
    freeze=json.loads((H/'design_freeze.json').read_text())
    frozen_bindings=freeze['files']+freeze['source_bindings']
    checks=[{'path':x['path'],'expected_sha256':x['sha256'],'actual_sha256':binding(x['path'])['sha256']} for x in frozen_bindings]
    assert all(x['actual_sha256']==x['expected_sha256'] for x in checks)
    selected_path=O/'prompt-manual-independent-review/prompt_manual_selected8_mechanism_review.json'
    selected=json.loads(selected_path.read_text())
    trace=json.loads((O/'input_request_execution_trace.json').read_text())
    metadata=json.loads((O/'input_metadata_and_serialization_order.json').read_text())
    cross=json.loads((O/'following_role_certificate_cross_tab.json').read_text())
    code_meta=json.loads((O/'source_code_redaction_metadata.json').read_text())
    constructor_meta=json.loads((O/'synthetic_constructor_code_projection_metadata.json').read_text())
    assert metadata['full4924_context_key_frequencies']['following_material_role_counts']=={
      'complete_actual_enumeration':102,'local_navigation_preview':27,'NO_TYPED_STATUS':19}
    assert sum(x['n'] for x in cross['rows'])==148
    byid={x['id']:x for x in selected['cases']}
    assert len(byid)==8
    for t in trace['traces']:
        assert t['actual_row']==byid[t['id']]['actual_row']
        for k in ['source_input_exactly_equals_frozen_snapshot','packet_is_exact_ordered_source_slice',
          'attempt_packet_equals_batch_packet','full_local_request_exact_assembly',
          'full_prompt_prefix_preserved','execution_layer_exclusion_present','raw_agent_aggregate_row_exact_match']:
            assert t[k] is True
    prompt=H/'candidate08_prompt_PROPOSED.txt'
    assert binding(prompt)['sha256']=='d79c097443fa249051c5264da1ff532ddf7d984225ac3e776807de95f7f21803'
    v13=M/'protocol/完整五维手册-v1.3.md';v14=M/'protocol/共用操作说明-v1.4.md'
    prompt_text=prompt.read_text()
    assert v13.read_text().strip() in prompt_text
    assert v14.read_text().split('## 版本与验证纪律')[0].strip() in prompt_text
    gate=H/'phase-gates/inherited-controls.json'
    gate_obj=json.loads(gate.read_text())
    assert gate_obj['status']=='FAIL_CONFIRMED_SEMANTIC_ERROR'
    assert gate_obj['root_reviewed_and_approved_to_continue'] is False
    evidence=[
      anchor(prompt,3,7,'完整读取与按当前命题/必要语义关系使用上下文同时成立，非自动继承。'),
      anchor(prompt,15,17,'理由和双来源引文须说明语义关系；resolved_context_issue仅用于实际解决的问题。'),
      anchor(v13,9,17,'实质讨论定义及上下文边界；不要求一律有义务动词。'),
      anchor(v13,65,67,'真正内容/证据要求计入；仅格式/字段名称等不自动计入。'),
      anchor(v13,144,148,'冒号非充分条件；给定材料的必要关系与缺料边界。'),
      anchor(v14,5,9,'当前对象/行为/限定条件；不得复制背景维度；全0有效。'),
      anchor(R/'run_production_v32.py',59,64,'sort_keys=True仅用于事件/raw规范化比较，不生成模型请求。'),
      anchor(R/'run_production_v32.py',67,85,'禁止参考字段；完整request通过stdin交CLI，未显式分割system/user角色。'),
      anchor(R/'run_production_v32.py',120,150,'读入不改context；顺序切批；请求json.dumps未sort_keys/未切片字符串。'),
      anchor(R/'run_production_v32.py',153,169,'首个技术有效尝试；聚合raw原行；不按标签或分数选择。'),
      anchor(R/'validate_binary_output.py',1,12,'validator明确不证明上下文关系或语义正确。'),
      anchor(R/'validate_binary_output.py',27,40,'递归提取context可引文字段；没有语义继承运算。'),
      anchor(R/'validate_binary_output.py',103,144,'核binary、非空理由、逐字引文/当前引文存在，不核引文是否蕴含该维。'),
      anchor(R/'output_schema_codex_compatible.json',30,77,'每维0/1均允许，没有要求至少一个1或五维同取值。'),
      anchor(P/'outputs/final-three-department-20261007/llm-v29/prepare_inputs_v29.py',34,70,'初始来源contexts复制；冒号同组件后4项预览；context_usage明确不继承标签。'),
      anchor(M/'complete_shared_material_v10.py',50,80,'来源认证完整段落区间补料，写structured_following及嵌套证书，usage禁止全维复制。'),
      anchor(M/'complete_shared_material_v11.py',21,63,'清除已核边界过冲；完整列举与导航预览同字段但不同role；19既有v10完整列不重写。'),
      anchor(M/'complete_shared_material_v14.py',28,77,'父作用域/附件边界来源补料；断言当前text/ID/顺序不变、两方法context相同。'),
      anchor(M/'rules-v36.2-development/runtime/source_context_adapter_v34.py',99,140,'规则侧完整来源证书只用于completeness/conditions，不允许复制标签。'),
      anchor(M/'rules-v36.2-development/runtime/source_context_adapter_v34.py',294,319,'规则侧把裸structured_following标成navigation_preview；此adapter不在实际LLM调用链。'),
      anchor(P/'outputs/coding-revision-20261008-r4/llm-candidate05-preparation/prepare_candidate05.py',76,81,'synthetic input只写id/text/contexts，期待留在另一对象。'),
      anchor(P/'outputs/coding-revision-20261008-r4/llm-candidate05-preparation/prepare_candidate05.py',117,122,'015/016从预声明时就是同字段的抽象定义/明确引导对照。'),
      anchor(P/'outputs/coding-revision-20261008-r4/llm-candidate05-preparation/prepare_candidate05.py',139,148,'固定顺序由ID哈希决定，不依标签；runner承继此顺序。'),
    ]
    verified=[
      {'id':'V1','finding':'015该次输出错误建立当前句—后项关系，五维均为假阳性，resolved_context_issue也声称未给定的明确补足。',
       'evidence':'原句是泛化过程定义；actual S理由改写为“规定”，全部维理由用“明确承接”。逐字引文存在但并不建立该关系。',
       'status':'VERIFIED_OUTPUT_BEHAVIOR','not_claimed':'理由是可审计的输出，不是模型内部因果记录。'},
      {'id':'V2','finding':'已核本地组装、顺序、输入对象、完整提示、raw/event/final绑定，无本地context改写/合并标签/字符串截断或ID错配。',
       'evidence':'两行source/frozen/packet/attempt/request逐层匹配；prompt d79c全文在前；唯一完成agent JSON=raw；首个attempt且零工具。',
       'status':'VERIFIED_LOCAL_PATH','not_claimed':'没有provider完整prompt回显，不能证明隐藏服务端未处理输入或模型真正遵从/逐字阅读。'},
      {'id':'V3','finding':'实际请求没有sort_keys；text与contexts的插入次序可成为真实表示因素。',
       'evidence':'L150默认json.dumps；两行实际键序id→text→contexts；唯一sort_keys在L59事件比较。',
       'status':'VERIFIED_SERIALIZATION','not_claimed':'当前未测试交换顺序的语义效果。'},
      {'id':'V4','finding':'015与016不在同一请求，不能解释成016紧邻导致的直接同请求泄漏。',
       'evidence':'015 source17=batch1位17；016 source46=batch2位21；固定ID哈希排序。',
       'status':'VERIFIED_BATCH_MEMBERSHIP','not_claimed':'其他同批记录/顺序/批长影响未隔离；这不是精确单因素配对。'},
      {'id':'V5','finding':'structured_following_units是补料/导航容器，不能凭字段名认定当前命题继承。全输入已经包含不同角色与来源元数据。',
       'evidence':'4924均有该key，148非空：102 v11完整列+27导航+19仅缺v11 role但均有v27证书；来源认证只证明材料出处/边界。',
       'status':'VERIFIED_INTERFACE_HETEROGENEITY','not_claimed':'不是148条都存在语义错误，不是19条缺料，也未证明字段名导致015错误。'},
      {'id':'V6','finding':'技术schema/validator允许全0，也没有计算全1；当前技术通过与语义失败可以同时成立。',
       'evidence':'输出的generic unit quote+context quote满足逐字和存在门禁；门禁没有蕴含关系检查，文档明确其限度。',
       'status':'VERIFIED_TECHNICAL_GATE_LIMIT','not_claimed':'不能把自动语义判别器伪装成无需验证的技术修复。'},
      {'id':'V7','finding':'选定8例未发现同一完整命题被同时要求0和1的实质定义冲突。',
       'evidence':'明确清单016、C06-04-B、C06-08-B、C08-06-A支持必要语境；存档/独立邻段/未来文件负例正常。',
       'status':'NO_CONTRADICTION_FOUND_IN_REVIEWED_SCOPE','not_claimed':'不证明手册无任何歧义；全0不能简单等同定义句/没有义务动词。'},
    ]
    hypotheses=[
      {'factor':'字段名称与生产形状','observed_basis':'synthetic015裸text-only structured_following，无生产context_usage/证书/role；full4924都有context_usage并有异构角色。',
       'unresolved':'可能把structured当作已证明的语义连接；同字段正负结果不足以证明；合成与生产形状不完全一致限制外推。',
       'minimum_diagnostic_if_separately_authorized':'保持原句、全部context文本、提示、模型和批次不变，只中性改名并机械证明实际request除key外不变；生产role/usage加入是另一因素，分开。'},
      {'factor':'text/contexts字段顺序','observed_basis':'默认序列化确实保留源插入序；当前两行均text在contexts前。',
       'unresolved':'未有位置因果证据。',
       'minimum_diagnostic_if_separately_authorized':'同一个完整对象只改变插入顺序；核request字节/JSON键序，不能仅用dict==。不删材料。'},
      {'factor':'同批组成/行位置','observed_basis':'015/016处不同请求；各25行且源顺序由ID哈希。',
       'unresolved':'批次、行位置与文本同时变化，不能归因单一因素。',
       'minimum_diagnostic_if_separately_authorized':'按预注册单一变量改变批次或行位置，保留所有首次输出，不投票/挑优/语义重试。'},
      {'factor':'长提示或隐藏执行层','observed_basis':'完整提示17060字符/36714bytes；执行层2132字符。015请求40303bytes/input_tokens25166，016 41260bytes/input_tokens25382。CLI事件不披露后端revision。',
       'unresolved':'本地无截断；stderr只有rollout状态库fallback与skills图标路径警告，无截断指示；不能断言长提示或服务端截断导致错误。',
       'minimum_diagnostic_if_separately_authorized':'先保存实际请求与可见token/执行元数据；长度/角色变化必须另作单因素，不把本次关系错误自动归因长提示。'},
      {'factor':'概念说明被泛化为内容承接','observed_basis':'015实际理由把“是…过程”换成“规定/明确承接”；prompt要求当前命题仍被违反。',
       'unresolved':'这是输出层误读类型；不是内部机制已证。manual L148离开缺料前提宽读风险与本次过继承方向也不同。',
       'minimum_diagnostic_if_separately_authorized':'先做普通语言的当前谓词/所用语境作用审查；不得把所有定义句或非义务句一律0。'},
    ]
    remedies=[
      {'priority':1,'option':'先修输入契约的可解释呈现并做表示隔离，不继续堆加案例指令。',
       'preserves':'保持全部必要父谓词、援引条件、指代、表列及真实清单；原4924/240字节和旧预测留存。',
       'bounded_change_if_later_authorized':'从既有来源证书/role机械整理导航预览与已核完整材料的展示，字段名称不授予语义继承。无typed role的19条须保留其既有v27证书，不能当作缺料丢弃。',
       'acceptance':'先确认材料文本/顺序范围、source hash、边界与同版两方法来源不变，再独立判断当前句是否实际引导该内容；字段中性化/顺序因素先诊断，未观察前不声称修复。'},
      {'priority':2,'option':'把当前关系是否成立列为语义审查对象，技术逐字引文不等于维度依据。',
       'preserves':'五维定义、输出子类和现有schema不变；不在技术层手工改标签。',
       'bounded_change_if_later_authorized':'可在独立诊断记录中说明本单元谓词、context补足的对象/条件/列表、是否只是独立相邻内容；先审关系再审每维。现有理由已经要求此项，重复要求本身不证明有效。',
       'acceptance':'无关系的泛定义/独立邻句不传播，明确内容要求与保障连续/父条件等正例仍支持；若关系失败，保留失败并停止，而非规则强设0或自动用另一次结果代替。'},
      {'priority':3,'option':'有限行为诊断须以不变性和真实语义对照分别记录，决定是否值得继续。',
       'preserves':'不读取预留267/独立16私有期待；不按A/B或κ挑选；本轮不生成新候选或运行。',
       'bounded_change_if_later_authorized':'由root/state预先冻结控制、唯一改变因子及实际请求对比，保存全部结果。key/顺序纯表示扰动应保持判读；把独立邻接改为当前明确引导是语义变化，应有对应差异。删除关键context不算纯表示不变性。',
       'acceptance':'只有有据的一般修复才可进一步检验全146既有控制、当前六例/历史已修与失败项、240全部五维及字段；边界意见仍保留，不能由少数合成通过承诺全文准确或κ≥.80。'},
    ]
    dependencies=[O/'input_request_execution_trace.json',O/'input_metadata_and_serialization_order.json',
      O/'audit_input_metadata_and_order.py',O/'following_role_certificate_cross_tab.json',
      O/'source_code_redaction_metadata.json',O/'synthetic_constructor_code_projection_metadata.json',
      selected_path,selected_path.with_suffix('.md'),H/'design_freeze.json',gate,
      prompt,v13,v14,R/'run_production_v32.py',R/'validate_binary_output.py',R/'output_schema_codex_compatible.json',
      Path(constructor_meta['source']),Path(constructor_meta['projection'])]
    dependencies += [Path(x['source_path']) for x in code_meta['records']]
    dependencies += [Path(x['review_projection_path']) for x in code_meta['records']]
    unique=[];seen=set()
    for p in dependencies:
        if str(p) not in seen:unique.append(binding(p));seen.add(str(p))
    report={
      'status':'READ_ONLY_MECHANISM_AUDIT_COMPLETE_CAUSAL_EXPLANATION_NOT_IDENTIFIED',
      'created_at_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'bottom_line':'015错误是可核的当前命题/后项关系误判；未找到本地组装、截断、顺序重排、schema强制或输出覆盖缺陷。structured字段作用异构及合成/生产形状差异是可检验假设，不是已证原因。',
      'reviewer_roles':{
        'primary':'/root/llm_repair05，08提示/作者控制准备者；本轮实际做请求/输入/代码追溯与机制报告，不声称独立于方法作者。',
        'selected8_source_review':'/root/llm_repair05/content_analysis_methods，既有子代理，未编写08提示；本轮受分派检查8个已暴露合成行/手册/提示，期待可见、同项目内部来源复核，不是外部独立验证。',
        'independent16':'由root及validation_state_oct8保密审查；本轮作者未读取其文本、期待或实际语义报告正文。目录名称independent不作为独立性证据。'},
      'scope':{'selected_synthetic_rows_read':8,'selected_dimensions':40,'full4924':'只机械读取结构keys/证书存在/标点及哈希，不展示或语义阅读任何新政策原文/预测。',
        'source_code':'读取保持行号的保护投影；受保护/其他长CJK文本常量遮蔽，仅015/016已暴露原句常量放行。原来源代码未修改。',
        'new_model_calls':0,'new_CLI_invocations':0,'new_candidate_or_prompt_or_label_change':False,
        'protected_reserved_or_new_unseen_policy_semantic_read':False,'independent16_semantic_read':False},
      'current_phase_state':{'actual_completed_controls':146,'actual_logical_requests':7,'actual_attempts':7,
        'inherited_phase_gate':binding(gate),'status':'FAIL_CONFIRMED_SEMANTIC_ERROR','exposed240':'NOT_RUN','full4924':'NOT_RUN','adoption_or_row_splicing':False},
      'verified_findings':verified,'unverified_hypotheses':hypotheses,
      'selected_control_comparison':[{'id':x['id'],'input':x['full_input'],'actual_labels':x['actual_row']['labels'],
        'classification':x['classification'],'review_reason':x['reason'],'actual_row_and_input_bound_in_selected8_report':True} for x in selected['cases']],
      'comparative_limits':'8例属于当前146的已暴露机制对照，不是对146重新盲态语义验证；015/016同时改变本句、后项措辞和请求批次，并非纯格式单因素实验。',
      'request_trace':trace['traces'],
      'full4924_metadata_counts':metadata['full4924_context_key_frequencies']['counts'],
      'full4924_following_roles':metadata['full4924_context_key_frequencies']['following_material_role_counts'],
      'full4924_role_certificate_cross_tab':cross['rows'],
      'full_key_frequency_file':binding(O/'input_metadata_and_serialization_order.json'),
      'bounded_remedy_options_NOT_IMPLEMENTED':remedies,
      'explicit_non_remedies':['不删全部上下文或按冒号/字段名判继承。','不把015改期望/手改标签或拼接其他轮结果。','不放宽语义门禁以通过，不以重复投票/语义重试取代首个输出。','不把泛定义错误泛化成所有定义句或所有非义务陈述全0。','不靠κ/分布/人工参照分数选新提示，不声称合成诊断验证全文准确率。'],
      'line_evidence':evidence,'bound_sources':unique,
      'mechanical_review_corrections_preserved':[
        {'path':str(O/'mechanical-review-history/initial_metadata_count_correction_note.json'),'description':'初始计数脚本误用v11 role键名、漏嵌套v27；正确递归频次与顺序判断未受影响，误计报告/脚本已保留。'},
        {'path':str(O/'mechanical-review-history/code_projection_api_assertion_failure.json'),'description':'初始保护器API结果dict被误当hit list而断言失败；改查其明确boolean，未输出或写入未遮蔽来源。'}],
      'freeze_closure_before_and_after':{'n':len(checks),'all_matched_before':True,'all_matched_after':None,'bindings':checks},
      'decision':'保持08 FAIL，240与4924不运行。本报告只支持有界、单因素、保留必要材料的机制诊断选择，不宣布修复已有效。',
    }
    for x in checks:assert binding(x['path'])['sha256']==x['expected_sha256']
    report['freeze_closure_before_and_after']['all_matched_after']=True
    jp=O/'candidate08_failure_mechanism_audit.json'
    jp.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    def link(name,path,line=None):return f'[{name}]({path}'+(f':{line}' if line else '')+')'
    md=f'''# 候选08：当前命题与后项传播失败的只读机制核查

结论：015是已确认的语义关系误判。该次输出把抽象“是…过程”改写为“规定”，并把后列项目称为“明确承接”；五维的引文虽逐字正确，却没有证明这些内容属于当前命题。未找到本地组装、截断、ID/行顺序错配、schema强制全1或聚合覆盖标签的缺陷。字段名、材料呈现顺序与批次影响仍属假设，不能据一次理由判断内部因果。

## 审查身份与边界

主审为 `/root/llm_repair05`，也是08提示/作者控制准备者。8行提示/手册复核实际执行者是既有子代理 `/root/llm_repair05/content_analysis_methods`，它未编写08提示，但属于同项目、期待可见，不能称外部验证或真人独立验证。`independent`目录名不证明独立性。

本轮只语义阅读8个已暴露合成行，机械检查完整4924的keys/哈希/证书存在与标点；来源代码使用保持行号的保护投影。未阅读独立16的原文/期待/语义报告正文、保留267或新政策正文。新增模型/CLI调用均0，未修改冻结文件或生成09。

## 可核的执行证据

1. 015/016的source→frozen→batch packet→attempt→完整request逐层一致；d79c提示全文和第7行排除指令均在真实请求。唯一完成agent JSON与raw及最终行一致，均首次技术有效、零工具。015请求40303bytes/19195字符，016为41260bytes/19732字符；CLI记录input_tokens分别25166/25382，其计数还受未公开CLI/服务层包装影响。完整提示为36714bytes/17060字符，执行层2132字符。完整v1.3及v1.4实质段存在，v1.4验证纪律末段没有加入。
2. {link('runner',R/'run_production_v32.py',124)} L124普通解析、L129按25行切批；L149建立rows包，L150默认`json.dumps(...,ensure_ascii=False)`，**没有sort_keys或重建行字段**。实际015/016均`id→text→contexts`。L59的sort_keys只做事件/raw规范化比较。因此交换text/contexts插入顺序会改变实际request；仅检查dict相等不够。
3. 015在第1批第17位，016在第2批第21位，二者不在同一请求。{link('原控制构造代码',Path(constructor_meta['source']),117)} L117–122自预声明即为定义/明确引导对照，L141–148依ID哈希固定顺序。可排除016紧邻造成的直接同请求泄漏；尚不能排除其他批次组成/行位置效应，也不能把此对照叫精确单因素实验。
4. {link('validator',R/'validate_binary_output.py',103)} L103–144只核0/1、非空理由、连续引文及每个1有unit引文；{link('schema',R/'output_schema_codex_compatible.json',30)}允许每维0/1，没有强制正类。通用unit引文加后项context引文能通过技术门禁，不能证明语义关系。validator L8–12已明确这一限度。
5. 两请求stderr各5个警告：状态库路径fallback与skills图标路径；无截断、context window、token limit或overflow指示。未有provider完整prompt回显、实际后端revision字段或角色分段证据；本地完整性不能证明模型确实阅读/遵从，也不能绝对排除隐藏服务处理。

## 字段到底表示什么

{link('初始输入构造',P/'outputs/final-three-department-20261007/llm-v29/prepare_inputs_v29.py',49)} L49–63最初按冒号和同组件附后4项，L70明示只消解关系、不继承标签。{link('v10',M/'complete_shared_material_v10.py',50)} L50–80后来按已核来源完整区间补料；{link('v11',M/'complete_shared_material_v11.py',47)} L47–63把完整列举与导航预览写不同role。{link('v14',M/'complete_shared_material_v14.py',70)} L70–77保持单元文字/ID/顺序且两方法context一致。这些是来源/边界材料事实，不预先证明某维属于当前句。

完整4924均有`structured_following_units`键和顶层`context_usage`，前者148非空。其角色/证书交叉结果如下，证书重复不可相加：

| 非空字段的角色 | n | v11证书 | v27证书 | 当前句冒号结尾 |
|---|---:|---:|---:|---:|
| complete_actual_enumeration | 102 | 102 | 82 | 102 |
| local_navigation_preview | 27 | 0 | 0 | 27 |
| 无v11 typed status | 19 | 0 | 19 | 0 |

19条只是没有v11角色，全部有既有v27来源证书，不能说缺料。{link('规则侧adapter',M/'rules-v36.2-development/runtime/source_context_adapter_v34.py',136)} L136–140仅把证书用作完整性/条件；L310–316将裸字段视为导航预览，**此adapter不在实际LLM调用链**。LLM直接收到原contexts。

015只有裸text-only后项，无生产`context_usage`、role或证书；这是合成与生产界面不完全相同的外推限制，不是事后取消负控制的理由。其固定期待和本轮FAIL保留。

## 当前146中的已暴露机制对照

| 控制 | 当前关系 | 08实际与本次判读 |
|---|---|---|
| C05-NEW-015 | 抽象过程定义；后列项目未由本句引导 | 实际五维1；确定五维传播错误 |
| C05-NEW-016 | “应包括下列”要求当前评价内容 | 五维1，支持 |
| C06-PAIR-04-A/B | 存档编号来源 / 必须满足所引证据条件 | 全0 / S、E，支持 |
| C06-PAIR-08-A/B | 自足保障延续+独立邻段 / 评价以下清单 | F / Ec，支持 |
| C08-PAIR-06-A/B | 当前必须提交五项 / 未来另发专题文件 | 五维1 / 全0，支持 |

这8例不构成146全体重新盲态验证。正例表明必要上下文不能删除，且同一structural字段不是必然全1；它们未隔离字段、文字与批次因素。{link('提示',prompt,7)} L7和L15、{link('v1.4',v14,7)} L7及v1.3 L17/65/146–148在此范围相容，未发现同一完整命题同时必须0/1。manual L148“从后项继承全部标签”有脱离缺料前提的宽读风险，但明确清单可逐维重新判读；不能宣称该措辞已证导致015过继承。也不能把“没有义务动词”或“定义句”一律判0。

## 有界的一般选项，尚未实施

- **先诊断呈现因素。** 保持原句、全部上下文、提示、模型和批次，分别隔离字段中性化与text/contexts顺序；生产role/usage补入是另一因素。先核实际request字节/键序，不能用语义dict相等替代。不删关键上下文，不将真实语义改写算成纯格式扰动。
- **若表示证据支持，再整理输入契约。** 使用既有来源证书和role机械区分导航预览/完整材料，字段名不授予维度继承。保留父谓词、援引条件、指代、表列和真正清单；原4924/240留存，不静默改输入。证书认证来源和边界，最终仍须判当前语义关系。
- **继续审查关系，不把技术门禁当语义判别器。** 普通语言说明当前谓词和context补什么、是否另项；现有理由已经要求此项，再添一句核对不等于已修。不能由关键词/冒号自动设0，不能用后一次输出替换首个输出。只有一般修复有证据才值得后续检查全部既有控制、已确认错误和240全部五维/理由/引文/子类/quality/issues；不得承诺κ或全文准确率。

以上是可供root选择的诊断/执行选项，本轮没有新测试输入、提示修改、模型调用或候选09。08当前保持**FAIL**；已完成146控制/7逻辑/7尝试，原240与4924均**NOT_RUN**，不采用、不拼接、不放低门禁。

完整来源SHA、逐层trace、代码行证据和假设/事实分列见{link('JSON主报告',jp)}。递归key频次见{link('metadata/order',O/'input_metadata_and_serialization_order.json')}，source SHA `6829d554cf5514e49565c7c58c4ffdb6f7768f9999b0eea49f114db023c03763`。本次主报告写入前后冻结闭包81项哈希全部一致。机械审查中的初始键名误计与API断言错误均单独留痕，更正未触及冻结来源。
'''
    assert len(checks)==81
    mp=jp.with_suffix('.md');mp.write_text(md)
    seal={'status':'READ_ONLY_MECHANISM_AUDIT_SEALED','reports':[binding(jp),binding(mp)],
      'supporting_files':[binding(p) for p in sorted(O.rglob('*')) if p.is_file() and p not in [jp,mp,O/'mechanism_audit_seal.json']],
      'frozen_source_bindings_matched_before_after':len(checks),'new_model_or_CLI_calls':0,'no_new_candidate':True,
      'current_C08_status':'FAIL_CONFIRMED_SEMANTIC_ERROR','later240_and4924':'NOT_RUN'}
    sp=O/'mechanism_audit_seal.json';sp.write_text(json.dumps(seal,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'reports':[binding(jp),binding(mp)],'seal':binding(sp),'new_model_calls':0,'frozen_bindings_unchanged':len(checks)},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
