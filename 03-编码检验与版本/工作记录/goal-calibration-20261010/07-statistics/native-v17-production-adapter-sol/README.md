# 原生 v17 records 接口候选

此目录另存有限的离线技术候选，未采纳生产来源资格，未执行真实编码或 R1/R2/R3/W/H。未读取真实首答、A/B/GOLD、预测、指标或政策正文。现有 toy items 候选、逐条 API 方案及当前 `native-llm77-v17-sol` 均未修改；代码拒绝将当前 v17 run_id 注册为新诊断 campaign。

`v17_adapter.py` 消费预先绑定的 plan 和整批台账；不派发 actor，不发现或遍历真实 campaign。`vendor/validate_v17.py` 与冻结 v17 技术校验器逐字相同；`vendor/stability_engine.py` 与已审 typing-fixed 数学实现逐字相同；`statistics_bridge.py` 的 statistics() 函数从独立审查通过的 batch_adapter.py 原样摘取。输出 schema 保留 v17 `records/dimensions/value/reason/evidence/read_manifest` 结构，只允许替换新 campaign、批号、手册/提示、scope 身份常量及本批确切 N。

每个 attempt 引用完整原始整批 UTF8 文件。原件的 path/bytes/SHA 与预留 runtime route 必须吻合，原件不会改写。完整批次校验失败时不产生任何成员标签或成员抽取指针。按真实记录的 attempt-number 顺序选择最早技术有效整批；后续调用非法，包括首个有效整批中有合法 null 的情况。至多三次技术尝试；三次失败保持技术失败，不填五维零，不跨 attempt 拼接。有效派生记录共用同一原件引用，固定 `/records/N`，明确 `derived_record_is_original_response=false`。

所有 R1/R2/R3/W/H 必须是预定同一样本和批次。R1/R2/R3 复用同一 frozen assignment 与初始派发字节。W 仅改变冻结 packet JSON 文件的展示为 sort_keys/indent=2/LF，解析对象和字符串完全保持；H 仅替换执行 prompt 第一行“判读要求”为“判读说明”。其他共同输入及资产绑定保持一致。runtime 路由为请求外操作元数据。本地文件展示变体与原始逐 record／用户提示内 JSON 预设有方法差异，生产采用须先冻结 `CONTEXT` 所示 native 方法加订；工具请求及文件读取不称 provider wire 控制或捕获。

五条件必须全部取得整批首个有效响应、耗尽三次失败，或明确零调用的事前材料/预检阻断，并与条件 terminal seal 一致，才能用 `--compare` 比较。未终结快照可保存，但 `paired_comparisons={}`、`three_main_runs=null`。请求提前比较直接拒绝，不创建比较输出。封存时间和派发独立性是文件绑定的声明，SHA 不独立认证真实时序。

## 来源技术资格与界限

`source_contract` 要求共同来源结构 profile 递归关闭：显式 object/array/标量类型，每一 object `additionalProperties=false`，无 `$ref`、组合 schema 或开放子容器。现有 v15 schema 仅靠自身无法满足这一要求；须由共同来源接口另冻结完整闭合 profile，候选不自动裁剪旧来源字段或生成正式 profile。

每条记录绑定原 packet 字节、source/output ID、source_bundle canonical SHA、原 CTX 指针和值的 SHA；引用位置名单另外绑定原文字段、current/context 角色、原位置和 CTX 身份。逐字引文必须是名单内具体字符串字段的连续子串。补充资产引文还须有共同冻结的 asset/page/text 链接、实际文件 SHA、合格文字视图及提交中对应页的呈现声明。只给资产路径和 SHA、没有合格文字视图的引用失败关闭。

这核验来源文件与冻结位置合同的完整性及文字视图的连续逐字命中。它不证明图像像素与转录语义一致、不判引用语义适用性、不证明真实工具呈现/阅读、实际服务模型或供应商身份、上下文独立真实性；不测分类正确性、真人信度、CI、通过线或项目完成。材料 complete 必须在 plan 明确声明，当前候选不采纳 pending-source 运行接口；complete 不由哈希推断语义充分性。

`data_mode=prospective_registered_inputs` 时，缺少 ROOT 事前生产采纳文件便在打开来源和输出之前拒绝。采纳文件须绑定 plan（以 production_adoption=null 求 base SHA）、共同来源合同及 native 方法加订。该文件本身仍是待核明的 ROOT 冻结声明。正式台账另要求实际可得 native 工具请求/创建回执的原件引用；本候选核验这些文件绑定，不把任意本地文件或模型名当作真实工具或供应商身份证明。

## 最小使用接口

构造输入形状见 `constructed-controls-r04-final/normal/inputs/plan.json`、`common-source-contract.json`、`ledger.json` 以及 main/batch-0001/assignment.json。这些只有两条自造记录，不能改模式或换名用于生产。

```sh
python3 -B v17_adapter.py --plan /absolute/prospective/plan.json --ledger /absolute/prospective/ledger.json --out /absolute/new-result.json
python3 -B v17_adapter.py --plan /absolute/prospective/plan.json --ledger /absolute/prospective/ledger.json --out /absolute/new-comparison.json --compare
```

输出以 xb 独占新建，拒绝覆盖。分析前、比较前均核对绑定文件；原件没有重排、美化、重新编码或逐 record 重构步骤。原生提交文件是 actor 的首个结构化整批文件字节，绝非 provider 原始网络响应。

## 实测与尚缺的正式输入

最终 `constructed-controls-r04-final/actual-controls-report.json` 记录 14/14 控制通过，所有输入原字节前后相同：正常、末成员失败导致全批失效、第二次最早有效、合法 null 后重试拒绝、bool/float 失效、先行比较拒绝、三次失败终结、第四次拒绝、错误首选拒绝、补充资产 quote 失效、非资格 pointer 拒绝、生产采纳缺失拒绝、开放来源 profile 拒绝。正常样例两条固定 records 指针同源；自造 R1/R2-S 四格为 (1,0,1,0)，Po=1/2、κ=0。只有设施控制，没有真实稳定性结果。

首轮 `constructed-controls/normal/actual-cli-record.json` 的真实设施失败“material_state 缺失”及其全部输入保留。后续构造 r02/r03 也保留，未覆盖失败原件；最终报告明确绑定最终执行代码。候选 meta 已补齐该字段，数学实现未改变。

正式运行还缺：事前诊断样本/权重/顺序/批次与新 campaign；共同手册、prompt 和全部共同来源修订；可执行完整闭合 profile、逐来源/CTX/引用位置合同及需要的合格资产文字视图；native batch 与 W/H 文件交付方法加订和 ROOT 采纳冻结；完整三槽条件路由与同字节派发请求；每次真实工具请求/回执、完整原批 UTF8、失败原件与时间/暴露声明；五条件 terminal 封存台账。这些清单见 `production-input-requirements.json`。当前没有生产 plan、采纳文件或真实诊断首答，真实运行仍不能由此候选单独启动或认证。
