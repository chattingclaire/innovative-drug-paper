第一次组合存在已确认的接线错误，暂不批准采用：standalone E 的 guarded consumer 在 acc.finish() 前，初始 combined 和实际封存 snapshot 则把 consumer 放到 finish 之后。该 consumer 只 acc.add('E', ...)，不能更新已生成的返回 decisions。仅移除新增节点可恢复完整 IF AST，并不足以证明新增调用位置正确。

第一次225项实际运行已独立读回：原期待和 hard 标记逐行相同；210 hard 中197通过、13失败，另15 pending。13失败完整保留，其中11个新增 E 阳性实际均为0；另有01402/I和既有 clinical_comparison_without_innovation。S/Ec完整decision、旧relation和来源状态均相同，没有异常或分类文件读取尝试。未重跑任何控制、selector、classifier或LLM，未改现有封印。

ROOT已确认组合插入位置错误，将另存 combined-v2 与新的225控制结果。此文件封存初始错误的位置、源hash和第一次13失败，暂停最终采用审核；后续修正版不能覆盖第一次失败证据。本审查不是对本代理先前自编运输适配器的独立作者审计，也不是正式语义验收。
