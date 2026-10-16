仅源码投影与构造检查已完成，尚未生成或导出真实全量模型输入。入口仅允许 `--self-test`；纯函数 `project_record` 供根代理审阅后另行决定使用。原始输入、既有报告中的 false 和冻结方案均未改动。

表格同时保留原有序表头数组、真实行单元格数组、行号与逐列配对；每个非空真实表头/单元格另有可被现行 validator 引用的独立 text 发生位置，指向父表及实际列位置。重复值不去重，不把重排拼接当作原文整句，不由表头生造标题。确指地址、list 顺序、父标题/父命题/成员及实际下一边界保留显式结构链接；文件名 source_title 不作为政策标题或引文。

13 项全新构造检查通过，包含重复单元格位置、表列配对、确指列表、重复段落、意见去除、无标题猜测、临时文件 SHA 相等/不等及现行 validator 引文路径。初次构造检查发现 validator 不遍历数组中的直接字符串；独立 text 位置方案已修复投影兼容性，validator 未改动。

5 个 source_sha256_bound=false 的逐条元数据澄清保存在 source_sha_binding_clarification01.json：均为盲包 generic source SHA 与 input.source_sha256 相等、与 input.unit_source_sha256 不等。当前 unit_source/unit_source_sha256 配对优先，绝不跨层混合路径与 SHA。原 false 保留，且此澄清不证明 alternate source 已认证。

每个政策 leaf 的字面来源缺少明确冻结绑定时仍为 unbound_policy_leaf_candidate。已有 manifest 可做文件 SHA 机械相等检查，但不据此声称文字 leaf authenticated；显式匹配绑定也仅称 externally_manifest_bound_not_reauthenticated。未知家族/模糊边界和表格维度不符会留 issue，不能静默视为就绪。完整实施字段白名单、去除字段与散列见 source_only_projection_delivery01.json；先前设计文件保持原样。
