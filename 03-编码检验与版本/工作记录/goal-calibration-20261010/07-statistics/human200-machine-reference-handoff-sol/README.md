本目录补齐旧冻结 200 条的 `machine_reference`、`combined` 和年度接入候选。制作者为非真人 AI（GPT-6.1 Sol ultra）；没有生成真人初判、真人裁定、主 LLM 标签、真实指标或正式验收。实际真人参照接收、完整主 LLM 接收和实际统计运行均为 0。旧 S/E/Ec v2 仍保持封存，本目录不修改其代码。

接入保留原 200 IDs、原 A/B 盲号、41 层、120/80 配额、1444/3037 历史域、N_h/n_h、精确 pi/权重以及冻结手册 5ea7ab74…。主 LLM 接口绑定 `native-full4481-v1-sol` 原 run-manifest 及其 approved_record_ids.json 原字节。规则只准使用 `rule-full4481-v2-root/run4481-first` 已封存原首答、冻结代码与 release。本目录不重新推断标签，也不在候选输出中择优。

ROOT 后续曝光台账指出：328 项语义复审与旧 200 相交 63 条，其中历史 remaining 29 条已用于开发。按既定文本家族闭合后的未来池为 remaining1261/exposed3220，仍是准备范围，尚无新抽样或冻结契约。旧 200 只允许描述原冻结版本的历史快照；程序在任何标签接入前拒绝更换规则版本、预测绑定、抽样/材料、域或用途。不能将旧 remaining 当更新后规则的独立验证。原域和原权重不随台账追溯改写。

可执行入口为 `handoff.py validate` / `handoff.py analyze`；`--stage machine_reference|combined`，加 `--annual` 启用年份。必须提供实际真人接收目录、实际 ROOT 复核文件和本目录下尚不存在的新输出目录。例如（所有 UNFILLED 模板均会拒绝，不能当实际复核）：

```bash
python3 handoff.py validate --stage combined --annual \
  --receive-dir /absolute/path/to/actual-human200-reception \
  --review /absolute/path/to/actual-reviewed-reference-and-complete-machine.json \
  --output-dir /absolute/path/to/this-handoff/new-run
```

`review.UNFILLED.template.json` 保留未确认身份、未确认执行、未确认遮盲及原件绑定。参考原件 `reference-original.UNFILLED.template.jsonl` 有 200 个 R 盲号、1000 个未填维度，`value:null` 配 `unfilled`，不会被当合法 NULL。R 与源 ID 的映射仅给协调者；不要把包含机器绑定的 review 或机器接收 inventory 发给真人裁定者。真人应基于同版材料独立实际裁定每条；A/B 一致也不自动成为参照。实际复核需引用直接真人执行确认、A/B 原字节、裁定原字节、真人身份、共用手册/材料及机器遮蔽证据。JSON 布尔值和 SHA 仅绑定所审证据，不能自行认证真人；这些事实须由实际用户及 ROOT 核定，本目录未填任何确认。

A/B 准入仍直接调用冻结 `human_first.reviewed_receive`，要求真正 `receive` 接收而非 dry-run、原件存档 SHA、一致的规范派生和原1000槽完成情况。新目录按同一冻结 `bound_xlsx_reader.inspect` 重读 A/B 原件，不改初判。这里修正一项已实际暴露的接入错误：旧 `human_first.project_records` 把 manifest 的 `ordered_source_ids` 三键绑定当成4481列表；实际须先精确核 path/bytes/SHA，再读取 wrapper 中的 `approved_record_ids`，核4481唯一、原 UTF8/LF 顺序 SHA、504批同一顺序。旧 human_first 文件保持不变，准备前两次结构失败均另存。

完整机器接入必须先有实际 ROOT 完整终止复核和 `LLM-complete-terminal-inventory`（504批/4481条）；模板未填。接收按冻结 whole-batch 最早技术有效选择核原 selection、每次原接收器、原 first.json/报告/actor seal、原字节镜像及冻结 validator。先核所有504批终止身份/原件，再打开有效批的标签；不能读取运行中的部分标签，不能跨尝试拼条、跳过更早有效答或按参照挑输出。三次技术失败保留 whole-method failure；实际已终止未返保留 missing return，并绑定 ROOT 终止证据及已有失败。所有这些真实机器分支尚未执行；没有声称已经接收到主 LLM 全批。

0/1 只能为 JSON 整数，拒绝 bool、字符串、NaN；合法 NULL 需要实际真人未定理由与身份。整项未返、整项失败、维度失败与语义 NULL 分开保存。现 engine 不支持“同一已返回参照行的个别维度未返”独立原因；遇到该原始状态保留原件并拒绝计算，不悄悄转成0、NULL或维度失败。A/B 原接收若不完整或违法也仍拒绝，不绕过已注册接收契约。

年度由已接收的全4481源年主图和原公开年图精确投影到旧200，保留来源条目身份、日期依据 SHA、来源组、issue/publication日期、待核 component_id:null 及原抽样字段。未读或复用 selected800 year map。`old200-source-year-projection.jsonl` 为200条，未知年份0；这是日期元数据接入，未重新审阅日期语义，也不是年度政策结果。2017等无来源声明继承冻结全框证据，不能由200样本缺项推断；附件独立年份仍未接入。

统计直接调用已审定域引擎 SHA05f599…；年度调用已独审修复候选引擎 SHAf6b334…，不改任何 engine。每次实际 analyze 固定5000 Rao–Wu、seed20261010、single_category，原始与设计加权四格、NULL/失败16状态、机器行/参照列方向和年度掩码均交给原引擎。每次 analyze 只生成一次完整权重矩阵 W，全部方法/维度/域/年度共用；不以年度重抽、不重分层，不把数值目标达成称正式验收。新动态域/新draw/材料freeze需要新注册契约和引擎范围复核，另列 `remaining-dependencies.json`；本接入始终保留拒绝。

验证范围见 `control-results-final.json` 和 `cli-blank-control-results.json`：30项先固定合成/空白控制通过；8次实际CLI空白入口均在读取标签前拒绝且未建结果目录。第一次30例控制有2个测试对既有输出键名误读，28通过/2失败原记录保留；修正只改测试读取键，第二次及最终30通过。共3轮合成统计测试、每轮4次小型 toy analyze（每次5000同W），未运行任何200真人统计。控制包含错误版本/域、AI或一致代参照、未遮盲、504中一批未终止/503部分批、合法NULL/未返/失败及精确方向。还核400人用材料原字节与全框对象一致、200主LLM冻结输入包原字节与对象一致、200规则实际交付源对象一致；这是身份/材料绑定验证，不声称400次真人阅读。

`bindings.json`、`common-material-identity-receipt.json`、`preparation-readback.json` 保留输入与覆盖；`output-seal.json` 和 `seal-readback.json` 覆盖本目录完整产物。当前实际结果为0，未称通过正式验收或增加真人工作量。
