#!/usr/bin/env python3
"""Diagnose source construction only after storage failure, never call judge."""
import copy
import importlib
import json
from pathlib import Path
import sys
import traceback
sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(OUT/'code-snapshot'))
source_packet = importlib.import_module('source_packet')
relations = importlib.import_module('relations')
plan = json.loads((OUT.parent/'controls12-fixed-before-execution.json').read_text())
results = []
with (OUT/'source-construction-diagnosis.jsonl').open('x', encoding='utf-8') as stream:
    for case in plan['cases']:
        item = {'name': case['name'], 'diagnostic_stage': 'SourcePacket_and_RelationView_only',
                'judge_calls_N': 0, 'not_a_recovery_of_original_lost_judge_outputs': True}
        try:
            unit = source_packet.semantic_unit(copy.deepcopy(case['synthetic_bundle']))
            view = relations.RelationView(unit)
            item.update(source_view_constructed=True, traces=view.traces(),
                        source_requests=copy.deepcopy(getattr(view, 'source_requests', [])))
        except Exception as error:
            item.update(source_view_constructed=False,
                        error={'type': type(error).__name__, 'message': str(error),
                               'traceback': traceback.format_exc()})
        stream.write(json.dumps(item, ensure_ascii=False, allow_nan=False)+'\n')
        stream.flush()
        results.append(item)
with (OUT/'source-construction-diagnosis.json').open('x', encoding='utf-8') as stream:
    json.dump({'status': 'independent_diagnosis_no_judge', 'judge_calls_N': 0,
               'original_first_values_not_reconstructed': True, 'cases': results},
              stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({'view_success_N': sum(x['source_view_constructed'] for x in results),
                  'view_failure_N': sum(not x['source_view_constructed'] for x in results),
                  'errors': [{'name': x['name'], 'error': x['error']} for x in results if 'error' in x],
                  'judge_calls_N': 0}, ensure_ascii=False))
