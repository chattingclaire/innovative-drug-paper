# 候选08：当前命题与后项传播失败的只读机制核查

结论：015是已确认的语义关系误判。该次输出把抽象“是…过程”改写为“规定”，并把后列项目称为“明确承接”；五维的引文虽逐字正确，却没有证明这些内容属于当前命题。未找到本地组装、截断、ID/行顺序错配、schema强制全1或聚合覆盖标签的缺陷。字段名、材料呈现顺序与批次影响仍属假设，不能据一次理由判断内部因果。

## 审查身份与边界

主审为 `/root/llm_repair05`，也是08提示/作者控制准备者。8行提示/手册复核实际执行者是既有子代理 `/root/llm_repair05/content_analysis_methods`，它未编写08提示，但属于同项目、期待可见，不能称外部验证或真人独立验证。`independent`目录名不证明独立性。

本轮只语义阅读8个已暴露合成行，机械检查完整4924的keys/哈希/证书存在与标点；来源代码使用保持行号的保护投影。未阅读独立16的原文/期待/语义报告正文、保留267或新政策正文。新增模型/CLI调用均0，未修改冻结文件或生成09。

## 可核的执行证据

1. 015/016的source→frozen→batch packet→attempt→完整request逐层一致；d79c提示全文和第7行排除指令均在真实请求。唯一完成agent JSON与raw及最终行一致，均首次技术有效、零工具。015请求40303bytes/19195字符，016为41260bytes/19732字符；CLI记录input_tokens分别25166/25382，其计数还受未公开CLI/服务层包装影响。完整提示为36714bytes/17060字符，执行层2132字符。完整v1.3及v1.4实质段存在，v1.4验证纪律末段没有加入。
2. [runner](/PROJECT_ROOT/outputs/编码修订核查-20261008/LLM编码/候选08-命题与证据判定/runtime-unchanged-v2/run_production_v32.py:124) L124普通解析、L129按25行切批；L149建立rows包，L150默认`json.dumps(...,ensure_ascii=False)`，**没有sort_keys或重建行字段**。实际015/016均`id→text→contexts`。L59的sort_keys只做事件/raw规范化比较。因此交换text/contexts插入顺序会改变实际request；仅检查dict相等不够。
3. 015在第1批第17位，016在第2批第21位，二者不在同一请求。[原控制构造代码](/PROJECT_ROOT/outputs/coding-revision-20261008-r4/llm-candidate05-preparation/prepare_candidate05.py:117) L117–122自预声明即为定义/明确引导对照，L141–148依ID哈希固定顺序。可排除016紧邻造成的直接同请求泄漏；尚不能排除其他批次组成/行位置效应，也不能把此对照叫精确单因素实验。
4. [validator](/PROJECT_ROOT/outputs/编码修订核查-20261008/LLM编码/候选08-命题与证据判定/runtime-unchanged-v2/validate_binary_output.py:103) L103–144只核0/1、非空理由、连续引文及每个1有unit引文；[schema](/PROJECT_ROOT/outputs/编码修订核查-20261008/LLM编码/候选08-命题与证据判定/runtime-unchanged-v2/output_schema_codex_compatible.json:30)允许每维0/1，没有强制正类。通用unit引文加后项context引文能通过技术门禁，不能证明语义关系。validator L8–12已明确这一限度。
5. 两请求stderr各5个警告：状态库路径fallback与skills图标路径；无截断、context window、token limit或overflow指示。未有provider完整prompt回显、实际后端revision字段或角色分段证据；本地完整性不能证明模型确实阅读/遵从，也不能绝对排除隐藏服务处理。

## 字段到底表示什么

[初始输入构造](/PROJECT_ROOT/outputs/final-three-department-20261007/llm-v29/prepare_inputs_v29.py:49) L49–63最初按冒号和同组件附后4项，L70明示只消解关系、不继承标签。[v10](/PROJECT_ROOT/outputs/coding-revision-20261007-r3/complete_shared_material_v10.py:50) L50–80后来按已核来源完整区间补料；[v11](/PROJECT_ROOT/outputs/coding-revision-20261007-r3/complete_shared_material_v11.py:47) L47–63把完整列举与导航预览写不同role。[v14](/PROJECT_ROOT/outputs/coding-revision-20261007-r3/complete_shared_material_v14.py:70) L70–77保持单元文字/ID/顺序且两方法context一致。这些是来源/边界材料事实，不预先证明某维属于当前句。

完整4924均有`structured_following_units`键和顶层`context_usage`，前者148非空。其角色/证书交叉结果如下，证书重复不可相加：

