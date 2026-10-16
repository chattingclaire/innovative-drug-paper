# 独立开发判读操作说明

只读本目录材料包与指定共同手册；不要读取兄弟A/B目录、admin映射、旧标签或审查结论，不自行外部搜索。逐条按同一手册判断S/E/Ec/I/F；标0/1/null，并保存原文关系理由。材料有语境不代表全部继承；只引用实际用于当前命题的有限语境。不得为追求一致率改答案。

提交labels.jsonl：每行{"id":"D001","labels":{"S":0,"E":0,"Ec":0,"I":0,"F":0},"evidence":{"S":{"path":"excluded","current_quote":"原文","contexts_used":[],"reason":"理由"},"E":{...},"Ec":{...},"I":{...},"F":{...}},"material_requests":[]}。contexts_used每项{"context_id":"C001","quote":"连续原文","purpose":"补足何关系"}；每个1至少有当前锚点，I3/F具体路径在reason说明必要证据项。null的material_requests注明维度、缺失原文或规则冲突。0也说明最接近内容为何不成立。不得增加未提供的事实。

五维分别执行，不看其他编码员结果，不协商。完成后不覆盖labels.jsonl；新意见另存。另写submission.json记录实际模型、推理设置、开始/结束时间、输入文件SHA、记录数、任何访问范围偏离。身份为AI，用途为开发校准，非真人独立编码或总体效度检验。
