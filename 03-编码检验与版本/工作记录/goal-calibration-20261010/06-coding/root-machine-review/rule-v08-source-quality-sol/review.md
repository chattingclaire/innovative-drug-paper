有限机械核查完成：v08 总 seal 的实际 SHA 为 `0a31bdc4207b0d908c274dc81c9d623381b701a1a53a634469c08080c24ddf06`，bytes=28531。719 项封存绑定检查覆盖 350 个不同文件，未发现 SHA/bytes 不一致；旧 v06 的 103 项及 v07 的 73 项封存文件均保持原字节。

| 首次范围 | 记录 | 五维槽 | 编码 null | 技术失败槽 | freeze → start → complete → seal（UTC） |
|---|---:|---:|---:|---:|---|
| old41 | 41 | 205 | 0 | 0 | 22:07:53.490245 → 53.494131 → 56.256672 → 56.268403 |
| old36 | 36 | 180 | 0 | 0 | 22:07:56.435978 → 56.441315 → 58.224296 → 58.232074 |

两次合计 77 个不同记录、385 个完整槽。保留 0/1、编码 null 和技术失败状态已分别核对；实际 prediction、decision 与 slot 值相符，无技术错误。冻结与封存输入绑定相同，当前输入 mtime 均早于冻结。源码静态顺序先写 freeze 再导入分类模块；上述时间属于本地记录。

00652 的 source_requests、material_requests 和 dependency_stop_reasons 均为空，原 substantive_list 误请求已从实际输出消失；协议 source_read_requirements_recorded=true。Ec/I 首判仍分别使用 current 的 payment/classification 路径，未加入来源关系使用。这些是程序状态事实，不认证语义必要性或判断正确。

01729 的关系模块先识别当前“国家药监局决定开展……”为 named_mechanism，记录同快照 SHA `ab19a319…8f81332` 和四段来源使用，均链接 READ-5。随后 dimensions.py 的纯宗旨分支让 _units 返回空列表，五项首判均为 0，basis_path=pure_document_enactment_purpose，context_evidence/needed_material 为空，候选与保留决定相同。关系模块承认“决定开展”，宗旨模块的制定句前内容模式未承认该行动；这就是本次记录的过宽路径差异。审查不读取参照来代判正确标签。

完整交付来源 bundle 与 v07 对应两范围逐字节相同。程序收据只证明记录了文字、结构和身份字段消费；可用库存、零协议错误或 scope=complete 不能证明语义正确或来源依赖真实必要。运行 image_read_N=0，字节哈希、转写文字和 geometry 不等于像素阅读。

总 seal 含评估文件绑定；本次只对其中七个文件作不解析内容的字节哈希，不读取参照文本、比较结果或 metrics，不计算性能。未执行/修改规则或测试，未改首判或旧封存。新 JSON、MD 与 seal 分别独立保存，完成后停止。
