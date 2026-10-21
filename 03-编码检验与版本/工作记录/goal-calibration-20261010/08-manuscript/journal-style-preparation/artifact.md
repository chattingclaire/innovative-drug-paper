# 科学决策样式底稿使用说明

本目录只准备可清空的组稿底稿；不读取统计或旧正文，不代表论文完成或 Goal 验收。

## 来源与复用

唯一版式来源为 `official-current-template.docx` 的逐字副本，原件：`/PROJECT_ROOT/outputs/goal-calibration-20261010/parallel-manuscript/evidence/official-current-template.docx`，SHA-256 `9d53ceb26f2f3b869edf09c4ce260af1ba1dd39971a543f21a565c3b8014a7e3`。官方文字规范优先于该文件遗留样式的默认值：例如中文题名样式内部为 22 pt，但规范明确为四号 14 pt；底稿按规范将使用角色校正。

`build_style_base.py` 默认写 `科学决策排版底稿.docx`，仅读取本目录官方副本，不读取研究结果。可指定 `--output /绝对路径/副本.docx`，默认拒绝覆盖；重建本底稿时显式加 `--replace`。正式组稿可复制 DOCX 后替换示例文字，也可复用脚本中的段落、三线表函数。两页展示中的手动分页可删除；章节序号由组稿者按实际结构维护。

## 页面与角色

保留原单节 A4 纵向页面（11906 × 16838 twips），四边 720 twips，单栏，页眉/页脚距离分别 851/992 twips；删除规范样稿的页眉横线、交替页码、示例作者脚注和首页差异行为。无页眉页脚、图像、文本框、域或内容控件。官方正常中文预览为 7 页，见 `template-reference-render-fonts/page-1.png` 至 `page-7.png`；首轮未载入中文字体的 5 页预览保留在 `template-reference-render/`，不可作字形验证依据。

全体文字黑色。Title 为黑体 14 pt 居中；英文题名 Times New Roman 14 pt 加粗居中。中文作者仿宋 12 pt，单位宋体 10.5 pt，均居中；英文作者和单位 Times New Roman 10.5 pt。中英文摘要、关键词 10.5 pt，左对齐、无首行缩进。正文宋体 12 pt、西文 Times New Roman，首行 2 字符、1.5 倍行距、段前后 0。一级标题黑体 12 pt；二至四级沿原角色黑体/楷体 10.5 pt，缩进 1 字符、编号后 1 汉字间隙，保持与下段同页。附录标题黑体 12 pt。参考文献宋体/Times New Roman 10.5 pt，首行顶格、续行悬挂 2 字符。

表格为按官方文字要求新增的三线表组件：无竖线/底色，顶底 1 pt、表头下 0.5 pt 黑线；10.5 pt 宋体，表头重复、行不拆分、自动行高；三列宽 2000/4053/4413 twips，单元格上下 70、左右 100 twips。题注 10.5 pt 居中、表注 10.5 pt 左排。表注中的对象、分母、口径、来源、权重、NA 是本项目的组稿要求，不误称全部为期刊规定。

## 编辑位置

`word/document.xml` 中每个可编辑段由 `KSJ_*` 书签定位；正文不含旧论文片段。

- `KSJ_title_zh/title_en`：题名；当前是底稿展示名称，正式组稿替换。
- `KSJ_author_zh/affiliation_zh/author_en/affiliation_en`：作者与单位空槽；匿名稿删除整段，署名稿仅填真实资料。
- `KSJ_abstract_zh/abstract_en/keywords_zh/keywords_en`：摘要与关键词占位；中文约 300 字、关键词 3–8 个，按真实论文填写，英文对应。
- `KSJ_classification/doi`：分类与出版字段；文章编号和 DOI 留空，不能自行生成。
- `KSJ_intro/heading2/heading3/heading4` 及各自文本：层级示例，可复制/删除；非既定论文结构。
- `KSJ_table_caption` 后唯一 `w:tbl`、`KSJ_table_note`：三线表及表注；全部单元格都明确为样式示例，不是结果。
- `KSJ_conclusion/appendix/appendix_text`：结语和附录；附录位于结语后、文献前。
- `KSJ_references/ref1/ref2`：书目格式槽，全部为占位符；只用实际核实并在正文引用的来源替换。

作者简介/基金未写入正文或脚注；有真实署名材料后，按官方首页脚注格式另加。无需的字段可删除，保留相关角色样式即可。

## 包保留和匿名处理

从官方包直接复制后定点替换 document、styles、settings、core/app 属性及相关关系/Content_Types；字体表、主题、编号定义逐字保留。其余未使用样式保留。删除原样稿 customXml、custom 属性、外部本机模板链接、嵌入 OLE、示例图像、示例脚注/尾注、页眉页脚及其关系，避免历史作者/软件资料或规范示例混入底稿。构建时逐字核验 preserve-only 部件，且检查源 SHA、单节几何、无外部关系和匿名属性。

