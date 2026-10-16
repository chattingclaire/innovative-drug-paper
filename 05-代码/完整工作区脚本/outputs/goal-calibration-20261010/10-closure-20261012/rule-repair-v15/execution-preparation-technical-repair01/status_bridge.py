"""Candidate only: exact source_requests field alias; no source or semantic approval."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

VERSION = 'source-request-status-alias-candidate-1'
KNOWN = frozenset({'resolved','stopped','unresolved'})

class BridgeContractError(ValueError):
    def __init__(self, code, detail=None):
        self.code = code
        self.detail = detail
        super().__init__(code)

def canonical_bytes(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf8')

def _no_duplicate_keys(pairs):
    result = {}
    for key,value in pairs:
        if key in result: raise BridgeContractError('duplicate_json_key',key)
        result[key]=value
    return result

def canonicalize_request(request):
    """Return copied request + field provenance; never infer from evidence or another request."""
    if not isinstance(request,dict): raise BridgeContractError('request_not_object')
    present = [field for field in ('status','dependency_status') if field in request]
    if not present: raise BridgeContractError('status_fields_missing')
    for field in present:
        value=request[field]
        if type(value) is not str or value not in KNOWN:
            raise BridgeContractError('status_field_unknown_or_invalid',{'field':field,'value':value})
    if len(present)==2 and request['status']!=request['dependency_status']:
        raise BridgeContractError('status_fields_conflict',{'status':request['status'],'dependency_status':request['dependency_status']})
    value=request[present[0]]
    output=copy.deepcopy(request)
    output['status']=value
    source = 'both_exactly_equal' if len(present)==2 else present[0]
    provenance={'source_fields_present':present,'source_field_values':{field:request[field] for field in present},'canonical_status':value,'canonical_status_source':source,'added_status_alias':'status' not in request,'original_request':copy.deepcopy(request),'original_request_canonical_sha256':hashlib.sha256(canonical_bytes(request)).hexdigest(),'canonical_request_sha256':hashlib.sha256(canonical_bytes(output)).hexdigest(),'nonstatus_fields_preserved':True,'resolution_evidence_or_consumption_certified':False}
    assert {k:v for k,v in output.items() if k!='status'} == {k:v for k,v in request.items() if k!='status'}
    return output,provenance

def _locate(document,pointer):
    if not isinstance(pointer,str) or not pointer.startswith('/'):
        raise BridgeContractError('request_pointer_invalid')
    tokens=[]
    for token in pointer[1:].split('/'):
        i=0
        while i<len(token):
            if token[i]=='~' and (i+1==len(token) or token[i+1] not in '01'):
                raise BridgeContractError('request_pointer_invalid')
            i+=2 if token[i]=='~' else 1
        tokens.append(token.replace('~1','/').replace('~0','~'))
    current=document
    for token in tokens[:-1]:
        if isinstance(current,dict) and token in current: current=current[token]
        elif isinstance(current,list) and token.isdecimal() and str(int(token))==token and int(token)<len(current):current=current[int(token)]
        else:raise BridgeContractError('request_pointer_missing')
    key=tokens[-1]
    if isinstance(current,dict) and key in current:return current,key
    if isinstance(current,list) and key.isdecimal() and str(int(key))==key and int(key)<len(current):return current,int(key)
    raise BridgeContractError('request_pointer_missing')

def bridge_json_bytes(raw,expected_sha256,*,pointer='/source_requests'):
    """Canonicalize one explicitly selected saved request list, with exact raw byte binding.

    No scan of records, no classifier, no protocol.check, no recovery approval.
    Raises on any alias error, so no partial canonical document can be used.
    """
    if type(raw) is not bytes:raise BridgeContractError('input_not_bytes')
    digest=hashlib.sha256(raw).hexdigest()
    if not isinstance(expected_sha256,str) or len(expected_sha256)!=64 or digest!=expected_sha256:
        raise BridgeContractError('original_bytes_sha_mismatch')
    try:
        document=json.loads(raw.decode('utf8',errors='strict'),object_pairs_hook=_no_duplicate_keys,
                            parse_constant=lambda value:(_ for _ in ()).throw(BridgeContractError('nonfinite_json_value',value)))
    except (UnicodeDecodeError,json.JSONDecodeError) as error:
        raise BridgeContractError('invalid_utf8_or_json',str(error)) from error
    parent,key=_locate(document,pointer)
    requests=parent[key]
    if not isinstance(requests,list):raise BridgeContractError('source_requests_not_list')
    output=copy.deepcopy(document); out_parent,out_key=_locate(output,pointer)
    normalized=[];origins=[]
    for index,request in enumerate(requests):
        try: canonical,origin=canonicalize_request(request)
        except BridgeContractError as error:
            raise BridgeContractError(error.code,{'request_pointer':pointer+'/'+str(index),'detail':error.detail}) from error
        normalized.append(canonical);origins.append({'request_pointer':pointer+'/'+str(index),**origin})
    out_parent[out_key]=normalized
    report={'bridge_version':VERSION,'operation':'candidate_status_alias_only','original_document_sha256':digest,'original_document_bytes':len(raw),'request_list_pointer':pointer,'original_source_requests':copy.deepcopy(requests),'request_origins':origins,'canonical_statuses':[r['status'] for r in normalized],'request_order_and_count_preserved':True,'canonical_document_sha256':hashlib.sha256(canonical_bytes(output)).hexdigest(),'substantive_source_proof_consumption_and_quote_checks':'unchanged and still required; not performed or certified by this bridge','protocol_or_driver_modified':False,'classifier_called':False,'actual_recovery_authorized_or_executed':False}
    return output,report

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',required=True);parser.add_argument('--input-sha256',required=True)
    parser.add_argument('--request-pointer',default='/source_requests');parser.add_argument('--out',required=True)
    args=parser.parse_args();out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=False)
    p=Path(args.input).resolve();raw=p.read_bytes()
    (out/'input-original.json').write_bytes(raw)
    result={'input_path':str(p),'original_sha256':hashlib.sha256(raw).hexdigest(),'original_bytes':len(raw),'expected_sha256':args.input_sha256,'request_list_pointer':args.request_pointer,'mode':'candidate_preparation_only','recovery_or_result_acceptance':False}
    exit_code=0
    try:
        candidate,report=bridge_json_bytes(raw,args.input_sha256,pointer=args.request_pointer)
        candidate_bytes=canonical_bytes(candidate)+b'\n'
        (out/'candidate-document.json').write_bytes(candidate_bytes)
        result.update(alias_contract_valid=True,report=report,candidate_file_sha256=hashlib.sha256(candidate_bytes).hexdigest(),candidate_file_bytes=len(candidate_bytes))
    except BridgeContractError as error:
        result.update(alias_contract_valid=False,error_code=error.code,error_detail=error.detail,canonical_document_withheld=True)
        exit_code=2
    (out/'bridge-receipt.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8')
    print(json.dumps({'alias_contract_valid':result['alias_contract_valid'],'candidate_preparation_only':True,'error_code':result.get('error_code')},ensure_ascii=False))
    return exit_code

if __name__=='__main__':raise SystemExit(main())
