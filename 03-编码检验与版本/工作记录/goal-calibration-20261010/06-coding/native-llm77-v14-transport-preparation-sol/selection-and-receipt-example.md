# 仅示例，非实际 scope 或阅读收据

下列是前瞻调用及保存方法；未执行 actor、未判读、未生成有效 read/use receipt。实际文件/指针/身份只从本批新 frozen packet 和原 inventory 取，不照抄占位符。

1. 当前 BODY：定位 packet `/source_bundle/source_record/text`，`utf8_text`。scope 原 view 与 locator沿用BODY inventory；helper file-byte SHA取实际 packet文件SHA。CTX geometry：原 `/source_bundle/source_record/contexts/<实际j>/structure` 用 `canonical_json`。CTX text：取同一原CTX中仅实际存在的 `text,title,caption,headers,row_cells`，按 `json.dumps(...,ensure_ascii=False,sort_keys=True,separators=(',',':'))` 的 UTF8字节建唯一不可覆盖 carrier。核SHA必须等于原 inventory text view SHA；保存原field-to-pointer映射后用 `file_utf8`读全carrier。carrier/geometry不是pixels。

2. 额外公共原文叶的7字段描述示例（严格示例，不是已冻结v14索引，也不是必要性声明）：

```json
{
  "resource_id": "SOURCE-TEXT-980acf76a2fb9b9537e89e6c223462549e984b39e6b1d9a54443e2dadce37036-L0001-L0026",
  "source_sha256": "980acf76a2fb9b9537e89e6c223462549e984b39e6b1d9a54443e2dadce37036",
  "view": "text",
  "view_sha256": "89fb8392fea750438d4378e6f630035432c1e259f715faf00d3bcc8ad059ebb5",
  "scope_pointer": "/source_full_text_resources/<实际新冻结索引>/text",
  "locator": {"source_bundle_pointer": "/source_full_text_resources/<实际新冻结索引>/text"},
  "encoding": "utf8_text"
}
```

此叶 parent原SHA和text SHA已机械核；仅在真实追加对象及pointer绑定后可成为additional_view。原 raw line/byte locator 保存在源对象，不写成虚构PDF坐标。必要选择由actor实际scope决定，不因可用而全读全部全文或图片。

3. 一个真实工具调用只发一块，示例（未执行；引号保持完整绝对路径）：

```python
r = await tools.exec_command({
    'cmd': 'python3 <已核helper绝对路径> --file <已冻结packet绝对路径> --file-sha256 <实际file-byte-SHA> --pointer <实际原view文件pointer> --encoding utf8_text --start-byte <前一实际end_byte或0> --max-bytes 6000 --audit-log <唯一emission文件>',
    'max_output_tokens': 12000
})
text(r.output)
```

经 functions.exec 运行时同样在首行设 `// @exec: {"max_output_tokens":12000}`，每次只一块。CTX carrier或instruction/必要代码用file_utf8且不传pointer。输出 metadata SHA是原view SHA；输入 file_byte SHA、source parent SHA、bundle canonical SHA三者各自绑定。

4. 保存关系：helper emission文件（实际程序执行）→ actor独立delivery文件（实际可见工具返回、真event或原schema允许的实际local event、完整markers、范围、截断状态、本人读账）→ 原scope的view read_receipt。delivery连续覆盖[0,view_total_bytes)，每块完成且本人真读过后，才写 complete/recorded 的whole-view原收据；`actual_range_or_page`可记录整view范围和实际chunk-delivery文件。`event_id`未知为null，不制造provider ID；`local_event_id`对应实际创建的delivery记录而非把emission伪称工具返回。原receipt的17必填字段：receipt_id/run_id/reader/source_id/resource_id/source_sha256/view/view_sha256/scope_pointer/locator_read/delivery_status/read_attestation/tool_name/event_id/local_event_id/visible_return_bytes/actual_range_or_page（照原schema保存）。未知visible_return_bytes允许null；不以预期stdout长度代填实际可见值。只有实际用到本条结论才另保存同view use_receipt。

5. 原source-quote严格使用 source_id/source_bundle_sha256/bundle_pointer/quote/span，其中span是原Unicode连续区间；quote逐字匹配原string leaf。侧文件仅保存公共source证据，不伪造 innovation_support 的current/context，不绕首判schema必填。纯 optional-debug事件不是source-read收据；真正来源工具失败仍按原gate技术槽处理。示例不能填充实际scope、首判、人员/像素/模型声明。
