# 77条事后核验 XLSX 只读接收

入口为本目录的 `intake.py`，仅使用 Python 标准库 zip/XML。它读取指定 A/B 保存文件，复制原输入字节到新 capture 目录，输出 `capture-proof.json` 与该次 `seal.json`，不写回工作簿、不计算指标、不调用正式 human_receiver、不生成新的编码判定。

已收到本轮真人事后核验报告。`baseline-binding.json` 绑定 ROOT 的结构化接收记录 `logs/user-human-review-report-received-20261010.json` 与应用回执 `logs/human-feedback-review-delivery/applied-human-feedback-receipt.json`；前者是 ROOT 转录/接收，不是原始逐字聊天导出。角色为 `AI_seeded_posthoc_review`，独立真人初判为否。用户未决为 03415 E；00036/00038/00045 S 是 ROOT 新增的源证据问题。不得因用户没有直接改原 XLSX，再要求重核同一轮77条；本接收器也不推定全部385个维度已逐一真人检查或认证77条 human gold。

冻结基线为 ROOT 保存两处 S 修改及补材后的 A/B 文件，字节 SHA 均须与应用回执一致。原手册、原 review-rows JSON 仅作路径/字节/SHA 绑定。每次输入通过编号与维度对齐基线，检查385行、77编号、每编号 S/E/Ec/I/F 各一次。编码表 A 列编号、B 列部门、C 列维度、D 列编码值、E 列理由、F 列该轮判读原句、G 列判断版本、H 列完整语境位置；并对比“原文语境”全部已保存文本单元格。

numeric 0/1 和 string 0/1 均可读取，明确“待定”保留为 pending。空白、待定、非法值分别列出，解析值均为 null，不能补0。公式编码值、布尔值、其他数值/文本列为非法。缺理由及待定无理由另列。编号/维度缺失、重复、集合变化与行位置变动均指出；原文、版本、部门、语境、表头、工作表顺序等 D/E 之外改动另列，不能隐藏为仅改标签。

每次 `--out` 必须是新建或空目录；已有任何文件即拒绝，不覆盖。不能输出到09-delivery或冻结基线目录。仅需将用户已保存的 A/B 路径传入，不要求新增列、身份注册或重复人工任务：

```sh
python3 -B intake.py --a '/absolute/path/A.xlsx' --b '/absolute/path/B.xlsx' --out '/absolute/path/new-empty-capture'
```

八个有限内存控制可用 `python3 -B intake.py --self-test` 重读；不写 XLSX。当前文件一次只读 smoke 已完成：A/B 各385行、385唯一组合、77编号；D列各385个binary，无空白/待定/非法值，E列无空理由。与已交付基线的标签、理由、编号、维度、原文、版本、语境、顺序及表头差异均为0，输入文件在捕获结束时 SHA 未变。八个内存控制全部通过：numeric 0、numeric 1、string 0、string 1、空白、待定、非法值、重复编号×维度；没有构造或写入控制 XLSX。

实际 capture proof 位于 `current-read-only-smoke-capture/capture-proof.json`，SHA-256 为 `91adca98bcc8acd17f317ef4fb04297ee5ac7f438c85c83f621a22878d300e65`；该目录保存两份原输入字节快照和独立 capture seal。冻结 baseline binding 的 SHA-256 为 `71579292c404c6ce63b5628a20632c3106138f8468bb41cef474b57111c65cea`，代码内固定核对，不从可变09-delivery文件重建基线。捕获仅证明指定文件的保存字节、结构及实际差异，无法从 A/B 文件名证明两名真人或协商前独立初判；不输出 κ 或协商前/后指标。
