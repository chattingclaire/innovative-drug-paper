以下仅为将来入口模板，未执行。所有 DELTA_* 参数应由 ROOT 在最终候选及 selector 到位后逐项设置；DELTA_MUTABLE_DIMENSIONS 为已批准的非空唯一维度数组，不能默认赋为全部维度。

生产静态契约需有 `allowed_mutable_dimensions`（S/E/Ec/I/F 固定顺序）、`manual_static_audit.approval_actor="ROOT"`、`approved=true`、`only_allowed_dimension_decision_or_explicit_request_mutations=true` 以及实际 proof bindings。required manifest 可诚实使用 `required_member_readback_complete=true`；兼容接受既有候选的 `independent_readback_complete`，不宣称本适配器由独立作者审计。ROOT 的实际 pre-inference adoption sidecar 还需明确记录相同 `allowed_mutable_dimensions`，并保留既有完整采用字段。prep 不会为 ROOT 生成此 sidecar。

准备入口（生成冻结运输元数据，不执行分类）：

```zsh
"$DELTA_PYTHON" "/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/08-audits/generic-rule-delta-execution-adapter-sol/prepare.py" \
  --selection "$DELTA_SELECTION" \
  --candidate-directory "$DELTA_CANDIDATE_DIRECTORY" \
  --candidate-version "$DELTA_CANDIDATE_VERSION" \
  --driver-version "$DELTA_DRIVER_VERSION" \
  --candidate-delivery "$DELTA_CANDIDATE_DELIVERY" \
  --candidate-freeze "$DELTA_CANDIDATE_FREEZE" \
  --required-candidate-members "$DELTA_REQUIRED_MEMBERS" \
  --parent-composite "$DELTA_PARENT_COMPOSITE" \
  --original-preparation "$DELTA_ORIGINAL_PREPARATION" \
  --authorization-id "$DELTA_AUTHORIZATION_ID" \
  --mutable-dimensions "${DELTA_MUTABLE_DIMENSIONS[@]}" \
  --output "$DELTA_PREPARATION_OUTPUT"
```

合并入口（仅真实一次完整 affected pass 成功并封存后）：

```zsh
"$DELTA_PYTHON" "/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/08-audits/generic-rule-delta-execution-adapter-sol/merge.py" \
  --preparation "$DELTA_PREPARATION_OUTPUT" \
  --parent-composite "$DELTA_PARENT_COMPOSITE" \
  --original-preparation "$DELTA_ORIGINAL_PREPARATION" \
  --candidate-version "$DELTA_CANDIDATE_VERSION" \
  --mutable-dimensions "${DELTA_MUTABLE_DIMENSIONS[@]}" \
  --output "$DELTA_COMPOSITE_OUTPUT"
```

`--validate-only` 为只读接口：不创建任何准备或合并成果、不创建 adoption，不执行候选或 classifier。旧 v9 缺少新 transport proof 和维度字段时，仅此旧 IF 只读检查允许归一化；生产始终要求新完整绑定。勿用 Python -O；两入口明确拒绝关闭断言的运行方式。
