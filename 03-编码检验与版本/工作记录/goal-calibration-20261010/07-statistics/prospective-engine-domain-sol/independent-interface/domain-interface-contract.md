# 冻结统计域接口的独立契约与合成期望

日期：2026-10-10。性质：代码/方法schema与纯toy接口核查，不是实际标签统计或正式验收。

本任务只读取旧engine源码、新domain源码草稿和 full-domain-allocation.json 的N/n/schema。未读取预测、sourcebody、真实标签或新draw IDs；所有本目录ID都以toy-only命名，自行构造，无现实成员含义。原封存交付保持不动。

## 1. 固定成员关系与元数据模式

权威成员关系是 `record.stratum_id → frozen stratum.domain`；合法值只有 `remaining` / `exposed`，每个单位只属于一个设计域。不要从ID前缀、标签、null/failure、旧/新机器输出或编码结果推断domain。global assigned IDs唯一、每层实际行数等于冻结n，保证单位互斥且nonresponse行保留。

字段映射：本文和独立oracle中的概念名 `domain_N` 在母engine实际schema中为 `design.domain_population_N`；full-domain方法表的 `domain_N` 不能直接作为同名engine字段。独立动态adapter显式完成这一映射。母engine另外支持 `design.domain_partition="remaining_exposed"` marker：marker存在时必须有双域；仅声明合法单域时不写该marker。

使用显式模式开关，而不是用 truthiness 回退：

| 情况 | 安全行为 |
|---|---|
| 所有strata都没有domain字段，design也没有domain_N | 允许legacy；只保留旧ALL/department行为，不宣称拥有remaining/exposed分解 |
| 任意stratum有domain字段 | 激活新模式；所有strata必须有合法非空字符串domain |
| domain部分填写、显式null、空串、非法值或非字符串 | 拒绝；不能将unknown design membership补成remaining/exposed或legacy |
| domain_N存在，但所有strata未填domain | 拒绝；总数声明无法替代逐层成员关系 |
| 全部strata正确填domain，domain_N缺省 | 可允许，按冻结strata ΣN推导并标记derived来源 |
| domain_N提供 | 必须为mapping，keys与实际非空设计域集合相同，每个值strict正整数，逐域等于Σ该域层N；bool/float/错误N/额外空域均拒绝 |
| 只有remaining或只有exposed的合法design | 可作为单域分析；只输出存在的域，不制造另一空域；full4481范围声明另按正式scope要求审查 |

full800/full1000方法表含ΣN=4481、remaining_N1444、exposed_N3037；remaining_n600，exposed_n200/400。每个正容量层n≥1，非普查层n≥2、π_h=n_h/N_h>0，已有methods适用。domain_N必须是总体容量，不能误填assigned n600/200/400。

新模式要从冻结stratum.department计算domain×department population结构，应要求各层department为非空字符串且每条record.department相同；缺失、多个部门的list、null/空串或冲突应拒绝。只观察到样本全部属于某部门，不能证明整层总体均属于该部门。

若工程选择允许混合部门层的观察域HT分析，则必须另定义该模式：不从Σ层N推出department_N、不凭样本部门宣称census、把部门总体质量作为域估计量而非已知容量。没有该模式时，新域schema应采用上述严格冻结部门策略。旧无domain设计保持既有宽松部门与census保护行为。

## 2. N、权重和掩码守恒

概率stratified SRSWOR、全部assigned行保留时，逐层 `Σassigned w_i=n_h·N_h/n_h=N_h`；因域互斥：

`N_ALL=N_remaining+N_exposed`；

`W_ALL=W_remaining+W_exposed`；

`C_ALL[a,b,c,d]=C_remaining+C_exposed`（按cell逐项）。

domain×department mask是两个冻结条件的交集。ALL包含全部单位；department mask跨两个域；一个domain mask跨全部该域部门；交叉mask两者均满足。mask不能先删unknown/failure，也不能按某一角色的完成情况决定成员。

