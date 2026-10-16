"""Read-only, one-leaf positional binding; CLI is invented self-tests only.

Never imports policy coders or loads a corpus/reference file. Outputs contain
identities and positions, not policy text. No legacy verification is trusted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from html.parser import HTMLParser
from pathlib import Path

VERSION = "literal-source-position-binder03"
BOUND = "literal_source_and_candidate_position_bound"
GRID_BOUND = "structured_grid_literal_bound_image_bytes_only_not_visual_revalidated"
UNBOUND = "unbound_policy_leaf"
HEX = re.compile(r"^[0-9a-f]{64}$")
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


class BindingError(Exception):
    pass


def digest(value):
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def file_sha(path):
    return digest(Path(path).read_bytes())


def require(condition, code):
    if not condition:
        raise BindingError(code)


def integer(value):
    return type(value) is int and value >= 0


def paired_identity(node, *, candidate=False):
    """A supplied partial layer fails; no inheritance or member mixing."""
    require(isinstance(node, dict), "identity_not_object")
    if candidate:
        keys = [k for k in ("candidate_path", "candidate_file") if k in node]
        require(len(keys) == 1 and "candidate_sha256" in node, "candidate_pair_incomplete_or_ambiguous")
        path, sha = node[keys[0]], node["candidate_sha256"]
        fields = [keys[0], "candidate_sha256"]
    else:
        unit_present = any(k in node for k in ("unit_source", "unit_source_sha256"))
        generic_present = any(k in node for k in ("source_path", "source", "source_sha256"))
        if unit_present:
            require(bool(node.get("unit_source")) and bool(node.get("unit_source_sha256")), "unit_source_pair_incomplete")
        if generic_present:
            require(bool(node.get("source_path") or node.get("source")) and bool(node.get("source_sha256")), "source_pair_incomplete")
        require(unit_present or generic_present, "source_pair_missing")
        if unit_present:
            path, sha, fields = node["unit_source"], node["unit_source_sha256"], ["unit_source", "unit_source_sha256"]
        else:
            key = "source_path" if node.get("source_path") else "source"
            path, sha, fields = node[key], node["source_sha256"], [key, "source_sha256"]
    require(isinstance(path, str) and bool(path), "identity_path_invalid")
    require(isinstance(sha, str) and HEX.fullmatch(sha), "identity_sha_invalid")
    actual_path = Path(path).expanduser().resolve()
    require(actual_path.is_file(), "identity_file_missing")
    actual_sha = file_sha(actual_path)
    require(actual_sha == sha, "candidate_sha_mismatch" if candidate else "source_sha_mismatch")
    image = None
    if any(k in node for k in ("source_image", "source_image_sha256")):
        image = image_identity(node, base=actual_path.parent)
    return {"path": str(actual_path), "sha256": sha, "pair_fields": fields, "image": image}


def image_identity(node, *, base, grid=False):
    path = node.get("source_image")
    sha_key = "source_image_sha256" if "source_image_sha256" in node else "source_sha256" if grid else "source_image_sha256"
    expected = node.get(sha_key)
    require(isinstance(path, str) and path and isinstance(expected, str) and HEX.fullmatch(expected), "image_pair_incomplete")
    image = Path(path).expanduser()
    image = (base / image).resolve() if not image.is_absolute() else image.resolve()
    require(image.is_file(), "image_file_missing")
    require(file_sha(image) == expected, "image_sha_mismatch")
    return {"path": str(image), "sha256": expected, "hash_field": sha_key,
            "image_bytes_bound": True, "visual_transcription_revalidated": False}


def occurrences(text, leaf, *, whitespace=False):
    found, start = [], 0
    while (index := text.find(leaf, start)) >= 0:
        found.append({"start": index, "end": index + len(leaf), "matching": "exact"})
        start = index + 1
    if found or not whitespace:
        return found
    original = [i for i, char in enumerate(text) if not char.isspace()]
    normalized = "".join(text[i] for i in original)
    target = "".join(c for c in leaf if not c.isspace())
    if not target:
        return []
    start = 0
    while (index := normalized.find(target, start)) >= 0:
        indexes = original[index:index + len(target)]
        found.append({"start": indexes[0], "end": indexes[-1] + 1,
                      "matching": "whitespace_only_reversible",
                      "normalized_character_to_original_index": indexes})
        start = index + 1
    return found


def choose_occurrence(matches, locator):
    locator = locator or {}
    original_count = len(matches)
    if "char_start" in locator:
        require(integer(locator["char_start"]), "source_char_start_invalid")
        matches = [m for m in matches if m["start"] == locator["char_start"]]
    if "occurrence_index" in locator:
        i = locator["occurrence_index"]
        require(integer(i) and i < len(matches), "source_occurrence_index_invalid")
        selected = matches[i]
    else:
        require(len(matches) != 0, "source_literal_absent")
        require(len(matches) == 1, "source_literal_ambiguous")
        selected = matches[0]
    selected = dict(selected)
    selected["matching_occurrence_count_before_locator"] = original_count
    return selected


def span_meta(text, span, *, encoding="utf-8", byte_base=0):
    a, b = span["start"], span["end"]
    result = dict(span)
    result.update({"container_text_sha256": digest(text), "container_character_n": len(text),
                   "line_start_one_based": text.count("\n", 0, a) + 1,
                   "line_end_one_based": text.count("\n", 0, max(a, b - 1)) + 1,
                   "utf8_byte_start": len(text[:a].encode("utf-8")),
                   "utf8_byte_end": len(text[:b].encode("utf-8"))})
    if encoding:
        result["source_byte_start"] = byte_base + len(text[:a].encode(encoding))
        result["source_byte_end"] = byte_base + len(text[:b].encode(encoding))
        result["source_encoding"] = encoding
    return result


def exact_subspan(text, leaf, start=None, code="candidate_leaf"):
    require(isinstance(text, str), code + "_container_not_text")
    matches = occurrences(text, leaf)
    if start is not None:
        require(integer(start), code + "_start_invalid")
        matches = [m for m in matches if m["start"] == start]
    require(len(matches) != 0, code + "_absent")
    require(len(matches) == 1, code + "_ambiguous")
    return span_meta(text, matches[0])


def source_relation(candidate, unit, selected, candidate_dir):
    """Only explicit complete native source identities; never filename meaning."""
    for node in (unit or {}, candidate):
        possible = []
        if any(k in node for k in ("unit_source", "unit_source_sha256")):
            require(node.get("unit_source") and node.get("unit_source_sha256"), "candidate_unit_source_pair_incomplete")
            possible.append((node["unit_source"], node["unit_source_sha256"]))
        if any(k in node for k in ("source", "source_path", "source_sha256")):
            require((node.get("source_path") or node.get("source")) and node.get("source_sha256"), "candidate_source_pair_incomplete")
            possible.append((node.get("source_path") or node["source"], node["source_sha256"]))
        for path, sha in possible:
            require(isinstance(path, str) and isinstance(sha, str), "candidate_source_identity_type")
            native = Path(path).expanduser()
            native = (candidate_dir / native).resolve() if not native.is_absolute() else native.resolve()
            if str(native) == selected["path"] and sha == selected["sha256"]:
                return {"relation": "explicit_candidate_source_path_and_sha_equal", "source_path": str(native), "source_sha256": sha}
    if "additional_sources" in candidate:
        entries = candidate["additional_sources"]
        require(isinstance(entries, list), "candidate_additional_sources_not_list")
        matching_paths = []
        for index, entry in enumerate(entries):
            require(isinstance(entry, dict) and isinstance(entry.get("path"), str) and entry["path"]
                    and isinstance(entry.get("sha256"), str) and HEX.fullmatch(entry["sha256"]),
                    "candidate_additional_source_pair_incomplete_or_invalid")
            native = Path(entry["path"]).expanduser()
            native = (candidate_dir / native).resolve() if not native.is_absolute() else native.resolve()
            if str(native) == selected["path"]:
                matching_paths.append((index, entry["sha256"]))
        require(len(matching_paths) <= 1, "candidate_additional_source_path_duplicate_or_conflicting")
        if matching_paths:
            index, sha = matching_paths[0]
            require(sha == selected["sha256"], "candidate_additional_source_sha_mismatch")
            return {"relation": "explicit_candidate_additional_source_path_and_sha_equal",
                    "candidate_source_json_pointer": f"/additional_sources/{index}",
                    "source_path": selected["path"], "source_sha256": sha}
    raise BindingError("candidate_selected_source_relation_missing")


def candidate_position(candidate, locator, leaf):
    require(isinstance(locator, dict), "candidate_locator_missing")
    require(set(locator) <= {"leaf_scope", "representation", "unit_id", "paragraph_id", "unit_start_in_paragraph", "leaf_start", "pages", "source_lines", "table_index"}, "candidate_locator_field_unsupported")
    scope = locator.get("leaf_scope")
    require(scope in {"unit", "unit_subspan", "paragraph", "table_field"}, "candidate_leaf_scope_invalid")
    require(locator.get("representation", "natural_text") in {"natural_text", "structured_table_row"}
            if isinstance(locator.get("representation", "natural_text"), str) else False, "candidate_representation_invalid")
    for key in ("unit_id", "paragraph_id"):
        if key in locator:
            require(isinstance(locator[key], str) and bool(locator[key]), "candidate_id_type_invalid")
    require("unit_start_in_paragraph" not in locator or "unit_id" in locator, "candidate_unit_offset_without_unit")
    if "leaf_start" in locator and scope in {"unit", "table_field"}:
        require(scope == "unit" and type(locator["leaf_start"]) is int and locator["leaf_start"] == 0, "candidate_leaf_offset_not_applicable")
    unit = para = None
    result = {"leaf_scope": scope, "representation": locator.get("representation", "natural_text")}
    if "unit_id" in locator:
        units = [(i, u) for i, u in enumerate(candidate.get("unit_candidates", []))
                 if isinstance(u, dict) and u.get("id") == locator["unit_id"]]
        require(len(units) == 1, "candidate_unit_id_missing_or_duplicate")
        ui, unit = units[0]
        require(isinstance(unit.get("text"), str) and unit["text"].strip(), "candidate_unit_text_missing")
        result["unit_json_pointer"] = f"/unit_candidates/{ui}/text"
        result["unit_id"] = locator["unit_id"]
        paragraph_id = unit.get("paragraph_id")
        require(paragraph_id is not None, "candidate_unit_paragraph_relation_missing")
        require("paragraph_id" not in locator or locator["paragraph_id"] == paragraph_id, "candidate_unit_paragraph_relation_mismatch")
    else:
        paragraph_id = locator.get("paragraph_id")
        require(scope in {"paragraph", "table_field"}, "candidate_unit_id_required")
    if paragraph_id is not None:
        paragraphs = [(i, p) for i, p in enumerate(candidate.get("paragraphs", []))
                      if isinstance(p, dict) and p.get("id") == paragraph_id]
        require(len(paragraphs) == 1, "candidate_paragraph_id_missing_or_duplicate")
        pi, para = paragraphs[0]
        require(isinstance(para.get("text"), str), "candidate_paragraph_text_missing")
        result.update(paragraph_id=paragraph_id, paragraph_json_pointer=f"/paragraphs/{pi}/text")
        if unit:
            result["unit_in_paragraph_span"] = exact_subspan(para["text"], unit["text"], locator.get("unit_start_in_paragraph"), "candidate_unit_in_paragraph")
        for supplied, actual in (("pages", para.get("pages", unit.get("pages") if unit else None)),
                                 ("source_lines", para.get("line_ids", para.get("source_lines")))):
            if supplied in locator:
                require(locator[supplied] == actual, "candidate_" + supplied + "_mismatch")
    elif scope != "table_field":
        raise BindingError("candidate_paragraph_id_required")
    if para is None:
        require(not any(k in locator for k in ("pages", "source_lines")), "candidate_paragraph_locator_without_paragraph")
    if scope == "unit":
        require(leaf == unit["text"], "candidate_current_unit_text_mismatch")
        result["leaf_span"] = span_meta(unit["text"], {"start": 0, "end": len(leaf), "matching": "exact"})
    elif scope == "unit_subspan":
        result["leaf_span"] = exact_subspan(unit["text"], leaf, locator.get("leaf_start"))
    elif scope == "paragraph":
        result["leaf_span"] = exact_subspan(para["text"], leaf, locator.get("leaf_start"))
    return result, unit, para


def tool_identity(name):
    path = shutil.which(name)
    require(path is not None, "extractor_unavailable_" + name)
    command = [path, "-v"] if name == "pdftotext" else [path, "-help"]
    version = subprocess.run(command, capture_output=True, timeout=10)
    return {"name": name, "path": str(Path(path).resolve()), "executable_sha256": file_sha(path),
            "version_probe_command": command, "version_probe_exit": version.returncode,
            "version_probe_output_sha256": digest(version.stdout + version.stderr)}


def flat_source(source, leaf, locator, whitespace):
    path = Path(source["path"])
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        encoding = source.get("encoding", "utf-8")
        require(encoding in {"utf-8", "utf-8-sig", "utf-16-le", "utf-16-be", "gb18030"}, "source_encoding_unsupported")
        data = path.read_bytes()
        text = data.decode(encoding, errors="strict")
        actual_encoding, base = ("utf-8", 3 if data.startswith(b"\xef\xbb\xbf") else 0) if encoding == "utf-8-sig" else (encoding, 0)
        require(text.encode(actual_encoding) == data[base:], "source_encoding_not_reversible")
        span = choose_occurrence(occurrences(text, leaf, whitespace=whitespace), locator)
        return {"representation": "native_text_file", "literal_position": span_meta(text, span, encoding=actual_encoding, byte_base=base),
                "extraction": {"kind": "strict_decode", "encoding": encoding, "text_sha256": digest(text)}}
    tool = tool_identity("textutil")
    command = [tool["path"], "-convert", "txt", "-encoding", "UTF-8", "-stdout", str(path)]
    proc = subprocess.run(command, capture_output=True, timeout=60)
    require(proc.returncode == 0, "doc_textutil_conversion_failed")
    text = proc.stdout.decode("utf-8", errors="strict")
    require(text.strip(), "doc_textutil_no_text")
    span = choose_occurrence(occurrences(text, leaf, whitespace=whitespace), locator)
    return {"representation": "textutil_flat_extracted_text_not_native_paragraph", "literal_position": span_meta(text, span, encoding=None),
            "extraction": {"tool": tool, "command": command, "text_sha256": digest(text), "stdout_sha256": digest(proc.stdout),
                           "native_table_or_legal_clause_structure_certified": False}}


def xml_paths(root):
    def walk(node, path, ancestors):
        yield node, path, ancestors
        counts = {}
        for child in node:
            local = child.tag.split("}")[-1]
            index = counts.get(local, 0)
            counts[local] = index + 1
            yield from walk(child, path + f"/{local}[{index}]", ancestors + [node.tag])
    yield from walk(root, "/word/document.xml/document[0]", [])


def docx_source(source, leaf, locator, whitespace):
    require(not any(k in locator for k in ("table_index", "row_index", "column_index", "grid_part")), "docx_native_grid_unsupported")
    with zipfile.ZipFile(source["path"]) as package:
        require("word/document.xml" in package.namelist(), "docx_document_xml_missing")
        xml = package.read("word/document.xml")
    root = ET.fromstring(xml)
    matches, unsupported_table_paragraphs, unsupported_matching = [], 0, 0
    unsupported_nested_paragraphs = 0
    pindex = 0
    for node, pointer, ancestors in xml_paths(root):
        if node.tag != W + "p":
            continue
        current_index = pindex
        pindex += 1
        if "xml_paragraph_index" in locator and locator["xml_paragraph_index"] != current_index:
            continue
        # A selected outer w:p does not own descendant textbox paragraphs.
        # Preserve its native text flow without admitting nested paragraphs,
        # tables or textbox content through node.iter().
        def native_text(current):
            if current is not node and current.tag in {W + "p", W + "tbl", W + "txbxContent"}:
                return ""
            if current.tag == W + "t":
                return current.text or ""
            if current.tag == W + "tab":
                return "\t"
            if current.tag == W + "br":
                return "\n"
            return "".join(native_text(child) for child in current)
        text = native_text(node)
        native_matches = occurrences(text, leaf, whitespace=whitespace)
        if W + "p" in ancestors or W + "tbl" in ancestors or W + "txbxContent" in ancestors:
            if W + "p" in ancestors:
                unsupported_nested_paragraphs += 1
            if W + "tbl" in ancestors or W + "txbxContent" in ancestors:
                unsupported_table_paragraphs += 1
            unsupported_matching += len(native_matches)
            continue
        if not native_matches and any(n is not node and n.tag in {W + "p", W + "tbl", W + "txbxContent"} for n in node.iter()):
            descendant_text = "".join(n.text or "" for n in node.iter() if n.tag == W + "t")
            unsupported_matching += len(occurrences(descendant_text, leaf, whitespace=whitespace))
        for match in native_matches:
            matches.append({**match, "xml_pointer": pointer, "xml_paragraph_index": current_index, "_text": text})
    if unsupported_matching:
        require(not matches, "source_literal_ambiguous_over_unsupported_docx_grid")
        raise BindingError("docx_table_or_textbox_literal_unsupported")
    selected = choose_occurrence(matches, locator)
    text = selected.pop("_text")
    return {"representation": "docx_native_non_table_w_p_text", "literal_position": span_meta(text, selected, encoding=None),
            "extraction": {"kind": "zip_word_document_xml_native_p_w_t_tab_br_excluding_nested_content", "document_xml_sha256": digest(xml),
                           "unsupported_table_or_textbox_paragraph_n": unsupported_table_paragraphs,
                           "unsupported_nested_paragraph_n": unsupported_nested_paragraphs}}


def pdf_source(source, leaf, locator, whitespace):
    tool = tool_identity("pdftotext")
    command = [tool["path"], "-bbox-layout", source["path"], "-"]
    proc = subprocess.run(command, capture_output=True, timeout=60)
    require(proc.returncode == 0, "pdf_bbox_extraction_failed")
    root = ET.fromstring(proc.stdout)
    pages = [n for n in root.iter() if n.tag.split("}")[-1] == "page"]
    matches = []
    for page_index, page in enumerate(pages):
        if "page_one_based" in locator and locator["page_one_based"] != page_index + 1:
            continue
        text, words, line_index = "", [], 0
        for line in (n for n in page.iter() if n.tag.split("}")[-1] == "line"):
            line_words = [n for n in line if n.tag.split("}")[-1] == "word"]
            for word_index, word in enumerate(line_words):
                value = "".join(word.itertext())
                start = len(text)
                text += value
                words.append({"start": start, "end": len(text), "word_text_sha256": digest(value),
                              "line_index_zero_based": line_index, "word_index_zero_based": word_index,
                              "bbox": {k: float(word.attrib[k]) for k in ("xMin", "yMin", "xMax", "yMax")}})
                text += " " if word_index < len(line_words) - 1 else ""
            text += "\n"
            line_index += 1
        for match in occurrences(text, leaf, whitespace=whitespace):
            matches.append({**match, "page_one_based": page_index + 1, "_text": text,
                            "word_coordinate_segments": [w for w in words if w["start"] < match["end"] and match["start"] < w["end"]]})
    selected = choose_occurrence(matches, locator)
    text = selected.pop("_text")
    return {"representation": "pdftotext_bbox_layout_single_page_extracted_text", "literal_position": span_meta(text, selected, encoding=None),
            "extraction": {"tool": tool, "command": command, "bbox_xml_sha256": digest(proc.stdout),
                           "page_n": len(pages), "cross_page_join_performed": False,
                           "pixel_transcription_or_legal_clause_revalidated": False}}


class NativeHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.counts, self.nodes = [], [{}], []

    def handle_starttag(self, tag, attrs):
        counts = self.counts[-1]
        index = counts.get(tag, 0)
        counts[tag] = index + 1
        path = (self.stack[-1]["path"] if self.stack else "") + f"/{tag}[{index}]"
        node = {"tag": tag, "path": path, "source_start_line_column": list(self.getpos()), "text": "",
                "explicitly_closed": False,
                "table_ancestry": [n["path"] for n in self.stack if n["tag"] in {"table", "tr", "td", "th"}]}
        self.stack.append(node)
        self.counts.append({})
        if tag in {"p", "td", "th"}:
            self.nodes.append(node)
        if tag == "br":
            for parent in self.stack:
                if parent["tag"] in {"p", "td", "th"}:
                    parent["text"] += "\n"
            self.handle_endtag(tag)
        elif tag in {"meta", "link", "img", "input", "hr", "area", "base", "embed", "source", "wbr"}:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if not any(n["tag"] == tag for n in self.stack):
            return
        while self.stack:
            node = self.stack.pop()
            self.counts.pop()
            if node["tag"] == tag:
                node["explicitly_closed"] = True
                node["source_end_tag_line_column"] = list(self.getpos())
                return

    def handle_data(self, data):
        if any(n["tag"] in {"script", "style"} for n in self.stack):
            return
        for node in self.stack:
            if node["tag"] in {"p", "td", "th"}:
                node["text"] += data


def html_source(source, document, leaf, locator, whitespace):
    require(document.get("source_html") and document.get("source_html_sha256"), "source_html_pair_missing_or_incomplete")
    html_path = Path(document["source_html"])
    if not html_path.is_absolute():
        html_path = Path(source["path"]).parent / html_path
    html_path = html_path.resolve()
    require(html_path.is_file() and file_sha(html_path) == document["source_html_sha256"], "source_html_sha_mismatch")
    data = html_path.read_bytes()
    text = data.decode("utf-8", errors="strict")
    parser = NativeHTML()
    parser.feed(text)
    parser.close()
    matches, unclosed_matching = [], 0
    for node_index, node in enumerate(parser.nodes):
        if "html_node_path" in locator and locator["html_node_path"] != node["path"]:
            continue
        if not node["explicitly_closed"]:
            unclosed_matching += len(occurrences(node["text"], leaf, whitespace=whitespace))
            continue
        for match in occurrences(node["text"], leaf, whitespace=whitespace):
            matches.append({**match, "html_node_path": node["path"], "html_node_index": node_index,
                            "source_start_line_column": node["source_start_line_column"],
                            "source_end_tag_line_column": node["source_end_tag_line_column"],
                            "native_node_tag": node["tag"], "table_ancestry": node["table_ancestry"], "_text": node["text"]})
    if unclosed_matching:
        require(not matches, "html_literal_ambiguous_over_unclosed_node")
        raise BindingError("html_native_node_closing_boundary_missing")
    selected = choose_occurrence(matches, locator)
    value = selected.pop("_text")
    return {"representation": "html_native_p_or_cell_decoded_text", "literal_position": span_meta(value, selected, encoding=None),
            "extraction": {"kind": "stdlib_HTMLParser_native_nodes", "source_html_path": str(html_path),
                           "source_html_sha256": file_sha(html_path), "html_decoding": "utf-8",
                           "entity_decoding": "HTMLParser_convert_charrefs", "cross_node_join_performed": False,
                           "legal_clause_completeness_certified": False}}


def json_value(document, pointer):
    require(isinstance(pointer, str) and pointer.startswith("/"), "json_pointer_invalid")
    node = document
    for token in pointer[1:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        node = node[int(token)] if isinstance(node, list) else node[token]
    return node


def grid_source(source, document, candidate, candidate_meta, unit, para, leaf, locator, candidate_locator):
    table_index, part = locator.get("table_index"), locator.get("grid_part")
    require(integer(table_index), "table_index_invalid")
    tables = document.get("tables")
    require(isinstance(tables, list) and table_index < len(tables), "source_table_missing")
    grid = tables[table_index]
    require(isinstance(grid, dict), "source_grid_not_object")
    require(not any(grid.get(k) for k in ("merges", "merged_cells", "gridSpan", "vMerge")), "merged_grid_unsupported")
    title, columns, rows = grid.get("title"), grid.get("columns"), grid.get("rows")
    require(isinstance(title, str) and title.strip(), "native_grid_title_missing")
    require(isinstance(columns, list) and columns and all(isinstance(c, str) for c in columns), "native_grid_columns_invalid")
    require(isinstance(rows, list) and all(isinstance(r, list) and len(r) == len(columns) and all(isinstance(c, str) for c in r) for r in rows), "native_grid_rows_invalid")
    ci = candidate_locator.get("table_index")
    require(integer(ci), "candidate_table_index_required")
    grids = candidate.get("structured_tables")
    require(isinstance(grids, list) and ci < len(grids), "candidate_native_grid_missing")
    actual = grids[ci]
    require(all(actual.get(k) == grid.get(k) for k in ("title", "columns", "rows")), "source_candidate_grid_mismatch")
    row, column = locator.get("row_index"), locator.get("column_index")
    pointer = f"/tables/{table_index}"
    cpointer = f"/structured_tables/{ci}"
    if part in {"cell", "row"}:
        require(integer(row) and row < len(rows), "row_index_invalid")
        if unit is not None or para is not None:
            for node in (unit, para):
                require(node is not None and node.get("cells") == rows[row] and node.get("columns") == columns and node.get("table_title") == title, "candidate_unit_paragraph_grid_relation_mismatch")
    if part == "cell":
        require(integer(column) and column < len(columns), "column_index_invalid")
        native = rows[row][column]
        pointer += f"/rows/{row}/{column}"
        cpointer += f"/rows/{row}/{column}"
    elif part == "header":
        require(integer(column) and column < len(columns), "column_index_invalid")
        native = columns[column]
        pointer += f"/columns/{column}"
        cpointer += f"/columns/{column}"
    elif part == "title":
        native = title
        pointer += "/title"
        cpointer += "/title"
    elif part == "row":
        require(candidate_locator.get("representation") == "structured_table_row", "table_row_requires_explicit_structure_representation")
        require(candidate_locator.get("leaf_scope") == "unit" and unit is not None, "table_row_requires_exact_current_unit")
        native = " | ".join(rows[row])
        pointer += f"/rows/{row}"
        cpointer += f"/rows/{row}"
    else:
        raise BindingError("grid_part_invalid")
    require(leaf == native, "native_grid_leaf_mismatch")
    candidate_meta["native_grid_leaf_pointer"] = cpointer
    candidate_meta["native_grid_leaf_sha256"] = digest(native)
    image = None
    if any(k in grid for k in ("source_image", "source_image_sha256")):
        image = image_identity(grid, base=Path(source["path"]).parent, grid=True)
        for key in ("source_image", "source_image_sha256", "source_sha256"):
            if key in actual:
                require(actual[key] == grid.get(key), "candidate_grid_image_identity_mismatch")
    return {"representation": "structured_table_row_not_natural_sentence" if part == "row" else "native_json_table_grid_leaf",
            "native_grid_position": {"source_json_pointer": pointer, "candidate_json_pointer": cpointer,
                                     "table_index": table_index, "candidate_table_index": ci, "row_index": row,
                                     "column_index": column, "grid_part": part, "table_title_sha256": digest(title),
                                     "column_sha256": [digest(c) for c in columns], "row_sha256": digest(json.dumps(rows[row], ensure_ascii=False)) if row is not None else None,
                                     "cell_n": len(columns), "native_grid_consistent": True},
            "image": image, "extraction": {"kind": "native_JSON_pointer", "serialized_row_delimiter": " | " if part == "row" else None}}


def bind_leaf(leaf_text, *, record_id, raw_pointer, source_identity, candidate_identity,
              candidate_locator, source_locator=None, allow_whitespace_normalization=False):
    """Deterministic read-only single-leaf API; all reports omit policy text."""
    output = {"version": VERSION, "status": UNBOUND, "record_id": record_id, "raw_pointer": raw_pointer,
              "text_sha256": digest(leaf_text) if isinstance(leaf_text, str) else None,
              "character_n": len(leaf_text) if isinstance(leaf_text, str) else None,
              "implementation_sha256": file_sha(__file__), "axes": {"candidate_position_bound": False,
              "source_literal_position_bound": False, "native_structure_bound": False,
              "image_bytes_bound": False, "visual_transcription_revalidated": False}, "reasons": []}
    try:
        require(isinstance(leaf_text, str) and leaf_text.strip(), "leaf_empty_or_not_text")
        require(isinstance(record_id, str) and record_id and isinstance(raw_pointer, str) and raw_pointer.startswith("/"), "leaf_identity_invalid")
        require(type(allow_whitespace_normalization) is bool, "normalization_flag_not_boolean")
        source = paired_identity(source_identity)
        suffix = Path(source["path"]).suffix.lower()
        if "format" in source_identity:
            declared_format = source_identity["format"]
            require(isinstance(declared_format, str) and declared_format == "docx", "explicit_source_format_unsupported")
            require(suffix in {"", ".docx"}, "explicit_source_format_conflicts_extension")
            require(zipfile.is_zipfile(source["path"]), "explicit_docx_not_zip")
            with zipfile.ZipFile(source["path"]) as package:
                require("word/document.xml" in package.namelist(), "docx_document_xml_missing")
            suffix = ".docx"
            source["format_resolution"] = {"selected_format": "docx", "method": "explicit_declaration_and_actual_ZIP_word_document_xml"}
        encoding = source_identity.get("encoding", "utf-8")
        require(isinstance(encoding, str) and encoding in {"utf-8", "utf-8-sig", "utf-16-le", "utf-16-be", "gb18030"}, "source_encoding_unsupported")
        source["encoding"] = encoding
        candidate_file = paired_identity(candidate_identity, candidate=True)
        output.update(source=source, candidate_identity=candidate_file)
        candidate = json.loads(Path(candidate_file["path"]).read_text(encoding="utf-8"))
        require(isinstance(candidate, dict), "candidate_document_not_object")
        if isinstance(candidate_locator, dict) and (candidate_locator.get("leaf_scope") == "table_field" or "table_index" in candidate_locator):
            require(suffix == ".json" and isinstance(source_locator, dict)
                    and source_locator.get("grid_part") in {"title", "header", "cell", "row"},
                    "candidate_table_field_requires_native_grid")
        cm, unit, para = candidate_position(candidate, candidate_locator, leaf_text)
        cm["source_relation"] = source_relation(candidate, unit, source, Path(candidate_file["path"]).parent)
        output["candidate_position"] = cm
        output["axes"]["candidate_position_bound"] = True
        locator = dict(source_locator or {})
        if candidate_locator.get("representation") == "structured_table_row":
            require(suffix == ".json" and locator.get("grid_part") == "row", "structured_row_requires_native_JSON_grid")
        common_locator = {"char_start", "occurrence_index"}
        if suffix in {".txt", ".md", ".doc"}:
            admitted = common_locator
        elif suffix == ".docx":
            admitted = common_locator | {"xml_paragraph_index"}
            if "xml_paragraph_index" in locator:
                require(integer(locator["xml_paragraph_index"]), "xml_paragraph_index_invalid")
        elif suffix == ".pdf":
            admitted = common_locator | {"page_one_based"}
            if "page_one_based" in locator:
                require(type(locator["page_one_based"]) is int and locator["page_one_based"] >= 1, "pdf_page_index_invalid")
        elif suffix == ".json" and "grid_part" in locator:
            admitted = {"grid_part", "table_index"}
            if locator["grid_part"] in {"row", "cell"}:
                admitted.add("row_index")
            if locator["grid_part"] in {"header", "cell"}:
                admitted.add("column_index")
        elif suffix == ".json" and "json_pointer" in locator:
            admitted = common_locator | {"json_pointer"}
        elif suffix in {".html", ".htm"}:
            admitted = common_locator | {"html_node_path"}
        elif suffix == ".json":
            admitted = common_locator | {"html_node_path"}
        else:
            admitted = set()
        require(set(locator) <= admitted, "source_locator_field_unsupported")
        if suffix in {".txt", ".md", ".doc"}:
            require(candidate_locator.get("representation", "natural_text") != "structured_table_row", "flat_source_cannot_prove_native_table_row")
            evidence = flat_source(source, leaf_text, locator, allow_whitespace_normalization)
        elif suffix == ".docx":
            evidence = docx_source(source, leaf_text, locator, allow_whitespace_normalization)
        elif suffix == ".pdf":
            evidence = pdf_source(source, leaf_text, locator, allow_whitespace_normalization)
        elif suffix in {".html", ".htm"}:
            evidence = html_source(source, {"source_html": source["path"], "source_html_sha256": source["sha256"]},
                                   leaf_text, locator, allow_whitespace_normalization)
            evidence["extraction"]["source_chain_kind"] = "direct_HTML_source"
        elif suffix == ".json":
            document = json.loads(Path(source["path"]).read_text(encoding="utf-8"))
            if "grid_part" in locator:
                evidence = grid_source(source, document, candidate, cm, unit, para, leaf_text, locator, candidate_locator)
                output["axes"]["native_structure_bound"] = True
            elif "json_pointer" in locator:
                native = json_value(document, locator["json_pointer"])
                require(isinstance(native, str), "source_json_pointer_not_text")
                span = choose_occurrence(occurrences(native, leaf_text, whitespace=allow_whitespace_normalization), locator)
                evidence = {"representation": "native_JSON_string", "source_json_pointer": locator["json_pointer"], "literal_position": span_meta(native, span, encoding=None), "extraction": {"kind": "explicit_native_JSON_pointer"}}
            else:
                evidence = html_source(source, document, leaf_text, locator, allow_whitespace_normalization)
                evidence["extraction"]["source_chain_kind"] = "hash_bound_JSON_to_HTML_link"
        elif suffix in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
            output["axes"]["image_bytes_bound"] = True
            raise BindingError("image_literal_requires_independent_region_transcript")
        else:
            raise BindingError("source_format_unsupported")
        require(file_sha(source["path"]) == source["sha256"], "source_changed_during_binding")
        require(file_sha(candidate_file["path"]) == candidate_file["sha256"], "candidate_changed_during_binding")
        linked = evidence.get("extraction", {})
        if linked.get("source_html_path"):
            require(file_sha(linked["source_html_path"]) == linked["source_html_sha256"], "source_html_changed_during_binding")
        tool = linked.get("tool")
        if tool:
            require(file_sha(tool["path"]) == tool["executable_sha256"], "extractor_changed_during_binding")
        output["source_position"] = evidence
        output["axes"]["source_literal_position_bound"] = True
        image = evidence.get("image") or source.get("image")
        if image:
            require(file_sha(image["path"]) == image["sha256"], "image_changed_during_binding")
            output["axes"]["image_bytes_bound"] = True
            output["image"] = image
        output["status"] = GRID_BOUND if image and evidence.get("native_grid_position") else BOUND
        output["proof_kind"] = "source_table_cell" if evidence.get("native_grid_position") else "source_literal_span"
    except BindingError as exc:
        output["reasons"].append(str(exc))
    except Exception as exc:
        output["reasons"].append("extraction_or_structure_error")
        output["error_type"] = type(exc).__name__
    return output


def manifest_payload(bindings):
    """Returned object has no self hash; caller freezes bytes separately."""
    require(isinstance(bindings, list), "manifest_bindings_not_list")
    require(all(b.get("status") in {BOUND, GRID_BOUND} for b in bindings), "manifest_contains_unbound_leaf")
    identities = [(b["record_id"], b["raw_pointer"]) for b in bindings]
    require(len(identities) == len(set(identities)), "manifest_duplicate_record_pointer")
    return {"schema_version": "literal-position-manifest01", "implementation_sha256": file_sha(__file__),
            "self_hash_embedded": False, "bindings": bindings}


def projection_map_from_frozen_manifest(manifest_path, expected_sha256):
    """A separate derived map refers to already-frozen manifest bytes."""
    require(file_sha(manifest_path) == expected_sha256, "manifest_file_sha_mismatch")
    payload = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    require(payload.get("self_hash_embedded") is False and "sha256" not in payload, "manifest_self_hash_contract")
    output = {}
    for b in payload["bindings"]:
        require(b["status"] in {BOUND, GRID_BOUND}, "manifest_unbound_leaf")
        row = output.setdefault(b["record_id"], {})
        require(b["raw_pointer"] not in row, "manifest_duplicate_record_pointer")
        row[b["raw_pointer"]] = {"text_sha256": b["text_sha256"], "source_sha256": b["source"]["sha256"],
                                 "candidate_sha256": b["candidate_identity"]["sha256"], "manifest_sha256": expected_sha256,
                                 "proof_kind": b["proof_kind"], "locator": {"source_position": b["source_position"],
                                 "candidate_position": b["candidate_position"], "image_axes": b["axes"]}}
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if not args.self_test:
        parser.error("Only --self-test on freshly invented temporary files is available.")
    from selftest_literal_source_binder import run
    print(json.dumps(run(), ensure_ascii=False, indent=2))
