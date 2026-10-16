"""CAL-5D v1.3 automatic rules: five-dimension implementation review.

Frozen earlier results remain intact. The inherited v25 module changes only
its completeness gate; each dimension module reviews evidence, then labels
are rebuilt exclusively from current-unit evidence.
"""
import copy
import common_definition_stage
import common_definition_delta06
import common_scope09
import common_coverage_relations11
import common_cited_list_conditions12
from rule_support import rebuild, DIMENSIONS
import inherited_rules_v25
import rules_se
import rules_ec
import rules_if
import rules_recall_v31
import rules_boundary_v32
import table_material_adapter_v321
import source_context_adapter_v34
import material_completeness_v34
import referenced_relations_v34
import rules_substantive_v33
import rules_semantic_v35
import rules_semantic_v36
import rules_bounded_v36_2
import rules_repair_v37
import rules_supply_membership_v38
import rules_current_relations_v39
from context_validation import validate_added_parents

VERSION = 'common-definitions-development-candidate12'


def code_unit(record, *, source_adapter=True, substantive_rules=True):
    record = source_context_adapter_v34.prepare(record) if source_adapter else record
    record = material_completeness_v34.prepare(record)
    record = rules_current_relations_v39.prepare(record)
    validate_added_parents(record)
    table_material_adapter_v321.verified_rows(record)
    result = copy.deepcopy(inherited_rules_v25.code_unit(record))
    result['version'] = VERSION
    result['semantic_protocol'] = common_definition_stage.PROTOCOL
    result['status'] = 'common_definition_development_candidate_not_adopted'
    if result.get('judgement_status') == 'undetermined':
        result['typed_contexts_v34'] = record.get('typed_contexts_v34', [])
        result['source_field_consumption_v34'] = record.get('source_field_consumption_v34', [])
        result['completeness_gate_v34'] = record.get('completeness_gate_v34')
        result['current_reference_gate_v39'] = record.get('current_reference_gate_v39')
        return result
    for module in (rules_se, rules_ec, rules_if, rules_recall_v31, rules_boundary_v32, table_material_adapter_v321):
        result = module.revise(record, result)
    if substantive_rules:
        result = rules_substantive_v33.revise(record, result)
    result = referenced_relations_v34.revise(record,result)
    result = rules_semantic_v35.revise(record,result)
    result = rules_semantic_v36.revise(record,result)
    result = rules_bounded_v36_2.revise(record,result)
    result = rules_repair_v37.revise(record,result)
    result = rules_supply_membership_v38.revise(record,result)
    result = rules_current_relations_v39.revise(record,result)
    result = common_definition_stage.revise(record, result)
    result = common_definition_delta06.revise(record, result)
    result = common_coverage_relations11.revise(record, result)
    result = common_scope09.revise(record, result)
    result = common_cited_list_conditions12.revise(record, result)
    result['implementation_scope_note'] = (
        'candidate12保留candidate11固定概念及实现，补当前实质条件清单、认证成员及明确法规条文的有界关系；'
        '法规名称绑定实际源标题，新增维度依据既有概念detector，不复制成员标签。未作独立效度验证。')
    result = rebuild(result)
    pending = result.get('common11_pending_dimensions') or {}
    if pending:
        result['partial_rule_labels_before_scope_resolution'] = dict(result['labels'])
        result['labels'] = {d: None if d in pending else value for d,value in result['labels'].items()}
        result['judgement_status'] = 'undetermined'
        result['input_assessment_status'] = 'necessary_guideline_scope_unresolved'
    result['source_list_repaired'] = bool(record.get('verified_following_list_v27') or record.get('verified_complete_following_list_v34'))
    result['typed_contexts_v34'] = record.get('typed_contexts_v34', [])
    result['source_field_consumption_v34'] = record.get('source_field_consumption_v34', [])
    result['implementation_components_v33'] = {'source_adapter': source_adapter, 'substantive_rules': substantive_rules}
    result['source_context_adaptation_log_v33'] = record.get('source_context_adaptation_log_v33', [])
    original = record['unit_text']
    for evidence in result['evidence']:
        assert original[evidence['start']:evidence['end']] == evidence['text']
        assert evidence['dimension'] in DIMENSIONS
    assert all((type(v) is int and v in (0,1)) or (d in pending and v is None)
               for d,v in result['labels'].items())
    return result
