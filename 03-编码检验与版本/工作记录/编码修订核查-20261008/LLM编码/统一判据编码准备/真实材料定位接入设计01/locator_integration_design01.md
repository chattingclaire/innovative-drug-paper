# 真实材料的逐leaf定位接入设计

本文件只设计接入流程并记录元数据盘点。尚未对真实4924条的任何leaf调用binder，也未产生模型输入视图、全量导出、规则结果或LLM结果。实际执行需等projector04独立复核、binder03独立复核及共同材料修订01交付闭合，由root明确授权后开始；不能以本设计替代这些条件。

## 本轮已核对的元数据

基线采用既有v14规则输入与LLM输入，二者各4924条、ID集合相同。规则输入SHA为 `fbee2777afe7e437ef1d2e0773e12a41ec3682914510f05f2dad2f31db7b6a6a`，LLM输入SHA为 `6829d554cf5514e49565c7c58c4ffdb6f7768f9999b0eea49f114db023c03763`。盘点只读取keys/types、ID关系、路径和计数，不输出政策文字值，不读取编码标签内容；新修订材料交付后应先重做元数据一致性核对，不能把v14计数直接称为新输入认证率。

- 55个候选JSON中，4924条current的unit_id全部唯一；4921条可连到唯一单paragraph_id。另3条不是此API支持的单段关系：01803有6个paragraph_ids，02883、02884使用table_id＋row且无单paragraph_id。其ID、路径和结构类型在metadata_inventory01.json中保留，不选首段充数。
- paragraph_context共4927个成员，全部声明paragraph_id，且其ID在对应候选JSON中唯一。这里核对的是ID存在性，尚未核对文字或源位置。
- 4663个非null heading与4776个非null preceding对象只有text＋pages，没有paragraph_id。不能凭页码或一个邻近段号生成来源认证。null heading/preceding不是缺失文字，不新增伪leaf。
- complete_following_list的102个容器只显式声明source_sha256而未声明path；其591个正文子项有完整source与candidate身份。必须先处理显式不完整来源层，不可因子项完整而抹掉父层问题，也不可自动用当前path补半对。
- 当前unit_type元数据包含58个normative_table_row、6个example_table_row和1个blank_example_table；64个unit具有cells，只有18个同时具备columns与table_title。55个候选中的structured_tables合计7项，只有3项具有title/columns/rows结构，另4项使用raw_cells/cells。它们需要不同接入契约，不能一律送进当前native JSON grid接口。
- 候选共12818个line对象，8889个含bbox，12731个含raw_text；这些是定位线索，不是已经与原PDF/原TXT重新认证的坐标。

来源显式关系沿用已存root补充盘点：原4050条top/unit关系，加874条additional_sources的唯一完整path/SHA关系。此关系证明候选指向该文件，尚未证明leaf文字或发生位置。详细计数及局限分别见metadata_inventory01.json、line_grid_metadata01.json和binder01中保留的来源关系补记。

## 接入顺序与身份契约

1. 先冻结共同材料修订01的两份输入、全部实际候选及来源身份，记录文件SHA、构造代码SHA、独立复核报告SHA和本设计SHA。输入的ID、当前文字、候选身份须逐项对应；该轮只做来源接入，不改标签或维度定义。
2. 只枚举projector声明的文字字段与结构子项。每个leaf用 `(record_id, raw_pointer)` 保留发生身份；同一句在多个语境字段重复出现，仍是多个发生位置，不能按文字哈希去重后丢掉结构。表格单格与数组中的同一格是同一来源发生的两种输出位置，按原接口additional_output_occurrence记录，不算新增分析单位。
3. 每个leaf分别确定完整source pair与candidate pair。就近层一旦显式出现任一成员，另一成员必须存在；不得跨层混配path与SHA。unit_source对优先于generic source对。source_image也必须完整成对；图像字节与转录验证分轴记录。
4. 对102个hash-only清单容器等缺半对，另建中性派生身份表：明确原raw_pointer、原hash、唯一完整关系的出处指针、候选身份及实际文件SHA核对结果。只有唯一、可复核的同一来源关系才能作为待授权材料适配修订的依据；无唯一关系就保持unbound。原输入不改，也不能在projector中静默继承父pair规避问题。
5. 先核candidate的实际位置，再核source的实际位置。candidate ID匹配不等于原文存在；原文某处出现同一字符串也不等于候选单位指向那次发生。两侧均需位置证据，重复发生不能默认取第一次。
6. 每项结果只保存文字SHA/长度、完整身份、位置、工具/代码身份、匹配方式、失败原因及结构关系，不把旧verification、判定意见或标签当证据。失败保持原值和原因，按原因汇总，随后才决定是否需要有限适配扩展。

