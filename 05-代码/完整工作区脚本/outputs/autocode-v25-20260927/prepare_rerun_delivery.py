"""Prepare readable delivery payloads only after complete prediction seal/analysis."""
from pathlib import Path
import json
from analyze_current_reruns import load_sealed_predictions,load_reference_units,sha
from comparison_statistics import DIMS,label
import math

HERE=Path(__file__).resolve().parent
NAME={'rules_baseline':'自动编码旧版','rules_v25':'自动编码新版','llm_gpt56_sol':'LLM gpt-5.6-sol'}

def as_text(value):
    return value if isinstance(value,str) else json.dumps(value,ensure_ascii=False)

LONG_HEADER=['编号','来源工作表','原表行','字段','行序','原文逐行','换行']
def fit_long_text(rows,headers,widths,sheet,long_rows):
    for i,row in enumerate(rows,2):
        for j,value in enumerate(row):
            if not isinstance(value,str):continue
            lines=sum(max(1,math.ceil(sum(1.75 if ord(c)>255 else 1 for c in line)/max(8,widths[j]-2))) for line in value.split('\n'))
            if max(30,lines*14+8)<=409:continue
            parts=value.splitlines(keepends=True);rebuilt=''
            for k,part in enumerate(parts,1):
                text=part.rstrip('\r\n');ending=part[len(text):]
                tag={'':'无','\n':'LF','\r':'CR','\r\n':'CRLF'}[ending]
                long_rows.append([row[0],sheet,i,headers[j],k,text,tag]);rebuilt+=text+ending
            assert rebuilt==value,'Long text must remain exactly reconstructible'
            row[j]=f'完整内容见「长文本逐行」：编号 {row[0]}，{sheet} 第{i}行，字段「{headers[j]}」。'

