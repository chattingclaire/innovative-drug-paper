"""Future exclusive capacity13 execution; requires actual ROOT GO after all production terminal."""
import argparse
import json
from pathlib import Path
from bootstrap import runtime
import capacity13_common as common

def execute(go):
    doc = common.profile()
    run = Path(doc["base_campaign_manifest"]["path"]).parent
    controller, _, _ = runtime()
    return controller.execute(run, go)

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--go", required=True)
    print(json.dumps(execute(p.parse_args().go), ensure_ascii=False))
