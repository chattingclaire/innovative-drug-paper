旧41逐维205格保持不变，预测文件与implementation03字节相同。旧36全部180格保留；首轮8个分歧格中7格改为一致，涉及4条，另1格Ec仍为FP；没有从原一致格产生新的分歧。两组指标分别报告，不合并为总体性能。

- RECODE25-01423 S: 0 → 1，原AI参照 1，FN → TP。
- RECODE25-01423 E: 0 → 1，原AI参照 1，FN → TP。
- RECODE25-01423 I: 0 → 1，原AI参照 1，FN → TP。
- RECODE25-03818 Ec: 1 → 1，原AI参照 0，FP → FP。
- RECODE25-04157 I: 0 → 1，原AI参照 1，FN → TP。
- RECODE25-04333 S: 0 → 1，原AI参照 1，FN → TP。
- RECODE25-04459 S: 0 → 1，原AI参照 1，FN → TP。
- RECODE25-04459 E: 0 → 1，原AI参照 1，FN → TP。

残留 RECODE25-03818 Ec 仍预测1、原AI参照0。实际trace为current/treatment_payment_content、context为空。只读检查冻结route exception发现“说明”匹配“药品说明书”复合名词，匹配片段为“支付范围与药品说明”。未改冻结代码、实际标签或参照；这不是新裁定。

此交付是已暴露旧材料开发回归，未来两条共同来源恢复需单独核验，不作材料充分性、人工信度或最终验收结论。
