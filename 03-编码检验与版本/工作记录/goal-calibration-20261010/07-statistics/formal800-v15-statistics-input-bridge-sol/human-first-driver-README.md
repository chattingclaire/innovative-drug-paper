本补充提供可参数化的`human_first_driver.py`；原`bridge.py`、README及21成员output-seal保持不变。原准备CLI的永久阻断只是原交付状态，本补充允许未来真正符合既有接收契约的A/B文件进入human_first转换与计算。

未来使用实际XLSX接收目录及真实阶段元数据，在本目录执行：

```sh
python3 human_first_driver.py --convert --upstream-reception /真实接收目录 --statistics-metadata /真实阶段元数据.json --statistics-metadata-sha256 实际SHA256 --output-dir /本目录/尚不存在的新转换目录
python3 human_first_driver.py --calculate --upstream-reception /真实接收目录 --statistics-metadata /真实阶段元数据.json --statistics-metadata-sha256 实际SHA256 --output-dir /本目录/尚不存在的新统计目录
```

元数据可以是既有metadata对象或含metadata的文档，analysis_stage必须human_first。A/B input_seals的原始SHA必须分别等于存档original-A/B.xlsx；设计保持原41层和800来源。既有身份及freeze声明原样交给旧引擎，驱动不生成verified/independent真人证明。所有输出只写新目录，不覆盖首次提交或刚封存的准备交付。

先核原准备交付的封存；再核上游report、seal所有输出、输入绑定、帮助代码及原XLSX的实际SHA/bytes，要求command=receive、两侧content_valid以及现有完整content handoff资格。随后检查实际保存的release.json、declaration-A/B.json和原件，复用原XLSX接收器的正式release、包/模板/手册、4000槽、执行人及独立声明核验。手填true不能取代这些实际文件绑定；文件、哈希和声明仍不能认证真人身份、独立性或开始时间，协调者外审限制保留。

合格时读A/B独立4000派生行，调用已封存的project_xlsx_derived_cells、project_parsed_cells、assemble_engine_payload。理由、单元格及原字节继续保留上游，不要求旧八字段sidecar。convert写engine-input、完整4000×2状态账本与覆盖情况；calculate额外直接调用原分域引擎analyze，固定5000次、seed20261010、既有single_category guard。所有四格、κ与CI公式完全继承，低于0.80也正常报告，不以分数作运行门槛。

在旧analyze调用之前记录attempt_started。未进analyze的拒绝保持false；实际调用后报错保持true，在本次新输出目录保存failure.json和自排除的failure-seal.json，保留输入、覆盖、状态及真实计算尝试。旧引擎DataError继承ValueError，现有catch覆盖；本次没有触发或构造实际统计失败。

`--coverage-only --upstream-reception /实际receive目录 --output-dir /本目录/新诊断目录`允许合法但未complete的接收内容按原800设计报告覆盖及待定，不调用引擎、不计算κ/CI、不称完整800验收。内容错误被拒绝；任何dry-run都不能进入真实转换、计算或这类实际接收诊断。空白与未提交保留状态及原设计权重，不补0。此补充只接human_first，不扩展参照、机器或年度接口。

本次仅执行一次现有真实final-blank-dry-run的拒绝检查及必要入口静态核。拒绝发生在解析A/B派生值及读取统计元数据之前；没有真实计算、伪release、伪声明或构造800标签。ROOT已有实际空表4000×2纯机械衔接证据保留在logs/root-formal800-xlsx-statistics-bridge-reception-20261010.json，本补充不重复bootstrap或扩展控制。

`human-first-driver-readback.json`保存本次有限拒绝及AST入口核对。`human-first-supplement-input-seal.json`绑定原准备封存、当前接收接口及真实空表报告/封存；`human-first-supplement-output-seal.json`仅封存新增文件，自排除。它们不是正式发布、真人接收或研究验收。
