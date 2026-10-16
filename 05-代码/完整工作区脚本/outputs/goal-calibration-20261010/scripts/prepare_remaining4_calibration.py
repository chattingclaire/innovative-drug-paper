"""Prepare source-complete local adjudication inputs; never edit existing judgments."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUPPORT = ROOT / "logs/remaining4-calibration-delivery"
SUPPORT.mkdir(exist_ok=True)
MANUAL = ROOT / "03-manual/common-manual-v1.3F-frozen/manual.txt"
PDF = ROOT / "00-baseline/source-files/64ac48e587537802-NHSA-常用问答-2026版.pdf"
IMAGE = ROOT / "01-review/context-projection-sol/literal-review-v2/pages/64ac48e587537802-p11.png"


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def split_exact(text, limit=520, max_lines=13):
    out, start = [], 0
    while start < len(text):
        end = min(start + limit, len(text))
        newlines = [i for i in range(start, end) if text[i] == "\n"]
        if len(newlines) >= max_lines:
            end = newlines[max_lines - 1] + 1
        out.append(text[start:end])
        start = end
    assert "".join(out) == text
    return out


def main():
    report = json.loads((ROOT / "logs/uniform-machine77-report-delivery/report-inputs.json").read_text())
    lookup = {(r[0][-5:], r[2].split()[0]): r for r in report["rows"]}
    bindings = []
    blocks = []
    packets = {}
    for sid in ["00005", "03876", "00138"]:
        p = ROOT / f"06-coding/development77-native-inputs-v14/packets/RECODE25-{sid}.compact.json"
        packets[sid] = json.loads(p.read_text())
        bindings.append({"path": str(p), "sha256": digest(p)})
    for p in [MANUAL, PDF, IMAGE]:
        bindings.append({"path": str(p), "sha256": digest(p)})

    def add(key, title, text, locator, path):
        blocks.append({"key": key, "title": title, "text": text, "locator": locator, "path": str(path), "text_sha256": hashlib.sha256(text.encode()).hexdigest()})

    b = packets["00005"]["source_bundle"]
    r = b["source_full_text_resources"][0]
    add("00005条件", "00005：突破性治疗程序的完整适用条件及申请语境", r["text"], "/source_bundle/source_full_text_resources/0/text；原附件文本第1—26行", r["locator"]["snapshot_absolute_path"])
    b = packets["00138"]["source_bundle"]
    for index in [2, 3, 4]:
        r = b["source_full_text_resources"][index]
        text = r["text"]
        if index == 2:
            start = text.index("附件3\n药品上市许可优先审评审批工作程序")
            text = text[start:]
        else:
            start = 0
        span = r["locator"]["physical_line_range_1based_inclusive"]
        title = {2: "00138：优先程序适用对象（续见下一材料块）", 3: "00138：完整适用条件、申报前沟通及纳入程序", 4: "00138：纳入后的技术审评、沟通与完整工作要求"}[index]
        add(f"00138语境{index}", title, text, f"/source_bundle/source_full_text_resources/{index}/text；字符起点{start}；原资源行{span[0]}—{span[1]}", r["locator"]["snapshot_absolute_path"])
    b = packets["03876"]["source_bundle"]
    add("03876流程", "03876：当前完整流程图转写；原图另见流程原图页", b["source_record"]["text"], "/source_bundle/source_record/text；原PDF物理第11页，印刷第8页", PDF)
    for page, label in [(8, "价格协商说明的前页"), (9, "价格协商说明"), (20, "商保目录使用说明的前页"), (21, "商保目录使用说明")]:
        text = subprocess.run(["/opt/homebrew/bin/pdftotext", "-f", str(page), "-l", str(page), "-layout", str(PDF), "-"], check=True, capture_output=True).stdout.decode("utf-8")
        add(f"03876补材{page}", f"03876：同版本原PDF整页补材——{label}", text, f"同版PDF物理第{page}页；整页文字抽取，非新版本政策", PDF)
    manual = MANUAL.read_text()
    for key, start, end in [
        ("共同语境规则", "### 必要语境的统一范围", "### 记录单元、语境与计数"),
        ("安全性规则", "## 三、安全性 S", "## 四、有效性 E"),
        ("经济性规则", "## 五、经济性 Ec", "## 六、创新性 I"),
        ("创新性规则", "## 六、创新性 I", "## 七、公平性 F"),
        ("公平性规则", "## 七、公平性 F", "## 八、概念来源与使用要求"),
    ]:
        text = manual[manual.index(start):manual.index(end)]
        add(key, "现行共同手册：" + key, text, "共同手册v1.3F；按所示标题的完整章节/小节", MANUAL)

    materials = []
    spans = {}
    nextrow = 7
    for block in blocks:
        chunks = split_exact(block["text"])
        first = nextrow
        for index, chunk in enumerate(chunks):
            materials.append([block["key"], f"{block['title']}\n{index + 1}/{len(chunks)}", block["locator"], chunk, block["path"]])
            nextrow += 1
        spans[block["key"]] = [first, nextrow - 1]
    def pos(*keys):
        return "；".join(f"{key}：原文语境D{spans[key][0]}—D{spans[key][1]}" for key in keys)
    specs = [
        ("00005", "S", "D7", "当前“有足够证据表明具有明显临床优势”的申请条件，是否承接同版完整定义中的安全性优势分支？请区分药物安全标准与疾病本身的严重程度。", ["00005条件", "共同语境规则", "安全性规则"]),
        ("03876", "Ec", "D179", "当前完整流程是否实质设定或适用药品价格协商安排，还是仅列阶段、协商成败和目录结果？商保目录是推荐参考，不能直接推成实际承保或支付范围。", ["03876流程", "03876补材8", "03876补材9", "03876补材20", "03876补材21", "经济性规则"]),
        ("00138", "I", "D215", "当前针对已纳入品种的沟通是否直接提供创新/改良研发可用的技术支持？请分别写清支持对象、具体安排、直接联系，并区分申报前与纳入后阶段。", ["00138语境2", "00138语境3", "00138语境4", "共同语境规则", "创新性规则"]),
        ("00138", "F", "D216", "当前沟通安排是否与明确治疗缺口相连，形成按需要配置的优先机会？请核验“审评中优先沟通”与本条是否为同一安排，不能仅由程序名称或品种身份推定。", ["00138语境2", "00138语境3", "00138语境4", "共同语境规则", "公平性规则"]),
    ]
    rows = []
    for sid, dim, orig, question, keys in specs:
        row = lookup[sid, dim]
        current = packets[sid]["source_bundle"]["source_record"]["text"]
        assert current == row[9]
        rows.append([sid, row[1], row[2], None, None, question, current, pos(*keys), f"原A/B编码表{orig}；理由E{orig[1:]}"])
    output = {"rows": rows, "materials": materials, "blocks": blocks, "material_spans": spans, "bindings": bindings, "image_path": str(IMAGE), "image_sha256": digest(IMAGE), "manual_path": str(MANUAL), "instruction": "只核验本表4项。D列填0或1，E列写原文依据及适用关系；证据仍不足时D暂留空、E注明缺失材料。请独立判断，不要求与任何一方一致。", "scope": {"records": 3, "slots": 4, "posthoc_calibration": True, "independent_blind_validation": False, "original_labels_modified": False, "excluded_already_reviewed": ["02573-Ec", "01423-S", "04333-S", "03415-E", "00036-S", "00038-S", "00045-S"]}}
    target = SUPPORT / "report-inputs.json"
    with target.open("x") as f:
        f.write(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"input": str(target), "slots": 4, "material_rows": len(materials), "source_blocks": len(blocks)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
