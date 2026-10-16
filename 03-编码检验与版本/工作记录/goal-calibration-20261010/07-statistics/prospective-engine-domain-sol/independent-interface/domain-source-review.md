# 冻结统计域引擎的独立源码与合成接口复核

日期：2026-10-10。结论：本次独立复核未发现阻断问题。该结论绑定下列最终源码；它是接口、数学与合成测试结论，不是实际项目结果或正式验收。

| 来源 | SHA256 |
|---|---|
| 最终 `metrics_engine.py` | `05f5999084a48b0e713e28f81e629015e61c1255cdaa43e89d30a6b59eed1d30` |
| 对照 `old_engine_source_frozen.py` | `7d6f75594745f0e2d6cf9e211c789bd5006630064089116c7553e2f7770ba0f1` |

初次 domain 扩展快照为 `f61d67ff1c1e31613254eac0ac8731c657cbddecd4b0f787ef7578caa7d1f9f8`；该快照的初审保留。最终快照新增严格要求 named-domain 行显式填写冻结部门、在 payload/metadata/design 三处禁止按域覆盖协议或输入绑定，并使 guard 的 records 与其域掩码同步。最终动态检查在开始和结束均计算源码哈希，确认运行过程中源码未变。

## 读取与执行范围

只读取旧、新引擎源码、full-domain plan 的 N/n/schema 白名单及本目录自行构造的 toy。未读取真实预测、真实参照标签、正文/语境、新抽取 ID 或母目录的实际统计结果；没有抽 ID、运行分类模型或计算任何新的真实标签。full-plan 方法表仅投影为总体/样本容量和冻结层 schema，原文件其余字段未进入复核输出。

`domain_toy_oracle.py` 使用独立的 Fraction 四格计算和接口规则，不 import 母引擎。`check_main_domain_interface.py` 另用纯 synthetic ledger 调用母引擎；角色名 A/B/reference 仅用于合成 API 测试，不被解释为真实人员或参照。

## 冻结域与允许、拒绝规则

最终 `prepare()` 第 110–140 行从字段存在性启动 named 模式：任一层含 `domain`，或 design 含 `domain_population_N` / `domain_partition` 即启动。显式 null、部分填写和错误值不能回退到 legacy。合法值固定为 `remaining` / `exposed`；单位通过唯一 `stratum_id` 继承冻结层归属，不能通过标签、ID 拼写或 row.domain 覆盖归属。

所有 named 层必须有单个非空冻结部门，所有 named 行必须显式携带相同部门；缺失、null/list/非法域、部门冲突或遗漏均拒绝。设计每层必须正容量、正 n，assigned 行数必须恰好等于冻结 n；遗漏失败行、重复单位 ID、n=0 和空设计均拒绝。已定义层的 noncensus singleton 仍沿用旧引擎方差拒绝规则。

`domain_population_N` 缺省时可由层容量逐域求和；提供时必须恰含实际非空域 keys、strict 正整数值，并逐域等于 ΣN_h。float、bool、额外空域、错误容量或仅有总体声明而缺少层归属均拒绝。`domain_partition="remaining_exposed"` 明确要求双域；不带该 marker 的合法单域设计可以存在。named full_4481_audit 还必须为 remaining1444 + exposed3037；named remaining_1444 必须仅 remaining1444。空 domain×department 交叉省略，不能变为零比例或通过状态。

完全没有上述三个域字段的旧设计保持 legacy。其旧部门含义和 census 保护规则不被重新解释为已知的 remaining/exposed 划分。

## 同一 ledger、权重与所有 assigned 分母

概率 SRSWOR 使用同一份 assigned ledger 和逐层 N_h/n_h；域和交叉域均为冻结整层的并集。因而 ALL 的总体容量、assigned 权重和四格计数分别等于两个域的对应量相加。nonprobability 保持旧 w=1，不能把它的 assigned 质量当作总体 N。

`analysis_scopes()` 第 315–345 行产生全长掩码：ALL、domain、department、domain×department。掩码不依赖 completed/null/failure；所有 assigned 单位保留在完整 4×4 状态表、角色边际及 attention 分母中。κ/P/R/F1 的 comparable 0/1 pair 分母可以小于 assigned 分母，且会独立报告。没有有效 pair 的非空域仍保留 assigned 质量，相关指标为 NA，数值目标不通过。

