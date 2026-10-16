# implementation02 关系补全审查

日期：2026-10-10。GPT-6.1 Sol、ultra 的 AI 代码审查，不是真人编码或专家裁定。首审代码 SHA256：`17b8b368dd195d7d07528cc5b73af0ca8e9c99c5971da2177681358c22302221`。

范围仅为 `relations.py` 的 `_local_operations`、`_resource_definitions`、`_anaphors`、`object_evidence` 与其公共引文接口。构造六个小合成关系输入，未调用维度分类器；没有加载实际41条 source/reference，没有读取旧预测或未封存首判，没有修改任何实现代码。本阶段唯一写入为本报告。

结论：两例符合预期，四例确认当前实体、来源或组件绑定缺口。新增接口已经限制到同段前缀或当前原段落，宜保留；最低必要修正是进一步绑定同一实体、同一组件，并在对象回退路径复用来源守卫，无须扩大语境扫描。

## 原函数、一般漏洞与最低必要修正

| 原函数/首审行号 | 当前正确基础与缺口 | 最低必要修正 | 对应合成验证 |
|---|---|---|---|
| `_local_operations` 154–169 | 只从含当前原文的 paragraph 前缀取必要句，且当前须有操作数据/参考关系；但164行仅比较两字操作词，未绑定本药与另一药品。 | 保留同段前缀规则；明确实体相反时拒绝借用。当前本药/本装置的操作参考应承接同一实体或原文明确指向的目标限制；不能只因“注射”等操作同词连结。 | 例1应成立，例2应拒绝。 |
| `_anaphors` 314–324；`object_evidence` 386–394 | `_anaphors` 已按当前 paragraph 来源SHA拒绝异源scope；但 `object_evidence` 的 parent/heading 回退绕过该守卫，异源 heading 仍被认定为当前对象。 | 对所有 parent/heading/objectscope 回退使用同一当前来源绑定；有显式组件边/组件ID时同时限定组件。不得在 anaphor 已拒绝后另一路径重新引入同一异源对象。 | 例3的关系为空是正确的，但 object_evidence 应 `established=false`，首审实际为true。 |
| `_resource_definitions` 347、357–360 | 当前须明确设立团队，服务来自含当前原文的原段落；但服务正则匹配任意“团队…负责/提供/服务”，没有把服务定义绑定到347行所设团队。 | 只接受当前所设团队名称、明确承接的“该团队”等定义，按最近指代及排他实体处理；另一支既有/数据管理团队的服务不能成为新设专项审评团队的服务。 | 例4应成立，例5缺当前团队定义，应拒绝named关系。 |
| `_resource_definitions` 361–375 | 要求同来源scope、服务和上市前stage同时存在；但stage和objects只比较SHA，等同整份文件，未核当前组件/安排。 | stage与scope必须属于当前原段落所处组件或有明确同一安排关系。显式component不同则拒绝；组件字段缺失时可用已给出的组件范围/结构边核明，不能把same SHA直接称为same component。 | 例6的COMP-B阶段不能补COMP-A当前团队，应拒绝named关系。 |

另有只读接口事项：两个新方法以 `self.text in raw` 和 `raw.find(self.text)` 定位当前出现（159–161、353行）。若同段重复当前原句，位置会固定取首次；应按封存来源位置或唯一出现核验定位，不能静默替代当前位置。本次没有额外构造第七个关系输入。

## 共用合成输入约定

所有 unit 仅有 `text/contexts/pages/attachments`，后两项为空数组，无记录ID、标签或参照答案。context 使用 `context_id/kind/text/structure/source_ref`；`source_ref.locator={}`。`1×64/2×64` 是合成来源身份占位SHA，未认证任何原始二进制文件，也未用于赋维度。以下直接调用 `RelationView(unit)`，没有调用 `dimensions.judge`。

共用团队设置：

