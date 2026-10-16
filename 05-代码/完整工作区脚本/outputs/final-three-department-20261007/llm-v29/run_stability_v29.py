"""Run the two frozen stability replicates with the official Codex CLI."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CLI = Path("/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex")
SOURCE_PROMPT = ROOT / "outputs/llm-v29-method-audit-20261005/完整系统提示词-v29.txt"
SCHEMA = HERE / "output_schema_codex_compatible.json"
VALIDATOR = ROOT / "outputs/llm-v29-method-audit-20261005/validate_binary_output.py"


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def reordered_prompt(text):
    start = text.index("### S 安全性")
    end = text.index("## 四、理由与逐字证据", start)
    region = text[start:end]
    names = [("S", "### S 安全性"), ("E", "### E 有效性"), ("Ec", "### Ec 经济性"), ("I", "### I 创新性"), ("F", "### F 公平性")]
    pieces = {}
    positions = [(key, region.index(marker)) for key, marker in names]
    for i, (key, pos) in enumerate(positions):
        pieces[key] = region[pos:positions[i + 1][1] if i + 1 < len(positions) else len(region)]
    return text[:start] + "".join(pieces[key] for key in ["F", "I", "Ec", "E", "S"]) + text[end:]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--variant", choices=["same-repeat", "same-repeat-2", "dimension-order-repeat"], required=True); ap.add_argument('--design',choices=['v1-invalid','v2-valid'],default='v2-valid'); args = ap.parse_args()
    packet_path = HERE / ("stability_sample_36_v2.json" if args.design=='v2-valid' else "stability_sample_36.json")
    dest = HERE / ("stability-v2" if args.design=='v2-valid' else "stability") / args.variant
    dest.mkdir(parents=True, exist_ok=False)
    prompt = SOURCE_PROMPT.read_text()
    if args.variant == "dimension-order-repeat": prompt = reordered_prompt(prompt)
    packet = json.loads(packet_path.read_text())
    request = prompt + "\n\n--- 冻结稳定性样本 ---\n" + json.dumps(packet, ensure_ascii=False)
    output = dest / "raw_output.json"; started = time.time()
    with tempfile.TemporaryDirectory(prefix="llm-v29-stability-") as cwd:
        proc = subprocess.run([str(CLI), "exec", "-", "--model", "gpt-5.6-sol", "--cd", cwd,
            "-c", 'model_reasoning_effort="medium"', "--skip-git-repo-check", "--ephemeral",
            "--ignore-user-config", "--sandbox", "read-only", "--output-schema", str(SCHEMA),
            "--output-last-message", str(output), "--json"], input=request, text=True, capture_output=True, timeout=1800)
    (dest / "events.jsonl").write_text(proc.stdout); (dest / "raw_stderr.txt").write_text(proc.stderr)
    check = subprocess.run(["python3", str(VALIDATOR), str(packet_path), str(output)], capture_output=True, text=True) if output.exists() else None
    if check: (dest / "validation.json").write_text(check.stdout)
    meta = {"variant": args.variant, "requested_model": "gpt-5.6-sol", "reasoning_effort": "medium",
        "status": "accepted_first_output" if proc.returncode == 0 and check and check.returncode == 0 else "failed_preserved",
        "elapsed_seconds": round(time.time()-started, 3), "n": 36, "sample_sha256": sha(packet_path), "design": args.design,
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(), "output_sha256": sha(output) if output.exists() else None}
    (dest / "run_metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps(meta, ensure_ascii=False))

if __name__ == "__main__": main()
