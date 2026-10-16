本入口为未来真实完成的LLM4481提供材料准入、统计来源适配及两机器比较。本轮仅准备，未分析部分3152结果，未调用模型/分类器或重跑生产。已做一次有限机械检查：3152的真实封存覆盖被拒绝，固定v16清单与4481元数据ID一致。

唯一入口为 `native_attention_adapter.py`。实际完整父collector和v16整批0216三成员结果合并、封存后，ROOT可运行：

```bash
python3 "/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/07-statistics/full4481-native-attention-compatible-adapter-preparation-sol/native_attention_adapter.py" run --parent "<完整v15父collector目录>" --compatible "<实际v16三成员合并目录>" --selection "<真实0216 root-selection.json>" --rule-attention "/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/07-statistics/rule-v11-v16-conditional-attention-robustness-root" --output "<新的统计输出目录>"
```

准入要求父及合并均为4481记录/504原批次、无缺失维项或技术问题，完整实际seal存在。合并status必须表明实际完成，并绑定同一父seal和真实新selection。每条ID/顺序、packet路径/字节/SHA逐项匹配固定v16清单；source bundle通过该清单的ID→packet哈希桥绑定。其余4478行必须与父JSONL原行含换行字节相同；01402/01403/01404必须完整取同一实际first、receipt、actor seal、attempt及五维，且有同版材料实际阅读和终止收据。仅契约、未完成父、3条delta或无seal结果全部拒绝。stat入口不重读事件语义、不重新判定临床/政策内容。

复用原聚合器的文件SHA在导入前校验，其所有计算函数和792/408情景调用原字节保持。只给隔离导入模块指定新的轻量统计facade：实际id/labels投影、显式native状态及原元数据symlink；不复制大型准备环境，不改旧代码/材料，也不向冻结目录写字节码。原API含rule命名，来源角色包装明确标为LLM，不能把facade当成新规则执行。null完整保留，不补0。

ROOT实际运行后输出原算法完整q/p/r、来源/来源年度系列、精确文本降权、篇幅、联合和多组件排除、留一结果；两机器使用相同材料及元数据。比较报告给每一情景/分组的点值、条件差异界、维度排序，以及各年部门排序/各部门年度排序。q点值为已观察阳性构成，p点值为观察阳性下端；含null时完整r点值为NA。零分母、空域和并列保留。条目/系列q均值的可判成员数可能随机器改变，原报告保留分母；比较不能当正式准确性或最终论文结果，任一机器都不是gold。

原组件映射、联合部门再分摊缺口及来源条目年份口径原样保留；不增加字段或改权重。具体准入及绑定见 `input-contract.json`，唯一一次检查见 `mechanical-check.json`。`formal_validation_complete=false`、`paper_writing_gate_open=false`。
