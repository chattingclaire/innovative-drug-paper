本目录是本代理编写的通用运输适配，不是新代码的独立作者审计。采用前由 ROOT 阅读源码差异并在外部静态契约记录代码阅读批准。未猜测 v10 最终版本、影响集合或必需成员；未打开或执行 v10 分类、selector、准备、合并或新语义 controls。

`prepare.py` 将候选版本、完整兼容父代、原 common 准备目录、冻结 selection、candidate freeze/total seal、完整 required members、driver version、授权标识和输出改成必填 CLI 参数。新增必填 `--mutable-dimensions` 接受 S/E/Ec/I/F 的非空唯一子集，按五维固定顺序绑定 `allowed_mutable_dimensions`；没有默认允许维度。保持 4481 原 common 的逐行字节、原序和 UTF8 lineage，五模块与静态 proof/全部有限 controls 实际总 seal 成员绑定；adapter/status_bridge 原字节不变；driver 仅七项运输替换，逆替换后完整原 AST 与文本一致。prepare 不运行 classifier，也不创建 ROOT adoption。

`merge.py` 仅接受一次实际已完成、已封存、零技术失败的 affected pass；外部 ROOT adoption 必须早于真实 started_at。所有候选、父代、scope、selection、输入、slots、origins 和 driver 约束在创建输出目录前验证。可变维度绑定 CLI、契约、plan/scope/algorithm 与 ROOT sidecar，补集完整 decision 同时要求结构相同和原 JSON 值 UTF8 字节相同；未选原父行与已选实际 delta 行均原字节保留。输出保留实际来源及继承历史，22405 槽和合法 null，不开启正式、人审或正文 gate。

最终语法通过。现已完成 v9 的只读兼容检验通过：3904 所选、577 继承；原 common 子集和 lineage 相同；完整 4481 prediction 行及 22405 slot 行字节相同，counts/origins 相同，S/E/Ec 完整决策字节相同，实际 value 变化145、decision变化184。旧 IF 契约归一化仅限此 v9 的 `--validate-only`，不能用于生产采用。旧原件与既有 sealed 输出未改。

详见 delivery-report.json 的实际路径/字节/SHA、两份完整差异和最终兼容记录。最初两份没有 final 字样的兼容 JSON 属于未封存草稿阶段；最终采用依据只绑定 final 记录。未来输出字段已由 v9/v8 固定名称改为通用 candidate/parent 名称，ROOT 应在后续统计适配中明确绑定真实合并文件。
