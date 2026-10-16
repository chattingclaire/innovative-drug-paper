# 全4481增补审计规划交付

本目录是未选择、未实施的两档事前设计：剩余1444原n600不变，开发曝光3037新增n200或n400，全域n800或n1000。主报告为 `full-domain-comparison.md`；41层及精确概率为 `full-domain-allocation.json`，全部合成场景为 `full-domain-comparison.json`。

只读已有白名单投影 `../inputs/metadata-and-fixed-labels.jsonl`、原剩余600方法分配及源绑定。程序检查投影SHA同时与源绑定和原600记录一致，防止保持相同N却偷换pool。输出全框归层hash，不输出抽样名单；固定辅助标签不是实际参照或新机器结果。

在项目根目录复现（仅覆盖本新目录的规划产物）：

```sh
outputs/goal-calibration-20261010/parallel-metrics/.venv/bin/python \
  outputs/goal-calibration-20261010/parallel-metrics/prospective-design/full-domain-supplement/full_domain_plan.py

outputs/goal-calibration-20261010/parallel-metrics/.venv/bin/python \
  outputs/goal-calibration-20261010/parallel-metrics/prospective-design/full-domain-supplement/verify_full_domain_plan.py
```

已有环境：Python 3.14.4、NumPy 2.4.2、SciPy 1.17.1；未安装依赖。`full-domain-QA.json`记录当前代码、输入、输出和环境；`delivery-manifest.json`逐文件绑定SHA与字节数，重算任何产物后应重新核验清单。`independent-design/`、`independent-math/`、`independent-risk/`保留各阶段独立核查及只读输入哈希，阶段附记不改写初审。

开发曝光域仍是开发曝光。全域性能与剩余域性能分别从加权四格求值，不能平均κ/P/R/F1；未知与失败保留原权重。规划半宽不是实际CI。若未来选此方案，先冻结最终样本量、每层分配、抽样seed、名单与材料/方法/真实身份，再将固定stratum.domain映射接入同一份共同重复权重的全域/剩余域/开发域输出；本次不执行这些步骤。

没有新增census、CI下界或半宽门槛，也没有点值达标保证。不能看200档分数后决定切换400档。报告中的合成参照都是聚合整数计数，未赋给真实ID。脚本、QA、独立复核和本说明全部新增于本目录，原剩余600/1444交付保持。
