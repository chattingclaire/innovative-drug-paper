"""Add explicit JSON types required by the Codex structured-output API."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
source = ROOT / "outputs/llm-v29-method-audit-20261005/output_schema_binary.json"
schema = json.loads(source.read_text())


def visit(node):
    if isinstance(node, dict):
        node.pop("uniqueItems", None)
        if "const" in node and "type" not in node:
            value = node["const"]
            node["type"] = "string" if isinstance(value, str) else "integer"
        for value in node.values():
            visit(value)
    elif isinstance(node, list):
        for value in node:
            visit(value)


visit(schema)
(HERE / "output_schema_codex_compatible.json").write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n")
