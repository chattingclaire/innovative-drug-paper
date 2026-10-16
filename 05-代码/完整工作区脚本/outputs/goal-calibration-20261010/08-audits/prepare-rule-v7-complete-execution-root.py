"""Bind the delivered generic rule repair to one complete production replay."""
from pathlib import Path
import copy,datetime,hashlib,json,sys
R=Path(__file__).resolve().parents[1]
OLD=R/'06-coding/rule-full4481-final-v5-sol'
OUT=R/'06-coding/rule-full4481-final-v7-root'
CANDIDATE=R/'06-coding/rule-five-dimension-joint-root/versions/joint-v7-relation-content-sol'
def bind(p):
 p=Path(p).resolve();b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def load(p):return json.loads(Path(p).read_bytes())
def save(p,x):
 with Path(p).open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
def main():
 delivery=Path(sys.argv[1]).resolve();assert delivery.parent==CANDIDATE and delivery.exists()
 seal=load(delivery)
 members=seal.get('files',seal.get('members',seal.get('output_files',seal.get('output_members',[]))))
 assert members,'Candidate delivery seal must enumerate actual files'
 for b in members:
  p=Path(b.get('path',b.get('relative_path','')))
  if not p.is_absolute():p=CANDIDATE/p
  actual=bind(p);assert actual['bytes']==b['bytes'] and actual['sha256']==b['sha256'],'Candidate seal file changed '+str(p)
 scope=load(OLD/'frozen-scope.json');release=load(OLD/'rule-production-release.json')
 authorization='ROOT-v7-generic-repair-original-common4481-once-20261011';run=OUT/'run4481-first'
 modules=[dict(bind(CANDIDATE/(n+'.py')),module=n) for n in ('source_packet','source_receipts','evidence','relations','dimensions')]
 final=bind(delivery);pre=bind(CANDIDATE/'initial-snapshot.json')
 algorithm={'algorithm_version':'joint-v7-relation-content-sol','modules':modules,'final_candidate_delivery_seal':final,'final_candidate_pre_execution_seal':pre,'source_and_manual_unchanged':True,'reference_not_classifier_input':True}
 save(OUT/'algorithm-bindings.json',algorithm)
 release.update(authorization_id=authorization,output_directory=str(run),algorithm=bind(OUT/'algorithm-bindings.json'),description='Complete disclosed development-derived rule production replay after verified direct-content and bounded-relation repairs; not formal independent validation.')
 save(OUT/'rule-production-release.json',release)
 old_materials=scope['material_bindings'];scope.update(authorization_id=authorization,output_directory=str(run),release=bind(OUT/'rule-production-release.json'),algorithm_bindings=bind(OUT/'algorithm-bindings.json'),driver_version='v7-full4481-original-common-driver-1',algorithm_origin='ROOT v6 generic direct-content repairs plus sol ultra v7 bounded-relation repairs',final_candidate_algorithm=bind(OUT/'algorithm-bindings.json'),final_candidate_pre_execution_seal=pre,final_candidate_delivery_seal=final)
 scope['packet_bindings']=bind(OUT/'packet-bindings.json')
 scope['material_bindings']=[b for b in old_materials if Path(b['path']).name!='rule-production-release.json']+[scope['release']]
 save(OUT/'frozen-scope.json',scope)
 preflight={'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':bind(OUT/'frozen-scope.json'),'files':[bind(OUT/n) for n in ('rule_driver.py','interface_common.py','status_bridge.py','packet-bindings.json','algorithm-bindings.json','rule-production-release.json')],'candidate_delivery':final,'record_N':4481,'dimension_N':22405,'source_manual_prompt_protocol_unchanged':True,'source_request_status_alias_only':True,'reference_files_not_authorized':True,'formal_validation_complete':False,'one_complete_run_authorized':True}
 save(OUT/'pre-execution-run-seal.json',preflight)
 print(json.dumps({'scope':preflight['scope'],'input':scope['source_packet'],'out':str(run)},ensure_ascii=False))
if __name__=='__main__':main()