def main():
    rules,llm,inputs,seal=load_sealed_predictions()
    qa_by_id={}
    llm_root=HERE/'llm_runs/gpt56-sol-v13-native-1'
    for batch in json.loads((llm_root/'first_output_QA.json').read_text()):
        if not batch['errors']:continue
        raw=json.loads((llm_root/batch['shard']/batch['output']).read_text())
        ids=[r['id'] for r in raw['rows']]
        for error in batch['errors']:
            prefix=error.split(':',1)[0]
            affected=[prefix] if prefix in ids else ids
            for rid in affected:qa_by_id.setdefault(rid,[]).append(error)
    sets={};allunits=[];summaries=[]
    for scope,title in [('current1268','1268条开发对照'),('H427','427条保留框')]:
        path=HERE/'rerun_comparisons'/scope/'metrics.json'
        report=json.loads(path.read_text())
        binding=json.loads((path.parent/'analysis_binding.json').read_text())
        assert sha(path)==binding['output_sha256']
        units,_=load_reference_units(scope,rules,llm,inputs);sets[scope]=units
        allunits += [(scope,u) for u in units]
        rows=[]
        for d in DIMS:
            for method in ['rules_v25','llm_gpt56_sol','rules_baseline']:
                for c in ['A','C']:
                    result=report['scenarios']['primary']['methods'][c][d]
                    m=result['by_method'][method]
                    conf=m['common_units_weighted']['confusion_on_joint_determinate']
                    own=m['all_units_unweighted']
                    rows.append([d,NAME[method],c,None,None,None,
                        own['joint_determinate_coverage'],result['common_unit_n'],
                        own['prediction_pending_n_or_weight'],own['reference_pending_n_or_weight'],
                        None,*[conf[k] for k in ['TP','FP','FN','TN']]])
        summaries.append({'name':title,'scope':scope,
            'note':'当前A/C为AI参考。共同可判样本的指标；各自覆盖率另列。'+('历史设计权重只作开发描述。' if scope=='current1268' else '剩余框全数427条，权重1，不外推原总体。'),
            'header':['维度','方法','参考','精确率','召回率','F1','自身可判覆盖','共同可判n','机器待定n','参考待定n','', 'TP（加权）','FP（加权）','FN（加权）','TN（加权）'],
            'rows':rows,'source':str(path),'source_sha256':sha(path)})
    assert len(allunits)==len({u['id'] for _,u in allunits})==1695
    record_header=['编号','材料组','分析单元完整原文',*DIMS,*['理由_'+d for d in DIMS],
                   '原文证据','F子类型','I子类型','S质量依据','材料问题','输入审查','原文来源','页码']
    books=[]
    protocol=(HERE/'protocol-v1.3.md').read_text()
    clarifications=(HERE.parent/'validation-expansion-20260926/V600-frozen-inputs/protocol_clarifications.md').read_text()
    manual_rows=[[i+1,line] for i,line in enumerate((protocol+'\n\n'+clarifications).splitlines())]
    for c in ['A','C']:
        rows=[]
        for scope,u in allunits:
            r=u['references'][c];inp=inputs[u['id']]
            rows.append([u['id'],scope,inp['text'],*[label(r['labels'][d]) for d in DIMS],
                *[r['dimension_reasons'][d] for d in DIMS],as_text(r['evidence']),
                as_text(r.get('fairness_subtypes',[])),as_text(r.get('innovation_subtypes',[])),
                r.get('safety_quality_basis','未知'),r.get('material_issue',''),as_text(r.get('input_assessment',{})),
                inp.get('source_title',''),as_text(inp.get('pages',[]))])
        books.append({'filename':f'AI评审{c}-1695条-同版首次结果.xlsx','coder':c,'header':record_header,'rows':rows,
            'manual_header':['行号','共用规范及澄清'],'manual_rows':manual_rows,
            'notice':f'AI评审{c}首次结果。不是真人编码或裁定金标准。current1268与H427分开分析。完整上下文见配套“完整分析单元与语境.jsonl”，按编号回查。'})
    detail_header=['编号','材料组','历史设计权重','分析单元完整原文']
    for prefix in ['A','C','自动新版','LLM']:
        detail_header += [prefix+'_'+d for d in DIMS]
    detail=[]
    for scope,u in allunits:
        rows=[u['id'],scope,u['weight'],inputs[u['id']]['text']]
        for r in [u['references']['A'],u['references']['C'],u['predictions']['rules_v25'],u['predictions']['llm_gpt56_sol']]:
            rows += [label(r['labels'][d]) for d in DIMS]
        detail.append(rows)
    llm_header=['编号','完整原文',*DIMS,*['理由_'+d for d in DIMS],
                'F子类型','I子类型','S质量依据','材料问题','来源','页码','首次输出校验问题']
    llm_rows=[];llm_evidence=[]
    for rid,r in sorted(llm.items()):
        inp=inputs[rid]
        llm_rows.append([rid,inp['text'],*[label(r['labels'][d]) for d in DIMS],
            *[r['dimension_reasons'][d] for d in DIMS],
            as_text(r['fairness_subtypes']),as_text(r['innovation_subtypes']),r['safety_quality_basis'],
            as_text(r['material_issue']),inp.get('source_title',''),as_text(inp.get('pages',[])),
            '；'.join(qa_by_id.get(rid,[])) or '无'])
        llm_evidence.extend([[rid,e['dimension'],as_text(e['source']),e['quote'],'；'.join(qa_by_id.get(rid,[])) or '无'] for e in r['evidence']])
    result={'reference_books':books,'comparison_book':{'filename':'自动与LLM重跑-同版对照.xlsx','summaries':summaries,
        'detail_header':detail_header,'detail_rows':detail,'llm_header':llm_header,'llm_rows':llm_rows,
        'evidence_header':['编号','维度','位置','首次提交证据','首次输出校验问题'],'evidence_rows':llm_evidence,
        'method_notes':[
            '统一标准：CAL-5D-20260926-v1.3，五维定义及澄清完全相同。',
            '自动编码新版和LLM均对4,924条完整分析单元重新执行。621条语境材料不计入分母。',
            'LLM为用户指定的gpt-5.6-sol，推理强度high；每个分片为无继承历史的独立会话，分片内保留自身批次历史。',
            'A、C为AI评审角色，结果按首次提交保留，不是真人金标准。',
            '1,268条属于已观察及开发材料，历史设计权重仅作描述。',
            '新增427条来自登记剩余材料框的全数评审，权重均为1，不外推原4,924条总体。',
            '1,268与427不重叠，共1,695条。两部分指标分开报告。',
            '主表精确率、召回率、F1使用每维、每位参考下三种机器版本都可判定的相同子集。',
            '自身可判覆盖率为该机器与当前参考均非待定的比例；待定保留，不填成0。',
            'n.a.表示对应分母为0，指标未定义，不表示零分。',
            '本表为统计快照；若修改逐条编码，需要重跑配套统计脚本。完整上下文见“完整分析单元与语境.jsonl”，按编号回查。',
            '各自全体记录、三分类表、待定完成界限及子类型敏感性见配套统计JSON；完成界限不是置信区间。',
            '旧自动版本仅作同一新参考下的版本对照；没有使用旧作者标签代替当前A/C。',
            'LLM首次输出存在结构或引文校验问题的批次数：'+str(seal['batches_with_QA_issues'])+'。主分析保留首次完整标签，更正另存。',
            '相对AI参考的符合程度不直接等于真人效度、构念效度或实际部门权重。']},
        'LLM_prediction_seal_sha256':sha(HERE/'llm_runs/gpt56-sol-v13-native-1/prediction_seal.json')}
    # Excel cannot display more than 409 points of row height. Long multiline
    # cells are transferred intact to a per-line sheet with an explicit pointer.
    for book in books:
        book['long_text_header']=LONG_HEADER;book['long_text_rows']=[]
        fit_long_text(book['rows'],book['header'],[24,20,138,8,8,8,8,8,64,64,64,64,64,120,30,38,35,70,75,70,15],'编码记录',book['long_text_rows'])
    comp=result['comparison_book'];comp['long_text_header']=LONG_HEADER;comp['long_text_rows']=[]
    for rows,headers,widths,sheet in [
        (comp['detail_rows'],comp['detail_header'],[24,20,20,138]+[11]*20,'逐条对照'),
        (comp['llm_rows'],comp['llm_header'],[24,138]+[8]*5+[64]*5+[30,38,35,70,70,15,70],'LLM全量'),
        (comp['evidence_rows'],comp['evidence_header'],[24,8,12,155,70],'LLM证据')]:
        fit_long_text(rows,headers,widths,sheet,comp['long_text_rows'])
    comp['method_notes'].append('超过Excel可显示行高的多行原文或证据完整转存于“长文本逐行”，原位置明确指向；按编号、来源表、原表行与字段回查，未截断内容。')
    comp['method_notes'].append('部分LLM判定理由为模板句、证据为整段原文，解释粒度有限；原始记录保持首次提交状态。')
    long_cells=[]
    for book in books:
        for i,row in enumerate(book['rows'],2):
            for j,v in enumerate(row):
                if isinstance(v,str) and len(v)>32767:long_cells.append([book['filename'],i,j,len(v)])
    assert not long_cells,('Excel cell limit: use a linked complete context table without silent truncation',long_cells)
    p=HERE/'rerun_delivery_payload.json';assert not p.exists(),'Preserve existing payload'
    p.write_text(json.dumps(result,ensure_ascii=False)+'\n')
    print(json.dumps({'payload':str(p),'reference_rows_each':1695,'LLM_rows':4924,'workbooks':3,'sha256':sha(p)},ensure_ascii=False))

if __name__=='__main__':main()
