# 开发统计独立绑定

已确认的 rules-v36.2-development-bindings.json 只读取v36.2输出与冻结v14 A/C/T，正式v33统计保持原样。driver 在统计前后核对输入哈希；生成新目录，拒绝覆盖既有结果。

03模板未确认、输出/执行adapter为空，运行将失败。等03完整4924行、197批执行QA完成后，以新文件填入真实full_development_binding、technical_QA、run_plan、execution_summary、row_provenance各自路径和SHA；逐项确认首次有效实际attempt、所有失败保留、精确请求与实际runtime、无工具、逐行重建一致。验证后由root确认adapter，再另存新完整bindings，不能修改此已执行绑定。

第二次调用同一driver，新输出目录同时纳入rules-v36.2与LLM-candidate03，所有03区间重新从03标签计算。已有v36.2结果仍保留；不继承02区间或75条稳定性。独立验证/真人验证均保持false。模板自身不授权使用未完成结果。

调用格式：

```text
python3 statistics/run_development_complete_statistics_r3.py --bindings ABSOLUTE_BINDINGS_PATH --bindings-sha256 ACTUAL_SHA256 --out NEW_ABSOLUTE_OUTPUT_DIRECTORY
```