- 当前文本 `setup`：`组建专项审评团队。`
- 同一团队功能 `service`：`该团队负责提供技术咨询与研究反馈。`
- `CTX-scope`：kind=`source_paragraph`，text=`一、适用范围：本工作适用于创新药研发。`，structure=`{"source_role":"self_declared_scope","component_id":"COMP-A"}`，来源SHA=1×64。
- `CTX-stage`：kind=`source_paragraph`，text=`本工作适用于临床试验上市前的研发阶段。`，structure=`{"component_id":"COMP-A"}`，来源SHA=1×64。
- 所有 `CTX-current` 的kind=`paragraph`，structure=`{"paragraph_id":"P1","component_id":"COMP-A"}`，来源SHA=1×64。

## 六例输入与首审结果

### 1. same_entity_operation：同实体操作前缀

当前：`本药参考注射操作数据改进装置设计。`

唯一原段落：`本药的注射操作存在困难。本药参考注射操作数据改进装置设计。`

预期：可生成 `parent_predicate`，引用当前原段落前缀的本药注射限制；该关系不是直接的I标签。

实际：一个 `parent_predicate`，`context_ids=["CTX-current"]`，`relation_subtype="same_paragraph_operation_reference"`，无补材请求。**通过。**

### 2. different_entity_operation：不同药品同操作词

当前仍为：`本药参考注射操作数据改进装置设计。`

唯一原段落：`另一药品的注射操作存在困难。本药参考注射操作数据改进装置设计。`

预期：没有当前本药限制的明确连接，不能借另一药品的限制生成本药操作关系。

实际：仍生成与例1相同的 `parent_predicate`、`same_paragraph_operation_reference`，无补材请求。**一般实体绑定错误。** 不需要因为拒绝该推断就无限请求其他背景。

### 3. no_current_reference_and_foreign_object_scope：无当前参考且异源scope

当前：`本项目只记录编号。`

当前原段落：`注射操作存在困难。本项目只记录编号。`

额外语境 `CTX-foreign-scope`：kind=`heading`，text=`创新药研发项目适用范围`，structure=`{"source_role":"self_declared_scope","component_id":"COMP-B"}`，来源SHA=2×64。

预期：当前没有操作数据/参考关系，不应借同段操作限制；异源scope不应补对象。关系为空且 `object_evidence.established=false`。

实际：`relations=[]`，无补材请求，前一门槛通过；但 `object_evidence()` 返回 `established=true`，引用 `CTX-foreign-scope`，role=`explicit_parent_or_heading_object`。**对象回退绕过异源守卫。**

### 4. team_all_bound_conditions：团队定义、scope和stage全部齐全

当前：`setup`。

`CTX-current.text=setup+service`，语境另含共用 `CTX-scope/CTX-stage`，同来源、同COMP-A。

预期：当前设立团队与该团队的具体服务直接承接，scope与上市前stage齐全，可生成资源定义的 `named_mechanism`。

实际：一个scope `anaphor`，一个 `named_mechanism`；后者引用 `["CTX-scope","CTX-current","CTX-stage"]`，`mechanism_name="专项审评团队"`，`resource_definition_required=true`，无补材请求。**通过。**

### 5. current_team_definition_missing_other_team_present：当前团队定义缺失，另一团队定义不能替代

当前：`setup`。

`CTX-current.text=组建专项审评团队。另一支数据管理团队负责提供技术咨询与研究反馈。`

另含共用 `CTX-scope/CTX-stage`，同来源、同COMP-A。

预期：专项审评团队的具体功能尚未明示，另一支团队服务不能替代，不能生成当前团队的 `named_mechanism`。

实际：生成scope `anaphor` 和引用 `["CTX-scope","CTX-current","CTX-stage"]` 的 `named_mechanism`，仍称 `mechanism_name="专项审评团队"`，无补材请求。**团队实体绑定错误。**

### 6. current_stage_missing_other_component_stage_present：当前阶段缺失，另一组件不能补

