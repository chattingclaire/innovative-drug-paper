# v11 独立源材料 QA

最终结论：全部检查通过，v11 材料已冻结。本审查未接触 r3 新确认标签、确认评者结果或 admin/private 新 gold，未改分类代码、提示词或论文正文。列表选择和范围仅依据原始来源与结构，不依据维度标签。

4,924 条 ID、原句、顺序保持不变；两种方法全部原句及 contexts 完全相同。清理 32 条确定越界中的 50 个旧上下文项；121 个真实必要列表提供完整连续原始段落，19 个 v10 新完整列表的整个 contexts 原样复用。另 27 个广义通知/工作程序/阶段/图表引导句明确标为非完整的局部导航预览，00054 明确为独立表单填写要求。v5/v6 的 5 个版本字段及 v10 的 23 条显式援引全文均原样保留。

121 个列表共 716 个段落：690 个通过原 PDF 指定页或原文指定行逐字核验；26 个来自图像 PDF，已实际渲染并逐页实看，证据位于同目录。跨页仅排除已核实位置的精确页码和精确固定页眉，不删除正文数字。所有连续区间均未夹入其他附件来源；使用锁定的人工核对端点，不使用探索性 heading-rank 草案直接生产。

00762 与 03864 的第四个后项均恰好结束于原 PDF 最后一页。candidate 随后追加的是早前第4页的图1转写；QA 将其明确记录为独立追加组件，实际来源边界是文档末尾，未把图表转写加入当前列举。

既有 19 个 v10 证书和 74 个新增证书均被冻结 verified_following_list 接受。20 个实际完整列表使用“一是”、圆圈、项目符号或 A/B 等结构，与旧验证器的 marker 形状不兼容，已提供真实完整源材料及明确完整性元数据，但没有伪称旧验证器接受，也没有修改冻结分类码。全部 production/runtime 文件哈希与 candidate_freeze 一致。

LLM SHA256: `13688745bab15d78b6b8cb7492011a38162ea0d740d5131a1307f65bc66538d3`

Rule SHA256: `7ef9c4031ba77b14cf10e523ab912292defff6ab60c08b0d948cc0dc36673bf2`

JSON 明细：`independent_source_material_v11_qa.json`；完整精确列表 proposal：`necessary_list_completion_proposal_v11.json`；32 清理 proposal：`independent_following_boundary_proposal_v10.json`。
