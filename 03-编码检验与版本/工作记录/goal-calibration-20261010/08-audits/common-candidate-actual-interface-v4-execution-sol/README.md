历史三条 S 对照的首次 v4 执行

ROOT 明确授权按 pre-execution-seal d3eb4a89… / algorithm-bindings 45c33b4e… 执行已封存的三条历史 S 计划。RECODE25-00036、00038、00045 各进行 semantic_unit / RelationView / judge 一次；结果 S 均为 0，固定历史预期均为 1。没有 NULL、构造或执行异常，无重试和临时补材。其他维仅保留观察值，不设置预期。此为既有真人核定条款的开发对照，不产生新真人或正式准确性指标。

三条已实际生成 cited_standard，包含同版原文的安全性标准；source_requests 为 resolved/primary_literal_complete_operative_standard，material_requests 为空。直接遗漏在生产—消费接口：relations.py 第 659 行发布该关系时没有 SE_scope_verified / closure_proof，dimensions.py 第 857–865 行 _se_allowed 因缺闭合准入标记拒绝该 cited_standard，第 425 行 _safety_effect 写形式排除，最终 S0。不能将此执行缺口称为待定或原文缺失。

00036/38 的入组标准来自原件第 4–17 行，安全性优势为第 15 行，解析组末坐标 1181 实际为下一章节第 18 行“二、工作程序”。00045 的终止组为第 30–35 行，重大安全性问题为第 33 行，编号成员末为第 34 行；第 35 行状态名单段也已被旧组带入，解析组末坐标 2718 实际为第 36 行“三、工作要求”。12 条关系及已解决请求引文均回核完整原件 SHA 980acf76… 的原字节、Unicode/UTF8 区间及实际行位置。

最小通用修复依据已交 ROOT / last22：让现有中性原件组解析输出当前行动、同版组件、有限成员和实际下一边界 receipt，分离边界与消费内容；经证明再接入既有 SE_scope_verified / closure_proof 协议。不能对任意 cited_standard 放行，不能以程序名称/ID/叶截止赋值或证明闭合。本目录只定位，不修改 v4，也不执行拟议 v5。

evidence.validate_decisions 三条通过，所有已生成当前/语境引文及关系引文均按原始 semantic_unit 核字面，源扫描事件逐项核原 producer inventory 的 source/view SHA；原冻结 resolver 没有产生身份变化。原 packet、历史计划、五模块、手册及共同冻结绑定执行前后保持。完整语义输入、trace、资源 inventory、所有检查、0 值和期望差异都保存。

附属 trace 分析脚本首次有语法错误，发生于判断全部完成之后；首个失败与代码保留在 analysis-failures/，修正后仅解析已保存 JSON 和原件，未再调用 adapter/RelationView/judge。最终 seal 排除自身，不覆盖既有纯接口和计划封存。
