# 完整比较报告：最终只读对齐附记

2026-10-10；GPT-6.1 Sol/ultra。新增附记，不修改原600/1444档、独立初审或其他旧交付。本次仅核版本与报告措辞，不重复952项数学检查，不读正文、语境或真实参照，不运行机器或抽样。

对齐通过：full-domain-allocation.json仍为初审SHA a27b6f4228b11714c0f2b3c9ea0d3dc9ec55f9591708ac3d361f33f9b4831a57；原small-plan-comparison.json仍为3a8e75bd83423d93b14907feec0ae13e76b76c433d35eec06eae936e8bbb75bb。原remaining N1444/n600及23层未被替换。最终比较仍含90个机器共同参照合成场景及36个人A/B合成场景，未被包装成实际标签。

完整报告的关键限定明确：第22行称乘数分配为预算启发式，不保证精度最优或过线；第5行保留开发域身份、区分全域与剩余域，开发曝光记录不称未见泛化；第60行将线性化半宽限定为事前信息诊断，不称实际主bootstrap CI、精确覆盖保证或验收门槛；第54行说明未来实际主CI与域接口条件，未称已经实施；第116行保持原点值目标，未增CI下限或半宽线，也未事后选择200/400预算。

| 最终只读文件 | SHA256 |
|---|---|
| full_domain_plan.py | e38ad2358a5c8ecffbf9d24a607d71c9c0de346b8e732a19729db5cb55c03b53 |
| source-bindings.json | f1c20e1e5b6e56720b694bf9f202ba632376e6b9908a0fc294fd1216a365f6a8 |
| full-domain-comparison.md | a7a6b0fb779bb302cd585aefc58628a42d3418ba7a09960d3cc9d5aef435fb9e |
| full-domain-comparison.json | 1118ae88cd5b8b43345d60f0c77729c5a577e8beead3afe0a7f8b9d741e651fb |

source-bindings中脚本SHA与最终脚本一致，所列五个既有输入的实际SHA全部匹配；比较JSON内的脚本/分配表绑定也匹配。详细布尔检查和证据行号见[final-alignment-note.json](final-alignment-note.json)。这是方法规划交付对齐，当前两档仍未选择或执行，不产生真人验收完成或机器达标结论。
