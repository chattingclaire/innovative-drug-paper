"""Preserve v1.1; create an editorial-only numbering correction with a proof."""
import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

BASE = Path(__file__).resolve().parents[1]
OLD = BASE / "03-manual/common-manual-v1.1-development.md"
NEW = BASE / "03-manual/common-manual-v1.2-development.md"
EXPECTED = "6ffc7b35a5cbe1c1f90c81d24d1508dba7adefe5e7bbd058c284d76e14b8a70f"

old_bytes = OLD.read_bytes()
assert hashlib.sha256(old_bytes).hexdigest() == EXPECTED
old = old_bytes.decode("utf-8")
changes = [
    ("# 五维共同编码手册 v1.1：开发校准版", "# 五维共同编码手册 v1.2：开发校准版"),
    ("## 十一、开发校准版本记录", "## 十二、开发校准版本记录"),
]
new = old
for before, after in changes:
    assert new.count(before) == 1
    new = new.replace(before, after, 1)
new_bytes = new.encode("utf-8")
if NEW.exists():
    assert NEW.read_bytes() == new_bytes
else:
    NEW.write_bytes(new_bytes)
restored = new
for before, after in reversed(changes):
    restored = restored.replace(after, before, 1)
assert restored.encode("utf-8") == old_bytes
assert OLD.read_bytes() == old_bytes
record = {
    "version": "v1.2-editorial-only",
    "created_at": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
    "old_file": str(OLD),
    "old_sha256": EXPECTED,
    "new_file": str(NEW),
    "new_sha256": hashlib.sha256(new_bytes).hexdigest(),
    "changes": [{"before": a, "after": b} for a, b in changes],
    "reversing_only_these_changes_restores_v11_bytes": True,
    "semantic_definition_or_example_changes": 0,
    "old_v11_preserved": True,
    "current_4_record_rejudgment_manual": "v1.1 unchanged",
    "final_independent_test_frozen": False,
}
(BASE / "03-manual/manual-v1.2-editorial-change-log.json").write_text(
    json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(record, ensure_ascii=False))
