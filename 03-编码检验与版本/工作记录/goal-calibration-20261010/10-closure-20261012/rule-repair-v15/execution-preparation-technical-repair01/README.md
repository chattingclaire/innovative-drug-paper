# 第二次实际技术尝试准备

首轮真实运行失败已保留：383 条完成记录均 PermissionError，0 条接收，原父进程 wait 返回 -15。本目录不重置该历史，不接收首轮部分结果。

本次仅把原 source-reading-protocol-v12.json 加入运行材料许可清单。所有运行 Python、五模块分类器、协议、审计、接收器字节保持不变；完整 4481 条重新执行，0 条继承。新 run/wait 路径已绑定，received 仍使用原未创建路径。

ROOT 应基于 release.UNRELEASED-technical-retry01.json 填入真实授权和既有规则/统一控制审查，另存为实际 release；使用本目录原样复制的 finalize_scope.py 生成独立 scope。随后仍用既有 Python /opt/homebrew/opt/python@3.14/bin/python3.14 -B 运行本目录 actual-first-run-supervisor.py --scope <新 scope 绝对路径> --scope-sha256 <真实 SHA>，以独立 session、DEVNULL stdin 和独立外部日志启动。不可复用首轮 scope/release 或输出目录。

等待真实 parent wait 完成后，用本目录 receive_merge.py 对新完整 run 按同一 scope 接收。所有命令均未在本目录实际启动。

protocol-dependency-checks.json 记录原配置遗漏的真实 PermissionError 复现，以及补绑定后原 prepare/check 在原审计下成功读取配置三次；READ/USE 均为 0，未调用分类器。初次纯检查脚本遗漏 source_receipts 导入的失败也已单列保留并仅修检查脚本。
