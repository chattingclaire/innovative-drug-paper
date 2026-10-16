#!/usr/bin/env python3
"""Run and technically receive only the 35 missing native predictions for the 77-row development diagnostic.

This is deliberately a separate, source-at-a-time coverage-recovery campaign.
It leaves the original full4481 campaign and its terminal attempts untouched.
"""
from __future__ import annotations
import argparse, hashlib, json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAPS = ROOT / "07-statistics/current-v5-rule-and-native-partial77-development-diagnostics-root/native-reference-coverage-gaps.json"
OUT = ROOT / "06-coding/native-reference77-coverage-recovery-v1-sol"
FULL = ROOT / "06-coding/native-full4481-v1-sol"
PREP = ROOT / "06-coding/full4481-common-v15-production-preparation-sol"
CLI = ROOT / "06-coding/isolated-codex-cli-0.162.1-root/node_modules/.bin/codex"
MANUAL = ROOT / "03-manual/full4481-common-release-20261010-root/manual.txt"
PROMPT = ROOT / "03-manual/full4481-common-release-20261010-root/execution-prompt.txt"
PROTOCOL = ROOT / "03-manual/full4481-common-release-20261010-root/common-execution-protocol.txt"
DIMS = ("S", "E", "Ec", "I", "F")

def bind(path: Path) -> dict:
    raw = path.read_bytes()
    return {"path":str(path.resolve()), "bytes":len(raw), "sha256":hashlib.sha256(raw).hexdigest()}

def save_new(path: Path, obj) -> None:
    with path.open("x", encoding="utf8") as f: json.dump(obj,f,ensure_ascii=False,indent=2); f.write("\n")

def load_json(p: Path): return json.loads(p.read_text())

def exact(p: Path, b: dict) -> None:
    if bind(p) != b: raise AssertionError(f"bound input changed: {p}")

def setup() -> list[str]:
    if OUT.exists():
        return load_json(OUT / "manifest.json")["source_ids"]
    ids = load_json(GAPS)["missing_record_ids"]
    OUT.mkdir(parents=True)
    shared = {"manual":bind(MANUAL),"execution_prompt":bind(PROMPT),"common_execution_protocol":bind(PROTOCOL),"cli_launcher":bind(CLI)}
    cases=[]
    for sid in ids:
        packet=PREP / "packets" / f"{sid}.json"
        if not packet.is_file(): raise AssertionError(f"missing packet {packet}")
        cdir=OUT / "cases" / sid
        cdir.mkdir(parents=True)
        case={"source_id":sid,"packet":bind(packet),"shared":shared,"requested_model":"gpt-6.1-sol","requested_reasoning_effort":"ultra",
              "scope":"Only a technically missing source in the existing 77-record development-diagnostic coverage; source-at-a-time recovery, not a full corpus replacement.",
              "prohibitions":["Do not read the A/B review workbooks, metrics, any previous machine results, other cases, original attempts, user configuration, memories, or history.","Do not change frozen inputs or create a prediction outside the supplied attempt directory."]}
        save_new(cdir / "case-assignment.json",case); cases.append({"source_id":sid,"case":bind(cdir/"case-assignment.json")})
    save_new(OUT / "manifest.json", {"artifact_type":"targeted_native_coverage_recovery_manifest","created_at_utc":datetime.now(timezone.utc).isoformat(),"source_ids":ids,"shared":shared,"cases":cases,
       "interpretation":"Technically separate coverage recovery for the 35 source IDs missing from the original campaign. It cannot be combined with that campaign as a single first-pass full-corpus run; any later metric is a development diagnostic."})
    return ids

def prompt_for(case_path: Path, slot: Path) -> str:
    return f'''You are a fresh, independent policy-text coding actor. This is one source only. Follow the frozen coding rules exactly and make one complete coding decision.\n\nRead these complete files before deciding:\n1. Case assignment: {case_path}\n2. Frozen coding manual: {MANUAL}\n3. Frozen execution prompt: {PROMPT}\n4. Frozen common execution protocol: {PROTOCOL}\n5. The packet path named by `packet.path` in the case assignment.\n\nUse only those research inputs. Do not read human reference sheets, metric outputs, previous machine outputs, other coding cases, memories, histories, or user settings. Do not delegate. Apply the five frozen dimensions S, E, Ec, I, F to the packet’s policy clause and its permitted source materials. A value must be 0, 1, or null only; retain null only where the frozen rule requires insufficient material.\n\nCreate exactly one new UTF-8 JSON file with exclusive creation at:\n{slot / 'first.json'}\n\nIt must be a single JSON object with this exact high-level structure:\n{{\n  "artifact_type":"targeted_native_coverage_recovery_first",\n  "source_id":"<the case source_id>",\n  "requested_model":"gpt-6.1-sol",\n  "requested_reasoning_effort":"ultra",\n  "input_bindings":{{"manual":<copy case shared manual binding>,"execution_prompt":<copy case shared execution_prompt binding>,"common_execution_protocol":<copy case shared protocol binding>,"packet":<copy case packet binding>}},\n  "dimensions":{{"S":{{"value":0,"reason":"...","evidence":[]}},"E":{{"value":0,"reason":"...","evidence":[]}},"Ec":{{"value":0,"reason":"...","evidence":[]}},"I":{{"value":0,"reason":"...","evidence":[]}},"F":{{"value":0,"reason":"...","evidence":[]}}}},\n  "completion_note":"first and only coding submission for this case"\n}}\n\nEvery dimension must be present. `reason` must explain the decision; `evidence` must be a JSON list (empty only when value is 0 and no positive evidence is used). Do not put content outside JSON in that file. After writing it, briefly report completion.\n'''

