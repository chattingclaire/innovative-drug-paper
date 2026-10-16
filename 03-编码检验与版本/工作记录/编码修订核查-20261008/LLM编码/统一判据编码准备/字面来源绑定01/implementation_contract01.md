# 字面来源绑定01 实现契约（编码前固定）

本模块提供确定性的单leaf只读绑定函数和仅构造自测CLI。没有真实全量读取、导出或模型入口，不消费标签、旧verification或编码意见。实现依据为根代理已审阅的`literal_source_binding_design01.json`；下列是首轮可执行范围，不声称完成全项目材料认证。

输入：非空leaf文本、record_id/raw_pointer、完整来源身份、完整candidate路径/SHA，以及明确candidate定位；可提供来源发生位置定位。输出只含散列、路径、JSON/XML/DOM/grid指针、字符/字节范围、页/行/bbox、工具身份和原因码，不序列化leaf或原文。候选正文仍是调用者输入，模块不更改。

来源优先成对使用unit_source/unit_source_sha256，其后source_path或source/source_sha256。任何显式不完整层都报unbound，不借父层补成员。候选文件必须通过实际SHA；其顶层或所选unit上必须存在与所选来源路径及SHA一致的显式来源关系。source_image及其SHA也为完整对；图像仅能认证字节，不能自动认证像素转录。

candidate_locator叶范围为unit、unit_subspan、paragraph或table_field。unit范围必须全文等于候选unit.text，并核unit唯一ID、paragraph_id关系、paragraph实际成员位置；重复subspan须明确起点。paragraph范围核唯一paragraph ID和字面subspan。请求中提供的pages/line IDs须与实际候选元数据一致。table_field另核候选native grid。表格整行只能以明确structured_table_row表示接受真实源格按` | `的确定性序列化，保留原grid指针，不称为自然原句。

TXT/MD：严格声明编码，精确字面匹配；可显式允许仅空白变化的可逆映射，绝不删标点或替换词。返回原字符、原字节及行范围。重复命中没有发生位置定位则unbound。

PDF：实际pdftotext -bbox-layout抽取，记录二进制/版本、抽取文本SHA、页/行/词bbox和可逆抽取字符位置。支持同页精确或显式空白归一匹配；拒绝无文本、歧义及跨页拼接。此为版面抽取文字位置，不声称法律款项完整或像素经人工核验。

DOC：实际textutil转UTF-8文字，记录工具、来源字节及抽取文字SHA、抽取字符/行位置。平面转换不支持原生表格定位或法律款划分。工具不存在或失败时明确unbound。

DOCX：读取ZIP中的word/document.xml，支持表格外原生w:p及w:t/tab/br顺序，保存XML段落指针和段内位置；初版不支持原生grid、合并格或其他package part。表格内文字不得作为普通段落绕过。

JSON：仅显式JSON string pointer、声明的native table grid，或完整source_html路径/SHA链。grid核原表题、列、行、格及候选grid的一致性；重复格保留行列。HTML链使用真实DOM p/td/th文字及节点位置，保留table ancestry；不把candidate行当成原生法律款。HTML实体解析留解码节点位置和源节点起点，不作跨块拼接。

PNG/JPEG等图像单源：可核实际字节身份，但没有独立已冻结区域转录时返回unbound；本任务不OCR、不以visually_checked替代像素核验。native JSON grid若链接图片，单列image_bytes_bound=true与visual_transcription_revalidated=false。

输出状态分为literal_source_and_candidate_position_bound、structured_grid_literal_bound_image_bytes_only_not_visual_revalidated、unbound_policy_leaf；同时分列candidate/source/native_structure/image_axes。工具、实现文件SHA及抽取trace SHA进入证据。异常原因只输出固定码/异常类型，避免异常消息泄露原文。

manifest不含自身SHA。先冻结含具体位置证据的manifest，再计算其文件SHA；另生成projector绑定map并引用该SHA。外部manifest身份不替代位置证据。初版仅提供manifest构建/派生纯函数，不自动写入真实数据。

将保存所有首次FAIL及后续修复记录。完成后停止修改交root独立复核；不自行冻结正式输入，不改07/02投影或规则候选。

## 根代理授权的显式来源关系补充

首轮元数据统计只检查candidate顶层及所选unit的source字段，不能据该统计断言没有其他显式关系。根代理随后确认874条所选unit_source均由candidate.additional_sources中的唯一path/sha256条目明确链接，实际文件SHA一致。本模块补支持这条原生显式列表关系：完整path/SHA、唯一精确路径、匹配SHA；缺半、错SHA、重复或冲突均不放行。保留原统计，另存补充覆盖统计；每个leaf仍需实际字面位置核验，列表关系本身不证明文字正确。

根代理另授权直接HTML来源入口，复用同一原生闭合p/td/th节点parser和SHA/位置契约；没有新增语义规则或跨块展开。直接HTML与JSON→HTML链在extraction中分别命名。
