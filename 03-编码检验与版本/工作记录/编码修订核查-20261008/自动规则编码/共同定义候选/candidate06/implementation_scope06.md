# candidate06 实施交付与范围

candidate06 从冻结05另存，目标手册绑定新定稿 `5abee1f2448cd8a54403d2ac615fea8ebc3c162e78c907029322ec0e85a9556c`。已逐段比较新旧手册并保存完整 diff；本次实质实施 E 需求／效果边界、有效药物选项缺失，以及 I 路径2的自足改良和基准／资格关系。不是仅更换 SHA，也不声称已穷尽手册自然语言或通过效度验证。

## 实现内容

- E：删除“满足临床需求程度”的独立阳性分支；同句独立药物效果、证据要求及否定／不确定效果保留。补入明确无有效药物选项；旧“有效治疗”片段在该命题内先按实际药物对象重新绑定，不能绕过来源校验。费用／供应障碍中的获取谓词只局部排除其“有效治疗”名词依据。无有效选项与某一药物无效分别留痕。
- I：自足药物产品属性实质改良（含评价、否定、不确定）不额外要求基准或已证优效；普通变化必须具有既有药物基准或实际改良研发资格、当前属性改变、原文治疗／使用改善关系。保留三个独立锚点；语境补全时保存认证前句。另一个培训措施的效果不能拼给属性变化。
- 明确“同一药物制剂”的并列动作可继续使用原基准，出现“另行”也不阻断；换到另一无明确基准药物或设备则不能借用。原隐含并列例的预设0有歧义，单列为观察，不作为真值或通过项。
- 必要同段语境调用实际 TXT／JSON 或 layout 认证，不接受仅自报 verification；失败显式抛出来源错误。旧 v34 总认证器及旧03表格／条款解析未改。06 共享段落入口收紧为实际 literal/layout 重现。
- runtime 身份及活动共用定义锚点绑定新手册；runner 启动时核实际手册字节，并将路径与 SHA 写入运行记录。旧继承证据保留其历史 rule/basis，同时另记目标手册及本次陈述性质，便于追溯。

## 先设计、后执行的构造检查

所有新句为人工构造（由编码代理编写），没有读真实新材料或参考标签。原35项设计及4份增补均在其相应实施／执行前保存。

最终实际执行 **50 项：47 项明确语义检查通过，2 项来源错误技术检查通过，1 项预期有歧义的观察不计通过**。技术异常不是维度真值。另5个既有受影响构造脚本实际 exit0，未与上述计数混加。构造使用真实临时来源文件和真实认证器；新构造通过完整候选代码路径，未 mock 来源认证。

首次执行有3项失败，原输出 `constructed_execution06_attempt01.json` 完整保留：独立疾病控制效果未覆盖、旧短证据绕过对象校验、自足实质改良评价仍受长度限制。均按预存预期修复。并列动作原预设0及历次执行不改；后续概念审阅撤销其唯一预期地位，见 `constructed_expectation_ambiguity06.json`，最终计数已剔除。

## 尚未覆盖或未重新审查的路径

- **E inherited effect vocabulary and general object paths**：The general-demand alternative and access-only effective-treatment noun are corrected; old independent effect/evidence rules remain. Other generic phrases such as clinical actual significance or target-indication rationale in the inherited list were not newly semantically audited. Target-manual binding does not assert full equivalence of every inherited E path.
- **E necessary object references beyond immediate paragraph predecessor**：The new no-effective-option relation supports explicit current drug options/active frames and an authenticated immediately preceding same-paragraph active drug-treatment/research frame (up to 300 chars). More remote paragraphs, title-only objects, complex cross-article referents and multi-object discourse are not resolved here. Supplied attempted context failing literal/layout reproduction raises a source error.
- **I path2 complex change/baseline paraphrases**：Core direct and source-bound baseline or actual improved-RD qualification + property change + treatment/use benefit is implemented. Detailed numeric transformations, inverse word order, multi-step implicit comparisons and unlisted paraphrases are not exhaustively recognized. The implementation does not turn missing grammar into evidence that the text semantically lacks innovation.
- **I implicit parallel-action baseline scope**：Explicit same-drug/formulation references retain a shared baseline, including 另行. The original implicit parallel example has nonunique expected 0 and is retained only as an observation; no blanket 另行 veto exists. Unexpressed or ambiguous sharing is not inferred by this bounded matcher.
- **I existing03 and05 context routes**：The consumed current-paragraph authenticator now requires literal/layout reproduction for all its routes; old03 semantic scope grammar is otherwise retained. New delta06 does not purport to re-audit every inherited I relationship.
- **Statement-nature metadata**：No-effective-option and specific-drug-ineffectiveness are separately marked. Remaining affirmative, requirement, negation and uncertainty annotations use current local expressions; nested logical negation and complex condition scope are not fully parsed.
- **S/Ec/F and unrelated parent/table modules**：Their concepts did not change between the two manuals. No new corpus-wide semantic validation, model comparison, prevalence target or score-based tuning was performed.

## 交付与不变范围

共有 43 个 runtime Python 文件；相对05变动旧文件 6 个、新增 2 个，逐行差异见 `code_changes06.diff`。角色与路径详见 `implementation_delivery06.json` 的函数行号、完整散列和具体实现说明。

最终43py整体 SHA256：`7dfaabaeb827477dbb9b86ce0221409997eb160d1b5f05782a9641fb7f488084`（排序 filename + NUL + bytes + NUL）。原05的41py、2个runner及2个实际输出共45个文件逐项散列保持不变。未运行真实21、33或全量，未调用外部LLM，未冻结或正式采用06。实现已停止修改，交 root 独立复核后冻结，再做授权的有界真实材料执行。
