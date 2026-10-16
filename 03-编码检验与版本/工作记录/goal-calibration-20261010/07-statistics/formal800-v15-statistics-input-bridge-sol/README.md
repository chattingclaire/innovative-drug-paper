# 正式800 v15统计输入桥：未填准备交付

本目录只机械读取800抽样管理映射及已审统计入口，当前没有正式800人机编码、真实独立初判或可信裁定。`prepared-unfilled/`不是收到的提交，也不是统计结果。新目录包含协调者私有盲号映射，访问权限设为700。

`bridge.py --prepare-only --output-dir 新目录`可生成真实抽样设计的未填模板。输出目录必须不存在，不覆写。本次已运行：

```sh
PYTHONDONTWRITEBYTECODE=1 python3 bridge.py --prepare-only --output-dir prepared-unfilled
```

每方法有800来源×5维=4000槽，共41个原层。remaining抽600、exposed抽200；原设计精确W分别1444、3037，ALL为4481。三个部门样本量NMPA384、NHSA340、NHC76，对应总体1848、2100、533。exposed200是开发曝光审计域。域成员只来自冻结的stratum.domain，来源行不另设可覆盖域字段。

`assigned-design-metadata.json`逐条保留来源ID、A/B不同盲号、原层、部门、N_h/n_h、pi及weight精确分数，policy_year=null。允许读取的抽样映射没有已核逐条年份字段，未从ID、文件名或标签推年。引擎模板不包含policy_year/year_mapping，因此不激活年度接口。年度修复文件仍是原目录的独立候选，未提升、未调用。

`analysis-metadata.UNFILLED.template.json`保留正式release、身份、参照和各输入封存的空位。`engine-input.UNFILLED.template.json`的data_role=null、每方法output=null，旧引擎必须拒绝；空位不记0。五个CSV均明确UNFILLED，value为空、state=not_submitted，不是五方真实编码。

纯机械接通函数如下，它们本身不认证任何人或来源：

- `project_xlsx_derived_cells(derived_rows, side, rows)`接收本轮`formal800-xlsx-reception-1`候选的derived-A/B.jsonl格式，核4000槽、盲号/维/发放行绑定。filled0/1是二元值；unfilled保留blank；invalid阻断。原XLSX字节、单元格、自由理由、包/手册/模板SHA及真实release/用户独立执行声明继续保留在上游，不要求旧JSON八字段sidecar。
- `project_parsed_cells(parsed_cells, method, rows)`接收已获上游接收资格的最小统计投影，每格仅join_id、dimension、state、value。A/B仅按各自盲号接通；reference/rule/LLM按source_id。reference必须另存，绝不由A/B一致、某一人的首判或source-aligned自动生成。state为binary、semantic_null、blank、not_submitted、missing_return、method_failure或dimension_failure。非binary的value必须null。缺槽保留not_submitted及absent_parsed_cell来源，不删原800行。
- `assemble_engine_payload(parsed_inputs, sealed_metadata, rows, design)`只组装已经实际接收、且有既有原件seal的阶段输入，保持原41层和ALL4481。仅生成机械join后的projection SHA，不创造independent/credible/verified真人旗标。先调用旧prepare检查800行、封存投影与层n。旧`analyze(payload, replicates=5000, seed=20261010)`是后续原始/设计加权四格、κ及注册CI入口；本次没有调用analyze。
- `coverage_summary(status_rows, rows)`分别报告方法×维×ALL/remaining/exposed的完整状态数量和精确原权重。部分可判对四格不能被表述为800全覆盖。0.80是既有数值目标，实际低于目标时仍应计算、报告；不以分数阻断计算，也不新增CI、年度或域目标。

计算资格与验收分开。CLI的`--calculate`和`--convert-only`目前在打开任何结果输入前fail-closed并退出2；原因是本轮尚无真实正式release、A/B实际接收及另存可信裁定/两机器封存。接收候选的content资格不认证真人身份/独立性/开始时间，也不等于研究验收。将来ROOT应把真实上游接收目录和其既有封存契约对齐到该纯转换函数，再开放执行；不能把模板手填true当真实执行的替代品。本交付没有自造release/裁定/机器封存或新增身份认证框架。

`missing-upstream.json`逐项记录缺件。human_first的实际独立首判信度可以在真实release和A/B封存齐备后独立计算；machine_reference/combined还需要可信且机器盲的参照与两机器封存。可信ref缺失时不能计算准确性。全部计算仍由共同原800设计进行；域分母使用原W掩码，不能用两域κ平均替代全域κ。

旧引擎只接收0/1/null/execution_failure四种状态；blank、not_submitted和逐维missing_return的细分在桥的完整4000槽status sidecar中原样保留，并投影到旧引擎未返回/逐维失败状态，绝不投影成语义null或0。此兼容差异见`interface-compatibility.json`。原引擎代码未修改。

本次元数据验证仅调用旧prepare与Rao-Wu权重函数。临时内存中synthetic角色只用于无任何标签值的解析形状检查，未生成800预测、四格、κ或准确率。真实管理数据产生共同W=5000×800；ALL/remaining/exposed全长掩码的每次复抽分母都回到4481/1444/3037，仅有浮点舍入差。`metadata-only-entry-validation.json`保存入口、W哈希及分母readback，不保存标签或矩阵本体。

`verify_preparation.py`只核模板未填状态、800/4000槽、原ID/精确pi/W绑定、未填引擎拒绝及计算模式先拒绝；不会读取真人标签、机器值、政策正文或77结果。`input-seal.json`绑定只读输入，`output-seal.json`封存本目录所有交付（自排除），`verify_seals.py`复核SHA。原统计源码与抽样文件保持只读。首次元数据import产生的单一新Python字节缓存已删除，后续禁用bytecode写入。