一次 `analyze()` 只生成一次 Rao–Wu replicate W。独立动态检查记录调用次数为 1，全部 scope 共享同一 W 哈希；每个概率 toy scope 的 replicate assigned 总权重等于该 scope 的已知容量（浮点容差 1e-10）。指标、attention 与跨部门 contrast 使用这份 W 的掩码切片，未按域重抽或重新生成 W。

`_guard_scope_prepared()` 第 351–359 行只缩小 finite-count guard 的固定层宇宙、stratum_ids 和 records。guard 输入与域向量长度一致；它不重生 W。single-category/joint-table guard 仍是各 view/comparison/dimension 的边际保护；源码明确未声称跨所有 views 的同时覆盖，也未声称已完成联合 16 状态向非线性指标的投影。

## census、NA、数值目标与正式验收

census 按本域全部冻结层是否 n_h=N_h 判断。另一域的 noncensus 不影响本域真实 census；null/failure 与 NA 不会因为 census 而消失。unknown identification bounds 保留其未知质量含义，不改写成 95% sampling CI。undefined replicate、noncensus degenerate bootstrap 和 nonprobability 的既有状态保留。

ALL κ/P/R/F1 从合并 weighted cells 重算，各域从其自身 cells 重算。源码没有平均各域非线性点值，也没有平均或隐式合并数值通过 flags。全体点目标是否达到、各域点目标是否达到分别报告；未增加 CI 下界/半宽门槛，也未把“各域都通过”附加为新的全体门槛。

formal_acceptance 在全体和每个 scope 均恒 False。`review_eligibility()` 第 401–438 行保留真实身份、独立初始作业、冻结流程、可信裁决等外部复核要求。即使 unit test 将所有 metadata attestations 设为 true，结果仍 formal=False 且 `metadata_cannot_authenticate_human_identity_on_its_own=True`。哈希只绑定字节、单位成员和版本，不能认证人员身份或人工作业过程。达到 0.8 点目标本身不构成正式验收。

## 独立动态证据

最终快照通过本代理的 **43 个元数据允许/拒绝案例、9 个非空统计域掩码核查、4 个 legacy 场景**。各项结果见 `main-domain-interface-results.json`，可复跑入口为 `check_main_domain_interface.py`。母代理另报告的 284 项回归不是本代理执行数量，未与本次数量合并。

| 合成 mask | assigned n / W | comparable pair n / W | weighted a,b,c,d | κ |
|---|---|---|---|---|
| ALL | 8 / 14 | 5 / 11 | 5,2,3,1 | −2/53 |
| remaining | 4 / 6 | 3 / 5 | 2,2,0,1 | 2/7 |
| exposed | 4 / 8 | 2 / 6 | 3,0,3,0 | 0 |
| department Beta | 4 / 4 | 1 / 1 | 0,0,0,1 | NA |
| exposed×Beta | 2 / 2 | 0 / 0 | 0,0,0,0 | NA |

全部五维重复此纯 toy 状态以检查接口掩码。Beta 与 exposed×Beta 为 toy census；后者含 assigned failure 而无 binary pair，正确保持非空域及 NA。ALL κ 为 −2/53，不能取两个域 κ 的均值 1/7。另一个纯合成 census 例将 remaining 四格设为 (1,1,1,1)，exposed 设为 (99,0,0,99)：ALL 点目标通过、remaining 不通过、exposed 通过；三个状态分别保留，formal 全为 False。

legacy 的正常、冻结部门缺省/歧义、全体 census、nonprobability 四种 toy 与旧源码逐项比较既有数值、状态、attention、部门对比和身份结果，均一致；只允许新增 schema/来源字段和 guard 范围说明。

## 交付白名单

`full-plan-schema-projection.json` 已含 full800/full1000 各 **41 层**的 whitelist，逐层仅 `id`、`domain`、`department`、`N`、`n`。方法表的 key 已映射成 id。两计划 ΣN=4481；Σn=800/1000；remaining N1444/n600、exposed N3037/n200/400。此文件可直接用于后续纯合成 ledger 构造，不能据此生成或猜测真实标签。

原 `domain-interface-contract.md` 与独立 oracle 初审保持原样；本附记承接其“新源码完成后再复核”的记录。最终源码在本次可检验范围内符合该接口契约，没有需要母代理阻断后续文档交付的错误。
