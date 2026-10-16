# candidate04 外层排版表格结构审查

2026-10-09；并行代码审查 AI。此为有界实现审查与构造自测，不是盲审、真实材料效度检验或人工金标准评价。

范围：只阅读 candidate04 的 `runtime/common_reference_resolution03.py` 和授权自测 `runtime/selftest_common_reference03.py`；执行自测时由其导入必要依赖。没有重新读取真实政策材料、实际输入、已有标签、结果或分数，没有运行 01432/02086 或 33 条回归，没有修改运行代码。仅新建本审查记录。

静态结论：当前实现符合“稳定外部布局可接受，条内表格结构不能认证为款”的预期。每次开启 table/td/th 都产生唯一序号；每个 p 记录开启时的完整祖先序列。全条各 p 及下一条边界 p 必须具有同一祖先序列，因此不同单元格即使标签名相同也不能混同。条文区间内新开启的 table 和条文 p 内的 table/td/th 开闭变化另行拒绝。外层布局表格在条文开始前已开启、持续覆盖全条及下一条边界，不会仅因存在 table 祖先而被拒绝。

现有来源约束继续存在：JSON 绑定原 HTML 散列；当前完整条文与实际 p 数量、顺序和规范化正文逐段相等；款序有效；完整引用区间认证；不从递归引用的第五条选择上下文。外层布局修复没有放宽这些条件。

执行结果：bundled Python `/Users/rainbow/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B` 运行授权 `selftest_common_reference03.py`，9 个结构检查、3 个 E 边界检查、3 个支付前提检查全部通过。结构夹具含来源散列绑定的临时 HTML/JSON：稳定 layout table 接受，条内 table p 反例拒绝，跨 td 反例拒绝；真实输入执行数为 0。临时夹具由自测自动清理，未新增政策样本。

root 已报告实际网页的第七条、两款与下一条处于稳定三层外部 table。该真实来源诊断仅作为本次任务背景，本审查未重新打开真实网页，也未据此宣称 candidate04 的实际回归已经成功；后续冻结与 33 条回归由 root 执行。此前 candidate03 审查与结果保留。

结论：本次限定范围内未发现阻碍冻结 candidate04 的实现问题。该认证依据显式 HTML 标签结构，并不提供通用浏览器 DOM 修复或所有法规版式的解析保证。

执行前后代码快照一致：

- `common_reference_resolution03.py` SHA256：`89f7bd189d841da58018810506bbc6a25a0452378c35c91a02687a7a4be0a5e9`。
- `selftest_common_reference03.py` SHA256：`502f57adff1b36f3654426ac6079468d11ef6d8d79c86d305729fcda040e5122`。
- 38 个 runtime `.py` 合并 SHA256：`29b02d5d9be81e105a5a1532ac1dace3c3d3ec3e01d8d4546c11e53c4d1f96bf`；按文件名排序，逐项拼接 `filename + NUL + bytes + NUL` 后计算。
