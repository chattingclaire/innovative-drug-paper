# 统计实现 null 修复复核

## 结论

原独立复核指出的显式 `null` 子类型缺陷已经解决。在本次限定范围内未发现新的正确性问题。

`subtype_set` 现在把缺字段或 `None` 统一规范化为空集合，并对非字符串数组的其他输入显式抛出 `ValueError`。三个原构造反例均变为预期结果：

- `safety_subtypes=None`：`exclude_quality_only` 下 S 为“待定”；
- `fairness_subtypes=None`：`F_access_affordability_only` 下 F 为“待定”；
- `innovation_subtypes=None`：`exclude_I_qualification_advantage_only` 下 I 为“待定”。

三个反例在 `primary` 下都保持原标签不变，输入记录中的 `None` 也未被修改。

新增两个测试覆盖显式 `null` 和非法类型。连同原有构造测试，运行 `python3 -m unittest -v test_comparison_statistics.py test_rerun_sensitivities.py`，12 项全部通过。

`analyze_llm_corrections.py` 的更正选择和计算路径未改变：仍按每个 shard、每个 batch 选择最高修订号，通过既有校验后，从首次输出深拷贝形成更正版本，并以四方法共同可判子集调用同一统计函数。新增代码只在摘要中说明该分母口径，并从既有结果读取 `common_unit_n`、用总单元数计算共同可判比例；没有参与更正选择或指标计算。

本次未读取任何输入、预测、参考标签、H427、统计结果、旧快照或外部资料。

## 复核文件 SHA-256

- `analyze_current_reruns.py`: `b62ee8deabe9380cf12084a0c04baa43806652a7875c7120b18f4cb8900f1774`
- `test_rerun_sensitivities.py`: `d68b11b248185eeeabaae25cd260f0ebad0a29ea3043af5be689f0a85eb35d74`
- `analyze_llm_corrections.py`: `4376663d7f13ae588da171aefc995b83811eef6e45740330c80ef421fd16fdaf`
