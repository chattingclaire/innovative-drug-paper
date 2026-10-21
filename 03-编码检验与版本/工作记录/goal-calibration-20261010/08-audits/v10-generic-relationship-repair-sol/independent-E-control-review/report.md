# clinical_comparison_without_innovation 独立 E 控制审查

结论：原固定 fixture 足以支持其已冻结的 E=1；old/new E=0 来自旧 E 规则的词义覆盖缺口。该结论依赖当前原文与冻结手册，未用旧标签、gold、native、准确率或通过数量作语义裁定依据。没有改 E 逻辑、既有期待值、fixtures 或五模块，也未执行 classifier 或模型。

## 原文、固定期待与材料范围

原控制位于 [原 fixture](</PROJECT_ROOT/outputs/goal-calibration-20261010/08-audits/v9-generic-relationship-repair-design-sol/revision02-bidirectional-before-implementation/synthetic-controls-fixed-before-edit.json:101>)（L100–L118）；当前完整句为：

> 应比较药物与现有治疗的完全应答率。

该项 `contexts=[]`，固定期待是 `E=1, I=0`，原解释为“普通效果比较无创新联系”。这里引用期待与原解释仅为保留审查对象，语义理由另由原文和手册建立。原文对象是“药物”，动作是“应比较”，比较基准是“现有治疗”，比较内容是“完全应答率”。这是当前药物治疗效果指标的实质比较要求，不是“临床价值”空泛提及、仅治疗用途、一般开展试验、研究程序、格式或资料流转；不需要从创新身份或兄弟成员补足效果内容。E=1 表示效果议题在场，不表示应答率更高、药物已有效或优于现有治疗。I 没有从该效果比较自动产生依据。

冻结手册 [共同实质门槛](</PROJECT_ROOT/outputs/goal-calibration-20261010/03-manual/full4481-common-release-20261010-root/manual.txt:9>) 逐字规定：“当前句段实质讨论、规定、评价、比较、要求证据，或实际安排直接对应某维内容的措施，均可表示关注”；同时规定“否定、不确定、尚未实现的要求也可纳入”。当前的“应比较”符合实质比较要求，不要求已经得到比较结果。

[§四 E 定义](</PROJECT_ROOT/outputs/goal-calibration-20261010/03-manual/full4481-common-release-20261010-root/manual.txt:94>)：“药物防治效果、健康收益、临床获益及支持这些判断的证据。”

[§四 E 纳入](</PROJECT_ROOT/outputs/goal-calibration-20261010/03-manual/full4481-common-release-20261010-root/manual.txt:96>)：“疗效、疾病控制、生存、健康相关生命质量、治疗优势、对应的药效研究/效果比较及证据要求”；本项属于对应的效果比较。[§四 E 排除](</PROJECT_ROOT/outputs/goal-calibration-20261010/03-manual/full4481-common-release-20261010-root/manual.txt:98>) 所列“只说开展试验、一般机制、收集数据或方法步骤，而无药物效果联系”与“仅治疗用途、适应症或笼统‘临床价值’”均不描述本项当前命题。

手册 SHA256：`5ea7ab74d30fb79c4cbd1d7d6b2ae40c4f52a52360075f3552199de949f9cc7b`。fixture 全文件 SHA256：`91909de53922d18be62f809d62189dc1b8cf2b6f59adb88af761dbc9a5a13de7`，与 attempt08 pre-execution seal 中绑定相同。

## old/new E=0 的静态原因

[原运行脚本](</PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding/rule-five-dimension-joint-root/versions/joint-v9-generic-relationship-sol/run_finite_controls.py:4>) 将 old 五模块设为 `joint-v8-target-product-gap-sol`；L17–L20 精确绑定 revision02 原控制及四份既有补充控制。[attempt08 pre-execution seal](</PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding/rule-five-dimension-joint-root/versions/joint-v9-generic-relationship-sol/attempt08-final-governance-controls/pre-execution-seal.json>) 也保留这一 old_code 绑定。本审查只读取此目标项的既有输出，不重新执行脚本。

[attempt08 中该控制的既有记录](</PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding/rule-five-dimension-joint-root/versions/joint-v9-generic-relationship-sol/attempt08-final-governance-controls/results.json:199507>) 保存 old E=0、new E=0；两侧 E 决策均为 `basis_path=no_substantive_relation`，原理由逐字为“当前完整命题未表达本维的实质内容、证据要求或直接制度关系。”两側 `near_candidate_exclusions=[]`、`needed_material=[]`、关系 traces 都为空。上述是既有程序行为记录，不是 E=0 的正确性依据。

具体旧路径如下：

