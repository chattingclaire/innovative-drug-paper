# 全量编码与指标结果（2026-10-12）

规则v11＋v16兼容结果和LLM同版兼容结果均已实际完成4481条，输出缺失0。LLM保留4478条原结果与同一实际整批的新3条；材料改变只涉及01402。本目录仅提供聚合工作簿，不包含逐条机器答案、原文或人审盲包答案。

77条A/B参照已用于校准：规则五维指标均1；LLM的S κ=0.948905、F κ=0.957529，其余维度均1。校准符合程度不能视为正式独立验证。全量机间一致性仅比较同版且双方均0/1的槽，不是准确率。独立人审200尚未交付，稳定性正在执行R1，已观察13个真实CLI starts，完整重复完成仍0条，正式95%CI尚未计算，最终验收及论文门仍为false。

主表采用条款等权与来源条目日期：48项issuedate、3项publication fallback。q=本维阳性赋值/五维阳性赋值总数；p=本维阳性/全部条款（包括全0）。q的0阳性分母和空组均为NA；观察p为已观察阳性的覆盖下界，null未填0。null条件界固定已观察0/1、只变动合法null，各维分别求界，不能解释为CI或已判0/1的误差界。r完整点在存在null时保留NA。

稳健性页摘取已运行的792情景、408留一情景：精确文本重复降权、排除联合/系列/多组件、2018–2025窗口、等来源及系列年度均值，保留重复组冲突/null。去重仅降权，不合并OR，不宣称语义去重。51来源有56组件但条款component_id全缺失；组件年份/组件等权与联合部门再分摊未执行。所有表格均注明数据来源键、范围与分母。

原始封存来源（相对根 `/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010`）：

- **M**：`07-statistics/current-full4481-v11-v16-source-aligned-diagnostics-root/metrics.json`
  SHA256 `955797adb43791bdba14243d0dcfe38a264d5063f67d41f315e990e59dd91053`（原封印逐字校验）。
- **NC**：`06-coding/native-full4481-v16-three-member-compatible-root/coverage.json`
  SHA256 `bea06fc56ce8c766a69c5d0047ee53dd0d7bbe89ecaab53ea6638413d96a3815`（原封印逐字校验）。
- **R**：`07-statistics/rule-v11-v16-conditional-attention-robustness-root/conditional-robustness.json`
  SHA256 `481b2b009659fabc36e8a791a4a5cf1d5412d1925710de5b014e1f1069e04382`（原封印逐字校验）。
- **N**：`07-statistics/full4481-native-v16-compatible-attention-comparison-root/frozen-core-evaluation/conditional-robustness.json`
  SHA256 `40b4fd9ba6e72aebc2883c75b7c7e7ffbd99df0b579409e6e656c97166263a29`（原封印逐字校验）。
- **C**：`07-statistics/full4481-native-v16-compatible-attention-comparison-root/machine-attention-comparison.json`
  SHA256 `50224c89ef9d5c377aea857cb9bf77526ad784275b1e7a7c65d858c51d2165e9`（原封印逐字校验）。

制作中仅读取上述聚合JSON及原seal；逐表投影数值和计数已核对，完成工作簿重算、错误扫描和四页视觉检查。原编码、参照、统计及封印未更改。
