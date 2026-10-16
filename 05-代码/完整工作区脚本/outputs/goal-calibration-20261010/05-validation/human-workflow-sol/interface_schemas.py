#!/usr/bin/env python3
"""导出接口 JSON Schema；运行时 workflow.py 用 stdlib 作更严格关系核验。"""
from pathlib import Path
import workflow as w

HERE = Path(__file__).resolve().parent
STR = {'type':'string'}
NONEMPTY = {'type':'string','minLength':1}
SHA = {'type':'string','pattern':'^[0-9a-f]{64}$'}
NULL = {'type':'null'}


def obj(properties, required=None):
    return {'type':'object','additionalProperties':False,'properties':properties,
            'required':list(properties) if required is None else list(required)}


def arr(items):
    return {'type':'array','items':items}


def ref(name):
    return {'$ref':'#/$defs/'+name}


def nullable(v):
    return {'anyOf':[v,NULL]}


def definitions():
    locator = obj({
        'physical_pages':arr({'type':'integer','minimum':1}),
        'printed_pages':arr({'type':['string','integer']}),
        'paragraph_ids':arr(STR),'line_ids':arr({'type':['string','integer']}),
        'article':{'type':['string','integer','null']},
        'table_cell':nullable(STR),'source_url':nullable(STR),'snapshot_attachment_id':nullable(STR)},[])
    source_ref = obj({'source_sha256':nullable(SHA),'source_locator':locator,
                      'provenance_status':{'enum':['binary_source_verified','derived_mapping_verified','unresolved']}})
    raw_scalar = {'type':['string','number','boolean','null']}
    nested_properties = {k:ref('raw_structure') for k in sorted(w.NESTED_KEYS)}
    nested_properties['source_ref'] = ref('source_ref')
    raw_structure = {'anyOf':[raw_scalar,arr(ref('raw_structure')),obj(nested_properties,[])]}
    structure_properties = {k:ref('raw_structure') for k in sorted(w.STRUCT_KEYS)}
    context = obj({'context_id':{'type':'string','pattern':'^CTX-[A-Za-z0-9_-]+$'},
                   'kind':{'enum':sorted(w.KINDS)},'structure':obj(structure_properties,[]),
                   'source_ref':ref('source_ref'),'text':nullable(STR),'title':nullable(STR),
                   'caption':nullable(STR),'headers':ref('raw_structure'),'row_cells':ref('raw_structure')},
                  ['context_id','kind','structure','source_ref'])
    attachment = obj({'attachment_id':{'type':'string','pattern':'^ASSET-[A-Za-z0-9_-]+$'},
                      'sha256':SHA,'kind':{'enum':['original_source_page','table_crop','diagram_crop']},
                      'source_ref':ref('source_ref')})
    neutral_props = {'unit_text':NONEMPTY,'unit_source_ref':ref('source_ref'),'source_title':nullable(STR),
                     'contexts':arr(ref('context')),'attachments':arr(ref('attachment')),
                     'material_status':{'enum':['ready','source_reference_pending','context_provenance_pending','parse_failure']},
                     'neutral_material_note':nullable(STR)}
    source_record = obj(dict(neutral_props,record_id=NONEMPTY))
    packet_record = obj(dict(neutral_props,packet_version={'const':w.VERSION},manual_version=NONEMPTY,
                            blind_id={'type':'string','pattern':'^[AB]-[0-9]{6}$'},content_sha256=SHA))
    asset = obj({'sha256':SHA,'relative_path':NONEMPTY,'mime_type':{'enum':list(w.MIME_EXT)}})
    source_manifest = obj({'schema_version':{'const':'neutral-source-draft-1'},'status':{'const':'frozen'},
                           'purpose':{'enum':['independent_validation','toy']},'records_file':NONEMPTY,
                           'records_sha256':SHA,'record_count':{'type':'integer','minimum':2},
                           'assets':arr(asset),'original_sources':arr(asset),'context_selection_version':NONEMPTY})
    executor = obj({'anonymous_code':{'type':'string','pattern':w.SAFE.pattern},
                    'assignment_status':{'enum':['confirmed_real_human','synthetic_toy']},'identity_registry_sha256':SHA})
    design_row = obj({'record_id':NONEMPTY,'department':NONEMPTY,'family_id':NONEMPTY,'stratum':NONEMPTY,
                      'N_h':{'type':'integer','minimum':1},'n_h':{'type':'integer','minimum':1},
                      'pi':{'type':'number','exclusiveMinimum':0,'maximum':1},'weight':{'type':'number','minimum':1}})
    draw = obj({'schema_version':{'const':'frozen-draw-draft-1'},'status':{'const':'frozen'},
                'purpose':{'enum':['independent_validation','toy']},'sampling_execution':{'const':'completed'},
                'draw_id':NONEMPTY,'round_id':{'type':'string','pattern':w.SAFE.pattern},'parent_round_id':nullable(STR),
                'source_manifest_sha256':SHA,'manual_sha256':SHA,'manual_version':NONEMPTY,'manual_status':{'const':'frozen'},
                'statistical_plan_sha256':SHA,'selected_record_ids':{'type':'array','minItems':2,'uniqueItems':True,'items':NONEMPTY},
                'presentation_seeds':obj({'A':NONEMPTY,'B':NONEMPTY}),'executors':obj({'A':executor,'B':executor}),
                'design_rows':arr(design_row)})
    context_quote = obj({'context_id':NONEMPTY,'quote':NONEMPTY})
    image_evidence = obj({'attachment_id':NONEMPTY,'sha256':SHA,'location':NONEMPTY,'quote_or_geometry':NONEMPTY,'use':NONEMPTY})
    path_piece = obj({'source':NONEMPTY,'quote':NONEMPTY,'explanation':NONEMPTY})
    path = obj({k:path_piece for k in ['support_object','support_arrangement','direct_relation','patient_drug_object','fairness_relation','current_arrangement_or_evaluation']},[])
    request = obj({'type':{'enum':['missing_source','unresolved_reference','unresolved_structure','rule_conflict']},
                   'current_reference_quote':NONEMPTY,'needed_material':NONEMPTY,'why_decisive':NONEMPTY})
    dimension = obj({'value':{'enum':[0,1,None]},'evidence_path':nullable(NONEMPTY),'current_quote':nullable(NONEMPTY),
                     'context_quotes':arr(context_quote),'image_evidence':arr(image_evidence),'reason':nullable(NONEMPTY),
                     'path_evidence':path,'material_requests':arr(request)})
    complete_dimension = dict(dimension)
    complete_dimension['properties']=dict(dimension['properties'],evidence_path=NONEMPTY,current_quote=NONEMPTY,reason=NONEMPTY)
    complete_dimension['allOf']=[{'if':{'properties':{'value':{'type':'null'}}},
                                  'then':{'properties':{'material_requests':{'minItems':1}}}}]
    viewed = obj({'attachment_id':NONEMPTY,'sha256':SHA,'viewed_at':NONEMPTY})
    labels_row = obj({'blind_id':{'type':'string','pattern':'^[AB]-[0-9]{6}$'},'content_sha256':SHA,
                      'completion_status':{'enum':['unfilled','complete']},'dimensions':obj({k:ref('dimension') for k in w.DIMS}),
                      'viewed_attachments':arr(viewed)})
    labels_row['allOf']=[{'if':{'properties':{'completion_status':{'const':'complete'}}},
                          'then':{'properties':{'dimensions':obj({k:ref('complete_dimension') for k in w.DIMS})}}},
                         {'if':{'properties':{'completion_status':{'const':'unfilled'}}},
                          'then':{'properties':{'dimensions':obj({k:{'allOf':[ref('dimension'),{'properties':{'value':{'const':None},'evidence_path':{'const':None},'current_quote':{'const':None},'reason':{'const':None},'context_quotes':{'maxItems':0},'image_evidence':{'maxItems':0},'material_requests':{'maxItems':0},'path_evidence':{'maxProperties':0}}}]} for k in w.DIMS}), 'viewed_attachments':{'maxItems':0}}}}]
    independent = obj({k:{'type':'boolean'} for k in ['own_first_judgment','machine_answers_unseen','peer_answers_unseen','no_discussion_before_seal']})
    ai = obj({'label_drafting_used':{'type':'boolean'},'description':NONEMPTY})
    submission = obj({'schema_version':{'const':w.VERSION},'state':{'enum':['unfilled','complete']},
                      'purpose':{'enum':['independent_validation','toy']},'round_id':NONEMPTY,'executor_code':NONEMPTY,
                      'actual_actor_type':{'enum':['pending','real_human_independent','real_human_posthoc_review','AI_draft','synthetic_toy']},
                      'identity_registry_sha256':nullable(SHA),'manual_sha256':SHA,'packet_sha256':SHA,'labels_sha256':nullable(SHA),
                      'record_count':{'type':'integer','minimum':2},'dimension_count':{'type':'integer','minimum':10},
                      'started_at':nullable(NONEMPTY),'submitted_at':nullable(NONEMPTY),'independence_declaration':nullable(independent),
                      'AI_assistance':nullable(ai),'prior_development_exposure':nullable(NONEMPTY),
                      'material_request_count':{'type':['integer','null'],'minimum':0},'image_view_attestation':{'type':['boolean','null']}})
    submission['allOf']=[{'if':{'properties':{'state':{'const':'complete'}}},'then':{'properties':{
        'actual_actor_type':{'enum':['real_human_independent','real_human_posthoc_review','AI_draft','synthetic_toy']},
        'identity_registry_sha256':SHA,'labels_sha256':SHA,'started_at':NONEMPTY,'submitted_at':NONEMPTY,
        'independence_declaration':independent,'AI_assistance':ai,'prior_development_exposure':NONEMPTY,
        'material_request_count':{'type':'integer','minimum':0},'image_view_attestation':{'const':True}}}}]
    packet_manifest = obj({'schema_version':{'const':w.VERSION},'purpose':{'enum':['independent_validation','toy']},
                           'round_id':NONEMPTY,'parent_round_id':nullable(STR),'side':{'enum':['A','B']},'executor_code':NONEMPTY,
                           'identity_registry_sha256':SHA,'manual_version':NONEMPTY,'manual_sha256':SHA,'packet_sha256':SHA,
                           'record_count':{'type':'integer','minimum':2},'dimension_count':{'type':'integer','minimum':10},
                           'assets':arr(asset),'content_set_sha256':SHA})
    return dict(source_ref=source_ref,raw_structure=raw_structure,context=context,attachment=attachment,
                source_record=source_record,packet_record=packet_record,source_manifest=source_manifest,
                draw_manifest=draw,dimension=dimension,complete_dimension=complete_dimension,labels_row=labels_row,
                submission=submission,packet_manifest=packet_manifest)


def main():
    defs=definitions()
    for name in ['source_manifest','source_record','draw_manifest','packet_record','packet_manifest','labels_row','submission']:
        schema={'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:human-workflow-sol:draft1:'+name,
                'title':'未来真人执行接口草案：'+name,'$ref':'#/$defs/'+name,'$defs':defs,
                '$comment':'仅技术接口。关系/哈希/连续引文/身份声明核验以workflow.py为准；不证明真人执行或语义正确。'}
        path=HERE/'schemas'/(name+'.schema.json')
        if path.exists():
            raise SystemExit('schema已存在；修订另版本或明确开发阶段更新，不自动覆盖')
        w.put_json(path,schema)


if __name__=='__main__':
    main()