## 各类leaf如何确定candidate位置

| leaf类型 | candidate位置契约 | 必须保持的边界 |
| --- | --- | --- |
| 当前unit | 规则输入的unit_id→唯一unit_candidates条目；其paragraph_id→唯一paragraphs条目；当前text须与unit.text相同，unit在paragraph内有唯一原字面span或明确已核对offset。使用leaf_scope=unit，unit_id与paragraph_id配对。 | 不把current_unit_id当作所有语境leaf的unit_id。3个非单段关系当前unsupported，不选首段；表格行另走结构表示。 |
| 整段或段内片段 | 使用该语境自己的paragraph_id及候选身份；leaf_scope=paragraph，整段从0开始，片段需唯一字面span，重复片段要实际leaf_start。supplied pages/source_lines须与该段的实际候选元数据一致。 | 文本、ID或位置不一致就报告；不能删掉不合的locator只为提高通过数。 |
| 最近标题 | 已声明ID时直接核对；只有text＋pages时，后续在同候选、同来源/组件中按实际文字与页/线/顺序定位，要求唯一候选发生，且源位置独立通过。候选heading_candidate类型仅作结构线索。 | 本轮未执行文字匹配。标题不存在于paragraphs而只在lines/heading_context_candidates中时，当前candidate API不支持；需另存辅助位置契约和构造复核，不能伪造paragraph。filename/source_title不补标题。 |
| 前一段 | 先从当前unit的真实段关系限定同一来源/组件，再核对候选实际段序与原字面、页/线位置。只存在text＋pages时须唯一发生，且实际source邻接关系另留证据。 | 不能仅靠“在候选数组中前一项”断定源文邻接；不同组件、被排除的行、标题及跨页关系都可能影响位置。 |
| 引用条文/定义 | 使用每条reference自己的source/candidate对、paragraph_id和reference_address；各段逐leaf调用。next_paragraph_text须配其next_paragraph_id，next_candidate_paragraph_text须配其next_candidate_paragraph_id，不借父段ID。 | current_unit_id是关联到当前问题的标识，不是引用条文的发生位置；外部条文不能沿用当前candidate。引用地址和完整款项范围仍须独立结构核对。 |
| 完整清单 | 标题、父命题、每个成员、实际终止边界分别绑定自己的段/单元/原行位置；保留列表序号、父子关系、原始raw_pointer及各发生ID。 | “所有段已包括”等旧bool不是完整性证明；成员字面都存在也不自动证明清单完整。完整区间必须由同源、同组件的实际段/行/HTML节点顺序及前后边界另行核对。 |
| 表题/表头/单格 | native JSON grid使用明确source table_index、candidate table_index；表头加column_index，单格再加row_index。必须检查真实source grid与candidate structured_tables的title/columns/rows一致；关联unit/paragraph的cells、columns、table_title也一致。 | 重复表题、行或格值不能按第一次命中选位置。只有table_id/row或raw_cells的其他结构尚未接入，不自动改名成同一grid。 |
| 当前表格行表示 | 明确representation=structured_table_row，leaf_scope=unit；source_locator为grid_part=row及实际表/行号。由已认证实际cells按固定` | `序列化后逐字等于current unit，unit与paragraph同时关联到该grid行。 | 名称写“表格行结构表示”，不冒称自然原句。空格位保留；空cell不是可引用政策leaf。当前契约不是通用CSV转义/合并格协议。一般certificate.text拼接表题、说明和列名不因此获准。 |

