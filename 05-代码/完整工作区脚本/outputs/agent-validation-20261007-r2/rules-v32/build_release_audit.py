"""Audit actual candidate execution without loading any A/C/new evaluation."""
from pathlib import Path
from hashlib import sha256
from collections import Counter, defaultdict
from datetime import datetime
import ast
import json

ROOT=Path(__file__).resolve().parent
OLD=ROOT.parents[1]/'recall-revision-20261007'
def sha(path):return sha256(Path(path).read_bytes()).hexdigest()
def rows(path):return [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]

def main():
    freeze_path=ROOT/'candidate_freeze.json';freeze=json.loads(freeze_path.read_text())
    for path,digest in freeze['production_runtime_sha256'].items():assert sha(path)==digest,path
    for path,digest in freeze['test_and_change_spec_sha256'].items():assert sha(path)==digest,path
    assert sha(freeze['protocol_path'])==freeze['protocol_sha256']
    assert sha(freeze['full_manual_path'])==freeze['full_manual_sha256']
    assert sha(freeze['input_path'])==freeze['input_sha256']
    preds_path=ROOT/'all_predictions.jsonl';run_path=ROOT/'all_predictions.run.json'
    run=json.loads(run_path.read_text())
    assert run['version']==freeze['version'] and run['n']==4924 and run['pending_n']==0
    assert run['input_sha256']==freeze['input_sha256'] and run['prediction_sha256']==sha(preds_path)
    assert run['reference_labels_loaded'] is False
    for path,digest in run['runtime_code_sha256'].items():assert sha(path)==digest,path
    inputs={x['id']:x for x in rows(freeze['input_path'])}
    old_path=OLD/'rules-v31/all_predictions_completed_material_v3.jsonl'
    old={x['id']:x for x in rows(old_path)}
    current={x['id']:x for x in rows(preds_path)}
    assert set(inputs)==set(old)==set(current) and len(inputs)==4924
    rule_basis=defaultdict(set);counts=Counter();changes=[];delta=Counter()
    for id,row in current.items():
        rec=inputs[id]['input'];new=row['prediction'];before=old[id]['prediction']
        assert new['version']==freeze['version']
        assert new['semantic_protocol']=='CAL-5D-20260926-v1.3+operation-v1.4'
        assert new['unit_text_sha256']==sha256(rec['unit_text'].encode()).hexdigest()
        assert new['labels'].keys()==before['labels'].keys()
        assert all(new['labels'][d]==before['labels'][d] for d in ['S','E','Ec']),id
        for e in new['evidence']:
            assert rec['unit_text'][e['start']:e['end']]==e['text']
            counts[e['rule']]+=1;rule_basis[e['rule']].add(e.get('protocol_basis','Legacy declaration linked by source-rule index to the frozen v1.3 dimension.'))
        ds=[d for d in ['S','E','Ec','I','F'] if new['labels'][d]!=before['labels'][d]]
        if ds:
            for d in ds:delta[(d,before['labels'][d],new['labels'][d])]+=1
            changes.append({'id':id,'original_id':row['original_id'],'changed_dimensions':ds,
                'old_labels':before['labels'],'candidate_labels':new['labels'],'unit_text':rec['unit_text'],
                'candidate_v32_evidence':[e for e in new['evidence'] if e['rule'].startswith('V32_')],
                'candidate_v32_suppressions':[e for e in new['suppressions'] if e['rule'].startswith('V32_')],
                'old_evidence_on_changed_dimensions':[e for e in before['evidence'] if e['dimension'] in ds],
                'verified_parent_context':rec.get('verified_parent_context',[]),
                'paragraph_context':rec.get('paragraph_context',[]),
                'source_path':rec.get('unit_source',rec['source']),
                'source_sha256':rec.get('unit_source_sha256',rec['source_sha256']),
                'candidate_path':rec['candidate_file'],'candidate_sha256':rec['candidate_sha256'],
                'unit_sha256':new['unit_text_sha256'],
                'why_not_an_accuracy_estimate':'This is a change of actual predictions under a previously frozen candidate; neither old predictions nor AI/human labels are treated as truth.'})
    source_records={}
    for path,digest in freeze['production_runtime_sha256'].items():
        p=Path(path);content=p.read_text();tree=ast.parse(content)
        source_records[path]={'sha256':digest,'lines':content.splitlines(),
            'strings':[(n.value,n.lineno) for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str)]}
    index=[]
    for rule in sorted(counts):
        hits=[]
        for path,rec in source_records.items():
            exact=[n for text,n in rec['strings'] if text==rule]
            if exact:hits.extend({'path':path,'sha256':rec['sha256'],'line':n,'lookup':'exact_rule_literal'} for n in exact)
        if not hits and rule in ['V27_I_dimension_evaluation_list','V27_F_dimension_evaluation_list']:
            for path,rec in source_records.items():
                hits.extend({'path':path,'sha256':rec['sha256'],'line':i+1,'lookup':'explicit_dynamic_dimension_suffix'}
                    for i,line in enumerate(rec['lines']) if "'_dimension_evaluation_list'" in line)
        assert hits,('Active rule lacks a source declaration',rule)
        index.append({'rule':rule,'actual_evidence_occurrences':counts[rule],
            'protocol_basis_recorded':sorted(rule_basis[rule]),'implementation_source_declarations':hits})
    change_path=ROOT/'actual_prediction_changes_vs_v31.json'
    change_data={'status':'actual_prediction_differences_only_not_validation_metrics','n':4924,
        'changed_unit_count':len(changes),'changed_label_count':sum(delta.values()),
        'direction_counts':{f'{d}:{a}->{b}':n for (d,a,b),n in sorted(delta.items())},
        'S_E_Ec_labels_all_unchanged':True,'cases':changes,
        'old_prediction_path':str(old_path),'old_prediction_sha256':sha(old_path),
        'candidate_prediction_path':str(preds_path),'candidate_prediction_sha256':sha(preds_path),
        'input_path':freeze['input_path'],'input_sha256':freeze['input_sha256'],
        'new_confirmation_outputs_or_reference_labels_loaded':False}
    assert not change_path.exists();change_path.write_text(json.dumps(change_data,ensure_ascii=False,indent=2)+'\n')
    idx_path=ROOT/'active_rule_source_index.json';assert not idx_path.exists()
    idx_path.write_text(json.dumps({'status':'all_actual_active_evidence_rules_have_source_declarations','active_rule_count':len(index),
        'manual':{'path':freeze['full_manual_path'],'sha256':freeze['full_manual_sha256']},
        'operation_note':{'path':freeze['protocol_path'],'sha256':freeze['protocol_sha256']},'rules':index},ensure_ascii=False,indent=2)+'\n')
    checks={'status':'passed_actual_full_rule_execution_and_immutable_source_audit','n':4924,
        'all_binary_no_pending':True,'all_literal_evidence_spans_valid':True,'old_S_E_Ec_preserved':True,
        'frozen_code_manual_input_hashes_unchanged':True,'all_active_rule_sources_indexed':True,
        'all_219_development_regressions_passed':True,'new_confirmation_or_agent_results_accessed':False,
        'scope':'Structural, material and development-regression QA; not independent classification accuracy, human validation, or publication eligibility.',
        'source_sha256':{str(p):sha(p) for p in [freeze_path,run_path,preds_path,change_path,idx_path,ROOT/'runtime/semantic_test_results.json']}}
    qa_path=ROOT/'actual_execution_QA.json';assert not qa_path.exists();qa_path.write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
    release={'status':'frozen_actual_4924_rule_candidate_not_confirmatory_validated','version':freeze['version'],
        'released_at':datetime.now().astimezone().isoformat(),'n':4924,
        'input_path':freeze['input_path'],'input_sha256':freeze['input_sha256'],
        'prediction_path':str(preds_path),'prediction_sha256':sha(preds_path),
        'run_manifest_path':str(run_path),'run_manifest_sha256':sha(run_path),
        'freeze_path':str(freeze_path),'freeze_sha256':sha(freeze_path),
        'change_path':str(change_path),'change_sha256':sha(change_path),
        'rule_source_index_path':str(idx_path),'rule_source_index_sha256':sha(idx_path),
        'QA_path':str(qa_path),'QA_sha256':sha(qa_path),
        'production_runtime_sha256':freeze['production_runtime_sha256'],
        'new_confirmation_or_agent_outputs_read_for_candidate_selection':False,
        'reference_labels_changed':False,'old_outputs_changed':False,'manuscript_connected':False}
    release_path=ROOT/'release_manifest.json';assert not release_path.exists();release_path.write_text(json.dumps(release,ensure_ascii=False,indent=2)+'\n')
    md=['# 自动规则v32候选：实际运行与开发修订','',
        '采用冻结v1.3五维手册及共用操作说明v1.4，旧版本和原参照保持封存。仅根据已暴露开发文本及正反语义控制修订通用实现，未读取新确认样本、agent判断或新指标。','',
        f'全量4924条已实际运行；219个开发回归测试通过。相对v31有{len(changes)}个单元、{sum(delta.values())}个I/F标签发生变化；S/E/Ec逐条保持。变化量不是准确率改进证明，确认比较可能同时出现进步和退步。','',
        '修订覆盖普通比较与具体改良、文件宗旨与实体支持、专有数据权利与一般保密、推荐/评议与实际保障，以及已核验列表父谓词的恢复。实际未满足治疗需求的较宽F构念保留，不额外要求支付或断供障碍。','',
        '|ID|变更|新通用规则|原文|','|---|---|---|---|']
    for c in changes:
        desc='; '.join(f"{d}:{c['old_labels'][d]}→{c['candidate_labels'][d]}" for d in c['changed_dimensions'])
        why=','.join(sorted({e['rule'] for e in c['candidate_v32_evidence']+c['candidate_v32_suppressions']}))
        md.append(f"|{c['id']}|{desc}|{why}|{c['unit_text'].replace('|','／').replace(chr(10),' ')}|")
    md+=['','候选与实际输出已封存；后续统计须使用本release绑定的同版输入及预测，不能按确认分数挑版本或回填原参照。此候选未接入论文。']
    (ROOT/'规则修订与实际变化.md').write_text('\n'.join(md)+'\n')
    print(json.dumps({'status':checks['status'],'changed_units':len(changes),'changed_labels':sum(delta.values()),'direction_counts':change_data['direction_counts'],
        'prediction_sha256':sha(preds_path),'run_sha256':sha(run_path),'release_sha256':sha(release_path),'active_rule_count':len(index)},ensure_ascii=False))

if __name__=='__main__':main()