## 预览字体说明

DOCX 实际指定宋体、黑体、仿宋（原低级标题角色另含楷体）及 Times New Roman。本机缺少对应宋体/黑体/仿宋文件；本目录 `render-fonts.conf` 请求 Songti SC/STHeiti 替代，仿宋无可用字体时回落 Songti SC。实际导出 PDF 的字体清单为 STSongti-SC-Regular、ArialUnicodeMS、TimesNewRomanPSMT、TimesNewRomanPS-BoldMT；不能把请求的 STHeiti 映射声称为实际已使用的字形。未安装字体或修改系统。PNG/PDF 用于检查可读性、字号和布局，不声称与 Windows 宋体/黑体/仿宋字形完全相同。最终投稿文档仍需在具备期刊指定字体的环境复核。

最终渲染共 2 页：`fidelity-qa/b_render/page-1.png` 和 `page-2.png`，已按原分辨率逐页查看。中英文可读，无缺字、文字重叠、表格截断或孤立标题；表题、表格与表注同页，三线表无竖线。参考/最终渲染差异均来自明确替换的内容槽和删除的官方说明；页面几何保持相同。源文件 SHA 未变；3 个 preserve-only 部件逐字相同，8 个指定部件编辑、29 个样稿部件移除。首次结构自检把子元素携带的命名空间序列化差异当成几何差异，后改为核对相同 pgSz/pgMar/cols 属性；尺寸未变，重建成功。最终 DOCX SHA-256：`3a6781cf2be5ecdb7682400e0ba8530a6d83918e691087e8dcc7820562f6b545`。

只使用 bundled Python 和 bundled LibreOffice，渲染命令需设置 `FONTCONFIG_FILE` 为本目录 `render-fonts.conf`。创建标记 create/count=1/docx 已在首次编制前成功一次。底稿无实际作者、基金、统计数值、有效书目记录或验收结论。

<details><summary>原包部件定位与保留核验</summary>

