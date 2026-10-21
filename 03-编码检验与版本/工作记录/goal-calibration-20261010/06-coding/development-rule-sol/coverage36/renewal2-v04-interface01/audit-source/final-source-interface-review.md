# 独立来源与接口审计

已完成来源完整性和接口检查。197 / 197 来源检查、13 / 13 reader 独立控件、7 / 7 最终诊断 fallback 独立控件通过。此前 20 / 20 pre-coder 与纯账本控件绑定旧 runner 候选；实际 coder 循环的 AST 与原 runner 相同。

两条 raw 记录保留 60 / 46 个 contexts，共 106 个；每条均完整保留供给资源中的 37 个文本、1 个几何节点和 9 张附件。37 个原文本的 SHA、交叠字符区间与 49 个页区域一致，9 张 PNG 均为 1819 × 2573，原资源至 CTX 的映射和各条 source graph 闭合。供给资源的完整性按其明确 scope 核对：规则一、规则二全文，以及规则三开头、前言和共同附录；不声称 PDF 每字均已转录。

新 reader 返回原始对象和规范化 JSON 字节完全一致，unknown 字段明确报错，没有删掉、重标或补建来源关系。source_references.source_field 的 source_context 字面值原样保留；它与 raw key contexts 的差异没有被当作 JSON 指针重写。相对附件路径以 design.asset_path_base 解析；region.page_asset 以 exact basename、physical_page、同一 source SHA 绑定。PNG 只读 SHA 与 IHDR，未解释像素；PDF 仅读完整性摘要。

原 reader 的失败是路径约束和新增字段/图结构接口不兼容，不是来源正文丢失。当前 raw loader 可验证材料，但冻结的 semantic contract 不接收两个 same_snapshot kind 和非空 source_references。独立仅边界验证确认两条均在 semantic_unit 抛出 UnsupportedSourceGraph，尚未加载 evidence、relations、dimensions，也未执行真实判定。这种拒绝应保留为技术失败；不能填成规则 0 或 rule-null。

runner 的分离诊断保留 raw source_record 全字段。无完整 reader 输出时，fallback 先从单次读取 payload 核对冻结 SHA，再核对有序 design IDs，才生成 10 格 technical_failure；每格 rule_not_executed=True、rule_value=None、rules_null=False、comparison_eligible=False，原空/部分 predictions 和 failed seal 不变。独立人工控制复现的旧“封存后改源被重读”失败保存在 fallback-controls-result-run01.json（5 / 6）；最终 bcdc74... 版本的 7 项全部通过，原失败没有覆盖。

三个语义文件与 implementation04 origin 逐字节相同。最终 runner SHA: bcdc74f2079ba41bb91a03480db5186e531c5a817647940a6610fe1f63232123；最终 reader SHA: dee2733f551797ec1485eb5316e00ffc71f9ad539c276b023dfd18d5dc08276e。

精确 15 项材料路径、SHA、bytes 见 runtime-material-read-allowlist.json；最终 5 个实现文件绑定见 final-source-interface-review.json。source delivery seal 在 design 中只给 path、没有预先 SHA，因此审计记录当前 digest 后再解析，确认其 source/resource 绑定与授权 design 一致；runner 封存当前 digest 并在结束后复核。seal 列出的 projection-audit/source_inputs 未跟随读取。

审计写入均位于本 audit-source 目录。未读新2参照、A/B/native 结果，未改任何语义/接口代码，未运行 actual predictions 或 evaluation。

执行命令（报告采用独占创建，重复执行会拒绝覆盖既有记录）：

```sh
python3 -B /PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding/development-rule-sol/coverage36/renewal2-v04-interface01/audit-source/source_integrity_audit.py
python3 -B /PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding/development-rule-sol/coverage36/renewal2-v04-interface01/audit-source/test_runner_guards_independent.py
python3 -B /PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding/development-rule-sol/coverage36/renewal2-v04-interface01/audit-source/test_fallback_independent.py run02
python3 -B /PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding/development-rule-sol/coverage36/renewal2-v04-interface01/audit-source/test_reader_contract_independent.py
```
