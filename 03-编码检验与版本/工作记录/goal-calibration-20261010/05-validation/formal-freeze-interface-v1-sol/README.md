已实现最小兼容入口；18项有限构造检查通过，实际规则/模型/800编码/真人接收为0。正式手册绑定a0ef2967ef964c625f331fefa82f4020d384ecae579e2a0a7d178651e8beda70，42660 B。联合发布和真实身份仍pending。

规则入口（未来ROOT完成scope并授权后，当前未运行）：

    python3 /PROJECT_ROOT/outputs/goal-calibration-20261010/05-validation/formal-freeze-interface-v1-sol/rule_driver.py --scope /绝对路径/已冻结scope.json --scope-sha256 <真实SHA> --input /绝对路径/原packet.jsonl --input-sha256 <真实SHA> --out /绝对路径/新首件目录

scope须status=frozen_for_execution，显式输入/输出、顺序/N/5N、来源seal/material_bindings、实际manual和algorithm_bindings。rule-scope.template.json尚不可执行。driver从algorithm-bindings.json的原路径、SHA和bytes加载五个封存v17模块，未复制或修改判定算法；可接裸完整bundle或现五键wrapper，仅解出原source_bundle，保存外层盲号/原行UTF8位置/SHA和嵌套对象SHA，不改变源对象。原图与源材料按原scope/receipt resolver绑定；规则仍不冒称像素阅读。来源全局故障若发生在创建授权输出后，保存driver-failure.json和failure seal，未处理维不补0；preflight不合法则stderr拒绝，不启动推断。max one是每个冻结scope的单次首件，不自动重试。

新真人入口（未来提交后；命令例未执行研究材料）：

    python3 /PROJECT_ROOT/outputs/goal-calibration-20261010/05-validation/formal-freeze-interface-v1-sol/human_receiver.py verify --interface v14-wrapper --packet-dir /绝对路径/本方coder-A --labels /绝对路径/labels.jsonl --submission /绝对路径/submission.json --sidecar /绝对路径/submission-sidecar.json --release /绝对路径/本方release.json --release-sha256 <真实SHA>

将verify改seal并加--destination /绝对路径/本轮首判封存目录即可原字节封存。已经封存的目录不覆盖；补材另round/release/目录。human-release.template.json仍pending，不授权当前编码。现800packet、labels.blank、原manifest和submission.blank一律保留。新release单独指向原packet/asset index及实际1.3F手册与身份登记，不重prepare/draw；分发给正式编码者的手册仅manual.md或同字节manual.txt，不把历史发展裁定、change-log、source-index或工具账本当共同手册。

完成labels保持现四根键及每维现七字段：value/evidence_path/current_quote/context_quotes/source_quotes/reason/material_request；unfilled/null占位不能接收。source_quotes保存exact五字段source_id/source_bundle_sha256/bundle_pointer/quote/span，span为Unicode码点半开区间，匹配原字符串叶，不能伪造CTX或拼句。I3和具体F原必要证据放sidecar.path_evidence，null保留具体缺材/未知理由；0也须当前引文和理由。缺失说明使用现一维一个material_request对象，多个缺材事项可在needed_material明确列出。

submission使用现原字段并增加sidecar_sha256；完成状态/真实时间/身份/标签及sidecar SHA如实填写。identity_registry绑定JSON的actors项须有executor_code/actual_actor_type/assigned_side，release与submission一致。purpose=independent_validation只收real_human_independent且无AI草拟、四项独立声明真实为true；AI_draft、human_posthoc_review及synthetic_fixture明确分开，AI/构造不称human_coding_completed。工具不能证明真实人员身份或独立性，外部登记审查保持pending。

sidecar结构见submission-sidecar.schema.json；blank是待填模板，不是合法完成提交。逐记录保存blind_id、五维path_evidence、source_read_events/source_use_events/image_view_events。source read绑定原bundle_pointer、对应text或对象/geometry视图SHA、实际演员/时间/完整交付声明；use必须接同条真实保存的read事件，当前引文、CTX及公共quote需对应实际读/用，不能由库存可用推定。CTX文字叶事件和共同对象事件均支持。图片事件另含原对象pointer与同资产SHA、真实像素查看声明/位置/观察文字；实际图片bytes SHA校验仅是完整性核验，不能当已看图。必要材料缺失仍走合法null；不要求机械读全库存。专项关系只保存和校验形式证据，不自动裁定关系是否实质成立。

旧入口兼容：human_receiver.py verify或seal --interface legacy后沿旧--packet-dir/--labels/--submission/--destination直接委托原workflow，不给旧包套新schema。只用两个全新构造旧记录确认该接点，没有运行旧测试套件或读取实际旧标签。所有构造事件均为临时synthetic fixture，已删除，不是研究read/use/真人首判。

此交付不修改LLM入口。source/index/material位置、身份/访问、联合发布与实际执行由ROOT后续真实绑定；本次代码格式通过不代表human/formal passed，也没有新的CI、准确率阈值或验收门槛。
