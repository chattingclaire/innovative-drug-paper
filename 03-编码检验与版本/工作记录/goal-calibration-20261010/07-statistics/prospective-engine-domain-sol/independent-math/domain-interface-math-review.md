统计域接口的独立数学与人工 toy 复核（2026-10-10）

结论：新版以完整 source-unit 设计的一份 W 支持 ALL、remaining、exposed、department 及 domain×department 视图，符合本任务的域掩码数学。未发现阻断性数学或域接口问题。旧无 domain 设计的核心数值、unknown/failure 处理及现有输出行为保持一致。

只读取旧/新 metrics_engine.py、获准 allocation 的 strata N/n/domain/department schema，以及本目录人工 toy 产物。未读取项目新/真实标签、预测、正文、语境、draw IDs 或项目统计结果。旧版文件未修改。新版执行仅限由独立脚本生成的 15 个人工总体单位、10 个人工已抽单位的 toy；没有实际项目执行。

最终绑定的旧版 SHA256 为 7d6f75594745f0e2d6cf9e211c789bd5006630064089116c7553e2f7770ba0f1；新版 freeze SHA256 为 05f5999084a48b0e713e28f81e629015e61c1255cdaa43e89d30a6b59eed1d30。schema 投影与其他读写产物哈希见 domain-read-scope-bindings.json。allocation 只做 schema 兼容性核查，未用其 N/n 构造或执行项目标签统计。

独立数学脚本 independent_domain_mask_checks.py 使用标准库：穷举 108 个原设计样本和 8 个条件 Rao–Wu 结果，通过 86 项相关检查。独立接口脚本 independent_domain_interface_checks.py 只在人工 payload 上调用旧/新引擎，通过最终 179 项检查；期望协方差由本目录独立数学 helper 计算，未采用母实现的协方差作为预期答案。本任务没有重复此前 11079 项合成规划比较。

域 D 的正确计算是在原完整 n 个已抽单位上定义 \(X_D(i)=1(i\in D)X(i)\)，把域外单位的分析值置零，再计算

\[
\widehat T_D=w^\top X_D,\qquad
\widehat T_D^{*(b)}=W_b^\top X_D,\qquad
\widehat V_D=\sum_h\frac{N_h^2(1-n_h/N_h)}{n_h}s_{h,X_D}.
\]

其中 s 是原层完整 n_h 个样本值（包括域外零值）的样本协方差。不能删除域外单位后重新定义 n_h、N_h、FPC 或生成子域 bootstrap 权重。新版 analysis_scopes 返回完整长度 mask；analyze 入口只调用一次 rao_wu_weights；全部比较、方法、五维、attention 和视图均对同一完整 W 做矩阵运算。直接捕获人工调用确认只请求一次 W，11 个非空视图共用同一 W SHA；每个视图输出的 assigned weight 和 replicate assigned total range 与冻结整层总体 N 一致。空的 remaining×department C 视图未输出。

一个互斥完备域划分使每次实际样本、每次共同权重重复的向量总量相加。一般协方差恒等式是

\[
V(\widehat T_D+\widehat T_E)
=V(\widehat T_D)+V(\widehat T_E)
+\operatorname{Cov}(\widehat T_D,\widehat T_E)
+\operatorname{Cov}(\widehat T_E,\widehat T_D).
\]

remaining/exposed 在新设计中各由完整互斥固定层组成、层间独立抽样，故交叉协方差为零，V(ALL)=V(remaining)+V(exposed)。同理，冻结部门与交叉域如果是互斥完整层划分，其协方差可相加。域与部门视图若重叠，则保留共同层的交叉协方差；它不因视图名称不同而消失。

旧无 domain 设计允许一个抽样层内存在多个观测部门，此时部门单位虽然互斥，SRSWOR 仍使其设计总量相关。独立反例为 N=4、n=2 的一个混合层，两个固定部门各有 2 单位，对常数1的部门总量真实协方差为

\[
\begin{pmatrix}4/3&-4/3\\-4/3&4/3\end{pmatrix}.
\]

