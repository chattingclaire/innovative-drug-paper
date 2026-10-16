#!/usr/bin/env python3
"""Arithmetic supplement: actual saved machines against actual latest A and B."""
from pathlib import Path
from fractions import Fraction
import ast,json,hashlib,datetime,math,warnings

ROOT=Path('/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010')
OUT=Path(__file__).resolve().parent
OLD=ROOT/'07-statistics/agent-blind-tables-current-recompute-sol'
DIMS=['S','E','Ec','I','F'];MISSING='unfilled_or_execution_failure';CHECKS=[]
INPUTS={}
def binding(p):
    p=Path(p);b=p.read_bytes();e={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};INPUTS[str(p)]=e;return e
def load(p):binding(p);return json.loads(Path(p).read_bytes())
def save(name,x):
    p=OUT/name
    if p.exists():raise RuntimeError('do not overwrite first supplemental output')
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return binding(p)

# Reuse exact saved arithmetic functions without executing its data loads/output code.
oldscript=OLD/'recompute.py';binding(oldscript)
tree=ast.parse(oldscript.read_text());defs=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in ['val','metric','compare']]
assert {x.name for x in defs}=={'val','metric','compare'}
exec(compile(ast.Module(body=defs,type_ignores=[]),str(oldscript),'exec'),globals())
seal=load(OLD/'seal.json');reviewpath=OLD/'review-rows.json'
actual=binding(reviewpath);expected=next(x for x in seal['files'] if x['path']==str(reviewpath));assert actual==expected
review=load(reviewpath);records=review['records'];assert len(records)==77
order=[x['id'] for x in records];assert len(set(order))==77
by={x['id']:x for x in records}
rulepath=ROOT/'06-coding/rule-v17-bounded-role-merge-development-sol/run77-first/predictions.jsonl';binding(rulepath)
rule={x['id']:x for x in [json.loads(z) for z in rulepath.read_bytes().splitlines() if z.strip()]};assert len(rule)==77
native={};partial={};firsts=[]
for rec in records:
    for field,target in [('native38',native),('partial7',partial)]:
        v=rec['machine_candidates'][field]
        if v is None:continue
        p=Path(v['original_first']['path']);actual=binding(p);assert actual==v['original_first']
        row=load(p);assert row['labels']==v['item']['labels']
        target[rec['id']]=row
        firsts.append({'id':rec['id'],'candidate_group':field,'first':actual,'runtime_thread_id':v['runtime_thread_id'],'technical_state':v['technical_state'],'manual_sha256':v['manual_sha256']})
assert len(native)==38 and len(partial)==7

comparisons=[];derived=[]
for group,items,assigned in [('rule17_complete77',rule,77),('native38_saved_complete_format_subset',native,77),('partial7_saved_per_record_subset',partial,16)]:
    for coder in ['A','B']:
        rows=[];provenance=[]
        for sid in order:
            if sid not in items:continue
            event=by[sid][coder]['latest'];machine=items[sid]
            rows.append((sid,machine['labels'],event['labels'],by[sid]['department']))
            provenance.append({'id':sid,'department':by[sid]['department'],'machine_labels':machine['labels'],'table_reference_labels':event['labels'],'table_coder':coder,'actual_latest_round':event['round'],'actual_table_first_output':event['first_output'],'table_manual':event['manual'],'table_source_packet':event.get('source_packet'),'table_source_bundle_sha256':event.get('source_bundle_sha256_as_saved'),'difference_dimensions':[d for d in DIMS if machine['labels'][d]!=event['labels'][d]],'ROOT_reference_v3_used':False})
        x=compare(group+'_vs_actual_latest_'+coder,rows,'machine_vs_reference',assigned,'Actual latest AI '+coder+' table is comparison reference by user instruction; mixed development source rounds, not human gold. ROOT v3 values not copied into A/B. Partial/missing candidates remain failures, no 0 imputation.')
        x['actual_table_reference_coder']=coder;x['ROOT_AI_reference_v3_used']=False
        x['reference_role']='actual saved latest AI development table, not credible human gold'
        x['candidate_first_provenance']=provenance
        comparisons.append(x);derived.append({'comparison':x['name'],'rows':provenance})

# One existing sklearn process crosschecks all six comparisons, retaining exact NA.
import sklearn
from sklearn.metrics import cohen_kappa_score,precision_score,recall_score,f1_score,confusion_matrix
cross=[]
with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    for x in CHECKS:
        rows=x['binary_rows'];pred=[a for sid,a,b in rows];ref=[b for sid,a,b in rows];n=len(rows);cells=x['cells'];ms=x['metrics']
        cm=confusion_matrix(pred,ref,labels=[0,1]).ravel().tolist() if n else [0,0,0,0]
        assert cm==[cells['d'],cells['c'],cells['b'],cells['a']]
        k=cohen_kappa_score(ref,pred,labels=[0,1]) if n else float('nan');ex=ms['kappa']['value'];assert (math.isnan(k) and ex is None) or (ex is not None and abs(k-ex)<1e-12)
        vals={'kappa':None if math.isnan(k) else float(k)}
        for key,fn in [('precision',precision_score),('recall',recall_score),('F1',f1_score)]:
            v=float(fn(ref,pred,zero_division=0));ex=ms[key]['value']
            if ex is not None:assert abs(v-ex)<1e-12
            vals[key]=None if ex is None else v
        cross.append({'comparison':x['comparison'],'dimension':x['dim'],'binary_N':n,'matrix_rows_machine_columns_actual_table':cm,'values':vals,'passed':True})
