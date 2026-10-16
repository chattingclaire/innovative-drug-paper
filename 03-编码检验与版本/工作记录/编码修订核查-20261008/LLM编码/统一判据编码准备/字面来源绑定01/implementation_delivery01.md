# 字面来源绑定01 交付

实现已停止修改，交root独立复核。主模块`literal_source_binder.py` SHA `6849a7db6a0d11d0d32a08a3c757e16935f980b49a4a9a4d9c38839c1f140ee6`；自测代码SHA `ca7d9eb8c0c2ca8deaa725ad0357f6027870b868617be3c76f67edc3653c8ffa`。本交付不是正式输入冻结或全量认证。

接口`bind_leaf`仅处理一个给定leaf及完整source/candidate身份和明确位置，不加载全量输入或人工参考标签，不调用LLM/规则。它实际核source/candidate文件SHA、唯一candidate unit/paragraph及成员位置、显式来源关系，再核来源文字的精确位置。输出只有散列、位置、路径、工具身份和原因码，未保存政策原文。CLI只提供`--self-test`。

支持TXT/MD严格解码、原字符/字节/行位置及显式可逆空白匹配；DOC实际textutil平面抽取；DOCX表格外word/document.xml原生段落；PDF实际pdftotext bbox同页文字和词坐标；直接HTML和JSON→HTML完整SHA链的闭合原生p/td/th节点；显式JSON string pointer和native JSON table grid。保留重复发生定位；缺定位的重复文字不自动选第一处。标点不删除，旧verification或visually_checked不作为证明。

native grid核真实源表题、列、行、格与candidate structured_tables以及所用unit/paragraph grid的一致性。整行只有明确`structured_table_row`才能按真实源格的` | `序列化绑定，状态明确称为结构表示，不称自然原句。`table_field`不能走非grid来源绕过候选文字位置。

图片只核实际字节；native JSON grid链接图片时分列`image_bytes_bound=true`、`visual_transcription_revalidated=false`。图片单源没有独立区域转录则unbound。本轮不OCR或视觉审阅。DOC原生格/法律款、DOCX合并格或表格文字、PDF跨页拼接/OCR/原生法律款、复杂HTML法律范围和其他package parts均未实施，不据未支持路径声称材料没有相关内容。

最终实际59/59构造检查通过，无工具缺失或跳过。所有来源为真实临时TXT、MD、CFB DOC、DOCX、PDF、HTML和native JSON文件；抽取/认证未mock。实际DOC生成器的输出CFB魔数已核；DOC和PDF用了真实工具。最终记录`constructed_execution_final_stopped01.json` SHA `1e4a666b8b9c2b9b8d53038be550ee8eebf91f5febb3d89ad29037d9f1236524`。工具及Python/标准库身份另见`runtime_tool_identity01.json`。

首次36项通过记录、随后3项契约FAIL、table_field范围绕过FAIL及临时fixture重名导致的1项失败全部保留。HTML缺闭合边界、representation任意形状、DOCX仅表格文字的unsupported诊断和table_field入口均按预存契约修复。fixture重名只修测试文件命名，不放松来源判据；详见`fixture_repair01.md`。构造计数不等于真实语料准确率或效度。

真实4924条仅做来源关系元数据核查。55份candidate实际SHA均与输入一致；首轮只查顶层/unit得到4050条直接匹配及874条未在这两层匹配，原记录保留。root随后实核874/874均唯一匹配`candidate.additional_sources[path,sha256]`，涉及33个candidate/source对，实际文件SHA相符。本模块已支持该显式列表关系，并补完整、缺半、错SHA、重复冲突及有身份无leaf等构造。补充统计合计4924/4924有显式候选—所选来源关系，但**真实leaf位置绑定数仍为0**。不再将874条称为缺少派生链；关系本身不证明任何文字leaf正确。root原证据SHA `978e47b09b6c60eec76ecb4fbe39f55305163cf406c21c5c7f0f00efdf6c578b`。

选定来源后缀为PDF3013、TXT1736、DOC68、JSON59、HTML25、PNG14、无后缀9。14PNG对应5个唯一文件，16字节头均为PNG；9无后缀对应1个ZIP容器。路径及识别元数据见`image_extensionless_header_metadata01.json`，没有读像素或正文。root另用系统file确认该ZIP是Word 2007+；本版按后缀分派，未加入明确format=docx的ZIP验证入口，该9条仍会unsupported。root可在整合时另存适配，不能仅改名或猜格式后声称本版已支持。

manifest工具先生成不含自身SHA的位置证据payload；冻结实际bytes后，另派生projector map引用其SHA，避免自hash循环。map保存candidate SHA和source/candidate具体位置证据；只有成功位置绑定结果能进入该payload。正式使用仍需root独立检查、来源快照/工具冻结、对实际leaf逐项运行并处理unbound。未真实全量绑定、导出、调用模型或改07/02/03候选。
