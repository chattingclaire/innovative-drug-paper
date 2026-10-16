已仅应用用户明确的两项双方S改值：01423 0→1、04333 1→0。其余保存值保留；03415 E=1仍待真人核定，不作新gold。本目录是算术派生结果，不编辑XLSX、不改旧JSON。

六机器对照沿用metrics-addendum完整schema及原名；A_B_comparison沿用原最新A/B schema。四格、类别计数、差异ID、原NA和35项sklearn独立交叉核对保存在metrics.json。机器逐维10指标，A/B保留原5个一致性指标，A/B都不是truth。

| 比较 | 保存/分配 | S κ | E κ | Ec κ | I κ | F κ |
|---|---:|---:|---:|---:|---:|---:|
| rule17_complete77_vs_actual_latest_A | 77/77 | 0.802395 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |
| rule17_complete77_vs_actual_latest_B | 77/77 | 0.802395 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |
| native38_saved_complete_format_subset_vs_actual_latest_A | 38/77 | 0.842975 | 0.786517 | 1.000000 | 1.000000 | 1.000000 |
| native38_saved_complete_format_subset_vs_actual_latest_B | 38/77 | 0.842975 | 0.786517 | 1.000000 | 1.000000 | 1.000000 |
| partial7_saved_per_record_subset_vs_actual_latest_A | 7/16 | 0.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |
| partial7_saved_per_record_subset_vs_actual_latest_B | 7/16 | 0.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |
| A_B_latest_actual_development_composite77 | 77/77 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |

四格方向：机器为行、修改A/B表为列，TP=a、FP=b、FN=c、TN=d；specificity=TN/(FP+TN)，NPV=TN/(FN+TN)。A/B四格行=A、列=B。两项同步改值不改变A/B总体计数或一致性，但改写了对应逐记录内容。

只有机器S对照改变，其他四维结果与旧addendum一致。native38仍38/77、39条未完成；partial7仍7/16、9条未完成，不拼成77、不补0。概率区间按旧契约保持NA/不适用。所有剩余AI值、未决03415E和两个非盲真人修订均不能冒充独立77条真人gold。

sklearn 1.8.0使用实际标签向量，对30个机器维度的全部10metrics及5个A/B维度的5metrics独立复算；四格和值全部通过，退化分母仍用原NA理由。旧输入bytes/SHA在交付前逐文件复核保持一致。
