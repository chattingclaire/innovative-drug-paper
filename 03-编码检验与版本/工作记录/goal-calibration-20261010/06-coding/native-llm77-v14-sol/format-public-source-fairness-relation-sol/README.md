这是 ROOT 授权的 batch-0005 R attempt03 前瞻格式准备。没有启动模型、重试或聊天；旧失败与首件只读，材料尝试计数保持 3/3。

output-item.schema.json 逐字保留原 schema，仅替换 F.fairness_specific.fairness_relation 的值为 anyOf：完整原锚点 + 完整原 source-quote schema。两个分支外的字节、其他五维条件及原 schema ID 都保留。format-binding.json 覆盖旧 runtime required_read_files 中唯一 output-item.schema.json entry；其他来源、手册、protocol、gate/native_records 不改。

未来启动使用 launcher-batch-0005-attempt03.txt（≤4000B），按其绑定完整读 instruction-R-attempt03.txt，保存新 initialprompt 与 fullR 各自 SHA。新 attempt 使用真实新 runtime UUID，独立阅读原材料并保存首件，不复用旧首件/阅读。公共五字段分支只允许表示位置，仍须原 pointer/span 校验、实际 read/use 及其他所有必填语义条件。

独立 format-check 由有效 input-identities 显式加载新 schema，并对实际嵌套公共锚点调用既有 verify_source_quote；v4 scope/native_records 仍原样。原 select_technical_receipts 的相同初始 prompt SHA 条件不能被悄悄宣称通过，本次是 changed-format variant，由 ROOT 保留真实旧失败和最后一次材料计数处理；这里不修改 selection/gate。

只有 5 个构造锚点例子的格式核查：原 current/context、新五字段合法，缺字段/额外字段不合法。未用旧04915候选或标签，不是性能或新首判测试。差异与静态接点见 diff-report.json、validator-contact-review.json。全部为 AI 准备，非真人检验；封存后停止。