含表格数组的已知certificate中的拼接text按既有projector契约排除；实际raw cell/header/title另作leaf。不能因为字段位于verified_context_certificates就排除其中全部正文：其中也有实际政策段落，须逐leaf确定来源；同样不能因名为text就自动认作原句。

## source位置如何产生

| 实际来源 | 可传给binder的source locator | 位置证据与失败处理 |
| --- | --- | --- |
| TXT/MD | char_start或明确occurrence_index | 严格声明编码及原文件SHA；保留原字符/字节/行span。候选line_id只有映射到真实原行后才可用于求offset；重复文字的页/行证据不足时unbound，不能取全源首个命中。 |
| DOC | 转换结果内明确char_start/occurrence_index | 记录实际textutil工具身份、命令和抽取文本SHA。只称转换抽取span，不把转换换行当native段落、原生单格或法条款项。 |
| DOCX及明确无后缀DOCX | xml_paragraph_index，必要时原生段内char_start | 实际ZIP与主文档结构核对、原生XML段指针及段内字面span；不得吸入表格、文本框或嵌套段内容。binder03需先独立通过。其他package part、native表格及合并格暂unsupported。 |
| PDF | page_one_based加明确原抽取char_start/occurrence_index | 实际pdftotext bbox输出、工具身份、页/词/行bbox与抽取span；候选bbox/line_id只能经真实抽取对应后成为证据。当前单页契约不能证明跨页拼段或删页眉后的重建原句。 |
| HTML或JSON→HTML链 | html_node_path，必要时节点内char_start | source_html对与实际文件SHA、关闭明确的native p/td/th节点位置、节点内span。保留表格祖先与节点顺序；不能把PDF候选段当native法条款项。 |
| native JSON标量/表格 | json_pointer，或grid_part/table_index/row_index/column_index | 标量限定真实字符串指针；grid按真实行列与候选关系核对。若来源JSON另有source_image，其字节验证与像素转录是两项证据。 |
| PNG/JPEG等图像 | 当前binder不消费像素转录 | 字节SHA只证明文件身份。独立转录报告存在不等于binder已消费该报告；须另有冻结的图像/区域/转录leaf位置与候选身份契约、构造与独立检查，授权后才能接入。 |

仅允许原字面匹配，或明确记录原位置索引映射的whitespace-only匹配。标点删除、NFKC全源归一后contains、凭文件名补标题、旧verification=true、共享判定意见均不是来源位置证据。候选中的normalized_pdf_body_span、original_text_span、bbox等只作为待核线索，不能直接当真实源offset。

## 暂未支持与执行后的原因计数

以下分支先保持unbound/unsupported；本设计没有对其真实leaf数量作推定：多段unit/paragraph序列；PDF跨页拼接、复杂版式或删行重建；不能唯一定位的标题/preceding/引用；只有原生表格行而无受支持grid关系；DOCX原生表格/合并格/其他part；图像像素转录消费；一般合成certificate；标点或其他非空白文字差异。

首次授权运行应按“记录数、leaf发生数、来源格式、材料类别、明确原因”分别报告。已绑定、unbound、unsupported、excluded_assembled及blank-cell位置分开，分母写清楚；不同语境的同文发生不能当新独立样本。只有真实执行后才能给出通过/失败数量及覆盖率，不能把本轮4924个唯一unit ID称为4924条认证通过。

后续扩展须由实际原因触发：先保存失败与有限适配契约、构造设计，再实现和独立复核；不为消除失败而放宽已冻结字面/位置要求，不无限扩展边界。通过项生成无自hash循环的冻结manifest，之后另存projector所需的绑定map；candidate视图、外部manifest绑定、实际认证和正式输入就绪继续分轴。即使manifest全部绑定，projector04正式accessor仍拒绝，正式模型包及授权还需root另行处理。
