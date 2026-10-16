合法材料待定 null 的现有 D/E 输入表示补充已完成，旧 adapter、release v1、旧桥和统计引擎均未修改。正式 v2 材料包为 `09-delivery/formal800-human-final-release-v2-20261010-sol`。共同手册、提示词、协议及原 XLSX 都保持原字节；两方 8000 个 D 值与 8000 个 E 理由仍为空，没有真人新提交。

`adapter.py` 是原成熟接收器在新目录的有限延伸。D 仅填 0/1 或留空。D 空且 E 以精确“待定：”或“待定:”开头、冒号后有具体非空缺失说明，保留 `value=null`、`completion_status=lawful_null`、`finished_judgment=true`。原 E、原单元格类型、原 XLSX bytes 与 SHA 完整保存。缺失说明是否实质具体并符合手册，仍由协调员核验，解析器不自动认证。

D/E 都空为 `unfilled`；D 空普通 E 或只有待定前缀为 `incomplete`，需澄清，不自动变 null 或 0。D 填 0/1 而 E 以“待定”开头，记 `invalid` 并准确报 E 的冲突位置，保留实际 D 值而不偷改。公式/布尔/未知盲号/维/行序及缺理由仍沿旧方法拒绝。未完成警告与技术非法错误分别保存。

`fully_filled` 仍只表示 4000 个二元值；新的 `fully_completed` 表示 4000 个 `filled + lawful_null` 已完成判断槽且无内容错误。正式真实发布与实际人类独立声明齐全后，可据 `fully_completed` 内容接收，不能要求合法 null 强填 0/1。没有声明或未完成时仍资格 pending。声明可由用户文字保留进已绑定 receipt，由协调员生成原有事实字段；没有要求用户加 JSON、sidecar 或复核栏。

源 ID 对齐保留双方原初判。任何一方合法 null 时对齐状态为 `lawful_null`，双 null 不记二元 agreement。二元/null 分歧保留在分歧清单；所有合法 null（含双 null）都进入协调员材料待定核验待办，裁定值、理由和执行人保持空白，不自动变参照。

`bridge.py` 仅将 `lawful_null` 投影为旧桥已经支持的 `semantic_null`；`unfilled/incomplete` 仍为 blank，非法内容拒绝。原 joint_binary、覆盖分母、NA 处理、Rao–Wu 5000 和 seed20261010、统计方案及阈值完全复用。`human_first_driver.py` 沿旧入口参数核原件/声明/release/4000 槽与原统计元数据，改用 v2 version、v2 adapter 和 `fully_completed`。没有自动生成 reference，不读机器/Gold或改变 engine。

实际接收命令（尚未执行真实人类件）：

```sh
python3 /本补充目录/adapter.py receive --xlsx-a /真实返回/A.xlsx --xlsx-b /真实返回/B.xlsx --release /v2包/release.json --release-sha256 8e96dfc55ff63cd77df0bca97774a909306a3a1327445b48c55924808037b758 --declaration-a /协调员已保存真实A声明.json --declaration-b /协调员已保存真实B声明.json --out /本补充目录/receptions/新首件目录
```

后续已实际接收的 human_first 转换/计算沿原参数：

```sh
python3 /本补充目录/human_first_driver.py --convert --upstream-reception /本补充目录/receptions/实际首件目录 --statistics-metadata /已绑定真实human_first统计元数据.json --statistics-metadata-sha256 该文件真实SHA --output-dir /本补充目录/statistics/新转换目录
```

需要实际数值运行时才将 `--convert` 改为 `--calculate`；`--coverage-only` 仅作已解析实际接收的未完成诊断。缺真实接收、声明或统计元数据时，不能称数值计算完成。dry-run 绝不进入实际转换/计算。入口及 release 的精确 SHA 见 `entrypoints.json` 与 v2 包 `coordinator-private/reception-contract.json`。

有限实测为四类输入：空/未完成、合法待定、二元、矛盾，共 9 个纯单元格控制；没有创建模拟人类 XLSX。另读实际 v2 原空包为 8000 unfilled/0 错误，完整盲号源 ID 衔接通过，一处临时内存 null 控制投影为 semantic_null，实际 dry-run 数值入口被拒绝。没有计算真实指标/CI，没有旧16测试重跑或大规模模拟；真实人类提交仍0。见 `finite-checks.json` 和 `checks/actual-v2-blank`。输入输出封存见 `seal.json`。
