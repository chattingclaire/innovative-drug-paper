# LLM03全量开发统计：执行前准备

状态：仅准备，未读取03部分结果，未运行模型或实际bootstrap，未采用新方法。原v36.2封存driver保持SHA 20653602caff956d8fade50071e3ec15c4655e65a0b715f22983abee04290f3b。专用副本仅改模块说明及可读标题，统计函数保持一致。

前提是LLM执行agent交付真实 full_development_binding.json 及SHA，状态 complete_actual_full_corpus_development_comparison_QA_PASS，4924条/197批齐全，technical_QA实际PASS。准备脚本会逐项核实际输入/输出/完整五维/来源行/批次/首次有效/全部失败保留/零tools等，并绑定实际prompt与runtime记录；通过后才生成执行适配和development绑定。Root此前已授权该开发统计，未授权自动采用方法。

准备冻结SHA：`90d75536f4d90785b4c6d79ddd977626c51ef4c673992fd300bbf3bdc0320aaa`。完整argv见精确执行计划_PENDING.json。下列两个SHA占位必须用实际闭合报告返回值替换，不能猜测或使用旧02的SHA。

1. Only after full03 actual QA closes; seal development inputs, no formal adoption

```sh
python3 "/PROJECT_ROOT/outputs/coding-revision-20261007-r3/statistics/prepare_candidate03_development_bindings_r3.py" --full-binding "/PROJECT_ROOT/outputs/coding-revision-20261007-r3/llm-candidate03-development/full-corpus-candidate03-material-v14-development/full_development_binding.json" --full-binding-sha256 ACTUAL_CLOSED_FULL_BINDING_SHA256 --preparation-freeze-sha256 90d75536f4d90785b4c6d79ddd977626c51ef4c673992fd300bbf3bdc0320aaa --root-confirmed-development --out "/PROJECT_ROOT/outputs/coding-revision-20261007-r3/methods-20261008/candidate03-complete-statistics-preparation/actual-input-bindings-v1"
```

2. Fresh5000 design statistics, probability180/challenge60 separated, all scopes/A/C/candidate

```sh
python3 "/PROJECT_ROOT/outputs/coding-revision-20261007-r3/statistics/run_candidate03_development_complete_statistics_r3.py" --bindings "/PROJECT_ROOT/outputs/coding-revision-20261007-r3/methods-20261008/candidate03-complete-statistics-preparation/actual-input-bindings-v1/rules-v36.2-plus-LLM03-development-bindings.json" --bindings-sha256 ACTUAL_NEW_DEVELOPMENT_BINDINGS_SHA256 --out "/PROJECT_ROOT/outputs/coding-revision-20261007-r3/methods-20261008/rules-v36.2-plus-LLM03-development-complete-statistics"
```

3. Fresh4481 and same180 descriptive all10pairs, actual03 subtypes definition6 and metadata composition56; no inherited02 results

```sh
python3 "/PROJECT_ROOT/outputs/coding-revision-20261007-r3/statistics/run_candidate03_full_findings_r3.py" --bindings "/PROJECT_ROOT/outputs/coding-revision-20261007-r3/methods-20261008/candidate03-complete-statistics-preparation/actual-input-bindings-v1/rules-v36.2-plus-LLM03-development-bindings.json" --bindings-sha256 ACTUAL_NEW_DEVELOPMENT_BINDINGS_SHA256 --out "/PROJECT_ROOT/outputs/coding-revision-20261007-r3/methods-20261008/rules-v36.2-plus-LLM03-development-findings"
```

步骤2：同180概率样本与60挑战样本分别计算；总体/部门、A/C/候选参照、四格/P/R/F1/κ、NA与适用主CI、同180注意力和部门/方法配对差值一并输出。N_h=947/760/60，B=5000、seed2026100731；NHC普查退化/稀有标签NA不修补。

步骤3：重新从03完整输出和其真实子型计算，全部10对保留，生成4481全量q与coverage、同180参考对照、6定义及56文件构成。51次逐条目剔除加原/文件等权/系列等权/最新年度/剔除联合五种，共56；6和56分别报告，不视作336种交叉情景。条件比例、等权簇均值、零分母簇、混合四格OR区分保留，不做新显著性筛选。

两个结果目录均新建并拒绝覆盖。步骤2会重新计算03的区间，步骤3会重新计算03的敏感性，不调用或借用02稳定性。03稳定性由执行agent另做真实重复，后续独立绑定。

准备QA验证了复制函数与原函数一致、3个入口语法和--help、3个PENDING失败门禁。它不是完整数据运行QA。实际结果生成后仍须独立数字交叉、语义与已知问题审读；正式采用由root完整判断。
