# Candidate03 单元隔离恢复 v2 接入准备

本目录只有准备结果。未读取 original03 部分标签，未运行模型、统计或 DOCX 成稿；真实完整执行核验尚未进行。

显式 profile：`LLM03_single_unit_reconciled_execution_v2`。方法 ID 为 `LLM-v32-candidate03-single-unit-reconciled-development`；统计键为 `LLM-candidate03-single-unit-reconciled`。只接收原批次 115 唯一终止失败、196 个原批次加 25 个单条请求构成的 4924 条完整输出。原 197 批协议继续记作技术不完整，不能称 197 批全通过。

先运行新 sealer，完整绑定、技术 QA、两段 QA、计划和 root 授权均满足后，才允许读取标签并按冻结 helper 复核真实请求、首个有效尝试、事件及完整逐行来源；此前退出 2，且不生成统计。所有旧入口及其 14 个冻结依赖 SHA 保持不变。

`精确执行计划_PENDING-v2.json` 保存未来三个顺序命令。两个实际 SHA 必须待真实输出闭合后填入，不自动选最新文件。统计仍使用原 5000 次固定设计、180 概率与 60 挑战分开；保留全部四格、κ/P/R/F1/NA、A/C 裁定前一致、同 180 注意力及部门差值。全量发现保留全部 10 对、6 个定义情景和 56 个文件/系列构成情景，各自计算，不扩成 336 个组合。

数值函数 AST 与旧冻结实现一致只说明公式代码保留，不等于新输出已通过。`preparation_QA.json` 仅报告 AST、帮助命令及真实 PENDING 拒绝检查，不含伪造 complete 自测。独立 payload checker 的数值公式保持与 adapter 分开，未来仍须实际独立核验。

文稿配置使用已给定 v4 stage/preflight 的路径和 SHA；新 adapter 本身从显式采用配置读取版本绑定，不硬编码 v3。31 个自动字段与 8 个 root 摘要字段仍须齐备，实际采用、独立 payload QA 和 DOCX 核验均另行执行。单独的稳定性实验不得由 02 或本准备状态替代。
