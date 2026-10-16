"""Candidate metadata proof only; never a reception, retry or execution authority."""
import hashlib
import shlex


def event_metadata(raw_event, index):
    """Project real CLI metadata without retaining policy text or agent text."""
    item = raw_event.get("item", {})
    output = item.get("aggregated_output")
    return {
        "raw_event_index": index,
        "event_type": raw_event.get("type"),
        "item_type": item.get("type"),
        "item_id": item.get("id"),
        "exit_code": item.get("exit_code"),
        "command": item.get("command"),
        "output_is_string": isinstance(output, str),
        "output_nonempty": isinstance(output, str) and bool(output.strip()),
        "output_utf8_bytes": len(output.encode()) if isinstance(output, str) else None,
        "output_sha256": hashlib.sha256(output.encode()).hexdigest() if isinstance(output, str) else None,
    }


def command_pages(command, executable):
    """Only the witnessed sole zsh -lc/direct pdftotext form; no shell additions."""
    if not isinstance(command, str):
        return None
    try:
        args = shlex.split(command)
        if len(args) == 3 and args[:2] == ["/bin/zsh", "-lc"]:
            args = shlex.split(args[2])
    except ValueError:
        return None
    if (len(args) != 8 or args[0] != executable
            or [args[1], args[3], args[5], args[7]] != ["-f", "-l", "-layout", "-"]):
        return None
    if not args[2].isdecimal() or not args[4].isdecimal():
        return None
    first, last = int(args[2]), int(args[4])
    if first < 1 or last < first:
        return None
    return {"path": args[6], "start": first, "end": last}


def map_pdf_page_event(entry, interval, metadata, first_event_index,
                       asset_binding, required_utf8_paths,
                       pdftotext_executable="/opt/homebrew/bin/pdftotext"):
    """Return an independent observable identity proof, never authenticate old chunks.

    Caller must retain the original first/declaration and raw event bytes, bind
    metadata to those events using event_metadata, and obtain first_event_index
    from the unchanged exact-first capture guard. This function cannot replace
    schema, allowlist, required UTF8/helper, quote, null or whole-first guards.
    """
    path = entry.get("path")
    if (not isinstance(path, str) or not path.lower().endswith(".pdf")
            or path in required_utf8_paths
            or interval.get("range_kind") != "physical_pages"):
        raise ValueError("Only supplemental physical PDF page metadata eligible")
    if any(entry.get(k) != asset_binding.get(k) for k in ("path", "bytes", "sha256")):
        raise ValueError("PDF asset binding differs")
    if (entry.get("not_truncated") is not True or not isinstance(entry.get("read_method"), str)
            or not entry["read_method"].strip() or not isinstance(entry.get("source_ids"), list)
            or not entry["source_ids"]):
        raise ValueError("Incomplete original PDF declaration metadata")
    if not set(entry.get("source_ids", [])) <= set(asset_binding.get("source_ids", [])):
        raise ValueError("PDF source-ID binding differs")
    left, right = interval.get("start"), interval.get("end")
    if type(left) is not int or type(right) is not int or left < 1 or right < left:
        raise ValueError("Illegal physical page range")
    if not isinstance(interval.get("presentation_event"), str) or not interval["presentation_event"].strip():
        raise ValueError("Missing original declaration identity")
    if type(first_event_index) is not int or first_event_index < 0:
        raise ValueError("Invalid captured-first event index")
    first = [m for m in metadata if m.get("raw_event_index") == first_event_index]
    if len(first) != 1 or first[0].get("event_type") != "item.completed" or first[0].get("item_type") != "agent_message":
        raise ValueError("Captured-first metadata identity absent")
    eligible = []
    for m in metadata:
        if (type(m.get("raw_event_index")) is not int or m["raw_event_index"] >= first_event_index
                or m.get("event_type") != "item.completed"
                or m.get("item_type") != "command_execution"
                or type(m.get("exit_code")) is not int or m["exit_code"] != 0
                or m.get("output_is_string") is not True or m.get("output_nonempty") is not True
                or type(m.get("output_utf8_bytes")) is not int or m["output_utf8_bytes"] <= 0
                or not isinstance(m.get("output_sha256"), str) or len(m["output_sha256"]) != 64
                or any(c not in "0123456789abcdef" for c in m["output_sha256"])
                or not isinstance(m.get("item_id"), str) or not m["item_id"]):
            continue
        pages = command_pages(m.get("command"), pdftotext_executable)
        if pages == {"path": path, "start": left, "end": right}:
            eligible.append(m)
    if len(eligible) != 1:
        raise ValueError("No unique real pre-first completed nonempty exact PDF-page command")
    match = eligible[0]
    return {
        "origin": "independent_observable_PDF_page_command_identity",
        "input_binding": {k: entry[k] for k in ("path", "bytes", "sha256")},
        "source_ids": entry["source_ids"],
        "physical_pages": {"start": left, "end": right},
        "original_declared_presentation_event": interval["presentation_event"],
        "original_chunk_identity_authenticated_or_recovered": False,
        "actual_raw_event_index": match["raw_event_index"],
        "actual_completed_item_id": match["item_id"],
        "actual_exit_code": 0,
        "output_utf8_bytes": match["output_utf8_bytes"],
        "output_sha256": match["output_sha256"],
        "output_semantics_or_pixels_verified": False,
        "required_UTF8_or_other_guards_relaxed": False,
        "original_first_or_declaration_modified": False,
        "reception_or_execution_authorized": False,
    }
