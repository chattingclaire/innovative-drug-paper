现有 `analyze.py` 硬编码旧机器 freeze 与旧材料差异条件，无法只传新路径复用。因此这里只补一个固定200开发复核入口，复用已接收的人审逐项投影及原冻结 Fraction 四格指标；旧脚本、人审原件和结果均不改。

入口只接受两份完整严格接收结果：规则 `rule-full4481-v15-v17-received-root`，LLM `native-full4481-v17-two-whole-batch-compatible-root`。核对封印、同一 v17 common、4481/22405、零未决技术槽，以及 LLM 0325/0485 两整批的接收绑定。未齐备即拒绝计算，不用旧 LLM 补位。

全部200条保留，02588/04598逐项标为材料补充、真人重读未核实；另列198条未变材料敏感性对照。历史120/80、原概率和权重不改。反馈已经用于修订，结果明确为开发复核，不能称独立A/B或验收。原脚本没有适用的独立准确性95%区间，本入口沿用 `independent_accuracy_CI=null` 和原理由，不发明区间。

两份严格结果完成后：

```sh
python3 -B compare.py --check-readiness
python3 -B compare.py --output-dir /绝对路径/新的对照输出目录
```

也可显式传 `--rule-received`、`--llm-received`；版本和完整接收条件仍固定。输出只写新目录：完整指标JSON、全部1000项逐项记录和简短中文对照。当前仅准备及语法/缺输入检查，未运行新指标、未造测试套件。
