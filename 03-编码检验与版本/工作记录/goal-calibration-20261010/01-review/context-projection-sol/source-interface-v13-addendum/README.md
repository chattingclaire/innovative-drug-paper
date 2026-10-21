此目录是v12的有限纯来源接口增补，按来源文档SHA `09d813b3014db4137d2bceab8bc280c396a5916fafa7bb4c216c5798ae824d06` 为同源59条记录增加第三条全文4段、第五条全文5段的可用原文库存，不按记录标签或得分选择材料。未改v12接口、原始4481记录、正文或27,534个旧CTX；01423原25CTX保持不变。

默认接口为 `/PROJECT_ROOT/outputs/goal-calibration-20261010/01-review/context-projection-sol/source-interface-v13-addendum/source_only_interface_v13.py`，Python调用 `lookup(record_id, selector='model')`，CLI调用 `python3 source_only_interface_v13.py model RECODE25-01423`。`rule`、`model`、`human`返回相同完整对象。`--inventory`提供可用资源定位/视图SHA，保留“未记录实际读入/使用”；`unit`与`--record-only`仍原样委托v12，属于不含全套增补库存的窄视图。

对增补文档，新增一个中性原文章节集合到 `explicit_or_primary_source_resources`，九段完整原文到 `source_full_text_resources`。所有旧根字段保留；仅这两个集合追加，以及新增 `source_bundle_extension`。原 `common_source_bundle_version` 的v12值保留，表示原核心版本；增补版本/来源SHA/旧bundle SHA另记在新根字段，完整新bundle SHA在 `frame-bundle-bindings.jsonl`。其他4422条整个默认对象与v12逐值、逐字节相同。

九段的原Unicode文字、JSON指针与HTML外段SHA已逐字核定。新primary HTML locator使用实际原文件bytes直接UTF8解码并保留CR/LF；原addendum坐标另作为provenance保留，它们匹配经过通用换行转换的文本视图，起止坐标较真实原文件字符坐标少11。未改原addendum，未虚构normalized char interval、PDF页码或像素定位。各原HTML `<p>`序号、行列、实际字符区间和可见文字均核过。JSON源、HTML源和既有JPG的绝对路径/原文件SHA列在registry与manifest，公共资源本身保留其实际JSON/HTML定位。

来源库可用、方法实际读入、方法实际使用仍分开；资源库存不代表全文件适用或任何维度成立。当前v12读取协议的原接口绑定未改，不宣称它已自动接受新增v13库存；ROOT后续绑定执行口径。没有读取标签/性能或进行新编码、来源外搜、真人/独立检验或正式联合冻结。

同一次纯对象扫描的输出：`source-interface-QA.json`、逐ID旧/新bundle SHA及bytes的 `frame-bundle-bindings.jsonl`、只含字段path/type/count的 `field-shape-counts.json`。字段路径以JSON Pointer表示，数组下标用 `*`；occurrence_N为所有出现次数，record_N为包含该路径的独立bundle数；没有输出正文词或判断标签。扫描覆盖全部4481，不把旧6+36的profile当全框。

实际bytes口径为sorted-key/compact/ensure_ascii=False JSON的UTF8，排除末尾LF。全框旧合计66,160,650，新合计69,477,394；每条受影响bundle增加56,216 bytes，受影响新范围64,152–84,609。最大单条244,587 bytes（RECODE25-00889）；不推测token容量。全框ID原顺序的UTF8/LF hash为 `c4ec6247ec8c07932a1463251943f66f60d983dcb2eda4e305fd18e76bc59771`。

59条实际完整增补bundle另存 `affected-common-source-bundles.jsonl`，无重新选样。可运行 `PYTHONDONTWRITEBYTECODE=1 python3 audit_integration.py` 复现这项有限机械核对；这是已知增补的原件/字节/shape检查，不是新增语义检验框架。有限工作已停止。
