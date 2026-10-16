# 第五轮已声明原件补全投影

只为04589、04614补入此前已声明的同一版本原文，不改当前句、旧contexts、人工答案和旧输出。不运行分类。

原件：`00-baseline/source-files/d959108cdaaa3b46-NMPA-药品注册管理办法-2020-正文.txt`。读取自两条原输入的source_documents.snapshot，实际字节SHA与原声明一致：`d959108cdaaa3b46c8334c217619a42f14c4d83f17af0934502a08c5d62864be`。55,251字节，18,743个Unicode码点，436物理行。

交付：`semantic-overrides.json`，对象键为两条记录ID，值为semantic_unit。该文件是本轮独立候选输入，不写回旧生产输入。重建脚本为 `prepare_source_overrides.py`。

采用现有source_packet.semantic_unit构造器：先精确复现两条旧semantic_unit，再分别追加完整原文source_textleaf和按原件逐物理行生成的source_texts；按原始第X条标题及下一条/章/节边界，生成126条ordered_article_groups。全部原文同时提供，未只摘选有利条句。每条新增437个来源上下文，旧contexts保持完整前缀，所有旧来源origin不变。

| 必需条款 | 原文行范围（含条标题） | 完整正文物理行数 |
|---|---:|---:|
| 第五十九条 | 198–199 | 1 |
| 第六十条 | 200–201 | 1 |
| 第六十一条 | 202–205 | 3 |
| 第六十八条 | 225–232 | 7 |
| 第六十九条 | 233–234 | 1 |
| 第七十条 | 235–240 | 5 |
| 第九十六条 | 339–347 | 8 |

完整126条款还包含后续终止、例外和其他一般时限等原文；提供材料不表示当前分类应继承这些内容。是否属于当前操作的适用对象、条件、OR分支、例外或比较基准，仍由独立关系解析判断。

完整textleaf的text_utf8_sha256等于原件source_sha256，Unicode/字节区间覆盖整个文件。逐行source_texts保留原换行，给出原文行号、Unicode半开区间、UTF-8字节半开区间及文本SHA。条组保留条标题资源、顺序成员、下一结构边界资源，均可还原到全文。没有伪造HTML/JSON来源类型、页码或组件ID；原件与旧contexts没有显式组件信息，只能声称同一完整正文快照。

已验证：原件声明SHA和长度、严格UTF-8往返、每一条坐标切片及文本哈希、构造器旧输入精确复现、旧当前句/上下文/origins完全保留、来源清单与context ID唯一、所有新增derived pointer和evidence.context_anchor文字逐字相符。绑定结果在 `source-projection-bindings.json`，完整条款索引在 `source-projection-article-index.json`。

本次没有调用judge、没有读取人工标签或用分类结果选择原文。后续若在277条回归中使用这两个覆盖输入，须说明这两条增加了同版来源材料，不能把变化全称为同输入规则修复，也不能把候选回归当作新的独立验证。
