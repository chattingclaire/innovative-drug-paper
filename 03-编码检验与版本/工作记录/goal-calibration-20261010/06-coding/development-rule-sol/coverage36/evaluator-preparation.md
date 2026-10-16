# 36条开发迁移评估器准备记录

评估器已准备，尚未读取本36条fixture的reference.jsonl或coverage01 labels/admin/diagnostics；implementation03旧文件未改。实际运行由root显式通知预测封存路径后启动。

- 版本：development-rule-sol-coverage36-implementation03-interface01；固定36条、180项。
- 合成测试首轮15项通过；补充空语境文本及附件单列保留后第二轮16项通过，无失败。人工构造测试目录明确标为evaluator-artificial-*，仅为协议验证。
- 完成封存与技术失败封存分别验证，首个参照读操作严格晚于seal/freeze/execution和预测、代码、来源、手册哈希检查。
- 技术失败没有替代规则标签；缺失预测仍保留对应源记录的五项。规则null/unknown、明确NA、技术失败、FP/FN分开计数；完整180总分母与二元已定分母并列。失败运行的计算标为诊断算术。
- 每项保留完整原始source_record，并单列source_page_attachments与source_image_attachments。JPG不删、不改称PDF、不读取或解释像素。A/B参照证据及理由原样保留。
- text=None仅在通用诊断文本拼接时忽略，不改原始source_contexts，不增加CTX或标签推断。
- 准备阶段python命令不存在；后使用已安装python3完成，未执行实际36条推断或读参照。

评估器SHA256：`f1bd5b53210e04bc129e12f8a16a0fa14889773756324908c1c8c53f08df2d5c`。完整哈希绑定和构造目录见evaluator-preparation.json。