save('sklearn-crosscheck.json',{'sklearn_version':sklearn.__version__,'process_N':1,'checks_N':len(cross),'all_passed':True,'checks':cross,'NA':'exact zero denominators stay NA; sklearn zero_division0 not imputed as metric'})
paired_equal=all(rec['A']['latest']['labels']==rec['B']['latest']['labels'] for rec in records)
metrics={'version':'actual-agent-modified-table-reference-arithmetic-addendum-v1','created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'comparison_reference':'用户明确指定实际Agent修改A/B表；两份各自真实保存值分别作参照，非ROOTv3替代。','actual_A_B_latest_labels_equal_for_all77':paired_equal,'comparisons':comparisons,'N_comparisons':6,'human_gold':False,'formal_acceptance':False,'identity':'AI非盲算术补充，requested GPT-6.1 Sol ultra，实际provider未知','all_real_firsts_retained':True,'no_label_changes_or_new_semantic_decisions':True,'no_new_model_calls':0,'CI95':None,'CI_reason':'历史曝光非概率开发资料，沿既有contract不报总体95%CI；不能把修订后分数叫原盲κ。','incomplete':'native38 only38/77; partial7 only7/16, not spliced77; no zeros for missing;800无实际A/B/可信参照，分类NA。','formula_orientation':'rows=machine, columns=actual latest AI A/B table; TP=a,FP=b,FN=c,TN=d; specificity=TN/(FP+TN); NPV=TN/(FN+TN)','kappa1_explanation':'同一比较中双方可判二元标签全一致且Pe<1时κ=1；只证明这批保存值相同，不证明政策判断正确、真人已复核或总体机器准确。全常数一致导致Pe=1则κ是NA，不填1。','historical_report_preserved':'旧vs ROOTv3全部封存不改，本补充成为按用户指定A/B修改表计算的机器主视图。'}
save('metrics-addendum.json',metrics)
save('derived-table-reference-rows.json',derived)
save('input-bindings.json',{'inputs':[x for p,x in INPUTS.items() if not Path(p).is_relative_to(OUT)],'original_firsts_metadata':firsts,'reuse':'AST仅导入旧sealed算术函数val/metric/compare，不执行旧cohort/编码/QA。','A_B_actual_firsts':'review-rows的actual latest事件，包含各真实labels/lineSHA/manual/source，未用v3替代。'})
lines=['已按用户指定的实际Agent修改A、B表分别复算六组机器指标。A/B最新保存值逐条相同，但仍分别绑定各自原提交；不复制ROOTv3裁定。','','| 机器与实际表 | 保存/分配 | S κ | E κ | Ec κ | I κ | F κ |','|---|---:|---:|---:|---:|---:|---:|']
for x in comparisons:
    vals=[x['dimensions'][d]['metrics']['kappa']['value'] for d in DIMS]
    lines.append('| '+x['name']+' | '+str(x['saved_pairs_N'])+'/'+str(x['assigned_records_N'])+' | '+' | '.join('NA' if v is None else f'{v:.6f}' for v in vals)+' |')
lines+=['','四格、各指标方向与分母、P/R/F1、specificity、NPV、Po/Pe/Ppos/Pneg、类别/待定/失败/覆盖和真实分歧ID均保存在metrics-addendum.json。','','κ=1表示当前两组可判标签完全一致且机会一致率未退化；不证明判断本身正确。常数一致Pe=1的κ为NA。原A/B开发κ=1不能替代真人执行或正式验证；不同source/manual修订链与历史AI身份保持原样。','','native38仅38/77，partial7仅7/16，不拼成77、不补0。对ROOTv3的旧报告保留为历史附表；本补充才是按用户指定修改A/B表的机器主结果。开发非概率，既有CI契约不报总体区间。800独立A/B/可信参照尚无，classification仍NA。','','existing sklearn '+sklearn.__version__+'单进程30项交叉复算全部通过，无新语义编码、模型运行或旧输出修改。']
p=OUT/'report.md';assert not p.exists();p.write_text('\n'.join(lines)+'\n',encoding='utf-8')
files=[binding(OUT/x) for x in ['recompute-addendum.py','metrics-addendum.json','derived-table-reference-rows.json','sklearn-crosscheck.json','input-bindings.json','report.md']]
seal=save('seal.json',{'seal_type':'actual-A-B-modified-table-reference-arithmetic-only','created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'member_N':len(files),'files':files,'old_files_changed':False,'actual_new_model_calls':0,'human_executed':False,'formal_acceptance':False,'seal_excludes_itself':True})
print(json.dumps({'metrics':binding(OUT/'metrics-addendum.json'),'seal':seal,'crosschecks_N':len(cross),'A_B_actual_equal':paired_equal},ensure_ascii=False))
