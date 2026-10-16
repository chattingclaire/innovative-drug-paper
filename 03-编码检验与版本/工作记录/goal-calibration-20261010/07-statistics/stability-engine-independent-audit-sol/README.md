# 有限独立审查产物

结论先读 `audit-report.md`，独立算式见 `hand-checks.md`。所有输入均为构造数据；没有真实标签/政策正文、Gold或模型调用。

- `independent_fixture.py`：十一条独立构造数据与请求组装器，不导入原实现。
- `audit_controls.py`：原引擎38项、修复副本34项有限控制；两个原接受缺陷的输入和原CLI输出另存。
- `supplemental_controls.py`：8项必要补充与合法输入回归。
- `controls-original.json`、`controls-repair.json`、`supplemental-controls.json`：逐项结果，不将重复阶段加总为独立证明。
- `originalbugoutput/`：修复前原CLI接受两个无效类型输入的完整输出。`boundary-originaloutput/`：外部引用信任及纯来源前置契约缺口的构造接受证据。
- `repair-candidate/`、`repair-candidate.diff`：仅在本目录复制修复，不动原sealed文件。复制的原22项回归日志在 `verification/`。
- `original-candidate-mixed-replay/`：用原CLI/原输入在新目录重放，五文件与旧封存结果逐字一致。
- `seal_audit.py`、`audit-seal.json`：本审查文件和只读源的字节封存；不认证实际模型/独立性/来源资格。

控制脚本保护既有构造目录，不可对本sealed目录直接再跑生成命令。复现时复制脚本到一个新的空审查目录（保持其父目录能找到同一只读候选），先 `python3 -B -c 'from pathlib import Path; from independent_fixture import build; build(Path("inputs/independent-eleven"))'`，在该目录用原CLI生成 `original-baseline-cli/`，再运行审查脚本。既有原缺陷也可直接在任意新输出目录重放：

```bash
python3 -B ../prospective-stability-engine-sol/stability_engine.py analyze \
  --registry inputs/census-boolean-pi/registry.json \
  --ledger inputs/census-boolean-pi/ledger.json \
  --out-dir NEW_EMPTY_OUTPUT
```

第二个反例改用 `inputs/retry-policy-json-type/`。用本目录 `repair-candidate/stability_engine.py` 分析这两条输入，应退出2并拒绝；合法构造baseline应成功。封存核验命令为 `python3 -B seal_audit.py --verify`。
