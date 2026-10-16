已完成只读 XLSX 接收适配与 16 项有限检查。真实 A/B 配发表读回各 800 个盲号、4000 维，共 8000 个 unfilled，未产生真人初判。全部旧文件保持不变；正式发布与实际人员独立执行声明仍待真实落实。本适配器不计算 weighted 统计、准确率或 CI。

运行入口是本目录 `adapter.py`。在项目目录执行空表机械核对，输出目录必须为本适配器目录内一个尚不存在的新目录：

```sh
python3 outputs/goal-calibration-20261010/05-validation/formal800-xlsx-reception-adapter-sol/adapter.py dry-run --xlsx-a outputs/goal-calibration-20261010/09-delivery/formal800-human-workbooks-prerelease-sol/coder-A/formal800-A-pre-release.xlsx --xlsx-b outputs/goal-calibration-20261010/09-delivery/formal800-human-workbooks-prerelease-sol/coder-B/formal800-B-pre-release.xlsx --out outputs/goal-calibration-20261010/05-validation/formal800-xlsx-reception-adapter-sol/receptions/新机械核对目录
```

收到实际文件后改用 `receive`，把 `--xlsx-a` 与 `--xlsx-b` 指向实际返回原件，把 `--out` 改为新的接收目录。没有正式 release 或真实独立执行声明时，文件内容仍可解析和保存，资格记 `qualification_pending`，不称正式内容接收完成。完整 4000 值与理由、真实发布绑定及真实声明均核对后，可记 `content_received_on_bound_declarations`。这只报告基于绑定声明的内容接收，不能认证真人作者、独立性或实际启动时间；语义、引文、对象与关系由协调员核验。

对于有真实发布与声明的接收，追加 `--release /绝对路径/release.json --release-sha256 真实SHA --declaration-a /绝对路径/A声明.json --declaration-b /绝对路径/B声明.json`。`release` 的最小读入字段为 `status="frozen_for_execution"`、`source_package_sha256`、`template_sha256` 的 A/B 两值、`packet_file_sha256` 的 A/B 两值、`manual{path或absolute_path,sha256,bytes}`、`manual_version`。使用实际未来发布的手册，不把历史 pre-release 手册状态冒作正式发布；源包、模板和 packet 不改。release 及声明原始 JSON 字节也一起保留。

声明沿既有提交契约使用实际 `completion_status="complete"`、`human_coding_completed=true`、`actual_actor_type="real_human_independent"`、`executor_code`、`record_N=800`、`dimensions_N=4000`、`packet_file_sha256`、`manual_sha256`、`actual_started_at`、`actual_submitted_at`、`prior_development_exposure`、`independence_declaration` 与 `AI_assistance`，增加所返回原件的 `xlsx_sha256`。四项独立声明是 `own_first_judgment`、`machine_answers_unseen`、`peer_answers_unseen`、`no_discussion_before_seal`，需如实为 true；AI_assistance 保留实际 `label_drafting_used=false` 与描述。该程序核对声明内容，不能证明声明真实。没有新建身份注册门槛；同一声明执行人无法同时被当作 A/B 独立执行。未生成可假冒真人的声明样件或 frozen release。

原件按读取时实际 bytes 保存为 `original-A.xlsx`、`original-B.xlsx` 并逐字节核 SHA，既有接收目录绝不覆盖。非法文件也保留原件与位置化错误供返查。修改后需另用新目录，不能覆盖原 first。`derived-A.jsonl` 与 `derived-B.jsonl` 是每方独立 4000 行派生记录，明确 `not_original_human_file=true`。每条保留盲号、维、原行、源 bundle SHA、值、自由文字理由、Excel 单元格实际类型/原 payload/原公式、规范化方式；派生 JSON 不能替代原始真人 XLSX。

列 A/B/C 与表头、原配发行序必须逐格等同模板，并按已封存 packet-index、labels.blank、mapping 与 draw-contract 检查原绑定。B 列只做原字符串等同性比较，不做语义阅读或改写。800 盲号、各五维齐全，未知/重复盲号或维、任意调序、增删有效输入、公式或布尔等非法 D 均拒绝用于后续统计。D 仅接受数值 0/1 或精确 Excel 文本 `0`/`1`；空 D 保留 null + unfilled，绝不补 0，也不当作已经做出的未知判断。` 1 `、`1.0` 等文本不猜测。填 0 与 1 都沿现契约要求 E 有非空自由文字理由。理由不代填，E 公式/布尔/数字不当自由文字。

`coordinator-private/source-aligned.jsonl` 按原 source_id 对齐双方各自盲序，共 4000 维，保留 A/B 独立初判。`disagreements.jsonl` 只含双方已填且值不同的项。`adjudication-todo.jsonl` 只含分歧或任一方待填项，裁定值/理由/执行人保持空白，agreement 不转成裁定答案。任一方内容错误时三项协调员派生结果均 withheld，禁止误用变动的原行。dry-run 待办均显式 dry_run，未填是等待实际独立输入，不是已发生的真人分歧。

有限兼容修正：旧 JSON 接收器的 source quote、七字段维结构与 sidecar 不是本 XLSX 的科研验收门槛。这里复用其封存字节绑定、严格 JSON、五维/非空理由/声明时间格式等成熟函数，另立仅含实际 D/E 的原件至派生记录接口。E 可以自由文字说明对象、关系和引文位置，没有要求额外复核栏或 sidecar，没有伪造 structured quote。`structured_evidence_automatically_validated=false` 并交协调员核验，不把 XLSX 永久判为不能接收。旧 JSON 接口和旧文件完整保留。

实际有限检查见 `finite-checks.json`，构造副本全部标为测试、非真人首判：4 个 XLSX 副本，仅 A/B 各填 3 个合法值；另少量非法控制核同错盲号/重复盲号维、错维、D 公式/布尔、缺理由、歧义文本、改动行序拒绝。异序对齐中同源 A 行 2 对 B 行 2417，唯一构造分歧保留为 0 与 1；两项一致没有自动裁定，3997 项未填仍 pending。核对原件字节、原 first 不能覆盖，以及全部 15 项旧绑定输入 SHA 保持不变。测试不代表真人实际编码、正式发布或指标验证。运行报告、每次接收 seal 与总交付 seal 记录实际输入输出 SHA。
