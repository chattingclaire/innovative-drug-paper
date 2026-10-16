# 完全应答率 E 最小覆盖候选

候选可供 ROOT 与独立 I/F 修正组合审查。本轮只做了两次有限控制，没有调用模型、没有分类或选取全量/局部生产记录，也没有改手册、原期待、人工参照、native 首答或既有版本。最终采用附件是 `static02/v9-to-E.diff` 与 `static02/e-patch-components.json`；根目录同名静态附件属于保留的第一版。

## 同版依据与原失败

原固定 `clinical_comparison_without_innovation` 当前完整句为“应比较药物与现有治疗的完全应答率。”，`contexts=[]`，原期待 E=1、I=0 一直保留。药物对象、比较动作、现有治疗基准和临床反应指标均由当前原文直接表达。共同手册§一允许当前实质比较及证据要求，也允许否定、不确定和尚未实现要求；§四定义“药物防治效果、健康收益、临床获益及支持这些判断的证据。”，纳入“对应的药效研究/效果比较及证据要求”。因此 E=1 表示效果议题在场，不证明该药有效、优于对照或有创新属性。

C 的同版独立审查已说明，v8/v9 沿用的 `SE_EFFECT` 没覆盖该确切指标；原 fixture E=1 依据手册成立。手册 SHA256 `5ea7ab74d30fb79c4cbd1d7d6b2ae40c4f52a52360075f3552199de949f9cc7b`。FDA 2018 年原指导的 III.B.2/III.B.3 把客观/完全反应作为抗肿瘤药评价终点，同时区分反应活动与已证实临床获益；这里仅用作术语旁证，不替代同版手册，不写回生产材料。[FDA 原指导](https://www.fda.gov/media/71195/download)。部分/完全/客观“应答率”“缓解率”六个确切指标形式是本候选操作化范围，不能从“应答”一词机械扩散 E。

## 代码隔离

仅增加 `E_OUTCOME_ENTRY`、纯当前原文 `_e_outcome_gate`、`RelationView._e_current_outcome_relationships` 和 E-only `_e_current_outcome_consume`。两处原流程入口分别在 constructor 原末尾、`judge` 原 I/F consumer 后与 `finish` 前；producer/consumer 第一条语句都验证 raw current-text gate。producer 只写私有 `e_current_outcome_relations`，不进入旧 relation graph、不加材料请求；consumer 只调用 `acc.add('E', ...)`。

删除上述新增节点及两次受控调用后，relations/dimensions **完整剩余 AST 与冻结 v9 相同**；source_packet/source_receipts/evidence 三模块字节相同。旧 helper、GAPS、SE_EFFECT 与所有 S/Ec/I/F 路径未改。静态证明与逐字补丁在 `static02/`，它们给出每个新增节点和消费位置，便于机械移植到 C 的 I/F 版本，而不拿完整 v9 文件覆盖其改动。

## 两次真实有限控制

| 记录 | 预先固定控制 | 真实结果 | 保留项 |
| --- | --- | --- | --- |
| execution01 | 原189 + 新22 | 新22全部符合；12个负例无 E=1；原189只有目标 E 从0变1 | 原8个I/F未满足、15个pending完整保留 |
| execution02（最终） | 原189 + 保持原22 + 新2 | 新24全部符合；13个负例无 E=1；原189仍只有目标 E 从0变1 | 原8个I/F未满足、15个pending完整保留 |

原目标实际五维从 `S0/E0/Ec0/I0/F0` 到 `S0/E1/Ec0/I0/F0`。两轮中其他四维完整 decision、gate 外完整五维 decision、旧 relation/source 日志差异均0，技术错误0，原文逐字证据经原 evidence validator 验证。原189基线使用已封存真实 v9 attempt08 的 `candidate` 输出，没有重跑旧189，也没有把其 v8 `baseline` 当成 v9。

第一轮之后，静态发现“药物仅用于界定研究对象，应比较手术与放疗的完全应答率。”可能发生逗号前背景药物向后句捐赠对象。第二次编辑前固定该 E0 负例及“应比较该药与手术治疗的完全缓解率。”E1 正例，只将**新增 producer** 切段从句号/分号收紧到也包括逗号。第一轮输出与期待原样保存，最终两条均符合。此收紧是当前对象关系修正，与通过数量无关；没有进行第三轮。

第二轮 summary 的 `targeted24.case_N` 仍序列化为22，是复制报告脚本的硬编码遗漏；实际 results 有24个新控制、213总行、24通过。原 summary/seal 不改，`summary-count-correction.json` 按实际行数机械补正该单一元数据字段，未重分类。所有原失败如下：00093/F、00381/I、00649/I、01382/I、01402/I、01731/I、01743/I、01757/I。它们不属于本 E 修正范围。

## 足够的局部影响门槛

ROOT 可调用 `select_static_impact.py` 的 `matches(current_original_raw_text)`；CLI 为 `python3 select_static_impact.py --source-jsonl ORIGINAL_CURRENT_TEXT_ROWS --output NEW_GATE_MANIFEST`。源行必须实际暴露 `text` 或 `source_record.text`，缺失就拒绝，不能以语境或预测代替原文。本轮未读取/选取4481当前原文，实际命中 N 未知。

该 raw gate 与两模块入口字面相同，筛完整记录，不过滤旧 E=0/null，**包含已 E=1** 的潜在证据变化。gate 外新 producer/consumer 完全跳过，原 v9 AST 全部保留，故 gate 是可能受影响路径的充分超集，绝非自动 E=1。ROOT 应与 I/F 独立 gate 取并集、绑定封存原始材料后一次实际重算，不按目标 ID、旧预测或当前分歧筛选。

## 实际范围与未解项

分类器实际只接触原189控制内98个唯一已暴露 packet binding 和预先固定合成控制；运行期间文件访问被阻断，未打开新 human200 或 remaining 正文。输入、输出与两轮 code-snapshot 均绑定哈希。当前自足药物对象和确切终点是新分支范围；省略主语、只在标题/父项出现的指标不由本分支补足，跨逗号关联保守不新增，其他既有路径保持。有限正反例不证明所有复杂语句正确，也不是人工核定、准确率或 κ 验收。组合版本的静态接线、影响并集和生产实际差异仍由 ROOT 核验。
