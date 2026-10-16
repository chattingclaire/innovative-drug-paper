已按用户指定的实际Agent修改A、B表分别复算六组机器指标。A/B最新保存值逐条相同，但仍分别绑定各自原提交；不复制ROOTv3裁定。

| 机器与实际表 | 保存/分配 | S κ | E κ | Ec κ | I κ | F κ |
|---|---:|---:|---:|---:|---:|---:|
| rule17_complete77_vs_actual_latest_A | 77/77 | 0.670659 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |
| rule17_complete77_vs_actual_latest_B | 77/77 | 0.670659 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |
| native38_saved_complete_format_subset_vs_actual_latest_A | 38/77 | 0.722628 | 0.786517 | 1.000000 | 1.000000 | 1.000000 |
| native38_saved_complete_format_subset_vs_actual_latest_B | 38/77 | 0.722628 | 0.786517 | 1.000000 | 1.000000 | 1.000000 |
| partial7_saved_per_record_subset_vs_actual_latest_A | 7/16 | 0.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |
| partial7_saved_per_record_subset_vs_actual_latest_B | 7/16 | 0.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |

四格、各指标方向与分母、P/R/F1、specificity、NPV、Po/Pe/Ppos/Pneg、类别/待定/失败/覆盖和真实分歧ID均保存在metrics-addendum.json。

κ=1表示当前两组可判标签完全一致且机会一致率未退化；不证明判断本身正确。常数一致Pe=1的κ为NA。原A/B开发κ=1不能替代真人执行或正式验证；不同source/manual修订链与历史AI身份保持原样。

native38仅38/77，partial7仅7/16，不拼成77、不补0。对ROOTv3的旧报告保留为历史附表；本补充才是按用户指定修改A/B表的机器主结果。开发非概率，既有CI契约不报总体区间。800独立A/B/可信参照尚无，classification仍NA。

existing sklearn 1.8.0单进程30项交叉复算全部通过，无新语义编码、模型运行或旧输出修改。
