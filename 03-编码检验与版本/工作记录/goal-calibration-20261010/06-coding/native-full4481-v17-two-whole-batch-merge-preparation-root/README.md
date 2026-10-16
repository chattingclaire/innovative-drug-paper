# v17 两个原整批合并准备

仅离线准备，未运行正式合并、未生成 v17 总体结果。使用已实际成功的 v16 三条合并入口作最小身份/范围调整；原五维首答、严格 JSON/证据/receipt/最早有效整批检查保持。

输入固定为当前完整 v16 父合成 `/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/native-full4481-v16-three-member-compatible-root`，以及两份未来真实 selection（按0325、0485顺序）。每批12条，整批24条全部来自各自同一真实首答，不只替换02588/04598，也不跨尝试/维度拼接。其余4457原行按字节保留；原 v16/0216 真实批次来源和首答链明确保留。新材料仅2条，24条均真实重推，不能称4481全量重新推理。

离线预检：

```sh
/opt/homebrew/opt/python@3.14/bin/python3.14 -B '/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/native-full4481-v17-two-whole-batch-merge-preparation-root/merge.py' --mode preflight
```

两批实际接收成功后才执行下面命令。本准备没有派发LLM，也没有创建两份selection。`--selection`必须两次且原顺序；父为固定v16路径，输出须不存在。

```sh
/opt/homebrew/opt/python@3.14/bin/python3.14 -B '/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/native-full4481-v17-two-whole-batch-merge-preparation-root/merge.py' --mode merge --parent '/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/native-full4481-v16-three-member-compatible-root' --selection '/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/native-v17-two-whole-batch-material-delta-preparation-root/batch-0325/root-selection.json' --selection '/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/native-v17-two-whole-batch-material-delta-preparation-root/batch-0485/root-selection.json' --output '/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/native-full4481-v17-two-whole-batch-compatible-root'
```

接收仍调用冻结 strict-readback-receiver.verify(manifest, assignment, first)：核actual process终态、原字节first/seal/report、manual/prompt、原成员顺序、完整实际文字展示、逐字packet证据，合法NULL保留。若后次被选，所有更早attempt都必须真实终态且再次只读接收仍技术不合格。两批全部核完才建输出目录。

输出沿用 selected-records.jsonl、coverage.json、selected-whole-batch-bindings.json、strict-merge-readback.json、status.json、seal.json；多批引用改复数列表，status明确4457继承/24实际新推/2材料改变、source_common_v16与source_common_v17。原v16稳定性800身份不变；合成不等于独立准确性或稳定性验收。
