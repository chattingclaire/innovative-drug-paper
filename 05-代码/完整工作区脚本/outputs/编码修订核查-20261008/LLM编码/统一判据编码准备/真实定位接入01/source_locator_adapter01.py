"""Finite positional adapter around unchanged binder03; no labels or coders."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
BINDER_PATH = BASE / "字面来源绑定03/literal_source_binder.py"
BINDER_SHA = "bbe0b92e37284a0018a86d4239f500f212d146ade8c8d188c900979f4cccd7f8"
PROJECTOR_PATH = BASE / "全量材料接口核查04/project_source_only_inputs.py"
PROJECTOR_SHA = "e8d20adcfdca24d9e9d8ab1e439bf3ed93c24bc1268f588c347a9708bc43859d"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name, path, expected):
    if sha(path) != expected:
        raise RuntimeError("fixed_dependency_sha_mismatch")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BINDER = load("fixed_real_locator_binder03", BINDER_PATH, BINDER_SHA)
PROJECTOR = load("fixed_metadata_pair_helper04", PROJECTOR_PATH, PROJECTOR_SHA)


class Unsupported(Exception):
    def __init__(self, code, **details):
        super().__init__(code)
        self.code, self.details = code, details


def require(condition, code, **details):
    if not condition:
        raise Unsupported(code, **details)


def offsets(text, leaf):
    if not isinstance(text, str):
        return []
    found, start = [], 0
    while (index := text.find(leaf, start)) >= 0:
        found.append(index)
        start = index + 1
    return found


def raw_value_and_ancestors(row, pointer):
    value, ancestors, prefix = row, [], ""
    for token in pointer[1:].split("/"):
        if isinstance(value, dict):
            ancestors.append((prefix, value))
        token = token.replace("~1", "/").replace("~0", "~")
        value = value[int(token)] if isinstance(value, list) else value[token]
        prefix += "/" + token
    return value, ancestors


class Adapter:
    def __init__(self):
        self.json_cache = {}

    def json_file(self, path, expected, kind):
        key = (path, expected)
        if key not in self.json_cache:
            require(Path(path).is_file(), kind + "_file_missing")
            require(sha(path) == expected, kind + "_sha_mismatch")
            try:
                document = json.loads(Path(path).read_text(encoding="utf-8"))
            except Exception as exc:
                raise Unsupported(kind + "_JSON_unreadable", error_type=type(exc).__name__)
            require(isinstance(document, dict), kind + "_JSON_not_object")
            self.json_cache[key] = document
        return self.json_cache[key]

    def plan(self, row, rule, occurrence, sidecar):
        pointer = occurrence["raw_pointer"]
        leaf, ancestors = raw_value_and_ancestors(row, pointer)
        require(isinstance(leaf, str) and bool(leaf.strip()), "leaf_empty_or_nonstring")
        require(hashlib.sha256(leaf.encode()).hexdigest() == occurrence["text_sha256"] and len(leaf) == occurrence["character_n"], "leaf_index_raw_text_mismatch")
        origin = occurrence.get("source_binding")
        if origin is None:
            origin = sidecar["current_source_priority"]
            for prefix, node in ancestors:
                if prefix:
                    origin = PROJECTOR.source_pair(node, origin, prefix)
        require(not origin.get("identity_issues"), "source_identity_issue_preserved", identity_issues=origin.get("identity_issues"))
        require(isinstance(origin.get("source_path"), str) and isinstance(origin.get("source_sha256"), str), "source_identity_pair_missing")
        require(isinstance(origin.get("candidate_path"), str) and isinstance(origin.get("candidate_sha256"), str), "candidate_identity_pair_missing")
        source = {"source_path": origin["source_path"], "source_sha256": origin["source_sha256"]}
        if "source_image" in origin or "source_image_sha256" in origin:
            require(origin.get("source_image") and origin.get("source_image_sha256"), "source_image_pair_incomplete")
            source.update(source_image=origin["source_image"], source_image_sha256=origin["source_image_sha256"])
        candidate_identity = {"candidate_path": origin["candidate_path"], "candidate_sha256": origin["candidate_sha256"]}
        suffix = Path(source["source_path"]).suffix.lower()
        require(suffix not in {".png", ".jpg", ".jpeg", ".gif", ".webp"}, "image_literal_consumption_unsupported")
        require(suffix in {".txt", ".md", ".doc", ".docx", ".pdf", ".html", ".htm", ".json"}, "source_format_not_declared_or_unsupported", source_suffix=suffix)
        candidate = self.json_file(candidate_identity["candidate_path"], candidate_identity["candidate_sha256"], "candidate")
        node = ancestors[-1][1] if ancestors else row
        current = pointer == "/text"
        unit = para = None
        if current:
            units = [u for u in candidate.get("unit_candidates", []) if isinstance(u, dict) and u.get("id") == rule["input"]["unit_id"]]
            require(len(units) == 1, "current_unit_id_nonunique_or_absent")
            unit = units[0]
            require(unit.get("text") == leaf, "current_candidate_unit_text_mismatch")
            require(isinstance(unit.get("paragraph_id"), str), "current_single_paragraph_relation_unsupported")
        table_parent = next((obj for _, obj in reversed(ancestors) if any(k in obj for k in ("column_names", "header_cells", "headers", "raw_row_cells", "row_cells"))), None)
        row_current = current and isinstance(unit.get("cells"), list)
        if table_parent is not None or row_current:
            require(suffix == ".json", "native_grid_source_required")
            source_doc = self.json_file(source["source_path"], source["source_sha256"], "source_grid")
            locator, source_locator, strategy = self.grid_plan(candidate, source_doc, leaf, pointer, node, table_parent, unit, current)
            return leaf, {"source_identity": source, "candidate_identity": candidate_identity,
                          "candidate_locator": locator, "source_locator": source_locator,
                          "candidate_strategy": strategy, "source_locator_basis": "actual_source_and_candidate_native_grid_positions"}
        field = pointer.rsplit("/", 1)[-1]
        if current:
            pid = unit["paragraph_id"]
            locator = {"leaf_scope": "unit", "unit_id": unit["id"], "paragraph_id": pid}
            strategy = "explicit_current_unit_and_single_paragraph_ID"
        else:
            paired = {"next_paragraph_text": "next_paragraph_id", "next_candidate_paragraph_text": "next_candidate_paragraph_id"}
            pid = node.get(paired[field]) if field in paired else node.get("paragraph_id")
            explicit_unit = node.get("unit_id")
            if pid is None and isinstance(explicit_unit, str):
                units = [u for u in candidate.get("unit_candidates", []) if isinstance(u, dict) and u.get("id") == explicit_unit]
                require(len(units) == 1, "context_unit_id_nonunique_or_absent")
                unit = units[0]
                require(unit.get("text") == leaf, "context_explicit_unit_text_mismatch")
                require(isinstance(unit.get("paragraph_id"), str), "context_single_paragraph_relation_unsupported")
                pid = unit["paragraph_id"]
            if pid is not None:
                require(isinstance(pid, str) and bool(pid), "context_paragraph_ID_invalid")
                strategy = "explicit_context_paragraph_ID"
            else:
                full = [p for p in candidate.get("paragraphs", []) if isinstance(p, dict) and p.get("text") == leaf]
                require(len(full) == 1, "no_ID_exact_full_paragraph_nonunique_or_absent", matching_paragraph_n=len(full))
                pid = full[0].get("id")
                require(isinstance(pid, str) and bool(pid), "matched_paragraph_ID_missing")
                strategy = "unique_exact_full_candidate_paragraph"
            locator = {"leaf_scope": "paragraph", "paragraph_id": pid}
        paras = [p for p in candidate.get("paragraphs", []) if isinstance(p, dict) and p.get("id") == pid]
        require(len(paras) == 1, "candidate_paragraph_ID_nonunique_or_absent")
        para = paras[0]
        matches = offsets(para.get("text"), leaf)
        require(len(matches) == 1, "candidate_leaf_subspan_nonunique_or_absent", candidate_match_n=len(matches))
        if current:
            locator["unit_start_in_paragraph"] = matches[0]
            require(row.get("pages") == unit.get("pages"), "current_unit_pages_mismatch")
            pages, page_basis = unit.get("pages"), "current_unit_actual_candidate_pages"
        else:
            locator["leaf_start"] = matches[0]
            pages = node.get("pages", node.get("source_pages", para.get("pages")))
            page_basis = "context_explicit_pages" if "pages" in node or "source_pages" in node else "matched_candidate_paragraph_pages"
            if isinstance(pages, list) and isinstance(para.get("pages"), list):
                require(all(p in para["pages"] for p in pages), "context_pages_outside_candidate_paragraph")
        source_locator = {}
        if suffix == ".pdf":
            require(isinstance(pages, list) and len(pages) == 1 and type(pages[0]) is int and pages[0] >= 1, "PDF_explicit_single_page_required")
            source_locator["page_one_based"] = pages[0]
        return leaf, {"source_identity": source, "candidate_identity": candidate_identity, "candidate_locator": locator,
                      "source_locator": source_locator, "candidate_strategy": strategy,
                      "source_locator_basis": page_basis if source_locator else "binder03_unique_literal_only_no_guessed_source_offset",
                      "declared_pages": pages, "candidate_paragraph_pages": para.get("pages"),
                      "candidate_source_lines": para.get("line_ids", para.get("source_lines")),
                      "declared_source_lines": node.get("source_lines", node.get("line_ids"))}

    def grid_plan(self, candidate, source_doc, leaf, pointer, node, table_parent, unit, current):
        owner = table_parent if table_parent is not None else unit
        title = owner.get("table_title")
        columns = owner.get("column_names", owner.get("columns", owner.get("header_cells", owner.get("headers"))))
        cells = owner.get("raw_row_cells", owner.get("row_cells", owner.get("cells")))
        require(isinstance(title, str) and isinstance(columns, list), "native_grid_title_columns_missing")
        pairs = []
        for si, sg in enumerate(source_doc.get("tables", [])):
            if not isinstance(sg, dict) or sg.get("title") != title or sg.get("columns") != columns:
                continue
            if not isinstance(sg.get("rows"), list):
                continue
            for ci, cg in enumerate(candidate.get("structured_tables", [])):
                if isinstance(cg, dict) and all(cg.get(k) == sg.get(k) for k in ("title", "columns", "rows")):
                    pairs.append((si, ci, sg))
        require(len(pairs) == 1, "native_grid_table_pair_nonunique_or_absent", matching_grid_pair_n=len(pairs))
        si, ci, grid = pairs[0]
        locator = {"leaf_scope": "table_field", "table_index": ci}
        source_locator = {"table_index": si}
        if current:
            part = "row"
            require(unit.get("text") == " | ".join(cells), "current_row_serialization_not_fixed_grid_join")
            locator.update(leaf_scope="unit", representation="structured_table_row", unit_id=unit["id"], paragraph_id=unit["paragraph_id"])
        elif pointer.rsplit("/", 1)[-1] in {"table_title", "title"}:
            part = "title"
        elif any("/" + k + "/" in pointer for k in ("column_names", "header_cells", "headers")):
            part = "header"
            source_locator["column_index"] = int(pointer.rsplit("/", 1)[-1])
        elif any("/" + k + "/" in pointer for k in ("raw_row_cells", "row_cells")):
            part = "cell"
            source_locator["column_index"] = int(pointer.rsplit("/", 1)[-1])
        else:
            raise Unsupported("native_grid_leaf_field_unsupported")
        source_locator["grid_part"] = part
        if part in {"row", "cell"}:
            explicit_row = owner.get("row_index_zero_based")
            if explicit_row is not None:
                require(type(explicit_row) is int and 0 <= explicit_row < len(grid["rows"]), "native_grid_row_index_invalid")
                require(grid["rows"][explicit_row] == cells, "native_grid_explicit_row_cells_mismatch")
                row_index = explicit_row
            else:
                rows = [i for i, row in enumerate(grid["rows"]) if row == cells]
                require(len(rows) == 1, "native_grid_row_nonunique_or_absent", matching_row_n=len(rows))
                row_index = rows[0]
            source_locator["row_index"] = row_index
        return locator, source_locator, "actual_unique_source_candidate_grid_pair_and_original_cell_indices"

    def bind(self, row, rule, occurrence, sidecar):
        base = {"id": row["id"], "raw_pointer": occurrence["raw_pointer"], "text_sha256": occurrence["text_sha256"],
                "character_n": occurrence["character_n"], "occurrence_kind": occurrence.get("occurrence_kind", "registered_projector_leaf"),
                "declared_source_binding": occurrence.get("source_binding"),
                "binder_called": False, "formal_model_input_ready": False}
        try:
            leaf, plan = self.plan(row, rule, occurrence, sidecar)
            base["plan"] = plan
            request = {k: plan[k] for k in ("source_identity", "candidate_identity", "candidate_locator", "source_locator")}
            base["binder_called"] = True
            binding = BINDER.bind_leaf(leaf, record_id=row["id"], raw_pointer=occurrence["raw_pointer"], **request, allow_whitespace_normalization=False)
            base["binding"] = binding
            base["status"] = "bound_literal" if binding["status"] == BINDER.BOUND else "bound_native_grid_image_bytes_only" if binding["status"] == BINDER.GRID_BOUND else "binder_unbound"
            base["reasons"] = binding["reasons"]
        except Unsupported as exc:
            base.update(status="adapter_unsupported", reasons=[exc.code], unsupported_details=exc.details)
        except Exception as exc:
            base.update(status="adapter_exception", reasons=["adapter_unexpected_exception"], error_type=type(exc).__name__)
        return base