| 部件 | 原字节 | 原 SHA-256 | 处理 |
|---|---:|---|---|
| [Content_Types].xml | 3195 | 979c92da2be3319022668d7cc0bd7d0c7cfb585d81d0807812f47e9b53d8ade1 | 定点编辑 |
| _rels/.rels | 737 | 514e1846381cb6bcfff105a4b0a17d666cf0ed1f0c120bff73b82226ab7ed977 | 定点编辑 |
| customXml/_rels/item1.xml.rels | 296 | 80482f86e196171d66001e0e74d1900408a3aaf2463e54005d251b5f2db9a0b0 | 删除原样稿内容 |
| customXml/_rels/item2.xml.rels | 296 | 2a6aee4c8a9714223a3568077411a0c82d11b484b1c9ab93a19d50b99c57baa5 | 删除原样稿内容 |
| customXml/_rels/item3.xml.rels | 296 | 3aa4054f7f463c6d441102c960783aa7f937d6945a0a885b624a66aafaeedb6c | 删除原样稿内容 |
| customXml/_rels/item4.xml.rels | 296 | 3c0d4d955517fe8112c945b1e56f63d5bef3c0005ccb627e40acda432e1cdc1d | 删除原样稿内容 |
| customXml/_rels/item5.xml.rels | 296 | fb008609ada31cc4b1c5c2f6dec6dfab38b6b703004219064e3501b8292e7ff7 | 删除原样稿内容 |
| customXml/item1.xml | 150 | d181da3d9903b9d32004f0000ef200f026633381880a8ee219f63deadb329a54 | 删除原样稿内容 |
| customXml/item2.xml | 437 | 1f3870d104da2cd1ecd18f64cfedc40529c1aed7de6bee0e007c7ebd9ea65948 | 删除原样稿内容 |
| customXml/item3.xml | 289 | f3b453b1755b133356885f27dfd8d96ac1d03abab49d28b11a2960c34226ed8a | 删除原样稿内容 |
| customXml/item4.xml | 26517 | fc50572a27d64d0f0476920d653ac12e58ffb52918b037c8a5fba4bec070ef0a | 删除原样稿内容 |
| customXml/item5.xml | 7218 | eda853b8fc0a1e49f4d80b87e67a00ab8bd347aabab430a111fd87008638b116 | 删除原样稿内容 |
| customXml/itemProps1.xml | 236 | ba148a5cb6db529e016e964394a1b6e0e0b32d711624c38f85d9d44f2e3b7fed | 删除原样稿内容 |
| customXml/itemProps2.xml | 236 | a8b5f99dc7b1400f0449d98b5b6a4e6e5163bbf8fb4c6b3b6656737ea74ecfb5 | 删除原样稿内容 |
| customXml/itemProps3.xml | 236 | 223b7d6011837c768119a1abd4d5c9148d3e74beb65aad6578bbc8b6dcb0154f | 删除原样稿内容 |
| customXml/itemProps4.xml | 236 | 308f97fac2e3103b96751c93bdec7617ce34f81b1af3a46b165f0b28dd62673b | 删除原样稿内容 |
| customXml/itemProps5.xml | 236 | ca3ac3c5f4e693c682c00eccba6ddcf514f30d0b8540b9befd2a9e7d247197b5 | 删除原样稿内容 |
| docProps/app.xml | 689 | 8b7daef24a78530c63cdae7b0e8129fbebb42c9268141dfa7803e9c8ad1e5cd3 | 定点编辑 |
| docProps/core.xml | 683 | 68608782f85da1bfc28303131cf9654aa2224360d3f76a4851062e81ace365ec | 定点编辑 |
| docProps/custom.xml | 750 | 50902c73c1e6df04aff45a785cfc0d75989ca25672a3d790230705877c7c7035 | 删除原样稿内容 |
| word/_rels/document.xml.rels | 3126 | efa221af0141913b2bc4bb05202ffce598826c6a53ea7903be6f493ac149d10b | 定点编辑 |
| word/_rels/settings.xml.rels | 413 | 3f4affc9ca674103709a46364b0b67b2b73f3825cd42e039cc3818f7914a900e | 删除原样稿内容 |
| word/document.xml | 441872 | 6fe42fc56972dac5de3be9c8f9596c142d73dfb56d2de043ee4eb89a47f1351b | 定点编辑 |
| word/embeddings/oleObject1.bin | 3584 | 35c23568562c23c74b59677aa41f4e10fc4a5a6c5e77d3bd636e10763a006efc | 删除原样稿内容 |
| word/embeddings/oleObject2.bin | 3584 | 49b9e267e2ce9e3ba4346253b69b68596f816d88f97effa38684c0d63e3f9cc2 | 删除原样稿内容 |
| word/endnotes.xml | 1500 | 090089c8ae8cff8f71e3382fdd6f232091a25dc221d6a8331d78c16e1d9425b2 | 删除原样稿内容 |
| word/fontTable.xml | 4136 | 7fafa8913da7a0c440fec2ad8d2b56db63e04e2e1a293e788eb279117289f687 | 逐字保留 |
| word/footer1.xml | 1367 | 736c6c0b804e96615edfb6984dff2348d14288e19fa57e562b46b4892ddc4c35 | 删除原样稿内容 |
| word/footer2.xml | 1850 | 92aabf586236bdce5b03d012d0c1eefb71e5116d13a502ea216071b9fae6811f | 删除原样稿内容 |
| word/footer3.xml | 1367 | 2e09111d8e71b202b0b58132d1dddacd84f871ac64f944c5d068cf24b2d41423 | 删除原样稿内容 |
| word/footnotes.xml | 7326 | 736ef4d8cafe72ef3768a25d405f520f0c815a514e05cb66ba5146afbef5796c | 删除原样稿内容 |
| word/header1.xml | 3023 | a5831c2b1d18f37e57674e317856a713d6debb9ac6dd72b14dcb27dee74222d0 | 删除原样稿内容 |
| word/header2.xml | 1948 | 4ad4e69a77538db4cd7ca355fd5d830bf3a0443351b258670532de166c28514f | 删除原样稿内容 |
| word/media/image1.wmf | 834 | abde7df22c629233de09bc7afa50de165c5b66ae919218db0643cd5f8d4d1a07 | 删除原样稿内容 |
| word/media/image2.wmf | 862 | a3e730fa7a1db3c940b73d87f211e1c0917ddc2f3e76ce80c660dc42de2a142d | 删除原样稿内容 |
| word/media/image3.png | 1052 | 57501e65546db0b311e414ef5e5fe1f893bbecff4be062ca808cc782a033fc13 | 删除原样稿内容 |
| word/numbering.xml | 1578 | 5e522b709da71d8f8b676499f908249d76ac3d7da620a545cef883e34cc9d1cb | 逐字保留 |
| word/settings.xml | 31009 | 62051d66026adb3a63cd117629cdf20194b9d582f82d4354eb911fda6cafc729 | 定点编辑 |
| word/styles.xml | 67961 | 4433b9e2ef421c6c616f19bd53636614398e979ab3ba8d031ed39b31ba87d4b6 | 定点编辑 |
| word/theme/theme1.xml | 6444 | e51596e3c6197a87cad5351fe80a81ed8778271578eb3b635f8088d375f08f2d | 逐字保留 |

</details>
