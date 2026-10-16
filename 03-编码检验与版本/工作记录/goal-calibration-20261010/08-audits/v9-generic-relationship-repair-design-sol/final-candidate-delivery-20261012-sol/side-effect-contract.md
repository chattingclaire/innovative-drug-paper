# 最终候选的副作用与影响契约

新增代码只受当前正文同一 `V9_REPAIR_ENTRY` 入口控制，constructor 最末追加关系、judge 在所有旧消费者运行完后追加 I/F 消费。三项证据/适配/receipt模块字节保持v8。两个入口之外删除新增定义和常量后，完整 AST 恢复冻结v8；入口无命中时 constructor 新builder与consumer都不调用。

新增builder读取当前 record 的 unit、norm/text、source_ref、contexts/by_id、bundle 和同源有限资源，局部建立 roles、quotes、scope 与 binding。新增关系唯一kind为 `v9_IF_relationship`。旧 `_add` 是唯一共享写入：append `relations` 并从其重建 `source_relation_traces`；其 `_used_views`、proposition/traces 和 `_quote`/context_anchor 都只读既有记录资源并返回局部结构。没有向 contexts/all_contexts/by_id、material_requests/source_requests、source_view_events、primary payload cache 或原包写入。新增builder的非名称赋值目标及全部helper调用已逐项记录于AST proof inventory。

旧 `_units` 只消费 parent_predicate、substantive_list、cited_standard、named_mechanism、policy_explanation、price_arrangement 六种kind；旧 object_evidence仅当前/父标题对象与parent_predicate、anaphor，不读新kind。新kind和trace不能向旧 S/E/Ec消费者捐献上下文。新consumer调用旧 `_object` → object_evidence、_form_only、_publication_purpose、_administrative_innovation_owner、current_anchor和pure normalizer；均只读/局部构造。Unit、acc.add、acc.boundary构造记录局部决策。

consumer仅写 acc.positive/excluded/boundaries 的 I/F 子项；全程先验证 affected_dimensions 是非空、无重复的 I/F 子集。错误权利撤销逐条绑定旧 I4 basis_path、精确当前anchor、实际自身数据或确切非创新表行，保留不同path和当前合法原创新数据权利。00654类型只撤销精确当前无差异需求的全领域分配旧F path。受限母对象只加声明维度的未闭合边界：00068只I，00071 I/F；不强行给0/1。

新增 `_v9_current_context` 要求当前完整原段按旧geometry筛选后身份唯一、当前片段唯一。父句须明确target且非role-only，或同源ordered group证明：完整 current原段等于原ordered member，source_lines若双方提供须一致；原成员序号和行位置单调、parent_context_id一致、first/last闭合、下一顶层边界同源且编号紧随。其边界仅证明治理边，只有当前成员与总领条件消费。没有parent型段落任意继承。

旧 _se_parent_binding/_se_geometry*、_se_current_geometry_contexts、_closed_primary_programme、_primary_role_quotes、matching_view/raw_span/norm、same_component/ordinal_number等依赖只读/局部写；静态body审计必须覆盖这些传递依赖。不能把AST删除成立等同于gate内隔离已经独立验收。完整有限控制亦仅为开发验证。

静态selector不导入或执行classifier，只验证exact五模块及既有混合v8兼容baseline、manifest/packet哈希后用入口判可达性。全部gate可达记录均整条重算，包括旧1、旧0、null及其全部旧/新依据链；材料binding或完整decision不合格也必须选择。没有以130、人工77、部门、record ID、native值或目标成绩筛选。上下文中再远的关系只可能在两个入口调用后消费，因此gate闭包覆盖新增父/定义/支持/撤销及旧正例影响。

入口外复用要同时满足：本文件body隔离获独立审核、同适配/原包/wrapper、v7→v8混合baseline兼容证明、五模块/selector哈希及完整manifest成立。缺一条件就保守全4481 fallback。全量fallback是执行范围退路，不是本轮已运行。ROOT另存独立批准contract；冻结contract的approved=false不得原地改写。
