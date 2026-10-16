# 五维未知值、失败与分母的独立数学核查

日期：2026-10-10。性质：prospective 接口审查与纯合成数学验证，**不构成任何真实标签结果或正式验收**。

本核查仅读取 `02-methods/unknown-and-denominator-policy.json` 和本目录自行构造的 toy 文件；未读取 pilot02、coverage 未封存结果、未曝光正文/语境或人工答案，未抽样、未运行新模型、未计算真实新标签。下文 D1–D5 为纯合成维度名称，不映射具体政策文本。

## 1. 可直接采纳的接口约定

输入以冻结的 assigned manifest 为主表，含唯一单位 ID、domain、固定非负权重、材料/规则/模型/参考版本以及角色。每个角色的最终结果是：

- `valid_output`：严格五个整数 `0` / `1` / JSON `null`，每个 semantic null 有来源或规则冲突原因。不得把字符串 `"0"`、Boolean、漏字段或不可解析响应静默转为 0/null。
- `execution_failure`：没有有效完成输出；与 semantic null 分开计数。
- `not_returned` / 尚未完成：assigned 单位在截止时没有输出；保留单独过程状态。最终报表不得以 observed-only inner join 删除它。

本 toy 接口采用**整份输出失败**：失败或未返回时五维标签均没有观测值；在数学补全中均可取 0/1，但原始过程状态保留。若工程计划支持按维执行失败，须在冻结接口中另列每维执行状态，并仅将失败维计入该维未决量；一个 semantic null 不删除同单位其余有效维度。

失败后按预先冻结的技术恢复规则重试，可将终态更新为有效输出；保留尝试日志，按单位与角色去重，每个 assigned 单位的分母和权重只进入一次，不能挑选较高分的尝试。无有效完成输出时，残缺响应中的“看似可用”标签不自动算已知值。

## 2. 分母与状态表

对同一 assigned domain 与维度 d，分别报告：

- `N_assigned` 与 `W_assigned=Σw_i`：包括 null、failure、未返回；是覆盖率分母的来源。
- A/B 各自有效 0/1 的边际 `n_A,d`、`n_B,d` 及其权重和。
- A/B **同时**有效 0/1 的 `n_pair,d` 及配对权重和；κ/P/R/F1 等来自这个维度的可比配对子域。
- 0/1/null 的完整 3×3 表；行 A，列 B。另保留 failure、未返回及其他过程状态的交叉分布。

`n_pair,d` 不能替代为 `min(n_A,d,n_B,d)`、任一角色有效边际 n、所有维度完整的 n 或 assigned n。相同角色的单维覆盖率使用该角色自己的已知 hit 和未决量，不以 A/B pair 子域计算后冒充全域关注度。

为了计数守恒，建议在审计层保留扩展状态的完整 joint table，再投影出 3×3 表和四格可比表。按 assigned 单位去重的 `any_failure` / `any_nonreturn` 不能简单把 A/B failure 边际相加：同一单位可能两边均失败。对于仅含 valid/null 与失败/未返回的接口：

`N_assigned = N_3x3 + N_outside_3x3`；`N_3x3 = n_pair + n_one_semantic_null + n_both_semantic_null`。

上述恒等式也须在权重质量上成立。加权四格表使用原 assigned 权重；标准化同一个配对子域内的权重不改变点估计比值，但不能因此改变估计对象或声称已代表 null/failure 子域。抽样误差与非响应所致识别范围是两个层次；区间推断仍须按冻结的抽样设计、层/簇/重复源关系处理。

## 3. coverage 边界：公式正确，未决量须完整

设 fixed eligible assigned 数为 N，已知该维 hit 数为 k_d，semantic null 数为 u_d^null，执行失败导致缺失数为 u_d^fail，未返回/待定数为 u_d^pending；另有合法接口中明确记录的非响应时亦计入。定义：

`t_d = u_d^null + u_d^fail + u_d^pending (+ 其他未决数)`。

只要每个未决二元值可独立取 0/1，且 N>0：

`p_d ∈ [k_d/N, (k_d+t_d)/N]`。

证明：令未决 hit 数为 x_d，则 `0≤x_d≤t_d`，`p_d=(k_d+x_d)/N`；全取 0/全取 1 分别达到端点。若 policy 的 u_d 已明确包含所有未决类型，可继续记为 u_d；若 u_d 仅指 semantic null，直接套公式会错误缩窄界限。

