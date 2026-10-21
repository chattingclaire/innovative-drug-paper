# 35条补跑：独立流程审查

结论：**35/35仅通过新补跑接收器的薄技术检查，不能据此认定符合原冻结全量4481整批流程。35条均应保留为另一次、已改变流程的开发覆盖补跑。**

本审查只读冻结合同、补跑脚本与35条既有记录；没有改标签、改原件、运行模型、调用原接收器或写其他目录。范围是流程与可观察证据，未裁定五维标签的语义正确性。

## 逐项结论

| 项目 | 实际证据 | 判断 |
|---|---|---|
| 冻结材料字节 | 35个目标packet均与原batch assignment路径/字节/SHA相同；0项当前绑定不一致 | 目标材料版本保持 |
| batch及上下文 | 原为既定整批、每批新上下文；补跑把32个原batch中的35条改为逐条独立CLI线程 | 原batch与选择单位已改变 |
| 并发 | 原最多3；脚本允许4；时间日志保守证明最多至少4进程重叠 | 超出冻结上限 |
| 完整文字呈现 | 35条events的aggregated_output均含完整手册/提示/协议/packet；未发现stdout截断标记 | 完整日志输出可核；模型所见未截断仍未独立核实 |
| 读取收据 | 35条均无read_manifest，未记录原要求的实际范围/事件/方法/source_id | 未满足原交付合同 |
| 每维证据 | 6条共22个非null维度证据为空；175维均未采用原pointer/quote/current-context role组合 | 原证据要求被改变 |
| 引文精确性 | 234处引文：232处逐字对应绑定packet，2处对应同次PDF提取stdout | 未发现直接可证的引文改写；不等于语义有效 |
| 图页已读声明 | 5条包含image read/check/verified声明；可用JSON事件未保存图像实际呈现回执，03876另有图像SHA读取 | 无法独立确认；SHA不是视觉阅读 |
| 输出与接收 | 35条均不兼容原schema；缺整批身份、records、read_manifest、report、seal；仅经新receiver接收 | 不能回填原canonical batch |
| 请求模型 | 35条argv请求gpt-6.1-sol/ultra | 请求已核；实际服务模型身份未核 |

## 核心证据

- [共同协议第11行](/PROJECT_ROOT/outputs/goal-calibration-20261010/03-manual/full4481-common-release-20261010-root/common-execution-protocol.txt:11)冻结既定静态batch、最多12条、260000 packet字节、最多3并发，保留首个完整整批技术有效提交；[actor说明第15行](/PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding/native-full4481-v1-sol/actor-instructions.txt:15)禁止拆成first-unit再汇总。补跑脚本[第48–57行](/PROJECT_ROOT/outputs/goal-calibration-20261010/08-audits/run-missing77-native-coverage-recovery-root.py:48)改为one source only，采用targeted_native_coverage_recovery_first；manifest也明确它不能与原主运行合称一次首次全量运行。
- [actor说明第7、9行](/PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding/native-full4481-v1-sol/actor-instructions.txt:7)要求完整且未截断的实际呈现及read_manifest；[共同协议第7行](/PROJECT_ROOT/outputs/goal-calibration-20261010/03-manual/full4481-common-release-20261010-root/common-execution-protocol.txt:7)明确程序加载和SHA不是模型阅读。35条事件确有完整原文stdout，但记录不含实际工具反馈预算/模型呈现区间，也无first内读取收据。不能从完整stdout推断服务模型一定看全；同样不能反向把没有截断标记说成已发生截断。
- [actor说明第13行](/PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding/native-full4481-v1-sol/actor-instructions.txt:13)及原schema要求每个0/1至少一条packet逐字证据；补跑[第57行](/PROJECT_ROOT/outputs/goal-calibration-20261010/08-audits/run-missing77-native-coverage-recovery-root.py:57)明确允许0的evidence为空。新接收器[第82–88行](/PROJECT_ROOT/outputs/goal-calibration-20261010/08-audits/run-missing77-native-coverage-recovery-root.py:82)只验绑定、维度集合、值成员及reason/evidence类型，不验来源引文、实际读取、report/seal、严格整数或duplicate keys；本审查另核当前35文件均为严格可解析JSON、175个值均为整数0/1/null，理由非空。
- [原validator第98–105行](/PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding/native-full4481-v1-sol/validate-structured-batch.py:98)校验packet quote为指定字符串子串及资产绑定，原validator自身也在[第139行](/PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding/native-full4481-v1-sol/validate-structured-batch.py:139)承认未独立核实真实模型/工具呈现。新接收器的35/35不应升级为更强的流程或语义证明。

无证据的22维如下：

| source_id | 空证据维度 |
|---|---|
| RECODE25-02233 | S, E, Ec, F |
| RECODE25-02269 | S, E, Ec, F |
| RECODE25-02542 | S, E, I |
| RECODE25-03474 | S, E, Ec, F |
| RECODE25-03876 | S, E, I, F |
| RECODE25-04459 | Ec, I, F |

两个非packet引文都属于RECODE25-03047的S/E补充资产证据。事件第20行对packet声明的同一原PDF执行pdftotext物理第14–15页；引文逐字存在于该stdout，原PDF在对应原assignment资产绑定中。它们不是packet字段引文，因此不能以替换字段名的方式假装已经符合原schema。完整字段、实际引用位置、事件行号及哈希见quote-exactness-audit.json与case-evidence-audit.json。

图页声明涉及RECODE25-02355、03271、03818、03876、04155。 available JSON日志仅有command_execution及agent_message项目；这类日志可能不完整记录图像工具呈现，故结论是未核实，而非断言未读或伪造。03876有asset.read_bytes/SHA动作及actual_read=true声明，字节校验本身不能证明视觉阅读。

## 具体可用用途与必要下一步

可用于单独归档此次逐条覆盖补跑、对这35条做开发诊断、核对材料字节与逐字引文；诊断指标必须清楚披露由42条原预测与35条改变流程的补跑组成，并保留未核实的读取/图页/服务身份边界。

不可作为原冻结4481主运行的完整整批首答、原canonical batch回填、同一首次全量运行、独立重复/稳定性样本、正式holdout效度或真人信度证据；也不能据它证明语义正确、实际服务模型身份或模型完整未截断阅读。

保留35条及薄技术回执原字节，不补写它们的首答或标签。若需要满足冻结生产流程的证据，下一步应另行授权并冻结新执行：使用原完整batch assignment/提示/schema/绑定资产、最多3并发、真实有界读取收据和原严格整批接收；原已终结attempt不能被覆盖或追写成原流程成功。当前审查不执行重跑。

## 审查文件与哈希

- report.json：机器可读结论、用途及限制。
- protocol-comparison.json：逐项冻结要求与实际证据。
- case-evidence-audit.json：35条逐条材料stdout区间、命令、缺失字段、证据定位与图页声明。
- quote-exactness-audit.json、concurrency-evidence.json、binding-readback.json：可复核事实。
- input-seal.json、input-integrity-readback.json、output-seal.json：输入前后SHA核对及审查输出哈希；output-seal不自包含。

服务模型身份：只验证请求为gpt-6.1-sol/ultra。没有provider wire/权威服务器模型标识；first.json及SHA均不能提升为该身份的独立证明。
