# 论文构建档案（2026-08-13）

本文件夹保存《制度视角下创新药多主体评价的认知分歧与协调路径》终稿的全部中间产物与构建工具，任何一台装有 pandoc + python3 的机器都能从源文件完整重建 docx。

## 文件清单

| 文件 | 作用 |
|---|---|
| 论文源文件-revised.md | **唯一编辑源**。含 `[@引用键]` 占位与 `[标黄]{.mark}` 高亮标记。改论文改这个文件 |
| 论文源文件-styled.md | 中间产物：加入《科学决策》样式 div 标记后的版本（脚本生成，勿手改） |
| 论文源文件-styled_numbered-最终编号版.md | 中间产物：引用编号展开后的最终文本 |
| renumber.py | 引用编号器：按正文首次出现顺序给 `[@键]` 编号并生成参考文献表（43 条文献的权威著录、含英文对照翻译都在此脚本内，**已经过 6 个核查 Agent 溯源修正**） |
| postprocess.py | docx 后处理：表格拉全宽 + 写入 20 条 Word 批注（批注文本也在此脚本内） |
| reference_kxjc-科学决策样式参考文档.docx | pandoc 样式参考（标题黑体居中、正文五号宋体首行缩进、表格封口等按期刊模板定制） |
| fig_make.py | 图1（分析框架）、图2（雷达图）绘图脚本 |
| fig1_framework.png / fig2_radar.png | 两张插图成品（300dpi） |
| 科学决策-投稿须知/版式/指南-原始网页.html | 期刊官网要求页面存档（gb2312 编码），官方模板 doc 在项目根目录 |
| 参考文献清单-核查前快照.txt | 核查前的 45 条文献快照（对照用；终稿为修正后 43 条） |

## 重建步骤

```bash
# 1. 样式标记（revised.md → styled.md）：见项目会话记录中的转换脚本，或直接编辑 styled.md 同步修改
# 2. 编号展开
python3 renumber.py 论文源文件-styled.md styled_numbered.md
# 3. 生成 docx
pandoc styled_numbered.md -o final.docx --reference-doc=reference_kxjc-科学决策样式参考文档.docx --resource-path=.
# 4. 后处理（需先 unzip final.docx -d finalw/，用 docx 技能的 comment.py 建批注基础设施后运行）
python3 postprocess.py && cd finalw && zip -Xr ../final_commented.docx .
```

## 数据文件（项目根目录）

- `all_sentences.json`：3387 句语料（55 份文件，NMPA19/NHSA24/NHC10/GOV2）
- `llm_all_results.json`：LLM 逐句编码结果（表2 LLM 列、5.2 节稳健性检验数字的数据源）
- `数据复核-0813/verify_data.py`：一键复核论文中所有可本地验证的数字
- **缺档提醒**：词典逐句编码结果未存档（κ 值、表3 频次无法复算），96 词词典全表、LLM 调用参数与提示词需从原编码脚本导出——见论文附录A的黄色批注。

## 2026-08-15 更新：缺档已全部找回

原以为丢失的编码脚本已从 Claude Code 会话记录 `~/.claude/projects/-Users-rainbow-Desktop-------------/b1283b56-….jsonl`（2026-07-24 会话）中恢复，存于 `编码脚本-已恢复/`：

| 文件 | 内容 |
|---|---|
| 词典编码脚本-policy_coding_v2.py | 96 词词典全表（安全17/有效19/经济21/创新18/公平21）、排除规则、分句与编码逻辑 |
| LLM编码脚本-llm_code_all.py | LLM 编码全流程：模型 `claude-sonnet-4-20250514`、max_tokens=4096、未设温度（用接口默认值）、每批 50 句、系统提示词全文 |

**已验证复现**：用恢复出的词典在 `all_sentences.json`（3387 句）上重跑，表 3 四个部门 × 五维度共 20 个频次**逐一精确一致**，列合计 348/440/736/365/232 一致，编码句 1701 一致；配合 `llm_all_results.json` 重算表 2，五个 κ 值（0.896/0.700/0.921/0.917/0.831）与总体 κ=0.867、一致率 97.1%、差异句 456 **全部精确一致**。论文表 2、表 3、表 4 现已完全可复算。

复现命令：
```bash
python3 数据复核-0813/verify_full.py
```