固定非负权重时，N 替换为 `W=Σassigned w_i`，k/t 替换为对应 hit/未决权重和。保留整数人数与权重质量两套量。**W=0 或 N=0 时 coverage 未定义**，不能返回 0。零权重未知值影响未知人数，却不影响这个加权 estimand 的识别范围。负权重不适用本单调边界，应拒绝。

这些公式适用于声明的固定 assigned 域。若用概率样本估计更大的有限总体，须声明 frozen design 下的目标分母与加权估计量，并另处理其抽样不确定性；不能把样本 assigned 数暗中称为总体 eligible 数。

## 4. attention share：H>0 的公式正确，H=0 需要分支

设 `H=Σ_j k_j`、`T=Σ_j t_j`。补全后 `q_d=(k_d+x_d)/(H+Σ_j x_j)`，仅在分母正时有定义。五维是多标签；同一单位可以给多个维度贡献 hit，但每个单位—维度至多贡献一次。

### H>0

每维的 tight marginal bounds 是：

`L_d = k_d/(H+Σ_{j≠d}t_j)`；`U_d = (k_d+t_d)/(H+t_d)`。

固定其他维 hit 增加本维 hit 时，q_d 不减；固定本维 hit 增加其他维 hit 时，q_d 不增。下界由本维未决全取 0、其他维未决全取 1 达到；上界由本维全取 1、其他维全取 0 达到。权重非负时相同推导成立。

这些端点对每一维分别可达；**不能将五个下界或上界当成共同可实现的 share 向量**。每个实际正分母补全的 q 向量总和为 1，端点向量可能不满足这一点。若未来引入互斥维度、确定性跨维约束或其他已知约束，上述界限仍可能是安全外界，但不保证 tight；届时须按约束集重新优化。当前五维独立二元补全下为 tight。

### H=0

所有未决取 0 的完成情景总是可行，因此必须报告 `zero_hit_completion_possible=true`；该情景 q 未定义。不能填入五个 0，也不能将 0/0 强制变为 0。另报告 `positive_hit_completion_possible = (T>0)`。

若 T=0：所有可行完成情景 q 均未定义，每维 bounds 为 null。

若 T>0，**在总 hit 正的完成情景中**，tight marginal bounds 为：

| 本维未决质量 t_d | 其他维未决质量 Σother t | q_d 在正 hit 情景下的 tight bounds |
|---|---|---|
| 0 | >0 | [0,0] |
| >0 | 0 | [1,1] |
| >0 | >0 | [0,1] |

这是混合识别结果：“undefined 是可行情景之一”＋“conditional-positive 数值范围”。例如只有 D1 一个 unknown，coverage 为 [0,1]；若最终有任何正 hit，share 必为 (1,0,0,0,0)，但全部补为 0 时 share 仍未定义。若 D1 与 D2 都可能 positive，两维各自 [0,1]，二者上界 1 不能同时取到。

部门差值只有在两域 share 均有定义的完成情景中才是数值。若两域的可行补全独立，可用 `[L_A-U_B, U_A-L_B]`；任一域存在零 hit 情景时，差值亦可能未定义，须保留标志。共享同一未知决策或跨域约束会影响 tightness。

## 5. κ、分类性能与正类一致率

固定四格方向：行=参考 A，列=预测 B；`a=TP(A1,B1)`、`b=FP(A0,B1)`、`c=FN(A1,B0)`、`d=TN(A0,B0)`。它们是可比 0/1 配对的计数或非负权重质量；`n=a+b+c+d`。

`P_o=(a+d)/n`；`P_e=((a+b)(a+c)+(c+d)(b+d))/n²`；`κ=(P_o-P_e)/(1-P_e)`。

`Precision=a/(a+b)`；`Recall=a/(a+c)`；`F1=2a/(2a+b+c)`。

`P_pos=2a/(2a+b+c)`；`P_neg=2d/(2d+b+c)`。

P_pos 与正类 F1 在同一四格表上数值相同，解释用途不同：P_pos 是不设优先角色的正类一致率；F1 用于有明确参考/预测角色的分类性能。交换 A/B 后 precision、recall 对调，P_pos 和 F1 保持不变；P_pos 不作机会校正，不能替代 κ，二者也不是两份独立证据。

