# 固定800条重复稳定性：外部捕获运输准备

本目录仅完成可执行准备、静态输入预检与机械故障控制。实际模型调用、分类器调用、已完成独立R重复均为0；GO未签发。原生产controller、slot、旧800方案、手册、prompt、协议、参照和标签未改。

## 固定设计与用途

沿用旧800条、87诊断批的成员、顺序、分层权重和五个逻辑条件。R1/R2/R3都是以后新建的独立批次会话，使用相同批次目录、相同核心请求字节和相同可控CLI配置。当前生产P及其技术重试均不算其中任何R。批次内条款共用上下文，不能声称逐条会话独立。

W沿用既有格式扰动packet；800组JSON解析对象实际核对相等，文件字节、hash和绑定路径不同。H仅改变请求首行；其余请求字节与R相同。W/H用于格式和表述敏感性诊断，不能充当R重复或补救不满意的结果。

该87批方案可以支持所披露诊断分组下的抽样重复稳定性。它与原生产P整批分组有差异，仅13个诊断批与P整批重合；不声称复现P整批。若要求保留800目标在P中的完整同伴上下文，另一路是351原批、3759条闭包，不能拿87批结果替代。这里选择87批以避免为800目标重复2959条伴随材料。原预设并未要求R必须等同P分组。

800样本保留remaining600/exposed200和历史机器辅助分层身份；不能称为新的盲真人验证或纯来源特征抽样。未读取新真人200答案。

## 输入与原首答来源

`prepared-fixed800-87-v2/run-manifest.json`绑定当前共同manual、execution_prompt、protocol、原packet、既有Wpacket、CLI和接收运行时。预检核对2663个唯一输入绑定、800组W对象相等、全部87批R的stdin/CWD相同；1305预留attempt槽全部为空。

每批提供相同只读`./assignment.json`。固定request不追加condition、attempt或输出路径；ROOT-only-route-ledger保存外部路由。assignment中保留的`attempt_output_routing`字段实际指向共同运输说明，不提供真实路由表。CLI的外部`--output-last-message`地址因slot而异，不属于stdin。该差异与ROOT运输改版已明确披露，不能称整条provider请求完全相同。

actor只读允许绑定输入，以每段至多2500 Unicode字符的helper显示完整文本，并在首答前完成manual/prompt/每个packet全部覆盖。完成命令事件须包含完整BEGIN、逐字正文和END，截断或伪造片段不算阅读。解析或hash不能代替模型阅读。必要图页另保留实际可观测工具事件。

actor最终只输出一个完整严格JSON，不写first/report/seal。ROOT保存CLI外部捕获的原始最终消息字节，原样复制为first，机械生成标明`ROOT_transport`身份的report、seal和receipt。seal明确run_id、batch_id、template_only=false、actual_completion_claimed=true及非空实际输入绑定；后一个标志只指实际CLI回合和捕获完成，不声称actor创建文件、真人复核或provider原始wire。

## 严格接收与故障控制

保留原严格schema、原批成员及顺序、0/1至少一条packet指针和逐字连续quote、语境限制、合法null规则。核心接收器仅加两个运输helper依赖允许绑定；逆还该单个AST块即与原AST一致。共同manual/prompt须覆盖全批，每个packet须覆盖对应source。真实事件须有唯一新thread、已完成回合和唯一结构化首答；禁止二答池、跨attempt拼接或按标签挑选。

每批至多3次真正技术attempt；只取最早技术有效的完整首答。合法null一经接收即终止该批，不触发重试。ROOT接收或依赖错误不作为模型重试理由；已完成CLI槽可仅补齐ROOT接收/选择而不再调模型。不能证实旧进程组结束时保留容量阻断并停止后续条件，需要ROOT处理；不得制造末态。

同campaign使用controller独占锁和3个OS容量锁。四个本地非模型测试进程的实际同时活动峰值为3。正式提交顺序固定，实际进程开始/完成顺序分别记录，不能保证或声称并发下物理完成顺序相同。GO还要求生产/恢复派发已关闭，避免与生产进程叠加。

最终37项机械控制全部通过，包含合法null、逐字证据、完整展示、首答唯一性、真实/fixture来源隔离、seal必需身份标志、同thread复用、防重复选择、未GO拒绝、进程不确定阻断和全部五条件末态前禁止统计。最初测试驱动误将assignment绑定对象当路径，2项正例失败、16项TypeError拒绝不计为有效负例控制；原记录与当时代码保留。修正驱动后的25、35、36及最终37项结果均保留，没有为通过修改分类期待。控制使用TOY fixture与本地非模型进程，不构成真实LLM兼容或重复运行成功证据。

原统计calculate函数AST、bridge和数学engine原字节保持；不会在五条件未全部末态时导入/计算统计。预设的R两两、R三次、W/R1和H/R1比较及800/600/200范围不变，未增加或更改阈值。

## 待GO依赖和唯一执行入口

ROOT先确认当前生产与恢复controller及真实子进程组全部末态，关闭生产/恢复继续派发，并签发独立的真实生产末态证书及`ROOT-execution-GO.json`。GO必须绑定本manifest、预检报告和真实末态证书，最大并发=3；证书绑定真实末态材料、活动模型进程数=0、全部子进程结束及已关闭PID，接收器再核对这些PID不存在。仅释放旧锁、预留目录或准备报告不够；PID复用造成保守阻断时保留原记录并由ROOT处理。

两个`.template.json`故意不合法，不能直接使用，也不是当前GO。下列命令尚未执行；未来真实GO就绪后，ROOT只需这一入口，按R1→R2→R3→W→H顺序完成全部87批，已有合法选择会复用而不重复调度。统计另在实际五条件末态后按保留接口办理，不属于本次准备完成声明。

```sh
/opt/homebrew/opt/python@3.14/bin/python3.14 \
  "/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/current-freeze-stability-external-capture-v2-sol/controller.py" \
  --run "/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/current-freeze-stability-external-capture-v2-sol/prepared-fixed800-87-v2" \
  --go "/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/current-freeze-stability-external-capture-v2-sol/ROOT-execution-GO.json"
```

本次435个首轮批次进程仍未调用；1305只是五条件×87批×3attempt的预留上限。并发上限是3个真实CLI进程，实际服务API请求数不可从本地事件推定。

## 观测限度与封存范围

新运输层未实际启动CLI（包括help），因此未观察真实首答成功或新runner运行兼容性。指定模型gpt-6.1-sol、reasoning_effort=ultra；实际服务模型身份未独立核实，未公开seed/temperature/top_p记为null。

完整工具事件和hash证明可观测呈现与绑定，不能证明隐藏provider上下文、语义理解或provider原始wire。read-only sandbox防写；helper和接收器只接受允许绑定材料。但这里没有认证逐文件操作系统读隔离，ROOT-only目录也不能据此宣称绝对不可读；不得把允许清单等同provider读取范围证明。

`freeze-seal.json`绑定本目录现有不可变文件，排除Python运行缓存和seal自身。它封存准备时实际存在的文件及空槽状态，不绑定未来执行后目录树不变。未来GO、ROOT进程与接收记录按外部台账独立增加，不覆盖准备件。交付到此停止，没有启动模型、分类器或新增审计。
