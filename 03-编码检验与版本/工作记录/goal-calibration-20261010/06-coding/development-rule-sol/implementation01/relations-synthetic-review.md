# relations.py 合成关系接口审查日志

日期：2026-10-10。审查者为 GPT-6.1 Sol、ultra 的 AI 实现审查，不能记为真人编码。

本阶段只读 `relations.py` 并导入新的关系/引文工具进行合成构造 QA；唯一新增文件为本日志。没有修改关系或维度代码，没有读取 `reference.jsonl`、未封存首判、旧预测或1444剩余池，没有加载41条实际来源进行判读，没有调用 `dimensions.judge`。以下六例均为新编写的小合成输入，不是语料记录。相同六例在修正后复查，未增加关系案例。

最终复查代码 SHA256：`d9622838082bc2fe19d45b6866ca8af75e1442d6b1edf6352e169a653c259da6`。六例的预期关系形状和无多余补材请求全部通过；这仅验证所列关系接口行为，不构成分类准确性或正式检验结论。

## 共用合成输入约定

每个 `unit` 有 `text/contexts/pages/attachments`，后两项均为空数组，没有记录ID或标签。下文 `1×64` 等表示重复字符组成的64位占位SHA，仅为合成来源身份，未用于决定标签。所有 context 的 `source_ref.locator` 均为 `{}`，本组直接测试关系API，不声明占位SHA具有二进制认证。

共用机制来源：

```json
{
  "context_id": "CTX-plan",
  "kind": "external_source",
  "text": "本试点适用范围为创新药研发。申请人可获得方案反馈，提供技术服务。",
  "source_ref": {
    "sha256": "1111111111111111111111111111111111111111111111111111111111111111",
    "locator": {},
    "metadata": {
      "source_title": "创新药研发支持试点工作方案",
      "document_date": "2024-07-31"
    }
  }
}
```

## 六例输入、首次结果及修后结果

### 1. action_not_on_named_plan：当前行动未作用于具名机制

当前文本：`该药物可以适用一般质量检查；附件列出《创新药研发支持试点工作方案》供了解。`

语境只有上述 `CTX-plan`。

首次结果：错误生成 `named_mechanism`，引用两段 `CTX-plan`，把全单元中的“适用”与附件导航的计划名称相连，版本记录为 `provided_same_version_source`。

修正：`_mechanisms` 按局部分句定位对机制名称直接施加的行动；名称前后的附件、资料、归档等载体关系不许可机制展开（最终代码207–220行）。

最终结果：`relations=[]`，`material_requests=[]`。通过。

### 2. historical_year_plus_later_unrelated_year：行动年份与随后独立动作年份分开

当前文本：`2024年决定开展创新药研发支持试点，2025年完善资料递交格式。`

语境只有上述2024版 `CTX-plan`。

首次结果：对全单元年份2024和2025同时与2024来源比较，没有生成机制关系，错误请求“具名机制的行动时期与来源版本未能绑定”。

第一轮修正后：按句号/分号分句仍未分开逗号后的独立动作，原例仍产生上述多余补材请求。

最终修正：机制行动分句加入中文/英文逗号边界；`_version(c, action_clause)` 只比较直接行动所在分句。完整决策命题仍保留整个固定单元。

最终结果：一个 `named_mechanism`；`context_ids=["CTX-plan","CTX-plan"]`，`current_years=["2024年"]`，`source_date="2024-07-31"`，`established=true`，`binding="explicit_historical_year"`；`material_requests=[]`。通过。

### 3. unlinked_other_source_parent：另一来源的父句不能补当前成员

当前文本：`当前成员只要求核对文件格式。`

语境：

| context_id | kind | text | SHA | structure |
|---|---|---|---|---|
| CTX-current | paragraph | 当前成员只要求核对文件格式。 | 1×64 | `{"paragraph_id":"P1","sequence_index":0}` |
| CTX-other-parent | parent_paragraph | 符合以下条件的药品可调整支付范围： | 2×64 | `{"paragraph_id":"P9","sequence_index":9}` |

首次结果：错误生成引用 `CTX-other-parent` 的 `parent_predicate`，没有检查当前来源与父句来源一致。

修正：`_parents` 从包含当前文本的 paragraph 建立来源集合，父句必须属于该集合（91–99行）。

最终结果：`relations=[]`，`material_requests=[]`。通过。本例验证异源拒绝，没有穷尽同源多重父句的所有图结构。

### 4. list_continues_beyond_boundary：读取完整本列表但停止于下一制度

