"""Audit sealed development batches with different A/B anonymous IDs.

Never reads a submission until both sidecars exist; reports development only.
"""
import argparse
import hashlib
import importlib.util
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DIMENSIONS=('S','E','Ec','I','F')
spec=importlib.util.spec_from_file_location('prior_exact_math',ROOT/'scripts/audit_pilot.py')
math=importlib.util.module_from_spec(spec);spec.loader.exec_module(math)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
    rows=[json.loads(s) for s in p.read_text().splitlines() if s.strip()]
    result={r['id']:r for r in rows}
    assert len(rows)==len(result), f'Duplicate IDs: {p}'
    return result
def policy_strings(node):
    for k in ['text','headers','title','row_cells','caption']:
        v=node.get(k)
        if isinstance(v,str):yield v
        elif isinstance(v,list):yield from (x for x in v if isinstance(x,str))
def validate(coder, packets, labels):
    issues=[]
    assert set(packets)==set(labels), f'{coder} output ID coverage mismatch'
    for ident,row in labels.items():
        source=packets[ident]
        assert set(row['labels'])==set(DIMENSIONS) and set(row['evidence'])==set(DIMENSIONS)
        contexts={x['context_id']:list(policy_strings(x)) for x in source['contexts']}
        images={x['attachment_id'] for field in ['source_page_attachments','source_image_attachments'] for x in source.get(field,[])}
        for d in DIMENSIONS:
            value=row['labels'][d]; e=row['evidence'][d]
            assert value is None or (type(value) is int and value in [0,1]), (coder,ident,d)
            def issue(name,**extra):issues.append({'coder':coder,'id':ident,'dimension':d,'issue':name,**extra})
            if not e.get('reason','').strip():issue('missing_reason')
            q=e.get('current_quote','')
            if value==1 and not q:issue('positive_without_current_anchor')
            if q and q not in source['text']:issue('current_quote_not_exact',quote=q)
            for c in e.get('contexts_used',[]):
                cq=c.get('quote','');cid=c.get('context_id')
                if cid not in contexts:issue('unknown_context_id',context=c)
                elif not cq or not any(cq in s for s in contexts[cid]):issue('context_quote_not_exact',context=c)
            for aid in e.get('image_sources_used',[]):
                if aid not in images:issue('image_not_attached_to_record',attachment_id=aid)
            if value is None and not any(x.get('dimension')==d for x in row.get('material_requests',[])):
                issue('pending_without_specific_material_request')
    return issues

