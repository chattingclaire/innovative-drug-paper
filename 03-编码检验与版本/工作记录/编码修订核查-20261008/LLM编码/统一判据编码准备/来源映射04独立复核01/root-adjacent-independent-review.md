# 来源映射04有限独立复核

结论：**通过；未发现实质阻断。** 可将有限映射04用于实际全量来源整理的保守定位步骤，沿用现有失败关闭边界。复核时间：2026-10-09T11:19:19.622206+08:00。这是独立AI的来源关系复核，不是语义编码效度验证。

只审阅交付、diff、实现与实际10项，并复现既有6项保护。未运行28196全量、未新增构造矩阵、未改作者文件或材料。实际10项审查器不导入作者binder/adapter，直接从给定source/candidate重建位置与映射。

实际9项均通过：候选原JSON字段及unit/paragraph span、来源SHA、native container及span、两侧canonical→original与original→canonical索引、全部transform原文/codepoint/位置及Roman guard一致。共核对111个来源侧事件、33个leaf侧事件。三个PDF案例明确单页并核对原行词bbox；三个TXT案例核对原文件字节；两个HTML案例核对原p节点边界及原文件字节切片[9666,9972)、[10198,10403)；一个DOC正文案例仅认证textutil转换流位置。

实际RECODE25-00452的DOC表格项保持binder_unbound/source_literal_absent。独立检查其候选含管道符的行文在原DOC转换流各分行中仍无有限映射命中，未删管道符、未跨行猜表格、未认证原生grid。

现有6项机制保护由并行独立AI逐项核对并用python3 -B仅复现原六案例，6/6按预期拒绝：实词改变、ASCII词界丢失、单元格内子p拼接、规范化重复后用index强选、临床期数之外Roman字形、从Ⅲ展开中截取I。所有案例candidate_position_bound=true而source_literal_position_bound=false，拒绝来自来源机制；既有报告及pycache未改。

应用范围：可扩展来源整理以收集成功、歧义和不支持状态；仍保留原source/candidate身份、原字段、双向索引、变换事件、明确页/节点边界及所有失败。此有限审阅没有建立全量成功率、自然段/法条完整性、图像转录真实性或语义编码有效性，formal_model_input_ready保持false。

逐项证据见同目录independent_actual10_checks.json、independent_existing6_mechanism_review.json及可复现检查器check_existing_actual10.py。作者两个交付目录文件（含既有pycache）、10项实际source/candidate前后SHA保持一致。