def dispatch(sid: str) -> dict:
    cdir=OUT/"cases"/sid; case_path=cdir/"case-assignment.json"; case=load_json(case_path)
    exact(case_path, bind(case_path)) # existence/readability only; assignment bound by manifest below
    manifest=load_json(OUT/"manifest.json"); input_case=next(x["case"] for x in manifest["cases"] if x["source_id"]==sid); exact(case_path,input_case)
    for key,path in (("manual",MANUAL),("execution_prompt",PROMPT),("common_execution_protocol",PROTOCOL),("cli_launcher",CLI)): exact(path,case["shared"][key])
    exact(Path(case["packet"]["path"]),case["packet"])
    slot=cdir/"attempt-0001"
    if slot.exists():
        return {"source_id":sid,"status":"already_started_or_terminal","slot":str(slot)}
    slot.mkdir()
    p=slot/"dispatch-prompt.txt"; p.write_text(prompt_for(case_path,slot),encoding="utf8")
    cmd=[str(CLI),"exec","--ignore-user-config","--skip-git-repo-check","--ephemeral","--json","--color","never","-C",str(slot),"--model","gpt-6.1-sol","-c",'model_reasoning_effort="ultra"','-c','approval_policy="never"',"--sandbox","workspace-write",'-c','features.multi_agent=false','-c','features.memories=false','-c','web_search="disabled"','-c','project_doc_max_bytes=0',"--output-last-message",str(slot/"final-message.txt"),"-"]
    save_new(slot/"dispatch-start.json",{"at_utc":datetime.now(timezone.utc).isoformat(),"case":input_case,"prompt":bind(p),"argv":cmd,"requested_model":"gpt-6.1-sol","requested_reasoning_effort":"ultra","fresh_context":True})
    with (slot/"events.jsonl").open("xb") as out,(slot/"stderr.txt").open("xb") as err:
        proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=out,stderr=err,cwd=slot); proc.communicate(p.read_bytes())
    result={"source_id":sid,"status":"terminal","returncode":proc.returncode,"first_exists":(slot/"first.json").exists(),"events":bind(slot/"events.jsonl"),"stderr":bind(slot/"stderr.txt")}
    save_new(slot/"terminal.json",result)
    return result

def receive(sid: str) -> dict:
    cdir=OUT/"cases"/sid; case=load_json(cdir/"case-assignment.json"); slot=cdir/"attempt-0001"; first=slot/"first.json"
    if not first.is_file(): return {"source_id":sid,"state":"technical_invalid","error":"first.json absent"}
    try:
        x=load_json(first)
        assert x["artifact_type"]=="targeted_native_coverage_recovery_first" and x["source_id"]==sid
        assert x["requested_model"]=="gpt-6.1-sol" and x["requested_reasoning_effort"]=="ultra"
        assert x["input_bindings"]=={"manual":case["shared"]["manual"],"execution_prompt":case["shared"]["execution_prompt"],"common_execution_protocol":case["shared"]["common_execution_protocol"],"packet":case["packet"]}
        assert set(x["dimensions"])==set(DIMS)
        for d in DIMS:
            z=x["dimensions"][d]; assert z["value"] in (0,1,None) and isinstance(z.get("reason"),str) and isinstance(z.get("evidence"),list)
    except Exception as e:
        return {"source_id":sid,"state":"technical_invalid","error":f"{type(e).__name__}: {e}","first":bind(first)}
    return {"source_id":sid,"state":"technical_valid","first":bind(first),"labels":{d:x["dimensions"][d]["value"] for d in DIMS}}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--setup",action="store_true"); ap.add_argument("--dispatch"); ap.add_argument("--dispatch-all",action="store_true"); ap.add_argument("--receive",action="store_true"); args=ap.parse_args()
    ids=setup()
    if args.setup: print(json.dumps({"status":"prepared","source_N":len(ids),"out":str(OUT)},ensure_ascii=False)); return
    if args.dispatch: print(json.dumps(dispatch(args.dispatch),ensure_ascii=False)); return
    if args.dispatch_all:
        todo=[s for s in ids if not (OUT/"cases"/s/"attempt-0001").exists()]
        with ThreadPoolExecutor(max_workers=4) as pool:
            results=[f.result() for f in as_completed([pool.submit(dispatch,s) for s in todo])]
        print(json.dumps({"started_N":len(todo),"results":results},ensure_ascii=False)); return
    if args.receive:
        rs=[receive(s) for s in ids]; save_new(OUT/"technical-reception.json",{"at_utc":datetime.now(timezone.utc).isoformat(),"results":rs,"technical_valid_N":sum(r["state"]=="technical_valid" for r in rs)})
        print(json.dumps({"technical_valid_N":sum(r["state"]=="technical_valid" for r in rs),"total_N":len(rs)},ensure_ascii=False)); return
    ap.error("choose --setup, --dispatch SOURCE_ID, --dispatch-all, or --receive")
if __name__=="__main__": main()
