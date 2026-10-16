#!/usr/bin/env python3
"""Seal or verify this tool-preparation directory, without reading true labels."""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from stability_engine import canonical, digest


def metadata(path, name):
    data = path.read_bytes()
    return {"path": name, "sha256": digest(data), "bytes": len(data)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    base = Path(__file__).resolve().parent
    seal_path = base / "preparation-seal.json"
    if args.verify:
        seal = json.loads(seal_path.read_text(encoding="utf-8"))
        failures = []
        for item in seal["files"]:
            p = base / item["path"]
            if not p.is_file() or metadata(p, item["path"]) != item:
                failures.append(item["path"])
        for item in seal["read_only_method_sources"]:
            p = Path(item["path"])
            if not p.is_file() or metadata(p, item["path"]) != item:
                failures.append(item["path"])
        current = {p.relative_to(base).as_posix() for p in base.rglob("*") if p.is_file()
                   and "__pycache__" not in p.parts and p != seal_path and not p.name.startswith(".")}
        if current != {item["path"] for item in seal["files"]}:
            failures.append("prepared file membership changed")
        print(json.dumps({"status": "seal_verified" if not failures else "seal_mismatch", "prepared_files": len(seal["files"]),
                          "failures": failures, "actual_model_or_independence_verified": False}, ensure_ascii=False))
        return 1 if failures else 0
    root = base.parent.parent
    sources = [root / "06-coding/llm-protocol-sol/稳定性与运行封存预设.md",
               root / "02-methods/prospective-statistical-contract-v2/validation-design-v2.json"]
    files = [metadata(p, p.relative_to(base).as_posix()) for p in sorted(base.rglob("*")) if p.is_file()
             and "__pycache__" not in p.parts and p != seal_path and not p.name.startswith(".")]
    seal = {"bundle": "prospective-stability-engine-sol", "status": "tool_preparation_only_not_formal_execution_or_completion",
            "data_mode": "synthetic_control", "sealed_at_utc": datetime.now(timezone.utc).isoformat(),
            "prepared_by": {"kind": "AI", "requested_model": "gpt-6.1-sol", "requested_reasoning_effort": "ultra", "human_expert": False},
            "boundaries": {"real_labels_or_gold_read": False, "real_model_called": False, "llm_tasks_created": False,
                           "actual_stability_computed": False, "formal_execution_plan_changed": False, "project_completion_status_changed": False},
            "read_only_method_sources": [metadata(p, str(p)) for p in sources], "files": files,
            "self_included": False, "ignored": ["__pycache__", "hidden runtime files"],
            "identity_or_independence_authenticated_by_hash": False}
    seal_path.write_bytes(canonical(seal) + b"\n")
    print(json.dumps({"status": "tool_preparation_sealed", "prepared_files": len(files), "path": str(seal_path), "synthetic_only": True}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
