# full4481 两域方案的独立风险与合成边界复核

日期：2026-10-10。范围：remaining1444 固定 n=600，加 exposed3037 的 n=200 / n=400，对应 full800 / full1000。结论基于白名单元数据、旧预测辅助量和方法层表，**不是新实际编码、真实参照或正式验收结果**。

本代理仅读：`inputs/metadata-and-fixed-labels.jsonl`（4481 白名单 metadata/oldpred）、`small-plan-comparison.json` 的方法信息，以及母代理明确提供的 `full-domain-supplement/full-domain-allocation.json` 方法层表。未打开层表中引用的原始预测文件、正文、语境或真实参考；没有抽取 ID、选择 seed、创建人参照或运行新模型。所有新增内容只写在本 independent-risk 目录；原交付保留。

## 1. 两域设计的有效性与旧辅助量的作用

元数据容量 independently 核对：remaining=1444；exposed=direct2770+family_only267=3037；共4481。exposed 旧五维双机全阴层：NMPA612、NHSA820、NHC315，共1747。remaining 对应层为536/348/91。两个 full 方案保持 remaining n600，新增 exposed n200/400；方法层表中每个非空层具有正 inclusion probability，单单位层普查，非普查层有 n≥2。

抽样前冻结的旧 rules39/LLM03 只作为 stratification/allocation auxiliary。设未来最终手册/机器版本/独立编码产生某个固定有限总体 cell indicator y_i，只要冻结选择机制不根据其实际答案调整，且每个目标单位 π_i>0：

`E_design[Σ_sample y_i/π_i] = Σ_population y_i`。

因此旧 auxiliary 与未来 actual prediction 不相同，不会使 HT cell-total 估计失去设计有效性；它会改变层内变异和正类/错误分布，从而削弱原来的效率。κ/P/R/F1 是这些总量的非线性函数，不能把 HT 总量无偏性写成 κ/P/R/F1 本身无偏或其区间自动足够窄。

full 域必须先合并各层设计加权 cell totals，再计算 κ/P/R/F1；不直接合并 raw800/1000 四格，也不按域容量平均两个域的 κ、Precision 或 Recall。remaining 的600占 raw800的75%、raw1000的60%，但其总体占比仅1444/4481≈32.22%；exposed 人群占比约67.78%，失衡对全域解释有实质影响。

exposed 域纳入概率审计后，可评价冻结版本在这4481条有限语料上的表现；这不会抹去3037条已有开发/曝光历史，也不会把全域结果转换成未曝光测试或未来语料泛化。真实 human 独立初始执行、可信裁决与冻结过程仍是正式验收的前提。

## 2. 实际全阴层的 inclusion probability 与漏检概率

每行是**单独的纯合成假设**：该层有 T 个未来新预测正类、实际比较轴正类或某个指定错误类别，其他层的分布不由本表指定。设在层 h 内 SRSWOR 抽 n_h 条，则：

`K_h~Hypergeometric(N_h,T,n_h)`；`E[K_h]=n_hT/N_h`；

`Pr(K_h=0)=C(N_h−T,n_h)/C(N_h,n_h)=∏_{j=0}^{T−1}(N_h−n_h−j)/(N_h−j)`。

T≤N_h；n_h>N_h−T 时该概率为0。下表用实际层容量和分配，T是合成数，不是观测 prevalence。

| 方案 | exposed 旧全阴层 | N_h/n_h | π_h | T=10 时全漏 | T=20 时全漏 | T=20 时预期抽到个数 |
|---|---|---|---:|---:|---:|---:|
| full800 | NHC | 315/11 | 3.49% | 69.72% | 48.01% | 0.70 |
| full800 | NHSA | 820/30 | 3.66% | 68.74% | 47.03% | 0.73 |
| full800 | NMPA | 612/22 | 3.59% | 69.15% | 47.52% | 0.72 |
| full1000 | NHC | 315/22 | 6.98% | 47.95% | 22.42% | 1.40 |
| full1000 | NHSA | 820/59 | 7.20% | 47.19% | 22.05% | 1.44 |
| full1000 | NMPA | 612/44 | 7.19% | 47.15% | 21.94% | 1.44 |

这些精确 design miss probabilities 不是95%CI，也没有为真实类别数 T 作推断。若已明确每层合成 T_h 且各层独立，总体全漏概率才可相乘；不能从未知真实类别分布中选择最有利的单层结果作为全域保证。

旧阳性保护不能转移给未来新阳性：remaining 的旧 I/F 阳性全部入样，保证的是历史 auxiliary 正类层的覆盖；exposed 的旧 I/F 相关类别本身也未全部普查。未来 actual prediction 或未来比较轴阳性若迁入上表低π层，n800/1000仍可能只贡献0、1、2个相关正类单位。

## 3. 合法全域四格：大 n 可以得到 NA 或过于乐观的点值

以下是抽象的预测轴/比较轴 category counts，不给任何 real ID 赋值，不构造任何 human/reference ledger。方向：`a=TP,b=FP,c=FN,d=TN`。

纯合成总体：exposed NMPA 旧全阴层612条中 `(a,b,c,d)=(16,4,4,588)`，其他3869条均为TN。全4481条四格为 `(16,4,4,4457)`。它数学上合法，predicted-positive 和 comparator-positive 均20，active union 为24：

`Precision=Recall=F1=0.8`；`κ=17824/22305≈0.799103`。

这说明即使三个分类率恰为0.8，κ也必须独立检查。

