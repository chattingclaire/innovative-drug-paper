# 全部 4481 条规则首轮执行准备

本目录目前只有准备实现、输入绑定和必要接入检查；未分类、未启动、未生成 ROOT release。最终算法身份已绑定 `joint-v15b-complete-repair-root`，最终 ROOT 审查及统一结果绑定仍由 ROOT 提供。4481 条全部实际执行，22405 槽，继承数为 0；不会生成或消费静态子集证明。

`prepare_static_inputs.py` 已机械核对全部 v17 原包与同序 common JSONL，生成 4481 包适配表及 4690 文件的联合材料清单。清单来自本次全部包的文档快照、全文载荷、资产、原文定位文件及包原件；只核身份与字节，不产生 READ/USE。比较基线为已完成 v13b 候选，其四份真实来源日志分别核对各自封印，不借用旧 v11 machine-freeze 身份。

## 最小改动

`rule_driver.py` 从成功 v13b 入口复制：只更换全框范围、最终算法 manifest 接入和实际 v15/v17 标识。`actual_reading_log`、原文叶完整性、有限原协议、异常审计、逐条执行、NULL/失败处理及 stop guard 均保留。4 个辅助文件逐字复用，证据在 `minimal-diff-proof.json`。

`receive_merge.py` 名称为接续兼容保留，实际直接接收全部新结果，无父结果继承。接收必须核实成功的真实 parent wait、全框一次运行、逐条来源与原协议回放、I 完整决定和 JSON token。S 变化仅允许已审有限标准内容/必要依赖，以及当前药物对象下的治疗获益和风险并列实质评价；其他 S 完整决定及 token 不变。接收原件中的旧请求和来源事件按原序保留，新增 E/Ec/F/S 必要依赖按明确维度核验；新增 READ 必须属于实际递送库存，USE 必须有真实 READ。

新增请求仅允许以下已审路径：`E_explicit_content_scope`、`S_finite_standard_scope`、`F_finite_standard_scope`、`F_requested_qualification_scope`，以及 `price_arrangement` 的 `finite_negotiation_definition_unresolved`。新合同不会把缺料传给 I，也不把合法 NULL 转为 0。完整接收会逐条保存标签/决定/轨迹变化以及来源追加记录。

## ROOT 后续一次接线

1. 完成本目录独审后，从 `release.UNRELEASED.json` 在本目录外建立真实 release。填入真实授权编号、`issuer="ROOT"`、状态 `released_for_production_provisional`、真实 `candidate_code_review`（ROOT 最终审查）和 `integrated_control_result` 绑定，并确认 `final_algorithm_and_controls_reviewed=true`。保留模板已列的算法 manifest、范围、材料、边界及实现绑定。模板不是授权；当前两个审查字段均为空。
2. 用 `finalize_scope.py --release <真实文件> --release-sha256 <真实SHA> --scope-out <新scope>` 独占生成实际 scope。该入口只从已有 ROOT release 派生，不创建 release。
3. 使用冻结 `/opt/homebrew/opt/python@3.14/bin/python3.14 -B`，在独立 session 中启动本目录 `actual-first-run-supervisor.py --scope <scope> --scope-sha256 <SHA>`。它会构造精确 driver argv，复用原 `wait_and_seal`，保存真实 `Popen.wait` 返回码。既有 run/wait 目录存在即拒绝；不自动重试或复位。
4. 完整终态后运行本目录 `receive_merge.py --scope <scope> --delta <实际run> --output <接收目录> --validate-only`。通过后使用相同命令去掉 `--validate-only`，独占保存接收候选。仅接收不等于生产采用或论文/真人验收。

实际 run、wait、接收目录均由 `execution-contract.json` 绑定。`delta` 参数名只兼容旧 CLI，本次必须是完整 4481 run。不要运行旧 `compare_v12.py`，其保护维度不适用于本轮。

## 当前验证范围

所有新 Python 文件语法检查通过。原 12 个 driver 辅助函数、原 stop guard AST 和 4 个辅助文件保持；已完成 E4/S/F 结果上的 56 项必要接收边界/维度路由检查通过，无新分类。空登记/无 release 入口已明确拒绝。未重跑 16 项旧运输控制、531 统一分类或 4481 总体。

`boundary-checks-attempt01.json` 保存完整实际检查结果。构造 driver 文件时曾因新目录表达式写错触发一次 FileNotFoundError，发生在创建文件之前；修正输出路径后生成成功，未影响来源、预期或任何实际执行。不存在被重置的规则尝试。

将来任何实际失败均保留原 run、wait 和封印；完整接收只接受技术失败为 0 的成功首轮，并保留所有合法 NULL。不改旧 v16、v13b、人工原表或既有稳定性运行。
