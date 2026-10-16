"""Prepare an immutable development manual and source-only independent AI packets.

This is a development exercise, never a human validation or holdout evaluation.
Only already-exposed IDs are selected. No historical labels enter coder packets.
"""
import hashlib
import json
import random
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def write_new(path, text):
    if path.exists():
        if path.read_text(encoding="utf-8") == text:
            return
        raise FileExistsError(f"Refusing overwrite: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def write_json(path, obj):
    write_new(path, json.dumps(obj, ensure_ascii=False, indent=2) + "\n")

audit = json.loads((ROOT / "01-review/manual-audit.json").read_text())
baseline = ROOT / "00-baseline/legacy-calibration-manual.md"
manual = baseline.read_text()
manual = manual.replace("# 五维共用编码手册", "# 五维共同编码手册 v1.0：开发校准版", 1)
manual = manual.replace(
    "本手册供人工校准讨论使用，尚未冻结为新一轮检验标准。",
    "本手册供开发校准使用，尚未冻结为独立最终检验标准。版本日期2026-10-10。"
    "本轮A/B为GPT-6.1 Sol、ultra的独立AI判读；其结果不能记为真人独立编码。", 1)

changes = {row["id"]: row for row in audit["necessary_changes"]}

def add_before(marker, text):
    global manual
    if manual.count(marker) != 1:
        raise ValueError(f"Ambiguous marker {marker}")
    manual = manual.replace(marker, text + "\n\n" + marker, 1)

add_before("### 记录单元、语境与计数", changes["MA01"]["replacement"])
add_before("## 三、安全性 S", changes["MA02"]["replacement"])
add_before("**排除：** 仅新获批/上市/申报", changes["MA03"]["replacement"] + "\n\n" + changes["MA04"]["replacement"])
old = "**具名支持计划的实施与撤回。** 当前明确决定启动、批准实施、纳入或终止确指计划，且共同材料已提供该同一计划的具体创新支持机制时，可补足支持关系。仅名称、宣传目的或没有明确承接的历史介绍不足；“计划开展”不因未来语气一律排除，“已经开展”也不因完成时一律纳入。所需机制缺失时先统一补材，不由单个编码员查得答案后私自使用。该门槛同样适用于设立和撤回，不能只补支持不补限制。"
assert old in manual
manual = manual.replace(old,
    "**具名支持计划的实施与撤回。** 依第二节五维共同的有限确指语境规则执行，并填写I3对象—可用安排—直接联系三项证据。"
    "当前‘纳入’若实质授予已核明的支持机会，可补足；仅记载身份或历史状态，不能展开全部待遇。", 1)
add_before("**患者可负担性：**", changes["MA05"]["replacement"])
add_before("## 八、概念来源与使用要求", changes["MA06"]["replacement"])

manual += """

## 九、共同分类释义与版本使用

下表仅解释本轮材料明确援引的2020年起注册类别。它不替当前单元生成创新标签；须满足I1/I4当前技术内容或资格—后果关系。分类所需语境也是共同材料，所有方法使用同版。2020年前旧分类、版本不明或数字没有药类时，登记补材，不自行套用。

|药品体系及已核时期|创新/改良类别含义|不能推定的内容|核明依据|
|---|---|---|---|
|化学药；2020-07-01起分类|1类为创新药；2类为基于既有活性成分的改良型新药，并要求临床优势|3/4类仿制、5类境外已上市不能仅由类别号称创新；单有重大适应症变化不能替代具体类别或改良关系|国家药监局2020年第44号，分类I及管理II；官方英文全文|
|治疗用生物制品；2020-07-01起分类|1类为创新型；2类为改良型，含规定的产品改进及优势要求|不得把化学药新结构条件套用；3类已上市/生物类似药不能仅因数字视创新|国家药监局2020年第43号，第二部分一；药监局直属交流中心全文|
|预防用生物制品；2020-07-01起分类|1类创新型疫苗、2类改良型疫苗，各有具体分类条件|‘改变人群/途径’孤立词不使全部疫苗都具创新资格；适用子类须按共同原文|同上第一部分一|
|中药；2020-07-01起分类，68号通告确认|1类创新药；2类改良型新药；3类古代经典名方复方制剂|前三类均可属中药新药，但3类不能自动称技术创新；分类不表示疗效高低|国家药监局2020年第68号通告一、二、五；上海药监官方转载|

资料链接：[化学药](https://english.nmpa.gov.cn/2020-06/30/c_528659.htm)；[生物制品](https://www.ccfdie.org/cn/yjxx/yphzp/webinfo/2020/07/1592159028365748.htm)；[中药](https://yjj.sh.gov.cn/qtgzwj/20201229/95fa9edd0d2d4a789af4adfcfa93c51a.html)。

## 十、判读输出与材料问题

每条保存五维0/1/null；null只用于缺失的关键原文、不可解析指代或待统一的真实规则冲突，须写明待补什么，不代替正常判断。材料充分但不符合判据时为0。五维逐一判断，不能因I/F难判把其他可判维也清空。

每维保存：标签、证据路径、当前原文连续锚点、实际使用的语境编号及连续引文、理由。支持I3填写研发对象、可用支持安排及直接关系；具体F填写患者药品对象、公平关系及当前安排/评价。0也简述最接近的候选内容为何未满足判据。引文来自当前或列明语境，不能加入自己的外部检索结果。

语境仅是可读材料；按第二节决定实际使用。包中若缺确指同一计划/条件，提出统一补材请求。若没有缺失援引而只是没有公平或支持关系，则依据现有完整命题判0，不因理想上可能有其他背景无限请求补材。相同规则适用于五维。

以下均为构造教学例，不是语料或检验答案：

|维度|实质关注例|不符合例|
|---|---|---|
|S|‘应报告该药导致的肝损伤，并采取停药措施。’=1|‘上传材料时应遵守网络安全要求。’=0|
|E|‘应比较该药与对照药改善生存的证据。’=1|‘申报账号有效期为一年。’=0|
|Ec|‘应说明治疗费用及基金预算影响。’=1|‘请在规定时间递交谈判文件。’=0|
|I|‘与原片剂相比，拟用口崩设计能否缓解吞咽障碍，仍需验证。’=1/I2|‘本指南面向创新药，申报文件须签字。’=0|
|F|‘应评价同等治疗需要患者取得药物的机会是否公平。’=1|‘处方平台保证电子信息顺畅流转。’=0|

## 十一、使用身份与本版本状态

本版本只供开发试判。AI独立判读、真人事后复核、真人协商前独立判读分别留存；agent生成或修订答案不更名为真人初判。开发试判分数不作为总体机器效度或真人信度验收。讨论后改变的答案另写裁定/重判文件，不覆盖初始提交。冻结后的独立样本若用于修订，转为开发；后续独立检验另行设计。所有变更以原文、概念和执行边界为依据，不按部门目标占比或预期分数选择。
"""

manual_path = ROOT / "03-manual/common-manual-v1.0-development.md"
write_new(manual_path, manual)
write_json(ROOT / "03-manual/manual-v1.0-change-log.json", {
    "status": "development_not_frozen_for_final_validation",
    "baseline": {"path": str(baseline), "sha256": sha(baseline)},
    "new_manual": {"path": str(manual_path), "sha256": sha(manual_path)},
    "changes": audit["necessary_changes"],
    "inherited_substantive_change_not_previously_logged": {
        "dimension": "I", "path": "I2",
        "change": "拟用产品设计针对明确使用障碍并给出改变—改善关系时，可计改良议题；尚未证明效果不取消议题",
        "already_in_candidate_manual": True, "not_new_this_run": True,
        "not_a_claim_of_proven_clinical_advantage": True},
    "new_common_classification_sources": [
        "https://english.nmpa.gov.cn/2020-06/30/c_528659.htm",
        "https://www.ccfdie.org/cn/yjxx/yphzp/webinfo/2020/07/1592159028365748.htm",
        "https://yjj.sh.gov.cn/qtgzwj/20201229/95fa9edd0d2d4a789af4adfcfa93c51a.html"],
    "metric_based_choice": False, "historical_labels_modified": False})

frame = {r["id"]: r for r in map(json.loads, (ROOT / "00-baseline/source-only-frame.jsonl").read_text().splitlines())}
expo = json.loads((ROOT / "01-review/exposure-ids.json").read_text())
excluded = set(expo["excluded_ids"])
old_if = json.loads((ROOT / "00-baseline/legacy-IF-disagreements.json").read_text())
selection = {}
for row in old_if["records"]:
    selection.setdefault(row["id"], []).append("archived_I_or_F_disagreement")
for ch in audit["necessary_changes"]:
    for ident in ch["evidence_ids"]:
        selection.setdefault(ident, []).append(ch["id"])
for row in audit["examples"]:
    if row.get("record_id") in frame:
        selection.setdefault(row["record_id"], []).append(row["example_id"])
# Preserve all named boundary cases instead of choosing by label balance or score.
assert set(selection) <= set(frame)
assert set(selection) <= excluded, "No fresh holdout ID may enter development"

source_manifest = json.loads((ROOT / "00-baseline/source_files_manifest.json").read_text())
source_path = next(Path(f["snapshot"]) for f in source_manifest["files"] if "model_source_file" in f["roles"])
sources = {row["id"]: row for row in map(json.loads, source_path.read_text().splitlines())}
trial = ROOT / "04-calibration/pilot01"
mapping = []
rows = []
for index, ident in enumerate(sorted(selection), 1):
    src = sources[ident]
    assert src["text"] == frame[ident]["unit_text"]
    blind_id = f"D{index:03d}"
    contexts = []
    for j, c in enumerate(src["contexts"], 1):
        if not isinstance(c.get("text"), str) or not c["text"].strip():
            continue  # Source-range geometry with no original text is not evidence.
        # Allowlist: pure original texts and source geometry, never review outcomes.
        contexts.append({"context_id": f"C{j:03d}", "kind": c["kind"],
                         "source_document": c.get("source_document"),
                         "structure": c.get("structure", {}), "text": c["text"]})
    packet = {"id": blind_id, "text": src["text"], "pages": src["pages"], "contexts": contexts}
    rows.append(packet)
    mapping.append({"blind_id": blind_id, "frame_id": ident,
                    "department": frame[ident]["analysis_group"],
                    "selection_reasons": selection[ident],
                    "historical_exposure_confirmed": True,
                    "unit_sha256": frame[ident]["unit_text_sha256"],
                    "context_id_map": {f"C{j:03d}": c["context_id"] for j, c in enumerate(src["contexts"], 1) if isinstance(c.get("text"), str) and c["text"].strip()},
                    "textless_context_metadata_omitted": [c for c in src["contexts"] if not isinstance(c.get("text"), str) or not c["text"].strip()],
                    "content_sha256": hashlib.sha256(canonical(packet).encode()).hexdigest()})

protocol = """# 独立开发判读操作说明

只读本目录材料包与指定共同手册；不要读取兄弟A/B目录、admin映射、旧标签或审查结论，不自行外部搜索。逐条按同一手册判断S/E/Ec/I/F；标0/1/null，并保存原文关系理由。材料有语境不代表全部继承；只引用实际用于当前命题的有限语境。不得为追求一致率改答案。

提交labels.jsonl：每行{"id":"D001","labels":{"S":0,"E":0,"Ec":0,"I":0,"F":0},"evidence":{"S":{"path":"excluded","current_quote":"原文","contexts_used":[],"reason":"理由"},"E":{...},"Ec":{...},"I":{...},"F":{...}},"material_requests":[]}。contexts_used每项{"context_id":"C001","quote":"连续原文","purpose":"补足何关系"}；每个1至少有当前锚点，I3/F具体路径在reason说明必要证据项。null的material_requests注明维度、缺失原文或规则冲突。0也说明最接近内容为何不成立。不得增加未提供的事实。

五维分别执行，不看其他编码员结果，不协商。完成后不覆盖labels.jsonl；新意见另存。另写submission.json记录实际模型、推理设置、开始/结束时间、输入文件SHA、记录数、任何访问范围偏离。身份为AI，用途为开发校准，非真人独立编码或总体效度检验。
"""
packet_hashes = {}
for coder, seed in [("A", 2026101001), ("B", 2026101002)]:
    coder_rows = rows.copy()
    random.Random(seed).shuffle(coder_rows)
    packet_path = trial / coder / "packet.jsonl"
    write_new(packet_path, "".join(canonical(row) + "\n" for row in coder_rows))
    write_new(trial / coder / "instructions.md", protocol)
    write_new(trial / coder / "manual.md", manual)
    packet_hashes[coder] = {"packet_sha256": sha(packet_path),
                            "manual_sha256": sha(trial / coder / "manual.md"),
                            "order_seed": seed, "ids": [r["id"] for r in coder_rows]}
write_json(trial / "admin/private_mapping.json", mapping)
write_json(trial / "admin/design.json", {
    "purpose": "development_execution_calibration", "independent_final_test": False,
    "human_execution": False, "n": len(rows),
    "selection": "all_named_archived_IF_disagreements_and_manual_boundary_evidence_no_label_filter",
    "already_exposed_only": True, "probability_sample": False,
    "same_current_text_context_and_manual_for_A_B": True,
    "identical_per_item_content_hash": True,
    "source": {"path": str(source_path), "sha256": sha(source_path)},
    "frame_allowlist_n": len(frame), "source_interface_rows": len(sources),
    "extra_GOV_records_not_selected": True,
    "input_bindings": packet_hashes,
    "model": "gpt-6.1-sol", "reasoning_effort": "ultra",
    "snapshot_time_utc": datetime.now(timezone.utc).isoformat()})
print(json.dumps({"manual": str(manual_path), "manual_sha256": sha(manual_path),
                  "pilot_n": len(rows), "department_counts": {g: sum(m["department"] == g for m in mapping) for g in ["NMPA", "NHSA", "NHC"]}}, ensure_ascii=False))
