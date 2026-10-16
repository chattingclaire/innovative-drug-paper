# v33 输入消费与完整性架构审计：封存候选

本审计仅读取获准的 v1.3/v1.4 手册、冻结 v33 runtime/冻结清单和无答案共用源材料，后续按 root 明确授权读取 source-only v12/v13。未读取 r3 confirmation、reference、statistics、PRIVATE、LLM 全量生产预测或根 plan。冻结 v33 生产代码 SHA256 全部未变。最低必要候选及代码 SHA 见 `audit_candidate_manifest.json`；独立快照在 `runtime-sealed-sourceblind-20261007/`。它不发布，也不是新的严格独立确认。

## 确证缺陷与最小修复

**A：完整 following 的字段表示改变完整性结果。** v33 只读取 `verified_following_list_v27`，adapter 只处理 v8/v9。同句“药品必须符合以下条件：”和同一完整证书，仅放到 `complete_following_list_v11`，旧代码就从可判变成五维待定。认证完整的“一是…”列举也不能因不使用 v27 marker 被断言有材料缺口。候选核验目标、文件 SHA、上下文 hash、连续段落与下一边界后，仅接入完整性 gate，不复制后项维度。

**B：关键评价内容缺失只有一种句法受到保护。** v33 gate 只识别“满足/符合以下/下列条件/要求：”。无后项时，“药品的临床评价应当包括以下内容：”“申请人应当提交以下药物评价资料：”却五维0，与手册要求冲突。候选增加最小评价内容 gate；完整后项存在时不待定，组织职责、导航和发布通知引导句可按自身内容判断。初次全量执行曾把“临床综合评价有关事项通知如下”误判，已收窄为直接内容/资料谓词并加反例；失败运行完整保留，没有改源、标签或手册迁就结果。

**C：新增引用及结构字段零消费。** v33 对 `explicitly_cited_articles_v10`、`complete_following_list_v11`、`structured_following_units`、`following_context_status_v11` 均无引用；新 v12 引用也无接口。提供量分别为23、102、148、130，v12明确引用48条。这不是全部记录错标的证明。

候选提供 typed roles，区分当前实质援引、行政办理、真实局部父谓词与导航 preview，不拼接任意父段，不对所引段落整段预测后复制五维。`referenced_relations_v34.py` 在旧过滤器及 v33 修订之后运行，再重建标签，防止旧过滤器覆盖新关系。

最低必要维度消费同时要求当前连续逐字实质关系锚点和所引连续逐字维度内容锚点。当前只评价疗效时，不借入同条安全或价格；事务申报、目录评审范围、身份和导航不传播维度。明确否定/未确定的疗效及风险仍可涉及该维度。依据记录当前 span、被引 span、段落/文件 SHA、出处及认证方法。复杂未识别关系和只有资格名称的引用不强行展开，不声称完整语义覆盖。

## 跨页认证与真实局部父谓词

14条 v10 初始拒绝的原因是第七条跨页，“安/全有效”间插入 PDF 页眉页脚。候选按每页 bbox，仅去除外侧页带中稳定重复短行与装饰页码，保留正文重复行、完整实质句、一次性边缘文字和错误/内文数字。移除行保留 page、原文、坐标、理由和 SHA；不按机关、政策、ID或维度词硬编码。

认证区分原始源抽取连续重现、版式重建后重现、已有实际源核验记录与真实文件/候选段落绑定。版式重建不虚称 raw extract 原本连续。v12的197条新字段/preview记录零拒绝：v10=23、v11=102、v12=48、preview=148 全接入。context 认证方法计数为原始供给源逐字重现937、版式重建14、既有实际源核验绑定80；preview不提升为完整性证书。详见 `source_adapter_authentication_probe.json` 与 `layout_reconstruction_results.json`。

v13三条同族认证覆盖目标、完整列表、父谓词、真实标题、下一边界及视觉证据 SHA。新 repair_version 不能绕过验证：缺 family、错父谓词、未知格式伪造文本都有拒绝控制。通用 source-bound 父条款认证不再只看旧 v28/v31 allowlist。

仅当当前单元是认证列表中的信息来源子项，且实际父谓词明确要求药物对应维度的信息时，建立当前来源锚点与具体内容锚点。实际“其他来源（真实世界研究、同情用药项目等）”由临床安全性信息父谓词建立 S，不复制背景创新性或试验获取公平性；另两条父段内句不因 family 存在新增维度。

## 控制、执行与来源纪律

14个接口控制、2个缺失评价内容正向对照、12个双锚点控制、5个 PDF 版式控制、7个 v13/未知格式认证控制、132个既有纯构造回归均通过。这些是开发控制，不是人工信度或算法准确率。

封存同一源码对 v12、v13 各完成4924条，全部可判，没有强制填补待定。权威封存结果为 `candidate_predictions_v12_sealed.*`、`candidate_predictions_v13_sealed.*`。前者新增引用依据 Ec11、I2，后者增加局部来源 S1；只是执行计数，不是性能提升计数。

同码 v12→v13 差异保存在 `same_code_v12_to_v13_differences.json`：五维变化1条、安全子类型变化1条、依据变化1条；F/I子类型及质量口径无变化。这是源更新的开发诊断，不能冒充纯代码改进。r3已被root接触，即使本执行者不知新标签，也不能声称严格新确认独立、达标或信效度通过。

重现脚本：`reproduce_architecture.py`、`reference_relation_controls.py`、`layout_reconstruction_controls.py`、`v13_local_family_controls.py`、`run_existing_constructed.py`。全量脚本 `run_candidate_v12.py` 绑定输入与代码 SHA，拒绝覆盖既有运行。
