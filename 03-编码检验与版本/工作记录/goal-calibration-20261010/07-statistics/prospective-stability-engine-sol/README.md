# 前瞻稳定性统计工具准备

本目录仅完成离线统计工具、输入契约和构造数学控制。没有读取真实编码标签或 Gold，没有调用模型，没有创建 LLM 任务，没有计算实际稳定率，也没有更改正式执行计划或项目完成状态。准备者为 AI；任务指定 GPT-6.1 Sol、ultra，不是真人专家。构造文件中 `actual_attempt_count` 等字段是待用台账字段，其当前数值均来自人工构造控制，不能描述为实际模型调用。

依据为两份只读预设：`06-coding/llm-protocol-sol/稳定性与运行封存预设.md`、`02-methods/prospective-statistical-contract-v2/validation-design-v2.json` 的重复稳定性及公式章节。现有三次主条件 R1/R2/R3 与两种预定等义变体 W/H 得以完整恢复。P 是既有生产首次有效结果的台账角色，用于防止诊断回填；P 不是新增重复条件，工具本身不发起任何执行。

## 使用

只依赖 Python 3.9+ 标准库。先冻结 registry，后由真实执行设施保存完整 ledger 和原始字节；本次只提供 TOY 输入。

```bash
python3 stability_engine.py analyze \
  --registry constructed-controls/inputs/mixed/registry.json \
  --ledger constructed-controls/inputs/mixed/ledger.json \
  --out-dir NEW_EMPTY_DIRECTORY

python3 -m unittest -v test_stability_engine.py

python3 seal_preparation.py --verify
```

输出目录必须为空，封存结果不会覆盖。相同输入字节产生相同的四个结果文件。`seal.json` 记录全部被读取的注册文件、实际原响应/检查报告/请求/来源文件及输出 SHA，另记录引擎 SHA。它不包含自身 SHA，避免循环。

## 可复核结果

- `stability_engine.py`：完整模块与 CLI；`input-contract.json`：静态 JSON Schema；`输入与统计契约.md`：跨文件规则与公式；`generate_contract.py`：Schema 重建脚本。
- `constructed_controls.py`：只生成八条虚构 TOY 记录；`test_stability_engine.py`：22 项有限意义控制；`verification.txt`：本次测试日志。
- `constructed-controls/inputs/{mixed,all-zero,rare,batch-context}/`：冻结输入、精确请求、纯构造来源、原响应、检查报告及 first 输入绑定。
- `constructed-controls/results/`：四组离线构造报告、firsts、全部尝试账和逐组 seal；`手算与反例.md`：独立手算。
- `preparation-seal.json`：本工具准备文件总清单及两份只读预设的 SHA。当前没有正式运行完成证据。

## 主要口径

固定比较 R1/R2、R1/R3、R2/R3、W/R1、H/R1；不给挑最佳基线的选项。四格以第一条件为行、第二条件为列，逐维同时输出原始及预定权重四格、双方边际、Po、Pe、κ、阳性数变化、变化 ID 和原响应绑定。NA 用 JSON `null` 及原因表示，不填 1。

逐维共同二元集合只接受双方技术有效且该维为 0/1。五维向量和 q 使用整组五维全部为 0/1 的共同集合；报告预定总数、共同数、排除 ID、两侧或三侧状态重叠、材料待定数量及权重和。q 每次先算各维 T，再用该次 Σ5T 作分母。null 模式另报，不叫二元稳定。

生产 P 只采用本条件首次技术有效完整响应；语义 null 是有效响应并停止重试。技术检查失效使整条响应失效，不提取其中四个“可用维度”。最多三次相同请求；失败原字节与传输状态保留。零次尝试只能记未调用及预检/材料/创建空提交原因。尚有重试名额的失败快照另标明剩余名额，不称已耗尽三次。

所有版本、请求设置、材料语义/CTX绑定、样本权重、次序、批次、条件和重试请求都先登记并严格核对。W 只把来源 JSON 展示改为两空格缩进，来源字符串内部字符保持；H 只把用户首行“判读要求”换成“判读说明”。不能叠加变体或把改版、分批、技术重试当作重复。

## 当前适用边界

输入必须显式选择 `context_unit=record` 或 `batch`，保存独立声明但标 `not_independently_verified`。batch 模式只能描述登记的批次上下文，输出明确说明它与协议逐记录独立上下文形状不同。此工具没有 native77 自动导入器，不默认 native77 已满足独立上下文。当前输入契约的原响应是一条记录的完整 JSON；真实批量响应若采用另一格式，必须先另外冻结保留整批原始字节和可追溯提取路径的适配契约，不能将拆分派生文件冒称整批原响应。

身份字节、请求 SHA、上下文 ID 和顺序索引只核对登记与绑定，不证明实际模型、实际派发次序或实际独立上下文。提供方回执不可得时必须留 null，不能从界面模型名称补造证据；已见返回模型字符串漂移则拒绝同条件分析。

引擎本地复核原响应的解析、ID、五维和值域及必需结构；原文引用、CTX、连续引文和资产的检查来自事前冻结外部检查器的报告，本工具不冒称重新验证这些语义/来源检查。构造检查器只提供测试断言，绝不是可直接用于正式生产的来源检查器。

非概率输入只描述共同材料；概率输入必须有正纳入概率和精确 1/π 权重及框覆盖声明，声明本身未被统计工具认证。缺行拒绝，未调用/null/失败保留。引擎一律不作总体结构或总体推断声明，不计算 CI，也不设统一稳定阈值或 CI 通过门槛；不把一致性当作分类正确性、真人独立信度或完整 Goal 验收。
