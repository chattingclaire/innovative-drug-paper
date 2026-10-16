# v17 两个原整批 LLM 离线准备

状态：已准备，未派发。只处理原 batch-0325（02577—02588）与 batch-0485（04595—04606），各 12 条、原顺序；不是两条单独推理。packet 总字节分别 117093、141692，均低于原 260000 上限。

基于已实际成功的 v16/0216 入口：保留 CLI 0.162.1、请求 gpt-6.1-sol/ultra、完整手册与科学提示词原字节、严格 parser、真实文字展示/首答/收据规则。每批最多 3 个 fresh 技术 attempt，仅选最早有效整批；合法 null 不重试，不比标签择优。receiver 仅把返回的材料身份从 v16 改为 v17；validator、presentation helper、submit helper 与已成功原件逐字相同。

必要变化：runner 从固定 0216 改为 --batch-id 选择这两批；材料、run、输出 slot/schema 常量重绑定。两批共享一把 execution.lock，新增 CLI 并发上限 1。旧 207 批终态及“全球无 codex exec”历史前提不沿用；ROOT 必须根据当前稳定性容量保留 1 个新增槽，并据真实观察建立 ROOT-execution-binding.json。现存模板 template_only=true、execution_authorized=false，不是实际绑定；既有 Goal 已授权机器侧工作，不需重新向用户申请权限。

只读预检（本轮已执行；不会创建 attempt/lock/first）：

```sh
/opt/homebrew/opt/python@3.14/bin/python3.14 -B '/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/native-v17-two-whole-batch-material-delta-preparation-root/runner.py' --mode preflight --batch-id batch-0325
/opt/homebrew/opt/python@3.14/bin/python3.14 -B '/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/native-v17-two-whole-batch-material-delta-preparation-root/runner.py' --mode preflight --batch-id batch-0485
```

ROOT 审查后填实当前容量观察、单槽预留、入口与 preparation-seal 绑定。然后按顺序执行（此处仅列命令，尚未执行）：

```sh
/opt/homebrew/opt/python@3.14/bin/python3.14 -B '/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/native-v17-two-whole-batch-material-delta-preparation-root/runner.py' --mode run --batch-id batch-0325 --go '/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/native-v17-two-whole-batch-material-delta-preparation-root/ROOT-execution-binding.json'
/opt/homebrew/opt/python@3.14/bin/python3.14 -B '/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/native-v17-two-whole-batch-material-delta-preparation-root/runner.py' --mode run --batch-id batch-0485 --go '/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/native-v17-two-whole-batch-material-delta-preparation-root/ROOT-execution-binding.json'
```

ROOT 收据由 runner 调用 strict-readback-receiver.py 的 verify(manifest, assignment, first) 产生，路径为每批 attempt-NNNN/root-reception.json；最早有效批次记录在各自 root-selection.json。所有真实首答、进程事件、失败及 attempt 原件保留。不得用预检/材料准备代替实际 READ 或编码。

本次按 ROOT 最新分工只先交付两批执行与接收入口；整批合并入口尚未实现。未来在两批接收后，从当前 native-full4481-v16-three-member-compatible-root 保留 4457 原行字节，整批替换 24 行，保留此前 v16/0216 的真实来源，另存 v17 全量合成。未新建总体结果、未读取新输出、未改稳定性配置/结果；原稳定性 800 仍是 v16。
