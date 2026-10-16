只读接入预检已完成，当前有效快照为 snapshot-20261008-v3。

52段原文及SHA全部匹配，39个测量字段未填，引用按正文与表1/4所在顺序模拟重排为61篇。旧[39]、[40]、[46]、[48]、[49]、[56]、[57]未使用；旧[44]、[45]保留。

全文接入预览_未成稿.md只供审阅，不能视为最终论文。预检脚本不会写DOCX，不读机器预测或未完成LLM03；统计契约仅声明未来须绑定的字段与区间。

运行 preflight_manuscript_integration.py --out 新目录 可生成一个新只读快照；使用 --require-manuscript-ready 时当前状态返回退出码2，明确阻止成稿。已有目录拒绝覆盖。verify_preflight_readonly.py 独立核验当前v3快照、输入SHA、首次引用、39字段及退出码2行为。

旧 snapshot-20261008 与 snapshot-20261008-v2 因root后续调整正文引用已被替代，不得接入最终论文。当前文件绑定见 delivery_binding.json，各快照文件哈希见v3/output_freeze.json。

仍需：完整采用规则/LLM及真实执行QA绑定、39字段、表2/3新统计、图2重绘、实例与语义核验、最终DOCX渲染与引文核验。