NA 规则：n=0 时所有相应率未定义；P_e=1 时 κ 未定义；预测正分母 0 时 precision 未定义；参考正分母 0 时 recall 未定义；`2a+b+c=0` 时 F1/P_pos 未定义。单侧无正类而另一侧有正类时，直接四格定义的 F1=0，precision 或 recall 仍可为 NA，不能先把 NA 换成 0 再计算。若采用更严格的 F1 NA 传播约定，须在 frozen policy 中明示；本 toy 采用 direct-count F1。

全负全一致例：agreement=1，但 κ、P、R、F1、P_pos 为 NA；全正全一致例：P/R/F1/P_pos=1，但 κ 仍 NA。任何 NA 都不通过对应 0.8 目标。

## 6. 识别边界不等于 95% CI，数值达标不等于正式验收

本报告所有 unknown bounds 都是固定观测下的 partial-identification 区间，没有 95% 的频率覆盖含义；禁止用同一字段、列名或图例称为 95% CI。抽样 CI 使用另一个明确命名的字段与冻结的设计方法。稀有类、零格或退化 bootstrap 必須保留信息限制，不能凭宽度为 0 宣称证据充分；本核查不新增 CI 下界/半宽验收目标。

即便 κ≥0.8，缺少可核查的 human 身份、独立作业过程、冻结规则/材料、与参考形成过程，仍只能报告探索性的计算结果。正式 human-human 验收必须有实际独立人工执行，machine-vs-reference 的参考也须可信；不能用机器填补 human/reference unknown 后把它叫观测人工标签。policy 当前 `actual_human_execution_completed=false` 与 `final_acceptance=false` 不因本 toy 通过而改变。

建议引擎分开返回 `math_valid`、`metric_threshold_pass`、`provenance_gate_pass`、`formal_acceptance_eligible`，最后一项仍须满足其余 frozen 项目要求。门槛分项和维度分项不能用宏平均或其他诊断项替代。

## 7. 给 meaningful_math_checks.py 的透明接入材料

- `toy-boundary-cases.json`：7 个手工期望 boundary 案例、8 个四格指标案例、1 个角色边际/配对/九格案例、3 个正式验收必要条件案例。期望分数采用 exact rational 字符串；null 表示 undefined。
- `toy_boundary_enumeration.py`：标准库独立实现；所有 unresolved binary cells 穷举补全，逐维比较实际最小/最大值与闭式界限。仅从同目录固定 toy JSON 读输入，不发现或扫描项目语料；可 import 函数与 `run_checks`，也可作为子进程运行。
- `toy-enumeration-result.json`：本次成功运行的 exact-arithmetic 结果；无真实标签或模型调用。

父引擎可以读取 fixture，将 `Fraction(str(x))` 转成数值与自身输出逐项比较。浮点比较应使用明确容差；undefined 比较用状态/None，不用 NaN 的相等测试。本独立实现可作 oracle，但有意义的测试应调用父引擎自己的入口后比较 JSON 的手工 `expected`，避免仅再次运行本文件证明自身一致。

其中 `per_dimension_marginal_vs_pair_n` 期望 assigned=7、weight=11；D1 的 A/B 有效边际分别 4/4，但 pair=2，pair weight=3。D2–D5 的 pair 数分别 3/3/4/4，说明一个未知维不得全行删掉。五维同时完整的配对数仅 1、权重质量 1，应作为独立诊断而不是各维默认分母。D1 九格合计 4 人、质量 7；outside 九格 3 人、质量 4。失败与未返回各有独立计数，不能归入 semantic null。

本次运行采用 `--full-sweep`：除固定案例外，覆盖一个单位五维全部 243 种 0/1/null 模式，加两个不同权重单位五维全部 59,049 种模式；每个模式再穷举其中所有未知二元补全。全部比较使用 Fraction 精确算术。

运行：

```bash
python3 toy_boundary_enumeration.py --full-sweep
```

结论：policy 已写出的 H>0 coverage/share 公式数学正确；未来接口须显式实现 H=0 的“undefined 可行＋正 hit 条件边界”，将 failure/nonreturn 计入未决质量而独立统计，并以每维实际 pair n 计算可比子域指标。本核查批准这些数学约定的 prospective 实施，不批准任何真实结果或正式验收。