κ/P/R/F1来自本mask的按维comparable0/1 pairs。角色边际有效n、pair n、assigned n分别报告；某维null/failure不删除其他维。九格0/1/null及第四failure状态保留本mask全部assigned权重；attention分母同样是全部assigned权重。failure subtypes可另计，但仍包含于未知边界质量。

nonprobability开发材料按旧规则w=1，故W等于assigned n；不能对它套用概率design的W=N总体恒等式或人口CI。

## 3. empty、NA、census和numeric状态

合法正容量域会有至少一个正n层，因此不应产生zero assigned-weight的活跃design域。空domain×department交叉可以省略；若固定schema必须保留，需明确empty status、n=W=0、所有相关率/边界NA、numeric不通过，不进入要求positive denominator的attention公式。不能把空share变成五个0。

整个domain是否census，应检查该冻结域的所有总体成员层均n=N；不能只看comparable rows，也不能让另一域的noncensus剥夺本域真实census。department/intersection census同样依赖完整冻结部门归属。完整语料审计里semantic null/failure仍可存在：census只消除抽样误差，不消除标签未知或分母NA。

ALL点值从合并weighted cells计算；各域点值分别从本域weighted cells计算。κ/P/R/F1等非线性指标不能直接平均，numeric Boolean也不取均值。full点目标通过与remaining/exposed各自点目标通过可能不同；域flags用于各自scope的数值报告，不能暗中新增“所有域必须通过”的全项目门槛。

formal_acceptance仍恒False。冻结hash能绑定文件/ID/投影/设计版本，不能认证“人类”“独立作业”“可信裁决”等事实；真实身份及流程仍需外部项目复核。指标NA均不通过对应0.8点目标；不新增CI下界/半宽目标。

## 4. 独立toy oracle与手工期望

本目录 `domain-toy-cases.json` 与 `domain_toy_oracle.py` 不import母engine；`domain-toy-results.json` 已通过21个元数据允许/拒绝case、9个非空mask及精确Fraction守恒检查。它们是接口预期，不是母engine已执行测试的证明。toy selector使用`domain:…|department:…`，可映射到母engine最终命名。

透明基例：四层N/n为remaining Alpha4/2、remaining Beta2/2、exposed Alpha6/2、exposed Beta2/2；assigned n8、W14。含1个semantic-null pair单位与2个failure pair单位：

| mask | assigned n/W | pair n/W | weighted a,b,c,d | κ |
|---|---|---|---|---|
| ALL | 8/14 | 5/11 | 5,2,3,1 | −2/53 |
| remaining | 4/6 | 3/5 | 2,2,0,1 | 2/7 |
| exposed | 4/8 | 2/6 | 3,0,3,0 | 0 |
| department Beta | 4/4 | 1/1 | 0,0,0,1 | NA |
| exposed×Beta | 2/2 | 0/0 | 0,0,0,0 | NA |

Beta和exposed×Beta均为真实toy census，尽管后者所有pairs均含failure。assigned denominator仍为2，pair denominator为0；这不是empty domain。ALL κ−2/53也不等于两个domain κ的均值1/7。

独立numeric toy：remaining四格(1,1,1,1)，exposed四格(99,0,0,99)，合并(100,1,1,100)。full κ=99/101、P/R/F1=100/101，通过0.8点目标；remaining不通过，exposed通过。三个flags分别保留，formal=False。这个纯cell例证不引入任何real human/reference identity。

## 5. 旧行为与新源码的后续静态复核

本次读取旧源码和新目录初始copy时，两者SHA256均为 `7d6f75594745f0e2d6cf9e211c789bd5006630064089116c7553e2f7770ba0f1`。新copy尚未domain扩展，故此契约不将其宣称为扩展已经通过。

新源码完成后，另写 `domain-source-review.md` 记录其实际hash与逐项静态结论。母代理可用本oracle的expected比较自己的新入口，并用完全无domain的相同合成输入对比old/new的既有数值、状态、旧department mask与census行为；代码来源/version/provenance及新增字段可以不同，不能把旧结果重新解释为有未声明的exposure分解。
