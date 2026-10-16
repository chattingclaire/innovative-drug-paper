Reader接口适配已完成，raw来源核验成功；两条更新确指图均明确为`UnsupportedSourceGraph`，没有进入判读。

- source_packet SHA: `dee2733f551797ec1485eb5316e00ffc71f9ad539c276b023dfd18d5dc08276e`。
- 48个预声明synthetic controls全部通过；此前45项通过的候选、测试、声明和实际接口日志全部保留。
- 两条raw来源分别保留60/46 contexts；每条37段同快照全文、1份原geometry、9附件及原source_ref/source_references完整保留。load返回原始parsed JSON对象相等，规范化JSON字节完全等价。
- 新增字段、kind、regions、geometry仅做strict type/ID闭合与资源SHA/文本/定位核验，不改原kind/边/角色，不从resource造context，不继承全文维度。
- semantic_unit使用原冻结reader的kind集合（核验完全相同）；新kind或非空source_references明确拒绝，raw对象在拒绝后不变。原契约synthetic材料仍可产生unit。
- loader只读13个exact材料路径：design、source、manual、resource及9张PNG；不需要source_seal、原PDF或旧projection文件。精确路径与SHA详见reader-exact-material-read-allowlist.json。
- evidence/relations/dimensions与授权冻结SHA、implementation04原文件逐字节一致；本代理未修改runner。

原reader真实失败见reader-before-interface-adaptation-failure.json；最终raw保全及严格unit拒绝见reader-actual-raw-attempt02.json；完整shape/资源inventory见reader-source-schema-inventory.json；完整diff见reader-interface-adaptation.patch。未读取new2 reference或A/B/native输出，未运行实际预测。
