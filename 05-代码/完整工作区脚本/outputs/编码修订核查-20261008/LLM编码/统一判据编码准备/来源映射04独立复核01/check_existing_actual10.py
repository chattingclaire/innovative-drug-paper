"""Independent relational audit of only the delivered ten actual cases.

Does not import the author adapter/binder, load semantic labels, build a new
construct matrix, or execute the full corpus. Only writes this review folder.
"""
from pathlib import Path
import hashlib
import html
from html.parser import HTMLParser
import json
import re
import subprocess
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
DELIVERY = BASE / "定位接入02"
AUTHOR_DIRS = [BASE / "定位接入02", BASE / "字面来源绑定04"]
SHA = lambda b: hashlib.sha256(b).hexdigest()


def identities():
    return {str(p): SHA(p.read_bytes()) for d in AUTHOR_DIRS for p in d.rglob("*") if p.is_file()}


def pointer(obj, path):
    for token in path[1:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        obj = obj[int(token)] if isinstance(obj, list) else obj[token]
    return obj


def canonical(text, base=0):
    """Independently reconstruct the declared finite operation log and map."""
    guards = {}
    for match in re.finditer(r"(?<![A-Za-z0-9ⅠⅡⅢ])[ⅠⅡⅢ](?:、[ⅠⅡⅢ])*期临床试验", text):
        for i in range(match.start(), match.end()):
            if text[i] in "ⅠⅡⅢ":
                guards[i] = {"kind": "explicit_clinical_trial_phase_suffix", "start": base + match.start(),
                             "end": base + match.end(), "original_text": match.group()}
    tokens, forward, events, pos = [], [], [], 0
    while pos < len(text):
        a = pos
        c = text[pos]
        guard = None
        if c in " \n":
            while pos < len(text) and text[pos] in " \n":
                pos += 1
            left, right = text[a-1:a] if a else "", text[pos:pos+1]
            keep = bool(left and right and re.fullmatch("[A-Za-z0-9]", left) and re.fullmatch("[A-Za-z0-9]", right))
            value = " " if keep else ""
            kind = "layout_whitespace_preserve_ASCII_word_boundary" if keep else "layout_whitespace_omit"
        else:
            pos += 1
            if a in guards:
                value = {"Ⅰ": "I", "Ⅱ": "II", "Ⅲ": "III"}[c]
                kind = "clinical_Roman_numeral_same_value_expansion"
                guard = guards[a]
            elif c in "，（）：":
                value = {"，": ",", "（": "(", "）": ")", "：": ":"}[c]
                kind = "explicit_punctuation_width_pair"
            else:
                value, kind = c, None
        start = len(tokens)
        tokens.extend(value)
        forward.extend([[base+a, base+pos]] * len(value))
        if kind:
            event = {"kind": kind, "original_start": base+a, "original_end": base+pos,
                     "original_text": text[a:pos], "original_codepoints": [f"U+{ord(x):04X}" for x in text[a:pos]],
                     "canonical_start": start, "canonical_end": len(tokens),
                     "canonical_text": value, "canonical_codepoints": [f"U+{ord(x):04X}" for x in value]}
            if guard:
                event["clinical_phase_guard"] = guard
            events.append(event)
    reverse = {str(i): [] for i in range(base, base+len(text))}
    for k, (a, z) in enumerate(forward):
        for i in range(a, z):
            reverse[str(i)].append(k)
    return "".join(tokens), forward, reverse, events


class HTMLText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.skip += 1
        elif tag == "br" and not self.skip:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def native_container(r):
    b = r["binding"]
    src = Path(r["plan"]["source_identity"]["source_path"])
    pos = b["source_position"]
    lp = pos["literal_position"]
    kind = pos["representation"]
    extra = {}
    if kind == "native_text_file":
        data = src.read_bytes()
        value = data.decode(pos["extraction"]["encoding"])
        assert data[lp["source_byte_start"]:lp["source_byte_end"]].decode(lp["source_encoding"]) == lp["finite_mapping"]["source_original_span_text"]
        assert "\n" not in value[lp["start"]:lp["end"]]
        extra["original_file_byte_slice"] = True
    elif kind == "textutil_flat_extracted_text_not_native_paragraph":
        value = subprocess.check_output(["/usr/bin/textutil", "-convert", "txt", "-encoding", "UTF-8", "-stdout", str(src)]).decode()
        assert "\n" not in value[lp["start"]:lp["end"]]
        assert pos["extraction"]["native_table_or_legal_clause_structure_certified"] is False
        extra["does_not_claim_DOC_container_bytes_or_native_table"] = True
    elif kind == "pdftotext_bbox_layout_single_page_extracted_text":
        page = lp["page_one_based"]
        assert r["plan"]["source_locator"] == {"page_one_based": page}
        data = subprocess.check_output(["pdftotext", "-f", str(page), "-l", str(page), "-bbox-layout", str(src), "-"])
        root = ET.fromstring(data)
        pages = [e for e in root.iter() if e.tag.split("}")[-1] == "page"]
        assert len(pages) == 1
        value, words = "", []
        lines = [e for e in pages[0].iter() if e.tag.split("}")[-1] == "line"]
        for li, line in enumerate(lines):
            ws = [e for e in line if e.tag.split("}")[-1] == "word"]
            for wi, word in enumerate(ws):
                text = "".join(word.itertext())
                start = len(value)
                value += text
                words.append({"start": start, "end": len(value), "word_text_sha256": SHA(text.encode()),
                              "line_index_zero_based": li, "word_index_zero_based": wi,
                              "bbox": {k: float(word.attrib[k]) for k in ("xMin", "yMin", "xMax", "yMax")}})
                if wi + 1 < len(ws):
                    value += " "
            value += "\n"
        expected = [w for w in words if w["start"] < lp["end"] and lp["start"] < w["end"]]
        assert expected == lp["word_coordinate_segments"]
        assert pos["extraction"]["cross_page_join_performed"] is False
        extra.update(explicit_single_page=True, original_page_line_word_bbox_verified=True)
    elif kind == "html_native_p_or_cell_decoded_text":
        raw = src.read_bytes().decode("utf-8")
        offsets = [0]
        offsets.extend(m.end() for m in re.finditer("\n", raw))
        a = offsets[lp["source_start_line_column"][0]-1] + lp["source_start_line_column"][1]
        z = offsets[lp["source_end_tag_line_column"][0]-1] + lp["source_end_tag_line_column"][1]
        chunk = raw[a:z]
        assert chunk.startswith("<" + lp["native_node_tag"])
        assert raw[z:].startswith("</" + lp["native_node_tag"])
        # Existing actual nodes have no nested p/cell; never concatenate siblings.
        assert len(re.findall(r"<(?:p|td|th)(?:\s|>)", chunk)) == 1
        parser = HTMLText()
        parser.feed(chunk)
        value = "".join(parser.parts)
        raw_match = lp["finite_mapping"]["source_original_span_text"]
        hits = [m.start() for m in re.finditer(re.escape(raw_match), chunk)]
        assert len(hits) == 1
        ba = len(raw[:a+hits[0]].encode())
        bz = ba + len(raw_match.encode())
        assert src.read_bytes()[ba:bz].decode() == raw_match
        assert pos["extraction"]["cross_node_join_performed"] is False
        extra.update(native_node_boundaries_verified=True, original_HTML_byte_span=[ba,bz])
    else:
        raise AssertionError("Unexpected delivered representation " + kind)
    return value, extra


def run():
    before = identities()
    source = DELIVERY / "actual10_results02.jsonl"
    rows = [json.loads(s) for s in source.read_text().splitlines() if s.strip()]
    assert len(rows) == 10
    checks = []
    for r in rows:
        plan, b = r["plan"], r["binding"]
        for key, prefix in [("source_identity", "source"), ("candidate_identity", "candidate")]:
            item = plan[key]
            assert SHA(Path(item[prefix+"_path"]).read_bytes()) == item[prefix+"_sha256"]
        candidate = json.loads(Path(plan["candidate_identity"]["candidate_path"]).read_text())
        cp = b["candidate_position"]
        selected = pointer(candidate, cp.get("unit_json_pointer", cp["paragraph_json_pointer"]))
        leaf = selected[cp["leaf_span"]["start"]:cp["leaf_span"]["end"]]
        assert SHA(leaf.encode()) == r["text_sha256"] and len(leaf) == r["character_n"]
        if "unit_in_paragraph_span" in cp:
            pp = pointer(candidate, cp["paragraph_json_pointer"])
            span = cp["unit_in_paragraph_span"]
            assert pp[span["start"]:span["end"]] == selected
        assert r["formal_model_input_ready"] is False
        if r["status"] == "binder_unbound":
            assert r["id"] == "RECODE25-00452" and r["reasons"] == ["source_literal_absent"]
            assert "source_position" not in b
            text = subprocess.check_output(["/usr/bin/textutil", "-convert", "txt", "-encoding", "UTF-8", "-stdout", plan["source_identity"]["source_path"]]).decode()
            target = canonical(leaf)[0]
            assert "|" in leaf
            assert all(target not in canonical(line)[0] for line in text.split("\n"))
            checks.append({"id": r["id"], "pointer": r["raw_pointer"], "status": "PASS_retained_DOC_table_failure", "source_literal_absent_independently_reproduced": True, "native_grid_not_claimed": True})
            continue
        assert r["status"] == "bound_with_finite_layout_mapping"
        container, extra = native_container(r)
        lp = b["source_position"]["literal_position"]
        mapping = lp["finite_mapping"]
        a, z = lp["start"], lp["end"]
        assert container[a:z] == mapping["source_original_span_text"]
        assert SHA(container.encode()) == lp["container_text_sha256"]
        assert len(container) == lp["container_character_n"]
        assert len(container[:a].encode()) == lp["utf8_byte_start"]
        assert len(container[:z].encode()) == lp["utf8_byte_end"]
        assert mapping["leaf_original_text"] == leaf
        for name, text, base in [("source", container[a:z], a), ("leaf", leaf, 0)]:
            canonical_text, forward, reverse, events = canonical(text, base)
            assert canonical_text == mapping["canonical_text"]
            assert forward == mapping[name+"_canonical_to_original_spans"]
            assert reverse == mapping[name+"_original_to_canonical_indices"]
            assert events == mapping[name+"_transformations"]
        assert lp["matching_occurrence_count_before_locator"] == 1
        assert mapping["NFKC_or_case_or_word_replacement_used"] is False
        checks.append({"id":r["id"],"pointer":r["raw_pointer"],"status":"PASS",
                       "representation":b["source_position"]["representation"],
                       "native_span":[a,z],"canonical_character_n":len(mapping["canonical_text"]),
                       "source_event_n":len(mapping["source_transformations"]),"leaf_event_n":len(mapping["leaf_transformations"]),
                       "source_and_candidate_SHA_match":True,"candidate_original_field_span_match":True,
                       "both_forward_and_reverse_indices_exact":True,"transformation_events_exact":True,
                       "native_container_and_span_exact":True,**extra})
    for r in rows:
        for key, prefix in [("source_identity", "source"), ("candidate_identity", "candidate")]:
            item = r["plan"][key]
            assert SHA(Path(item[prefix+"_path"]).read_bytes()) == item[prefix+"_sha256"]
    after = identities()
    assert before == after
    report={"scope":"Existing actual ten cases only; independent source-relational audit; no semantic validity inference",
            "actual_n":10,"mapped_cases_independently_checked":9,"retained_actual_DOC_table_failure":1,
            "all_passed":True,"author_files_unchanged":True,"author_files_before_and_after_sha256":before,
            "actual_sources_and_candidates_SHA_verified_before_and_after":True,
            "full_28196_executed":False,"new_construct_matrix":False,"author_binder_or_adapter_imported":False,
            "actual10_results_sha256":SHA(source.read_bytes()),"results":checks}
    (HERE/"independent_actual10_checks.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k != "author_files_before_and_after_sha256"},ensure_ascii=False,indent=2))


if __name__ == "__main__":
    run()