当前：`setup`。

`CTX-current.text=setup+service`，另含共用COMP-A `CTX-scope`，但没有共用 `CTX-stage`。

替代的 `CTX-stage-other`：kind=`source_paragraph`，text=`另一制度适用于临床试验上市前的研发阶段。`，structure=`{"component_id":"COMP-B"}`，来源SHA=1×64。

预期：同文件的另一制度不是当前安排的阶段定义，不能生成当前团队的 `named_mechanism`。

实际：生成scope `anaphor` 和引用 `["CTX-scope","CTX-current","CTX-stage-other"]` 的 `named_mechanism`，无补材请求。**当前组件阶段绑定错误。**

## 结果边界与后续复查

六例共调用关系API六次，分类调用0次，实际41条加载0次，reference加载0次。例1和例4验证应成立的关系；例2、3、5、6确认接口层的四个一般错误。源SHA在新增方法中用于来源筛选，并无标签向量输出；问题是筛选仍不足以证明同一实体/组件，不是采用ID或全文指纹查标签。

root可按本报告修正后复查相同六例，保留首审记录。修复与合成关系QA不能替代后续封存分类、分离评估或真人参照检验，也不能从这些合成例推出实际41条标签数量或模型指标。

## 修后复查：原六例全部符合预期

修后 `relations.py` SHA256：`193b2f9b60b5313d1906003b702a6663ed00b04bf2b61ee83a1de25b529d0ffb`。运行前后校验该文件SHA一致。以上首审输入、失败及原行号均保留；本节为修后最终状态。

再次只调用同六个 `RelationView` 输入，未增添案例、未调用维度分类器，也未加载实际41条source/reference。六例全部断言通过，所有补材请求仍为空。

| 原例 | 修后关系 / 对象结果 | 与首审相比 |
|---|---|---|
| 1 同实体操作前缀 | 一个 `parent_predicate`；引用 `CTX-current`，subtype仍为 `same_paragraph_operation_reference`。 | 正确关系保留。 |
| 2 不同药品同操作词 | `relations=[]`。 | 不再借用另一药品的注射限制。 |
| 3 无当前参考且异源scope | `relations=[]`；`object_evidence.established=false`，对象引文为空。 | 异源heading不再经对象回退重新引入。 |
| 4 团队三条件齐全 | `anaphor`及`named_mechanism`；后者引文恰为 `CTX-scope/CTX-current/CTX-stage`，名称仍为`专项审评团队`，`resource_definition_required=true`。 | 正确的当前团队资源定义保留。 |
| 5 当前团队定义缺失、另一团队定义存在 | 仅 `anaphor`，没有 `named_mechanism`。 | 不再借另一支数据管理团队的服务。 |
| 6 当前阶段缺失、另一组件阶段存在 | 仅 `anaphor`，没有 `named_mechanism`。 | 不再借COMP-B的上市前阶段建立COMP-A资源关系。 |

修后代码对应：`_local_operations` 171–173行排除当前未同指的明确其他药品/品种/项目主体；`object_evidence` 401–407行在parent/heading回退复用当前paragraph的来源SHA；`_resource_definitions` 369–372行将服务限制为当前所设团队名称或该/本/此团队，并排除明确其他团队；373–381行同时检查阶段、当前paragraph、scope之间已给组件ID的冲突。公共 `same_component` 31–35行仅拒绝双方已给且不同的组件ID，没有生成未知组件身份。

本轮复查确认首审四个失败在原六例中均不再出现。当前主体排除与团队指代仍是文本规则，未知组件仍不等于已认证同一组件；本次没有增加其他表述变体，也没有据此宣称任意实体或组件关系都已完整解决。首审所述重复当前原句的定位事项未在本轮新增检验。

累计两轮关系API调用12次，分类调用0次，实际41条加载0次，reference加载0次；本次仍只追加本报告，未改实现代码。
