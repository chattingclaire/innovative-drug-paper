# 第六轮必要原文投影

已生成 `semantic-overrides.json`，共6条：第五轮04589、04614逐对象原样保留；新增01383、03423、04067、03919。仅增补已声明同版原材料，没有分类、读取人工答案或改标签。未复制或修改任何code文件；使用第五轮现有source_packet构造器。

文件SHA-256：`99dd419850d6b11b9b59c6295028c1da4dcf73dbc31b59dc106ba9030f46ad64`。逐条增补前后SHA、原件绑定、构造器SHA及保留检查见 `source-projection-bindings.json`；可由 `prepare_source_overrides.py`重建。

## 01383：JSON/HTML的公告、附件及附表

原JSON实际SHA为09d813b3…；其声明的原HTML实际SHA为e0e9f205…，两者均验证文件字节。原JSON的全部4段公告、32段规范、3张附表均保留。附表图像3个实际文件也与原JSON声明SHA相符；空单元格仍为空，不改成0或补写内容。

新增完整资源位于 `source_bundle.explicit_or_primary_source_resources[1]`：

- `source_texts`：公告和规范逐段原字符串、附件连接的HTML原可见文字，以及全部非空表格单元格原字符串。每个段落对应JSON pointer和原HTML的p元素范围/片段SHA；HTML内容对照仅去空白检查，输出仍保留原JSON全角空格及标点。
- `ordered_announcement_resource_ids`：4段原公告次序；第0段是明确简称定义，第3段是当前完整所在段（保留当前句后的受理/批准限制）。
- `ordered_normative_resource_ids`及`ordered_article_groups`：32段规范的原次序、15个原条号及完整款段，不只取第三、第五条。
- `attachment_connection_resource_ids`：原HTML“附件：药品试验数据保护实施办法”和规范标题“药品试验数据保护实施办法”两段真实连接文字。locator同时指出原JSON `excluded_metadata`中的相应位置，没有因字段叫excluded就丢弃附件证据。
- `original_tables`及`original_excluded_metadata`：完整保留原JSON的3个附表对象、列名、行、组别、备注、例外、图像来源及原附属文字。

旧资源仍完整保留，第三/第五条既有成员以相同ID和对象内容复用；完整资源的这两个条组与旧局部资源是同一物理来源别名，后续解析应按原SHA+JSON位置或成员ID去重，不误作两个独立规范，也不能因为有同SHA就跨公告与附件泛继承。

`source_full_text_resources[9]`和`[10]`另提供完整原JSON、完整原HTML严格UTF-8 textleaf。两个源文件各有自己的SHA，不能把HTML SHA当成JSON主SHA。没有虚构component_id，附件连接靠上述实际文字、原文次序及定位核实。

## 04067：原UTF-8正文与完整第42条

同版原件dbddfca4…字节SHA核验通过。完整原件textleaf位于 `source_full_text_resources[0]`，同一SHA的逐物理行资源和54个原条组位于 `explicit_or_primary_source_resources[0]`。每个行资源保存严格原文、行号、Unicode半开区间、UTF-8字节半开区间和文字SHA。

第42条保留第205—216行（总领、五项及原空行），第43条从第217行开始，`next_boundary_source_resource_id`指向该真实边界。原条标题与首句写在同一行，因此条组第一成员保留标题和首句，不伪拆标题或人为制造编号。全文及其他条款一起保留，没有只取参与者安全分支，数据可靠性等并列内容未删。

## 03423：完整PDF页面及六项范围

PDF原文件SHA为462725c5…，按已声明文件读取。依PDF技能重新渲染并视觉核对物理页5、6、7（印刷页2、3、4）；三页原文清楚，完整六项以及“因此”总结、下一小节均可定位，没有待补缺口。核查图保存在 `source-review/`。

`source_full_text_resources[0]`的`paragraphs`含三张完整物理页的PyMuPDF原提取文字，包括原换行及印刷页码；每页有PDF文件SHA、物理页码、页面尺寸、提取版本和独立文本SHA。文字SHA不是PDF文件SHA。

同一资源的`bounded_unordered_list`仅给出字面索引：当前总领所在页、原始引导语“这些特征包括但不限于以下几个方面：”、六个原小标题及成员页内半开区间、真实页次序、“因此”总结开头和下一小节标题。未把无编号清单伪造成编号条款。认知、感官、运动、其他生理和病理生理学、多病共存和多重用药、心理和社会因素六项全部保留；第7页完整总结也保留，未仅拼接含安全或药效的句子。

## 03919：同一PDF的公告及完整问答附件

只补当前主来源4c8ec1df…PDF物理页1、12、13。实际文件SHA与声明一致，三页重新渲染视觉核对，题名、附件关系、六个问题及全部回答均清楚。第12—13页是完整附件2，文档亦于第13页结束。

新增 `source_full_text_resources[0]` 包含三页完整原提取文字、PDF文件SHA、页码、页面尺寸、提取器版本及独立文本SHA；`annex_literal_index`提供第1页原公告附件2题名、第12页“附件2”与完整标题、六个问题的原页内标题区间，以及第13页文档闭合边界。第13页问题五的主体责任、参与者保护、流程管理三段和下一问题都保留，没有只取安全词或严重不良事件一句。

对象来源来自同一PDF第1页和第12页的真实完整题名及正文。旧包中另一SHA的TXT第二条虽保持原样，没有借它生成本次新增对象材料；后续解析仍须自行证明本句与同附件语境的直接承接。03526未新增。

## 保留与结构核验

对4条旧输入先由原source_packet精确复现，再生成新增资源。由于构造器会把新primary资源排列到既有full资源之前，投影最后做稳定排列：按原contexts顺序保留原对象与原origin，新增ID追加在末尾。所有旧context对象内容与构造器新结果逐项相等；保留旧origin仍指向完全未改的原资源。

当前句、source_ref、source_record、旧contexts前缀及旧origins均未改。新增来源指针逐一回读原bundle，文字逐字一致；全部非空新增上下文可生成并核对原文锚点；来源inventory与context ID均唯一。第五轮两条逐对象相等。未虚构组件ID、页码、法律条件或语义标签。

这四条后续若使用补全输入，须单列材料补全影响并保留同代码旧输入对照。来源可用不等于标签应为1，也不表示规则已经消费这些资源。
