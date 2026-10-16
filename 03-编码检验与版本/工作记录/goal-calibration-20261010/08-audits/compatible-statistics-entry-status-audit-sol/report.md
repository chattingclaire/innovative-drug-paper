两个 ROOT 新统计入口的只读静态核查通过。两份实际源码各只有一处状态断言变化：保留原 startswith/endswith 判定，增加精确接受 `complete_compatible_rule_composite_with_explicit_execution_origins`。逆恢复此一断言后，完整源文件字节与完整 AST 都等于各自原版。

全部非 main 函数源码及 AST 原样相同；main 仅含上述状态扩展，恢复后亦完整相同。因此数学、四格方向、数量/覆盖分母、null/NA、F1 直接公式、条件 bounds、年份部门绑定和源/祖先 seal/origin 检查均未变。实际四格或指标是否正确仍待 ROOT 在真实新 composite 完成后运行并读回；本核查不重算统计，不执行任一 calculator 函数、classifier 或 LLM。

仅读取变更声明和四个 Python 源文件，没有读取 prediction、真人表、人审200/remaining、packet、年份数据或原文；原件未修改。报告独立于本代理前一项自行编写的运输适配器，不把此次静态兼容核查称为正式独立语义验收，正式/人审/正文 gate 保持 false。
