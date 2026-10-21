# v12 S/F 影响执行与结果接收候选

状态：准备完成、未发布、未执行。静态范围为 2082 条，余下 2399 条保留当前混合生产的实际原件和来源。只允许 S/F 改变，E/Ec/I 完整决定和原来源请求、已保存来源事件必须相等；不以标签或人工分数选择范围。此目录未创建实际 GO、采纳或分类结果。

## 最小模块清单

- `rule_driver.py`：原 v11/v16 一次运行入口的薄改版。保留原冻结、完整材料交付、source protocol prepare/check、真实事件防护、judge 循环和失败封存。新增 S/F 范围和已审核实现绑定；调用 `literal_inventory_bridge.py`，准确记录 v12 算法身份。逐项修改及可逆原字节/AST 证据见 `driver-transport-proof.json`。
- `literal_inventory_bridge.py`：在原 `source_receipts.resolve_inventory` 后补足显式来源中缺失的 literal inventory。只从冻结原文件、定位区间、结构化指针和文字 SHA 核验身份，保留原 inventory；不以读事件/标签/参考答案反推身份，不制造 READ 或 source event。
- `interface_common.py`、`status_bridge.py`：原入口完整副本。五个分类模块直接绑定冻结 v12 原件，未复制改写；原来源协议没有改写。
- `finalize_scope.py`：接收 ROOT 独立提供的实际原格式 release 及指定 SHA，核绑定后写新的 frozen scope；本组件不产生 release。
- `receive_merge.py`、`merge_common.py`：核验实际一次运行封存和完整输入，逐条比较后按原 predictions/slots/lineage/status/seal 格式合并。未选 2399 条逐字保留父结果；选中 2082 条登记真实 v12 运行来源。`merge_common.py` 复用既有字节处理函数。
- `check_transport.py`：16 项有限 NONHUMAN 运输/接收控制，全部通过。结果在 `transport-control-results.json`，不调用分类器。

## 已绑定输入

`execution-contract.json` 绑定当前 machine freeze、完整父规则输出及来源链、v16 材料、原冻结手册/提示/协议、v12 代码独审、2082 静态选择及原 01402 补 inventory 采用依据。

`affected-current-v16-common-lines.jsonl` 为当前 v16 完整源行的逐字子集，SHA `e9ffbf6554e1e095f27fe912f7617003be0633f0c3224315592403a3b2ef1625`。`packet-bindings.json` 对应相同顺序的 2082 个现行 native packet；`original-input-lineage-sidecar.json` 保留原行号、字节偏移和行 SHA。`algorithm-bindings.json` 绑定冻结 v12 五个模块。`preparation-bindings.json` 是本候选文件清单，不是运行许可。

`scope.UNRELEASED.json` 与 `release.UNRELEASED.json` 均不能启动分类。原 source base / v15 兼容描述保留原运输语义，实际当前 v16 来源、完整 packet manifest 和原 01402 材料变化另有明确绑定；本轮不修改当前 v16 材料。

## ROOT 审阅后执行

下列命令仅说明接续方法，本次没有执行。运行目录须不存在。ROOT 按 `release.UNRELEASED.json` 原格式提供实际 release，保留已绑定输入/实现/范围，填入真实授权身份和已发布状态；不要直接改写候选模板。

```sh
cd '/PROJECT_ROOT/outputs/goal-calibration-20261010/10-closure-20261012/rule-repair-v12/execution-preparation'
python3 finalize_scope.py --release '<ROOT实际release绝对路径>' --release-sha256 '<实际release SHA256>' --scope-out '<新frozen-scope绝对路径>'
python3 rule_driver.py --scope '<新frozen-scope绝对路径>' --scope-sha256 '<finalize_scope返回的SHA256>' --input "$PWD/affected-current-v16-common-lines.jsonl" --input-sha256 e9ffbf6554e1e095f27fe912f7617003be0633f0c3224315592403a3b2ef1625 --out '/PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding/rule-v12-sf-v16-affected-root/run-affected-first'
python3 receive_merge.py --scope '<同一个frozen-scope绝对路径>' --delta '/PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding/rule-v12-sf-v16-affected-root/run-affected-first' --output '/PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding/rule-full4481-v12-sf-v16-delta-merged-root'
```

需要只核接收而不写合并产物时，在最后一个命令添加 `--validate-only`。不得使用 Python `-O`。失败首轮按原 driver 留存，不重试覆盖原目录；此接收器只合并 2082 条完整成功且 10410 槽均保留的单次运行，不把技术失败改为 NULL。

## 不变项核对与来源身份

接收器对 E/Ec/I 同时比较完整 decision 字典和原 JSON token，而非只比较 0/1；核对五维 prediction/slot 一致、NULL 标志、技术失败、实际材料交付及 native packet SHA。原 `source_requests` / `material_requests` 完整相等；按当前 machine-freeze 绑定的实际来源日志逐条比较已保存 source event 组。S/F 关系轨迹的合法改变会列出，不强迫它们相等。

新 run ID、回执 ID、中立 inventory 身份补充、旧 recovery 注记属于运行来源元数据，不算新语义差异，也不要求逐字相等。旧 01402 的 29 项已保存事件按原实际快照核对；没有保存的旧 BODY/READ-0、scope_review 和辅助 effective unit 不可补称为历史实录。新一轮仍须通过原协议产生并核验自身 BODY、scope 和实际事件；selected 的旧来源只嵌入 superseded_parent_origin，不把旧缺失标记当成新执行事实。

准备阶段另只读检验了当前 01402 的 inventory：原 14 项完整保留、从冻结 literal 来源核出新增 5 项，共 19 项；没有调用 semantic_unit、RelationView、judge 或 protocol prepare/check，没有生成新事件或回执。此检查只证明中立身份桥可消费已知原件，不是一次新分类。

合并候选即使成功，也只表示本次规则 S/F 影响执行和兼容拼接通过；不自动采纳生产、不重跑 LLM、不生成正式独立准确性结论或开放论文验收。
