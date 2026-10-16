v3 修复独立审查发现的具名文件宗旨误判。48 个构造案例、269 项检查全部通过；真实77/800/4481推断均为0。四项开发标签已披露，本交付是AI开发修复，非盲、非正式验证，不宣称准确率提高，也不以κ=1为目标。

原出版边界只识别“制定/印发/发布本或该文件”，使“为…制定具名程序”的纯宗旨落入安全目标正判。v3通用识别具名与书名号文件，先按当前完整命题划定宗旨，再保留独立风险问题、评价/监测要求、触发后果及实际安全检验标准。文件标题里的风险评价词不等于当前设置内容；具体制定药物风险评价/不良反应监测/安全性检验标准仍可S=1。原本/该边界保持，没有硬编码案例名、ID或文本hash。

修复前先验与手册第42/44/62/69/76行引文保存在publication-purpose-prior-expectations.json。attempt08在复制的v2代码上真实执行，46例263检查中259通过、4个宗旨失败；attempt09修复后全部通过。直接检验标准必要控制在attempt10出现1个真实失败并保留；补足当前药物安全标准内容关系后attempt11为48例269检查全通过。完整虚构输入、当前锚点、角色链、请求和read/use receipts均保留，不是实际政策运行。

相对v2只改dimensions的出版内容投影与明确安全标准分支，并同步driver候选3身份；relations和来源adapter未变，驱动非main辅助函数AST、精确资产/材料白名单、来源同版和坐标guard、首轮不可覆盖、单次实际运行护栏均保留。publication-purpose-repair.patch给出与封存v2的最小真实diff；actual-candidate.patch是对原request-routing候选的累计diff。v1、v2全部seal文件及21项旧输入字节复核未改变。

v2的I3/F独立门槛、操作性安全定义和同版实际评估价关系全部保留，四个原0根因及有限材料引文另见root-causes-and-chains.json/material-evidence.json。manualcandidate仍绑定实际SHA 7bb13ef1a5ad3d230abe5e786eb3dccd1ef4dfdc17a8f8ae4cbf2958d7229a65，未称ROOT正式冻结。共同来源v15在本任务未读或run。独立代理将只读v3 seal复跑固定37+6控制；本报告尚不宣称独立通过。ROOT完成来源、手册、代码对齐并另授权前，不运行真实77。
