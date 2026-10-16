# 完整native批次提交到稳定性统计：冻结候选 v1

本目录补齐完整批次输入资格、首次有效选择、固定记录抽取与旧统计数学的衔接。交付仅含独立构造的2条和3条小批次，没有派发模型、打开真实来源/编码/参照或导入任何真实native运行。新的真实R1/R2/R3/W/H仍未做。编制者为AI；不是独立真人审核。

`batch_adapter.py` 是新入口；`vendor/stability_engine.py` 是SHA为 `4e4bc00ef8f2d5e9d69b99841c18642bbb8919fbea83601d52c61816aca98e6d` 的未修改typing-fixed副本，仅复用其数学函数。没有把派生单记录交回旧引擎冒充原响应。

```bash
python3 -B batch_adapter.py analyze \
  --registry constructed-controls/inputs/mixed/registry.json \
  --ledger constructed-controls/inputs/mixed/ledger.json \
  --out-dir NEW_EMPTY_DIRECTORY

python3 -B seal_candidate.py --verify
```

依赖Python 3.9+及jsonschema；实际本次jsonschema版本4.26.0。结果目录必须为空，写文件采用排他创建，已封存结果不会覆盖。同字节输入生成同字节report/firsts/audit/report.md。重新执行构造脚本或控制脚本也拒绝覆盖既有控制。

完整规则见[完整批次输入与抽取契约.md](完整批次输入与抽取契约.md)。`batch-input-contract.json`是本候选的登记与状态机器契约说明；可执行跨文件校验以代码为准。正式来源接口的必需冻结项见`production-qualification-freeze.required.json`；这些项目前都是待采用占位，不能直接用于真实生产。

原字节资格：保存原生编码者首个结构化整批提交文件的完整UTF-8字节及SHA，而不是提供方网络/wire原始响应。本构造夹具中的raw文件是人工创建的模拟提交。SHA核对文件一致，不证明该文件由原生工具或某provider实际产生，也不证明真实先后时序、完整可见历史、派发/交付或独立上下文。

登记选择`context_unit=batch`，逐批次用逻辑新上下文；批内共享历史。这是既有native事前变体，明确偏离旧逐record独立上下文形状。只描述指定材料、次序、批次与设施的稳定性，不把统计接受解释为符合旧API方案、正式共同冻结或Goal验收。旧方案和旧目录均未修改。

源资格没有使用assert-true报告：`toy-source.schema.json`递归关闭，`toy_qualification.py`实际检查source/output唯一映射、内容/CTX、连续当前与CTX引文、字段路径、null补材请求和toy资产能力。unknown元数据整包拒绝，禁止静默裁剪。它仅支持显式synthetic toy形状；真实共同source schema、opaque adapter及生产引用校验器没有读取、捏造或冻结采用，生产路径目前直接拒绝。不能通过改data_mode、换宽松schema或给布尔检查true取得生产资格。

`constructed-controls/controls.json`：61/61项有限机械控制。保存21份原失败提交字节和检查报告、13份拒绝台账、5份拒绝来源包；控制包括重复/遗漏/增加/换序、错批次/条件/内容SHA、未知字段、五维类型、非连续引文、CTX/资产、malformed/重复key/NaN/非UTF8、合法null后重试、最多3次、first跨条件回填、请求变化、复用上下文、反馈/截断/伪遥测、未终结比较锁及实际CLI/不可覆盖/字节封存。

`verification/legacy-single-record-controls.json`：6/6项独立单记录旧CLI数学回归，核四格方向、退化κ、共同向量和q零分母。其外部true旗标明确仅是旧数学夹具，不给来源资格；新batch路径不接受此类报告替代执行检查。

`verification/build01-original-cli-failure.json`与`build02-original-cli-failure.json`保留两次构造序列化缺陷的原CLI失败；对应原输入目录没有覆盖。第一处把对象键插入顺序当条件顺序，第二处内存source字段顺序与封存字节排序不同；已在新候选中按固定条件集合/批次数组和同一键排序请求组装修复。修复后的实际CLI、逐批次原传输/quote/malformed失败、构造controls和旧回归全部保留。

本候选没有新增稳定性通过线、CI或分类效度结论。全部五诊断条件选择或明确终结失败并封存后才生成比较；只有一次失败且还有重试槽时可生成审计快照，比较保持锁定。P的失败/null不由诊断填补。ROOT另行派独立审查；本控制不是独立审查完成声明。
