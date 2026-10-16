"""Seal the preparation inventory for independent review. No CLI/model."""
import ast
import json
import sys
from pathlib import Path

sys.dont_write_bytecode=True
from candidate08_support import HERE,FREEZE,PLAN,read,sha,binding,check_plan,source_paths


def main():
    assert not FREEZE.exists()
    target=HERE/'preparation_manifest.json'
    assert not target.exists(),'Preparation inventory is immutable; preserve earlier versions.'
    check_plan(read(PLAN))
    assert sha(HERE/'candidate08_prompt_PROPOSED.txt')==read(HERE/'prompt_lock_before_independent_inputs.json')['prompt']['sha256']
    for p in HERE.rglob('*.py'):ast.parse(p.read_text())
    files=[binding(p) for p in sorted(HERE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p!=target]
    obj={'status':'FINAL_PREPARATION_PENDING_INDEPENDENT_TECHNICAL_PREFLIGHT_AND_ROOT_FREEZE',
        'model':'gpt-5.6-sol','reasoning_effort':'medium','nominal_logical_requests':17,'max_identical_technical_attempts':51,
        'current_model_calls':0,'current_real_CLI_invocations':0,'locked_prompt_sha256':sha(HERE/'candidate08_prompt_PROPOSED.txt'),
        'independent16_original_or_expected_not_semantically_read_by_prompt_author':True,
        'core_files':files,'source_bindings':[binding(p) for p in source_paths()]}
    target.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':obj['status'],'path':str(target),'sha256':sha(target),'core_files':len(files),'source_bindings':len(obj['source_bindings'])},ensure_ascii=False))


if __name__=='__main__':main()
