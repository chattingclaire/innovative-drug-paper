# 原发放200条 A/B 初判统计接入

`human_first_repaired.py` 只计算原发放200条的**协商前A/B人际一致性**。它复用旧 `human_first.reviewed_receive()` 的真实提交准入，以及后续封存 `handoff.initial_projection()` 的原件重读和已修复的总体ID解析。旧入口把 `ordered_source_ids` 文件绑定误当ID列表；旧文件和发放包保持原样。

必须先实际接收两位真人完整初判，并有引用用户实际确认及原件字节的复核文件。未填review会在打开标签、投影、分析及建立结果目录前拒绝。不得把模板、AI填写或合成控制当真实review。

入口保持原1444/3037历史域、120/80抽样配额、原权重和原统计引擎，使用5000次Rao–Wu、seed 20261010和single_category。**120条不被重新认证为当前版本未开发样本。** 本入口不生成裁定参照，不读取机器预测，不计算机器准确性或年度结果，不宣布项目验收。

真人交回 A/B 原件后，先用 `receive_originals_compatible.py` 接收（替换原件路径与尚不存在的接收子目录名称）。它复用封存 `receive.py` 的逐字复制、分配/模板/标准化检查和不覆盖规则，只在精确绑定的 reader 导入时补入 `posixpath`。实际输出仍在旧接收目录的新子目录内：

```sh
"/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/parallel-metrics/.venv/bin/python" -B \
  "/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/10-closure-20261012/human200-readiness/receive_originals_compatible.py" \
  --A /absolute/path/to/returned-A.xlsx \
  --B /absolute/path/to/returned-B.xlsx \
  --mode receive \
  --output-dir "/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/05-validation/human200-reception-root/actual-AB-initial-new"
```

报告与 seal 都增加 `runtime_compatibility`，如实绑定兼容入口、所复用的旧 receiver/reader 和标准库补入说明；原 `receiver_bindings` 字段仍保留，增强后的报告哈希进入原 seal 的文件清单。接收不认证真人身份或独立性，也不自动准入统计。临时 NONHUMAN 空提交与小表检查见 `receive-originals-compatibility-check.json`；未在项目接收目录创建任何假首交记录。

实际提交与复核完成后，再使用已核的项目统计环境运行以下 A/B 入口。`--receive-dir` 指向上一步接收目录，`--review` 指向实际执行证据复核；输出必须是本目录 `runs` 下尚不存在的新目录：

```sh
"/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/parallel-metrics/.venv/bin/python" -B \
  "/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/10-closure-20261012/human200-readiness/human_first_repaired.py" \
  --receive-dir /absolute/path/to/actual-human200-reception \
  --review /absolute/path/to/actual-AB-execution-review.json \
  --output-dir /absolute/path/to/human200-readiness/runs/actual-AB-initial
```

没有调用后续接入的完整 `contract()`，因为它涉及机器预测和机器材料；本入口只精确核验A/B投影、原手册/材料/抽样/总体ID元数据及原引擎所需绑定。成功时输出统计输入、A/B结果和来源封存记录，不覆盖旧结果。

当前完成未填review拒绝控制、元数据适配接口正路径核查和既有统计环境依赖导入检查，分别见 `unfilled-review-check.json`、`metadata-adapter-check.json`、`runtime-import-check.json`；未运行真人统计，也没有产生真人身份、标签、参照或执行确认。总体ID解析的已有核查见 `frame-reuse-check.json`。

另修复了封存 Excel reader 缺少 `posixpath` 导入导致相对 worksheet Target 报错的兼容问题：本入口在真实复核通过后的投影导入阶段，只给精确绑定的 reader 补入该标准库模块；封存文件未改。旧 `reviewed_receive()` 不解析 Excel，因此没有改它。三个内存 NONHUMAN 表验证绝对、相对及规范化相对路径读取结果一致，并保留外部路径和越界路径拒绝；未填 review 仍在标签读取、投影和结果目录建立前拒绝。证据见 `xlsx-relative-target-compatibility-check.json`，该记录绑定修复后的入口；此前检查保留其原版本绑定。
