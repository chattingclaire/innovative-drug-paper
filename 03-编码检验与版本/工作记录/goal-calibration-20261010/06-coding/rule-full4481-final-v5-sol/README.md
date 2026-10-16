# 最终 v5：原共同 4481 材料首次全域规则运行

本目录为 ROOT 明确授权的首次全域执行，算法为已封存 `joint-v5-primary-standard-bridge-sol`。五模块字节、候选 algorithm-bindings、pre-execution-seal、delivery-seal 通过执行绑定引用，不在本目录编辑或复制语义模块。

实际输入是 `full4481-common-v15-production-preparation-sol/packets` 的 4481 个原冻结 packet，按既有 `rule-full4481-v2-root` 顺序。入口逐项校验原 packet 的 canonical bundle SHA 与原共同 JSONL 一致，使用共同手册 5ea7ab74…、原提示与协议。未来 neutral projection 与 659 批候选计划均未采用，GO=false。

`rule_driver.py` 由旧 driver 机械适配：绑定最终算法及两个最终 seal；原 native packet 校验和读取；逐记录即时持久化预测、来源消费、技术失败与 execution-ledger。旧严格协议校验保持，所有首次失败保留，候选诊断不得代替 retained 标签。入口差异见 `rule-driver-vs-baseline.diff`；执行前入口绑定见 `pre-execution-run-seal.json`。

本次只运行一次，不读取主 LLM 部分标签，不读取或改变历史真人参照，不作新的政策语义开发阅读，不改变手册或阈值，NULL 不填 0。结束后 `summary.json`、变更表、待定和严格失败明细仅机械比较同输入不同规则版本；版本差异不是重复稳定性，也不代表正式效度或真人核验。

原运行、旧算法和全部材料保持不变。`run4481-first` 包含原严格 ledger 口径的完整结果；最终状态由该目录 execution/seal 记录，不由本说明预告。
