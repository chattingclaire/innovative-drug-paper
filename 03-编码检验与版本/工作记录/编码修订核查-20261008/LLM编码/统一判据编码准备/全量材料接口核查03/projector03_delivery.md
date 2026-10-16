# projector03 有限边界修复交付

已另存03并停止修改源码，等待独立复核。02的独立报告、作者31项复现和新独立33项结果已先闭合；02原3项FAIL保留。03仅修改boundary完整性分支及版本号，未更改来源认证或正式就绪契约。

实现内容：

- 将 `boundary` 纳入已声明结构子项，使用既有投影规则逐字保留对象内title、definition、unit_text等原文leaf及段落位置；列表保留独立发生ID、顺序和父节点关系。
- 对 `boundary`、`next_boundary`、`next_structure` 的显式空对象、空列表、空白字符串和非法标量报告candidate_view问题。未把空值推断为“已确认没有后继边界”。
- 字符串边界有registry但文字/身份绑定未满足时，保留external_binding失败，并在不输出该边界的情况下另报candidate_view问题；不再称视图完整。

`projection03_boundary_design.json` 在修改前保存12项构造设计。复制02源码基线上先实际执行，4PASS、8FAIL，保存在 `projection03_boundary_before.json`。修复后12项全部通过，涵盖3类正常字符串边界、对象多原文字段、重复有序列表、空/非法值及错误证明。该组是本次实施者构造检查，不称独立复核。

另将02独立设计的33项fixture正文和预期原样回归，只适配目标projector路径/SHA；33项全部通过。原设计及首次3FAIL未修改，03结果另存 `regression_independent02/actual_independent02.json`。两组执行绑定的源码SHA均为 `63ed686b1b49a20fd74ded6e601c8ee51b60fe97e378bb8ef4444f0e6027a408`。原01/02含全部既有独立记录共30份文件与修改前散列一致。

源码差异见 `projector03_boundary_changes.diff`；完整代码、设计、执行、原文件保留散列见 `projector03_delivery.json`。03仅运行临时构造，不读取真实政策正文或答案，不导出全量，不调用模型或规则。临时文件和外部registry只用于接口检查，没有实际leaf认证。

view、身份元数据、外部manifest绑定、实际认证继续分开。`actual_source_authentication_verified` 与 `formal_model_input_ready` 仍固定false；正式输入accessor在全部构造中继续拒绝。表格当前行表示仍可逐字保留，但自然原句/真实grid/序列化证明尚未实现。未扩展复杂未知结构或自动判定空边界为合法终止标记；无法按既定字段投影的材料仍需明确契约。

交付后应由root或另一复核者检查，再决定后续机械候选导出及独立来源绑定工作；这45项（12新构造＋33旧独立回归）不构成编码效度或真实材料完整率。
