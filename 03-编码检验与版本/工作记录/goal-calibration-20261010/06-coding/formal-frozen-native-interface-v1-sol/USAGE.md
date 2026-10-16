最小调用（只绑定组件，不读取800正文、不生成包）

```sh
python3 -B "/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/formal-frozen-native-interface-v1-sol/builder.py" bind \
  --binding "/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/formal-frozen-native-interface-v1-sol/runtime-binding.json" --binding-sha 4a7a6f9c65cc99a7a81e6c1df29511fb761f9a9c74d31e8c663552147b051a4f
```

Python scope/read/use 入口：在新的独立进程将本目录加入 sys.path，`import necessary_read_gate as gate; gate.configure(binding_path,binding_file_sha); import native_records`。随后原 `gate.prepare_scope/check_scope`、`native_records.check_saved_scopes/select_technical_receipts` 接口参数不变，scope/read/use 只据真实执行记录。

未来 build CLI（本轮未调用）：`builder.py build --binding PATH --binding-sha SHA --authorized-order PATH --order-file-sha SHA --out NEW_DIRECTORY --actor-attempt-root ROOT_APPROVED_NAMESPACE`。authorized-order 保留原 `ordered_source_ids/source_selection_manifest` 格式；selection manifest 实物SHA核验，不由标签/难度选源。build 显式读取 bound 新 schema，保留完整 source，生成每记录完整指令与单独短R launcher及实际SHA/bytes，原 conservative full-material budget 同时计入新版 wrapper/overlay。调用该命令须 ROOT 另行决定，不是本组件授权。

未来 receiver CLI（本轮未调用）：`receiver.py --plan PATH --plan-sha SHA --native-root ROOT --report-root RECEIVER_ROOT --runtime-binding PATH --runtime-binding-sha SHA --scheduling-root ROOT_EXTERNAL_SCHEDULING --actor-seal PATH --batch ID --attempt N --creation-request PATH --creation-return PATH --report NEW_PATH ...`。原 request/return/runtime pointer、真实 technical-evidence、short初始文件/长instruction、prior-report 参数均保留。未来 plan 仍需绑定 actual initial、完整 instruction、packet order/files、actual external creation/history；`manual_v1_3` 是兼容键名，必须绑定本次 actual v1.3F bytes，不允许沿用旧 manual SHA。新 plan 须明确 `receiver_report_root`、`authorized_scheduling_roots` 和 `authorized_short_scheduling_roots`，其路径不得靠 CLI 自行猜换；runtime binding 与 plan native-binding 文件必须同一实物。原 v4 plan/binding 可按原 namespace 复用。组件没有创建实际 formal campaign plan。

不得重置旧材料 attempt 状态；不允许把此新组件当作旧材料第四次。未来 RWH 条件和正式共同freeze/真实human执行需 ROOT 单独落实。unknown telemetry、截断/compaction/history证据原门槛不变。
