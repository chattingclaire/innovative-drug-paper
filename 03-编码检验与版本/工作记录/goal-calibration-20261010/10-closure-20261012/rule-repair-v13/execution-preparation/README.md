# v13b 最小执行准备

状态：准备完成，未授权、未运行、未采用。父生产仍为 v11/v16 混合来源。已绑定 ROOT 最终候选审查 `../final-independent-review.json`（SHA 7ae6711aac909a363e30d04d07ef23841d621e7edcd083e7187ccf924ac0fcee），该审查不构成运行 release。

沿用原 2082 条静态清单及实际成功 v12 运行的完整源、packet 顺序和身份；2399 条继续继承原生产实际来源。原 v12 排除证明仍保留原版本身份，本次范围沿用依据是上述新审查。没有重建 selector、生成新的成员清单或重新编码材料。

## 相对 v12 的最小改动

- `rule_driver.py` 只改说明、运行版本、实际算法身份和 `freeze.semantic_change`。原 `source_reading_protocol_v12.py`、`source_only_interface_v12`、`v12_source_base` 及其完整协议行为保留。
- `receive_merge.py` 只改输出算法身份文字，其逐条接收条件、来源核验及合并逻辑不变。相对 v11 仅允许 S/F 变化，E/Ec/I 完整决定和原 JSON token 必须相同，source requests / material requests / 原已保存 source events 必须相同。
- `interface_common.py`、`status_bridge.py`、`literal_inventory_bridge.py`、`merge_common.py`、`finalize_scope.py` 均逐字复用。
- `algorithm-bindings.json` 绑定冻结 `joint-v13b-clinical-safety-role-root` 五模块；执行契约、scope 和 release 模板仅重绑定必要路径、实现和新审查。
- `compare_v12.py` 是唯一新增的结果核对入口：完成全部 4481 条合并后，与已封存 v12 合并逐条比较 E/Ec/I/F 的标签、完整决定和原 JSON token，差异只允许在 S。它不分类、不改结果、不采用候选。

具体逐字替换及可逆字节/AST证明见 `path-rebinding-proof.json`。语法、12 项实际实现绑定、原 scope 静态绑定和未授权状态已核验。原 16 项运输控制复用其既有封存通过结果，本轮没有重跑。候选353项对照及有限独审在上级目录，不将它们称为本次总体执行。

## 材料与来源

直接复用原源文件：`/PROJECT_ROOT/outputs/goal-calibration-20261010/10-closure-20261012/rule-repair-v12/execution-preparation/affected-current-v16-common-lines.jsonl`，SHA e9ffbf6554e1e095f27fe912f7617003be0633f0c3224315592403a3b2ef1625。

本目录 `packet-bindings.json` 和 `original-input-lineage-sidecar.json` 是原文件逐字副本，源数据文件没有重新生成。旧 scope 内 v12 来源协议名、历史 v15 描述及旧中间身份均保留其原契约意义；实际材料仍由当前 v16 绑定核验。01402 继续使用原中立 literal inventory bridge 和现行 packet；旧29项事件和新协议 BODY 的层级不变，旧 recovery 不冒称本轮真实读取。

## ROOT 审阅并另行 release 后执行

以下命令仅供 ROOT 接续；本次没有执行。运行目录与合并目录须不存在。ROOT 另行提供与模板绑定相同的原格式实际 release，填写真实授权身份。不得直接改写模板，不得使用 Python `-O`。

```sh
cd '/PROJECT_ROOT/outputs/goal-calibration-20261010/10-closure-20261012/rule-repair-v13/execution-preparation'
python3 finalize_scope.py --release '<ROOT实际release绝对路径>' --release-sha256 '<实际release SHA256>' --scope-out '<新frozen-scope绝对路径>'
python3 rule_driver.py --scope '<新frozen-scope绝对路径>' --scope-sha256 '<finalize_scope返回的SHA256>' --input '/PROJECT_ROOT/outputs/goal-calibration-20261010/10-closure-20261012/rule-repair-v12/execution-preparation/affected-current-v16-common-lines.jsonl' --input-sha256 e9ffbf6554e1e095f27fe912f7617003be0633f0c3224315592403a3b2ef1625 --out '/PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding/rule-v13b-sf-v16-affected-root/run-affected-first'
python3 receive_merge.py --scope '<同一个frozen-scope绝对路径>' --delta '/PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding/rule-v13b-sf-v16-affected-root/run-affected-first' --output '/PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding/rule-full4481-v13b-sf-v16-delta-merged-root'
python3 compare_v12.py --candidate-composite '/PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding/rule-full4481-v13b-sf-v16-delta-merged-root' --output '/PROJECT_ROOT/outputs/goal-calibration-20261010/10-closure-20261012/rule-repair-v13/v13b-vs-completed-v12-comparison.json'
```

接收器可先加 `--validate-only` 只核验。仅完整2082条/10410槽、技术失败为0、实际首轮封存成功才可合并；失败原件保留，不改为NULL、不覆盖重试。最后一步独占创建比较结果，遇非S完整决定差异立即拒绝，不改写已完成的合并或原 v12 结果。

合并和比较通过仍不自动采用生产，不触发 LLM、不更新曝光或正式统计，也不开放论文验收。
