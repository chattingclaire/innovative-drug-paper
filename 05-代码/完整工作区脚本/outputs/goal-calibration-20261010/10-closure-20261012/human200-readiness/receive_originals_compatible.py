"""Receive issued200 originals through the sealed receiver plus its missing import.

Accepts the unchanged receive.py arguments. Reception never authenticates people,
adjudicates labels, or runs formal statistics. Existing output directories fail.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import posixpath
import sys
from types import SimpleNamespace

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RECEIVER = ROOT / "05-validation/human200-reception-root"
EXPECTED = {
    "receiver": ("receive.py", 6000,
                 "6c6024fbb8672f0d1b6629489948f2e2632105a9f8ca1c8bd00c366f910a6464"),
    "receiver_bindings": ("bindings.json", 4059,
                          "3c4b3793e8357cf8868785c16458f0d308f43383d3710d75eb2eb91042aa2aa0"),
    "reader": ("bound_xlsx_reader.py", 11782,
               "a3259e7f87c075ccb117799cbbb86533100e9bb0885167ff3df2b1709d3dc6c1"),
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def binding(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest()}


def prepare_receiver():
    frozen = {}
    for key, (name, size, digest) in EXPECTED.items():
        expected = {"path": str(RECEIVER / name), "bytes": size, "sha256": digest}
        require(binding(expected["path"]) == expected, "Changed sealed dependency: " + key)
        frozen[key] = expected
    declared = json.loads(Path(frozen["receiver_bindings"]["path"]).read_text())
    require(declared["code"] == frozen["receiver"] and declared["vendor"] == frozen["reader"],
            "Receiver/reader binding mismatch")
    spec = importlib.util.spec_from_file_location("_issued200_compatible_receiver", frozen["receiver"]["path"])
    receiver = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(receiver)

    class ReaderLoader:
        def __init__(self, original):
            self.original = original

        def create_module(self, spec):
            return self.original.create_module(spec)

        def exec_module(self, module):
            self.original.exec_module(module)
            require("posixpath" not in module.__dict__, "Unexpected sealed reader dependency")
            module.posixpath = posixpath

    def reader_spec(name, location):
        require(name == "_bound200_xlsx_reader" and binding(location) == frozen["reader"],
                "Compatibility import must use the exact sealed reader")
        spec = importlib.util.spec_from_file_location(name, location)
        spec.loader = ReaderLoader(spec.loader)
        return spec

    # A module-local facade: no process-wide importlib or sealed source mutation.
    receiver.importlib = SimpleNamespace(util=SimpleNamespace(
        spec_from_file_location=reader_spec,
        module_from_spec=importlib.util.module_from_spec,
    ))
    runtime = {
        "kind": "ROOT_owned_missing_standard_library_import_wrapper",
        "wrapper": binding(__file__), **frozen,
        "injected_standard_library": "posixpath",
        "injection_scope": "exact_bound_reader_module_after_original_loader",
        "python_version": sys.version,
        "sealed_source_modified": False,
        "original_receiver_main_reused": True,
        "human_identity_or_independence_authenticated": False,
        "formal_numeric_results_generated": 0,
    }
    original_put_json = receiver.put_json

    def put_json(path, data):
        require(path.name in ("report.json", "seal.json"), "Unexpected receiver JSON artifact")
        require("runtime_compatibility" not in data, "Runtime provenance already present")
        # report is augmented before the original seal hashes output_members.
        original_put_json(path, {**data, "runtime_compatibility": runtime})

    receiver.put_json = put_json
    return receiver


def main():
    prepare_receiver().main()


if __name__ == "__main__":
    main()
