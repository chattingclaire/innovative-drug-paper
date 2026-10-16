"""Revalidate the aggregated 4,924-row artifact against the effective inputs."""
import json,subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];RUN=HERE/'production-25-v29';VAL=ROOT/'outputs/llm-v29-method-audit-20261005/validate_binary_output.py'
inputs=[json.loads(line) for line in (HERE/'effective_blind_inputs_v29.jsonl').read_text().splitlines()]
rows=[json.loads(line) for line in (RUN/'all_predictions.jsonl').read_text().splitlines()]
output={'protocol_version':'CAL-5D-20260926-v1.3','execution_version':'LLM-binary-v29','release_stage':'final_binary_labels','rows':rows,'issue_records':json.loads((RUN/'all_issue_records.json').read_text())}
with tempfile.TemporaryDirectory(prefix='verify-v29-') as td:
 p=Path(td);(p/'input.json').write_text(json.dumps({'rows':inputs},ensure_ascii=False));(p/'output.json').write_text(json.dumps(output,ensure_ascii=False));proc=subprocess.run(['python3',str(VAL),str(p/'input.json'),str(p/'output.json')],capture_output=True,text=True)
(RUN/'full_output_validation.json').write_text(proc.stdout)
raise SystemExit(proc.returncode)
