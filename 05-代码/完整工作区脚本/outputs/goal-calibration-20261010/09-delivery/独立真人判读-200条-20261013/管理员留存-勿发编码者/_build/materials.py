"""Package frozen source materials mechanically; never draw or label records."""
from __future__ import annotations

import hashlib
import html
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


BUILD = Path(__file__).resolve().parent
ADMIN = BUILD.parent
OUT = ADMIN.parent
ROOT = OUT.parents[1]
COMMON = ROOT / "01-review/source-interface-v17-finite-source-addendum-root/common-frame-bundles-v17.jsonl"
PACKETS = ROOT / "01-review/source-interface-v17-finite-source-addendum-root/packet-bindings-v17.json"
COMMON_SHA = "0f248d9a5a8755e20875b88cecb521821b26b56a270beb2b866f0f4f4796a039"
PACKETS_SHA = "1ebca062a3b3e28b130bc747d770b832945b479ffba2f923f34fe0d7b93740ab"
BLIND_RE = re.compile(r"[A-Za-z0-9_-]+\Z")
RECODE_RE = re.compile(r"RECODE\d+-\d+")
ABS_RE = re.compile(r"(?:file://)?/Users/[^\s<>\"']+")

# Only presentation/administrative identifiers are suppressed. Policy strings
# and contextual resource contents otherwise flow through verbatim.
PRIVATE_KEYS = {
    "absolute_path", "path", "snapshot", "snapshot_relative_path",
    "snapshot_relative_to_projection", "original_path", "source_path",
    "relative_path", "relative_path_base", "source_locator_bases",
    "common_source_bundle_version", "unit_id", "source_id", "record_id",
    "original_blind_id", "A_blind_id", "B_blind_id", "stratum", "weight",
    "weight_exact", "pi", "pi_exact", "machine_prediction", "machine_predictions",
    "rule_prediction", "llm_prediction", "predictions", "labels", "gold",
}
ROOT_NAMES = {
    "source_documents": "来源文档",
    "explicit_or_primary_source_resources": "明确引用的原始资料",
    "source_full_text_resources": "补充原文资料",
    "source_reference_index": "来源索引",
    "source_provenance_addenda": "来源补充说明",
    "preserved_historical_neutral_source_supplements": "其他原文补充",
    "source_asset_locations": "原图与附件信息",
    "source_bundle_extension": "补充材料信息",
}
FIELD_NAMES = {
    "text": "原文", "source_texts": "原文内容", "source_document": "来源文档",
    "contexts": "上下文", "kind": "材料类型", "context_id": "上下文定位",
    "pages": "页码", "source_ref": "原文定位", "locator": "位置",
    "source_locator": "原文位置", "structure": "结构位置", "paragraph_id": "段落位置",
    "paragraph_ids": "段落位置", "physical_page": "PDF页码", "physical_pages": "PDF页码",
    "printed_page": "文内页码", "document_title": "文档标题", "document_year": "文档年份",
    "heading_path": "标题层次", "paragraphs": "段落", "source_title_actual_page_read": "来源标题",
    "source_title_lines_verbatim_extraction_candidates": "来源标题文字",
    "source_resource_id": "来源标识", "source_version_id": "来源版本",
    "source_text_resource": "原文资源信息", "source_page_assets": "来源页面信息",
    "source_display_regions": "来源图表区域", "source_regions": "来源区域",
    "source_visual_text_resources": "图文资料", "source_title_visual_evidence": "标题图文资料",
    "source_texts": "原文内容", "source_attachments": "附件信息",
}
BODY_STYLE = """body{font:16px/1.75 -apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif;color:#253244;background:#f5f7fa;margin:0}main{max-width:1040px;margin:24px auto;padding:30px 38px;background:#fff;border:1px solid #dce2e9;border-radius:12px}h1{font-size:28px;margin:0 0 12px}h2{font-size:21px;border-bottom:2px solid #dfe8ef;padding-bottom:8px;margin-top:32px}h3{font-size:18px}a{color:#175c95}nav,.hint{font-size:14px;color:#58697b}.hint{background:#f0f5f8;padding:12px 16px;border-left:4px solid #416f8f}.literal{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit;background:#fafbfc;padding:10px 14px;margin:8px 0;border:1px solid #e7ebef;border-radius:4px}.body{font-size:18px;background:#f8fbfd;border-color:#cddce8}dl{margin:8px 0 18px}dt{font-weight:600;margin-top:12px;color:#41536a}dd{margin-left:14px}ol{padding-left:24px}li{margin:10px 0}details{border:1px solid #dce3ea;border-radius:6px;margin:12px 0;padding:10px 14px}summary{cursor:pointer;font-weight:600}img{max-width:100%;height:auto;border:1px solid #dfe4e9;margin:12px 0}.small{font-size:13px;color:#67778a}.file-list{list-style:none;padding:0}.file-list li{padding:8px 12px;background:#f7f9fb}code{font-size:12px;overflow-wrap:anywhere}@media(max-width:700px){main{margin:0;padding:20px 16px;border-radius:0}h1{font-size:24px}}"""


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def binding(path: Path) -> dict:
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": sha(raw)}


