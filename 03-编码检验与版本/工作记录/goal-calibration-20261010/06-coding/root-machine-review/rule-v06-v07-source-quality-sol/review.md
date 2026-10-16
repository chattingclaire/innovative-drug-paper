限定机械审查已完成：八次 run seal 和 v06/v07 最终交付 seal 均按实际 SHA、字节数核等。2,136 项绑定检查覆盖 280 个不同文件，未发现新的机械不一致。v06 最终封存有 103 项文件，v07 有 73 项；v07 总 seal 的实际 SHA 为 `1fa87a328b7aa3311bc40fe85e2450f241b76699636f937b7118500a1b93f136`。

| 版本 | 记录执行 | 唯一 ID | 五维槽 | 保留决定 | 技术失败槽 | 编码 null |
|---|---:|---:|---:|---:|---:|---:|
| v06 | 83 | 77 | 415 | 400 | 15 | 0 |
| v07 | 83 | 77 | 415 | 415 | 0 | 0 |

实际错误为 v06 的 RECODE25-01459、01464、01480 三处来源收据身份绑定失败。三个 prediction 的 labels/decisions 为 None，候选决定保留在 candidate_decisions_diagnostic_only；15 个槽明确 technical_failure，rule_value=None、rules_null=False、comparison_eligible=False，未当作规则 0 或编码 null。原运行文件保持封存，v07 的成功输出另存于新版本。

每个 run 的冻结、开始、完成、seal 时间顺序成立；当前冻结输入的 mtime 均早于该 run 冻结时间，冻结与封存绑定完全相同。源码静态路径先写 freeze 再导入分类模块。时间和程序日志属于本地记录，不能独立证明历史进程或提供外部时间见证。

77 个预备完整 bundle 与 v12 默认接口的原来源字段一致，八次交付的 166 个 bundle 均逐项核等。有效语义单元只按已声明规则移除行政 ID，并保留正文、原 CTX 和来源 bundle；派生片段逐一追溯原 bundle 指针、文字、来源 SHA 和原 view SHA。审查未调用 lookup、judge、RelationView 或身份解析器，也未运行构造对照。

v07 三条身份 delta 只修改消费侧 inventory 副本中 FULLSOURCE-3ef0e76014ea81d63f5b 的空 source_sha256，解析值来自原 payload 显式 source_pdf_sha256=a83ae5…，并与唯一 SOURCE 身份、原 PDF SHA/字节数及原 payload 文件内容和 view SHA 核等。原 producer inventory 空值仍保留；没有从空字段猜出处，没有改写正文或来源材料。source_packet、relations、evidence、dimensions 四模块与 v06 逐字节相同。

v07 有 1,892 个程序消费/读入收据和 187 个使用收据，均绑定实际原来源及 view，使用记录可追溯对应读入。136 次可用图像资源列举均没有像素读取收据；图像字节哈希、视觉转写文字和 geometry 的程序扫描不等于真正看图。当前日志没有必需 image view；本审查不把所有可用图片无条件列为必读，也不认证必要语境选择的语义充分性。

00652 的 substantive_list 缺失成员范围按协议默认必要依赖处理，missing_required_source 与 source_read_requirements_recorded=false 保持在实际日志中。现有维度汇总器把请求路由到 Ec、I：两项实际正判断来自 current 命题，context_evidence=[]，并在 details.unresolved_material_requests 保留该未解请求；source_relation_traces 和 source use receipts 均为空。S/E/F 没有该请求的维度依赖。机械上可同时保留自足当前判断并停止从缺失成员建立额外关系，因此 rule_null=0 不要求全五维置 null；但 415 只能称保留决定，不能称所有必要来源已闭合或语义已验证。本审查不认证这五项构念判断正确。

审查只读取两版本四个限定范围、其封存元数据及绑定的来源原对象；没有读取参照/其他模型答案内容、计算性能、修改首判或运行程序。记录与收据机械相容不构成真人独立验证、总体效度或泛化证据。审查结果封存后停止。
