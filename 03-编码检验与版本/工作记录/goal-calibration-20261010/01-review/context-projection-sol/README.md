# pilot01纯来源语境修复

此目录只保存来源材料、投影器和核查，不读取A/B未封存提交，不加手册判断、类别提示或采样角色。旧目录和正在填写的初始包均未修改。只在双方首判封存后，统一同版补材/重判并保留旧首判，不能悄悄替换当前输入。

- `build_projection.py`：按pilot01私有map的frame_id读取41条，frame allowlist检查；源材料只读。保留原CTX编号，递归校验所有嵌套CTX引用。所有原始text/headers/title/row_cells/caption和结构原值保留；无text节点也保留。结构仅允许明确键和child_groups/row_cell_column_pairs的嵌套键；结果键递归扫描。
- `canonical_source_context.jsonl`：41条，280语境节点（252文本叶、28无text结构）。每条仅id/text/pages/contexts以及适用的原PDF页图附件；每context追加原件SHA及原始locator，不含旧标签/理由/预期类。
- `projection-audit.json`：0悬空、0禁结果键；280节点来源身份都可关联已核SHA快照。逐节点保存恢复方法、提取/视觉定位级别、原SHA和保留的未解决项。
- `source-visual-review.json`：AI对原PDF完整物理页5–6（印刷页2–3）的来源核对，9个不同文本/34次出现，含完整列举、跨页延续、或条件、例外和1.1/1.2边界。它不是真人编码或专家裁定。
- `source-assets/`：从本Goal源PDF快照直接渲染的两页，SHA绑定；`tmp/pdfs/`为本次渲染中间件。

运行：

```bash
python3 /Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/01-review/context-projection-sol/build_projection.py
```

源doc标识D2不是坏SHA：实际导出器算法为`D2- + sha256(json.dumps((original_path, source_sha256), ensure_ascii=False, sort_keys=True))[:20]`，已逐节点核对。UNBOUND文本叶来自早期不完整pair的可见投影，后续source-only sidecar已恢复完整path/SHA；该完整pair及文本SHA实际核对。无text容器只在关联子节点来源唯一时推导源身份；这属于结构来源关联，不冒称其自身有原文证据。

最终文本核查分级：48片段与原件提取文本精确一致，157片段只在NFKC/空白表示下相同；另外47未在纯文本提取中精确定位，其中34已通过完整原PDF页图核对，仍保留原表示。剩余13项明确待核，8项已有候选段落locator吻合；候选稿吻合不自动证明原件逐字认证完成。详情逐项保存在audit，不删必要材料、不中性化成0、不擅改原文。

此输出解决初始包丢失28无text节点和CTX悬空问题；不自动解决所需确指计划/其他文件的材料补充。根代理另保存的2024同版试点和NHC解释正文应按共同中性语境协议加入后另版本；不能倒灌2025试点条件，也不能把来源补材当预期标签。此版本可作为后一轮共同来源底稿，正式冻结仍需完成待核来源和所需补材。
