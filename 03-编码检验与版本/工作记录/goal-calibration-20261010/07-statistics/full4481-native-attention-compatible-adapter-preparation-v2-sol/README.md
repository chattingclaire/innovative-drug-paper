本v2只修正原v1的机械ID桥。按封存manifest.source_id（RECODE）对齐unit-metadata.unit_id和collector.id；manifest.output_id（B）是独立标识，保留在原完整manifest绑定中，不重写、猜造或强迫相等。原v1目录/seal完全不动，除一处准入等式外入口字节相同。精确diff见exact-diff.patch。

一次实际元数据检验确认4481个source及4481个output均唯一；unit来源ID顺序全匹配；source==output为0条，修复后来源等式通过4481条。末项RECODE25-04924映射B-04481，说明不能按来源后缀重造输出ID。检验不读标签、正文或heldout答案，不运行完整统计、模型或分类器。

唯一入口仍为native_attention_adapter.py，未来runtime参数沿原v1：run --parent <真实完整v15父目录> --compatible <真实v16合并目录> --selection <真实0216 selection> --rule-attention <已封存同算法规则统计目录> --output <新目录>。入口依据新v2自身seal和input-contract绑定；其余所有完整4481/504、4478原行字节、三成员同实际first/receipt/actor/attempt、v16 packet/source bundle、null/NA要求原样保留。原core函数/792与408情景算法不改不复制。

原source/output完整映射及字节SHA由packet-bindings-v16.json原封存绑定保留；原packet/labels/材料字段均未修改。未生成新的actual分析或论文结论。formal_validation_complete=false，paper_writing_gate_open=false。