def put(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError(f"Refusing to overwrite a different existing file: {path}")
        return
    with path.open("xb") as stream:
        stream.write(raw)


def save(path: Path, value: object) -> None:
    put(path, (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode())


def safe_string(value: str) -> str:
    return ABS_RE.sub("［本地来源路径已隐藏］", RECODE_RE.sub("［材料身份已隐藏］", value))


def project(value: object) -> object:
    if isinstance(value, str):
        return safe_string(value)
    if isinstance(value, list):
        return [project(item) for item in value]
    if isinstance(value, dict):
        return {
            key: project(item) for key, item in value.items()
            if key not in PRIVATE_KEYS and not (key == "id" and isinstance(item, str) and RECODE_RE.search(item))
        }
    return value


def pointer_part(key: object) -> str:
    return str(key).replace("~", "~0").replace("/", "~1")


def render(value: object, pointer: str = "") -> str:
    if isinstance(value, str):
        return f'<div class="literal" data-pointer="{html.escape(pointer, quote=True)}">{html.escape(value)}</div>'
    if isinstance(value, list):
        if not value:
            return '<span class="small">无</span>'
        return "<ol>" + "".join(f"<li>{render(item, pointer + '/' + str(index))}</li>" for index, item in enumerate(value)) + "</ol>"
    if isinstance(value, dict):
        return "<dl>" + "".join(
            f"<dt>{html.escape(FIELD_NAMES.get(key, key))}</dt><dd>{render(item, pointer + '/' + pointer_part(key))}</dd>"
            for key, item in value.items()
        ) + "</dl>"
    if value is None:
        return '<span class="small">未提供</span>'
    return '<span class="small">' + html.escape(json.dumps(value, ensure_ascii=False)) + "</span>"


def collect_assets(bundle: dict, cache: dict) -> list[dict]:
    base = Path(bundle["source_locator_bases"]["canonical_row_attachment_relative_path_base"])
    seen: dict[str, dict] = {}

    def add(path: str | Path, expected: str | None, pointer: str, kind: str) -> None:
        candidate = Path(path).resolve()
        if not expected or not re.fullmatch(r"[a-f0-9]{64}", expected):
            raise ValueError(f"Asset has no valid SHA at {pointer}: {candidate}")
        key = (str(candidate), expected)
        if key not in cache:
            raw = candidate.read_bytes()
            if sha(raw) != expected:
                raise ValueError(f"Asset SHA mismatch: {candidate}")
            cache[key] = raw
        raw = cache[key]
        if expected not in seen:
            seen[expected] = {"sha256": expected, "bytes": len(raw), "path": str(candidate),
                              "suffix": candidate.suffix.lower() or ".bin", "original_paths": [], "pointers": [], "kinds": []}
        entry = seen[expected]
        if str(candidate) not in entry["original_paths"]:
            entry["original_paths"].append(str(candidate))
        if pointer not in entry["pointers"]:
            entry["pointers"].append(pointer)
        if kind not in entry["kinds"]:
            entry["kinds"].append(kind)

    def walk(value: object, pointer: str = "") -> None:
        if isinstance(value, dict):
            for key in ("absolute_path", "path"):
                if isinstance(value.get(key), str) and value.get("sha256"):
                    add(value[key], value["sha256"], pointer, key)
            if isinstance(value.get("snapshot"), str):
                add(value["snapshot"], value.get("snapshot_sha256", value.get("sha256", value.get("source_sha256"))), pointer, "snapshot")
            if isinstance(value.get("source_path"), str):
                add(value["source_path"], value.get("source_sha256"), pointer, "source_path")
            if isinstance(value.get("relative_path"), str) and value.get("sha256"):
                add(Path(value.get("relative_path_base", str(base))) / value["relative_path"], value["sha256"], pointer, "relative_path")
            if isinstance(value.get("snapshot_relative_path"), str):
                add(base / "source-library" / value["snapshot_relative_path"], value.get("snapshot_sha256"), pointer, "snapshot_relative_path")
            for key, item in value.items():
                walk(item, pointer + "/" + pointer_part(key))
        elif isinstance(value, list):
            for index, item in enumerate(value):
                walk(item, pointer + "/" + str(index))

    walk(bundle)
    return list(seen.values())


def prepare_asset(entry: dict, cache: dict) -> tuple[bytes, str, bool]:
    raw = cache[(entry["path"], entry["sha256"])]
    # PDFs and images remain byte-exact. Structured source-provenance attachments
    # are mechanically projected only if they expose administrator identifiers.
    try:
        decoded = raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw, entry["suffix"], False
    if not RECODE_RE.search(decoded) and "/Users/" not in decoded and "file://" not in decoded:
        return raw, entry["suffix"], False
    try:
        parsed = json.loads(decoded)
    except json.JSONDecodeError:
        if entry["suffix"] == ".jsonl":
            parsed_lines = [json.loads(line) for line in decoded.splitlines() if line.strip()]
            projected = "".join(json.dumps(project(item), ensure_ascii=False, separators=(",", ":")) + "\n" for item in parsed_lines)
        else:
            projected = safe_string(decoded)
    else:
        projected = json.dumps(project(parsed), ensure_ascii=False, indent=2) + "\n"
    encoded = projected.encode()
    if RECODE_RE.search(projected) or "/Users/" in projected:
        raise ValueError("Private identifiers remained in projected source attachment")
    return encoded, entry["suffix"], encoded != raw


def page(blind: str, bundle: dict, asset_entries: list[dict]) -> tuple[str, int]:
    projected = project(bundle)
    record = projected["source_record"]
    body = record["text"]
    contexts = record.get("contexts", [])
    if body != bundle["source_record"]["text"]:
        raise ValueError("Administrative projection changed current policy text")
    for original, delivered in zip(bundle["source_record"].get("contexts", []), contexts):
        if original.get("text") != delivered.get("text"):
            raise ValueError("Administrative projection changed context text")
    sections = []
    for key, item in projected.items():
        if key in {"source_record", "source_asset_locations"} or not item:
            continue
        title = ROOT_NAMES.get(key, key)
        sections.append(f'<section><h2>{html.escape(title)}</h2>{render(item, "/" + pointer_part(key))}</section>')
    other_record = {key: item for key, item in record.items() if key not in {"text", "contexts"}}
    if other_record:
        sections.append('<details><summary>当前条款的原文定位与附件信息</summary>' + render(other_record, "/source_record") + "</details>")
    if projected.get("source_asset_locations"):
        sections.append('<details><summary>原图与附件的来源信息</summary>' + render(projected["source_asset_locations"], "/source_asset_locations") + "</details>")
    links = []
    images = []
    for index, entry in enumerate(asset_entries, 1):
        relative = "../附件/" + entry["delivery_filename"]
        suffix = entry["delivery_suffix"].lstrip(".").upper()
        label = f"来源文件 {index}（{suffix}）"
        links.append(f'<li><a href="{html.escape(relative, quote=True)}">{label}</a></li>')
        if entry["delivery_suffix"] in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
            images.append(f'<figure><figcaption>{label}</figcaption><a href="{html.escape(relative, quote=True)}"><img loading="lazy" src="{html.escape(relative, quote=True)}" alt="{label}"></a></figure>')
    content = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{blind}｜完整判读材料</title><style>{BODY_STYLE}</style></head><body><main>
<nav><a href="../材料目录.html">返回材料目录</a> · <a href="../共同编码手册.txt">共同编码手册</a></nav>
<h1>{blind} · 完整判读材料</h1>
<p class="hint">先阅读当前条款，再结合必要上下文、原文资料和原图，按照共同手册独立填写五个维度。材料页没有预设答案。</p>
<h2>当前条款正文</h2><div id="current-body" class="literal body">{html.escape(body)}</div>
<h2>完整上下文</h2>{render(contexts, '/source_record/contexts')}
{''.join(sections)}
<section><h2>可打开的原始文件与附件</h2><ul class="file-list">{''.join(links)}</ul>{''.join(images)}</section>
</main></body></html>'''
    if RECODE_RE.search(content) or "/Users/" in content:
        raise ValueError("Private identifiers remained in material HTML")
    return content, len(contexts)


def main() -> None:
    audit_path = ADMIN / "materials-audit.json"
    if audit_path.exists():
        raise RuntimeError("Materials already packaged; do not rerun a sealed build")
    draw_path = ADMIN / "draw.json"
    assignments_path = ADMIN / "blind-assignment.json"
    draw = json.loads(draw_path.read_text())
    assignments = json.loads(assignments_path.read_text())
    records = draw["records"]
    selected = [record["unit_id"] for record in records]
    if len(selected) != 200 or len(set(selected)) != 200:
        raise ValueError("Expected exactly 200 distinct frozen draw records")
    common_raw = COMMON.read_bytes()
    if sha(common_raw) != COMMON_SHA or binding(PACKETS)["sha256"] != PACKETS_SHA:
        raise ValueError("Current source freeze SHA mismatch")
    packet_by_id = {item["source_id"]: item for item in json.loads(PACKETS.read_text())}
    selected_set = set(selected)
    bundles, raw_bundles = {}, {}
    for line in common_raw.splitlines():
        bundle = json.loads(line)
        unit_id = bundle["source_record"]["id"]
        if unit_id not in selected_set:
            continue
        if sha(line) != packet_by_id[unit_id]["source_bundle_sha256"]:
            raise ValueError("Selected raw source bundle SHA mismatch")
        bundles[unit_id] = bundle
        raw_bundles[unit_id] = line
        put(ADMIN / "原始源束" / (unit_id + ".json"), line)
    if set(bundles) != selected_set:
        raise ValueError("The current source lacks drawn records")
    cache, raw_assets, assets_by_unit = {}, {}, {}
    for unit_id in selected:
        entries = collect_assets(bundles[unit_id], cache)
        assets_by_unit[unit_id] = [entry["sha256"] for entry in entries]
        for entry in entries:
            digest = entry["sha256"]
            if digest in raw_assets:
                continue
            raw = cache[(entry["path"], digest)]
            put(ADMIN / "原始来源附件" / (digest + entry["suffix"]), raw)
            delivered, suffix, modified = prepare_asset(entry, cache)
            raw_assets[digest] = {**entry, "delivery_sha256": sha(delivered), "delivery_bytes": len(delivered),
                                  "delivery_filename": digest + suffix, "delivery_suffix": suffix,
                                  "administrative_fields_projected": modified, "_delivery_bytes": delivered}
    pages, side_reports = [], {}
    for side in ("A", "B"):
        side_rows = assignments["methods"][side]
        if [row["unit_id"] for row in side_rows] != selected:
            raise ValueError(f"Side {side} order differs from frozen draw order")
        if len({row["original_blind_id"] for row in side_rows}) != 200:
            raise ValueError("Duplicated blind identifiers")
        coder = OUT / ("发给编码者" + side)
        asset_manifest = []
        for entry in raw_assets.values():
            put(coder / "附件" / entry["delivery_filename"], entry["_delivery_bytes"])
            asset_manifest.append({key: entry[key] for key in ("sha256", "delivery_sha256", "delivery_filename", "delivery_bytes", "administrative_fields_projected")})
        index_links = []
        for row in side_rows:
            unit_id, blind = row["unit_id"], row["original_blind_id"]
            if not BLIND_RE.fullmatch(blind):
                raise ValueError("Unsafe blind identifier for material filename")
            if row["source_bundle_sha256"] != sha(raw_bundles[unit_id]):
                raise ValueError("Blind map and source bundle SHA differ")
            entries = [raw_assets[digest] for digest in assets_by_unit[unit_id]]
            content, context_n = page(blind, bundles[unit_id], entries)
            target = coder / "材料" / (blind + ".html")
            put(target, content.encode())
            index_links.append(f'<li><a href="材料/{blind}.html">{blind}</a></li>')
            pages.append({"side": side, "blind_id": blind, "unit_id": unit_id,
                          "source_bundle_sha256": row["source_bundle_sha256"],
                          "material_locator": row["material_locator"], "html": binding(target),
                          "body_utf8_sha256": sha(bundles[unit_id]["source_record"]["text"].encode()),
                          "context_N": context_n, "asset_source_SHAs": assets_by_unit[unit_id]})
        index = f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>编码者{side}材料目录</title><style>{BODY_STYLE}ol{{columns:4}}@media(max-width:700px){{ol{{columns:2}}}}</style></head><body><main><h1>编码者{side} · 200条材料目录</h1><p><a href="共同编码手册.txt">共同编码手册</a> · <a href="填写说明.txt">填写说明</a></p><p class="hint">盲号与本方填写表逐条对应。请按填写表顺序独立判读。</p><ol>{"".join(index_links)}</ol></main></body></html>'
        put(coder / "材料目录.html", index.encode())
        side_reports[side] = {"material_page_N": 200, "unique_asset_N": len(raw_assets), "source_asset_bindings": asset_manifest}
    # Validate all intended relative material links, except documents owned by
    # the main workbook builder, which may be copied after this subprocess.
    from html.parser import HTMLParser
    class LinkCollector(HTMLParser):
        def __init__(self):
            super().__init__(); self.targets = []
        def handle_starttag(self, tag, attrs):
            for key, value in attrs:
                if key in {"href", "src"} and value:
                    self.targets.append(value)
    linked_n, pending_main = 0, []
    for side in ("A", "B"):
        coder = OUT / ("发给编码者" + side)
        for file in [coder / "材料目录.html", *sorted((coder / "材料").glob("*.html"))]:
            collector = LinkCollector(); collector.feed(file.read_text())
            for value in collector.targets:
                resolved = (file.parent / value).resolve()
                if coder.resolve() not in resolved.parents:
                    raise ValueError(f"Link escaped reviewer package: {file}: {value}")
                if not resolved.is_file():
                    if resolved.name in {"共同编码手册.txt", "填写说明.txt"}:
                        pending_main.append(str(resolved)); continue
                    raise ValueError(f"Broken material link: {file}: {value}")
                linked_n += 1
    manifest = {"created_at_utc": datetime.now(timezone.utc).isoformat(), "draw": binding(draw_path),
                "blind_assignment": binding(assignments_path), "current_common": binding(COMMON),
                "current_packets": binding(PACKETS), "pages": pages,
                "assets": [{key: item for key, item in entry.items() if key != "_delivery_bytes"} for entry in raw_assets.values()],
                "sides": side_reports}
    save(ADMIN / "materials-manifest.json", manifest)
    save(audit_path, {"status": "packaged_materials_links_verified", "created_at_utc": datetime.now(timezone.utc).isoformat(),
                     "selected_record_N": 200, "material_page_N": len(pages), "unique_source_asset_N": len(raw_assets),
                     "raw_bundles_SHA_verified_N": len(raw_bundles), "raw_source_assets_SHA_verified_N": len(raw_assets),
                     "administrative_attachment_projection_N": sum(entry["administrative_fields_projected"] for entry in raw_assets.values()),
                     "reachable_local_link_N": linked_n, "pending_main_builder_documents": sorted(set(pending_main)),
                     "labels_generated_N": 0, "model_calls": 0, "draw_performed": False,
                     "policy_text_semantic_adjudication_performed": False,
                     "raw_bundle_original_bytes_preserved": True, "HTML_private_identifier_scan_passed": True,
                     "builder": binding(Path(__file__)), "manifest": binding(ADMIN / "materials-manifest.json")})
    print(json.dumps({"status": "materials_ready", "material_pages": len(pages), "unique_assets": len(raw_assets),
                      "projected_administrative_attachments": sum(entry["administrative_fields_projected"] for entry in raw_assets.values()),
                      "pending_main_builder_documents": sorted(set(pending_main))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
