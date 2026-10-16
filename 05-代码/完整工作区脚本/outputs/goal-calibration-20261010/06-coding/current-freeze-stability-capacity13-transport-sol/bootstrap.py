"""Load unchanged frozen ROOT runner/receiver; apply only scheduling capacity overlay."""
from pathlib import Path
import sys
import types
sys.dont_write_bytecode = True
import capacity13_common as common

def runtime():
    sys.modules["transport_common"] = common
    doc = common.profile()
    base = Path(doc["base_campaign_manifest"]["path"]).parent.parent
    bindings = {Path(b["path"]).name: b for b in doc["implementation_bindings"]}
    for name in ("receiver", "runner", "controller"):
        b = bindings[name + ".py"]
        common.check(b)
        source = Path(b["path"]).read_text(encoding="utf8")
        if name == "controller":
            for old, new in (("hard-cap3", "hard-cap13"), ('"actual_concurrency_cap": 3', '"actual_concurrency_cap": 13'), ("ThreadPoolExecutor(max_workers=3)", "ThreadPoolExecutor(max_workers=13)")):
                if source.count(old) != 1:
                    raise ValueError("Unexpected frozen controller capacity location")
                source = source.replace(old, new)
        module = types.ModuleType(name)
        module.__file__ = b["path"]
        module.__capacity13_source_compiled_in_memory__ = name == "controller"
        sys.modules[name] = module
        exec(compile(source, b["path"], "exec"), module.__dict__)
    return sys.modules["controller"], sys.modules["runner"], sys.modules["receiver"]
