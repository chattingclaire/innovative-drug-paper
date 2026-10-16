# v15 同版 PDF 公共文本源接口

本目录只做源材料封存与机械投影。原 PDF SHA 为 `64ac48e58753780279df45a96c595f6415e84fef087a316b66f26def2cd5658c`；物理页 8、9、20、21 使用 `pdftotext -f/-l -layout` 重新抽取，全文 UTF-8 字节与既有四个补材块完全相同，包含页末 formfeed。未读问句、目标编码、开发标签、Gold 或机器预测；未运行 77、800 或 4481 编码。

新增 `source_full_text_resources` 是一个可被旧通用 FULLSOURCE inventory 与 receipt adapter 消费的完整 payload，`paragraphs` 为四个整页全文。`source_sha256` 和 `source_pdf_sha256` 都绑定原 PDF；整页 UTF-8 SHA 单独存放在页 locator 中。没有使用 PDF 不适用的 `verbatim_UTF8_snapshot_text`。

`source_documents` 仅新增该 PDF 的 `source_text_resource` 文件绑定。relative_path 以旧 scope 的 v12_source_base（/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/01-review/context-projection-sol/full-frame-preflight）解析，真实指向本目录 source-library 的封存 payload JSON。`common_source_bundle_version` 保留原 identity；已有 extension 原样保留并新增 `v15_same_pdf_physical_page_text`。仅新增 source availability，不授予语义适用性，也不建立实际阅读或使用记录。

机械遍历原 4481 束，224 个同 PDF 束新增资源，其余 4257 束的 canonical bytes 不变。77 个固定输入仍使用既有全局顺序，5 束改变；13 个批次使用 native-v16 的实际历史 source-ID assignment 元数据。两个机器都指向同一裸 JSONL 和相同逐束 SHA，尚未实际消费。packet_version 与原包其他字段、资产绑定保持原值。

入口：source_only_interface_v15.py；新增材料：source-library/nhsa-common-qa-physical-pages-8-9-20-21-v15.json；共同 whitelist：common-material-bindings-v15.json（完整保留旧 v18 的 13 项绑定）；77 bare inputs：development77/common-source-bundles-v15.jsonl；compact packets：development77/packets；新 packet schema：development77/packet.schema.v15.json；完整 mechanical projection：common-frame-bundles-v15.jsonl 与 frame-bundle-bindings-v15.jsonl。

有限验证：77 packet/source schema、通用 adapter 结构转换、原 FULLSOURCE 精确身份解析、真实源基路径与 whitelist 文件 SHA/bytes、6 个 endpoint 只读 source accessor 调用。无 dimensions/relations/driver 编码调用。source-only-QA-v15.json、report.json 与 seal.json 给出真实绑定与限制。seal 排除自身。
