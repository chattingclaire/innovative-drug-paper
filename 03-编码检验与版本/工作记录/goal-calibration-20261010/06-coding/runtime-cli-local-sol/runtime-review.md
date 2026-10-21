隔离环境仅完成一次官方包安装，当前可执行入口不可报告为可用。npm安装exit0，新darwin-arm64原生文件在探测前实际存在（192631440字节，SHA256：c6f92c1c2115b348fafeab37338ef2ef3f43330e7cfd85664222f7defc9b3599）；新入口 `--version` 在20秒内未返回，stdout/stderr为空，随后该native路径已经不存在。文件消失原因未核明，不据此宣称XProtect、Gatekeeper或新exit137。已停止，没有重试、重新安装、执行 `exec --help` 或运行模型。

固定版本：wrapper0.130.0，官方平台包0.130.0-darwin-arm64。采用官方npm包及正常脚本，以npm标准prefix安装；缓存及空npm配置在本目录，全局wrapper字节核对未变。官方入口以模块相对路径定位平台依赖，本次曾实际补齐缺文件。官方文档提供[npm安装途径](https://learn.chatgpt.com/docs/codex/cli)，不能把安装成功等同运行成功。

入口绝对路径（目前其新native缺失）：
`/PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding/runtime-cli-local-sol/node_modules/.bin/codex`

准确模型/设置组合未核明。公共models_cache(client_version0.160.1)列出gpt-6.1-sol和ultra，但不证明0.130.0 CLI可按同设置运行。[同版本配置schema](https://github.com/openai/codex/blob/rust-v0.130.0/codex-rs/core/config.schema.json)只接受none、minimal、low、medium、high、xhigh，不能原样指定ultra。[官方GPT-6.1 Sol模型页](https://developers.openai.com/api/docs/models/gpt-6.1-sol)核明精确slug、API档位列到max；桌面ultra的CLI/API等效映射保留unknown，未替换为gpt-6.1、Astra或其他档位。

没有更改全局npm、用户auth/config、quarantine或codesign，没有再次执行原应用binary。启动超时后限定当前新native路径检查，没有发现残留匹配子进程。首次封存尝试因新native消失而发生FileNotFoundError，已保存该失败记录；最终报告使用探测前SHA并明确其历史角色，不伪称当前文件仍在。

- 安装次数1；安装成功，但当前native再次缺失。
- 真实可用入口：未验证通过；version/help均未验证通过。
- gpt-6.1-sol + ultra精确组合：未核明；literal ultra不属于旧CLI schema。
- 实际model calls：0；实际label runs：0。

实际argv、stdout/stderr、版本/探测前SHA、官方来源与取得记录、初次封存失败和最终字节manifest均存于本目录。这是独立环境核查，不是编码执行或研究验收。
