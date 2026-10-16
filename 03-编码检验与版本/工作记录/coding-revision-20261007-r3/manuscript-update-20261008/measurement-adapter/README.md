# 数值接入器：准备版，尚未进行真实采用组装

`assemble_manuscript_payload_r3.py` 只读已核定文件，输出 JSON，不生成或修改 DOCX，不调用模型，也不计算新 bootstrap。当前配置没有采用任何规则或 LLM 方法；只运行了 PENDING 失败门禁与合成算术检查。

先由 root 复制 `采用方法_PENDING.json` 为另一个真实采用文件，明确填写方法ID、实际输出、执行绑定、统计方法键/冻结ID、同版完整统计及冻结清单、A/C统计和8项摘要绑定。不得自动选择最新文件或最高κ。`实际schema核对.json` 记录所读实际schema；`payload_schema_contract.json` 给出与DOCX编辑器约定的键。

- 31自动字段：15规则q百分数、8个Ec/联合计数、4个P(F|Ec)百分数、15部门配对方向一致项数、5维A/C κ合并字段、2个采用ID。
- 8项解释摘要用 `八项解释摘要_PENDING.json` 另行明确提供；每项绑定实际采用输出SHA和依据文件。此文件绑定测量输入，不反向绑定采用文件，避免相互文件哈希形成循环。
- 所有概率指标严格取同180的 ALL / eligible_design_weighted；逐项用精确四格复核点值。表2含80个点和同记录的80个主CI；CI须为5000次 department_unit_rescaled_SRSWOR。来源文件条件重采样CI不能替代主CI。
- 全量两方法必须各4924条、五维完整二元。4481部门归属从冻结metadata核验；443条GOV排除。表3/图2每行q使用精确分数，五维和严格为1；显示百分比四舍五入后不强行补齐100。
- 15方向按精确q差的符号比较：两个精确零为一致，一个零和非零为不一致。全部15项保留。
- 零分母保留NA及原因；未填字段、输入/版本/SHA不符、固定正文方向不成立或摘要新增未映射引用均停止。

未来真实第一次组装：

```sh
python3 assemble_manuscript_payload_r3.py --adoption /绝对路径/真实采用绑定.json --out /绝对路径/新的待复核目录
```

所有输入与摘要满足门槛后，可产生 `manuscript_measurement_payload.json`，状态为 `assembled_pending_independent_QA`，退出码仍为2。它仅供独立数字核验，作者脚本必须拒绝此状态。独立核验者按 `独立数值QA_PENDING模板.json` 核对真实payload，绑定采用文件SHA、本脚本SHA、payload_content_sha256及自己的审计脚本；不得直接把模板状态改为PASS充数。

复核完成后，以完全相同采用文件再次运行，另给真实QA路径和SHA：

```sh
python3 assemble_manuscript_payload_r3.py --adoption /绝对路径/真实采用绑定.json --independent-qa /绝对路径/真实独立QA.json --independent-qa-sha256 实际64位SHA --out /绝对路径/新的已复核目录
```

全部通过才输出 `ready_for_authoring` 和退出码0；仍不是已生成或已渲染的论文。引用交由作者脚本按已绑定v3清单处理，adapter不重新排号。input_bindings包含采用文件、52段、v3报告/冻结/引用/OOXML清单、数据/统计/执行/参考/抽样，以及独立QA及其脚本。

`--check-only` 检查但不写payload。当前演示 `pending-gate-demo/gate_report.json` 返回2，列出39待填字段，打开预测/统计文件数为0。`preparation_QA.json` 的20项检查仅是准备阶段合成算术和失败门禁测试，不是实际全量统计或独立效度验证。

支持的明确执行profile：`rules_development_candidate`、`rules33_confirmed_execution`、`LLM03_full_execution`、`LLM02_reconciled_execution`。03执行ID与统计历史ID可不同，必须在配置中分别明确，且绑定同一输出SHA。03不能继承02的CI或稳定性结论；敏感性和稳定性文字由root绑定03实际依据后提供。