| 非空字段的角色 | n | v11证书 | v27证书 | 当前句冒号结尾 |
|---|---:|---:|---:|---:|
| complete_actual_enumeration | 102 | 102 | 82 | 102 |
| local_navigation_preview | 27 | 0 | 0 | 27 |
| 无v11 typed status | 19 | 0 | 19 | 0 |

19条只是没有v11角色，全部有既有v27来源证书，不能说缺料。[规则侧adapter](/PROJECT_ROOT/outputs/coding-revision-20261007-r3/rules-v36.2-development/runtime/source_context_adapter_v34.py:136) L136–140仅把证书用作完整性/条件；L310–316将裸字段视为导航预览，**此adapter不在实际LLM调用链**。LLM直接收到原contexts。

015只有裸text-only后项，无生产`context_usage`、role或证书；这是合成与生产界面不完全相同的外推限制，不是事后取消负控制的理由。其固定期待和本轮FAIL保留。

## 当前146中的已暴露机制对照

| 控制 | 当前关系 | 08实际与本次判读 |
|---|---|---|
| C05-NEW-015 | 抽象过程定义；后列项目未由本句引导 | 实际五维1；确定五维传播错误 |
| C05-NEW-016 | “应包括下列”要求当前评价内容 | 五维1，支持 |
| C06-PAIR-04-A/B | 存档编号来源 / 必须满足所引证据条件 | 全0 / S、E，支持 |
| C06-PAIR-08-A/B | 自足保障延续+独立邻段 / 评价以下清单 | F / Ec，支持 |
| C08-PAIR-06-A/B | 当前必须提交五项 / 未来另发专题文件 | 五维1 / 全0，支持 |

这8例不构成146全体重新盲态验证。正例表明必要上下文不能删除，且同一structural字段不是必然全1；它们未隔离字段、文字与批次因素。[提示](/PROJECT_ROOT/outputs/编码修订核查-20261008/LLM编码/候选08-命题与证据判定/candidate08_prompt_PROPOSED.txt:7) L7和L15、[v1.4](/PROJECT_ROOT/outputs/coding-revision-20261007-r3/protocol/共用操作说明-v1.4.md:7) L7及v1.3 L17/65/146–148在此范围相容，未发现同一完整命题同时必须0/1。manual L148“从后项继承全部标签”有脱离缺料前提的宽读风险，但明确清单可逐维重新判读；不能宣称该措辞已证导致015过继承。也不能把“没有义务动词”或“定义句”一律判0。

## 有界的一般选项，尚未实施

- **先诊断呈现因素。** 保持原句、全部上下文、提示、模型和批次，分别隔离字段中性化与text/contexts顺序；生产role/usage补入是另一因素。先核实际request字节/键序，不能用语义dict相等替代。不删关键上下文，不将真实语义改写算成纯格式扰动。
- **若表示证据支持，再整理输入契约。** 使用既有来源证书和role机械区分导航预览/完整材料，字段名不授予维度继承。保留父谓词、援引条件、指代、表列和真正清单；原4924/240留存，不静默改输入。证书认证来源和边界，最终仍须判当前语义关系。
- **继续审查关系，不把技术门禁当语义判别器。** 普通语言说明当前谓词和context补什么、是否另项；现有理由已经要求此项，再添一句核对不等于已修。不能由关键词/冒号自动设0，不能用后一次输出替换首个输出。只有一般修复有证据才值得后续检查全部既有控制、已确认错误和240全部五维/理由/引文/子类/quality/issues；不得承诺κ或全文准确率。

以上是可供root选择的诊断/执行选项，本轮没有新测试输入、提示修改、模型调用或候选09。08当前保持**FAIL**；已完成146控制/7逻辑/7尝试，原240与4924均**NOT_RUN**，不采用、不拼接、不放低门禁。

完整来源SHA、逐层trace、代码行证据和假设/事实分列见[JSON主报告](/PROJECT_ROOT/outputs/编码修订核查-20261008/LLM编码/候选08-命题与证据判定/failure-mechanism-audit/candidate08_failure_mechanism_audit.json)。递归key频次见[metadata/order](/PROJECT_ROOT/outputs/编码修订核查-20261008/LLM编码/候选08-命题与证据判定/failure-mechanism-audit/input_metadata_and_serialization_order.json)，source SHA `6829d554cf5514e49565c7c58c4ffdb6f7768f9999b0eea49f114db023c03763`。本次主报告写入前后冻结闭包81项哈希全部一致。机械审查中的初始键名误计与API断言错误均单独留痕，更正未触及冻结来源。
