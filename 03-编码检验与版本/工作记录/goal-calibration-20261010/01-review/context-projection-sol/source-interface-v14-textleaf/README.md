# v14原正文字符串叶共同材料

本版包装sealed v13，仅按主来源SHA980acf76…为142条记录在source_full_text_resources末尾追加已封存5个原UTF8文本resource对象。原正文、全部27,534个CTX、所有旧root字段和旧数组前缀逐值保留；其余4,339条完整bundle canonical UTF8字节保持原样。旧bundle中的版本字段也保留，新材料版本在外层manifest、逐ID绑定和本交付seal记录。

全frame共4,481条。bundle正文UTF8总量由69,477,394增至74,435,608字节（不含JSONL行尾）；实际frame JSONL为74,440,089字节。最大单条244,587字节，RECODE25-00889。每个受影响bundle增加34,917字节。逐ID旧/新SHA及bytes在frame-bundle-bindings-v14.jsonl。该scan只作来源机械值/byte核验，无语义编码。

77开发包保持原连续ID顺序，实际JSONL2,510,439字节。10条变化：00005、00036、00038、00045、00086、00099、00110、00118、00131、00138（均RECODE25前缀）。前9条位于历史batch-0001，00138位于历史batch-0005；这是历史分组映射，不是新派发。67条bundle字节与v13相同。

实际v14 rule/model/human调用仅00045、另一个同源00004、非同源00001三条×三角色，共9次，结果字节相同。未执行4481×3角色检查。全frame机械重构沿原v13实现，源文件/列表仅在审计进程内缓存；9次角色调用前已恢复原函数。新增资源库存记录available，consumer_read/use仍not_recorded；接口调用和SHA校验不冒充规则或LLM读入/使用来源。

5个原文resource按连续完整物理行保存全部原28,076字节，原Unicode、LF和0基半开码点/UTF8字节坐标不变。它们真实的source_resource_id/source_sha256可供七字段additional view绑定；source-textleaf-contract-check.json记录00045五叶实际沿既有原引用校验函数通过，未运行旧套件。人、规则、模型默认调用返回完整共同bundle。

原所援技术指南版本unknown保持；本轮original July DOC新核false。未新增PDF页码或图像声明，未读标签/参照/性能，未运行规则或LLM编码。共同手册/规则/提示/抽样的正式联合freeze尚未执行。
