"""Clarify existing complete-unit, purpose, and routing rules after real errors."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parent = ROOT / "03-manual/common-manual-v1.2-development.md"
text = parent.read_text()
assert text.startswith("# 五维共同编码手册 v1.2：开发校准版")
text = text.replace("# 五维共同编码手册 v1.2：开发校准版", "# 五维共同编码手册 v1.3：开发校准版", 1)
anchor = "## 三、安全性 S"
assert text.count(anchor) == 1
addition = """### 完整单元、宗旨与程序归类的执行核对

下列说明落实本节已有的完整命题、有限确指、一般宗旨排除和条件—实质后果规则，不增加维度，不改变五维定义。五维使用同一门槛。

1. **分别读取基础安排和例外。** 完整表行或句段同时含基础待遇和条件例外时，先列出本记录的每一实质分支，再按各自对象、适用条件和直接后果判断。备注中的确切援引不能删除本行另一列的基础安排。基础分支可补同版同一安排的条内定义；例外仅用其确指范围。不要把基础的全部条件移给例外，也不要把例外推广到基础或兄弟行。同维只要本记录一个实际分支成立即记1，仍至多计一次；不同分支的待遇不自行相加。
2. **制定文件的目的不等于实质措施。** 完整记录仅说明为何制定/印发文件，虽出现药物安全、效果、经济、创新或公平宗旨，也不据此继承该文件后文的全部安排。须在当前本身找出已表达的实质问题、评价/证据要求或可使用措施。反之，目的句若同时明确风险问题及控制要求、效果比较、支付信息核验等内容，仍按这些内容判断；不因总则、目的或背景位置清零，不要求已产生效果，也不要求每句列具体不良反应。
3. **申报归类与支付后果分开。** “此类正在申请调整的品种，申报时选择条件编号”规定申报归类。读取完整被选成员及其共同父谓词可确定分类范围，但“主动申请调整支付范围”作为对象描述，不自动把选择编号变成支付调整授权或信息核验。若当前确实规定符合条件者可申请调整、必须经申报方可调整，或要求核验具体支付内容，则按经济性既有规则纳入；不另要求金额、如何改变的详细清单、充分批准条件或最终成功。前后兄弟记录的续约/补充协议后果不能倒借。

以下是构造教学对照，句子不是语料原文或独立检验答案：

|执行边界|不符合的构造例|实质内容成立的构造例|
|---|---|---|
|安全宗旨与实际风险内容|“为促进合理用药、保障患者用药安全，制定本规范。”S=0|“为降低相互作用风险，药师应审核用药禁忌并拒绝调配严重错误处方。”S=1|
|选择编号与调整权利|“主动申请调整支付范围的品种，申报时选择选项乙。”Ec=0|“符合下列条件的品种可申请调整支付范围。”Ec=1；须读完整确指条件|
|形式与内容核验|“支付范围字段不得为空。”Ec=0|“应核对协议支付范围是否与提交的实际范围一致。”Ec=1|

表格基础/例外的真实来源说明由共同材料单列，不把来源生产者的解释当作首判答案；各编码方仍保存自己的当前完整引文、分支关系、实际使用材料和理由。

"""
text = text.replace(anchor, addition + anchor, 1)
text += "\nv1.3在真实开发分歧裁定后补充上述执行说明和构造对照；依据均为v1.1已有规则。04333旧安全标签和旧root理由另版纠正，01423保留基础分支的S=1并更正依据；机器与AI首判均不覆盖。该版本尚未联合冻结或用于正式检验。\n"
out = ROOT / "03-manual/common-manual-v1.3-development.md"
with out.open("x") as stream:
    stream.write(text)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
report = {
    "created_at": datetime.now(timezone.utc).isoformat(),
    "parent_path": str(parent), "parent_sha256": sha(parent),
    "manual_path": str(out), "manual_sha256": sha(out),
    "semantic_definition_parent": "common-manual-v1.1-development.md",
    "definition_parent_sha256": "6ffc7b35a5cbe1c1f90c81d24d1508dba7adefe5e7bbd058c284d76e14b8a70f",
    "changes": ["complete base and exception branches retained", "file-purpose vs substantive contents clarified", "application routing vs payment consequences clarified", "three constructed teaching contrasts added"],
    "definitions_changed": False, "thresholds_changed": False,
    "all_previous_text_retained_except_title": True,
    "existing_support": ["v1.1 lines9,32-44,50-56,66,84-88", "source-impact4-v12/admin/root-adjudication.json", "source-impact4-v12/admin/root-adjudication-native36-v2.json"],
    "existing_material_and_first_outputs_changed": False,
    "formal_joint_freeze": False, "actual_runs_using_v13_completed": 0,
}
(ROOT / "03-manual/manual-v1.3-clarification-change-log.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"manual_sha256": sha(out), "parent_sha256": sha(parent), "definitions_changed": False}, ensure_ascii=False))
