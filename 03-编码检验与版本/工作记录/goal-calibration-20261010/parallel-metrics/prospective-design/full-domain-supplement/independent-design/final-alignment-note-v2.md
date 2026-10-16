# run03最终只读对齐附记v2

2026-10-10；GPT-6.1 Sol/ultra。上一轮final-alignment-note.md/json作为round01原样保留；本轮只新增v2，不改初审、原600/1444档或其他旧交付。run03日志状态为full_comparison_planning_only，stderr为空，18项版本/措辞检查通过；不重复952项数学检查，数学QA由母代理另行绑定。

两项小改动已只读确认：human κ显示六位小数，134/134合成边际例现显示0.799989，避免四位显示0.8000造成点值达标错觉；read_inputs新增prior600.projected_inputs_sha256与当前投影实际SHA相等守卫，同层计数相同也不能静默换pool。原600的投影SHA与实际冻结投影匹配；场景仍为90个机器/36个人合成例，不是实际标签。

分配JSON仍为a27b6f4228b11714c0f2b3c9ea0d3dc9ec55f9591708ac3d361f33f9b4831a57；原600 JSON仍为3a8e75bd83423d93b14907feec0ae13e76b76c433d35eec06eae936e8bbb75bb。N1444/n600保持，source-bindings所列五个原输入SHA全部匹配。

| 最终run03文件 | SHA256 |
|---|---|
| full_domain_plan.py | 4a744b6efa43eabe8c0dc4cc471347e88c158a6e76f999a7ea8b53fb4120099d |
| source-bindings.json | 3fb042dbc8be3520eacd6b7fac40a41ce84cd7dae3463770f209c04dd38cb889 |
| full-domain-comparison.md | 541c6a0260facca5ba5a58fda26fd2eb163e0a5a9b68afabe17f82b5cd79b350 |
| full-domain-comparison.json | d1a9c9d119628bce64aadec8906c046e23ef7cae1d7a5fa0b17ac5cc74823064 |

比较JSON、source-bindings与最终脚本绑定一致。完整报告继续明确：分配是预算启发式，开发域不是未见泛化；剩余域保留并分列；规划宽度不是实际主CI、覆盖保证或新门槛。仍未选择或执行800/1000方案，未抽ID、读正文/真实参照或运行新机器。详细布尔检查与round01保留SHA见[final-alignment-note-v2.json](final-alignment-note-v2.json)。