| 静态位置 | 原逻辑与本句的关系 |
| --- | --- |
| [v8 OBJECT](</PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding/rule-five-dimension-joint-root/versions/joint-v8-target-product-gap-sol/relations.py:11>) 与 [v8 object_evidence](</PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding/rule-five-dimension-joint-root/versions/joint-v8-target-product-gap-sol/relations.py:1840>) | 对象模式明列“药物”“治疗”；当前句已直接表达药物对象，不需要旁文，不是对象缺失。 |
| [v8 _generic](</PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding/rule-five-dimension-joint-root/versions/joint-v8-target-product-gap-sol/dimensions.py:402>) | L407–L408 直接跳过 S/E/Ec；所以 TOPICS[E] 未覆盖“应答率”只是旁证，不是本项实际 E 入口。 |
| [v8 E 分支](</PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding/rule-five-dimension-joint-root/versions/joint-v8-target-product-gap-sol/dimensions.py:489>) | E 的 effect 入口只对 `SE_EFFECT` 或获益风险模式取值；随后检查泛称“有效性”、特定“安全有效”内容、药效学变化、健康相关生命质量及整体健康效果。原句只有明确的“完全应答率”效果指标，没有这些其他入口词。 |
| [v8 SE_EFFECT](</PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding/rule-five-dimension-joint-root/versions/joint-v8-target-product-gap-sol/dimensions.py:869>) | 该表达式包括“治疗应答”和“药物作用反应”，却没有“完全应答率”或同义的应答率指标路径。“治疗应答”这一连续字面串不能覆盖“现有治疗的完全应答率”。 |
| [v9 attempt08 _safety_effect](</PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding/rule-five-dimension-joint-root/versions/joint-v9-generic-relationship-sol/attempt08-final-governance-controls/code-snapshot/dimensions.py:451>) 与 [v9 attempt08 SE_EFFECT](</PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding/rule-five-dimension-joint-root/versions/joint-v9-generic-relationship-sol/attempt08-final-governance-controls/code-snapshot/dimensions.py:876>) | 相同 E 分支和相同效果模式被沿用；`_safety_effect` 完整函数逐字 SHA256 在 v8 与 attempt08 均为 `860ac177b30e58a4da3d0dc6b8211c944e0b5ad64bbf277e38ca638bbb8fa502`。 |

因此，当前实质比较动作与药物对象已经完整，但程序没有把当前指标识别为效果内容，随后落入空的 E 决策。缺口存在于 v8，v9 继承；不能据两边值一致而把 fixture 改成 E=0，也不能把 E 缺口包装为 v10 I/F 通用关系修复的新增失败。

## 对 v10 的治理处理

保留本 fixture 及 `E=1, I=0` 期待原样；保留 old/new E=0 这一既有失败的原始记录。v10 若只授权最小 I/F 关系修复，应继续保持 E 完整决策隔离，并在交付记录中列出本项是冻结控制内已存在且未获授权修复的 E 识别问题。此审查既不提出 E 代码补丁，也不允许为了全通过改期待、删控制、缩句或替换“完全应答率”为旧模式可匹配词。没有据此给剩余七项强制赋 1，也没有读取这七项、01402 补材、human200、remaining 或未选邻近原文。

## 可供选择的五个有限反例草案（无执行、未冻结）

这些是文本关系审查草案，不是已加入 controls 的 fixtures，也没有期待字段或运行结果。采用前应由主任务选择必要项并先冻结。

1. **错主体：** 当前“对仿制药乙提供研究方案反馈。”；有限语境“创新药甲与仿制药乙分别申报。对仿制药乙提供研究方案反馈。”检查创新药甲的身份不能向乙的服务捐赠创新支持对象。
2. **错药型：** 当前“中药注册分类3类药品可申请本通道。”检查手册 §九对应的中药3类含义，不能套用化学药1类或生物制品1类的新颖条件；仅进入通道也不能生成创新资格。
3. **基础与例外：** 当前“创新药以及具有明确实质改良条件的新药可获得研究方案反馈；撤回申请的收件回执不提供该项服务。”检查基础支持机会与纯手续例外分别保留，既不能因例外删去基础关系，也不能把支持内容赋给例外收件手续。
4. **兄弟成员：** 当前“申请人应在三个工作日内提交签字申请表。”；父项“申请人应履行以下要求：”；另一个成员“提交与现有治疗相比的完全应答率分析。”检查兄弟的效果分析内容不能转移到当前纯签字递交记录。
5. **宗旨流程：** 当前“为支持创新药研发，现将本办法印发。”检查制定/印发宗旨与实际提供支持机会分别判断，不能由后文支持安排或标题向这句仅印发动作供给关系。

这些反例不从数字类别、关键词或纯语法主语直接判维，仍依据对象、动作、有限语境和当前实质关系。
