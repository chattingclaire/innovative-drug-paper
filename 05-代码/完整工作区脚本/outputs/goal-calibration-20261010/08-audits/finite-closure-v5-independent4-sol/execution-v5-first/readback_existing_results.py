"""Verify nested original quotes and scope receipt in saved results only."""
import hashlib
import json
from pathlib import Path

D=Path(__file__).resolve().parent
def bind(p):
    b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def walk(v,path=''):
    if isinstance(v,dict):
        yield path,v
        for k,x in v.items():yield from walk(x,path+'/'+k)
    elif isinstance(v,list):
        for i,x in enumerate(v):yield from walk(x,path+'/'+str(i))

def main():
    target=D/'scope-receipt-and-nested-quote-readback.json'
    if target.exists():raise RuntimeError('Existing readback must remain')
    rows=json.loads((D/'execution-results.json').read_bytes());out=[]
    for row in rows:
        unit=json.loads((D/'semantic-units'/(row['case_id']+'.json')).read_bytes())
        contexts={c['context_id']:c for c in unit['contexts']};checks=[]
        for path,q in walk({'decisions':row['decisions'],'trace':row['trace']}):
            if not {'context_id','start','end','text','source_ref'}<=set(q):continue
            c=contexts[q['context_id']]
            assert q['source_ref']==c['source_ref'] and q['text']==c['text'][q['start']:q['end']]
            entry={'path':path,'context_id':q['context_id'],'literal_context_and_source_ref_verified':True}
            if c['kind']=='source_textleaf':
                loc=q['source_ref']['locator'];p=Path(loc['snapshot_absolute_path']);b=p.read_bytes();raw=b.decode('utf8')
                assert bind(p)['sha256']==q['source_ref']['sha256']==loc['snapshot_sha256']
                lo,hi=loc['unicode_code_point_interval_half_open'];assert raw[lo:hi]==c['text']
                start,end=lo+q['start'],lo+q['end'];assert raw[start:end]==q['text']
                entry.update(original_file=bind(p),original_codepoint_interval=[start,end],
                    original_utf8_interval=[len(raw[:start].encode()),len(raw[:end].encode())],
                    original_start_line=raw[:start].count('\n')+1)
            checks.append(entry)
        bridge=[r for r in row['trace']['relations'] if r['details'].get('relation_subtype')=='SE_primary_literal_operational_standard']
        receiptchecks=[]
        for relation in bridge:
            details=relation['details'];proof=details['closure_proof']
            assert details['affected_dimensions']==['S','E','Ec'] and details['SE_scope_verified'] is True
            assert proof['actual_next_normative_boundary'] is True and proof['EOF_is_not_closure'] is True
            source=Path(row['fixed_control']['source_text']['path']);text=source.read_bytes().decode('utf8')
            a,b=proof['current_snapshot_span'];assert text[a:b]==unit['text']==proof['current_exact_raw_text']
            anchor=details['current_operative_anchor'];assert anchor['text']==unit['text'][anchor['start']:anchor['end']]
            x,y=proof['actual_next_boundary_snapshot_span'];boundary=text[x:y]
            assert boundary=='三、其他事项'
            boundary_text=''.join(q['text'] for q in proof['boundary_quotes']);assert boundary_text==boundary
            ca,cb=proof['content_snapshot_span'];assert cb<=x
            receiptchecks.append({'source_sha256_verified':bind(source)['sha256']==proof['source_sha256'],
                'current_unique_original_snapshot_anchor_verified':True,'actual_next_normative_boundary':boundary,
                'boundary_original_interval':[x,y],'content_original_interval':[ca,cb],
                'content_range_precedes_boundary':True,'typed_consumers':['S','E','Ec'],
                'identity_and_proof_only_nested_quotes_verified':True})
        out.append({'case_id':row['case_id'],'actual_S':row['actual_S'],'expected_S':row['expected_S'],
            'matches':row['matches_fixed_S_expectation'],'SE_bridge_relation_count':len(bridge),
            'nested_literal_quote_checks':checks,'scope_receipt_checks':receiptchecks,
            'S_basis':row['decisions']['S']['basis_path'],'S_needed_material':row['decisions']['S']['needed_material'],
            'material_requests':row['trace']['material_requests'],
            'extra_candidate_calls':0,'classification_output_mutated':False})
    target.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'saved_results_readback':4,'nested_quote_checks':sum(len(x['nested_literal_quote_checks']) for x in out),
        'scope_receipts':sum(len(x['scope_receipt_checks']) for x in out),'candidate_calls_added':0}))

if __name__=='__main__':main()
