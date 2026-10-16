# 真人核定范围补充

原49项复审和原封存保持不变。`reviews-scoped.json` / `.jsonl` 保留相同语义值、理由、引文及原AI/规则出处；将原先笼统的真人待验证标记保存在 `legacy_human_review_scope` 中，另列 `formal_reference_validation_pending=true`。新 `needs_human_review` 只表示本次条目级定向核定。

定向清单仅2项：A-000347 / RECODE25-00202 拟将原AI 1改为0；A-000704 / RECODE25-00241 属未定PK-PD边界，保留null。没有另列缺材项。其余47项不因为AI审查尚非真人金标准而自动变成新增真人校准任务；原有正式独立编码/裁定流程仍待实际完成。

44项规则遗漏和3项规则过度纳入仍是可供规则法技术核查的AI审查候选，本补充不修改规则、原AI值或正式标签，也不改变任何E判断。
