# 真人盲包接入核定：600域与full800

当前设计和候选集可以沿用，但**现有CLI不能直接一次抽样并生成保留完整v14材料的真实A/B盲包**。无需先等最终机器验证分数；仍须完成实际联合冻结、一次抽ID入口、v14真人包适配和真实A/B分配。本次没有抽样、编码、造人或改旧文件。

ROOT目前倾向的full800是已有方案：剩余1444抽600（23层）＋曝光3037抽200（18层），共41层。部门n=药监384、医保340、卫健76；其中剩余312/237/51，曝光72/103/25。所有4481单位pi>0，最小pi=0.034921；w=N_h/n_h。600本身给曝光3037的pi=0，不能外推全框。

600的既有依据是全取141个旧I/F辅助阳性与102个其他维分歧，抽取其他共同阳性和241个全阴性；三部门均覆盖。精度依据为原90个合法聚合情景、36个人κ情景及稀少/零格风险，不是实际性能或窄CI保证。曝光200沿用18个优先类别层及既有预算分配，补全全框正概率；不重设n，不看分数切换1000，不加CI门槛。两个域、三部门和ALL必须分别报告，以同一W投影后从加权四格求指标。

本次实际核查：600规划42成员＋manifest（43文件）、全域增补43成员及真人workflow39成员的SHA/bytes全部相符。v14的4481 ID集与许可元数据相同，3037排除集／1444剩余集完全相同；41层N和归层hash `2570735a88a20669025a661d35cb2516356a3be190ee157ea5b1d546177b6109`不变。77个开发ID全部在3037中。当前v14 frame74440089B已另核文件SHA；本次不读取候选正文作语义判断、不重做全库QA。

真正待办如下：

1. **实际联合冻结。** 手册v1.3 SHA `a5ced25d0960efce2a72437551854db6f7923569ba060a53feceaf7905cbd92f`，42941B，但正文明确“开发校准版、尚未冻结”。旧full800候选的final_selected/actual_seed_selected/actual_draw均false。ROOT指定抽样seed20261010，应在真实执行freeze里与方案、RNG/层与ID顺序、source/manual/规则/LLM protocol/统计hash一起绑定；与同数的bootstrap seed用途分开。不能只把manual_status改frozen。00064所援版本未知和原DOC新核false保留，不为抽样外搜或回填。
2. **一次抽ID入口。** [small_plan.py](/PROJECT_ROOT/outputs/goal-calibration-20261010/parallel-metrics/prospective-design/small_plan.py)和[full_domain_plan.py](/PROJECT_ROOT/outputs/goal-calibration-20261010/parallel-metrics/prospective-design/full-domain-supplement/full_domain_plan.py)只生成分配／精度，不抽实际ID。v14 lookup的selector是rule/model/human角色名称。唯一已检出的[select_development_coverage.py](/PROJECT_ROOT/outputs/goal-calibration-20261010/scripts/select_development_coverage.py)只选已有曝光36条开发材料，不能冒作概率holdout selector。没有可诚实提供的现成`draw full800 --seed`命令；可复用既有unit_stratum与full800.strata完成最小一次抽取接入，旧规划无需重算。
3. **完整v14材料接入真人workflow。** [workflow.py](/PROJECT_ROOT/outputs/goal-calibration-20261010/05-validation/human-workflow-sol/workflow.py)严格接收旧neutral-source-draft-1八字段记录；v14为十根完整bundle，source_ref/原JSON与HTML定位、TXT/JSON/HTML原件、公共text资源不符合旧白名单／mime／neutral五字段投影。必须有限适配并保留所有原资源、CTX、geometry、SUPP、未知与示例角色；不能靠删根、假PDF页码或mime使旧检查通过。源路径本身不是正文，资产要实际可交付及绑定SHA。
4. **真实人员／发行。** 旧build要求confirmed_real_human、真实登记SHA和已抽draw；现模板仍pending。管理员可以先准备中性材料候选，不能用TOY人员或假confirmed发“真实真人包”。两方分别交付，各自空表800×5项全部unfilled null，不造首判；私有层/权重/mapping另控权。

已可复用的只读材料入口是：

```sh
python -B "/PROJECT_ROOT/outputs/goal-calibration-20261010/01-review/context-projection-sol/source-interface-v14-textleaf/source_only_interface_v14.py" human RECORD_ID
```

旧workflow build参数为`--source-package --draw-manifest --manual --executor-a --executor-b --output`，但目前缺兼容真实source包、真实draw和真实人登记；因此报告JSON保留其条件式用法，**不是一条当前可运行的完整v14盲包命令**。不应重跑两个规划main，它们会写旧目录且不产生抽样。

分域统计依赖已经有实现：[metrics_engine.py](/PROJECT_ROOT/outputs/goal-calibration-20261010/07-statistics/prospective-engine-domain-sol/metrics_engine.py) SHA `05f5999084a48b0e713e28f81e629015e61c1255cdaa43e89d30a6b59eed1d30`，与ROOT此前实际核验相同。它使用完整共同W输出ALL/remaining/exposed及部门域；不是继续待建框架。统计实际ledger／真人参照／最终机器判断尚未有，本次不算指标。正式首判前冻结M、材料、抽样和统计，最终机器验证在可信参照之后；机器开发的技术重试并不是单纯准备空白来源材料必须先通过的成绩门槛。

full800支持全4481有限语料审计；剩余600提供登记剩余域的独立检验。曝光200（包括可能抽中的77开发材料）始终为曝光用途，不能洗成新holdout。样本注意力是加权估计，不等于4481全文人工认证；剩余未选844条也不自动保证是未来留出。所有真实真人初判、裁定和正式验收仍为未执行。

完整绑定、41层现有参数和必要依赖见[report.json](/PROJECT_ROOT/outputs/goal-calibration-20261010/05-validation/real-human-blindpack600-readiness-sol/report.json)。仅生成本报告及seal，未新增selector、适配程序或框架。
