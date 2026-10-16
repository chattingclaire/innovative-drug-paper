# 新完整批次恢复轮：独立预检

**原研究材料和整批结构保持一致；接收与运输身份说明需要补强。** 207批、2349条的成员/顺序、packet、手册、提示、资产、batch上下文及null/证据约束均与原轮一致；schema仅改变run_id和scope常量。此轮另存，不能称旧轮第4次。

本审查只读原轮、新准备和运行中pilot，不调用模型、不改first或标签、不写旧目录或v2准备。

## 真实差异与重要修复

- v2接收器只验seal的first/report SHA，遗漏原v3的run_id/batch_id、template_only=false及actual_completion_claimed=true；空actual_input_bindings也可通过。提供的strict_reception_guard.py只读补验严格schema、0/1逐字packet证据、上述seal身份/完成、非空且属于冻结白名单的输入绑定，以及一个正常终结CLI turn。原首答不变；薄回执与补强回执分别保留。
- v2准备允许后续13并发，共同协议为3；当前实际pilot为3，尚未发现13执行。ROOT撤回该计划，ROOT-transport-capacity3-sidecar.json供新controller冻结，后续必须实际拒绝超过3的配置。已读v2准备字节不改。
- 新output-validation-contract仍写旧轮run_id及旧schema/validator/routing；新routing header也残留旧run_id。实际新assignment/schema/routes具有新轮身份。应在ROOT运输说明明确历史引用与新执行权威，不能悄悄重写已经被pilot读取的文件。
- 新schema重新缩进，从72593变为310458字节；actor又新增完整schema阅读要求。原严格validator只核manual/prompt/packet的声明整篇覆盖，不自动保证schema完整呈现。独立事件快照保留实际已呈现范围，不能从有效schema解析推断模型已完整读schema。
- 原脚本按1至3次顺序选择首个技术有效整批，没有标签比较或拼接。新controller须以补强回执作为有效和展开门槛，不能只看既有root-selection文件存在。系统性模型/account拒绝时停止新派发；合法null或语义分歧不得触发重试。

## 可执行补强接口

运行strict_reception_guard.py时给--manifest、--assignment、--submission；该程序只向stdout返回补充回执，不写接收目录。也可调用verify(manifest_path, assignment_path, submission_path)。默认template_only沿原v3的缺失视False行为，actual_completion_claimed必须为真正True；--require-explicit-template-false是更强的新规则，不能在已派发后追加要求。

pilot快照不是终结判定。正在运行时未产生first/seal或材料覆盖尚未完成，应保持pending；首答终结后由补强模块判断是否技术有效。若seal标志缺失/错误或证据格式不符，保留原件并按新轮有限技术重试规则处理，不能补写首答；null本身始终不是失败理由。

## 证据与限制

frozen-comparison.json含207批逐项差异及旧297成功selection字节核对。pilot-observation-snapshot.json与三个immutable events快照含实际stdout范围核对；这些事件不能证明服务端模型身份，也不保存实际工具反馈预算或所有图像呈现消息。完整stdout与无截断标记只能支持日志层观察，不能提升为独立模型完整未截断阅读证明。

输入前后SHA见input-seal.json/input-integrity-readback.json；guard及容量sidecar有独立guard-ready-seal.json，全部审查输出最终SHA见output-seal.json。输出仅在本审查目录。
