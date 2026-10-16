此目录是 full4481 规则路径的机械执行适配准备件，当前未 release、未执行真实推断。原算法来源仍为已披露开发校准标签的 v4 candidate，正式验证及人类验证均未完成，不能据此声称全量已编码或已验收。

`rule_driver.py` 仅改变执行范围、外部确切绑定及状态包装。六个实现文件（`interface_common.py` 与五个 coder 模块）以及 `manual-candidate-binding.json` 均与原 v4 逐字节相同。旧文件未修改。`finite_protocol`、读源/引用审计、合法 null、异常时数据保留、维度槽计算、真实推断循环及终端故障处理保持原字节。准确 unified diff 见 `driver-mechanical-diff.patch`；所有原始和新文件 SHA/bytes 见 `implementation-provenance.json`。

固定执行范围为4481条、22405维，purpose=`production_provisional`，max run=1。首输出目录已存在即拒绝。外部共同手册、prompt、共同执行协议 txt 与 ROOT release 都按绝对路径、SHA256、bytes 绑定；共同执行协议 txt 用 `protocol`，原读源协议代码用 `source_reading_protocol_code`（文件名仍为 `source_reading_protocol_v12.py`）。prompt/共同协议仅确切绑定，不改变规则判据。Gold/参考标签不作为输入、材料或比较授权。

`release.example.json` 是最小字段例，不是真实 release。release 的 `authorization_id` 与 scope 相同，`source_input` 与 scope 的 `source_packet` 相同，manual/prompt/protocol 绑定及 output_directory 完全相等。scope/release 不相互绑定 SHA，避免循环；真实 scope 的 CLI SHA 固定本轮授权内容。正式 ROOTbind 到位后直接替换范例参数，无额外语义或验收门槛。

`prepare_scope.py` 的 `build_scope(params)` 只读显式传入文件，载入完整 source inventory 并追加当前 common 文件、源包 seal、源 manifest、有序ID与算法 manifest 的确切绑定。参数可用文件路径或 path/sha256/bytes 三字段 binding；source inventory 的每一项使用三字段 binding，有序ID文件可为 JSON array 或 `{"approved_record_ids": [...]}`。默认生成 `prepared_not_released`；最终冻结时由 ROOT 显式设置 `frozen_for_execution`。参数完整例见 `scope-params.example.json`。

准备命令（不会导入 coder，不会推断）：

```sh
python3 -B prepare_scope.py --params /absolute/final-params.json --out /absolute/new-source-scope.json
```

收到 ROOT GO 且最终绑定冻结后的执行命令：

```sh
python3 -B rule_driver.py --scope /absolute/new-source-scope.json --scope-sha256 EXACT_SCOPE_SHA256 --input /absolute/common-frame-bundles-v15.jsonl --input-sha256 EXACT_SOURCE_SHA256 --out /absolute/unique-first-full4481-rule-output
```

唯一有限合成机械自检已经通过。它使用人工构造的普通字符串及合成ID，不含真实政策或参考标签，检查准备scope/错误purpose/错误全量数量/虚称blind/release共同绑定不等/已有首输出的拒绝，并静态比较原辅助函数、推断循环与故障处理。没有 coder 被导入，真实推断次数为0，没有生成 pycache。结果见 `mechanical-selfcheck.json`。不要把合成自检解释为规则效度或全量运行成功。