当前文本：`符合以下条件的药品可申请支持：`

全部节点使用1×64来源SHA。语境：

| context_id | kind | text | structure |
|---|---|---|---|
| CTX-list | ordered_list | 空字符串 | `{"child_groups":[{"position":"contexts","ordered_context_ids":["CTX-intro","CTX-member","CTX-stop","CTX-after"]}]}` |
| CTX-intro | paragraph | 符合以下条件的药品可申请支持： | `{"sequence_index":0}` |
| CTX-member | ordered_members | 一、满足规定的对象条件。 | `{"sequence_index":1}` |
| CTX-stop | boundary | 第二章另一制度 | `{"sequence_index":2}` |
| CTX-after | ordered_members | 另一制度规定应评价药物疗效。 | `{"sequence_index":3}` |

首次结果：`substantive_list` 引用 `["CTX-member","CTX-after"]`，过滤边界而继续读取边界后内容，仍声称 `full_scope=true`。

修正：先保留容器全部节点，再在 `boundary/following_heading` 停止，随后才选择有文本的成员引用（113、130–134行）。这样无文本边界不会在截断前被丢弃；无文本节点也不会被伪作字面引文。

最终结果：一个 `substantive_list`，只引用 `["CTX-member"]`；`material_requests=[]`。通过。

补充接口核验：在本例结构中保留 `CTX-stop` 引用但删除边界实体，然后将现有结构通过 `source_packet.semantic_unit`，在进入关系API之前得到 `PacketInterfaceError`：`contexts/0/structure/child_groups/0/ordered_context_ids/2: dangling CTX reference`。没有新增关系案例或分类调用。无文本边界实体保留的修正另经只读代码检查，未额外构造新关系输入。

### 5. explanation_merges_different_policy_and_version：不同政策解释不能拼接

当前文本：`2024年完善偏远地区药品配送服务。`

语境均为 `external_source`：

| context_id | text | SHA | source_ref.metadata |
|---|---|---|---|
| CTX-measure | 鼓励完善偏远地区药品配送服务。 | 3×64 | `{"source_title":"甲配送政策解读","source_document_kind":"甲政策解读","policy_document_date":"2024-11-14"}` |
| CTX-problem | 偏远地区药品可及性差。 | 4×64 | `{"source_title":"乙医疗政策解读","source_document_kind":"乙政策解读","policy_document_date":"2025-01-01"}` |

首次结果：错误生成 `policy_explanation`，引用 `["CTX-problem","CTX-measure"]`，虽然其中一个 `version_binding.established=false`，仍拼接了另一政策的问题与措施。

修正：按来源SHA、政策文号、政策日期和来源标题组成身份绑定分组；绑定不完整或版本未成立时不展开；问题和措施必须在同组中对应当前措施（264–285行）。

最终结果：`relations=[]`，`material_requests=[]`。通过。本输入本身没有政策文号，因此经不完整身份绑定排除；它没有单独验证所有字段完整但措施仍不对应的其他场景。

### 6. routine_archive_over_requests_named_support：普通归档不请求具名支持全文

当前文本：`实施创新药研究计划资料的归档管理。`

语境为空数组。

首次结果：没有关系，但错误请求“当前实质实施具名支持安排，缺少同版对象与直接可用机制原文”。当前行动实际作用于资料归档。

修正：具名机制缺材请求须有当前支持安排实施关系；`计划资料/文件/归档/名称/格式` 的载体关系不触发此请求（248–252行）。

最终结果：`relations=[]`，`material_requests=[]`。通过。

## 实际核验记录

最终复查对相同六例分别创建 `RelationView(unit)`；断言关系种类依次为：`[]`、`[named_mechanism]`、`[]`、`[substantive_list]`、`[]`、`[]`，六例 `material_requests` 均为空。另断言第2例只绑定2024年，第4例只引用 `CTX-member`。分类调用次数为0，fixture来源加载次数为0，reference读取次数为0。

标题、日期与SHA在这里用于识别来源、绑定版本、限制引用和去重，没有直接赋S/E/Ec/I/F标签的分支。本审查没有导入维度模块，不能把关系QA通过解释为五维分类合格。

只读审查保留的范围说明：一般标准细地址、同源但无当前边的父句、多子群或“或”成员范围、解释同政策身份与当前原政策的进一步连接，都不属于这六例的全面验证。`full_scope=true` 是关系输出声明，来源图闭合和容器截断通过不能单独替代原政策的实质完整性检查。该记录供实施开发修复与后续独立核查使用，不作为真人参照或正式模型验收。
