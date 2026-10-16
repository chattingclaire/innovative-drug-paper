from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib,json,os,tempfile
ROOT=Path('/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/validation-expansion-20260926/D668/agent-A')
DIMS=['S','E','Ec','I','F']
def row(n,labels,reasons,evidence,rationale,basis,F=None,I=None,quality='no_quality_basis',status='sufficient',issue='无'):
    assert len(labels)==len(reasons)==5
    return {'id':f'D668-{n:04d}','labels':dict(zip(DIMS,labels)),'dimension_reasons':dict(zip(DIMS,reasons)),'evidence':evidence,'rationale':rationale,'material_issue':issue,'fairness_subtypes':F or [],'innovation_subtypes':I or [],'safety_quality_basis':quality,'input_assessment':{'status':status,'basis':basis}}
def publish(batch,rows,questions=None):
    inp=(ROOT/f'材料-{batch:02d}.json').read_bytes()
    packet=json.loads(inp)
    assert len(rows)==len(packet['rows'])==(18 if batch==27 else 25)
    assert [r['id'] for r in rows]==[r['id'] for r in packet['rows']]
    for r in rows:
        assert set(r['labels'])==set(r['dimension_reasons'])==set(DIMS)
        assert all((type(v) is int and v in (0,1)) or v=='待定' for v in r['labels'].values())
        assert all(isinstance(v,str) and v.strip() for v in r['dimension_reasons'].values())
        assert all(isinstance(r[k],str) and r[k].strip() for k in ['evidence','rationale','material_issue'])
        assert len(set(r['fairness_subtypes']))==len(r['fairness_subtypes']) and set(r['fairness_subtypes'])<=set(['access','affordability','clinical_management','dimension_information'])
        assert len(set(r['innovation_subtypes']))==len(r['innovation_subtypes']) and set(r['innovation_subtypes'])<=set(['attribute','research_support','qualification_advantage'])
        assert bool(r['fairness_subtypes'])==(r['labels']['F']==1)
        assert bool(r['innovation_subtypes'])==(r['labels']['I']==1)
        assert r['safety_quality_basis'] in ['quality_only','quality_and_other','no_quality_basis','undetermined']
        if r['labels']['S']==0: assert r['safety_quality_basis']=='no_quality_basis'
        if r['labels']['S']==1: assert r['safety_quality_basis']!='undetermined'
        if r['labels']['S']=='待定': assert r['safety_quality_basis']=='undetermined'
        assert r['input_assessment']['status'] in ['sufficient','context_insufficient','text_problem'] and r['input_assessment']['basis']
        if r['input_assessment']['status']!='sufficient': assert all(v=='待定' for v in r['labels'].values())
    out={'coder':'A','identity':{'kind':'AI','name':'V600独立评审A','underlying_model_revision':'未知'},'protocol_version':'CAL-5D-20260926-v1.3','protocol_acknowledged':True,'completed_at':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds'),'input_packet_sha256':hashlib.sha256(inp).hexdigest(),'batch':batch,'total_batches':27,'rows':rows,'rule_questions':questions or []}
    raw=(json.dumps(out,ensure_ascii=False,indent=2)+'\n').encode()
    fd,temp=tempfile.mkstemp(prefix=f'.结果-{batch:02d}-',suffix='.tmp',dir=ROOT)
    with os.fdopen(fd,'wb') as f:
        f.write(raw);f.flush();os.fsync(f.fileno())
    assert json.loads(Path(temp).read_bytes())==out
    os.link(temp,ROOT/f'结果-{batch:02d}.json')
    os.unlink(temp)
    print(json.dumps({'published':f'结果-{batch:02d}.json','rows':len(rows),'sha256':hashlib.sha256(raw).hexdigest()},ensure_ascii=False))
