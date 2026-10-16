# 候选09离线准备

当前只准备11条已知开发材料的两阶段执行。StageA、StageB分别需要root授权；没有自动串行运行，也没有授权146、240或4924。旧08的FAIL、完整LLM03及既有标签保持原样。

StageA先生成无五维标签的当前命题与语境关系记录。它必须覆盖当前句的对象、动作、产品属性、并列限定和实质条件，并为每个可引用语境路径记录used、not_used或ambiguous及原文锚点。这与08在最终编码同响应中要求解释不同：A先独立落盘和封SHA，经过实际语义审查后，B才可能另发请求。StageB继续收到全部原材料及同ID的原始A记录和其规范JSON SHA；A不是人工真值，B须用原文核对它。

两提示已在独立反馈之前锁定。均保留完整v1.3以及v1.4“版本与验证纪律”之前的实质操作部分原字节；不称v1.4全文，不把0.80纪律重新加入提示。最终B schema、validator和原run_attempt来自原冻结运行层，逐字节相同。

模型固定gpt-5.6-sol、medium；每阶段11条一批、单worker、1逻辑请求、最多3次相同请求的技术尝试。首次技术有效即停止，所有attempt留存，零工具。material_issue即使结构允许，也不能被语义重试或用虚构答案补齐。A有真实缺料或确定错误便停止，不人工改A继续。

## 文件和门禁

- `prompt_lock.json`：A/B提示和不变手册绑定，先锁提示后接受独立检查。
- `runtime/stageA_context_inventory.py`、`stageA_output_schema.json`、`validate_stageA.py`：A库存、schema和技术validator。库存严格复现旧B对contexts中text/headers/row_cells/caption/definition/title/note字符串叶的实际遍历语义，包括重复/空叶及旧函数忽略裸list字符串的行为；完整原contexts仍在输入中。库存证明路径和字面，不能证明语义承接。
- `run_candidate09.py`：两个独立入口、同请求技术重试、事件raw唯一绑定、A原记录封存、B另授权、全状态留痕。root语义门禁只在本地准入检查；B请求组装函数不接受门禁、意见或期待参数，packet只含rows和stageA_records。
- `initial11_input_binding.json`：11原input和visibility metadata机械绑定；后者不进任何模型请求。作者未人工阅读私有语义期待或11原文。
- `offline_plan.json`：固定范围、技术/语义审查条件、停止条件及限制。
- `freeze_candidate09.py`：生成闭包manifest；独立preflight通过后另写design_freeze，不构成实际运行授权。
- `selftest_*_no_model_result.json`：仅自造mock，技术通过不能代替真实A/B语义审查。
- `runner-code-review/`：StageA辅助模块作者对另一个作者的runner代码只读复核，非外部效度验证。原两项技术意见及旧稿保留于preparation-history；当前技术收尾增加源变更硬拒绝和预执行拒绝receipt。

## 运行接口

先离线生成manifest，再由独立preflight对其完整闭包实核，最后冻结。以下命令只是接口说明，本文件不授权真实执行：

```text
python3 freeze_candidate09.py --manifest-only
python3 freeze_candidate09.py --freeze --independent-review-file ABS_REPORT --expected-review-sha256 SHA
python3 run_candidate09.py --stage A --plan-only
python3 run_candidate09.py --stage A --execute --authorization-file ROOT_STAGE_A_AUTH
python3 run_candidate09.py --stage B --execute --authorization-file ROOT_STAGE_B_AUTH
```

实际应使用本机已给定的bundledPython绝对路径，不安装依赖。plan-only也验证冻结闭包；B的plan-only同样要求真实A门禁和另行B授权，不提前合成假的A记录。当前准备没有调用CLI或模型；未来授权execute中的CLI版本查询会单独留存，区别于模型请求。

root授权字段见`run_candidate09.py:read_authorization`：status=AUTHORIZED_BOUNDED_EXECUTION，candidate/scope/n/model/effort和design/input SHA绑定，authorized_stage为A或B，batch_size=11、workers=1、max_attempts=3，allow_other_scopes/allow_semantic_retries/allow_automatic_next_stage全部false。B另外绑定stageA_seal与stageA_semantic_gate的完整path/SHA。

A门禁status=PASS_ROOT_STAGEA_SEMANTIC_REVIEW，reviewed_rows=11、confirmed_semantic_errors=0、approved_for_stageB=true、original_stageA_not_edited=true，并绑定原A seal/output/input SHA。门禁全文只用于准入；审查意见和期待标签不会作为模型材料。B技术通过后仍要实际审读全部55维、理由、引文、子类、质量依据和顶层issues；不自动全量或采用。

## 关键风险与验证范围

A的逐字引文和路径完整不保证关系判断正确；A可能遗漏同句属性，B也可能受A错误锚定。应先完整审11条A，再评六个原始真实错误和原正确项是否同时保留，不能用合成控制分数或κ代替。新设计仍是开发修复，不能称独立真人效度验证。原11包含已登记的受保护共享上下文，当前单元ID无交集不能推成上下文全未见；原材料保真和人类展示遮蔽是两件事。
