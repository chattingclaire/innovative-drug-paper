本目录交付一个基于 v18 算法、继承 exception-audit-v2 驱动护栏的隔离候选。最终构造控制 105/105 通过，真实 cohort 运行数为 0；未读取 run77、真实 800/4481 材料、Gold、真实标签或原失败政策正文。原正式 first 失败未被读取、覆盖或重新分类。本候选尚未构成正式 freeze，是否进入后续冻结由 ROOT 另行审查。

故障的数据流是：`RelationView` 的确指关系解析器生成 `material_requests`，构造末尾把同一请求保留到 `source_requests`；`Accumulator.finish` 原来优先使用显式维度，缺少显式维度时从当前正文 `TOPICS` 匹配主题词，具名机制则默认仅 I。缺失标准或列表的内容尚未知，当前正文可能只说“符合该标准”或“提供以下内容”，这时主题词筛选不能代表来源消费者，甚至得到空路由。驱动的依赖 guard 再逐请求检查 `needed_material` 或 `details.unresolved_material_requests`，因此正确拒绝没有完整传播的候选结果。

候选仅依据实际接口代码，建立封闭的潜在消费者契约。表中的五维表示“该类有界关系的缺失内容可能进入哪些现有谓词”，不表示真实缺失来源实际含有这五个议题。已知生成器的确指和适用条件保持原代码。

| 请求 path | 原生成器的适用条件 | 代码允许的消费者 | 构造证据 |
| --- | --- | --- | --- |
| substantive_list | `_lists` 要求当前有 INTRO 和 SUBSTANTIVE；确指完整成员范围不能闭合时才请求 | S、E、Ec、I、F | 完整有序成员仅含五维名词，受当前“应提供”谓词治理，五个现有谓词均得到 1；同一当前句缺少成员时保留五个 null |
| cited_standard | 操作性标准核验/资格后果、精确条文条件—待遇引用、完整条件组或表格同源定义的解析要求不满足 | S、E、Ec、I、F | 同源有界标准提供五维资料要求时现有五个谓词均得到 1；确指标准或条文缺失且当前句无主题词时保留未知 |
| named_mechanism | 当前实际实施具名安排，或创新药申请前适用/限制规范；同版对象/机制或组件边界缺失 | I、F | 完整具名来源的研发反馈服务得到 I3；对象定义中的尚无有效治疗药物缺口与优先审评机会得到 F；S/E/Ec 在具名关系分支被明确排除 |

消费者表由 `dimensions._units` 和各谓词的 `unit.kind` 分支决定。`_generic`、`_safety_effect`、`_economics` 不消费 named_mechanism；`_innovation` 和 `_fairness` 消费它。列表与标准展开为有界来源单位，实际送入全部五维现有谓词。构造的完整来源正向 witness 与缺源对照均保存在 `control-results-attempt03.json`，包含原始构造 bundle、关系 kind、原/候选值、引文、理由和请求。

`_material_request_route` 验证请求为具体对象，必须提供非空 `path/reference/missing`，只能是必要且未解决的依赖。已知 kind 可用合法显式消费者子集缩小路由；无显式子集时使用封闭消费者集合。空、字符串、重复、未知、与消费者不兼容或互相冲突的维度声明，以及未知 kind、已解决/非必要的伪 material request，全部抛 `MaterialRequestRoutingError`。没有主题词回退，没有任意 kind 的五维兜底，也没有按记录 ID、政策名称或失败内容加例外。请求原对象不被改写，保证原 guard 的对象匹配继续成立。

每个合法路由维度仍按原 accumulator 顺序处理：已有充分正向证据则保留原 1、原完整命题、原引文和原理由，并在 `details.unresolved_material_requests` 原样审计请求；没有充分正向证据且存在合法未解决依赖时输出 null，在 `needed_material` 原样保留请求，理由列明请求类型、确指内容及缺口；无相关请求的维度继续原判定。新 `material_request_routes` 记录路由版本、消费者、是否来自显式子集和未推断缺失来源主题的事实。

正向语义门槛没有改变。全部原顶层函数、Unit、正向累计方法以及原主题/阈值常量的 AST 均相同；四个其他算法模块与 v18 原字节相同。**0/null 的依赖不确定性范围明确改变**：原来当前正文无主题词而漏分配的标准/列表请求，现按可达消费者保留未知；具名机制补齐实际 F 消费者。这个更正不能宣传为“完全没有语义输出变化”，也不能据此推断真实失败记录需要哪些来源或实际影响哪些维度。

驱动的 dependency guard 保持原字节，`capture_exception_source_audit`、`dimension_slots` 及其他原辅助函数保持原 AST。精确白名单、reference/calibration 禁止读取、第一输出不得覆盖、冻结作用域及单次运行限制均保留。驱动版本与 freeze 的 fixed_algorithm_version 已改为本隔离候选，算法 manifest 精确绑定本目录五个实际模块；不将 v18 接入描述为 v17 原算法运行。正式手册 binding 只复制原文件，未重新打开其中外部手册或 seal。

控制除了缺源/完整源成对 witness，还验证了独立 S 保留 1、其他未知维度 null；五维独立正向证据全部保留原值/引文/理由；无依赖直接安全、疗效、制定宗旨及行政内容保持原值；合法显式子集不会影响无关维度；不合法请求保留原请求快照并形成五维技术失败；来源解析失败和 relation implementation error 不转成 0；原 guard 仍拒绝未传播的诊断五个 0；合法 null 的槽位掩码、异常时 live/returned 来源日志与深拷贝状态保持正确。

原材料的完整 source protocol 没有在本次执行。控制运行使用严格文件 audit allowlist，只读取声明的接口代码和 Python 标准库；完整读路径记录在控制结果。驱动只抽取原 guard、异常分支和槽位/快照辅助函数，对构造数据执行，不启动真实 cohort loop。白名单与完整作用域主程序的护栏此次有静态保留证据，不能把这些证据表述为真实来源阅读完成。

执行历史如实保留：attempt01 的 88 个控制通过；增强静态 AST 核对时，attempt02 的控制工具误把 AST targets 列表直接交给 `ast.dump`，在结果写出前得到 TypeError，错误说明单独保存；修正工具后 attempt03 的 105 个控制通过。该工具修正未更改候选算法。`actual-candidate.patch` 为实际差异，`input-bindings-complete.json`、`edit-provenance.json`、`report.json` 和 `seal.json` 提供输入、输出、版本及 SHA/bytes。
