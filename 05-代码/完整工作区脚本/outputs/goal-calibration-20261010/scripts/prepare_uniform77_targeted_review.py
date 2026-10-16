"""Prepare located materials for the five new disagreements, without editing labels."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = [("00005", "S", "D7"), ("02573", "Ec", "D144"), ("03876", "Ec", "D179"), ("00138", "I", "D215"), ("00138", "F", "D216")]


def main():
    data = json.loads((ROOT / "logs/uniform-machine77-report-delivery/report-inputs.json").read_text())
    lookup = {(row[0], row[2].split()[0]): row for row in data["rows"]}
    out = ROOT / "09-delivery/agent-review-20261010/本轮新增5项分歧核验材料.txt"
    sections = [
        "本轮新增5项分歧：4条材料的局部语义核验（2026-10-10）",
        "当前A/B与规则均为0，LLM均为1。下列机器理由是待核查意见，不是已经确认的人类结论。数值点指标已达0.80不决定这些条款的语义判断。现A/B与两机器原判均未修改。",
        "此前已接收并保存的01423-S、04333-S、03415-E、00036-S、00038-S、00045-S不在本次补核范围。没有新加真人复核栏；若真人补核，直接在现有A/B对应D/E位置修改或提供逐项值与理由，由ROOT另存参照版本并完整复算。",
        "统一边界：当前明确要求、实施或限定实质安排，可用同版本同一安排的定义、对象与直接机制解释。程序名称、一般指引或已纳入身份不能展开全篇；不能从兄弟行动借来另一项措施。定性经济安排不要求金额，但仅阶段、协商成败或目录结果仍排除。I3要同时有创新研发对象、可用支持和直接联系；F要同时有治疗缺口与按需机会联系。",
    ]
    sources = []
    for suffix, dim, location in TARGETS:
        sid = f"RECODE25-{suffix}"
        row = lookup[sid, dim]
        assert row[3:6] == [0, 1, 0]
        packet_path = ROOT / f"06-coding/development77-native-inputs-v14/packets/{sid}.compact.json"
        packet = json.loads(packet_path.read_text())
        raw = json.loads(Path(row[12]).read_text())
        first = next(item for item in raw["records"] if item["source_id"] == sid)
        decision = first["dimensions"][dim]
        sections.extend([
            f"\n{suffix}／{dim}：现有A/B编码表{location}；新机器对照表编码对照{location}（参照列D，LLM列E）。",
            "当前完整条款：\n" + row[9],
            "当前参照理由：\n" + row[6],
            "LLM原判理由：\n" + row[7],
            "原判所用完整引文（逐字来自冻结材料）：",
        ])
        for evidence in decision["evidence"]:
            pointer = next((evidence.get(key) for key in ("pointer", "json_pointer", "packet_json_pointer", "packet_pointer") if evidence.get(key)), None)
            if pointer:
                value = packet
                for key in pointer[1:].split("/"):
                    key = key.replace("~1", "/").replace("~0", "~")
                    value = value[int(key)] if isinstance(value, list) else value[key]
                assert evidence["quote"] in value
            else:
                pointer = f"{evidence['asset_path']} 页{evidence['page']}"
            sections.append(pointer + "\n" + evidence["quote"])
        if suffix == "00005":
            question = "核验点：当前有足够证据表明明显临床优势的申请条件，是否使用了同版对明显临床优势的完整定义（其中明确包含安全性优势分支）？与已复核00036/00038使用同一标准的口径是否一致？严重疾病本身不能支持S。"
        elif suffix == "02573":
            question = "核验点：药品甲乙类别调整在当前完整材料中，是否已承载支付/报销类别的实质调整含义？如果必须补足甲乙支付含义，应使用同版权威原文并统一加到材料包；不能仅靠模型外部常识，也不因没有金额自动判0。"
        elif suffix == "03876":
            question = "核验点：商保目录新增适应症在此图中，是目录内容结果还是明确的药品支付/保障范围变更？完整流程是否在当前实质适用价格协商安排，还是只展示协商阶段/成败/目录结果？不能直接把商保目录等同所有保险承保或实际支付。"
        elif dim == "I":
            question = "核验点：当前沟通安排是否直接承接创新/改良研发的专门技术服务？LLM引用申报前解决技术问题，与当前已纳入后工作要求是否是同一适用行动/机制？普通沟通形式不足，不能由优先程序身份继承全部创新待遇。"
        else:
            question = "核验点：当前沟通服务是否确实以已明示的短缺等治疗缺口配置优先机会？LLM引用审评中优先沟通，是否能解释当前同一安排，还是来自平行子项的另一行动？一般程序品种身份不足。"
        sections.extend([question, "完整材料文件：" + str(packet_path), "完整机器初判：" + row[12]])
        sources.append({"source_id": sid, "dimension": dim, "cell": location, "packet_path": str(packet_path), "packet_sha256": hashlib.sha256(packet_path.read_bytes()).hexdigest(), "raw_first_path": row[12], "raw_first_sha256": hashlib.sha256(Path(row[12]).read_bytes()).hexdigest()})
    with out.open("x") as stream:
        stream.write("\n\n".join(sections) + "\n")
    receipt = {"artifact": str(out), "sha256": hashlib.sha256(out.read_bytes()).hexdigest(), "sources": sources, "new_cases_N": 4, "new_slots_N": 5, "human_review_received": False, "original_labels_modified": False}
    with (ROOT / "logs/uniform-machine77-report-delivery/targeted-new-disagreement-materials-seal.json").open("x") as stream:
        stream.write(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"output": str(out), "new_slots_N": 5, "original_labels_modified": False}, ensure_ascii=False))


if __name__ == "__main__":
    main()