ALL 总量严格为4、方差为0；部门方差单独相加则错误地得到8/3。对含每部门各一单位的人工样本，原设计 FPC 样本协方差估计为 [[2,−2],[−2,2]]。新版实际接口保留此矩阵，未对子部门重抽或把它们当作独立层。无完整冻结 department 归属时，部门 view 的 frozen_stratum_ids 和 population_N 为 None，且不能声称该部门已全取；其样本视图、点估计和完整设计 mask 方差仍可计算。

κ、precision、recall、F1 以及 attention share 都是非线性函数。full 必须由其所需加权分子/分母或四格总量相加后计算函数；不得按 1444/3037 的域大小平均域 κ/F1/precision 等。新版对每个 mask 独立形成加权四格并计算指标，未平均域指标；global 原点目标仍只针对 ALL，per-scope 数值标识单独输出，formal_acceptance 均保持 False，没有新增 CI 下限或半宽门槛。

域全取判定有两个合法途径：整个总体 n_h=N_h 时，任何完整观测的部门子集都没有抽样误差；否则，必须通过冻结的完整层归属知道该视图包含哪些总体层，且这些成员层全部 n_h=N_h。观测成员恰来自全取层不足以排除其他未抽单位属于该部门。新版 named domain 要求每层 domain∈{remaining,exposed} 且 department 明确，记录 department 与冻结层一致；部分 domain 声明、缺 department、错误域总数、跨域独立输入/协议/seal override 和记录级 domain override 均拒绝。最终补强的根 payload override 拒绝与记录 department 显式绑定也经过独立人工检查。

人工交叉视图 exposed×department A 是全取，而整个 department A 还包含非全取的 remaining 层。新版前者的已定义 κ=[1,1]，后者全取标识为 False。非全取 remaining×department A 即使样本 A/B κ 恒为1，其退化 bootstrap 也不声称有效 [1,1] CI。singleton census 合法，其重复权重保持1；非全取 n=1 仍被拒绝。未知/零分母指标即使来自 census 也保留 undefined，不能以“没有抽样误差”创建未定义点值。

新版 view guard 只缩小对应完整层集合的有限计数宇宙，不改变生成 W 的 prepared 设计。独立以 joint16 模式核对每个 view 的成员层、N 合计和 alpha/(H_view×16)，并确认 guard 调用没有再生成或缩小 W。这些 count guards 的 coverage 仍是一个 view×comparison×dimension 内的声明，不是所有域、部门、指标的 simultaneous95；其非线性投影仍明确未实现。Bootstrap 百分位与 guard 不互相代替。

人工加入 semantic null、整方法执行失败、维度执行失败和 missing return 后，再核查全部 11 个视图、5 个方法、5 维。unknown/failure 保留各 view 的 assigned 权重分母，full16-state 表合计 assigned mass；没有将未知行删除或重编码为0，也没有重新归一化声称完整域性能。二元指标仍限两个方法均完成0/1的可比子域，并同时报告全部 unknown/failure 表。非概率设计的 named 视图不会产生 W、人口 CI 或 census 标识。

去除全部 domain 元数据的人工 payload，在旧版与新版使用相同 source W 时，旧版所有 comparison 已有字段、attention、部门 contrast、numeric_targets 和 project_review 完全一致；新增 scope 描述和 schema 1.1 字段不改变旧结果。旧全局 census 但未声明层 department 的情形保留合法原行为：所有单位已观察到，观测部门子集可以按其实际完整成员计算 N 与无抽样误差结果。

人工接口核查使用等概率穷举的 8 行条件 Rao–Wu W，是为了精确核对域矩阵运算，未把它作为项目实际区间或 B=5000 的正式运行。母 API/CLI 默认 B=5000、seed=20261010 和 linear 分位数规则保留；未来实际执行仍须核对冻结调用参数、共同 ledger、身份、源及分析范围。解析协方差与梯度仅作 secondary 诊断，不能替代 primary 共同重缩放 bootstrap 边际95百分位区间，也不构成有限样本精确覆盖率证明。本次没有新增验收门槛、AC1 macro、CVI 或 KMO，未执行真实指标，接口与冻结检查 PASS 不等于真实数值达到 .8。
