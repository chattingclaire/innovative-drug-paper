# implementation05 有限修复与实际回归

说明书名词内部“说明”不再触发支付内容动作。真实“说明支付标准”以及直接“明确预算/费用”保留。改动仅限 `_payment_route_only` 和 `_economics` 的一个既有支付谓词门；其余函数、通用动作常量、evidence、relations和来源读取层不变。

| 单独开发域 | 整条一致 | 全维度一致 | 全维度F1 / κ | 执行错误 / 空值 |
|---|---:|---:|---:|---:|
| 旧41材料回归 | 41/41 | 205/205 | 1 / 1 | 0 / 0 |
| 36条开发比较 | 36/36 | 180/180 | 1 / 1 | 0 / 0 |

两组各真实执行一次，用同一冻结代码；各预测新seal后才由独立程序读取原参照评价与算术复算。旧41预测逐字节等v04/03；36只改变RECODE25-03818的Ec=1→0，其他179格不变。36的F全阴性，F1/κ仍为null，各维度完整分母与混淆矩阵保存在分别的metrics.json；未合并作正式效度。

同组四项必要名词/真实动作对照修前1通过、3失败，修后一次4通过；源测试字节和期待未改，修前代码/失败及最小scope追加声明均保留。未增加无关或递归toy。

旧v04回归428文件、首次36的532文件、旧41的81文件及两条共材实际技术失败329文件均保持封存原样。两条共材v04失败不能改成0或普通规则空值；本版未使用它们的新参照或A/B/native判断。旧41已知材料投影缺口依然存在，此表仅是旧材料下AI开发回归。

正式v12来源seal绑定已收到，将在本版完成后以另版来源复杂关系接口接入；当前没有声称全来源可执行。新接口必须保全textless geometry、reference closure、source role、例示和oldSUPP，只有有限适用关系可供判定，所有可用全文不作默认继承。暂不1444/4481推断。

精确复现：reproduction-before-runs.json。当前代码diff：payment-predicate-repair.patch。原4控制与修前/修后实际日志：payment-predicate-tests-before-run01.json、payment-predicate-tests-after-run01.json。全77条变更：v04-to-v05-all77-version-deltas.jsonl。
