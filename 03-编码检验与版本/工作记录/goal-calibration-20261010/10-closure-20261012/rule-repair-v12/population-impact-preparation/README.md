# v12 S/F 静态影响范围准备候选

本目录只准备范围与来源复用方案，尚未采纳、未启动分类、未更改生产。定版静态结果为 `attempt03/selection.json` 和 `attempt03/record-scope.jsonl`：完整 4481 中选中 2082，未选 2399。这些是可能改变的保守范围，不是预测改变数量。选择不使用现有标签、正例、人工反馈值或检验分数。

输入以 `input-bindings.json` 固定：当前 machine-freeze（SHA `f6e2e2d08a4f4c448ea1bd8b1b07c51cc95b5f7d2eb35dd0c371fd6d1a961b80`）、当前 v16 的 4481 包/共同源行、当前实际规则 lineage、共同手册/提示/协议、完整 v11 与冻结 v12 的五个模块。4481 个实际 packet 文件均核 SHA、字节数、ID、包内容与当前共同源行的一致性。预测文件只核字节绑定，未解析预测值。

## 静态充分条件和未选记录等价证明

S 扫描每个完整来源包中递归的 `text` 字段。这包括当前句、原上下文、原文段落、明确来源资源、历史补充、图文转写和完整文字快照。来源适用性不由扫描授予；纳入任何未实际适用的文字只会多选。

此文字闭包与冻结代码对应：`source_packet.py:36–136` 的 `semantic_unit/_derived_contexts` 从原 `text` 字段取得当前与上下文文字；`evidence.py` 的 `context_anchor` 返回其精确子串；`dimensions.py:285` 的 `_units` 仅以当前或引文子串建单元。S 额外消费的 `SE_` 父谓词由 `relations.py:2432,2438,2576,2578,2580,2586` 取源 `text` 或以句号连接有限源子串。因此任一可能进入新 S helper 的文字都在此闭包内，不需要先运行关系建构或分类。包的说明、路径、字符串数组元数据不直接成为 S 单元正文，故不以其通用“文件”说明决定范围。

S 门包含三类必要词的宽化并集：`安全`；`字段/栏目/标题/文件/附件`；SE_RISK 每个分支的必要字词（保留风险、不良、禁忌等，并放宽 AESI/ADR/SAE/AE 的边界和部分限定）。这些只是影响候选词，绝不建立 S 正例。三类全部不命中时：

1. `_s_owned_data_security_scope` 无安全属性可匹配，返回原 scope 与空列表；
2. `_s_risk_question_content_scope` 无名称角色可匹配，返回原 scope；其 `_s_field_answer_review` 不会被调用；
3. 当前/直接父谓词风险检查均无 SE_RISK 内容可匹配，返回 False，且父关系辅助检查不会产生额外调用；
4. 把这些恒等/False 代入 `_safety_effect` 后，程序实际执行的 AST 归约与完整 v11 原函数完全相同，包括 E 的分支、排除理由和完整决定字段。

F 门要求原 `_v9_repair_gate` 命中当前句，且包内存在与当前 primary SHA 相同的非空 `paragraphs`，其中有原 `_v9_structured_plan` 所用的引号计划名称结构。前者 False 时整个 v9 增补不可达；后者 False 时 `plans` 不能增加，方法在任何新增 helper 前返回。门宽于真正资格/机会判断，故不会因旧 F 标签或现有阳性证据排除候选。当前匹配直接使用冻结 `evidence.py` 中 `matching_view` 和 `_CJK_WHITESPACE` 的原 AST，仅加载此纯规范化函数，未导入或调用分类器。

自动 AST 检查还证实：dimensions 除五个新增 S helper 和 `_safety_effect` 外全部相同；relations 除新增 F helper 和 `_v9_structured_plan` 外全部相同；后者在新增 helper 前的整段和 I 发射完全相同；evidence/source_packet/source_receipts 字节相同。S 和 F 门同时 False 后，新 helper 的所有差异均为不可达或恒等，故在同一来源输入上五维完整决定、请求和事件与完整 v11 同轨。这里证明的是代码/结构等价，不是从实际输出相同反推范围。

## 当前混合生产结果如何继承

当前实际来源仍是 v9 3824、v7 577、v10 36、v11 44。`input-bindings.json.adopted_compatibility_chain` 另固定了 v8→v9→v10→v11 的 57 份既有采用、父 seal、范围及静态排除证明文件；选择器逐项核字节，核每份现有 selection 与已采用 affected IDs 完全相同，并核四阶段父 seal 连续。逐 ID 的“最后命中已采用范围的版本”与当前实际 lineage 全部一致。v8 的 7 条后来均进入更高版本范围，故当前没有 v8 实际来源。

v8 使用已有单分支修改的排除证明；v9/v10/v11 使用已有 ROOT 批准的静态 contract 和其绑定的兼容性证据。本次不重跑旧选择器，不以旧标签重新选范围。逐记录输出保留旧实际 run、旧预测行 SHA 与经历的既有静态排除阶段。未选 2399 条仅在这条已采用的兼容链上复用原生产结果，不能记为“v12 已实际执行”。01402 的原技术失败及仅回执身份修复仍由现有采用链保留，不把回执修复记为新推断。

## 后续执行所需的原来源契约

ROOT 审过本候选后，才可另建实际执行目录。新范围须使用当前 v16 精确包及原共同源行，保持 source_record/上下文/源文件/附件及字节哈希，不把本次扫描生成的候选词或命中位置传给分类器。原 `source_packet.semantic_unit`、`source_inventory`、来源阅读协议和 `source_receipts.resolve_inventory` 原件身份核验契约可以复用；后者只可用已绑定源快照与 payload 补清身份，不能从消费者自己声明的事件反向生成来源身份，更不能把元数据扫描写为实际图片阅读。

旧 `rule-v11-I-v16-affected-v2-root` 的 scope/driver/interface 仅供来源运输契约参考；其中 I-only 允许变更范围和旧 run 名不能原样继承。新实际范围应完整计算每条五维，只允许 S/F 的必要变更，并比较 E/Ec/I 的完整决定以及来源请求/事件是否保持；如有新不一致须先解释，而不是改为只比较数值。未选条目保留原字节与实际 lineage。失败、合法 NULL、缺失和已完成保持各自身份，不作为筛除原因。若源包、代码或来源适配器改变，当前静态排除证书即不适用，须重新明确范围。

原 v12 目录的停用 stub 与 legacy-v11 I-only 入口均未改写；本目录也不写 adoption 或正式统计。当前开发材料曝光登记仍须沿本轮现有 prospective 方案办理，不能把本次范围检查当独立准确性验证。

## 复现和保留记录

从本目录执行 `python3 select_static_impact.py --out <全新的目录>` 即可复现静态准备，目录独占创建。`python3 check_static_selector.py --out <新的结果文件>` 只跑 15 个 NONHUMAN 静态候选控件；已保存的 `static-control-results.json` 为 15/15，通过不代表分类准确性。

保留了初次计数器实现错误（attempt01，未形成选择输出）及修复后的 attempt02。attempt02 因 AST 删除 helper 的变量名笔误触发全量 fallback，且早期扫描包含行政元数据而全选；它不是最终范围。对应源码与旧 input-bindings 字节均保留，没有用后来的代码假装早期成功。attempt03 才是修正这两项准备工具问题后的定版结果，八项静态代码检查全部通过。未运行真实分类或旧 331 控件复跑。
