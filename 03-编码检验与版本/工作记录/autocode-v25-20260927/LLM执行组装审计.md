# LLM 执行组装审计

## 有界结论

在本次只读结构审计覆盖的 11 个 `assemble*.py` / `build*.py` 中，未发现由输入文本关键词、正则表达式或字符串匹配触发 0/1/待定标签的自动分类器。标签均来自显式逐条判断表、五位代码、逐条 judgment 参数或按记录 ID 的冻结查表。固定理由模板本身没有参与标签选择，因此不应误判为自动标签分类器。

就可见实现而言，未发现违反“脚本只组装明确判断、引用原文或选择证据”的标签生成偏离。

该结论只针对脚本结构。它不能证明判断表由何种认知过程产生，不能证明模型逐条阅读或注意了哪些材料，也不能证明每条理由、证据和标签在语义上正确、充分或高质量。本次没有读取任何参考标签、性能统计、既有输出内容或评价指标，也没有重编码。

## 标签来源核对

- shard01：从逐批 decision 文件中的 `positive_dimensions` / `pending` 显式参数生成标签；原文只用于正类整段证据及显式附加语境证据。
- shard02：直接展开逐条 `labels` 向量；显式 evidence 字典只负责证据组装。
- shard04：`PACKETS` 中逐条写定五维标签、理由和证据；输入只用于 ID/顺序核对。
- shard05：`batches` 中逐条写定标签、理由和证据，不读取输入文本决定标签。
- shard06：`PACKET_CODES` 按包、按行、按 S/E/Ec/I/F 位置写定五位代码；子类型与少量语境证据由显式 ID 集合/字典指定。输入文本只被整段复制为正类证据，结构化语境遍历只选择证据文本，不改变标签。
- shard08：一个脚本直接展开完整逐条 labels/reasons/evidence，另一个把显式紧凑代码 `0/1/?` 展开为标签；没有文本触发。
- shard10：一个脚本展开显式 `0/1/?` 与理由代码，另一个直接组装逐条 labels/reasons/evidence；没有文本触发。
- shard11：`save` 调用中逐条内嵌标签、理由和证据；脚本不读取输入文本决定标签。
- shard12：`J` 按记录 ID 写定正维度、子类型与 S 基础，`make_row` 只把该查表结果展开成五维标签。

静态 AST 检查确认：11 个脚本均未导入 `re`，也未调用 `search`、`match`、`fullmatch`、`findall`、`lower`、`casefold`、`find`、`startswith` 或 `endswith` 等潜在文本触发操作。唯一与文本相关的条件出现在 shard06 的语境证据结构遍历及避免重复引用判断中，不进入标签计算。

## shard06 与 shard12 的解释局限

shard06 的标签来自显式 `PACKET_CODES`，但五维理由主要从固定正/负模板生成；对正类通常把整个 `inp['text']` 作为证据，对一组显式 ID 再取结构化语境中的首个文本片段。该实现能证明标签不是由关键词规则即时算出，却不能证明模板理由针对该条完成了充分解释，也不能证明整段引文精确定位了支持判断的最小证据。

shard12 的标签来自显式 ID 查表 `J`，但理由由五个维度描述模板统一生成，所有正类证据直接引用整段 `inp['text']`。schema 通过只能说明字段形状满足要求，不能据此称逐条解释充分。

shard01 也会把整段输入作为正类证据，但其正类理由来自逐条 decision 参数；同样不能仅凭组装和 schema 验证推断证据粒度或解释质量。

## 审计边界

12 份 manifest 显示 shard01–11 各 420 条、shard12 为 304 条，合计 4924 条。manifest 的文件清单没有绑定本次审计的组装脚本，只列出 `validate_output.py` 作为 Python 文件，因此 manifest 不能证明这些辅助脚本就是实际输出的唯一生成路径。

shard03、07、09 没有匹配的 `assemble*.py` 或 `build*.py`，本次无法从该类脚本判断其组装机制。由于按要求没有读取输出文件，本审计也不证明脚本产物与现存输出逐字一致。上述限制不构成本次已发现的实现偏离，但限制了结论外推。

## 组装脚本 SHA-256

- `shard-01/assemble_explicit.py`: `41c30e4c5377cbfd71133f5c6e91be31ceea39acdef92aa60da646e60661e9cc`
- `shard-02/assemble_explicit.py`: `c6a29a68ccdf599bb170635f8a9e688a1d9aff0027a9106994a03013736cb047`
- `shard-04/assemble_explicit.py`: `97496cf1bb09338d7648c0e5e87578a9e39dccef17dc0cb25a6b9d1fa98ba29c`
- `shard-05/assemble_explicit.py`: `18247fd5682d7b36ace1b867bbe90a400f63d23753160a9879f1ec3af0f34a1e`
- `shard-06/assemble_explicit.py`: `4178b3ed443ea43812d2be2b606cedf4c880c1673dac017edde4f67fe667b608`
- `shard-08/build_compact_explicit.py`: `73b7b84a235be48fad20c950082c6bdfde37ca6f1bbf0158ac65adbe6b7c03ed`
- `shard-08/build_explicit.py`: `0937540b6f5fb186bea7c8e7b1b6e244c6db0807fd16ccb4c542be998d418759`
- `shard-10/assemble_compact.py`: `78e563f3414739399b9b1d644a50d93e1a8010f47a8d26227b8a5b76bf304fc7`
- `shard-10/assemble_explicit.py`: `cdd76fe6058f6ac4b7fcc71322bac7c27c5a45b794711131d1befa5674fb408a`
- `shard-11/build_outputs.py`: `9552674760e272d91a736355b1b334b76b5cd3eaf64acbc2cc8c3b27efdcdb67`
- `shard-12/assemble_explicit_decisions.py`: `f1bd4646fec4213570509fc6ff0378c96148460ed80c66679e66d031ee44343f`

## Manifest SHA-256

- `shard-01/manifest.json`: `0da44d36905144b0616ed2372f9d5e23d8f42997f57b28a0734290c1d4d9ae04`
- `shard-02/manifest.json`: `a1be407a8435caad8ed73b6737af40d8f81470e6cb4b9202195fb786eb94409a`
- `shard-03/manifest.json`: `f2b15fa20ce0d1f6cc691d2437e86ffa4998b522ced626d9407cb6ac5210a8d8`
- `shard-04/manifest.json`: `73ec64c58efadfec4ecbd70975f96e5986a8ff36f80b81534cc8df4fb8fa143e`
- `shard-05/manifest.json`: `3bca1df56dc901739c3889126b0cbefbb1e1f7a69f8ec640ef84c305a934baa9`
- `shard-06/manifest.json`: `55e011ccf9c2fa409b153765a07d132df7b4876230669eb133a69d644c4de7ca`
- `shard-07/manifest.json`: `ec9cb018f0776288eda72ec66e4b6e055792856ca367de1ecb5508cf240b26f1`
- `shard-08/manifest.json`: `93d55e465e9a35dde80baf9ed084ccb687bfaa0fe492c43359c726b68b516e13`
- `shard-09/manifest.json`: `28eaca7de1907cee8c1a5bb3cc249c28fd360d67915ba6e4fc42374b13d0329c`
- `shard-10/manifest.json`: `053adb608e7406b188e6b6878fe02467a7ca9342dda58987a7b6dc10bcb552db`
- `shard-11/manifest.json`: `b8eb04566ed8dddd2c9c96a0b632f581e69de99cf119b2439e3267b6bff9dac3`
- `shard-12/manifest.json`: `b29b6e781dd3d5cd63ad2c9435b93621009fe70d685fc3fcfd13a120f2c21c27`
