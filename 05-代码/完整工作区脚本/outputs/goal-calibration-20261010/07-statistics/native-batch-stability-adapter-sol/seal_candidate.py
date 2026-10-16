#!/usr/bin/env python3
"""Exclusive candidate inventory seal, excluding itself and bytecode caches."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEAL = ROOT / "candidate-seal.json"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def inventory():
    return [{"path": str(p.relative_to(ROOT)), "bytes": p.stat().st_size, "sha256": sha(p.read_bytes())}
            for p in sorted(ROOT.rglob("*")) if p.is_file() and p != SEAL and "__pycache__" not in p.parts and p.suffix != ".pyc"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        seal = json.loads(SEAL.read_text(encoding="utf-8"))
        if seal["files"] != inventory():
            raise SystemExit("candidate inventory differs")
        for item in seal["read_only_external_files"]:
            p = Path(item["path"])
            if p.stat().st_size != item["bytes"] or sha(p.read_bytes()) != item["sha256"]:
                raise SystemExit("read-only input differs: " + str(p))
        print(json.dumps({"status": "candidate_seal_verified", "files": len(seal["files"]), "read_only_files": len(seal["read_only_external_files"])}))
        return
    provenance = json.loads((ROOT / "read-only-provenance.json").read_text(encoding="utf-8"))
    seal = {"contract_version": "native-batch-stability-adapter-sol-v1", "data_mode": "synthetic_control",
            "files": inventory(), "read_only_external_files": provenance["files"],
            "excluded": ["candidate-seal.json itself", "__pycache__", "*.pyc"], "seal_self_included": False,
            "actual_provider_identity_or_independence_authenticated": False, "new_true_R_runs_executed": False,
            "classification_or_Goal_validation_claim": False, "independent_review_completed": False}
    with SEAL.open("x", encoding="utf-8") as stream:
        json.dump(seal, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"status": "candidate_sealed", "files": len(seal["files"])}))


if __name__ == "__main__":
    main()
