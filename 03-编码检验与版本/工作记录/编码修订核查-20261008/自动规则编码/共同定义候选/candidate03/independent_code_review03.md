# candidate03 有界实现审查记录

审查日期：2026-10-09。审查者为并行代码审查 AI；这是已暴露开发材料的实现审查，不是盲审、金标准评估或独立效度验证。

本次仅阅读 `runtime/common_reference_resolution03.py`、`runtime/common_definition_stage.py` 及必要调用依赖。没有修改运行代码，没有读取金标签、已有输出或分数，没有扩样或全量执行。本记录由审查者保存。

此前实际输入只涉及两条：

- `未用于本次编写的开发检查/real12_rule_inputs_original_lines.jsonl` 的 `RECODE25-01432`（原 ID `3c93f0797a:u00056`）：当前直接引用只选择 p0022，即经绑定 HTML 全条两段对应认证的第七条第一款；最终语境锚点仅 p0022，新增 E 亦仅 p0022；未保留第五条递归证据，旧 E 为空。
- `已曝光23条检查/real21_rule_inputs_original_lines.jsonl` 的 `RECODE25-02086`（原 ID `5f940f44cf:renew22_u014`）：最终语境锚点为 renew22_p025、p026、p027；“原支付范围满足条件(1)的情况下”前提锚点数为 0。此处记录证据定位，不报告新分数。

环境及执行记录：首次系统 `python3 -B` 已完成 01432；继续认证 02086 的 PDF 语境时因 `ModuleNotFoundError: No module named 'pypdf'` 中止，02086 未完成该次完整管线。随后使用既有 bundled Python `/LOCAL_HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B` 完成 02086；支付 helper 更新后，使用该环境各复跑两条中的每一条一次。因此此前共有 2 个不同实际输入、4 次完整单条管线执行；未安装依赖。表格修复后的本次收束没有重跑这两条。

支付语境问题已闭环：旧实现对整分句作过滤，却允许必需内容 fallback 的窄“医保支付范围”绕过。最新 `_payment_context_premise_only` 根据 relation 真实跨度回查所属完整分句；构造“(2)调整医保支付范围的药品:原支付范围满足条件(1)的情况下”两路径均被排除，“原医保支付范围满足条件的情况下”被排除，“应当确定新的医保支付范围”保留。此前实际两条复跑时使用的 38 个 runtime `.py` 合并 SHA256 为 `d9fcf3b6ab1a16d35abe1a6bfaccb116cf7b38b5d8d65d0fe91e17bc0a267bf8`。

表格边界问题已闭环：原解析器会把 table/td 内的 p 当作条文款段。root 增加表格祖先标记及条文区间中的表格位置检查。本次只再次运行同一个纯内存构造反例，未读取其他实际输入：

```html
<p>第七条 首款正文。</p><table><tr><td><p>表格单元格内的说明。</p></td></tr></table><p>第八条 后续条文。</p>
```

以两上下文分别对应首款与表格 p，并给定“符合本办法第七条第二款”，修复后的 `select_direct_contexts` 返回空列表，原反例通过。该探针仅以 mock 代替 JSON/HTML 文件读取与文件散列，验证结构解析拒绝路径；它不是新的真实来源认证试验。root 报告的其他 selftest 没有在本次重复运行。

接受的明确范围限制：款选择仅支持绑定原 HTML 的 JSON，PDF 提取段落不作款认证；无下一条边界、编号项及不支持的款序拒绝；新增 E 仅覆盖直接条件中明确用于证明药品有效性的试验数据表达。未把这些拒绝解释为人工判断错误。

本次收束结论：已复核的支付窄短语绕过和表格 p 误认证均已修复；不据两条开发输入推断总体性能。

最终代码快照（探针执行前后散列一致）：

- `common_reference_resolution03.py` SHA256：`96dc862d32ea74f18e544cb51b99217430ea3ceb50565af49fc21dcc5eb952b4`。
- `common_definition_stage.py` SHA256：`af33f75ace80ffa9fe38300881cd0ee714d3974fffae822b8904b95d8badc724`。
- 38 个 runtime `.py` 合并 SHA256：`6d81fb47362d6a45a387c6654be22b01361eb4cf1485d3f24e3c6f2242a9c174`。算法为按文件名排序，逐项拼接 `filename + NUL + bytes + NUL` 后计算 SHA256。
