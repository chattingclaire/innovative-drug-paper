"""Actual temporary source files; no corpus, gold labels, model or coder."""
import copy
import json
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

import literal_source_binder as b


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def make_candidate(folder, source, current, *, paragraph=None, tables=None):
    path = folder / (source.name.replace(".", "_") + "-candidate.json")
    paragraph = current if paragraph is None else paragraph
    unit = {"id": "u", "text": current, "paragraph_id": "p", "pages": [1]}
    para = {"id": "p", "text": paragraph, "pages": [1], "line_ids": ["invented:1"]}
    data = {"source": str(source), "source_sha256": b.file_sha(source), "unit_candidates": [unit], "paragraphs": [para]}
    if tables is not None:
        data["structured_tables"] = copy.deepcopy(tables)
        for node in (unit, para):
            node.update(cells=tables[0]["rows"][0], columns=tables[0]["columns"], table_title=tables[0]["title"])
    write_json(path, data)
    return path


def request(source, candidate, leaf, **kwargs):
    return b.bind_leaf(leaf, record_id="INVENTED", raw_pointer="/text",
                       source_identity=kwargs.pop("source_identity", {"source_path": str(source), "source_sha256": b.file_sha(source)}),
                       candidate_identity={"candidate_path": str(candidate), "candidate_sha256": b.file_sha(candidate)},
                       candidate_locator=kwargs.pop("candidate_locator", {"unit_id": "u", "paragraph_id": "p", "leaf_scope": "unit"}), **kwargs)


def minimal_pdf(path, pages):
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>", b"", b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    kids = []
    for lines in pages:
        page_id = len(objects) + 1
        stream_id = page_id + 1
        kids.append(f"{page_id} 0 R")
        stream = "BT /F1 12 Tf 50 780 Td " + " ".join(("0 -20 Td " if i else "") + "(" + text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") + ") Tj" for i, text in enumerate(lines)) + " ET"
        objects += [f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R >> >> /Contents {stream_id} 0 R >>".encode(), f"<< /Length {len(stream.encode())} >>\nstream\n{stream}\nendstream".encode()]
    objects[1] = f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {len(kids)} >>".encode()
    data = b"%PDF-1.4\n"
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(data)); data += f"{index} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(data)
    data += f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode()
    data += b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:])
    data += f"trailer << /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    path.write_bytes(data)


def minimal_docx(path, text, *, table=False):
    para = f"<w:p><w:r><w:t>{escape(text)}</w:t></w:r></w:p>"
    body = f"<w:tbl><w:tr><w:tc><w:tcPr><w:gridSpan w:val='2'/></w:tcPr>{para}</w:tc></w:tr></w:tbl>" if table else para
    xml = f"<?xml version='1.0' encoding='UTF-8'?><w:document xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'><w:body>{body}<w:sectPr/></w:body></w:document>"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("word/document.xml", xml)
        z.writestr("[Content_Types].xml", "<Types xmlns='http://schemas.openxmlformats.org/package/2006/content-types'><Default Extension='rels' ContentType='application/vnd.openxmlformats-package.relationships+xml'/><Default Extension='xml' ContentType='application/xml'/><Override PartName='/word/document.xml' ContentType='application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml'/></Types>")
        z.writestr("_rels/.rels", "<Relationships xmlns='http://schemas.openxmlformats.org/package/2006/relationships'><Relationship Id='rId1' Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument' Target='word/document.xml'/></Relationships>")