在实际 n22/n44 的 SRSWOR 层内，存在两种合法的抽样完成情景：

- **24个 active categories 全部漏掉**：raw full 四格分别为 `(0,0,0,800)` / `(0,0,0,1000)`；设计加权四格均为 `(0,0,0,4481)`。agreement=1，但 κ、Precision、Recall、F1 均NA。其 design probability 分别为40.82% / 16.10%。
- **只观到1个TP，未观到FP/FN**：其余 sampled units 全为TN。raw正类分母仅1；设计加权TP分别为612/22=27.82、612/44=13.91。κ/P/R/F1点值均1，但总体合成值仍为前述0.8/.7991。加权正类质量27.82或13.91不是27或14个独立实观正类；这个情景的正类 Kish 信息诊断为1，不能作为设计CI公式或验收目标。

还有一个补充稀疏错误案例：在 remaining 的旧I/F普查区域141条中放置80个合成TP，在 exposed NMPA旧全阴层放置20个合成FN，其余全TN。合成总体四格 `(80,0,20,4381)`，P=1、R=0.8、F1=8/9、κ=35048/39529≈0.886639。两个方案漏掉全部20个FN的概率仍分别47.52% / 21.94%；样本可包含80个合成正类单位，却给R/F1/κ点值全1。这说明“分母非零”也不等于已获得充足错误信息。

这些案例描述抽样信息风险，不把抽象比较轴宣称为人工真值，也不把合成点值填进项目结果表。

## 4. 旧 auxiliary 失配后：设计有效但效率可明显下降

仍以未来某类别T=20全部处在 exposed NMPA旧全阴层为纯合成情景，HT总量的期望恒为20。精确二元 category-total design variance 为：

`Var(T_hat)=(N_h−n_h)·T·(N_h−T)/((N_h−1)·n_h)`。

full800 为3492800/6721≈519.68，full1000 为1681280/6721≈250.15。若仅作数学基准，整个4481总体用同样总n的单层SRS、同样20个正类，variance分别约91.63与69.32；上述 auxiliary 失配情景的variance约为基准5.67倍/3.61倍。这个基准不是替代方案，也未满足“remaining必须600”的约束；用途只在于证明旧辅助配置不保证未来新类别效率。

这里计算的是明确固定合成 category total 的精确 design variance，**不是实际 κ/P/R/F1 95%CI，也不是 anticipated linearization width**。它不支持“真实区间会恰有某宽度”的结论。即便总样本从800增至1000，这个未来类别的预期有效观测也只从0.72到1.44。

## 5. human κ、machine 稀疏分母与验收边界

纯 algebra human A/B 示例，不对应任何真实人：

| 合成 A/B 四格 a,b,c,d | Po | A/B positive margins | κ | Ppos |
|---|---:|---|---:|---:|
| 4,1,1,994 | 0.998 | 5/5 | 159/199≈0.798995 | 0.8 |
| 1,4,0,995 | 0.996 | 5/1 | 199/599≈0.332220 | 1/3 |
| 0,0,0,1000 | 1 | 0/0 | NA | NA |

低阳性时Pe接近1，κ对少量正类/分歧及不等边际敏感；高Po或总n1000不能替代 κ 的实际信息量。机会校正、正类一致率和边际状态应同时报告，不能把Ppos改称κ。

machine 纯algebra例：四格 `(2,0,0,998)` 时P/R/F1/κ均1；仅增加1个FN并保持n1000，即 `(2,0,1,997)`，R变为2/3、F1为0.8、κ=997/1247≈0.799519。若预测正类为0、比较轴有2个正类，P=NA、R=0、F1=0；反向则R=NA、P=0、F1=0。双方无正类时P/R/F1/κ为NA。大总n与小正类分母并存，区间可能宽、退化或未定义，必须按真实 frozen design 与实际 cells 报告。

unknown/failure 另行保留 assigned 单位、边界和可比pair n；正类的语义缺失或未完成输出不能换成0以制造分母或通过率。机器不能填补 human/reference unknown 后冒称 observed human。

**保持既有每维0.8点目标。** 95%CI用于描述实际精度；本风险说明不新增CI下界、半宽、额外阳性数量或隐含样本量验收门槛。规划 linearization widths、合成variance与漏检概率都不属于真实主结果CI。正式验收仍依赖实际独立human身份、冻结过程、可信reference、目标scope和实际数值；不得按“补抽直到过0.8”改变冻结设计。

## 6. 可复核交付

- `risk-inputs-and-toy-cases.json`：只含聚合metadata容量、actual method N/n投影、明确synthetic四格和手工期望；三份允许读取源有SHA256绑定，无real ID。
- `risk_math_checks.py`：仅从本目录固定fixture读取，标准库 exact Fraction 算术；超几何乘积与组合式/PMF分别交叉核查；验证概率和为1、E[K]、HT期望/variance，以及toy四格与合法sample pattern。不抽样、不调用模型、不创建95CI。
- `risk-math-results.json`：30个miss cases、7个独立四格案例、6个合法sample patterns及2个精确variance检查全部通过。real ID draws=0、real human/reference labels=0、new model calls=0、formal_acceptance=False。

结论：full800/full1000在正π、固定设计和可信新执行下可支持4481有限总体概率审计；辅助量失配与旧全阴低π层使正类/错误信息可能稀疏，full1000降低风险但不构成精度保证。总样本数不能当作κ或P/R/F1的有效正类分母；实际结果必须保留加权cells、逐维分母、unknown/failure与设计一致区间的具体证据。
