# 全新人工原件接线候选：未采用，真实登记仍为空

`project_humans.py` 只把未来唯一实际抽样所对应的原件投影为动态统计引擎所需的记录片段。它没有采样器，不计算一致性或准确率，不生成 `sealed_project` 元数据，不登记范围或认证真人身份。原1261/旧91入口、原Excel解析器和统计核心均未修改。

复用的原函数及其字节SHA固定在代码 `PINS`：A/B使用 `statistics-handoff/dynamic_xlsx_projection.project_dynamic_xlsx` 和原 `bound_xlsx_reader.normalize`；裁定使用原 `human200-machine-reference-handoff-sol/handoff.reference_output`；真实模式先调用原动态引擎的 `scope_admission.registry_entry` 与 `validate_registration`。不调用旧200人的 `inspect`，不导入或执行统计引擎。

## 最小接口

请求为 `all-new-human-projection-v1`，包含 `synthetic_only`、已批准的 `scope`、`blind_assignment_binding` 和 `sources`。实际请求中的 `scope` 仍须由现有动态登记表批准为 `registered_remaining_pool`；当前空登记在打开盲号表或任何真人原件前拒绝。所有文件绑定都必须是绝对路径、字节数与SHA256。

盲号表包含原 `draw_binding`、`common_materials_binding`、`inherited_human_N: 0` 和每种方法的固定行。每行只接受 `unit_id`、`original_blind_id`、`source_bundle_sha256`、`material_locator`，严格保持原draw全部ID与次序；材料SHA与登记的完整材料身份表一致。A/B表中每个B列材料位置还须与这张表逐条一致，不能仅靠材料位置非空通过。

`sources`可分阶段提供：先仅 `A`、`B`；之后仅 `reference`；或三份原件均收到后同时提供。冻结盲号表可预先包含全部三种方法，首阶段不会因此要求裁定原件已经存在。每阶段都保留完整原draw成员、盲号和材料映射，不重新编号或按收到的行排序。

- A/B各自提供 `format: frozen_dynamic_xlsx`、`raw_binding`、`template_binding`。原件须为发放的完整五维表；无文件、缺身份行或身份错配拒绝，不拿空模板冒充未交原件。
- 裁定提供单独的 `format: blind_five_slot_jsonl_v1` 与 `raw_binding`，五维显式保留值和状态、合法NULL理由、失败证据和真人身份。不得从A/B一致或AI生成裁定。
- 真实身份只读取已绑定的ROOT接收记录；请求本身不能自填独立性。TOY专用 `identity_code` 不可用于真实模式。

输出 `records` 为 `unit_id/stratum_id/department/outputs`，按原draw顺序排列；每方法另保留原件绑定、逐槽完成状态及按来源ID排序的 `joined_projection_sha256`。A/B二元值、合法NULL、部分未完成均沿用原解析；五维全部未填写输出 `None`，证明链仍保留原始 `unfilled/incomplete`，不声称原件没有收到。裁定整条 `execution_failure` 与 `not_returned` 分别投影为失败对象与 `None`。缺失/失败不转成0或合法NULL，不删分配行。

动态引擎未来 `input_seals[method].sha256` 必须使用**原件字节SHA**，不能用证明链SHA替代；本候选在 `original_bytes_sha256_for_future_input_seal` 明确提供该来源，但不自动设置 `sealed` 或任何真人证据标志。

## 原件接收与投影审定分开

为避免“先有投影哈希才能投影”的循环，本薄层接受现有登记条目所绑定的两种接收记录状态，不新建登记系统：

1. `ROOT_reviewed_actual_method_source_for_projection`：ROOT已独立审查真实身份、原始首交字节、盲法/时序以及原draw、手册、材料、发放模板和盲号映射；`joined_projection_sha256`必须尚为空。薄层只据此读取对应原件，生成待审记录片段及哈希。
2. ROOT独立核对原件与投影后，才能另行封存原生的 `ROOT_reviewed_actual_method_submission` 最终接收记录及登记版本，绑定真实投影SHA。薄层在这一状态下会复核其SHA一致。

两种记录均通过现有登记的 `admitted_submission_receipts` 绑定；前一种只是原件读取接收阶段，**原生统计 `admit` 仍因状态不是最终 `ROOT_reviewed_actual_method_submission` 而拒绝**。没有修改原引擎放宽这个要求。薄层还要求接收记录绑定 `blind_assignment_binding`；A/B另绑定 `issued_template_binding`。这些是原件映射核对字段，生成哈希不能替代真人独立性、机器盲法或真实裁定证据。

本轮没有上述真实接收记录、实际抽样或登记采用。独立原件接收、投影审定、最终登记以及后续同版机器记录拼接仍需真实工作与外部审查；这里只交付可审阅的薄层，不能声称全链条已准入。先A/B后裁定的记录片段不会自动合并成统计输入或执行A/B一致性分析。

## 有限检查与执行边界

`check_toy.py`使用3条完全虚构来源，8项检查已通过：零继承且先A/B后裁定的映射、二元/合法NULL/部分空白/整条空白/显式失败保留；重复来源ID、重复盲号、错误来源ID、材料SHA错配、材料位置错配、裁定盲号错配拒绝；空真实登记在读取原件前拒绝。结果为 `toy-check-results.json`，夹具及一次投影片段在 `controls/TOY-01/`。这不是实际抽样、真人答案或统计结果；未重跑旧套件。

准备接线不取决于200条工作量是否获确认，也不触发人审、24条接续或任何全量任务。实际运行仍须符合原范围、材料与身份接收条件，不能以此候选替代1151范围准入或4481项目目标。
