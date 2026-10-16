"""Finite NONHUMAN transport checks; no semantic_unit, RelationView or judge."""
import argparse
import copy
import json
from pathlib import Path
import tempfile
from literal_inventory_bridge import append_literal_entries
from merge_common import bind, sha, save
from receive_merge import validate_pair
from finalize_scope import finalize
import rule_driver


def run():
    results=[]
    def check(name, operation, reject=False):
        try:
            operation()
            results.append({'name':name,'passed':not reject,'expected':'reject' if reject else 'accept','actual':'accept'})
        except (ValueError, AssertionError, KeyError) as error:
            results.append({'name':name,'passed':reject,'expected':'reject' if reject else 'accept','actual':'reject','reason':str(error)})
    with tempfile.TemporaryDirectory(prefix='NONHUMAN-v12-transport-') as temporary:
        t=Path(temporary);text='测试原文。';raw=json.dumps({'paragraphs':[text]},ensure_ascii=False).encode();p=t/'source.json';p.write_bytes(raw)
        html=('<p>'+text+'</p>').encode();hp=t/'source.html';hp.write_bytes(html)
        lexeme=json.dumps(text,ensure_ascii=False);decoded=raw.decode();a=decoded.index(lexeme);b=a+len(lexeme)
        loc={'kind':'structured_JSON_and_original_HTML','structured_snapshot':{'absolute_path':str(p),'sha256':sha(raw),'json_pointer':'/paragraphs/0','raw_JSON_string_literal_unicode_interval_half_open':[a,b],'raw_JSON_string_literal_utf8_byte_interval_half_open':[len(decoded[:a].encode()),len(decoded[:b].encode())]},'raw_html':{'absolute_path':str(hp),'sha256':sha(html),'raw_unicode_interval_half_open':[0,len(html.decode())],'raw_utf8_byte_interval_half_open':[0,len(html)],'outer_html_sha256_utf8':sha(html)}}
        leaf={'text':text,'text_sha256':sha(text.encode()),'source_resource_id':'TOY-LEAF','source_document_resource_id':'TOY-DOC','source_sha256':sha(raw),'source_version_id':'TOY-V1','source_locator':loc,'role':'literal'}
        bundle={'explicit_or_primary_source_resources':[{'source_sha256':sha(raw),'source_version_id':'TOY-V1','source_texts':[leaf]}],'source_documents':[{'source_resource_id':'TOY-DOC','source_sha256':sha(raw),'source_version_id':'TOY-V1'}]}
        materials=[bind(p),bind(hp)];original=[{'resource_id':'TOY-ORIGINAL','source_sha256':sha(raw),'available_views':{'text':'0'*64},'locator':{'kind':'original'}}]
        def inventory(bun=None, old=None, mats=None):
            return append_literal_entries(bundle if bun is None else bun,original if old is None else old,materials if mats is None else mats)
        def valid():
            extended,delta=inventory();assert extended[:1]==original and len(delta)==1 and delta[0]['read_or_use_attested'] is False
            again,d2=inventory(old=extended);assert again==extended and not d2
        check('literal_append_and_idempotent_old_inventory_preservation',valid)
        bad=copy.deepcopy(bundle);bad['explicit_or_primary_source_resources'][0]['source_texts'][0]['text_sha256']='0'*64
        check('wrong_literal_SHA',lambda:inventory(bad),True)
        badver=copy.deepcopy(bundle);badver['source_documents'][0]['source_version_id']='TOY-V2'
        check('wrong_source_version',lambda:inventory(badver),True)
        check('unbound_original_file',lambda:inventory(mats=[]),True)
        badloc=copy.deepcopy(bundle);badloc['explicit_or_primary_source_resources'][0]['source_texts'][0]['source_locator']['structured_snapshot']['raw_JSON_string_literal_utf8_byte_interval_half_open'][1]-=1
        check('conflicting_coordinate_systems',lambda:inventory(badloc),True)
        conflict=copy.deepcopy(original);conflict.append({'resource_id':'TOY-LEAF','source_sha256':'f'*64,'available_views':{'text':leaf['text_sha256']},'locator':loc})
        check('existing_ID_conflict',lambda:inventory(old=conflict),True)

        dims=('S','E','Ec','I','F')
        decisions={d:{'value':0,'reason':'NONHUMAN unchanged '+d} for d in dims}
        old={'id':'NONHUMAN-TOY','labels':{d:0 for d in dims},'decisions':decisions,'implementation_errors':[],'source_requests':[],'material_requests':[],'relation_traces':[]}
        new=copy.deepcopy(old);new['decisions']['S']={'value':1,'reason':'NONHUMAN permitted S repair'};new['labels']['S']=1
        new['candidate_decisions_diagnostic_only']=copy.deepcopy(new['decisions'])
        event={'resource_id':'TOY','view':'text','source_sha256':'a'*64,'view_sha256':'b'*64,'locator_read':{'kind':'toy'}}
        oldlog={'actual_text_geometry_events':[event]}
        newlog={'actual_text_geometry_events':[event],'source_requests':[],'material_requests':[],'uniform_source_protocol_check':{'errors':[],'dependency_stop_reasons':[]},'run_id':'NEW-TOY','source_identity_resolution_delta':[{'kind':'new_available_literal'}]}
        def pair(n=None,nl=None):
            n=copy.deepcopy(new if n is None else n);nl=copy.deepcopy(newlog if nl is None else nl)
            slots={d:{'id':n['id'],'dimension':d,'rule_value':n['labels'][d],'retained_rule_decision':n['decisions'][d],'technical_failure':False,'record_implementation_errors':[],'global_implementation_errors':[],'rules_null':n['labels'][d] is None,'status':'source_dependency_unresolved' if n['labels'][d] is None else 'retained_rule_decision'} for d in dims if d in n['decisions']}
            return n,nl,slots
        def validate(triple):
            n,nl,slots=triple
            return validate_pair(json.dumps(old).encode(),json.dumps(n).encode(),oldlog,nl,slots)
        check('permitted_S_change_and_fresh_receipt_metadata',lambda:validate(pair()))
        null=copy.deepcopy(new);null['labels']['S']=None;null['decisions']['S']['value']=None;null['candidate_decisions_diagnostic_only']=copy.deepcopy(null['decisions'])
        check('lawful_NULL_retained_as_NULL',lambda:validate(pair(null)))
        changed=copy.deepcopy(new);changed['decisions']['E']['reason']='NONHUMAN unauthorized detail';changed['candidate_decisions_diagnostic_only']=copy.deepcopy(changed['decisions'])
        check('same_label_but_changed_E_complete_reason',lambda:validate(pair(changed)),True)
        missing=copy.deepcopy(new);missing['decisions'].pop('I')
        check('missing_I_decision',lambda:validate(pair(missing)),True)
        changedlog=copy.deepcopy(newlog);changedlog['actual_text_geometry_events'][0]['view_sha256']='c'*64
        check('changed_stored_source_event',lambda:validate(pair(nl=changedlog)),True)
        failure=pair();failure[2]['S']['technical_failure']=True
        check('technical_failure_is_not_NULL',lambda:validate(failure),True)
        misnull=pair(null);misnull[2]['S']['rules_null']=False
        check('NULL_flag_inconsistent',lambda:validate(misnull),True)
        request=copy.deepcopy(new);request['source_requests']=[{'request':'NONHUMAN new request'}]
        check('changed_original_source_request',lambda:validate(pair(request)),True)
        check('I_only_scope_cannot_authorize_SF',lambda:rule_driver.validate_sf_scope({'allowed_mutable_dimensions':['I'],'immutable_dimensions':['S','E','Ec','F']}),True)
        h=Path(__file__).parent;release=h/'release.UNRELEASED.json'
        check('UNRELEASED_template_cannot_finalize_scope',lambda:finalize(release,bind(release)['sha256'],t/'must-not-exist.json'),True)
        assert not (t/'must-not-exist.json').exists()
    return {'scope':'finite_NONHUMAN_transport_only','N':len(results),'passed_N':sum(x['passed'] for x in results),'classifier_calls':0,'real_source_classification':False,'real_release_created':False,'results':results}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();result=run();save(a.out,result)
    print(json.dumps({k:result[k] for k in ('N','passed_N','classifier_calls','real_release_created')}))
    if result['N']!=result['passed_N']:raise SystemExit(1)
