# H0041 数组证据指针越界：隔离兼容候选

本候选无运行、接收或重试授权。它只在内存中包装冻结校验器的 `pointer_value`：原函数仍先执行；仅当真实内置 JSON 数组的合法非负索引越界造成 `IndexError` 时，转换为原接收器已有的 `ValueError` 技术无效路径。合法返回值、缺失键、非法索引、类型错误、原断言及其他 `IndexError` 保持原语义。

`verification.json` 保存 H0041 原始首答的只读复现、边界回归及所有绑定文件检查前后的哈希。实际首答引用 `contexts/11/title`，该数组只有 10 项；候选不会修正引用、标签或答案，也不会改变任何冻结源文件。

候选 API：`load_readonly_validator()` 仅供纯校验；`wrap_receiver_module_loader(original_loader)` 供 ROOT 独立审核后在新的兼容入口内替换 `receiver.module`。该 hook 先调用原加载器并保留原绑定检查，只对 `unchanged_production_validator_capture` 名称及精确绑定的原校验器包装函数。没有接收器或调度器的执行入口。

恢复条件：ROOT 独立审阅并另行决定采用；原控制器、该批和有关子进程均已真实终态；重新核验 seal、manifest、冻结实现及 H0041 原件；纳入与原授权兼容的新入口。然后由原控制器重新接收已经存在的 attempt-0001，保留其技术无效记录，再由原最多三次尝试流程决定是否调用后续尝试。不得重复 attempt-0001、手改首答、重置计数、跳过更早尝试、接收有效结果后重跑或把技术失败混作语义不一致。

纯验证命令：使用冻结 Python 3.14，以 `-B` 运行本目录的 `verify_candidate.py`；仅向标准输出打印结果。
