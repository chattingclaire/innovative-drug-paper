# measurement adapter v4

只修历史闭包接口；旧 v1/v2/v3 脚本、真实失败、数据、统计和参考全部保留。

真实 v6 采用配置已实际接入，输出位于 `actual-payload-pending-independent-QA-v6/`，状态 `assembled_pending_independent_QA`；退出码 2 仅表示尚待根代理实际独立数值 QA，不是成稿成功。39 个字段、52 段替换、表 2/3 与图 2 数值包已构建，未输出 DOCX。

窄修复只允许已经核 SHA、文件名含 PENDING、文档 status=PENDING 且两项根采用标记均 false 的历史采用模板，在递归闭包中跳过精确的 `{path:null,sha256:null}`。本次两份模板合计 32 个指针完整留痕。直接 verify/json/object、当前采用配置的必需字段和执行 QA 不接受此占位符。

根代理后续使用本目录 `independent_verify_adopted_payload.py` 对实际 payload 独立数值核验；须真实 PASS 后才按同一代码和配置绑定生成 ready 状态。当前没有运行独立数值 QA，也没有伪造 ready。
