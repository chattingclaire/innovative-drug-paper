"""Future hard-cap3 all-five controller; the ROOT must issue genuine GO."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from transport_common import campaign, CONDITIONS, route, check, binding, load, save, now, validate_GO, exclusive
from runner import run_attempt
from receiver import receive, validate_selection

def run_batch(run, d, condition, n, go):
    r = route(d, condition, n, 1)
    selection = Path(r["selection_directory"])
    if (selection / "root-selection.json").exists():
        validate_selection(d, condition, n, load(selection / "root-selection.json"))
        return {"state": "already_selected", "selection": binding(selection / "root-selection.json")}
    if (selection / "root-zero-call-block.json").exists():
        return {"state": "not_called", "block": binding(selection / "root-zero-call-block.json")}
    for attempt in (1, 2, 3):
        item = route(d, condition, n, attempt)
        receipt = selection / f"root-attempt-reception-{attempt:04d}.json"
        if receipt.exists():
            old = load(receipt)
            if old["state"] != "technical_invalid_whole_batch":
                if old["state"] == "technical_valid_whole_batch":
                    return receive(run, condition, n, attempt)  # Finish ROOT-only interrupted selection.
                return {"state": "reception_incomplete_need_ROOT_attention", "receipt": binding(receipt)}
            check(old["completion"])
            continue
        slot = Path(item["output_directory"])
        if (slot / "ROOT-process-completion.json").exists():
            result = receive(run, condition, n, attempt)  # No repeat model call.
        elif any(slot.iterdir()):
            return {"state": "uncertain_partial_attempt_do_not_dispatch", "slot": str(slot)}
        else:
            result = run_attempt(run, condition, n, attempt, go)
        if result["state"] != "technical_invalid_whole_batch":
            return result
    return {"state": "technical_exhausted", "actual_attempts": 3, "no_imputed_labels": True}

def execute(run, go):
    run, d = campaign(run)
    go_binding = validate_GO(run, d, go)
    with exclusive(run / "ROOT-controller.lock"):
        epoch = run / "ROOT-controller-runs" / now().replace(":", "").replace("+", "_")
        epoch.mkdir(parents=True, exist_ok=False)
        save(epoch / "start.json", {"at_utc": now(), "GO": go_binding, "campaign_manifest": binding(run / "run-manifest.json"), "actual_concurrency_cap": 3, "condition_order": list(CONDITIONS), "planned_submission_batch_order": list(range(1, 88)), "physical_start_and_completion_order_preserved_separately": True})
        results = {}
        for condition in CONDITIONS:
            with ThreadPoolExecutor(max_workers=3) as pool:
                futures = [pool.submit(run_batch, run, d, condition, n, go) for n in range(1, 88)]
                rows = []
                for n, f in enumerate(futures, 1):
                    try:
                        result = f.result()
                    except Exception as error:
                        result = {"state": "ROOT_execution_or_reception_error_no_retry", "error": {"type": type(error).__name__, "message": str(error)}}
                    rows.append({"batch_number": n, **result})
            results[condition] = rows
            terminal = all(r["state"] in ("selected", "already_selected", "not_called", "technical_exhausted") for r in rows)
            save(epoch / f"{condition}-result.json", {"at_utc": now(), "all_terminal": terminal, "results": rows})
            if not terminal:
                save(epoch / "result.json", {"all_terminal": False, "need_ROOT_attention": True, "results": results, "no_later_condition_started": True})
                return {"all_terminal": False, "need_ROOT_attention": True, "controller_epoch": str(epoch)}
        result = save(epoch / "result.json", {"at_utc": now(), "all_terminal": True, "all_five_conditions_terminal": True, "results": results, "statistics_computed": False})
        return {"all_terminal": True, "result": result, "statistics_computed": False}

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", required=True)
    p.add_argument("--go", required=True)
    a = p.parse_args()
    print(json.dumps(execute(a.run, a.go), ensure_ascii=False))
