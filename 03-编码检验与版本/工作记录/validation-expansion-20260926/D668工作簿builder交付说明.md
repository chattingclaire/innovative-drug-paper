# D668 两份工作簿的统一 builder

`build_reviews_d668.mjs` 是一份独立 builder，使用 bundled Node 和 `@oai/artifact-tool` 创作；`openpyxl` 仅用于保存后的只读核验。没有修改旧 V600 builder、20份冻结输入、统计方法或报告呈现器。

本轮仅完成代码、schema对照和内存合成准备。没有打开真实D668材料或标签，没有导入artifact-tool、运行marker、创作、渲染或导出工作簿。最终合成QA为 `D668-workbook-builder-synthetic-QA-complete.json`，19种错误情况均被拒绝。

## 未来输入与输出

输入必须是完成后的新归档：`status=completed_supplementary_AI_content_analysis_not_human_validation`、`phase=R600_plus_D668`。直接读取 `archive.raw_coder_submissions.D`、`archive.original_submission_manifest.D`，不会伪造V600字段或使用机器、规范化、共识标签替代首次原始提交。

builder同时要求两名AI各27批、668个分析单元完整，并确认主归档具有R48份和D54份清单、1268唯一单位的统计元数据及完整统计表数目。冻结文件必须为D668精确20项，外部提供的冻结SHA须与实际文件一致。D封存61份发布文件（54材料包、6份共同文档副本、1映射）、54份原始提交、54份首次接收及54份record逐一核验。R目录和机器预测文件不另行读取。

固定输出：

- `D668工作簿交付/补充内容编码668-A-AI评审.xlsx`
- `D668工作簿交付/补充内容编码668-C-AI评审.xlsx`

四个页签为“独立盲评”“原文语境”“共同手册”“执行说明”。这是首次提交的可读导出。**统计与原始编码以封存JSON为准；在工作簿中的编辑不改写首次提交或统计输入。**

主表用“668个分析单元”，显示分块行数另外列出。续行按编号和块序关联，不增加分析单元数；五维标签仅在每个编号的首块显示。两份文件分别保留各自的原标签、逐维理由、证据、子型、材料状态、完整原文及核验语境，三份共同文档逐字保留。明确标识AI执行、补充内容分析和“不是新验证”。

## 原始字段和来源可重构性

原文语境页按编号、转义后的字段路径、类型、块序/总块数存放全部字段。非空数组与对象也保留容器类型标记，使数字键对象、数组、null、空容器及嵌套结构可以区分。源材料和首次提交的原始行顺序另存为 `row_id_order`；按ID关联呈现，不覆盖原顺序。准备阶段完整重建每名AI的27份材料包和27份原始提交，并与原对象比较。

字符串日期、数值样文本、公式样文本与前导单引号使用可核对的文本转义；数值0和null不混同。长文本按Unicode字符和显示高度分块，逐字符拼接必须等于原值。字段值重构不等于重建原JSON字节排版：原始空白、数值词法与字节序以封存首次文件及SHA为准。

每份未来QA记录主结果JSON、冻结、封存、材料、首次提交、首次接收record和builder的哈希。实际输入在准备后与导出前后复查；目标文件、partial、QA和预览均拒绝覆盖。XLSX只读QA检查全单元格值、类型、全部原字段分块重构、公式/错误单元格为0、表范围、冻结窗格与行高限制。

## 已对照的真实源码 schema

仅阅读了冻结统计/桥接/接收源码及冻结元数据，没有读取实际标签：

- `d668_analysis_bridge.py` 的 `archive.freeze_original`、`release_seal_original`、`D_mapping_original`、`ID_join_provenance` 和D分组原始提交/清单字段匹配。
- `original_submission_manifest.D[相对结果路径]` 只有 `sha256` 与 `byte_count`；builder没有假设旧V600的 `ids`、`coder` 或 `input_packet_sha256` 清单字段。后两者从首次文档直接核验。
- `input_snapshot_hashes` 是绝对路径→SHA的平面映射；builder对实际freeze、seal、61份发布文件、54份原始提交、首次接收binding/raw/record使用该结构，未使用旧V600嵌套snapshot格式。
- 首次record为 `receipt-records/agent-X/结果-NN.json`；核对 `file`、`sha256`、`byte_count` 和 `binding`。binding的六个字段与 `d668_receive.py` 一致。
- `d668_statistics.py` 的 `metadata.unique_sample_units=1268`、`ai_codings_per_unit=2`、方法版本和输出行数120/40/30/10/60/30/290匹配。工作簿不重新计算这些结果。

## 实际运行命令

仅在全部首次原始提交已封存、真实主统计JSON完成后执行。首次实际author前，由主任务运行下列marker**恰好一次**，预期输出是两份xlsx。本轮没有运行它。

```sh
/LOCAL_HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node \
  /LOCAL_HOME/.codex/plugins/cache/openai-primary-runtime/spreadsheets/26.909.12148/skills/spreadsheets/container_tools/mark_artifact_operation_started.mjs \
  --operation-kind create --expected-output-count 2 --output-format xlsx
```

紧接着运行统一builder，一次处理A/C两份：

```sh
/LOCAL_HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node \
  '/PROJECT_ROOT/outputs/validation-expansion-20260926/build_reviews_d668.mjs' \
  --results '/PROJECT_ROOT/outputs/validation-expansion-20260926/D668-原4924范围主统计.json' \
  --freeze '/PROJECT_ROOT/outputs/validation-expansion-20260926/D668-最终冻结清单.json' \
  --holdout '/PROJECT_ROOT/outputs/validation-expansion-20260926/D668' \
  --receipts '/PROJECT_ROOT/outputs/validation-expansion-20260926/D668-原始提交接收' \
  --expected-freeze-sha256 ada4bc6a62c1bc55322e2fe0416eeda54b7575465ea766c2aabf4a61f24b23f7
```

builder不自行运行marker。合成准备模式 `--self-test` 禁止同时提供真实输入路径，且不导入artifact-tool。

## 当前QA边界与后续必查

合成夹具已验证两AI各668个分析单元/27批、打乱原提交顺序仍按ID正确联接、首块标签、原始阳性/待定/子型、全部类型/字段/全文重构、三份共同文件、19种缺交/重复/非法标签/错权重/错哈希拒绝。合成长文本生成每份692显示行、52500原字段行；这些只是软件夹具数目，不是真实研究统计。

预览计划覆盖四页签完整合并标题：主表 `A1:J7`、原文语境 `A1:F7`、两文档页 `A1:C7`，另有理由、末行、澄清段预览；合成QA已检查标题范围完整。实际author后仍须阅读生成预览，核对实际长文本、换行、标题与末行未被裁切。渲染、xlsx保存后只读回读和原生Excel表现本轮均未实际测试，不能把当前准备QA称为实际工作簿验收。
