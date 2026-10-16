# 稳定性运输容量13：最小外置修订

仅完成准备与机械控制，未签GO，未启动CLI（包括help）、模型或分类器。当前生产与恢复仍按其原3并发运行；本修订不迁移、不停止这些进程。

本修订是公开容量例外：将尚未执行的固定800条/87诊断批R1/R2/R3/W/H的真实CLI进程上限由3改为13。明确例外覆盖共同protocol第11行“最多3并发”及旧cap3运输元数据的3上限，不能称完全遵循原3容量条款。样本、方法、指标和阈值不降低；用户既有13并行授权已确认，实际采用仍由ROOT复核。

原core R请求、CWD、成员与顺序、材料、W/H、首答schema、完整读取与逐字quote/null规则、每批至多3技术attempt、最早有效完整首答选择、ROOT_transport捕获与封存身份、五条件顺序和统计接口均不变。P及其技术重试仍不是R；W/H仍不是R重复。新ROOT manifest除容量13及四项ROOT外置绑定外，与旧manifest完全相同；沿用旧run_id以保持首答schema身份，实际运输修订由独立profile/sidecar/GO绑定区分。模型可见旧文件不追加此容量修订。

未复制旧全目录或研究材料。封存runner与receiver直接读原代码字节后在内存加载；controller仅在内存将worker上限、启动记录容量及对应docstring由3换成13。外部common覆盖OS令牌循环与GO容量核验，追加必需ROOT容量profile/预检/sidecar绑定及容量例外确认、只授权cap13入口声明。ROOT GO schema只有这些运输字段改变；原首答与seal/schema不动。差异定位保存在capacity-only-delta-proof.json。

ROOT已明确同意沿用原campaign锁和预留空槽。controller使用同一个原ROOT-controller.lock，防止cap3与cap13同时运行；OS容量使用同一个ROOT-capacity目录，13入口用1..13，旧3入口仅用1..3。ROOT真实GO只可授权其中一个入口。未来执行记录追加到原assignment允许的ROOT-output空槽；这属于原freeze允许的追加，不能覆盖旧准备文件或重置attempt。原3127个封存文件hash全部保持，1305槽仍空。严格接收器要求first位于原assignment目录下，因此不另改输出路由，避免更改研究输入或接收规则。

仅新增3项必要控制，全部通过：缺失GO在Popen前拒绝；template_only=true的13 GO按该字段拒绝；14个真实本地Python非模型进程竞争同一13令牌，活动峰值实际为13，最终全部退出。未重复原37控制，其封印仍复用。本地控制不能证明真实模型服务在13并发下的吞吐、可用性或provider身份。新runtime尚无真实CLI执行成功证据。

正式GO仍必须等待生产、恢复、controller及真实子进程全部末态，生产/恢复不再派发。ROOT签发真实终态证书及独立ROOT-execution-GO.json：保留原campaign_manifest和原cap3预检绑定，并增加本目录run-manifest/preflight/sidecar三个绑定、容量例外认可和仅cap13授权；max_concurrent_CLI=13。生产证据/已关闭PID等原检查保持，任何仍在进程表中的PID阻断启动。ROOT-GO-capacity13.template.json故意无效，不是授权，不可直接使用；真实GO文件目前不存在。

未来ROOT真实GO就绪且决定采用后，唯一执行入口如下。入口固定使用原campaign与同一预留槽；已有效的整批选择复用，合法null不重试，部分或不确定槽阻断，不跨attempt拼接。按R1→R2→R3→W→H执行全部87批，未到五条件末态不计算统计。原statistics_after_terminal.py接口保持可用，不在此次准备运行。

```sh
/opt/homebrew/opt/python@3.14/bin/python3.14 \
  "/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/current-freeze-stability-capacity13-transport-sol/controller.py" \
  --go "/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/current-freeze-stability-capacity13-transport-sol/ROOT-execution-GO.json"
```

freeze-seal.json封存当前存在的外置修订文件，预留的未来GO和实际运行记录另增；旧cap3总封印不变。到此停止准备，无模型/分类器、无人审200答案读取，无新标签、无指标验收声明。
