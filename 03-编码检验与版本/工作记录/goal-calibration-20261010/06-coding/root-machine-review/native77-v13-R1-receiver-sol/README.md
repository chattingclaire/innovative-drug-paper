# 原生77条R1首件接收准备

本目录只准备接收入口。复用封存plan-v2、wrapper-v2、原schema及v4 gate/native_records，不创造actor首件或真实阅读收据。准备期间不读取任何attempt或scheduling实际结果，不做标签/性能审查。

ROOT在actor完整seal存在后，以新的独立Python进程调用receiver.py，提供`--actor-seal`、`--batch`、`--attempt`、真实`--creation-request`/`--creation-return`和本目录内新的`--report`路径。request/return须是scheduling中实际工具记录；如有外层包装，用`--request-pointer`/`--return-pointer`指定JSON Pointer；`--thread-pointer`默认`/threadId`，`--runtime-pointer`默认`/runtime_uuid`，须按真实identity字段指定，不能改actor文件。

新的短bootstrap使用`--scheduling-root`指定native-llm77-v13-sol/bootstrap-scheduling-v1，再提供冻结launcher的`--initial-prompt-file`和`--initial-prompt-sha`。真实creation request.prompt须逐字节匹配该文件且≤4000B；receipt.initial_prompt_sha256只绑定实际launcher。`--original-instruction-file`另绑原完整R+wrapper长材料，SHA仍核plan-v2的原值，不冒充实际初始prompt。文件SHA核对不宣称已经通过工具完整读过长材料，实际阅读保持由事件证据说明。旧scheduling七首次已被ROOT行政停止，入口保留该事实且不选complete_valid，不推断所有七批均已截断。

用`--runtime-evidence-member`和`--runtime-evidence-pointer`指向actor seal中真实环境工具返回的UUID值（stdout仅去末尾CR/LF）；缺少该原件时身份匹配保留待核，不把identity自填字符串当外部证明。

入口先核完整seal全部成员SHA/bytes及无未封存成员，再读取actor成员。核实际创建提示SHA/配置、threadId与runtime UUID、逐条first-output与whole.items同对象/完整次序、原schema、完整current/原CTX连续引用和独立public quote，并用v4 records.check_saved_scopes核实际保存的scope-check列表。所有actor首件只读。缺seal保持pending且不读取partial。

可选`--technical-evidence`为ROOT取得的真实外部技术证据索引，结构为`{"facts":{"known_compaction":{"value":null,"artifact":{"path":"实际选定scheduling原件绝对路径","sha256":"实际SHA","bytes":0},"json_pointer":"/真实字段"}}}`。示例是接口形状，bytes/SHA不能照填。可用事实键为known_input_truncation、known_output_truncation、known_compaction、additional_user_messages、hidden_background_history、complete_platform_history；null或缺项保持未知。非null事实必须与实际外部原件对应位置完全一致，不接受actor自填字段作为外部证明。未知完整平台历史不会被编造成false；provider/wire容量、参数和telemetry保持不可见，不作为额外拒绝条件。

只有真实冻结用户消息历史为[]、且完整有效候选所需三个known技术字段均有实际false证据，才调用原records.select_technical_receipts。证据不足返回selection_pending_technical_evidence，保留首件，不拒绝native、不触发重试。不得为了调用旧接口把未知填false。合法null/request不重试；确证技术失败最多三次fresh同byte重试。使用`--prior-report`按序绑定本接收器先前封存报告，不能略去失败或拼接attempt。

public-only支持无法由原必填schema表达时，保留完整首件、原quote和读账，具体schema错误作为format_failed并标terminal_no_retry；不能伪造current/CTX、改标签求通过或扩schema。接收报告包含input/actor/creation/history绑定、format与scope结果、真实技术事实/未知项、receipt、selection及retry_policy；报告和伴随seal排他写入。本R1-only入口从不调用all_batches_sealed_gate，不宣称RWH五条件完成。

这里只做代码语法/CLI帮助检查，不跑旧套件或构造新大套件。实际接收由ROOT之后调用；准备模型调用、actor读取和阅读收据均为0。