def run():
    checks, unavailable = [], []
    def check(name, result, expected_bound, *, reason=None, extra=True):
        actual_bound = result["status"] in {b.BOUND, b.GRID_BOUND}
        passed = actual_bound == expected_bound and extra
        if reason:
            passed = passed and reason in result["reasons"]
        checks.append({"name": name, "passed": bool(passed), "expected_bound": expected_bound, "binding": result})
    with tempfile.TemporaryDirectory(prefix="literal-binder-invented-only-") as temporary:
        root = Path(temporary)
        leaf = "构造当前文字。"
        txt = root / "source.txt"; txt.write_text("构造前段。\n" + leaf + "\n构造后段。", encoding="utf-8")
        c = make_candidate(root, txt, leaf)
        first = request(txt, c, leaf)
        check("txt_exact_source_candidate_byte_line", first, True,
              extra=first.get("source_position", {}).get("literal_position", {}).get("line_start_one_based") == 2)
        repeated = root / "repeated.txt"; repeated.write_text(leaf + "\n" + leaf, encoding="utf-8")
        cr = make_candidate(root, repeated, leaf)
        check("source_repeated_without_locator", request(repeated, cr, leaf), False, reason="source_literal_ambiguous")
        second = request(repeated, cr, leaf, source_locator={"occurrence_index": 1})
        check("source_repeated_explicit_occurrence", second, True, extra=second.get("source_position", {}).get("literal_position", {}).get("start") == len(leaf) + 1)
        spaced = root / "spaces.txt"; spaced.write_text("构造 当前\n文字。", encoding="utf-8")
        cs = make_candidate(root, spaced, leaf)
        check("whitespace_only_reversible", request(spaced, cs, leaf, allow_whitespace_normalization=True), True)
        punct = root / "punctuation.txt"; punct.write_text("构造当前文字!", encoding="utf-8")
        cp = make_candidate(root, punct, leaf)
        check("punctuation_not_erased", request(punct, cp, leaf, allow_whitespace_normalization=True), False, reason="source_literal_absent")
        md = root / "source.md"; md.write_text("# 构造标题\n\n" + leaf, encoding="utf-8")
        check("md_native_position", request(md, make_candidate(root, md, leaf), leaf), True)
        base = json.loads(c.read_text())
        for name, change, reason in [
            ("candidate_duplicate_unit", lambda d:d["unit_candidates"].append(copy.deepcopy(d["unit_candidates"][0])), "candidate_unit_id_missing_or_duplicate"),
            ("candidate_wrong_paragraph", lambda d:d["unit_candidates"][0].update(paragraph_id="other"), "candidate_unit_paragraph_relation_mismatch"),
            ("candidate_wrong_current_text", lambda d:d["unit_candidates"][0].update(text="其他构造句。"), "candidate_unit_in_paragraph_absent")]:
            changed=copy.deepcopy(base);change(changed);path=root/(name+".json");write_json(path,changed)
            check(name, request(txt,path,leaf), False, reason=reason)
        check("candidate_pages_mismatch", request(txt,c,leaf,candidate_locator={"unit_id":"u","paragraph_id":"p","leaf_scope":"unit","pages":[7]}), False, reason="candidate_pages_mismatch")
        check("candidate_lines_mismatch", request(txt,c,leaf,candidate_locator={"unit_id":"u","paragraph_id":"p","leaf_scope":"unit","source_lines":["wrong"]}), False, reason="candidate_source_lines_mismatch")
        repeated_candidate=copy.deepcopy(base);repeated_candidate["paragraphs"][0]["text"]=leaf+"\n"+leaf
        crr=root/"candidate-repeated-paragraph.json";write_json(crr,repeated_candidate)
        check("candidate_repeated_unit_requires_offset",request(txt,crr,leaf),False,reason="candidate_unit_in_paragraph_ambiguous")
        check("candidate_repeated_unit_explicit_offset",request(txt,crr,leaf,candidate_locator={"unit_id":"u","paragraph_id":"p","leaf_scope":"unit","unit_start_in_paragraph":len(leaf)+1}),True)
        stale_candidate=b.bind_leaf(leaf,record_id="INVENTED",raw_pointer="/text",source_identity={"source_path":str(txt),"source_sha256":b.file_sha(txt)},candidate_identity={"candidate_path":str(c),"candidate_sha256":"0"*64},candidate_locator={"unit_id":"u","paragraph_id":"p","leaf_scope":"unit"})
        check("candidate_sha_mismatch",stale_candidate,False,reason="candidate_sha_mismatch")
        check("candidate_representation_shape",request(txt,c,leaf,candidate_locator={"unit_id":"u","paragraph_id":"p","leaf_scope":"unit","representation":{"opinion":"untrusted config"}}),False,reason="candidate_representation_invalid")
        check("encoding_metadata_shape",request(txt,c,leaf,source_identity={"source_path":str(txt),"source_sha256":b.file_sha(txt),"encoding":{"opinion":"untrusted config"}}),False,reason="source_encoding_unsupported")
        check("table_field_cannot_bypass_candidate_text",request(txt,c,"构造前段。",candidate_locator={"leaf_scope":"table_field","table_index":0}),False,reason="candidate_table_field_requires_native_grid")
        check("source_sha_mismatch", request(txt,c,leaf,source_identity={"source_path":str(txt),"source_sha256":"0"*64}), False, reason="source_sha_mismatch")
        check("partial_unit_source_no_fallback", request(txt,c,leaf,source_identity={"unit_source":str(txt),"source":str(txt),"source_sha256":b.file_sha(txt)}), False, reason="unit_source_pair_incomplete")
        check("partial_image_no_fallback", request(txt,c,leaf,source_identity={"source_path":str(txt),"source_sha256":b.file_sha(txt),"source_image":"missing.bin"}), False, reason="image_pair_incomplete")
        alt=root/"alternate.txt";alt.write_bytes(txt.read_bytes())
        check("alternate_without_candidate_relation",request(alt,c,leaf),False,reason="candidate_selected_source_relation_missing")
        addbase=json.loads(c.read_text());entry={"path":str(alt),"sha256":b.file_sha(alt)}
        for name, entries, expected, reason in [
            ("additional_source_exact_unique",[entry],True,None),
            ("additional_source_missing_sha",[{"path":str(alt)}],False,"candidate_additional_source_pair_incomplete_or_invalid"),
            ("additional_source_missing_path",[{"sha256":b.file_sha(alt)}],False,"candidate_additional_source_pair_incomplete_or_invalid"),
            ("additional_source_wrong_sha",[{"path":str(alt),"sha256":"0"*64}],False,"candidate_additional_source_sha_mismatch"),
            ("additional_source_duplicate_identical",[entry,entry],False,"candidate_additional_source_path_duplicate_or_conflicting"),
            ("additional_source_duplicate_conflicting",[entry,{"path":str(alt),"sha256":"0"*64}],False,"candidate_additional_source_path_duplicate_or_conflicting")]:
            data=copy.deepcopy(addbase);data["additional_sources"]=entries;cc=root/(name+".json");write_json(cc,data)
            result=request(alt,cc,leaf);check(name,result,expected,reason=reason)
        absent=root/"additional-without-leaf.txt";absent.write_text("该临时来源没有请求的字面内容。",encoding="utf-8")
        data=copy.deepcopy(addbase);data["additional_sources"]=[{"path":str(absent),"sha256":b.file_sha(absent)}];cc=root/"additional-without-leaf-candidate.json";write_json(cc,data)
        check("additional_identity_not_literal_proof",request(absent,cc,leaf),False,reason="source_literal_absent")
        grid = {"title":"构造表题","columns":["甲列","乙列"],"rows":[["重复格","重复格"]]}
        image=root/"image.bin";image.write_bytes(b"invented-image-bytes-not-pixels")
        grid.update(source_image=str(image),source_image_sha256=b.file_sha(image),visually_checked=True)
        native=root/"grid.json";write_json(native,{"tables":[grid]})
        row=" | ".join(grid["rows"][0]);cg=make_candidate(root,native,row,tables=[grid])
        for part, value, sloc in [("title",grid["title"],{}),("header",grid["columns"][1],{"column_index":1}),
                                  ("cell0",grid["rows"][0][0],{"row_index":0,"column_index":0}),
                                  ("cell1",grid["rows"][0][1],{"row_index":0,"column_index":1})]:
            kind="cell" if part.startswith("cell") else part
            result=request(native,cg,value,candidate_locator={"leaf_scope":"table_field","table_index":0},source_locator={"table_index":0,"grid_part":kind,**sloc})
            check("native_grid_"+part,result,True,extra=result["axes"]["image_bytes_bound"] and not result["axes"]["visual_transcription_revalidated"])
        row_result=request(native,cg,row,candidate_locator={"unit_id":"u","paragraph_id":"p","leaf_scope":"unit","table_index":0,"representation":"structured_table_row"},source_locator={"table_index":0,"grid_part":"row","row_index":0})
        check("native_serialized_row_explicit_representation",row_result,True,extra=row_result.get("source_position",{}).get("representation")=="structured_table_row_not_natural_sentence")
        check("serialized_row_not_natural_sentence",request(native,cg,row,candidate_locator={"unit_id":"u","paragraph_id":"p","leaf_scope":"unit","table_index":0},source_locator={"table_index":0,"grid_part":"row","row_index":0}),False,reason="table_row_requires_explicit_structure_representation")
        check("invalid_boolean_row_index",request(native,cg,"重复格",candidate_locator={"leaf_scope":"table_field","table_index":0},source_locator={"table_index":0,"grid_part":"cell","row_index":False,"column_index":0}),False,reason="row_index_invalid")
        badgrid=copy.deepcopy(json.loads(cg.read_text()));badgrid["structured_tables"][0]["rows"][0][0]="错格";bc=root/"badgrid.json";write_json(bc,badgrid)
        check("candidate_grid_mismatch",request(native,bc,"重复格",candidate_locator={"leaf_scope":"table_field","table_index":0},source_locator={"table_index":0,"grid_part":"cell","row_index":0,"column_index":0}),False,reason="source_candidate_grid_mismatch")
        for name, altered, reason in [
            ("grid_missing_title",{**grid,"title":""},"native_grid_title_missing"),
            ("grid_merged_unsupported",{**grid,"merges":[[0,0,0,1]]},"merged_grid_unsupported"),
            ("grid_bad_dimensions",{**grid,"rows":[["单格"]]},"native_grid_rows_invalid")]:
            path=root/(name+".json");write_json(path,{"tables":[altered]});cc=make_candidate(root,path,"重复格",tables=[altered])
            check(name,request(path,cc,"重复格",candidate_locator={"leaf_scope":"table_field","table_index":0},source_locator={"table_index":0,"grid_part":"cell","row_index":0,"column_index":0}),False,reason=reason)
        certificate="构造表题；列名：甲列 | 乙列"
        certcandidate=make_candidate(root,native,certificate,tables=[grid])
        check("assembled_certificate_not_native_leaf",request(native,certcandidate,certificate,candidate_locator={"unit_id":"u","paragraph_id":"p","leaf_scope":"unit","table_index":0},source_locator={"table_index":0,"grid_part":"cell","row_index":0,"column_index":0}),False,reason="native_grid_leaf_mismatch")
        image.write_bytes(b"changed-invented-image")
        check("image_modified_byte_identity",request(native,cg,"重复格",candidate_locator={"leaf_scope":"table_field","table_index":0},source_locator={"table_index":0,"grid_part":"cell","row_index":0,"column_index":0}),False,reason="image_sha_mismatch")
        docx=root/"ordinary.docx";minimal_docx(docx,leaf)
        check("docx_native_paragraph",request(docx,make_candidate(root,docx,leaf),leaf),True)
        merged=root/"merged.docx";minimal_docx(merged,leaf,table=True)
        check("docx_merged_table_not_plain_paragraph",request(merged,make_candidate(root,merged,leaf),leaf),False,reason="docx_table_or_textbox_literal_unsupported")
        if shutil.which("pdftotext"):
            pdf=root/"ordinary.pdf";minimal_pdf(pdf,[["Fresh invented policy sentence."]])
            check("pdf_actual_bbox_extractor",request(pdf,make_candidate(root,pdf,"Fresh invented policy sentence."),"Fresh invented policy sentence."),True)
            repeated_pdf=root/"repeated.pdf";minimal_pdf(repeated_pdf,[["Fresh repeated sentence.","Fresh repeated sentence."]])
            check("pdf_repeated_without_locator",request(repeated_pdf,make_candidate(root,repeated_pdf,"Fresh repeated sentence."),"Fresh repeated sentence."),False,reason="source_literal_ambiguous")
            cross=root/"cross.pdf";minimal_pdf(cross,[["Fresh first"],["second sentence."]])
            check("pdf_no_cross_page_join",request(cross,make_candidate(root,cross,"Fresh first second sentence."),"Fresh first second sentence.",allow_whitespace_normalization=True),False,reason="source_literal_absent")
        else:
            unavailable.append({"fixture":"PDF","reason":"actual_pdftotext_unavailable","counted_as_pass":False})
        if shutil.which("textutil"):
            doc_text=root/"doc-generation.txt";doc_text.write_text("Actual temporary DOC sentence.",encoding="utf-8")
            doc=root/"ordinary.doc"
            proc=subprocess.run([shutil.which("textutil"),"-convert","doc","-output",str(doc),str(doc_text)],capture_output=True,timeout=60)
            if proc.returncode==0 and doc.is_file() and doc.read_bytes().startswith(bytes.fromhex("d0cf11e0a1b11ae1")):
                check("doc_actual_binary_and_textutil",request(doc,make_candidate(root,doc,"Actual temporary DOC sentence."),"Actual temporary DOC sentence."),True)
            else:
                unavailable.append({"fixture":"DOC","reason":"actual_DOC_fixture_generation_failed_or_not_CFB","exit_code":proc.returncode,"stderr_sha256":b.digest(proc.stderr),"counted_as_pass":False})
        else:
            unavailable.append({"fixture":"DOC","reason":"actual_textutil_unavailable","counted_as_pass":False})
        html=root/"source.html";html.write_text("<html><body><p>Fresh &amp; exact paragraph.</p><table><tr><td>Fresh cell.</td></tr></table></body></html>",encoding="utf-8")
        direct_html=request(html,make_candidate(root,html,"Fresh & exact paragraph."),"Fresh & exact paragraph.")
        check("direct_html_native_closed_p",direct_html,True,extra=direct_html.get("source_position",{}).get("extraction",{}).get("source_chain_kind")=="direct_HTML_source")
        cell=request(html,make_candidate(root,html,"Fresh cell."),"Fresh cell.")
        check("direct_html_native_table_cell",cell,True,extra=bool(cell.get("source_position",{}).get("literal_position",{}).get("table_ancestry")) and not cell["axes"]["native_structure_bound"])
        dup_html=root/"duplicate.html";dup_html.write_text("<html><body><p>Fresh duplicated p.</p><p>Fresh duplicated p.</p></body></html>",encoding="utf-8")
        dup_c=make_candidate(root,dup_html,"Fresh duplicated p.")
        check("direct_html_repeated_ambiguous",request(dup_html,dup_c,"Fresh duplicated p."),False,reason="source_literal_ambiguous")
        check("direct_html_repeated_explicit_node",request(dup_html,dup_c,"Fresh duplicated p.",source_locator={"html_node_path":"/html[0]/body[0]/p[1]"}),True)
        link=root/"html-link.json";write_json(link,{"source_html":str(html),"source_html_sha256":b.file_sha(html)})
        hc=make_candidate(root,link,"Fresh & exact paragraph.")
        check("html_link_native_p_and_entity",request(link,hc,"Fresh & exact paragraph."),True)
        linkbad=root/"bad-html-link.json";write_json(linkbad,{"source_html":str(html),"source_html_sha256":"0"*64})
        check("html_link_bad_sha",request(linkbad,make_candidate(root,linkbad,"Fresh & exact paragraph."),"Fresh & exact paragraph."),False,reason="source_html_sha_mismatch")
        open_html=root/"open.html";open_html.write_text("<html><body><p>Fresh open paragraph.",encoding="utf-8")
        check("direct_html_missing_close",request(open_html,make_candidate(root,open_html,"Fresh open paragraph."),"Fresh open paragraph."),False,reason="html_native_node_closing_boundary_missing")
        open_link=root/"open-link.json";write_json(open_link,{"source_html":str(open_html),"source_html_sha256":b.file_sha(open_html)})
        check("html_missing_closing_node",request(open_link,make_candidate(root,open_link,"Fresh open paragraph."),"Fresh open paragraph."),False,reason="html_native_node_closing_boundary_missing")
        png=root/"image-only.png";png.write_bytes(bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108000000003a7e9b550000000a49444154789c636000000002000148afa4710000000049454e44ae426082"))
        image_only=request(png,make_candidate(root,png,leaf),leaf)
        check("image_only_bytes_not_literal",image_only,False,reason="image_literal_requires_independent_region_transcript",extra=image_only["axes"]["image_bytes_bound"] and not image_only["axes"]["source_literal_position_bound"])
        check("empty_leaf",request(txt,c," "),False,reason="leaf_empty_or_not_text")
        unknown=root/"unknown.bin";unknown.write_bytes(b"unsupported binary")
        check("unsupported_source",request(unknown,make_candidate(root,unknown,leaf),leaf),False,reason="source_format_unsupported")
        manifest=b.manifest_payload([first]);mp=root/"manifest.json";write_json(mp,manifest)
        mapping=b.projection_map_from_frozen_manifest(mp,b.file_sha(mp))
        check("manifest_no_circular_self_hash",first,True,extra=manifest["self_hash_embedded"] is False and mapping["INVENTED"]["/text"]["manifest_sha256"]==b.file_sha(mp))
        raw=json.dumps(checks,ensure_ascii=False)
        require_no_text=leaf not in raw and "Fresh & exact paragraph." not in raw and "Actual temporary DOC sentence." not in raw
    return {"schema_version":"literal-binder-constructed-execution01","implementation_sha256":b.file_sha(b.__file__),
            "test_code_sha256":b.file_sha(__file__),"check_n":len(checks),"passed_n":sum(c["passed"] for c in checks),
            "passed":all(c["passed"] for c in checks) and require_no_text,"no_literal_text_in_report":require_no_text,
            "checks":checks,"unavailable_fixtures_not_counted_as_pass":unavailable,
            "real_policy_source_files_opened":False,"real_corpus_bound_or_exported":False,"labels_models_rules_used":False,
            "fixtures":"All newly invented actual temporary files; no mocked extraction or authentication."}