def main():
    parser=argparse.ArgumentParser();parser.add_argument('trial',type=Path);args=parser.parse_args()
    trial=args.trial.resolve();admin=trial/'admin'
    output=admin/'diagnostics.json';assert not output.exists(),'Preserve audit, create a new audit version'
    paths={c:{n:trial/c/n for n in ['packet.jsonl','labels.jsonl','manual.md','submission.json']} for c in 'AB'}
    for c in 'AB':
        for p in paths[c].values():assert p.exists(),f'Both sealed complete outputs required: {p}'
    mappings=json.loads((admin/'private_mapping.json').read_text())
    by_coder={c:{x['blind_id']:x for x in mappings if x['coder']==c} for c in 'AB'}
    packets={c:read(paths[c]['packet.jsonl']) for c in 'AB'}
    labels={c:read(paths[c]['labels.jsonl']) for c in 'AB'}
    assert sha(paths['A']['manual.md'])==sha(paths['B']['manual.md'])
    canonical={};mapped_labels={};quality=[]
    inputs={}
    for c in 'AB':
        assert set(packets[c])==set(by_coder[c])
        canonical[c]={};mapped_labels[c]={}
        for bid,p in packets[c].items():
            fid=by_coder[c][bid]['frame_id'];node=dict(p);node.pop('id')
            canonical[c][fid]=node;mapped_labels[c][fid]=labels[c][bid]
            for field in ['source_page_attachments','source_image_attachments']:
                for asset in p.get(field,[]):
                    img=trial/c/asset['relative_path'];assert sha(img)==asset['sha256']
        quality.extend(validate(c,packets[c],labels[c]))
        inputs[c]={n:{'path':str(p),'sha256':sha(p)} for n,p in paths[c].items()}
    assert canonical['A']==canonical['B'],'A/B source contents differ beyond anonymous IDs/order'
    metrics={};differences=[]
    for d in DIMENSIONS:
        cells=[0,0,0,0];nine=Counter();pending=[]
        for fid in sorted(canonical['A']):
            a=mapped_labels['A'][fid]['labels'][d];b=mapped_labels['B'][fid]['labels'][d]
            nine[f'{a if a is not None else "null"}|{b if b is not None else "null"}']+=1
            if a is not None and b is not None:cells[2*a+b]+=1
            else:pending.append({'frame_id':fid,'A':a,'B':b})
            if a!=b or a is None or b is None:
                differences.append({'frame_id':fid,'dimension':d,'A':a,'B':b,'text':canonical['A'][fid]['text'],
                                    'A_blind_id':mapped_labels['A'][fid]['id'],'B_blind_id':mapped_labels['B'][fid]['id'],
                                    'A_evidence':mapped_labels['A'][fid]['evidence'][d],
                                    'B_evidence':mapped_labels['B'][fid]['evidence'][d]})
        m=math.statistics(*cells)
        m.setdefault('cells',dict(zip(['A0_B0','A0_B1','A1_B0','A1_B1'],cells)))
        for key,value in [('A_0',cells[0]+cells[1]),('A_1',cells[2]+cells[3]),('B_0',cells[0]+cells[2]),('B_1',cells[1]+cells[3])]:
            m.setdefault(key,value)
        m.update({'total_n':len(canonical['A']),'pending_n':len(pending),'pending':pending,
                  'full_3x3':{f'{a}|{b}':nine[f'{a}|{b}'] for a in ['0','1','null'] for b in ['0','1','null']},
                  'population_CI':None,'CI_reason':'Purposive development material; no population probability inference',
                  'development_point_at_least_0_80':m['kappa'] is not None and m['kappa']>=.8})
        metrics[d]=m
    result={'status':'sealed_AI_development_diagnostics_not_formal_validation','n':len(canonical['A']),
            'computed_at_utc':datetime.now(timezone.utc).isoformat(),'identity':'AI','same_material_and_manual':True,
            'different_anonymous_ids_and_order':True,'inputs':inputs,'quality_issues':quality,
            'metrics':metrics,'disagreements_and_pending':differences,'first_submissions_modified':False,
            'reference_direction':'Symmetric A/B agreement; neither is treated as gold',
            'final_acceptance_claim':False}
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    fmt=lambda v:'NA' if v is None else f'{v:.4f}'
    lines=[f'# {trial.name}：开发判读封存诊断','',
           '双方是AI独立执行者，材料用于开发。此表不是真人独立信度或冻结后最终验收，不外推总体。首判与本轮提交分开保存。','',
           '|维度|可判n/全部n|A0B0/A0B1/A1B0/A1B1|A/B正例|待定n|Po|κ|正类一致性|负类一致性|',
           '|---|---|---|---|---|---|---|---|---|']
    for d,m in metrics.items():
        lines.append(f'|{d}|{m["n"]}/{m["total_n"]}|{list(m["cells"].values())}|{m["A_1"]}/{m["B_1"]}|{m["pending_n"]}|{fmt(m["agreement"])}|{fmt(m["kappa"])}|{fmt(m["positive_specific_agreement"])}|{fmt(m["negative_specific_agreement"])}|')
    lines+=['','注：各维使用双方0/1可判对；未知九格、实际原文理由、材料/手册SHA及格式问题见JSON。四格方向为行A、列B。正类一致性与以同表一方作参照的F1数学相同，不作为另一份效度证据。没有概率抽样，故不报告总体95%区间。',
            f'证据格式检查：{len(quality)}项待处理；不覆盖原始提交。']
    (admin/'diagnostics.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'n':result['n'],'quality_issues':len(quality),
                      'metrics':{d:{k:m[k] for k in ['n','pending_n','kappa']} for d,m in metrics.items()}},ensure_ascii=False))

if __name__=='__main__':main()
