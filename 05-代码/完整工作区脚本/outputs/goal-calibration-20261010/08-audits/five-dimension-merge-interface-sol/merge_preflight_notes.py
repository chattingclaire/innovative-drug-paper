"""Static conclusions over recorded AST snapshots only."""
import json,hashlib,datetime
from pathlib import Path
HERE=Path(__file__).resolve().parent
inv=json.loads((HERE/'all-definition-and-call-inventory.json').read_text())
def binding(p):
 b=p.read_bytes();return{'path':str(p.resolve()),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def loc(branch,module,name):
 d=inv[branch][module]['effective_functions'].get(name)
 if d:return{'file':str((HERE/'source-code-observation-snapshots'/branch/(module+'.py')).resolve()),'symbol':name,'first_line':d['first_line'],'last_line':d['last_line'],'ast_sha256':d['ast_sha256']}
def obs(key,priority,symbols,finding,recommendation,status='static code observation; no classifier execution'):
 return{'id':key,'priority':priority,'locations':[loc(*s)for s in symbols],'finding':finding,'merge_recommendation':recommendation,'status':status}
findings=[
 obs('M01-consumer-dispatch','P1',[('IF_v2','dimensions','judge'),('SE_v2_observed','dimensions','judge'),('SE_v2_observed','dimensions','_se_allowed'),('IF_v2','dimensions','_generic'),('SE_v2_observed','dimensions','_generic')],
 '双方都改judge与_generic。I/F judge以affected_dimensions及only_IF_consumers取交集，并只在五维全开放时调用_generic；SE v2的judge也取交集，但先调用_generic与SE判据，依赖各内部guard。SE generic跳过三维但不含I/F创新修饰管理工作的排除。整份选择任一judge/generic会丢部分契约。',
 '合并为一个显式消费者集合，以affected_dimensions与only_IF取交集；每个谓词只在自己的消费维度获准时调用。generic内继续逐维消费过滤，保留SE三维专用判据及I/F创新修饰对象排除。不能凭调用顺序让I-only关系给F或SE贡献标签。'),
 obs('M02-init-union','P1',[('IF_v2','relations','RelationView.__init__'),('SE_v2_observed','relations','RelationView.__init__')],
 '两个初始化各添加自己的resolver组，后面才把material_requests转成stopped source_requests。一次整块覆盖会移除另一组，而且执行顺序影响去重和早期stop。',
 '在同一共同基线和来源读/用日志之后显式注册两组resolver，只注册一次；保留完整source_requests传播。不要在未解决M03/M04前仅简单连接调用并称可发布。'),
 obs('M03-relation-dedup-contract','P1',[('IF_v2','relations','RelationView._add'),('SE_v2_observed','relations','RelationView._add')],
 '_add双方均沿用基线signature=(kind,引文text+sourceSHA)，同kind同引文的不同relation_subtype、消费者、current projection、闭合证明会被先到关系去重；顺序可隐藏后续收窄或补证明关系。',
 'ROOT应审定中性的关系身份：纳入current命题/确指跨度、relation_subtype、消费者与实际语义范围；或仅在角色和消费者完全等价时合并证据。不可按文本相同就压掉另一维或按预期标签合并。'),
 obs('M04-required-request-resolution','P1',[('IF_v2','relations','RelationView._request'),('IF_v2','dimensions','Accumulator.finish'),('SE_v2_observed','relations','RelationView._se_operational_references')],
 '新resolver成功添加有界关系时没有共同接口将较早的同一确指依赖标成resolved；既有停止请求仍可能传播。相反，Accumulator先取独立positive，会在details保留未解决请求。正值与source依赖状态不可混称已闭合。',
 '只对同一确指地址、目标对象、同版绑定、完整已消费范围做request→resolved receipt，保留不相干或仍必要的stop。material_requests与source_requests须一致；不能因为任一正值而清空所有依赖，也不能因为老请求未移除而将完整已读内容称缺失。'),
 obs('M05-complete-scope-projection','P1',[('IF_v2','dimensions','_units'),('SE_v2_observed','dimensions','_units'),('SE_v2_observed','relations','RelationView._se_group_proof'),('SE_v2_observed','relations','RelationView._se_article_proof')],
 'SE v2 _units在list/cited关系中把boundary_quotes仅作闭合证明而不投影成内容，并在SE_scope_verified时保留整组context证据；I/F _units为单内容ctx。两种证据契约需要同时保留。',
 '只对带SE_scope_verified/closure_proof的SE关系使用新完整证据契约；boundary quote不成为Unit.text、不为对象/主题提供内容。I/F其他关系保持其有限原文投影。源码原件下一条/下一段只能证明终界，不能捐献兄弟S/E/Ec或I/F标签。'),
 obs('M06-programme-boundary','P1',[('IF_v2','relations','RelationView._closed_primary_programme'),('IF_v2','relations','RelationView._primary_standard_group'),('SE_v2_observed','relations','RelationView._closed_primary_programme')],
 'I/F提供PROGRAMME_HEADING_RE，承认章/节编号及CJK内部空格，且_closed_primary_programme增加require_current=True可选参数。SE两函数仍为旧基线，不能覆盖后退。',
 '保留I/F通用heading与严格源坐标/连续性/下一个章节闭合；新可选参数向后兼容SE单参数调用。require_current=False只由实际当前支持桥启用，不作为标题全文继承开关。条/款闭合则保留SE明确款次及实际终界证明；两类边界分开。'),
 obs('M07-same-paragraph-identity','P1',[('SE_v2_observed','relations','RelationView._se_bounded_content'),('SE_v2_observed','dimensions','_se_object'),('IF_v2','relations','RelationView._bounded_IF_modification_bridge')],
 '观察到的SE同段content/object路径以paragraph包含current或source_paragraph适用scope触发，未在这些路径显式检查primary source SHA和same_component。提供相同current文本的异源/异组件候选有借对象或定义风险。I/F具体改良路径另查同源。',
 '将同段关系定位到唯一primary-source current段及组件、实际句段位置和对象指代；scope须有直接适用关系。共享same_component并不足以替代source身份检查。不要用来源包可见性或正文包含同句就认同段。'),
 obs('M08-edition-proof','P1',[('SE_v2_observed','relations','RelationView._se_edition'),('IF_v2','relations','RelationView._version'),('IF_v2','relations','RelationView._edition_binding')],
 'SE edition fallback在原件title-lines中命中当前引用标题且存在日期字样即established；如果当前明确历史年不同，或同标题多版且当前未指定版，目标正文含日期不单独证明当前确指的是该版。',
 '同版证明应保留当前明确年份/法定具名引用与来源原件身份的一致校验；明确冲突时不能fallback绕过。标题只能定位确指资源，不作为阳性白名单或版次替代。未唯一绑定保留具体补材。'),
 obs('M09-parent-predicate-contract','P2',[('IF_v2','relations','RelationView._parents'),('IF_v2','relations','RelationView._bounded_IF_first_member'),('IF_v2','relations','RelationView._bounded_IF_individual_consultation'),('SE_v2_observed','relations','RelationView._se_direct_content_parents')],
 '直接parent_paragraph、立即preceding里的首项操作父句、同父unit_id的文档定义、SE target_paragraph_id内容父谓词是不同接口。不能互相放宽成任意前段；各路径取不同证明。',
 '保留关系subtype/作用维度及实际direct-parent证明。首项路径目前限定第一序号、当前整段、唯一同源preceding、冒号和实质申请谓词；SE target必须真实指向当前成员。若要统一，先提出中性source geometry契约而非扩大邻居继承。'),
 obs('M10-boundary-accumulator','P1',[('IF_v2','dimensions','Accumulator.__init__'),('IF_v2','dimensions','Accumulator.boundary'),('IF_v2','dimensions','Accumulator.finish'),('SE_v2_observed','dimensions','Accumulator.finish')],
 'I/F累加器新增已供材料但手册关系未定的boundaries，SE仍为基线累加器。全选SE会失去manual_relation_boundary与独立positive附带未定证据；全选I/F但未接SE谓词会失去三维实质修复。',
 '合并保留I/F累加器新增字段和优先级，接SE的既有add/exclude/request接口；边界与缺材分开。不要用未定项训练expected值或将semantic boundary归technical failure。'),
 obs('M11-negation-and-exception','P2',[('IF_v2','dimensions','_units'),('IF_v2','relations','sentence_spans'),('SE_v2_observed','dimensions','_safety_effect'),('IF_v2','dimensions','_innovation'),('IF_v2','dimensions','_fairness')],
 '共有matching_view/current_proposition、Unit当前分句、sentence_spans及evidence模块保持原否定/例外原文；三维/I/F判断表达议题或制度关系，不等于效果已成立。新resolver可补有限角色，但不应删除否定、OR条件或withdrawal。',
 '合并不得引入通用“有不/无即0”或删否定规则。完整current_proposition保留固定全条；当前触发和补充角色的句/款/对象范围分别记原始坐标；费用/风险获益/改良否定正值仍解释内容议题，非已实现优势。'),
 obs('M12-predicate-shadowing','P2',[('SE_v2_observed','dimensions','_safety_effect'),('SE_v2_observed','dimensions','_economics')],
 'SE模块同时保留基线_safety_effect/_economics和尾部同名新定义，Python最后定义生效。比较/复制第一个函数会错取基线行为，且merge看起来可能通过文本应用但实际shadow不同。',
 '函数级表已按运行时最后定义标记，并另存全部定义。ROOT候选应明确单一有效实现或明确重命名、注册，不依赖悄然shadow；保留各作者原文件不改。')]
with(HERE/'merge-conflicts-and-recommendations.json').open('x',encoding='utf8')as f:f.write(json.dumps({'identity':'nonhuman AI read-only interface preflight','not_release_or_semantic_acceptance':True,'SE_v2_status':'unsealed observed snapshot only','findings':findings},ensure_ascii=False,indent=2)+'\n')
recipe={'preferred_integration_base':'I/F sealed v2 for preserved manual-boundary accumulator and shared programme closure; not approval of its semantic outcomes','modules_unchanged_use_once':['evidence.py','source_packet.py','source_receipts.py'],'relations_keep_IF':['PROGRAMME_HEADING_RE','_primary_standard_group','_closed_primary_programme','seven _bounded_IF* resolvers'],'relations_append_SE_after_owner_seal':['_se_bounded_content','_se_direct_content_parents','_se_group_proof','_se_complete_lists','_se_edition','_se_article_proof','_se_operational_references'],'dimensions_keep_IF':['GAPS','INNOVATION_OBJECT','SUPPORT_ACTION','Accumulator boundary and finish','_innovation','_fairness'],'dimensions_add_SE_after_owner_seal':['SE_* constants','effective final _safety_effect','effective final _economics','_se_allowed','_se_form_or_status','_se_object','_ec_identity_only'],'manual_constant':'single five-dimension frozen5ea7 metadata; never old candidate manual string','must_manually_reconcile':['RelationView.__init__','_add dedupe identity','required request resolution interface','_units scope/closure-proof projection','_generic per-dimension dispatch and administrative innovation guard','judge consumer intersection'],'no_merge_code_written':True,'no_test_or_full_run_authorized_or_performed_in_this_preflight':True,'SE_v2_exact_release_binding_pending':True}
with(HERE/'proposed-function-merge-plan.json').open('x',encoding='utf8')as f:f.write(json.dumps(recipe,ensure_ascii=False,indent=2)+'\n')
lines=['当前结论是接口预审，未生成或执行合并规则。I/F v2保持封存；SE v1封存，SE v2仍未封存，本次只绑定其读取时观察快照，不作为发布版本。',
'AST比较137个有效函数/方法、42个常量，32个函数发生新增或修改。双方相对共同基线同时修改的函数只有RelationView.__init__、_generic、judge；SE v2另改_units，I/F另改Accumulator和条文/程序闭合。evidence/source_packet/source_receipts三模块与共同基线及双方版本逐字节一致。',
'合并建议以I/F封存v2保留共同闭合与边界累加器，再在SE v2封存后接其专用判据/有界关系；这只是降低覆盖冲突，不表示I/F语义审核已通过。三个共同入口和_units必须手工核契约，不能整份覆盖。保留I/F修正GAPS，不能把“境外已上市境内未上市”错误等同治疗选项缺口恢复；MANUAL五维统一5ea7元数据。',
'接口重点：affected_dimensions与only_IF_consumers取交集；boundary_quotes只验证闭合；_add文本+SHA去重可能压掉不同角色/消费者；已有必要请求不能因新关系成立而无差别清空，也不能将已消费确指范围继续称缺失。SE同段/对象路径与版次fallback有静态身份风险，已通知所有者，等待最终代码。',
'否定和例外完整原文保持，共有证据验证不改。不以否定词排除实质议题，不以同段、前段或scope可见性展开所有五维。父句接口保留自己的位置、对象、作用维度证明。',
'本轮未导入执行分类器，未运行77/800/4481，未改手册/材料/任何所有者代码，未读取主LLM标签。访问披露：曾误将SE before-v2-repair.json预览作绑定元数据，实际含固定开发控制expected字段；未用于比较或建议，ROOT已告知，之后只读代码与封存元数据。初次AST提取遗漏walker调用，0函数输出已完整保留mechanical-attempt-001；当前表为修正后的纯静态机械结果。',
'待SE v2封存可另加发布精确绑定及相对本快照变化报告；现有观察报告不覆盖、不假称封存背书。独立I/F20例语义审核仍由ROOT核验，不在本轮接口报告中当金标准或据此改代码。','']
for f in findings:
 lines.extend([f["id"]+' '+f['priority'],f['finding'],'建议：'+f['merge_recommendation'],''])
(HERE/'合并接口预审说明.txt').write_text('\n'.join(lines)+'\n')
manifest={'status':'static preflight completed; SE v2 release pending','time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'no_owner_code_mutation':True,'no_semantic_predicate_or_cohort_execution':True,'artifacts':[binding(p)for p in sorted(HERE.iterdir())if p.is_file()]}
(HERE/'preflight-observation-seal.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'finding_N':len(findings),'seal':binding(HERE/'preflight-observation-seal.json')},ensure_ascii=False))
