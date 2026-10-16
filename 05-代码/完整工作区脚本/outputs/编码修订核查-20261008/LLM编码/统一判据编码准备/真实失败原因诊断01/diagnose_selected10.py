"""Read only ten preselected first failures; diagnostics only, no binder/coder."""
import hashlib
import io
import json
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET
from lxml import html, etree

HERE = Path(__file__).resolve().parent
PUNCT = {"，": ",", "（": "(", "）": ")", "：": ":", "；": ";", "！": "!", "？": "?", "［": "[", "］": "]", "．": "."}
ROMAN = {"Ⅰ": "I", "Ⅱ": "II", "Ⅲ": "III", "Ⅳ": "IV", "Ⅴ": "V", "Ⅵ": "VI", "Ⅶ": "VII", "Ⅷ": "VIII", "Ⅸ": "IX", "Ⅹ": "X"}
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def digest(data):
    return hashlib.sha256(data.encode() if isinstance(data, str) else data).hexdigest()


def exclusive(path, value):
    if isinstance(value, bytes):
        with path.open("xb") as stream:
            stream.write(value)
    else:
        with path.open("x", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")


def canon(text, punctuation=False, roman=False):
    value, mapping = "", []
    for i, char in enumerate(text):
        if char.isspace():
            continue
        piece = ROMAN.get(char, char) if roman else char
        piece = PUNCT.get(piece, piece) if punctuation else piece
        value += piece
        mapping += [i] * len(piece)
    return value, mapping


def exact_probe(text, leaf, punctuation=False, roman=False):
    original, mapping = canon(text, punctuation, roman)
    target, target_mapping = canon(leaf, punctuation, roman)
    out, start = [], 0
    while target and (index := original.find(target, start)) >= 0:
        indexes = mapping[index:index + len(target)]
        a, b = indexes[0], indexes[-1] + 1
        out.append({"source_start": a, "source_end": b, "source_span": text[a:b],
                    "source_character_index_per_compared_character": indexes,
                    "leaf_character_index_per_compared_character": target_mapping,
                    "source_nonidentical_characters": [{"source_index": si, "leaf_index": li,
                        "source_character": text[si], "source_codepoint": f"U+{ord(text[si]):04X}",
                        "leaf_character": leaf[li], "leaf_codepoint": f"U+{ord(leaf[li]):04X}"}
                        for si, li in zip(indexes, target_mapping) if text[si] != leaf[li]],
                    "source_whitespace_in_span": [{"index": k, "character": text[k], "codepoint": f"U+{ord(text[k]):04X}"} for k in range(a, b) if text[k].isspace()],
                    "leaf_whitespace": [{"index": k, "character": c, "codepoint": f"U+{ord(c):04X}"} for k, c in enumerate(leaf) if c.isspace()]})
        start = index + 1
    return out


def tool_run(command):
    proc = subprocess.run(command, capture_output=True, timeout=60)
    metadata = {"command": command, "exit_code": proc.returncode, "stdout_sha256": digest(proc.stdout),
                "stderr_sha256": digest(proc.stderr), "executable_path": str(Path(command[0]).resolve()),
                "executable_sha256": digest(Path(command[0]).read_bytes())}
    if proc.returncode:
        raise RuntimeError("diagnostic_extractor_failed:" + json.dumps(metadata))
    return proc.stdout, metadata


def xml_tag(element):
    return element.tag.split("}")[-1]


def extract_source(path, selected_pages, file_number):
    suffix = path.suffix.lower()
    source = {"path": str(path), "source_sha256": digest(path.read_bytes()), "carriers": []}
    if suffix == ".pdf":
        data, tool = tool_run(["/opt/homebrew/bin/pdftotext", "-bbox-layout", str(path), "-"])
        artifact = HERE / f"source_{file_number:02d}_bbox.xml"
        exclusive(artifact, data)
        root = ET.fromstring(data)
        pages = [n for n in root.iter() if xml_tag(n) == "page"]
        source.update(extraction=tool, bbox_artifact=str(artifact), page_n=len(pages), all_page_text_sha256={})
        for pi, page in enumerate(pages, 1):
            text, lines = "", []
            for li, line in enumerate(n for n in page.iter() if xml_tag(n) == "line"):
                words = [{"text": "".join(w.itertext()), "bbox": dict(w.attrib)} for w in line if xml_tag(w) == "word"]
                native_text = " ".join(w["text"] for w in words)
                lines.append({"line_index_zero_based": li, "start": len(text), "end": len(text) + len(native_text), "text": native_text, "words": words})
                text += native_text + "\n"
            source["all_page_text_sha256"][str(pi)] = digest(text)
            if pi in selected_pages:
                source["carriers"].append({"kind": "explicit_pdf_page", "page_one_based": pi, "text": text, "native_lines": lines})
    elif suffix == ".txt":
        raw = path.read_bytes();text = raw.decode("utf-8", errors="strict")
        assert text.encode("utf-8") == raw
        source["carriers"].append({"kind": "strict_utf8_native_file", "text": text})
    elif suffix in {".html", ".htm"}:
        data = path.read_bytes();data.decode("utf-8", errors="strict")
        tree = html.fromstring(data)
        for node in tree.xpath("//p|//td|//th"):
            source["carriers"].append({"kind": "native_html_element", "xpath": node.getroottree().getpath(node),
                "source_line": node.sourceline, "tag": node.tag, "text": node.text_content(),
                "serialized_node": etree.tostring(node, encoding="unicode"),
                "node_extractor": "lxml.html diagnostic element text; not binder authentication"})
    elif suffix == ".doc":
        flat, tool = tool_run(["/usr/bin/textutil", "-convert", "txt", "-encoding", "UTF-8", "-stdout", str(path)])
        source.update(flat_extraction=tool)
        source["carriers"].append({"kind": "textutil_flat_conversion", "text": flat.decode("utf-8", errors="strict")})
        data, tool = tool_run(["/usr/bin/textutil", "-convert", "docx", "-stdout", str(path)])
        artifact = HERE / f"source_{file_number:02d}_diagnostic_conversion.docx"
        exclusive(artifact, data)
        source.update(structured_conversion_extraction=tool, converted_docx_artifact=str(artifact), converted_docx_sha256=digest(data))
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            xml = archive.read("word/document.xml")
        tree = etree.fromstring(xml)
        source["converted_xml_sha256"] = digest(xml)
        for p in tree.xpath("//w:p[not(ancestor::w:tbl)]", namespaces=NS):
            source["carriers"].append({"kind": "DOC_to_DOCX_converted_paragraph", "xpath": tree.getroottree().getpath(p),
                "text": "".join(p.xpath(".//w:t/text()", namespaces=NS)),
                "conversion_structure_certified": False})
        source["converted_tables"] = []
        for table in tree.xpath("//w:tbl[not(ancestor::w:tbl)]", namespaces=NS):
            rows = []
            for row in table.xpath("./w:tr", namespaces=NS):
                cells = [{"xpath": tree.getroottree().getpath(cell), "text": "\n".join("".join(p.xpath(".//w:t/text()", namespaces=NS)) for p in cell.xpath("./w:p", namespaces=NS))} for cell in row.xpath("./w:tc", namespaces=NS)]
                rows.append({"xpath": tree.getroottree().getpath(row), "cells": cells})
            source["converted_tables"].append({"xpath": tree.getroottree().getpath(table), "rows": rows, "conversion_structure_certified": False})
    else:
        raise RuntimeError("unselected_format:" + suffix)
    return source


def run():
    cases = json.loads((HERE / "selected_case_materials01.json").read_text())
    paths = list(dict.fromkeys(x["plan"]["source_identity"]["source_path"] for x in cases))
    sources = []
    for i, p in enumerate(paths, 1):
        pages = {x["plan"]["source_locator"]["page_one_based"] for x in cases if x["plan"]["source_identity"]["source_path"] == p and "page_one_based" in x["plan"]["source_locator"]}
        sources.append(extract_source(Path(p), pages, i))
    exclusive(HERE / "native_source_extracts01.json", sources)
    actual = []
    for case in cases:
        source = next(s for s in sources if s["path"] == case["plan"]["source_identity"]["source_path"])
        scoped = source["carriers"]
        if case["plan"]["source_locator"].get("page_one_based"):
            scoped = [c for c in scoped if c.get("page_one_based") == case["plan"]["source_locator"]["page_one_based"]]
        probes = {}
        for name, punctuation, roman in (("whitespace_only", False, False), ("explicit_punctuation_and_whitespace", True, False), ("diagnostic_explicit_Roman_glyphs_plus_punctuation_and_whitespace", True, True)):
            hits = []
            for ci, carrier in enumerate(scoped):
                for match in exact_probe(carrier["text"], case["leaf"], punctuation, roman):
                    hits.append({"carrier_index_in_scoped_source": ci, "carrier_kind": carrier["kind"], "carrier_locator": {k:v for k,v in carrier.items() if k in ("page_one_based", "xpath", "source_line", "tag")}, **match})
            probes[name] = hits
        actual.append({"id": case["id"], "raw_pointer": case["raw_pointer"], "occurrence_index_one_based": case["occurrence_index_one_based"],
            "source_path": source["path"], "source_sha256": source["source_sha256"], "candidate_path": case["plan"]["candidate_identity"]["candidate_path"],
            "candidate_sha256": case["candidate_actual_sha256"], "leaf": case["leaf"], "probes": probes,
            "authentication_performed": False, "first_binding_status_unchanged": "binder_unbound", "formal_model_input_ready": False})
    exclusive(HERE / "diagnostic_exact_mapping_evidence01.json", {"schema": "selected-first-failure-diagnostic-mappings01-v1", "at_utc": datetime.now(timezone.utc).isoformat(),
        "script_sha256": digest(Path(__file__).read_bytes()), "punctuation_probe_map": PUNCT, "Roman_probe_map": ROMAN,
        "meaning": "Finite diagnostic exact equality under explicit logged character transformations, with original character indices. Never a source/coding authentication result; no NFKC or approximate similarity.", "cases": actual})
    print(json.dumps({"n": len(actual), "cases": [{"id": x["id"], "pointer": x["raw_pointer"], "index": x["occurrence_index_one_based"], "probe_counts": {k: len(v) for k,v in x["probes"].items()}, "matched_source_span": next((v[0]["source_span"] for v in x["probes"].values() if v), None)} for x in actual]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    run()
