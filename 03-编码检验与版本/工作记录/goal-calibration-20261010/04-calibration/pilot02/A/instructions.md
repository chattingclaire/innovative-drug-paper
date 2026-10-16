# 开发补材后独立重判说明

本批41条来自已完成开发首判的同一组记录，材料与手册已版本化修复。两位分别判断同一共同手册/来源，不看另一位结果；本轮是补材后的开发重判，不能称为未曝光最终检验。可以保留自己的既有认识，但不得把旧标签当新依据，不读取旧提交/讨论或admin文件。

只读本目录packet.jsonl、manual.md、instructions.md、source-pages中的附件。不要读取兄弟目录、主目录其他审查、预测/旧答案；不自行搜索外部资料。逐条判断S/E/Ec/I/F为0/1/null。当前和语境关系须直接，不把新补材全部内容继承给当前。CTX编号保留原值；SUP是新增连续原文。没有text的结构节点必须保留并沿其相关CTX阅读。

含source_page_attachments的记录，应实际查看所附完整页，确认图表分支/共同谓词/跨页关系。源文本与图有冲突时以原图核明，记录具体差异，不静默更改材料。

每行labels.jsonl格式：{"id":"P2A001","labels":{"S":0,"E":0,"Ec":0,"I":0,"F":0},"evidence":{"S":{"path":"excluded","current_quote":"当前连续原文","contexts_used":[],"image_sources_used":[],"reason":"原文关系理由"},"E":{...},"Ec":{...},"I":{...},"F":{...}},"material_requests":[]}。
contexts_used每项为{"context_id":"CTX-...或SUP-...","quote":"该节点连续原文","purpose":"实际补足的关系"}；image_sources_used为实际查看附件的attachment_id数组。每个1保存当前连续原文锚点，I3/F具体路径说明所需证据项；0说明最接近内容为何不足。null登记维度与具体材料缺失/规则冲突，不将未知填0。

分别完成后封存labels.jsonl，不覆盖；写submission.json，记录身份AI、实际模型/推理设置、起止时间、输入及全部使用图片SHA、记录数、输入范围偏离和实际查看附件清单。不得协商、按一致率改值，不得称为真人执行或指标验收完成。新意见另存。
