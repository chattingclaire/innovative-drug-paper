"""Small byte-binding helpers; no coding, labels or statistics on import."""
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path

if not __debug__:
    raise RuntimeError("This binding/validation interface cannot run under python -O")

ROOT = Path(__file__).resolve().parents[2]
CONDITIONS = ("R1", "R2", "R3", "W", "H")


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def binding(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def check(item):
    actual = binding(item["path"])
    assert all(actual[k] == item[k] for k in actual), "Changed bound file: " + item["path"]
    return actual


def load(path):
    def pairs(rows):
        obj = {}
        for k, v in rows:
            if k in obj:
                raise ValueError("Duplicate JSON key: " + k)
            obj[k] = v
        return obj
    def nonfinite(x):
        raise ValueError("Nonfinite JSON number: " + x)
    return json.loads(Path(path).read_text(), object_pairs_hook=pairs, parse_constant=nonfinite)


def save(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write((json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode())
    return binding(path)


def put(path, raw):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)
    return binding(path)


def module(item, name):
    check(item)
    spec = importlib.util.spec_from_file_location(name, item["path"])
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def campaign(run):
    run = Path(run).resolve()
    doc = load(run / "run-manifest.json")
    assert doc["run_id"] == run.name and doc["status"] == "prepared_before_any_diagnostic_dispatch"
    for item in doc["implementation_bindings"]:
        check(item)
    return run, doc


def route(doc, condition, batch, attempt):
    assert condition in CONDITIONS and 1 <= batch <= doc["batch_N"] and attempt in (1, 2, 3)
    return next(x for x in doc["routes"] if (x["condition"], x["batch_number"], x["attempt_number"]) == (condition, batch, attempt))


def selected_dir(doc, condition, batch):
    return Path(route(doc, condition, batch, 1)["selection_directory"])


def check_prior(directory, attempt):
    assert not (directory / "root-selection.json").exists(), "First valid batch already fixed"
    assert not (directory / "root-zero-call-block.json").exists(), "Batch has a recorded zero-call block"
    for earlier in range(1, attempt):
        assert load(directory / f"root-attempt-reception-{earlier:04d}.json")["state"] == "technical_invalid_whole_batch"
    assert not (directory / f"root-attempt-reception-{attempt:04d}.json").exists(), "Immutable receipt already exists"
