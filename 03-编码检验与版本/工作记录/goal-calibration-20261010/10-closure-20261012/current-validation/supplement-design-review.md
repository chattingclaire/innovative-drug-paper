可行。条件于已冻结机器、当前 remaining1261 和旧 91 条交集，可将余 1170 中「任一机器在 F 或 I 预测为 1」的 40 条单列全查层，其余 1130 条按部门做不放回简单随机抽样。这样保证稀少维度的机器阳性代理全部进入人工工作范围；不保证真实阳性数量、指标精度或达标。此项为设计可行性复核，未登记、抽样或决定随机样本量与抽样种子；原候选及封存组件未改。

数据来自 [supplement-planning-counts.json](/PROJECT_ROOT/outputs/goal-calibration-20261010/10-closure-20261012/current-validation/supplement-planning-counts.json)，SHA256 `074c00da0e962f0b09d77e84c367457b0e6a2481c34571ba9366dfb5a6aa531b`。该文件已绑定现机器清单、实际两机预测、曝光框与旧 200 抽取编号。此次复核只读取聚合计数、设计元数据和代码，没有重读政策正文、预测证据或真人答案。

| 部门 | 旧 C91 全取 | 新 F/I 代理阳性全取 P40 | 剩余随机框 Q1130 | 当前目标 |
|---|---:|---:|---:|---:|
| NHC | 10 | 0 | 84 | 94 |
| NHSA | 34 | 8 | 449 | 491 |
| NMPA | 47 | 32 | 597 | 676 |
| 合计 | 91 | 40 | 1130 | 1261 |

P40 内，只有 I 代理阳性 22 条、只有 F 代理阳性 3 条、二者均有阳性 15 条；因此包含 R1170 的全部 18 条 F 代理阳性及全部 37 条 I 代理阳性，重叠只计一次。旧 C91 自身的 I/F 代理阳性各 2 条继续全部保留。

现有接入能力支持这一拆分，无需增加第三种 role。[reuse_admission.py:105](/PROJECT_ROOT/outputs/goal-calibration-20261010/10-closure-20261012/current-validation/reuse-admission/reuse_admission.py:105) 把旧交集定义为 `certainty`、其余定义为 `supplement`；[第 185–211 行](/PROJECT_ROOT/outputs/goal-calibration-20261010/10-closure-20261012/current-validation/reuse-admission/reuse_admission.py:185) 要求 `certainty_ids` 恰好保留旧交集。因此该字段仍是旧 91，不能为方便而改成 131。新 40 与 Q 中新抽取项均属于补充工作队列，其材料、盲法与本组开始时间沿用补充回执要求。

[第 216–246 行](/PROJECT_ROOT/outputs/goal-calibration-20261010/10-closure-20261012/current-validation/reuse-admission/reuse_admission.py:216) 允许同一部门/role 内有多个不同 stratum_id，只要求成员完整、层内部门与 role 一致、层 N 与实际成员一致、所有非空层正概率且非全查层 n≥2；对 `supplement` 层也允许 n=N。可保留 3 个旧 91 层，新增 NHSA/NMPA 两个 P 全查层，再设 3 个 Q 随机层，共 8 个非空层。NHC 的 P 层为空，不登记空层。P 的统计全查性质由 n=N 表达，不依赖把 role 改名为 certainty。现接口没有额外限制每个部门/role 只能有一个层。

原数学核心不需要改。对于任一混淆表单元格或其他可加总的指标，目标总量估计沿用：

`全量估计 = C91 的观察总量 + P40 的观察总量 + Σ部门 (Q部门规模 / 该部门实际随机抽取数) × Q样本观察总量。`

C 与 P 在这份新设计中的纳入概率和权重均为 1，Q 使用各部门自己的 n/N 与 N/n；旧 200 原概率与权重另行保留。比率及 κ 从加权总量计算，不把其宣称为精确无偏。不能忽略抽样设计直接合并样本算总体准确率。

[frozen_year_core.py:245](/PROJECT_ROOT/outputs/goal-calibration-20261010/07-statistics/prospective-dynamic-domain-engine-sol/frozen_year_core.py:245) 对所有 strata 循环，n=N 时保留原权重；[第 262 行](/PROJECT_ROOT/outputs/goal-calibration-20261010/07-statistics/prospective-dynamic-domain-engine-sol/frozen_year_core.py:262) 的解析协方差对全查层贡献为零。依据是层 n/N，并非层名或角色。因此继续保留 5000 次共用 W、现有统计重抽样种子 20261010、RaoWu/FPC、原点目标及置信区间处理；该统计种子不等于尚未决定的新抽样种子。核心 SHA256 `f6b33491bb27d7325cdc18c25fb7d54fef45909e1ef38c3f27606edcb61c2262` 与 current-basis 的绑定核对一致。既有控制已验证全查权重 1、全查方差 0 和共享 W；本次未重新运行统计或声称已验证真实八层执行。

若采用此方向，变更集中在新设计数据和既有待完成接入，范围有限：

1. 对当前 [supplement-design-candidate.json](/PROJECT_ROOT/outputs/goal-calibration-20261010/10-closure-20261012/current-validation/supplement-design-candidate.json) 另出新版本：六层改为上述八个非空层，冻结完整目标成员、P/Q 判定谓词与逐 ID 层成员，并绑定现机器预测及本计数；明确 P 来自机器代理辅助分层，C 仍仅来自固定旧 ID。成员确定先于补充真人反馈，不按后来答案改层、补挑或丢弃。
2. 实际工作量决定后，才为三个 Q 层登记 n 与新抽样种子，形成一次真实抽取及精确新权重；当前不设这些数。已有 `reuse_admission` 的纯部门/role、全查、成员与概率检查可直接复用，无需为本方案再开发一轮准入门。
3. 最终标签/来源 join 仍是原先未完成的工作。[reuse_admission.py:344](/PROJECT_ROOT/outputs/goal-calibration-20261010/10-closure-20261012/current-validation/reuse-admission/reuse_admission.py:344) 明确组件只准入元数据、不授权统计。以后把八层的实际 n/N、原件与真实回执接到受审入口时，保留旧/新两组真实时序；动态引擎原 [scope_admission.py:145](/PROJECT_ROOT/outputs/goal-calibration-20261010/07-statistics/prospective-dynamic-domain-engine-sol/scope_admission.py:145) 与后续资格检查中的旧 `before_answers` 契约，不能为继承旧 91 而倒填。此处是沿用既有待办，不是 P40 带来的新限制。数学核心保持原件。

代理阳性全取可确保观察这些已知稀少案例，降低它们被随机抽样漏掉的风险；相同总工作量下，不能保证所有维度的方差都更小。两机可能共同漏报，Q1130 只是没有 F/I 阳性标记，可能含真实阳性和机器 NULL；三个部门的 Q 都须保留正抽取概率。真实召回率及其精度仍依赖 Q 中假阴性的数量与实际抽样。即使 P 全取，F/I 真实阳性也可能很少或为零，分母退化时仍按原规则报告不可估计，不能强行报通过。代理抽样身份及机器答案应留在协调端，不进入编码者的盲判材料。

此方案只支持固定当前机器在当前 1261 条目标中的有限总体验证设计；不自动外推至全部 4481 条或未来政策，也不证明旧 91 的原随机代表性、真人完成情况或盲法事实。当前建议是保留此低工作量方向供后续明确分配时采用；不据此承诺总样本量 100 或 200 足够。
