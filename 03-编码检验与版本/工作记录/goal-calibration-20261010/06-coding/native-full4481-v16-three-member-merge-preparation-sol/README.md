这是准备好的严格机械合并入口，尚未合并，也不调用模型/分类器。仅接收未来实际原504批/4481条完整 collector seal 和既有 native-v16-batch0216 实际 earliest-valid 整批选取。当前3152或其他部分父快照在读取父 labels/新 first 前拒绝；未生成的新 first/receipt/selection 不会被代填。

```sh
/opt/homebrew/opt/python@3.14/bin/python3.14 -B outputs/goal-calibration-20261010/06-coding/native-full4481-v16-three-member-merge-preparation-sol/merge.py --mode merge --parent <真实full父collector目录> --selection outputs/goal-calibration-20261010/06-coding/native-v16-batch0216-material-delta-preparation-sol/batch-0216/root-selection.json --output outputs/goal-calibration-20261010/06-coding/native-full4481-v16-three-member-compatible-root
```

输出目录必须不存在，且直接位于本研究06-coding或07-statistics下。全部父/新输入验证通过后才创建输出；原first、receipt、seal、selection、父目录全部只读。原4478条非0216父行含终止符逐字节保留。三条替换严格按01402/01403/01404原位置，完整五维决定、理由、证据来自同一个实际first；不拼attempt/维度，不进行语义判断或参照比较。01402 packet对应封存v16材料；01403/01404 packet绑定与父及v16对应表原样一致，仍是在新整批上下文中的实际新输出。

验证复用既有封存collector的strict JSON/binding/pointer函数和既有新材料strict-readback-receiver.verify。后者复用原schema/seal/process guard并核可观测完整材料呈现、截断补读、原顺序与逐字引用。合并额外重新机械验证每项0/1的packet pointer/quote；合法null不会触发重新推理。选取必须是实际ROOT原earliest-valid选择；如果选择attempt2/3，先核更早的实际终态、原技术拒绝receipt以及读回仍不合法；发现更早合法整批即拒绝合并。没有生成实际执行证据。

输出采用既有collector行schema，新增material_origin来源字段。selected-records.jsonl、coverage.json、selected-whole-batch-bindings.json、strict-merge-readback.json、status.json及seal.json一起封存。501个非0216父整批origin保留；0216的新whole origin同时保留父0216 origin。三个新行保留父行哈希、父seal/first/receipt/packet绑定；统一的新first、selection、receipt与actor seal可追溯。

status.json状态为 `complete_native_full4481_v16_three_member_compatible_composite_with_explicit_execution_origins`，含actual_merge_performed、4481/22405、preserved4478、新真实推理输入3、unresolved_technical_dimension_N=0及显式not_all4481_reencoded_in_v16。merger本身model_calls/classifier_calls均为0；原所有失败历史不删除，不宣称重新执行全部4481。status另含source_common_v15/v16、material_delta_bindings四绑定及material_changed_record_ids仅01402。现source-aligned统计入口直接读取selected-records与其真实packet，不需新增统计公式或标签转换。

完整覆盖只表示输出技术覆盖。formal_validation_complete保持false，不把此合并当作真人核定、独立稳定性重复或provider实际模型身份核实。预检只做少量机械拒绝/字节保留控制，不运行真实merge、原大控制套件或任何生产。
