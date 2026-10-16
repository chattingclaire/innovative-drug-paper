V11候选已冻结：仅补同条受保护原持有人资格与当前数据依赖许可限制的I4关系。创新对象是原创新/改良药品持有人；仿制/类似药申请人是受限相对方。临床优势语境不自动进入E。

第六条连续四段依次给出改良型持有人及4年保护期、境外上市分支、证明相较既有药品明显临床优势的新的临床试验数据范围及排除、当前未经同意依赖其数据不予许可及自行取数且未依赖例外。逐字引文和原SHA/JSON/HTML定位见设计、v16输入及实际role receipt；第三/第五条不能替代第六条。

纯gate仅当前“数据保护”或“受保护…数据”文字提名，绑定static_gate.py。新增producer的首个guard及新consumer调用使用同一入口。必须唯一匹配同版完整当前原段所在原条款，并核条首、连续原位置、当前末段及下一条边界。必要定义缺失时只新增typed私有I请求，explicit dimensions/affected_dimensions=['I']；旧requests/contexts/bundle/source扫描状态不改。完整普通数据对象不产新增I。语法与未解析额外分支保守保留旧路径，不改OBJECT/GAPS/旧helpers。

一次有限开发控制241例=原189+C12+E24+16新增；226硬断言225通过、1失败，15pending单列，不算硬通过。硬断言含3项guard-only控制，223项有硬标签期待。新v16 01402 I=1；原v15 01402 expected1原样，actual0→null，必要同条持有人定义缺失，仍是未满足项。原期待、输入、全部失败与pending保留。开发控制不是正式准确性验收。

241例S/E/Ec/F完整decision相同；207例gate-out五维相同；旧relations行、旧材料/来源requests与扫描events相同。实际五模块与唯一执行快照逐字同一；删新增定义/常量/导入/两个guarded调用后精确恢复combined-v2 AST，前三模块字节同一。旧_add仅追加新kind并重建trace，旧行不变；其余复用helper只读/局部写。0分类器文件IO、0模型、0生产。

静态selector覆盖入口内全部旧0/1/null全记录及完整依据链；任何新旧packet绑定变化亦强制选入。不按原标签或预测筛选。ROOT须绑定实际兼容基线、新旧完整manifest并独立审查；闭包无法证明则全4481 fallback。作者未执行总体selector。候选冻结不是采用或语义最终验收，后续由ROOT单独进行。
